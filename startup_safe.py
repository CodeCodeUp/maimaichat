#!/usr/bin/env python3
"""
安全启动脚本 - 解决 OSError [WinError 10038] 问题
专门为Windows环境优化的启动方式
"""
import sys
import os
import logging
import atexit
from threading import Event
import signal

# 设置工作目录为脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
os.chdir(script_dir)

from config import Config
from modules.scheduler.publisher import ScheduledPublisher
from modules.scheduler.scheduled_posts import ScheduledPostsStore
from modules.maimai.api import MaimaiAPI

# 创建全局关闭事件
shutdown_event = Event()
scheduled_publisher = None

def setup_logging():
    """配置日志系统"""
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

def cleanup_resources():
    """清理资源函数"""
    global scheduled_publisher
    logger = logging.getLogger(__name__)
    
    if scheduled_publisher:
        logger.info("正在停止定时发布处理器...")
        try:
            scheduled_publisher.stop(timeout=10)
            logger.info("定时发布处理器已停止")
        except Exception as e:
            logger.error(f"停止定时发布处理器时发生错误: {e}")

def signal_handler(signum, frame):
    """信号处理函数"""
    logger = logging.getLogger(__name__)
    logger.info(f"收到退出信号 {signum}")
    shutdown_event.set()
    cleanup_resources()
    sys.exit(0)

def main():
    """主函数"""
    global scheduled_publisher
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== 脉脉自动发布系统安全启动 ===")
    logger.info(f"Python版本: {sys.version}")
    logger.info(f"工作目录: {os.getcwd()}")
    
    # 注册清理函数
    atexit.register(cleanup_resources)
    
    # 注册信号处理器（Windows兼容）
    try:
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    except Exception as e:
        logger.warning(f"注册信号处理器失败: {e}")
    
    try:
        # 初始化组件
        logger.info("初始化系统组件...")
        
        SCHEDULED_POSTS_FILE = os.path.join('data', 'scheduled_posts.json')
        scheduled_posts_store = ScheduledPostsStore(SCHEDULED_POSTS_FILE)
        maimai_api = MaimaiAPI(Config.MAIMAI_CONFIG)
        scheduled_publisher = ScheduledPublisher(scheduled_posts_store, maimai_api)
        
        # 启动定时发布处理器
        scheduled_publisher.start()
        logger.info("定时发布处理器已启动")
        
        # 导入并启动Flask应用（延迟导入避免循环依赖）
        from app import app
        
        logger.info(f"启动Flask服务器: http://{Config.HOST}:{Config.PORT}")
        
        # 使用生产级服务器配置
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=False,  # 生产环境禁用debug
            threaded=True,
            use_reloader=False,
            processes=1  # 单进程多线程模式
        )
        
    except KeyboardInterrupt:
        logger.info("收到键盘中断信号")
        shutdown_event.set()
    except Exception as e:
        logger.error(f"系统运行异常: {e}", exc_info=True)
    finally:
        cleanup_resources()
        logger.info("=== 系统已安全退出 ===")

if __name__ == '__main__':
    main()