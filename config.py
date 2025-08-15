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
        "api_key": "sk-RhixfnCsWWIK8N8tqXmuCItASYMRQhLG4Z1ZIYMmDfhcAPKq",
        "base_url": "https://tbai.xin/v1",
        "main_model": "gemini-2.5-pro-search",
        "assistant_model": "gemini-2.5-flash-search"
    }
    
    # 脉脉API配置（需要用户配置）
    MAIMAI_CONFIG = {
        "base_url": "https://maimai.cn/api",
        "access_token": os.environ.get('MAIMAI_ACCESS_TOKEN', ''),
        "user_agent": "MaimaiChat/1.0"
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
