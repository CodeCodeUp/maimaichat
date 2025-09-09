from typing import List, Dict, Any, Optional
from modules.database.base_dao import BaseDAO, KeyValueDAO
import logging

logger = logging.getLogger(__name__)

class AIConfigDAO(BaseDAO):
    """AI配置DAO"""
    
    def __init__(self):
        super().__init__('ai_configs')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'name', 'description', 'api_key', 'base_url', 'main_model', 'assistant_model', 'enabled', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def find_enabled(self) -> List[Dict[str, Any]]:
        """查找所有启用的AI配置"""
        return self.find_all({'enabled': 1})
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称查找AI配置"""
        result = self.find_all({'name': name})
        return result[0] if result else None


class AIConfigSettingsDAO(KeyValueDAO):
    """AI配置设置DAO"""
    
    def __init__(self):
        super().__init__('ai_config_settings')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'setting_key', 'setting_value', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def _get_key_field(self) -> str:
        return 'setting_key'
    
    def _get_value_field(self) -> str:
        return 'setting_value'
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取键值 - 重写以使用正确的字段名"""
        record = self.find_by_key(key)
        if record:
            return record.get('setting_value', default)
        return default
    
    def set_value(self, key: str, value: Any) -> bool:
        """设置键值 - 重写以使用正确的字段名"""
        if self.exists_by_key(key):
            return self.update_by_key(key, {'setting_value': value}) > 0
        else:
            return self.insert({'setting_key': key, 'setting_value': value}) is not None
    
    def get_current_config_id(self) -> str:
        """获取当前配置ID"""
        return self.get_value('current_config_id', '')
    
    def set_current_config_id(self, config_id: str) -> bool:
        """设置当前配置ID"""
        return self.set_value('current_config_id', config_id)


class ScheduledRequestDAO(BaseDAO):
    """定时HTTP请求DAO"""
    
    def __init__(self):
        super().__init__('scheduled_requests')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'name', 'url', 'method', 'headers', 'cookies', 'data', 'enabled', 'last_executed', 'last_result', 'execution_count', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return ['headers', 'cookies', 'data', 'last_result']
    
    def _get_datetime_fields(self) -> List[str]:
        return ['last_executed', 'created_at', 'updated_at']
    
    def find_enabled(self) -> List[Dict[str, Any]]:
        """查找所有启用的定时请求"""
        return self.find_all({'enabled': 1}, 'created_at ASC')
    
    def update_execution_result(self, request_id: str, success: bool, result_data: str = None, error: str = None) -> bool:
        """更新执行结果"""
        from datetime import datetime
        
        # 先获取当前执行次数
        current = self.find_by_id(request_id)
        if not current:
            return False
        
        execution_count = current.get('execution_count', 0) + 1
        
        if success:
            last_result = {
                "success": True,
                "data": result_data,
                "executed_at": datetime.now().isoformat()
            }
        else:
            last_result = {
                "success": False,
                "error": error,
                "executed_at": datetime.now().isoformat()
            }
        
        update_data = {
            'last_executed': datetime.now(),
            'last_result': last_result,
            'execution_count': execution_count
        }
        
        return self.update(request_id, update_data) > 0


