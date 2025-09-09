import os
import logging
from modules.database.manager import init_database_manager
from modules.database.stores import *
from modules.scheduler.http_request import ScheduledRequestsStoreDB
from modules.scheduler.scheduled_posts import ScheduledPostsStoreDB
from modules.ai.config_store import AIConfigStoreDB
from modules.scheduler.daily_request import DailyRequestScheduler

logger = logging.getLogger(__name__)

def init_database_from_config():
    """从配置初始化数据库连接"""
    try:
        # 数据库配置
        db_config = {
            'host': '116.205.244.106',
            'port': 3306,
            'user': 'root',
            'password': '202358hjq',
            'database': 'maimaichat'
        }
        
        # 初始化数据库管理器
        db_manager = init_database_manager(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        
        # 创建数据库（如果不存在）
        db_manager.create_database_if_not_exists()
        
        # 测试连接
        if not db_manager.test_connection():
            raise Exception("数据库连接测试失败")
        
        logger.info("数据库连接初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def create_database_stores():
    """创建数据库版本的存储类实例"""
    try:
        # 初始化数据库连接
        if not init_database_from_config():
            raise Exception("数据库连接初始化失败")
        
        # 创建存储实例
        stores = {
            'ai_config_store': AIConfigStoreDB(),
            'scheduled_requests_store': ScheduledRequestsStoreDB(),
            'scheduled_posts_store': ScheduledPostsStoreDB(),
            'topic_store': TopicStoreDB(),
            'prompt_store': PromptStoreDB(),
            'group_keywords_store': GroupKeywordsStoreDB(),
            'auto_publish_store': AutoPublishStoreDB()
        }
        
        # 加载数据（兼容原接口）
        for name, store in stores.items():
            if hasattr(store, 'load'):
                store.load()
                logger.info(f"已初始化 {name}")
        
        return stores
        
    except Exception as e:
        logger.error(f"创建数据库存储实例失败: {e}")
        raise

def get_database_scheduler(scheduled_requests_store):
    """获取数据库版本的调度器"""
    return DailyRequestScheduler(scheduled_requests_store)