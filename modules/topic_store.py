import json
import os
import uuid
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TopicStore:
    """话题存储管理类"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.topics = {}
        self._ensure_file_exists()
        self.load()
    
    def _ensure_file_exists(self):
        """确保存储文件存在"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载话题数据"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.topics = json.load(f)
                logger.info(f"已加载 {len(self.topics)} 个话题")
        except Exception as e:
            logger.error(f"加载话题数据失败: {e}")
            self.topics = {}
    
    def save(self):
        """保存话题数据到文件"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.topics, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存 {len(self.topics)} 个话题")
        except Exception as e:
            logger.error(f"保存话题数据失败: {e}")
            raise
    
    def add_topic(self, name: str, circle_type: str, topic_id: str) -> str:
        """添加话题，topic_id为必填参数"""
        if not topic_id:
            raise ValueError("话题ID不能为空")
        
        if topic_id in self.topics:
            raise ValueError(f"话题ID {topic_id} 已存在")
        
        topic_data = {
            "id": topic_id,
            "name": name,
            "circle_type": circle_type,
            "created_at": self._get_timestamp(),
            "updated_at": self._get_timestamp()
        }
        
        self.topics[topic_id] = topic_data
        self.save()
        logger.info(f"已添加话题: {name} (ID: {topic_id})")
        return topic_id
    
    def update_topic(self, topic_id: str, name: str = None, circle_type: str = None) -> bool:
        """更新话题"""
        if topic_id not in self.topics:
            return False
        
        topic = self.topics[topic_id]
        if name is not None:
            topic["name"] = name
        if circle_type is not None:
            topic["circle_type"] = circle_type
        topic["updated_at"] = self._get_timestamp()
        
        self.save()
        logger.info(f"已更新话题: {topic_id}")
        return True
    
    def delete_topic(self, topic_id: str) -> bool:
        """删除话题"""
        if topic_id not in self.topics:
            return False
        
        del self.topics[topic_id]
        self.save()
        logger.info(f"已删除话题: {topic_id}")
        return True
    
    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """获取单个话题"""
        return self.topics.get(topic_id)
    
    def get_all_topics(self) -> List[Dict]:
        """获取所有话题"""
        return list(self.topics.values())
    
    def search_topics(self, keyword: str) -> List[Dict]:
        """搜索话题"""
        keyword = keyword.lower()
        results = []
        for topic in self.topics.values():
            if (keyword in topic["name"].lower() or 
                keyword in topic["circle_type"].lower()):
                results.append(topic)
        return results
    
    def batch_add_topics(self, topics_data: List[Dict]) -> Dict:
        """批量添加话题"""
        results = {
            "success": [],
            "failed": [],
            "skipped": []
        }
        
        for topic_data in topics_data:
            try:
                # 提取必要字段
                topic_id = topic_data.get('id', '').strip()
                name = topic_data.get('name', '').strip()
                circle_type = str(topic_data.get('circle_type', '')).strip()
                
                if not topic_id or not name or not circle_type:
                    results["failed"].append({
                        "data": topic_data,
                        "error": "缺少必要字段：id, name 或 circle_type"
                    })
                    continue
                
                # 检查是否已存在
                if topic_id in self.topics:
                    results["skipped"].append({
                        "data": topic_data,
                        "reason": f"话题ID {topic_id} 已存在"
                    })
                    continue
                
                # 添加话题
                self.add_topic(name, circle_type, topic_id)
                results["success"].append({
                    "id": topic_id,
                    "name": name,
                    "circle_type": circle_type
                })
                
            except Exception as e:
                results["failed"].append({
                    "data": topic_data,
                    "error": str(e)
                })
        
        logger.info(f"批量添加完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, 跳过 {len(results['skipped'])} 个")
        return results
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()