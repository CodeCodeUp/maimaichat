import json
import os
import logging
from typing import Dict, List, Optional
import threading

logger = logging.getLogger(__name__)


class GroupKeywordsStore:
    """分组关键词存储管理"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self._lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """确保文件存在"""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self._save_data({})

    def _load_data(self) -> Dict[str, List[str]]:
        """加载关键词数据"""
        try:
            with self._lock:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            logger.error(f"加载分组关键词失败: {e}")
            return {}

    def _save_data(self, data: Dict[str, List[str]]) -> bool:
        """保存关键词数据"""
        try:
            with self._lock:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存分组关键词失败: {e}")
            return False

    def get_all_group_keywords(self) -> Dict[str, List[str]]:
        """获取所有分组关键词"""
        return self._load_data()

    def get_group_keywords(self, group_name: str) -> List[str]:
        """获取指定分组的关键词"""
        data = self._load_data()
        return data.get(group_name, [])

    def has_keywords(self, group_name: str) -> bool:
        """判断分组是否有关键词"""
        keywords = self.get_group_keywords(group_name)
        return len(keywords) > 0

    def add_keyword_to_group(self, group_name: str, keyword: str) -> bool:
        """为分组添加关键词"""
        if not keyword.strip():
            return False
            
        keyword = keyword.strip()
        data = self._load_data()
        
        if group_name not in data:
            data[group_name] = []
        
        if keyword not in data[group_name]:
            data[group_name].append(keyword)
            return self._save_data(data)
        
        return True

    def remove_keyword_from_group(self, group_name: str, keyword: str) -> bool:
        """从分组中移除关键词"""
        data = self._load_data()
        
        if group_name not in data:
            return False
            
        if keyword in data[group_name]:
            data[group_name].remove(keyword)
            return self._save_data(data)
        
        return False

    def update_group_keywords(self, group_name: str, keywords: List[str]) -> bool:
        """更新分组的所有关键词"""
        data = self._load_data()
        
        # 去重和过滤空值
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        keywords = list(dict.fromkeys(keywords))  # 去重但保持顺序
        
        data[group_name] = keywords
        return self._save_data(data)

    def delete_group(self, group_name: str) -> bool:
        """删除分组的所有关键词"""
        data = self._load_data()
        
        if group_name in data:
            del data[group_name]
            return self._save_data(data)
        
        return False

    def ensure_group_exists(self, group_name: str) -> bool:
        """确保分组存在（如果不存在则创建空分组）"""
        data = self._load_data()
        
        if group_name not in data:
            data[group_name] = []
            return self._save_data(data)
        
        return True

    def sync_with_topic_groups(self, topic_groups: List[str]) -> bool:
        """与话题分组同步，确保所有分组都有关键词配置"""
        data = self._load_data()
        updated = False
        
        # 添加新分组
        for group in topic_groups:
            if group not in data:
                data[group] = []
                updated = True
        
        # 移除不存在的分组（可选，这里保留历史数据）
        # existing_groups = set(data.keys())
        # for group in existing_groups:
        #     if group not in topic_groups:
        #         del data[group]
        #         updated = True
        
        if updated:
            return self._save_data(data)
        
        return True