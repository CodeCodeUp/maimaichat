import json
import os
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ScheduledPostsStore:
    """定时发布存储管理类"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.posts = {}
        self._ensure_file_exists()
        self.load()
    
    def _ensure_file_exists(self):
        """确保存储文件存在"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载定时发布数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.posts = json.load(f)
                logger.info(f"已加载 {len(self.posts)} 个定时发布任务")
        except Exception as e:
            logger.error(f"加载定时发布数据失败: {e}")
            self.posts = {}
            
    def save(self):
        """保存定时发布数据到文件"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.posts, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存 {len(self.posts)} 个定时发布任务")
        except Exception as e:
            logger.error(f"保存定时发布数据失败: {e}")
            raise
    
    def add_post(self, title: str, content: str, topic_url: str = None, 
                 topic_id: str = None, circle_type: str = None, topic_name: str = None) -> str:
        """添加定时发布任务，随机设置5-20分钟后发布"""
        post_id = str(uuid.uuid4())
        
        # 随机生成5-20分钟后的发布时间
        delay_minutes = random.randint(5, 20)
        scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
        
        post_data = {
            "id": post_id,
            "title": title,
            "content": content,
            "topic_url": topic_url,
            "topic_id": topic_id,
            "circle_type": circle_type,
            "topic_name": topic_name,  # 新增：保存话题名称
            "created_at": datetime.now().isoformat(),
            "scheduled_at": scheduled_at.isoformat(),
            "status": "pending"
        }
        
        self.posts[post_id] = post_data
        self.save()
        
        logger.info(f"已添加定时发布任务: {title} (预计 {delay_minutes} 分钟后发布)")
        return post_id
    
    def get_pending_posts(self) -> List[Dict]:
        """获取待发布的任务（已到发布时间）"""
        now = datetime.now()
        pending_posts = []
        
        for post_id, post_data in self.posts.items():
            if post_data["status"] == "pending":
                scheduled_time = datetime.fromisoformat(post_data["scheduled_at"])
                if now >= scheduled_time:
                    pending_posts.append(post_data)
        
        # 按照创建时间排序，先创建的先发布
        pending_posts.sort(key=lambda x: x["created_at"])
        return pending_posts
    
    def get_next_post_to_publish(self) -> Optional[Dict]:
        """获取下一个要发布的任务（只返回一个）"""
        pending_posts = self.get_pending_posts()
        return pending_posts[0] if pending_posts else None
    
    def mark_as_published(self, post_id: str) -> bool:
        """标记任务为已发布并删除"""
        if post_id in self.posts:
            post_data = self.posts[post_id]
            logger.info(f"任务 {post_data['title']} 发布成功，已删除")
            del self.posts[post_id]
            self.save()
            return True
        return False
    
    def mark_as_failed(self, post_id: str, error: str) -> bool:
        """标记任务为发布失败"""
        if post_id in self.posts:
            self.posts[post_id]["status"] = "failed"
            self.posts[post_id]["error"] = error
            self.posts[post_id]["failed_at"] = datetime.now().isoformat()
            self.save()
            logger.error(f"任务 {self.posts[post_id]['title']} 发布失败: {error}")
            return True
        return False
    
    def get_all_posts(self) -> List[Dict]:
        """获取所有定时发布任务"""
        posts_list = list(self.posts.values())
        # 按创建时间倒序排列
        posts_list.sort(key=lambda x: x["created_at"], reverse=True)
        return posts_list
    
    def get_pending_count(self) -> int:
        """获取待发布任务数量"""
        return len([p for p in self.posts.values() if p["status"] == "pending"])
    
    def delete_post(self, post_id: str) -> bool:
        """删除定时发布任务"""
        if post_id in self.posts:
            post_title = self.posts[post_id]["title"]
            del self.posts[post_id]
            self.save()
            logger.info(f"已删除定时发布任务: {post_title}")
            return True
        return False
    
    def update_post(self, post_id: str, title: str = None, content: str = None) -> bool:
        """更新定时发布任务"""
        if post_id not in self.posts:
            return False
        
        post = self.posts[post_id]
        updated = False
        
        if title is not None and post["title"] != title:
            post["title"] = title
            updated = True
        if content is not None and post["content"] != content:
            post["content"] = content
            updated = True
        
        if updated:
            post["updated_at"] = datetime.now().isoformat()
            self.save()
            logger.info(f"已更新定时发布任务: {post_id}")
            return True
        
        return False
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """获取单个定时发布任务"""
        return self.posts.get(post_id)
    
    def reschedule_post(self, post_id: str, delay_minutes: int = None) -> bool:
        """重新安排发布时间"""
        if post_id not in self.posts:
            return False
        
        if delay_minutes is None:
            delay_minutes = random.randint(5, 20)
        
        new_scheduled_at = datetime.now() + timedelta(minutes=delay_minutes)
        self.posts[post_id]["scheduled_at"] = new_scheduled_at.isoformat()
        self.posts[post_id]["status"] = "pending"
        
        if "error" in self.posts[post_id]:
            del self.posts[post_id]["error"]
        if "failed_at" in self.posts[post_id]:
            del self.posts[post_id]["failed_at"]
        
        self.save()
        logger.info(f"已重新安排任务发布时间: {self.posts[post_id]['title']} ({delay_minutes} 分钟后)")
        return True