class ScheduledPostDAO(BaseDAO):
    """定时发布任务DAO"""
    
    def __init__(self):
        super().__init__('scheduled_posts')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'title', 'content', 'topic_url', 'topic_id', 'circle_type', 'topic_name', 'auto_publish_id', 'status', 'scheduled_at', 'published_at', 'error', 'failed_at', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['scheduled_at', 'published_at', 'failed_at', 'created_at', 'updated_at']
    
    def find_pending_posts(self) -> List[Dict[str, Any]]:
        """查找待发布的任务（已到发布时间）"""
        from datetime import datetime
        
        sql = f"""
        SELECT * FROM `{self.table_name}` 
        WHERE `status` = 'pending' AND `scheduled_at` <= %s 
        ORDER BY `created_at` ASC
        """
        result = self.db.execute_query(sql, (datetime.now(),))
        return [self._process_record(record) for record in result]
    
    def get_next_post_to_publish(self) -> Optional[Dict[str, Any]]:
        """获取下一个要发布的任务"""
        pending_posts = self.find_pending_posts()
        return pending_posts[0] if pending_posts else None
    
    def mark_as_published(self, post_id: str) -> bool:
        """标记任务为已发布并删除"""
        return self.delete(post_id) > 0
    
    def mark_as_failed(self, post_id: str, error: str) -> bool:
        """标记任务为发布失败"""
        from datetime import datetime
        
        update_data = {
            'status': 'failed',
            'error': error,
            'failed_at': datetime.now()
        }
        return self.update(post_id, update_data) > 0
    
    def get_pending_count(self) -> int:
        """获取待发布任务数量"""
        return self.count({'status': 'pending'})
    
    def reschedule_post(self, post_id: str, new_scheduled_at) -> bool:
        """重新安排发布时间"""
        update_data = {
            'scheduled_at': new_scheduled_at,
            'status': 'pending',
            'error': None,
            'failed_at': None
        }
        return self.update(post_id, update_data) > 0


class TopicDAO(BaseDAO):
    """话题DAO"""
    
    def __init__(self):
        super().__init__('topics')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'name', 'circle_type', 'group_name', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def find_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        """根据分组查找话题"""
        return self.find_all({'group_name': group_name}, 'updated_at DESC')
    
    def find_by_circle_type(self, circle_type: str) -> List[Dict[str, Any]]:
        """根据圈子类型查找话题"""
        return self.find_all({'circle_type': circle_type}, 'updated_at DESC')
    
    def search_by_name(self, name_keyword: str) -> List[Dict[str, Any]]:
        """根据名称关键词搜索话题"""
        sql = f"SELECT * FROM `{self.table_name}` WHERE `name` LIKE %s ORDER BY `updated_at` DESC"
        result = self.db.execute_query(sql, (f'%{name_keyword}%',))
        return [self._process_record(record) for record in result]
    
    def get_all_groups(self) -> List[str]:
        """获取所有分组"""
        sql = f"SELECT DISTINCT `group_name` FROM `{self.table_name}` WHERE `group_name` IS NOT NULL ORDER BY `group_name`"
        result = self.db.execute_query(sql)
        return [record['group_name'] for record in result]


class GroupsDAO(BaseDAO):
    """话题分组DAO"""
    
    def __init__(self):
        super().__init__('groups')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'group_name', 'description', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def get_all_group_names(self) -> List[str]:
        """获取所有分组名称"""
        try:
            groups = self.find_all(order_by='group_name ASC')
            return [group['group_name'] for group in groups]
        except Exception as e:
            logger.error(f"获取所有分组名称失败: {e}")
            return []
    
    def create_group_if_not_exists(self, group_name: str, description: str = None) -> bool:
        """创建分组如果不存在"""
        try:
            if self.find_all({'group_name': group_name}):
                return True  # 已存在
                
            group_data = {
                'group_name': group_name,
                'description': description or f'话题分组: {group_name}'
            }
            result = self.insert(group_data)
            return result is not None
        except Exception as e:
            logger.error(f"创建分组失败: {e}")
            return False


class PromptDAO(KeyValueDAO):
    """提示词DAO"""
    
    def __init__(self):
        super().__init__('prompts')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'name', 'content', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def _get_key_field(self) -> str:
        return 'name'
    
    def get_prompt(self, name: str, default: str = None) -> str:
        """获取提示词"""
        record = self.find_by_key(name)
        if record:
            return record.get('content', default)
        return default
    
    def set_prompt(self, name: str, content: str) -> bool:
        """设置提示词"""
        if self.exists_by_key(name):
            return self.update_by_key(name, {'content': content}) > 0
        else:
            return self.insert({'name': name, 'content': content}) is not None
    
    def delete_prompt(self, name: str) -> bool:
        """删除提示词"""
        return self.delete_by_key(name) > 0
    
    def get_all_prompts(self) -> Dict[str, str]:
        """获取所有提示词"""
        records = self.find_all(order_by='name ASC')
        return {record['name']: record['content'] for record in records}


