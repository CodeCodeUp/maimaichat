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

        logger.info(f"开始发布内容：{title}")

        # 调用脉脉API发布
        result = maimai_api.publish_content(
            title=title,
            content=content,
            topic_url=topic_url
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


if __name__ == '__main__':
    logger.info("=== 脉脉自动发布系统启动 ===")
    logger.info(f"服务地址：http://localhost:{Config.PORT}")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )