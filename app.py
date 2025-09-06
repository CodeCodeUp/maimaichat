from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
import os
from datetime import datetime
from config import Config
from modules.ai_generator import AIContentGenerator
from modules.maimai_api import MaimaiAPI

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

# 初始化AI配置存储
from modules.ai_config_store import AIConfigStore
AI_CONFIG_FILE = os.path.join('data', 'ai_configs.json')
ai_config_store = AIConfigStore(AI_CONFIG_FILE)

# 初始化AI生成器和脉脉API
current_ai_config_id = ai_config_store.get_current_config_id()
current_config = ai_config_store.get_current_config()
ai_generator = AIContentGenerator(current_config)
maimai_api = MaimaiAPI(Config.MAIMAI_CONFIG)

# 初始化话题存储
from modules.topic_store import TopicStore
TOPIC_FILE = os.path.join('data', 'topics.json')
topic_store = TopicStore(TOPIC_FILE)

# 初始化定时发布存储
from modules.scheduled_posts import ScheduledPostsStore
SCHEDULED_POSTS_FILE = os.path.join('data', 'scheduled_posts.json')
scheduled_posts_store = ScheduledPostsStore(SCHEDULED_POSTS_FILE)

# 初始化定时发布处理器
from modules.scheduler import ScheduledPublisher
scheduled_publisher = ScheduledPublisher(scheduled_posts_store, maimai_api)

# 初始化提示词存储
from modules.simple_prompt_store import PromptStore
PROMPT_FILE = os.path.join('data', 'prompts.json')
prompt_store = PromptStore(PROMPT_FILE)

# 初始化分组关键词存储
from modules.group_keywords_store import GroupKeywordsStore
GROUP_KEYWORDS_FILE = os.path.join('data', 'group_keywords.json')
group_keywords_store = GroupKeywordsStore(GROUP_KEYWORDS_FILE)


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
        logger.info("开始对话生成，消息数：%d", len(messages))
        result = ai_generator.chat(messages=messages, use_main_model=use_main_model)

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

        logger.info(f"开始发布内容：{title}")

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
                topic_name=topic_name
            )
        elif topic_url:
            # 使用话题链接提取
            logger.info(f"使用话题链接：{topic_url}")
            result = maimai_api.publish_content(
                title=title,
                content=content,
                topic_url=topic_url
            )
        else:
            # 无话题发布
            logger.info("无话题发布")
            result = maimai_api.publish_content(
                title=title,
                content=content
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
        
        new_id = topic_store.add_topic(name, circle_type, topic_id, group=group)
        topic = topic_store.get_topic(new_id)
        
        return jsonify({'success': True, 'data': topic})
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
        groups = topic_store.get_all_groups()
        return jsonify({'success': True, 'data': groups})
    except Exception as e:
        logger.error(f"获取分组列表失败: {e}")
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

        logger.info(f"添加定时发布任务：{title}")

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
            topic_name=topic_name  # 新增：保存话题名称
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
        config = ai_config_store.get_all_configs()[config_id]
        
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
        
        config = ai_config_store.get_all_configs()[config_id]
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
        prompts = prompt_store.load_prompts()
        return jsonify({'success': True, 'data': prompts})
    except Exception as e:
        logger.error(f"获取提示词失败: {e}")
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
    
    try:
        # 注册信号处理器以支持优雅关闭
        import signal
        
        def signal_handler(signum, frame):
            logger.info(f"收到退出信号 {signum}，正在优雅关闭...")
            scheduled_publisher.stop()
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
        logger.info("定时发布后台任务已停止")
        logger.info("=== 脉脉自动发布系统已退出 ===")