class KeywordGroupDAO(BaseDAO):
    """关键词分组DAO"""
    
    def __init__(self):
        super().__init__('keyword_groups')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'group_name', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def find_by_group_name(self, group_name: str) -> Optional[Dict[str, Any]]:
        """根据分组名查找"""
        result = self.find_all({'group_name': group_name})
        return result[0] if result else None
    
    def exists_by_group_name(self, group_name: str) -> bool:
        """检查分组是否存在"""
        return self.find_by_group_name(group_name) is not None
    
    def create_group_if_not_exists(self, group_name: str) -> bool:
        """创建分组（如果不存在）"""
        if not self.exists_by_group_name(group_name):
            return self.insert({'group_name': group_name}) is not None
        return True
    
    def get_all_group_names(self) -> List[str]:
        """获取所有分组名称"""
        try:
            groups = self.find_all(order_by='group_name ASC')
            return [group['group_name'] for group in groups]
        except Exception as e:
            logger.error(f"获取所有关键词分组名称失败: {e}")
            return []


class KeywordDAO(BaseDAO):
    """关键词DAO"""
    
    def __init__(self):
        super().__init__('keywords')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'group_name', 'keyword', 'created_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at']
    
    def find_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        """根据分组查找关键词"""
        return self.find_all({'group_name': group_name}, 'created_at ASC')
    
    def add_keyword_to_group(self, group_name: str, keyword: str) -> bool:
        """添加关键词到分组"""
        try:
            # 确保分组存在
            group_dao = KeywordGroupDAO()
            group_dao.create_group_if_not_exists(group_name)
            
            # 检查关键词是否已存在
            if self.exists_keyword_in_group(group_name, keyword):
                logger.warning(f"关键词 '{keyword}' 已存在于分组 '{group_name}' 中")
                return True
            
            # 插入关键词
            return self.insert({'group_name': group_name, 'keyword': keyword}) is not None
            
        except Exception as e:
            logger.error(f"添加关键词失败: {e}")
            return False
    
    def remove_keyword_from_group(self, group_name: str, keyword: str) -> bool:
        """从分组中移除关键词"""
        sql = f"DELETE FROM `{self.table_name}` WHERE `group_name` = %s AND `keyword` = %s"
        return self.db.execute_update(sql, (group_name, keyword)) > 0
    
    def exists_keyword_in_group(self, group_name: str, keyword: str) -> bool:
        """检查关键词是否存在于分组中"""
        sql = f"SELECT 1 FROM `{self.table_name}` WHERE `group_name` = %s AND `keyword` = %s LIMIT 1"
        result = self.db.execute_query(sql, (group_name, keyword))
        return len(result) > 0
    
    def get_all_groups_with_keywords(self) -> Dict[str, List[str]]:
        """获取所有分组及其关键词"""
        sql = f"""
        SELECT kg.group_name, COALESCE(k.keyword, '') as keyword
        FROM keyword_groups kg 
        LEFT JOIN keywords k ON kg.group_name = k.group_name 
        ORDER BY kg.group_name, k.created_at
        """
        result = self.db.execute_query(sql)
        
        groups = {}
        for record in result:
            group_name = record['group_name']
            keyword = record['keyword']
            
            if group_name not in groups:
                groups[group_name] = []
            
            if keyword:  # 只添加非空关键词
                groups[group_name].append(keyword)
        
        return groups
    
    def delete_group(self, group_name: str) -> bool:
        """删除分组及其所有关键词"""
        try:
            # 删除分组下的所有关键词
            self.db.execute_update(f"DELETE FROM `{self.table_name}` WHERE `group_name` = %s", (group_name,))
            
            # 删除分组
            group_dao = KeywordGroupDAO()
            group_record = group_dao.find_by_group_name(group_name)
            if group_record:
                return group_dao.delete(group_record['id']) > 0
            
            return True
        except Exception as e:
            logger.error(f"删除分组失败: {e}")
            return False


