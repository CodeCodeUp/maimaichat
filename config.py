import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # AI API配置
    AI_CONFIG = {
        "api_key": "sk-slUU3FYBuF4l2miWBqFS6Of7IsnUJYEtMjohcFjYrzTxk67t",
        "base_url": "https://veloera.wenwen12345.top/v1",
        "main_model": "claude-sonnet-4-20250514",
        "assistant_model": "gemini-2.5-flash-search"
    }
    
    # 脉脉API配置
    MAIMAI_CONFIG = {
        "base_url": "https://api.taou.com",
        "access_token": os.environ.get('MAIMAI_ACCESS_TOKEN', 'ec881ead60b43be8bea12b41e28e4454'),
        "device_params": {
            'version': '6.6.82',
            'ver_code': 'android_60682',
            'channel': 'Web',
            'vc': 'Android 9/28',
            'push_permit': '1',
            'net': 'wifi',
            'open': 'icon',
            'appid': '3',
            'device': 'OnePlus PJD110',
            'udid': 'c9b89d28-0765-4918-afdd-68be20cfdb3c',
            'is_push_open': '1',
            'isEmulator': '0',
            'rn_version': '0.69.0',
            'launched_by_user': '1',
            'android_id': 'b64f590c10c2c723',
            'oaid': 'NA',
            'hms_oaid': 'NA',
            'sm_dl': '0',
            'sm_did': 'DUEINujjJdNIUMUECt21d4vszLqZBtT9-ba4RFVFSU51ampKZE5JVU1VRUN0MjFkNHZzekxxWkJ0VDktYmE0c2h1',
            'u': '233201628',
            'webviewUserAgent': 'Mozilla/5.0 (Linux; Android 9; PJD110 Build/PQ3A.190605.06051204; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36',
            'density': '6.0',
            'screen_width': '2160',
            'screen_height': '3840'
        },
        "headers": {
            'User-Agent': '{OnePlus PJD110} [Android 9/28]/MaiMai 6.6.82(60682)',
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
            'Accept-Encoding': 'gzip',
            'x-maimai-reqid': '30e2bc243fac46539e909165121b99ee'
        }
    }
    
    # 默认提示词模板
    DEFAULT_PROMPTS = {
        "职场话题": "请根据以下话题生成一篇适合在脉脉发布的职场讨论文章，语言要贴近职场人士，内容要有深度和思考性：",
        "情感话题": "请根据以下话题生成一篇适合在脉脉发布的情感话题文章，语言要温暖真诚，能引起共鸣：",
        "生活话题": "请根据以下话题生成一篇适合在脉脉发布的生活分享文章，语言要轻松自然，贴近生活：",
        "自定义": ""
    }
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/app.log'
