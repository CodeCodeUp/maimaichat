import threading
import time
import logging
from datetime import datetime
from modules.scheduled_posts import ScheduledPostsStore
from modules.maimai_api import MaimaiAPI

logger = logging.getLogger(__name__)

class ScheduledPublisher:
    """定时发布任务处理器"""
    
    def __init__(self, scheduled_posts_store: ScheduledPostsStore, maimai_api: MaimaiAPI):
        self.scheduled_posts_store = scheduled_posts_store
        self.maimai_api = maimai_api
        self.running = False
        self.thread = None
        self.check_interval = 30  # 每30秒检查一次
    
    def start(self):
        """启动定时任务处理器"""
        if self.running:
            logger.warning("定时发布处理器已在运行中")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("定时发布处理器已启动")
    
    def stop(self):
        """停止定时任务处理器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("定时发布处理器已停止")
    
    def _run_scheduler(self):
        """定时任务主循环"""
        logger.info("定时发布处理器开始运行")
        
        while self.running:
            try:
                self._process_pending_posts()
            except Exception as e:
                logger.error(f"定时发布处理异常: {e}")
            
            # 等待下次检查
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)
        
        logger.info("定时发布处理器已退出")
    
    def _process_pending_posts(self):
        """处理待发布的任务"""
        # 获取下一个要发布的任务（只获取一个）
        post_to_publish = self.scheduled_posts_store.get_next_post_to_publish()
        
        if not post_to_publish:
            return
        
        post_id = post_to_publish['id']
        title = post_to_publish['title']
        content = post_to_publish['content']
        topic_url = post_to_publish.get('topic_url', '')
        topic_id = post_to_publish.get('topic_id', '')
        circle_type = post_to_publish.get('circle_type', '')
        topic_name = post_to_publish.get('topic_name', '')  # 新增：获取话题名称
        
        logger.info(f"开始发布定时任务: {title}")
        
        try:
            # 调用脉脉API发布，完全复制正常发布的逻辑
            if topic_id and circle_type:
                # 使用话题ID、圈子类型和话题名称
                result = self.maimai_api.publish_content(
                    title=title,
                    content=content,
                    topic_id=topic_id,
                    circle_type=circle_type,
                    topic_name=topic_name  # 新增：传递话题名称
                )
                logger.info(f"使用选择的话题发布: ID={topic_id}, Name={topic_name}, CircleType={circle_type}")
            elif topic_url:
                # 使用话题链接
                result = self.maimai_api.publish_content(
                    title=title,
                    content=content,
                    topic_url=topic_url
                )
                logger.info(f"使用话题链接发布: {topic_url}")
            else:
                # 无话题发布
                result = self.maimai_api.publish_content(
                    title=title,
                    content=content
                )
                logger.info("无话题发布")
            
            if result['success']:
                # 发布成功，删除任务
                self.scheduled_posts_store.mark_as_published(post_id)
                logger.info(f"定时任务发布成功并已删除: {title}")
            else:
                # 发布失败，标记为失败状态
                error_msg = result.get('error', 'Unknown error')
                self.scheduled_posts_store.mark_as_failed(post_id, error_msg)
                logger.error(f"定时任务发布失败: {title}, 错误: {error_msg}")
                
        except Exception as e:
            # 发布异常，标记为失败状态
            error_msg = str(e)
            self.scheduled_posts_store.mark_as_failed(post_id, error_msg)
            logger.error(f"定时任务发布异常: {title}, 错误: {error_msg}")
    
    def get_status(self):
        """获取处理器状态"""
        return {
            'running': self.running,
            'pending_count': self.scheduled_posts_store.get_pending_count(),
            'check_interval': self.check_interval
        }