class AutoPublishConfigDAO(BaseDAO):
    """自动发布配置DAO"""
    
    def __init__(self):
        super().__init__('auto_publish_configs')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'topic_id', 'max_posts', 'current_posts', 'is_active', 'last_published_at', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return []
    
    def _get_datetime_fields(self) -> List[str]:
        return ['last_published_at', 'created_at', 'updated_at']
    
    def find_active(self) -> List[Dict[str, Any]]:
        """查找所有激活的自动发布配置"""
        return self.find_all({'is_active': 1})
    
    def find_by_topic_id(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """根据话题ID查找自动发布配置"""
        result = self.find_all({'topic_id': topic_id})
        return result[0] if result else None
    
    def find_publishable(self) -> List[Dict[str, Any]]:
        """查找可发布的配置（激活且未达到最大发布数量）"""
        sql = f"""
        SELECT * FROM `{self.table_name}` 
        WHERE `is_active` = 1 
        AND (`max_posts` = -1 OR `current_posts` < `max_posts`)
        ORDER BY `last_published_at` ASC NULLS FIRST
        """
        return self.db.execute_query(sql)
    
    def increment_posts(self, config_id: str) -> bool:
        """增加已发布数量"""
        try:
            sql = f"""
            UPDATE `{self.table_name}` 
            SET `current_posts` = `current_posts` + 1, 
                `last_published_at` = NOW(),
                `updated_at` = NOW()
            WHERE `id` = %s
            """
            rows_affected = self.db.execute_update(sql, (config_id,))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"增加发布数量失败: {e}")
            return False
    
    def reset_posts(self, config_id: str) -> bool:
        """重置已发布数量"""
        try:
            return self.update(config_id, {'current_posts': 0}) > 0
        except Exception as e:
            logger.error(f"重置发布数量失败: {e}")
            return False


class AIConversationDAO(BaseDAO):
    """AI对话历史DAO"""
    
    def __init__(self):
        super().__init__('ai_conversations')
    
    def _get_table_fields(self) -> List[str]:
        return ['id', 'topic_id', 'messages', 'created_at', 'updated_at']
    
    def _get_json_fields(self) -> List[str]:
        return ['messages']
    
    def _get_datetime_fields(self) -> List[str]:
        return ['created_at', 'updated_at']
    
    def find_by_topic_id(self, topic_id: str) -> List[Dict[str, Any]]:
        """根据话题ID查找对话历史"""
        return self.find_all({'topic_id': topic_id})
    
    def get_latest_by_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """获取话题的最新对话历史"""
        sql = f"""
        SELECT * FROM `{self.table_name}` 
        WHERE `topic_id` = %s 
        ORDER BY `created_at` DESC 
        LIMIT 1
        """
        result = self.db.execute_query(sql, (topic_id,))
        return result[0] if result else None
    
    def add_message(self, conversation_id: str, role: str, content: str) -> bool:
        """为现有对话添加消息"""
        try:
            # 获取现有对话
            conversation = self.find_by_id(conversation_id)
            if not conversation:
                return False
            
            # 添加新消息
            messages = conversation.get('messages', [])
            messages.append({
                'role': role,
                'content': content
            })
            
            # 更新对话
            return self.update(conversation_id, {'messages': messages}) > 0
        except Exception as e:
            logger.error(f"添加消息失败: {e}")
            return False
    
    def create_with_messages(self, conversation_id: str, topic_id: str, messages: List[Dict[str, Any]]) -> bool:
        """创建新对话并设置消息"""
        try:
            data = {
                'id': conversation_id,
                'topic_id': topic_id,
                'messages': messages
            }
            result = self.insert(data)
            return result is not None
        except Exception as e:
            logger.error(f"创建对话失败: {e}")
            return False