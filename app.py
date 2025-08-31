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

# 初始化AI生成器和脉脉API
ai_generator = AIContentGenerator(Config.AI_CONFIG)
maimai_api = MaimaiAPI(Config.MAIMAI_CONFIG)

# 初始化话题存储
from modules.topic_store import TopicStore
TOPIC_FILE = os.path.join('data', 'topics.json')
topic_store = TopicStore(TOPIC_FILE)


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

        # 支持两种模式：
        # 1) 旧版：传入topic/custom_prompt
        # 2) 新版：传入messages数组
        use_main_model = data.get('use_main_model', True)

        if 'messages' in data:
            messages = data['messages']
            if not isinstance(messages, list) or not all('role' in m and 'content' in m for m in messages):
                return jsonify({'success': False, 'error': 'messages格式不正确'}), 400
            logger.info("开始对话生成，消息数：%d", len(messages))
            result = ai_generator.chat(messages=messages, use_main_model=use_main_model)
        else:
            if 'topic' not in data:
                return jsonify({'success': False, 'error': '缺少必需参数：topic 或 messages'}), 400
            topic = data['topic']
            custom_prompt = data.get('custom_prompt', '')
            logger.info(f"开始生成内容，主题：{topic}")
            result = ai_generator.generate_content(topic=topic, custom_prompt=custom_prompt, use_main_model=use_main_model)

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
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需参数：title 或 content'
            }), 400

        title = data['title']
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
        
        return jsonify({'success': True, 'message': f"分组 '{name}' 删除成功"})
    except Exception as e:
        logger.error(f"删除分组失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    logger.info("=== 脉脉自动发布系统启动 ===")
    logger.info(f"服务地址：http://localhost:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )