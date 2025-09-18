from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
import os
import json
import re
from datetime import datetime
from config import Config
from modules.ai.generator import AIContentGenerator
from modules.maimai.api import MaimaiAPI

# 创建Flask应用
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)

# 配置日志
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def parse_ai_response(content: str) -> dict:
    """
    解析AI返回的内容，使用正则表达式直接提取title和content
    不依赖JSON格式正确性，只要找到"title":"xxx"和"content":"xxx"就提取
    """
    try:
        # 打印AI原始回答
        logger.info("="*50)
        logger.info("AI原始回答:")
        logger.info(content)
        logger.info("="*50)
        
        # 使用更简单直接的正则表达式，优先匹配完整的对象
        # 方法1：匹配完整的对象结构 {title:"...", content:"..."}
        object_pattern = r'\{\s*"title"\s*:\s*"((?:[^"\\]|\\.)*?)"\s*,\s*"content"\s*:\s*"((?:[^"\\]|\\.)*?)"\s*\}'
        object_matches = re.findall(object_pattern, content, re.DOTALL)
        
        if object_matches:
            titles = [m[0] for m in object_matches]
            contents = [m[1] for m in object_matches]
            logger.info("使用对象模式匹配成功")
        else:
            # 方法2：单独匹配title和content字段
            title_pattern = r'"title"\s*:\s*"((?:[^"\\]|\\.)*?)"'
            content_pattern = r'"content"\s*:\s*"((?:[^"\\]|\\.)*?)"'
            
            titles = re.findall(title_pattern, content, re.DOTALL)
            contents = re.findall(content_pattern, content, re.DOTALL)
            logger.info("使用字段模式匹配")
        
        logger.info(f"正则提取结果: 找到 {len(titles)} 个title, {len(contents)} 个content")
        logger.info(f"提取的titles: {titles}")
        logger.info(f"提取的contents: {[c[:100] + '...' if len(c) > 100 else c for c in contents]}")
        
        # 配对title和content
        valid_items = []
        max_pairs = min(len(titles), len(contents))
        
        for i in range(max_pairs):
            title = titles[i].strip()
            content_text = contents[i].strip()
            
            if title and content_text:
                # 处理转义字符
                title = title.replace('\\"', '"').replace('\\n', '\n')
                content_text = content_text.replace('\\"', '"').replace('\\n', '\n')
                
                # 清理content中的方括号内容
                cleaned_content = re.sub(r'\[[^\]]*\]', '', content_text)
                valid_items.append({
                    'title': title,
                    'content': cleaned_content
                })
                
                logger.info(f"处理第{i+1}个对象:")
                logger.info(f"  原始title: {title}")
                logger.info(f"  原始content长度: {len(content_text)}")
                logger.info(f"  清理后content长度: {len(cleaned_content)}")
        
        if valid_items:
            logger.info(f"最终解析成功: 共{len(valid_items)}个有效对象")
            return {
                'items': valid_items,
                'success': True
            }
        
        # 如果没有找到配对，返回原始内容
        logger.warning("未找到有效的title和content配对，使用原始内容")
        return {
            'items': [{'title': None, 'content': content}],
            'success': False
        }
        
    except Exception as e:
        logger.warning(f"解析异常: {e}，使用原始内容")
        return {
            'items': [{'title': None, 'content': content}],
            'success': False
        }

# 初始化数据库存储（替代JSON存储）
from modules.database.init import create_database_stores, get_database_scheduler

logger.info("初始化数据库存储...")
db_stores = create_database_stores()

# 获取数据库版本的存储实例
ai_config_store = db_stores['ai_config_store']
topic_store = db_stores['topic_store']
scheduled_posts_store = db_stores['scheduled_posts_store']
prompt_store = db_stores['prompt_store']
group_keywords_store = db_stores['group_keywords_store']
scheduled_requests_store = db_stores['scheduled_requests_store']
auto_publish_store = db_stores['auto_publish_store']

# 调试：检查topic_store实例
logger.info(f"应用启动时 topic_store 类型: {type(topic_store)}")
logger.info(f"topic_store 模块: {topic_store.__class__.__module__}")
logger.info(f"topic_store 类名: {topic_store.__class__.__name__}")
if hasattr(topic_store, 'keyword_group_dao'):
    logger.info("✓ topic_store 有 keyword_group_dao 属性：数据库版本")
else:
    logger.warning("✗ topic_store 没有 keyword_group_dao 属性：可能是JSON版本")

# 测试方法调用
test_groups = topic_store.get_all_groups()
logger.info(f"启动时测试 topic_store.get_all_groups(): {test_groups}")

# 强制确认prompt_store类型
logger.info(f"应用启动时 prompt_store 类型: {type(prompt_store)}")
logger.info(f"prompt_store 模块: {prompt_store.__class__.__module__}")
logger.info(f"prompt_store 类名: {prompt_store.__class__.__name__}")

# 验证数据库存储实例
if hasattr(prompt_store, 'dao'):
    logger.info("✓ prompt_store 有 dao 属性（数据库版本）")
else:
    logger.error("✗ prompt_store 没有 dao 属性（可能是JSON版本）")

# 初始化AI生成器和脉脉API
current_ai_config_id = ai_config_store.get_current_config_id()
current_config = ai_config_store.get_current_config()
ai_generator = AIContentGenerator(current_config)
maimai_api = MaimaiAPI(Config.MAIMAI_CONFIG)

