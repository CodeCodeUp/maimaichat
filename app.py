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

# 提示词存储
from modules.prompt_store import PromptStore
PROMPT_FILE = os.path.join('logs', 'prompts.json')
prompt_store = PromptStore(PROMPT_FILE, Config.DEFAULT_PROMPTS)
# 历史与草稿存储
from modules.storage import ChatStore, DraftStore
CHAT_FILE = os.path.join('data', 'chats.json')
DRAFT_FILE = os.path.join('data', 'drafts.json')
chat_store = ChatStore(CHAT_FILE)
draft_store = DraftStore(DRAFT_FILE)


@app.route('/')
def index():
    """主页"""
    return send_from_directory('static', 'index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'ai_models': {
                    'main': Config.AI_CONFIG['main_model'],
                    'assistant': Config.AI_CONFIG['assistant_model']
                }
            }
        })
    except Exception as e:
        logger.error(f"获取配置失败：{str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    try:
        return jsonify({'success': True, 'data': prompt_store.get_all()})
    except Exception as e:
        logger.error(f"获取提示词失败：{e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prompts', methods=['POST'])
def update_prompts():
    try:
        data = request.get_json()
        if not data or 'prompts' not in data:
            return jsonify({'success': False, 'error': '缺少prompts'}), 400
        updated = prompt_store.update(data['prompts'])
        return jsonify({'success': True, 'data': updated})
    except Exception as e:
        logger.error(f"更新提示词失败：{e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        logger.error(f"获取配置失败：{str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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

        logger.info(f"开始发布内容：{title}")

        # 调用脉脉API发布
        result = maimai_api.publish_content(
            title=title,
            content=content,
            topic_url=topic_url
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"发布内容异常：{str(e)}")
        return jsonify({
            'success': False,
            'error': f'发布内容时发生错误：{str(e)}'
        }), 500

# ===== Chat Persistence APIs =====
@app.route('/api/chats', methods=['GET'])
def list_chats():
    return jsonify({'success': True, 'data': chat_store.list()})

@app.route('/api/chats/<chat_id>', methods=['GET'])
def get_chat(chat_id):
    data = chat_store.get(chat_id)
    if not data:
        return jsonify({'success': False, 'error': 'Chat not found'}), 404
    return jsonify({'success': True, 'data': {'id': chat_id, **data}})

@app.route('/api/chats', methods=['POST'])
def save_chat():
    payload = request.get_json() or {}
    chat_id = payload.get('id')
    if 'messages' not in payload:
        return jsonify({'success': False, 'error': '缺少messages'}), 400
    new_id_val = chat_store.save(chat_id, payload)
    return jsonify({'success': True, 'id': new_id_val})

@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    chat_store.delete(chat_id)
    return jsonify({'success': True})

# ===== Draft Persistence APIs =====
@app.route('/api/drafts', methods=['GET'])
def list_drafts():
    return jsonify({'success': True, 'data': draft_store.list()})

@app.route('/api/drafts/<draft_id>', methods=['GET'])
def get_draft(draft_id):
    data = draft_store.get(draft_id)
    if not data:
        return jsonify({'success': False, 'error': 'Draft not found'}), 404
    return jsonify({'success': True, 'data': {'id': draft_id, **data}})

@app.route('/api/drafts', methods=['POST'])
def save_draft():
    payload = request.get_json() or {}
    draft_id = payload.get('id')
    if 'title' not in payload and 'content' not in payload:
        return jsonify({'success': False, 'error': '缺少草稿内容'}), 400
    new_id_val = draft_store.save(draft_id, payload)
    return jsonify({'success': True, 'id': new_id_val})

@app.route('/api/drafts/<draft_id>', methods=['DELETE'])
def delete_draft(draft_id):
    draft_store.delete(draft_id)
    return jsonify({'success': True})

@app.route('/api/test-connection', methods=['POST'])
def test_connections():
    """测试API连接"""
    try:
        data = request.get_json()
        test_type = data.get('type', 'all')  # 'ai', 'maimai', 'all'

        results = {}

        if test_type in ['ai', 'all']:
            logger.info("测试AI API连接")
            results['ai'] = ai_generator.test_connection()

        if test_type in ['maimai', 'all']:
            logger.info("测试脉脉API连接")
            results['maimai'] = maimai_api.test_connection()

        return jsonify({
            'success': True,
            'results': results
        })

    except Exception as e:
        logger.error(f"测试连接异常：{str(e)}")
        return jsonify({
            'success': False,
            'error': f'测试连接时发生错误：{str(e)}'
        }), 500

@app.route('/api/topic-info', methods=['POST'])
def get_topic_info():
    """获取话题信息"""
    try:
        data = request.get_json()

        if not data or 'topic_url' not in data:
            return jsonify({
                'success': False,
                'error': '缺少必需参数：topic_url'
            }), 400

        topic_url = data['topic_url']

        logger.info(f"获取话题信息：{topic_url}")

        result = maimai_api.get_topic_info(topic_url)

        return jsonify(result)

    except Exception as e:
        logger.error(f"获取话题信息异常：{str(e)}")
        return jsonify({
            'success': False,
            'error': f'获取话题信息时发生错误：{str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '页面未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    logger.error(f"服务器内部错误：{str(error)}")
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    logger.info("启动脉脉自动发布系统")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )
