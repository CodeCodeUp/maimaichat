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
        self.groups = {}  # 新增: 用于存储分组信息
        self._ensure_file_exists()
        self.load()
    
    def _ensure_file_exists(self):
        """确保存储文件存在，并使用新的数据结构"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                # 初始化为新的数据结构
                json.dump({"topics": {}, "groups": {}}, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载话题数据，并处理旧格式到新格式的迁移"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 检查是否是旧格式（顶层是字典且不包含 'topics' 和 'groups' 键）
                if isinstance(data, dict) and 'topics' not in data and 'groups' not in data:
                    self.topics = data
                    self.groups = {}
                    logger.info("检测到旧版话题数据格式，将自动迁移。")
                    self.save()  # 保存为新格式
                else:
                    self.topics = data.get('topics', {})
                    self.groups = data.get('groups', {})
                
                logger.info(f"已加载 {len(self.topics)} 个话题和 {len(self.groups)} 个分组")
        except Exception as e:
            logger.error(f"加载话题数据失败: {e}")
            self.topics = {}
            self.groups = {}
            
    def save(self):
        """保存话题和分组数据到文件"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                # 保存为新的数据结构
                data_to_save = {
                    "topics": self.topics,
                    "groups": self.groups
                }
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存 {len(self.topics)} 个话题和 {len(self.groups)} 个分组")
        except Exception as e:
            logger.error(f"保存话题数据失败: {e}")
            raise
    
    def add_topic(self, name: str, circle_type: str, topic_id: str, group: Optional[str] = None) -> str:
        """添加话题，并可选择性地加入分组"""
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
        
        if group:
            if group not in self.groups:
                self.groups[group] = []
            if topic_id not in self.groups[group]:
                self.groups[group].append(topic_id)
        
        self.save()
        logger.info(f"已添加话题: {name} (ID: {topic_id}) 到分组 '{group or '未分组'}'")
        return topic_id
    
    def update_topic(self, topic_id: str, name: str = None, circle_type: str = None, group: Optional[str] = None) -> bool:
        """更新话题，并支持修改分组"""
        if topic_id not in self.topics:
            return False
        
        topic = self.topics[topic_id]
        updated = False

        if name is not None and topic["name"] != name:
            topic["name"] = name
            updated = True
        if circle_type is not None and topic["circle_type"] != circle_type:
            topic["circle_type"] = circle_type
            updated = True
        
        # 更新分组逻辑
        if group is not None:
            # 从旧分组移除
            for g, topic_ids in self.groups.items():
                if topic_id in topic_ids:
                    topic_ids.remove(topic_id)
                    # 如果分组为空，可以选择删除该分组
                    # if not self.groups[g]:
                    #     del self.groups[g]
                    break
            
            # 添加到新分组
            if group:  # 如果提供了新分组名称
                if group not in self.groups:
                    self.groups[group] = []
                if topic_id not in self.groups[group]:
                    self.groups[group].append(topic_id)
            updated = True

        if updated:
            topic["updated_at"] = self._get_timestamp()
            self.save()
            logger.info(f"已更新话题: {topic_id}")
            return True
            
        return False
    
    def delete_topic(self, topic_id: str) -> bool:
        """删除话题，并从所有分组中移除"""
        if topic_id not in self.topics:
            return False
        
        del self.topics[topic_id]
        
        # 从分组中移除
        for group_name in list(self.groups.keys()):
            if topic_id in self.groups[group_name]:
                self.groups[group_name].remove(topic_id)
                if not self.groups[group_name]:  # 如果分组为空，则删除该分组
                    del self.groups[group_name]
        
        self.save()
        logger.info(f"已删除话题: {topic_id}")
        return True
    
    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """获取单个话题，并附带其分组信息"""
        topic = self.topics.get(topic_id)
        if topic:
            topic['group'] = self.get_topic_group(topic_id)
        return topic
    
    def get_topic_group(self, topic_id: str) -> Optional[str]:
        """查找指定话题ID所在的分组"""
        for group_name, topic_ids in self.groups.items():
            if topic_id in topic_ids:
                return group_name
        return None

    def get_all_topics(self) -> Dict:
        """获取所有话题，按分组进行组织"""
        grouped_topics = {group: [] for group in self.groups}
        grouped_topics["未分组"] = []
        
        all_topic_ids_in_groups = {tid for tids in self.groups.values() for tid in tids}

        for topic_id, topic in self.topics.items():
            # 为每个话题动态添加分组信息
            topic_with_group = topic.copy()
            group_name = self.get_topic_group(topic_id)
            topic_with_group['group'] = group_name

            if topic_id in all_topic_ids_in_groups:
                # 找到它所在的分组
                for group, topic_ids in self.groups.items():
                    if topic_id in topic_ids:
                        grouped_topics[group].append(topic_with_group)
                        break
            else:
                grouped_topics["未分组"].append(topic_with_group)
        
        # 移除值为空列表的未分组键
        if not grouped_topics["未分组"]:
            del grouped_topics["未分组"]
            
        return grouped_topics

    def search_topics(self, keyword: str) -> List[Dict]:
        """搜索话题，并在结果中包含分组信息"""
        keyword = keyword.lower()
        results = []
        for topic in self.topics.values():
            if (keyword in topic["name"].lower() or 
                keyword in topic["circle_type"].lower()):
                # 为每个话题动态添加分组信息
                topic_with_group = topic.copy()
                topic_with_group['group'] = self.get_topic_group(topic['id'])
                results.append(topic_with_group)
        return results

    def batch_add_topics(self, topics_data: List[Dict]) -> Dict:
        """批量添加话题，支持分组"""
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
                group = topic_data.get('group', '').strip() or None  # 新增: 获取分组信息
                
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
                self.add_topic(name, circle_type, topic_id, group=group)
                results["success"].append({
                    "id": topic_id,
                    "name": name,
                    "circle_type": circle_type,
                    "group": group
                })
                
            except Exception as e:
                results["failed"].append({
                    "data": topic_data,
                    "error": str(e)
                })
        
        logger.info(f"批量添加完成: 成功 {len(results['success'])} 个, 失败 {len(results['failed'])} 个, 跳过 {len(results['skipped'])} 个")
        return results
    
    # --- 分组管理方法 ---

    def get_all_groups(self) -> List[str]:
        """获取所有分组名称"""
        return list(self.groups.keys())

    def add_group(self, group_name: str) -> bool:
        """添加一个新分组"""
        if not group_name or group_name.isspace():
            raise ValueError("分组名称不能为空")
        if group_name in self.groups:
            raise ValueError(f"分组 '{group_name}' 已存在")
        
        self.groups[group_name] = []
        self.save()
        logger.info(f"已添加新分组: {group_name}")
        return True

    def rename_group(self, old_name: str, new_name: str) -> bool:
        """重命名分组"""
        if not new_name or new_name.isspace():
            raise ValueError("新分组名称不能为空")
        if old_name not in self.groups:
            return False
        if new_name in self.groups:
            raise ValueError(f"分组 '{new_name}' 已存在")
        
        self.groups[new_name] = self.groups.pop(old_name)
        self.save()
        logger.info(f"已将分组 '{old_name}' 重命名为 '{new_name}'")
        return True

    def delete_group(self, group_name: str, delete_topics: bool = False) -> bool:
        """删除分组"""
        if group_name not in self.groups:
            return False
        
        topic_ids_in_group = self.groups[group_name]
        del self.groups[group_name]
        
        if delete_topics:
            for topic_id in topic_ids_in_group:
                if topic_id in self.topics:
                    del self.topics[topic_id]
            logger.info(f"已删除分组 '{group_name}' 及其包含的 {len(topic_ids_in_group)} 个话题")
        else:
            logger.info(f"已删除分组 '{group_name}'，分组内话题变为未分组状态")

        self.save()
        return True
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()