import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from modules.database.dao import ScheduledPostDAO

logger = logging.getLogger(__name__)

class ScheduledPostsStoreDB:
    """定时发布存储管理类 - 数据库版本"""
    
    def __init__(self):
        self.dao = ScheduledPostDAO()
        logger.info("初始化定时发布数据库存储")
    
    def load(self):
        """从数据库加载定时发布数据（兼容原接口）"""
        try:
            count = self.dao.count()
            logger.info(f"已加载 {count} 个定时发布任务")
        except Exception as e:
            logger.error(f"加载定时发布数据失败: {e}")
    
    def save(self):
        """保存定时发布数据到数据库（兼容原接口，实际无需操作）"""
        pass
    
    def add_post(self, title: str, content: str, topic_url: str = None, 
                 topic_id: str = None, circle_type: str = None, topic_name: str = None, 
                 auto_publish_id: str = None, publish_type: str = 'anonymous') -> str:
        """添加定时发布任务，基于最后一篇待发布时间计算发布时间"""
        post_id = str(uuid.uuid4())
        
        # 根据是否为自动发布，调整时间间隔计算
        if auto_publish_id:
            # 自动发布：30-60分钟随机间隔
            delay_minutes = random.randint(30, 60)
            logger.info(f"自动发布任务，随机延迟：{delay_minutes}分钟")
        else:
            # 手动发布：5-20分钟间隔
            delay_minutes = random.randint(5, 20)
            logger.info(f"手动发布任务，随机延迟：{delay_minutes}分钟")
        
        # 获取当前所有待发布任务的最晚发布时间
        latest_scheduled_time = self._get_latest_scheduled_time()
        
        if latest_scheduled_time:
            # 如果有待发布任务，从最晚的发布时间再加上延迟
            scheduled_at = latest_scheduled_time + timedelta(minutes=delay_minutes)
            logger.info(f"基于最后待发布时间计算：{latest_scheduled_time.strftime('%H:%M:%S')} + {delay_minutes}分钟")
        else:
            # 如果没有待发布任务，从当前时间开始计算
            scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
            logger.info(f"基于当前时间计算：{datetime.now().strftime('%H:%M:%S')} + {delay_minutes}分钟")
        
        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "topic_url": topic_url,
            "topic_id": topic_id,
            "circle_type": circle_type,
            "topic_name": topic_name,
            "publish_type": publish_type,
            "auto_publish_id": auto_publish_id,
            "scheduled_at": scheduled_at,
            "status": "pending"
        }
        
        try:
            self.dao.insert(post_data)
            logger.info(f"已添加定时发布任务: {title} (预计 {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')} 发布)")
            return post_id
        except Exception as e:
            logger.error(f"添加定时发布任务失败: {e}")
            raise
    
    def _get_latest_scheduled_time(self) -> Optional[datetime]:
        """获取所有待发布任务中最晚的发布时间"""
        try:
            pending_posts = self.dao.find_all({'status': 'pending'}, 'scheduled_at DESC', 1)
            if pending_posts:
                scheduled_at_str = pending_posts[0]['scheduled_at']
                if isinstance(scheduled_at_str, datetime):
                    return scheduled_at_str
                elif isinstance(scheduled_at_str, str):
                    return datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
            return None
        except Exception as e:
            logger.error(f"获取最晚发布时间失败: {e}")
            return None
    
    def get_pending_posts(self) -> List[Dict]:
        """获取待发布的任务（已到发布时间）"""
        try:
            return self.dao.find_pending_posts()
        except Exception as e:
            logger.error(f"获取待发布任务失败: {e}")
            return []
    
    def get_next_post_to_publish(self) -> Optional[Dict]:
        """获取下一个要发布的任务（只返回一个）"""
        try:
            return self.dao.get_next_post_to_publish()
        except Exception as e:
            logger.error(f"获取下一个发布任务失败: {e}")
            return None
    
    def mark_as_published(self, post_id: str) -> bool:
        """标记任务为已发布并删除，如果是自动发布任务则触发下一轮循环"""
        try:
            post = self.dao.find_by_id(post_id)
            if post:
                # 检查是否是自动发布任务
                auto_publish_id = post.get('auto_publish_id')
                
                result = self.dao.mark_as_published(post_id)
                if result:
                    logger.info(f"任务 {post['title']} 发布成功，已删除")
                    
                    # 如果是自动发布任务，触发下一轮生成
                    if auto_publish_id:
                        self._trigger_next_auto_publish_cycle(auto_publish_id)
                
                return result
            return False
        except Exception as e:
            logger.error(f"标记任务为已发布失败: {e}")
            return False
    
    def _trigger_next_auto_publish_cycle(self, auto_publish_id: str):
        """触发下一轮自动发布循环"""
        try:
            from modules.auto_publish.generator import AutoPublishCycleGenerator
            cycle_generator = AutoPublishCycleGenerator()
            
            # 先增加已发布数量
            from modules.database.dao import AutoPublishConfigDAO
            auto_config_dao = AutoPublishConfigDAO()
            auto_config_dao.increment_posts(auto_publish_id)
            
            # 继续自动发布循环
            success = cycle_generator.continue_auto_publish_cycle(auto_publish_id)
            if success:
                logger.info(f"已触发自动发布配置 {auto_publish_id} 的下一轮循环")
            else:
                logger.warning(f"触发自动发布配置 {auto_publish_id} 下一轮循环失败")
                
        except Exception as e:
            logger.error(f"触发下一轮自动发布循环失败: {e}")
    
    def mark_as_failed(self, post_id: str, error: str) -> bool:
        """标记任务为发布失败"""
        try:
            post = self.dao.find_by_id(post_id)
            if post:
                result = self.dao.mark_as_failed(post_id, error)
                if result:
                    logger.error(f"任务 {post['title']} 发布失败: {error}")
                return result
            return False
        except Exception as e:
            logger.error(f"标记任务为失败失败: {e}")
            return False
    
    def get_all_posts(self) -> List[Dict]:
        """获取所有定时发布任务"""
        try:
            return self.dao.find_all(order_by='created_at DESC')
        except Exception as e:
            logger.error(f"获取所有发布任务失败: {e}")
            return []
    
    def get_pending_count(self) -> int:
        """获取待发布任务数量"""
        try:
            return self.dao.get_pending_count()
        except Exception as e:
            logger.error(f"获取待发布任务数量失败: {e}")
            return 0
    
    def delete_post(self, post_id: str) -> bool:
        """删除定时发布任务"""
        try:
            post = self.dao.find_by_id(post_id)
            if post:
                result = self.dao.delete(post_id) > 0
                if result:
                    logger.info(f"已删除定时发布任务: {post['title']}")
                return result
            return False
        except Exception as e:
            logger.error(f"删除发布任务失败: {e}")
            return False
    
    def update_post(self, post_id: str, title: str = None, content: str = None) -> bool:
        """更新定时发布任务"""
        try:
            update_data = {}
            if title is not None:
                update_data['title'] = title
            if content is not None:
                update_data['content'] = content
            
            if update_data:
                result = self.dao.update(post_id, update_data) > 0
                if result:
                    logger.info(f"已更新定时发布任务: {post_id}")
                return result
            return False
        except Exception as e:
            logger.error(f"更新发布任务失败: {e}")
            return False
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """获取单个定时发布任务"""
        try:
            return self.dao.find_by_id(post_id)
        except Exception as e:
            logger.error(f"获取发布任务失败: {e}")
            return None
    
    def reschedule_post(self, post_id: str, delay_minutes: int = None) -> bool:
        """重新安排发布时间，保持队列顺序"""
        try:
            if delay_minutes is None:
                delay_minutes = random.randint(5, 20)
            
            # 获取当前所有待发布任务的最晚发布时间（排除当前要重新安排的任务）
            latest_scheduled_time = None
            pending_posts = self.dao.find_all({'status': 'pending'})
            
            for post_data in pending_posts:
                if post_data['id'] != post_id:
                    scheduled_time_str = post_data['scheduled_at']
                    if isinstance(scheduled_time_str, datetime):
                        scheduled_time = scheduled_time_str
                    else:
                        scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                    
                    if latest_scheduled_time is None or scheduled_time > latest_scheduled_time:
                        latest_scheduled_time = scheduled_time
            
            if latest_scheduled_time:
                # 如果还有其他待发布任务，排在最后
                new_scheduled_at = latest_scheduled_time + timedelta(minutes=delay_minutes)
                logger.info(f"重新安排任务排队：基于最后任务时间 {latest_scheduled_time.strftime('%H:%M:%S')} + {delay_minutes}分钟")
            else:
                # 如果没有其他待发布任务，从当前时间开始
                new_scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
                logger.info(f"重新安排任务：基于当前时间 + {delay_minutes}分钟")
            
            result = self.dao.reschedule_post(post_id, new_scheduled_at)
            if result:
                post = self.dao.find_by_id(post_id)
                if post:
                    logger.info(f"已重新安排任务发布时间: {post['title']} ({new_scheduled_at.strftime('%Y-%m-%d %H:%M:%S')})")
            return result
            
        except Exception as e:
            logger.error(f"重新安排发布时间失败: {e}")
            return False