# 初始化定时发布处理器
from modules.scheduler.publisher import ScheduledPublisher
scheduled_publisher = ScheduledPublisher(scheduled_posts_store, maimai_api)

# 初始化定时HTTP请求调度器
daily_request_scheduler = get_database_scheduler(scheduled_requests_store)


@app.route('/')
def index():
    """主页"""
    return send_from_directory('static', 'index.html')


@app.route('/api/generate', methods=['POST'])
def generate_content():
    """生成AI内容（对话模式）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求体'}), 400

        if 'messages' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：messages'}), 400
        
        messages = data['messages']
        if not isinstance(messages, list) or not all('role' in m and 'content' in m for m in messages):
            return jsonify({'success': False, 'error': 'messages格式不正确'}), 400
        
        use_main_model = data.get('use_main_model', True)
        topic_id = data.get('topic_id')  # 新增：话题ID，用于保存对话历史
        save_conversation = data.get('save_conversation', False)  # 新增：是否保存对话历史
        
        logger.info("开始对话生成，消息数：%d", len(messages))
        result = ai_generator.chat(messages=messages, use_main_model=use_main_model)

        # 如果生成成功，尝试解析结构化内容
        if result.get('success') and 'content' in result:
            parsed_data = parse_ai_response(result['content'])
            if parsed_data['success']:
                # 如果成功解析出结构化内容，添加到结果中
                result['parsed_items'] = parsed_data['items']
                result['item_count'] = len(parsed_data['items'])
                logger.info(f"成功解析结构化内容，包含{len(parsed_data['items'])}个对象")

        # 如果生成成功且需要保存对话历史
        if result.get('success') and save_conversation and topic_id:
            try:
                # 构建完整的对话历史（包含AI回复）
                complete_messages = messages.copy()
                if 'content' in result:
                    complete_messages.append({
                        'role': 'assistant',
                        'content': result['content']
                    })
                
                # 保存对话历史
                conversation_id = auto_publish_store.save_conversation(topic_id, complete_messages)
                if conversation_id:
                    result['conversation_id'] = conversation_id
                    logger.info(f"已保存对话历史: {conversation_id}")
                else:
                    logger.warning("保存对话历史失败")
            except Exception as e:
                logger.error(f"保存对话历史异常: {e}")
                # 不影响主要功能，只记录错误

        return jsonify(result)

    except Exception as e:
        logger.error(f"生成内容异常：{str(e)}")
        return jsonify({'success': False, 'error': f'生成内容时发生错误：{str(e)}'}), 500


@app.route('/api/publish', methods=['POST'])
def publish_content():
    """发布内容到脉脉"""
    try:
        data = request.get_json()

        # 验证必需参数
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需参数：content'
            }), 400

        title = data.get('title', '')  # 允许标题为空
        content = data['content']
        topic_url = data.get('topic_url', '')
        topic_id = data.get('topic_id', '')
        circle_type = data.get('circle_type', '')
        publish_type = data.get('publish_type', 'anonymous')  # 获取发布方式，默认匿名

        logger.info(f"开始发布内容：{title} (发布方式: {'匿名' if publish_type == 'anonymous' else '实名'})")

        # 调用脉脉API发布，支持两种话题模式
        if topic_id and circle_type:
            # 使用选择的话题ID和圈子类型，从话题存储中获取名称
            logger.info(f"使用选择的话题：ID={topic_id}, circle_type={circle_type}")
            topic_data = topic_store.get_topic(topic_id)
            topic_name = topic_data.get('name') if topic_data else None
            
            result = maimai_api.publish_content(
                title=title,
                content=content,
                topic_id=topic_id,
                circle_type=circle_type,
                topic_name=topic_name,
                publish_type=publish_type
            )
        elif topic_url:
            # 使用话题链接提取
            logger.info(f"使用话题链接：{topic_url}")
            result = maimai_api.publish_content(
                title=title,
                content=content,
                topic_url=topic_url,
                publish_type=publish_type
            )
        else:
            # 无话题发布
            logger.info("无话题发布")
            result = maimai_api.publish_content(
                title=title,
                content=content,
                publish_type=publish_type
            )

        if result['success']:
            logger.info(f"内容发布成功：{title}")
        else:
            logger.error(f"内容发布失败：{result.get('error', 'Unknown error')}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"发布内容异常：{str(e)}")
        return jsonify({'success': False, 'error': f'发布内容时发生错误：{str(e)}'}), 500


@app.route('/api/topic-info', methods=['POST'])
def get_topic_info():
    """获取话题信息"""
    try:
        data = request.get_json()
        if not data or 'topic_url' not in data:
            return jsonify({'success': False, 'error': '缺少话题链接'}), 400

        topic_url = data['topic_url']
        logger.info(f"获取话题信息：{topic_url}")

        result = maimai_api.get_topic_info(topic_url)

        if result['success']:
            logger.info(f"话题信息获取成功：{result.get('title', 'Unknown')}")
        else:
            logger.error(f"话题信息获取失败：{result.get('error', 'Unknown error')}")

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取话题信息异常：{str(e)}")
        return jsonify({'success': False, 'error': f'获取话题信息时发生错误：{str(e)}'}), 500


# ===== 话题管理API =====

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """获取所有话题"""
    try:
        topics = topic_store.get_all_topics()
        return jsonify({'success': True, 'data': topics})
    except Exception as e:
        logger.error(f"获取话题列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics', methods=['POST'])
def create_topic():
    """创建话题，支持指定分组"""
    try:
        data = request.get_json()
        if not data or 'name' not in data or 'circle_type' not in data or 'id' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：id, name 或 circle_type'}), 400
        
        topic_id = data['id'].strip()
        name = data['name'].strip()
        circle_type = data['circle_type'].strip()
        group = data.get('group', '').strip() or None  # 新增: 获取分组
        
        if not topic_id or not name or not circle_type:
            return jsonify({'success': False, 'error': '话题ID、名称和圈子类型都不能为空'}), 400
        
        success = topic_store.add_topic(topic_id, name, circle_type, group_name=group)
        if success:
            topic = topic_store.get_topic(topic_id)
            return jsonify({'success': True, 'data': topic})
        else:
            return jsonify({'success': False, 'error': '添加话题失败'}), 500
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"创建话题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics/<topic_id>', methods=['PUT'])
def update_topic(topic_id):
    """更新话题，支持修改分组"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        name = data.get('name', '').strip() if data.get('name') is not None else None
        circle_type = data.get('circle_type', '').strip() if data.get('circle_type') is not None else None
        group = data.get('group', '').strip() if data.get('group') is not None else None # 可以传入""来取消分组
        
        # 确保至少有一个字段被更新
        if name is None and circle_type is None and group is None:
            return jsonify({'success': False, 'error': '至少需要提供一个要更新的字段: name, circle_type, 或 group'}), 400

        success = topic_store.update_topic(topic_id, name, circle_type, group)
        if not success:
            # update_topic 返回 False 可能意味着话题不存在或没有任何内容被实际更新
            # 为了更精确的反馈，可以检查话题是否存在
            if not topic_store.get_topic(topic_id):
                return jsonify({'success': False, 'error': '话题不存在'}), 404
            else:
                # 如果只是没有内容更新，可以视为成功，或者返回一个特定的消息
                 return jsonify({'success': True, 'message': '没有检测到变更', 'data': topic_store.get_topic(topic_id)})

        topic = topic_store.get_topic(topic_id)
        return jsonify({'success': True, 'data': topic})
    except Exception as e:
        logger.error(f"更新话题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics/<topic_id>', methods=['DELETE'])
def delete_topic(topic_id):
    """删除话题"""
    try:
        success = topic_store.delete_topic(topic_id)
        if not success:
            return jsonify({'success': False, 'error': '话题不存在'}), 404
        
        return jsonify({'success': True, 'message': '话题删除成功'})
    except Exception as e:
        logger.error(f"删除话题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics/search', methods=['GET'])
def search_topics():
    """搜索话题"""
    try:
        keyword = request.args.get('q', '').strip()
        if not keyword:
            return jsonify({'success': False, 'error': '缺少搜索关键词'}), 400
        
        topics = topic_store.search_topics(keyword)
        return jsonify({'success': True, 'data': topics})
    except Exception as e:
        logger.error(f"搜索话题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics/batch', methods=['POST'])
def batch_import_topics():
    """批量导入话题"""
    try:
        data = request.get_json()
        if not data or 'topics' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：topics'}), 400
        
        topics_data = data['topics']
        if not isinstance(topics_data, list):
            return jsonify({'success': False, 'error': 'topics必须是数组格式'}), 400
        
        if len(topics_data) == 0:
            return jsonify({'success': False, 'error': 'topics数组不能为空'}), 400
        
        # 获取分组名称（如果提供）
        group_name = data.get('group_name')
        
        # 转换字段名：将前端的'group'字段转换为数据库的'group_name'字段
        for topic in topics_data:
            if 'group' in topic and topic['group']:
                topic['group_name'] = topic['group']
                del topic['group']  # 删除原字段避免混淆
        
        # 如果提供了分组名称，为所有话题设置分组
        if group_name:
            for topic in topics_data:
                if 'group_name' not in topic or not topic['group_name']:
                    topic['group_name'] = group_name
        
        # 执行批量导入
        results = topic_store.batch_add_topics(topics_data)
        
        # 构建响应
        response_data = {
            'success': True,
            'results': results,
            'summary': {
                'total': len(topics_data),
                'success': len(results['success']),
                'failed': len(results['failed']),
                'skipped': len(results['skipped'])
            }
        }
        
        logger.info(f"批量导入完成: 总数 {len(topics_data)}, 成功 {len(results['success'])}, 失败 {len(results['failed'])}, 跳过 {len(results['skipped'])}")
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"批量导入话题失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== 分组管理API =====

@app.route('/api/topics/groups', methods=['GET'])
def get_topic_groups():
    """获取所有话题分组"""
    try:
        logger.info("get_topic_groups() - 开始获取分组")
        logger.info(f"topic_store类型: {type(topic_store)}")
        groups = topic_store.get_all_groups()
        logger.info(f"get_topic_groups() - 获取到分组: {groups}")
        return jsonify({'success': True, 'data': groups})
    except Exception as e:
        logger.error(f"获取分组列表失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/topics/groups', methods=['POST'])
def create_topic_group():
    """创建新分组"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'success': False, 'error': '缺少参数: name'}), 400
        
        group_name = data['name'].strip()
        topic_store.add_group(group_name)
        return jsonify({'success': True, 'message': f"分组 '{group_name}' 创建成功"})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"创建分组失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/topics/groups/<old_name>', methods=['PUT'])
def rename_topic_group(old_name):
    """重命名分组"""
    try:
        data = request.get_json()
        if not data or 'new_name' not in data:
            return jsonify({'success': False, 'error': '缺少参数: new_name'}), 400
            
        new_name = data['new_name'].strip()
        if not topic_store.rename_group(old_name, new_name):
            return jsonify({'success': False, 'error': f"分组 '{old_name}' 不存在"}), 404
            
        return jsonify({'success': True, 'message': f"分组 '{old_name}' 已重命名为 '{new_name}'"})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"重命名分组失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/topics/groups/<name>', methods=['DELETE'])
def delete_topic_group(name):
    """删除分组"""
    try:
        # 可选参数，决定是否同时删除分组内的话题
        delete_topics = request.args.get('delete_topics', 'false').lower() == 'true'
        
        if not topic_store.delete_group(name, delete_topics):
            return jsonify({'success': False, 'error': f"分组 '{name}' 不存在"}), 404
        
        if delete_topics:
            return jsonify({'success': True, 'message': f"分组 '{name}' 及其包含的话题删除成功"})
        else:
            return jsonify({'success': True, 'message': f"分组 '{name}' 删除成功，话题已变为未分组状态"})
    except Exception as e:
        logger.error(f"删除分组失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== 定时发布API =====

@app.route('/api/scheduled-publish', methods=['POST'])
def schedule_publish():
    """添加定时发布任务"""
    try:
        data = request.get_json()
        
        # 验证必需参数
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需参数：content'
            }), 400

        title = data.get('title', '')  # 允许标题为空
        content = data['content']
        topic_url = data.get('topic_url', '')
        topic_id = data.get('topic_id', '')
        circle_type = data.get('circle_type', '')
        publish_type = data.get('publish_type', 'anonymous')  # 获取发布方式，默认匿名

        logger.info(f"添加定时发布任务：{title} (发布方式: {'匿名' if publish_type == 'anonymous' else '实名'})")

        # 确定话题信息，完全复制正常发布的逻辑
        topic_name = None
        if topic_id and circle_type:
            # 使用选择的话题ID和圈子类型，从话题存储中获取名称
            logger.info(f"使用选择的话题：ID={topic_id}, circle_type={circle_type}")
            topic_data = topic_store.get_topic(topic_id)
            topic_name = topic_data.get('name') if topic_data else None
                
        elif topic_url:
            # 使用话题链接提取
            logger.info(f"使用话题链接：{topic_url}")
        else:
            logger.info("无话题定时发布")

        # 添加到定时发布队列，保存完整的话题信息
        post_id = scheduled_posts_store.add_post(
            title=title,
            content=content,
            topic_url=topic_url,
            topic_id=topic_id,
            circle_type=circle_type,
            topic_name=topic_name,  # 新增：保存话题名称
            publish_type=publish_type  # 新增：保存发布方式
        )

        # 获取任务信息以返回预计发布时间
        post_info = scheduled_posts_store.get_post(post_id)
        scheduled_time = post_info['scheduled_at'] if post_info else None

        return jsonify({
            'success': True,
            'message': '已添加到定时发布队列',
            'post_id': post_id,
            'scheduled_at': scheduled_time,
            'pending_count': scheduled_posts_store.get_pending_count()
        })

    except Exception as e:
        logger.error(f"添加定时发布任务异常：{str(e)}")
        return jsonify({'success': False, 'error': f'添加定时发布任务时发生错误：{str(e)}'}), 500


@app.route('/api/scheduled-posts', methods=['GET'])
def get_scheduled_posts():
    """获取所有定时发布任务"""
    try:
        posts = scheduled_posts_store.get_all_posts()
        return jsonify({
            'success': True,
            'data': posts,
            'pending_count': scheduled_posts_store.get_pending_count()
        })
    except Exception as e:
        logger.error(f"获取定时发布任务异常：{str(e)}")
        return jsonify({'success': False, 'error': f'获取定时发布任务时发生错误：{str(e)}'}), 500


@app.route('/api/scheduled-posts/<post_id>', methods=['DELETE'])
def delete_scheduled_post(post_id):
    """删除定时发布任务"""
    try:
        success = scheduled_posts_store.delete_post(post_id)
        if not success:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        return jsonify({
            'success': True,
            'message': '任务删除成功',
            'pending_count': scheduled_posts_store.get_pending_count()
        })
    except Exception as e:
        logger.error(f"删除定时发布任务异常：{str(e)}")
        return jsonify({'success': False, 'error': f'删除定时发布任务时发生错误：{str(e)}'}), 500


@app.route('/api/scheduled-posts/<post_id>', methods=['PUT'])
def update_scheduled_post(post_id):
    """更新定时发布任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        title = data.get('title')
        content = data.get('content')
        
        success = scheduled_posts_store.update_post(post_id, title, content)
        if not success:
            return jsonify({'success': False, 'error': '任务不存在或未发生更新'}), 404
        
        return jsonify({'success': True, 'message': '任务更新成功'})
    except Exception as e:
        logger.error(f"更新定时发布任务异常：{str(e)}")
        return jsonify({'success': False, 'error': f'更新定时发布任务时发生错误：{str(e)}'}), 500


@app.route('/api/scheduled-posts/<post_id>/reschedule', methods=['POST'])
def reschedule_post(post_id):
    """重新安排发布时间"""
    try:
        data = request.get_json() or {}
        delay_minutes = data.get('delay_minutes')
        
        success = scheduled_posts_store.reschedule_post(post_id, delay_minutes)
        if not success:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
        
        # 获取更新后的任务信息
        post_info = scheduled_posts_store.get_post(post_id)
        scheduled_time = post_info['scheduled_at'] if post_info else None
        
        return jsonify({
            'success': True,
            'message': '发布时间已重新安排',
            'scheduled_at': scheduled_time
        })
    except Exception as e:
        logger.error(f"重新安排发布时间异常：{str(e)}")
        return jsonify({'success': False, 'error': f'重新安排发布时间时发生错误：{str(e)}'}), 500


# ===== 自动发布管理API =====

@app.route('/api/auto-publish', methods=['GET'])
def get_auto_publish_configs():
    """获取所有自动发布配置"""
    try:
        configs = auto_publish_store.get_all_configs()
        
        # 为每个配置添加话题信息
        for config in configs:
            topic_id = config.get('topic_id')
            if topic_id:
                topic_data = topic_store.get_topic(topic_id)
                config['topic_name'] = topic_data.get('name', '') if topic_data else ''
                config['topic_group'] = topic_data.get('group_name', '') if topic_data else ''
        
        return jsonify({
            'success': True,
            'data': configs
        })
    except Exception as e:
        logger.error(f"获取自动发布配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish', methods=['POST'])
def create_auto_publish_config():
    """创建自动发布配置并立即启动自动循环"""
    try:
        data = request.get_json()
        topic_id = data.get('topic_id')
        prompt_key = data.get('prompt_key')  # 添加提示词键名
        max_posts = data.get('max_posts', -1)
        publish_type = data.get('publish_type', 'anonymous')  # 添加发布方式参数
        min_interval = data.get('min_interval', 30)  # 最小发布间隔
        max_interval = data.get('max_interval', 60)  # 最大发布间隔
        
        if not topic_id:
            return jsonify({'success': False, 'error': '话题ID不能为空'}), 400
        
        # 检查话题是否存在
        topic_data = topic_store.get_topic(topic_id)
        if not topic_data:
            return jsonify({'success': False, 'error': '话题不存在'}), 404
        
        # 检查是否已存在该话题和提示词的配置（修改支持同话题多配置）
        existing_config = auto_publish_store.get_config_by_topic_and_prompt(topic_id, prompt_key)
        if existing_config:
            return jsonify({'success': False, 'error': f'该话题的提示词"{prompt_key}"已配置自动发布'}), 400
        
        config_id = auto_publish_store.create_config(topic_id, max_posts, prompt_key, publish_type, min_interval, max_interval)
        if config_id:
            config = auto_publish_store.get_config(config_id)
            config['topic_name'] = topic_data.get('name', '')
            config['topic_group'] = topic_data.get('group_name', '')
            
            # 立即启动自动发布循环
            from modules.auto_publish.generator import AutoPublishCycleGenerator
            cycle_generator = AutoPublishCycleGenerator()
            cycle_started = cycle_generator.start_auto_publish_cycle(config_id)
            
            message = '自动发布配置创建成功'
            if cycle_started:
                message += '，已立即生成第一篇内容并安排发布'
            else:
                message += '，但启动自动循环失败，请检查日志'
            
            return jsonify({
                'success': True,
                'data': config,
                'message': message,
                'cycle_started': cycle_started
            })
        else:
            return jsonify({'success': False, 'error': '创建配置失败'}), 500
            
    except Exception as e:
        logger.error(f"创建自动发布配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/<config_id>', methods=['PUT'])
def update_auto_publish_config(config_id):
    """更新自动发布配置"""
    try:
        data = request.get_json()
        
        # 验证配置是否存在
        config = auto_publish_store.get_config(config_id)
        if not config:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        # 准备更新数据
        updates = {}
        if 'max_posts' in data:
            updates['max_posts'] = data['max_posts']
        if 'is_active' in data:
            updates['is_active'] = int(data['is_active'])
        if 'min_interval' in data:
            updates['min_interval'] = data['min_interval']
        if 'max_interval' in data:
            updates['max_interval'] = data['max_interval']
        if 'prompt_key' in data:
            updates['prompt_key'] = data['prompt_key']
        if 'publish_type' in data:
            updates['publish_type'] = data['publish_type']
        
        if not updates:
            return jsonify({'success': False, 'error': '没有提供更新数据'}), 400
        
        success = auto_publish_store.update_config(config_id, updates)
        if success:
            updated_config = auto_publish_store.get_config(config_id)
            
            # 添加话题信息
            topic_id = updated_config.get('topic_id')
            if topic_id:
                topic_data = topic_store.get_topic(topic_id)
                updated_config['topic_name'] = topic_data.get('name', '') if topic_data else ''
                updated_config['topic_group'] = topic_data.get('group_name', '') if topic_data else ''
            
            return jsonify({
                'success': True,
                'data': updated_config,
                'message': '配置更新成功'
            })
        else:
            return jsonify({'success': False, 'error': '更新配置失败'}), 500
            
    except Exception as e:
        logger.error(f"更新自动发布配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/<config_id>', methods=['DELETE'])
def delete_auto_publish_config(config_id):
    """删除自动发布配置"""
    try:
        # 验证配置是否存在
        config = auto_publish_store.get_config(config_id)
        if not config:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        success = auto_publish_store.delete_config(config_id)
        if success:
            return jsonify({
                'success': True,
                'message': '配置删除成功'
            })
        else:
            return jsonify({'success': False, 'error': '删除配置失败'}), 500
            
    except Exception as e:
        logger.error(f"删除自动发布配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/<config_id>/toggle', methods=['POST'])
def toggle_auto_publish_config(config_id):
    """切换自动发布配置状态"""
    try:
        data = request.get_json()
        is_active = data.get('is_active', True)
        
        # 验证配置是否存在
        config = auto_publish_store.get_config(config_id)
        if not config:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        success = auto_publish_store.toggle_config(config_id, is_active)
        if success:
            updated_config = auto_publish_store.get_config(config_id)
            
            # 添加话题信息
            topic_id = updated_config.get('topic_id')
            if topic_id:
                topic_data = topic_store.get_topic(topic_id)
                updated_config['topic_name'] = topic_data.get('name', '') if topic_data else ''
                updated_config['topic_group'] = topic_data.get('group_name', '') if topic_data else ''
            
            # 如果是激活配置，检查是否需要启动自动发布循环
            if is_active:
                # 检查该配置是否有待发布的内容（包括未到发布时间的）
                all_pending_posts = scheduled_posts_store.get_all_pending_posts()
                has_pending_for_config = any(
                    post.get('auto_publish_id') == config_id
                    for post in all_pending_posts
                )

                if not has_pending_for_config:
                    # 没有待发布内容，启动自动发布循环生成第一篇
                    logger.info(f"自动发布配置 {config_id} 激活时无待发布内容，启动生成循环")
                    
                    try:
                        from modules.auto_publish.generator import AutoPublishCycleGenerator
                        cycle_generator = AutoPublishCycleGenerator()
                        cycle_started = cycle_generator.start_auto_publish_cycle(config_id)
                        
                        if cycle_started:
                            logger.info(f"自动发布配置 {config_id} 启动成功，已生成第一篇内容")
                            message = f'配置已激活，已生成第一篇内容并安排发布'
                        else:
                            logger.warning(f"自动发布配置 {config_id} 启动失败")
                            message = f'配置已激活，但内容生成失败，请检查日志'
                    except Exception as e:
                        logger.error(f"启动自动发布循环失败: {e}")
                        message = f'配置已激活，但启动循环失败: {str(e)}'
                else:
                    logger.info(f"自动发布配置 {config_id} 激活时已有待发布内容，无需重新生成")
                    message = f'配置已激活，检测到已有待发布内容'
            else:
                message = f'配置已停用'
            
            return jsonify({
                'success': True,
                'data': updated_config,
                'message': message
            })
        else:
            return jsonify({'success': False, 'error': '切换配置状态失败'}), 500
            
    except Exception as e:
        logger.error(f"切换自动发布配置状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/<config_id>/reset', methods=['POST'])
def reset_auto_publish_posts(config_id):
    """重置自动发布配置的发布数量"""
    try:
        # 验证配置是否存在
        config = auto_publish_store.get_config(config_id)
        if not config:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        success = auto_publish_store.reset_posts(config_id)
        if success:
            updated_config = auto_publish_store.get_config(config_id)
            
            # 添加话题信息
            topic_id = updated_config.get('topic_id')
            if topic_id:
                topic_data = topic_store.get_topic(topic_id)
                updated_config['topic_name'] = topic_data.get('name', '') if topic_data else ''
                updated_config['topic_group'] = topic_data.get('group_name', '') if topic_data else ''
            
            return jsonify({
                'success': True,
                'data': updated_config,
                'message': '发布数量已重置'
            })
        else:
            return jsonify({'success': False, 'error': '重置发布数量失败'}), 500
            
    except Exception as e:
        logger.error(f"重置自动发布发布数量失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/publishable', methods=['GET'])
def get_publishable_configs():
    """获取可发布的自动发布配置"""
    try:
        configs = auto_publish_store.get_publishable_configs()
        
        # 为每个配置添加话题信息
        for config in configs:
            topic_id = config.get('topic_id')
            if topic_id:
                topic_data = topic_store.get_topic(topic_id)
                config['topic_name'] = topic_data.get('name', '') if topic_data else ''
                config['topic_group'] = topic_data.get('group_name', '') if topic_data else ''
        
        return jsonify({
            'success': True,
            'data': configs
        })
    except Exception as e:
        logger.error(f"获取可发布配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/conversation/<topic_id>', methods=['GET'])
def get_conversation_history(topic_id):
    """获取话题的AI对话历史"""
    try:
        conversations = auto_publish_store.get_conversation_history(topic_id)
        return jsonify({
            'success': True,
            'data': conversations
        })
    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auto-publish/conversation', methods=['POST'])
def save_conversation():
    """保存AI对话历史"""
    try:
        data = request.get_json()
        topic_id = data.get('topic_id')
        messages = data.get('messages', [])
        
        if not topic_id:
            return jsonify({'success': False, 'error': '话题ID不能为空'}), 400
        
        if not messages:
            return jsonify({'success': False, 'error': '对话消息不能为空'}), 400
        
        conversation_id = auto_publish_store.save_conversation(topic_id, messages)
        if conversation_id:
            return jsonify({
                'success': True,
                'data': {'conversation_id': conversation_id},
                'message': '对话历史保存成功'
            })
        else:
            return jsonify({'success': False, 'error': '保存对话历史失败'}), 500
            
    except Exception as e:
        logger.error(f"保存对话历史失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



# ===== AI配置管理API =====

@app.route('/api/ai-configs', methods=['GET'])
def get_ai_configs():
    """获取所有AI配置"""
    try:
        configs = ai_config_store.get_all_configs()
        return jsonify({
            'success': True, 
            'data': configs,
            'current_config_id': ai_config_store.get_current_config_id()
        })
    except Exception as e:
        logger.error(f"获取AI配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-configs', methods=['POST'])
def create_ai_config():
    """创建新的AI配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        config_id = ai_config_store.add_config(data)
        config = ai_config_store.get_config(config_id)
        
        return jsonify({
            'success': True, 
            'data': config,
            'config_id': config_id,
            'message': f'AI配置 "{data["name"]}" 创建成功'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"创建AI配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-configs/<config_id>', methods=['PUT'])
def update_ai_config(config_id):
    """更新AI配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '缺少请求数据'}), 400
        
        success = ai_config_store.update_config(config_id, data)
        if not success:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        config = ai_config_store.get_config(config_id)
        return jsonify({
            'success': True, 
            'data': config,
            'message': 'AI配置更新成功'
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"更新AI配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-configs/<config_id>', methods=['DELETE'])
def delete_ai_config(config_id):
    """删除AI配置"""
    try:
        success = ai_config_store.delete_config(config_id)
        if not success:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        return jsonify({
            'success': True, 
            'message': 'AI配置删除成功',
            'current_config_id': ai_config_store.get_current_config_id()
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"删除AI配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-configs/<config_id>/test', methods=['POST'])
def test_ai_config(config_id):
    """测试指定AI配置连接"""
    try:
        config_data = ai_config_store.get_config(config_id)
        if not config_data:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        if not config_data['enabled']:
            return jsonify({'success': False, 'error': '配置已被禁用'}), 400
            
        # 创建临时AI生成器测试连接
        temp_generator = AIContentGenerator(config_data)
        result = temp_generator.test_connection()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"测试AI配置连接失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai-configs/current', methods=['POST'])
def switch_ai_config():
    """切换当前使用的AI配置"""
    try:
        global current_ai_config_id, ai_generator
        
        data = request.get_json()
        if not data or 'config_id' not in data:
            return jsonify({'success': False, 'error': '缺少参数: config_id'}), 400
        
        config_id = data['config_id']
        success = ai_config_store.set_current_config(config_id)
        
        if not success:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
        # 更新全局变量
        current_ai_config_id = config_id
        current_config = ai_config_store.get_current_config()
        ai_generator = AIContentGenerator(current_config)
        
        logger.info(f"已切换AI配置到: {current_config['name']}")
        
        return jsonify({
            'success': True, 
            'message': f'已切换到 {current_config["name"]}',
            'current_config_id': config_id
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"切换AI配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """测试当前AI和脉脉API连接状态"""
    try:
        ai_result = ai_generator.test_connection()
        maimai_result = maimai_api.test_connection()
        current_config = ai_config_store.get_current_config()
        
        return jsonify({
            'success': True,
            'ai_connection': ai_result,
            'maimai_connection': maimai_result,
            'current_ai_config': current_config['name'] if current_config else 'Unknown'
        })
    except Exception as e:
        logger.error(f"测试连接异常：{str(e)}")
        return jsonify({'success': False, 'error': f'测试连接时发生错误：{str(e)}'}), 500


# ===== 提示词管理API =====

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    """获取所有提示词"""
    try:
        logger.info("API /api/prompts GET 被调用")
        
        prompts = prompt_store.load_prompts()
        
        return jsonify({'success': True, 'data': prompts})
    except Exception as e:
        logger.error(f"获取提示词失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prompts', methods=['POST'])
def save_prompts():
    """保存所有提示词"""
    try:
        data = request.get_json()
        if not data or 'prompts' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：prompts'}), 400
        
        prompts = data['prompts']
        if not isinstance(prompts, dict):
            return jsonify({'success': False, 'error': 'prompts必须是对象格式'}), 400
        
        success = prompt_store.save_prompts(prompts)
        if success:
            return jsonify({'success': True, 'message': '提示词保存成功'})
        else:
            return jsonify({'success': False, 'error': '保存失败'}), 500
            
    except Exception as e:
        logger.error(f"保存提示词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prompts/current', methods=['GET'])
def get_current_prompt():
    """获取当前选定的提示词"""
    try:
        current_key, current_content = prompt_store.get_current_prompt()
        return jsonify({
            'success': True, 
            'data': {
                'key': current_key,
                'content': current_content
            }
        })
    except Exception as e:
        logger.error(f"获取当前提示词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prompts/current', methods=['POST'])
def set_current_prompt():
    """设置当前选定的提示词"""
    try:
        data = request.get_json()
        if not data or 'key' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：key'}), 400
        
        prompt_key = data['key']
        
        # 检查提示词是否存在
        if not prompt_store.exists_prompt(prompt_key):
            return jsonify({'success': False, 'error': '指定的提示词不存在'}), 404
        
        success = prompt_store.set_current_prompt_key(prompt_key)
        if success:
            return jsonify({'success': True, 'message': f'已设置当前提示词: {prompt_key}'})
        else:
            return jsonify({'success': False, 'error': '设置失败'}), 500
            
    except Exception as e:
        logger.error(f"设置当前提示词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== 分组关键词管理API =====

@app.route('/api/group-keywords', methods=['GET'])
def get_group_keywords():
    """获取所有分组关键词"""
    try:
        keywords = group_keywords_store.get_all_group_keywords()
        return jsonify({'success': True, 'data': keywords})
    except Exception as e:
        logger.error(f"获取分组关键词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/group-keywords/<group_name>', methods=['GET'])
def get_group_keywords_by_name(group_name):
    """获取指定分组的关键词"""
    try:
        keywords = group_keywords_store.get_group_keywords(group_name)
        has_keywords = group_keywords_store.has_keywords(group_name)
        return jsonify({
            'success': True, 
            'data': {
                'group_name': group_name,
                'keywords': keywords,
                'has_keywords': has_keywords
            }
        })
    except Exception as e:
        logger.error(f"获取分组关键词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/group-keywords/<group_name>', methods=['PUT'])
def update_group_keywords(group_name):
    """更新分组的关键词"""
    try:
        data = request.get_json()
        if not data or 'keywords' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：keywords'}), 400
        
        keywords = data['keywords']
        if not isinstance(keywords, list):
            return jsonify({'success': False, 'error': 'keywords必须是数组格式'}), 400
        
        success = group_keywords_store.update_group_keywords(group_name, keywords)
        if success:
            return jsonify({'success': True, 'message': f'分组 "{group_name}" 关键词更新成功'})
        else:
            return jsonify({'success': False, 'error': '更新失败'}), 500
            
    except Exception as e:
        logger.error(f"更新分组关键词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/group-keywords/<group_name>/keywords', methods=['POST'])
def add_keyword_to_group(group_name):
    """为分组添加关键词"""
    try:
        data = request.get_json()
        if not data or 'keyword' not in data:
            return jsonify({'success': False, 'error': '缺少必需参数：keyword'}), 400
        
        keyword = data['keyword']
        if not isinstance(keyword, str) or not keyword.strip():
            return jsonify({'success': False, 'error': '关键词不能为空'}), 400
        
        success = group_keywords_store.add_keyword_to_group(group_name, keyword.strip())
        if success:
            return jsonify({'success': True, 'message': f'关键词 "{keyword.strip()}" 添加成功'})
        else:
            return jsonify({'success': False, 'error': '添加失败'}), 500
            
    except Exception as e:
        logger.error(f"添加关键词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/group-keywords/<group_name>/keywords/<keyword>', methods=['DELETE'])
def remove_keyword_from_group(group_name, keyword):
    """从分组中移除关键词"""
    try:
        success = group_keywords_store.remove_keyword_from_group(group_name, keyword)
        if success:
            return jsonify({'success': True, 'message': f'关键词 "{keyword}" 删除成功'})
        else:
            return jsonify({'success': False, 'error': '关键词不存在或删除失败'}), 404
            
    except Exception as e:
        logger.error(f"删除关键词失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("=== 脉脉自动发布系统启动 ===")
    logger.info(f"服务地址：http://localhost:{Config.PORT}")
    
    # 启动定时发布处理器
    try:
        scheduled_publisher.start()
        logger.info("定时发布后台任务已启动")
    except Exception as e:
        logger.error(f"启动定时发布处理器失败: {e}")
        exit(1)
    
    # 启动每日定时HTTP请求调度器
    try:
        daily_request_scheduler.start()
        logger.info("每日定时HTTP请求调度器已启动")
    except Exception as e:
        logger.error(f"启动每日定时HTTP请求调度器失败: {e}")
        # 注意：这里不退出程序，因为这是新功能，不应影响主功能
        logger.warning("每日定时HTTP请求功能可能无法正常工作")
    
    try:
        # 注册信号处理器以支持优雅关闭
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"收到退出信号 {signum}，正在优雅关闭...")
            scheduled_publisher.stop()
            daily_request_scheduler.stop()
            exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 启动Flask应用
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True,  # 显式启用多线程支持
            use_reloader=False  # 禁用自动重载以避免线程冲突
        )
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号...")
    except Exception as e:
        logger.error(f"Flask应用运行异常: {e}")
    finally:
        # 确保定时任务处理器被正确停止
        logger.info("正在清理资源...")
        try:
            scheduled_publisher.stop(timeout=15)
        except Exception as e:
            logger.error(f"停止定时发布处理器时出错: {e}")
        
        try:
            daily_request_scheduler.stop()
        except Exception as e:
            logger.error(f"停止每日定时HTTP请求调度器时出错: {e}")
        
        logger.info("所有后台任务已停止")
        logger.info("=== 脉脉自动发布系统已退出 ===")