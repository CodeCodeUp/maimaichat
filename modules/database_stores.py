from typing import Dict, List, Optional
import logging
import uuid
from datetime import datetime

from modules.database_dao import TopicDAO, PromptDAO, KeywordDAO, KeywordGroupDAO, GroupsDAO

logger = logging.getLogger(__name__)

class TopicStoreDB:
    """话题存储管理类 - 数据库版本"""
    
    def __init__(self):
        self.dao = TopicDAO()
        self.groups_dao = GroupsDAO()
        self.keyword_group_dao = KeywordGroupDAO()  # 添加关键词分组DAO
        self.topics = {}  # 保持兼容性
        logger.info("初始化话题数据库存储")
    
    def load(self):
        """从数据库加载话题数据（兼容原接口）"""
        try:
            topics = self.dao.find_all()
            self.topics = {topic['id']: topic for topic in topics}
            logger.info(f"已加载 {len(self.topics)} 个话题")
        except Exception as e:
            logger.error(f"加载话题数据失败: {e}")
            self.topics = {}
    
    def save(self):
        """保存话题数据到数据库（兼容原接口，实际无需操作）"""
        pass
    
    def add_topic(self, topic_id: str, name: str, circle_type: str = None, group_name: str = None) -> bool:
        """添加话题"""
        try:
            topic_data = {
                'id': topic_id,
                'name': name,
                'circle_type': circle_type,
                'group_name': group_name
            }
            
            result = self.dao.insert(topic_data)
            if result:
                # 更新内存缓存
                self.topics[topic_id] = topic_data
                self.topics[topic_id]['created_at'] = datetime.now().isoformat()
                self.topics[topic_id]['updated_at'] = datetime.now().isoformat()
                logger.info(f"已添加话题: {name}")
            return result is not None
        except Exception as e:
            logger.error(f"添加话题失败: {e}")
            return False
    
    def update_topic(self, topic_id: str, **kwargs) -> bool:
        """更新话题"""
        try:
            result = self.dao.update(topic_id, kwargs) > 0
            if result:
                # 更新内存缓存
                if topic_id in self.topics:
                    self.topics[topic_id].update(kwargs)
                    self.topics[topic_id]['updated_at'] = datetime.now().isoformat()
                logger.info(f"已更新话题: {topic_id}")
            return result
        except Exception as e:
            logger.error(f"更新话题失败: {e}")
            return False
    
    def delete_topic(self, topic_id: str) -> bool:
        """删除话题"""
        try:
            topic = self.dao.find_by_id(topic_id)
            if topic:
                result = self.dao.delete(topic_id) > 0
                if result:
                    # 更新内存缓存
                    if topic_id in self.topics:
                        del self.topics[topic_id]
                    logger.info(f"已删除话题: {topic['name']}")
                return result
            return False
        except Exception as e:
            logger.error(f"删除话题失败: {e}")
            return False
    
    def get_topic(self, topic_id: str) -> Optional[Dict]:
        """获取单个话题"""
        try:
            return self.dao.find_by_id(topic_id)
        except Exception as e:
            logger.error(f"获取话题失败: {e}")
            return None
    
    def get_all_topics(self) -> List[Dict]:
        """获取所有话题 - 返回数组格式"""
        try:
            topics = self.dao.find_all()
            logger.info(f"TopicStoreDB.get_all_topics() - 从DAO获取的数据类型: {type(topics)}, 数量: {len(topics)}")
            result = topics  # 直接返回数组，不转换为字典
            logger.info(f"TopicStoreDB.get_all_topics() - 最终返回的数据类型: {type(result)}, 数量: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"获取所有话题失败: {e}")
            return []
    
    def get_topics_by_group(self, group_name: str) -> List[Dict]:
        """根据分组获取话题"""
        try:
            return self.dao.find_by_group(group_name)
        except Exception as e:
            logger.error(f"根据分组获取话题失败: {e}")
            return []
    
    def get_topics_by_circle_type(self, circle_type: str) -> List[Dict]:
        """根据圈子类型获取话题"""
        try:
            return self.dao.find_by_circle_type(circle_type)
        except Exception as e:
            logger.error(f"根据圈子类型获取话题失败: {e}")
            return []
    
    def search_topics_by_name(self, name_keyword: str) -> List[Dict]:
        """根据名称关键词搜索话题"""
        try:
            return self.dao.search_by_name(name_keyword)
        except Exception as e:
            logger.error(f"搜索话题失败: {e}")
            return []
    
    def get_all_groups(self) -> List[str]:
        """获取所有分组 - 从keyword_groups表获取"""
        try:
            # 从keyword_groups表获取分组名称
            logger.info("TopicStoreDB.get_all_groups() - 开始获取分组")
            groups = self.keyword_group_dao.get_all_group_names()
            logger.info(f"TopicStoreDB.get_all_groups() - 获取到分组: {groups}")
            return groups
        except Exception as e:
            logger.error(f"获取所有分组失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return []
    
    def count_topics(self) -> int:
        """统计话题数量"""
        try:
            return self.dao.count()
        except Exception as e:
            logger.error(f"统计话题数量失败: {e}")
            return 0
    
    def count_topics_by_group(self, group_name: str) -> int:
        """统计分组下的话题数量"""
        try:
            return self.dao.count({'group_name': group_name})
        except Exception as e:
            logger.error(f"统计分组话题数量失败: {e}")
            return 0
    
    def batch_add_topics(self, topics_data: List[Dict]) -> Dict:
        """批量添加话题"""
        results = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        try:
            for topic_data in topics_data:
                try:
                    # 生成ID如果没有
                    if 'id' not in topic_data or not topic_data['id']:
                        topic_data['id'] = str(uuid.uuid4())
                    
                    # 检查是否已存在
                    if self.dao.find_by_id(topic_data['id']):
                        results['skipped'].append(topic_data['id'])
                        continue
                    
                    # 尝试插入
                    result = self.dao.insert(topic_data)
                    if result:
                        # 更新内存缓存
                        self.topics[topic_data['id']] = topic_data
                        results['success'].append(topic_data['id'])
                    else:
                        results['failed'].append(topic_data['id'])
                        
                except Exception as e:
                    logger.error(f"添加话题 {topic_data.get('id', 'unknown')} 失败: {e}")
                    results['failed'].append(topic_data.get('id', 'unknown'))
            
            logger.info(f"批量添加话题完成: 成功 {len(results['success'])}, 失败 {len(results['failed'])}, 跳过 {len(results['skipped'])}")
            return results
            
        except Exception as e:
            logger.error(f"批量添加话题失败: {e}")
            # 所有话题都标记为失败
            for topic_data in topics_data:
                results['failed'].append(topic_data.get('id', 'unknown'))
            return results
    
    def update_topic_group(self, topic_id: str, group_name: str) -> bool:
        """更新话题分组"""
        return self.update_topic(topic_id, group_name=group_name)
    
    def clear_group(self, group_name: str) -> int:
        """清空指定分组的所有话题"""
        try:
            topics = self.dao.find_by_group(group_name)
            count = 0
            for topic in topics:
                if self.dao.delete(topic['id']) > 0:
                    # 更新内存缓存
                    if topic['id'] in self.topics:
                        del self.topics[topic['id']]
                    count += 1
            
            if count > 0:
                logger.info(f"已清空分组 '{group_name}' 的 {count} 个话题")
            return count
        except Exception as e:
            logger.error(f"清空分组话题失败: {e}")
            return 0
    
    def add_group(self, group_name: str) -> bool:
        """添加话题分组到keyword_groups表"""
        try:
            if not group_name or not group_name.strip():
                return False
            
            # 创建关键词分组（确保与get_all_groups使用相同的表）
            result = self.keyword_group_dao.create_group_if_not_exists(group_name.strip())
            if result:
                logger.info(f"已创建关键词分组: {group_name}")
            return result
        except Exception as e:
            logger.error(f"添加关键词分组失败: {e}")
            return False
    
    def delete_group(self, group_name: str, delete_topics: bool = False) -> bool:
        """删除分组"""
        try:
            if not group_name or not group_name.strip():
                return False
            
            # 如果需要删除分组下的话题
            if delete_topics:
                # 删除分组下的所有话题
                topics_in_group = self.dao.find_by_group(group_name.strip())
                for topic in topics_in_group:
                    self.dao.delete(topic['id'])
                    logger.info(f"已删除话题: {topic['name']}")
            else:
                # 将分组下的话题设置为未分组状态
                topics_in_group = self.dao.find_by_group(group_name.strip())
                for topic in topics_in_group:
                    self.dao.update(topic['id'], {'group_name': None})
                logger.info(f"已将分组 '{group_name}' 下的 {len(topics_in_group)} 个话题设为未分组状态")
            
            # 删除关键词分组（与get_all_groups和add_group使用相同的表）
            result = self.keyword_group_dao.find_by_group_name(group_name.strip())
            if result:
                success = self.keyword_group_dao.delete(result['id']) > 0
                if success:
                    logger.info(f"已删除关键词分组: {group_name}")
                return success
            else:
                logger.warning(f"分组不存在: {group_name}")
                return False
        except Exception as e:
            logger.error(f"删除关键词分组失败: {e}")
            return False


class PromptStoreDB:
    """提示词存储管理类 - 数据库版本"""
    
    def __init__(self):
        self.dao = PromptDAO()
        logger.info("初始化提示词数据库存储")
    
    def load(self):
        """从数据库加载提示词数据（兼容原接口）"""
        try:
            prompts = self.dao.get_all_prompts()
            logger.info(f"已从数据库加载 {len(prompts)} 个提示词")
        except Exception as e:
            logger.error(f"加载提示词数据失败: {e}")
    
    def get_prompt(self, name: str, default: str = None) -> str:
        """获取提示词"""
        try:
            return self.dao.get_prompt(name, default)
        except Exception as e:
            logger.error(f"获取提示词失败: {e}")
            return default
    
    def set_prompt(self, name: str, content: str) -> bool:
        """设置提示词"""
        try:
            result = self.dao.set_prompt(name, content)
            if result:
                logger.info(f"已设置提示词: {name}")
            return result
        except Exception as e:
            logger.error(f"设置提示词失败: {e}")
            return False
    
    def delete_prompt(self, name: str) -> bool:
        """删除提示词"""
        try:
            result = self.dao.delete_prompt(name)
            if result:
                logger.info(f"已删除提示词: {name}")
            return result
        except Exception as e:
            logger.error(f"删除提示词失败: {e}")
            return False
    
    def get_all_prompts(self) -> Dict[str, str]:
        """获取所有提示词"""
        try:
            logger.info("PromptStoreDB: 开始获取所有提示词")
            result = self.dao.get_all_prompts()
            logger.info(f"PromptStoreDB: 成功获取 {len(result)} 个提示词")
            for key in result.keys():
                logger.info(f"PromptStoreDB: 提示词Key: {key}")
            return result
        except Exception as e:
            logger.error(f"获取所有提示词失败: {e}")
            import traceback
            logger.error(f"详细错误: {traceback.format_exc()}")
            return {}
    
    def exists_prompt(self, name: str) -> bool:
        """检查提示词是否存在"""
        try:
            return self.dao.exists_by_key(name)
        except Exception as e:
            logger.error(f"检查提示词存在失败: {e}")
            return False
    
    def count_prompts(self) -> int:
        """统计提示词数量"""
        try:
            return self.dao.count()
        except Exception as e:
            logger.error(f"统计提示词数量失败: {e}")
            return 0
    
    # 兼容性方法，保持与原始JSON存储API一致
    def load_prompts(self) -> Dict[str, str]:
        """加载所有提示词 - 兼容性方法"""
        logger.info("PromptStoreDB.load_prompts(): 被调用")
        result = self.get_all_prompts()
        logger.info(f"PromptStoreDB.load_prompts(): 返回 {len(result)} 个提示词")
        return result
    
    def save_prompts(self, prompts: Dict[str, str]) -> bool:
        """保存所有提示词 - 兼容性方法"""
        try:
            # 先清空现有提示词，再重新插入
            success = True
            
            # 获取当前所有提示词名称
            current_prompts = self.get_all_prompts()
            
            # 删除不在新数据中的提示词
            for name in current_prompts.keys():
                if name not in prompts:
                    if not self.delete_prompt(name):
                        success = False
            
            # 更新或插入新的提示词
            for name, content in prompts.items():
                if not self.set_prompt(name, content):
                    success = False
            
            if success:
                logger.info(f"已保存 {len(prompts)} 个提示词")
            else:
                logger.warning("保存提示词时部分操作失败")
            
            return success
        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
            return False


class GroupKeywordsStoreDB:
    """分组关键词存储管理类 - 数据库版本"""
    
    def __init__(self):
        self.group_dao = KeywordGroupDAO()
        self.keyword_dao = KeywordDAO()
        logger.info("初始化分组关键词数据库存储")
    
    def load(self):
        """从数据库加载分组关键词数据（兼容原接口）"""
        try:
            groups_keywords = self.keyword_dao.get_all_groups_with_keywords()
            logger.info(f"已从数据库加载 {len(groups_keywords)} 个分组的关键词")
        except Exception as e:
            logger.error(f"加载分组关键词数据失败: {e}")
    
    def get_all_groups_with_keywords(self) -> Dict[str, List[str]]:
        """获取所有分组及其关键词"""
        try:
            return self.keyword_dao.get_all_groups_with_keywords()
        except Exception as e:
            logger.error(f"获取所有分组关键词失败: {e}")
            return {}
    
    def get_group_keywords(self, group_name: str) -> List[str]:
        """获取指定分组的关键词"""
        try:
            keywords = self.keyword_dao.find_by_group(group_name)
            return [kw['keyword'] for kw in keywords]
        except Exception as e:
            logger.error(f"获取分组关键词失败: {e}")
            return []
    
    def add_keyword_to_group(self, group_name: str, keyword: str) -> bool:
        """添加关键词到分组"""
        try:
            result = self.keyword_dao.add_keyword_to_group(group_name, keyword)
            if result:
                logger.info(f"已添加关键词 '{keyword}' 到分组 '{group_name}'")
            return result
        except Exception as e:
            logger.error(f"添加关键词到分组失败: {e}")
            return False
    
    def remove_keyword_from_group(self, group_name: str, keyword: str) -> bool:
        """从分组中移除关键词"""
        try:
            result = self.keyword_dao.remove_keyword_from_group(group_name, keyword)
            if result:
                logger.info(f"已从分组 '{group_name}' 移除关键词 '{keyword}'")
            return result
        except Exception as e:
            logger.error(f"从分组移除关键词失败: {e}")
            return False
    
    def create_group(self, group_name: str) -> bool:
        """创建分组"""
        try:
            result = self.group_dao.create_group_if_not_exists(group_name)
            if result:
                logger.info(f"已创建分组: {group_name}")
            return result
        except Exception as e:
            logger.error(f"创建分组失败: {e}")
            return False
    
    def delete_group(self, group_name: str) -> bool:
        """删除分组及其所有关键词"""
        try:
            result = self.keyword_dao.delete_group(group_name)
            if result:
                logger.info(f"已删除分组: {group_name}")
            return result
        except Exception as e:
            logger.error(f"删除分组失败: {e}")
            return False
    
    def exists_group(self, group_name: str) -> bool:
        """检查分组是否存在"""
        try:
            return self.group_dao.exists_by_group_name(group_name)
        except Exception as e:
            logger.error(f"检查分组存在失败: {e}")
            return False
    
    def get_all_groups(self) -> List[str]:
        """获取所有分组名称"""
        try:
            groups = self.group_dao.find_all(order_by='group_name ASC')
            return [group['group_name'] for group in groups]
        except Exception as e:
            logger.error(f"获取所有分组失败: {e}")
            return []
    
    def count_keywords_in_group(self, group_name: str) -> int:
        """统计分组中的关键词数量"""
        try:
            return self.keyword_dao.count({'group_name': group_name})
        except Exception as e:
            logger.error(f"统计分组关键词数量失败: {e}")
            return 0
    
    def exists_keyword_in_group(self, group_name: str, keyword: str) -> bool:
        """检查关键词是否存在于分组中"""
        try:
            return self.keyword_dao.exists_keyword_in_group(group_name, keyword)
        except Exception as e:
            logger.error(f"检查关键词存在失败: {e}")
            return False
    
    # 兼容性方法，保持与原始JSON存储API一致
    def get_all_group_keywords(self) -> Dict[str, List[str]]:
        """获取所有分组关键词 - 兼容性方法"""
        return self.get_all_groups_with_keywords()
    
    def has_keywords(self, group_name: str) -> bool:
        """判断分组是否有关键词 - 兼容性方法"""
        try:
            keywords = self.get_group_keywords(group_name)
            return len(keywords) > 0
        except Exception as e:
            logger.error(f"判断分组是否有关键词失败: {e}")
            return False
    
    def update_group_keywords(self, group_name: str, keywords: List[str]) -> bool:
        """更新分组的所有关键词 - 兼容性方法"""
        try:
            # 先清空分组的现有关键词
            current_keywords = self.get_group_keywords(group_name)
            for keyword in current_keywords:
                if not self.remove_keyword_from_group(group_name, keyword):
                    logger.warning(f"删除关键词 '{keyword}' 失败")
            
            # 添加新的关键词
            success = True
            # 去重和过滤空值
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            keywords = list(dict.fromkeys(keywords))  # 去重但保持顺序
            
            for keyword in keywords:
                if not self.add_keyword_to_group(group_name, keyword):
                    success = False
                    logger.error(f"添加关键词 '{keyword}' 到分组 '{group_name}' 失败")
            
            return success
        except Exception as e:
            logger.error(f"更新分组关键词失败: {e}")
            return False