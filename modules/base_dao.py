from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime

from modules.database_manager import get_db_manager, json_serialize, json_deserialize, format_datetime, parse_datetime

logger = logging.getLogger(__name__)

class BaseDAO(ABC):
    """数据访问层基类"""
    
    def __init__(self, table_name: str):
        """
        初始化DAO
        
        Args:
            table_name: 表名
        """
        self.table_name = table_name
        self.db = get_db_manager()
    
    def find_by_id(self, record_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """根据ID查找记录"""
        sql = f"SELECT * FROM `{self.table_name}` WHERE `id` = %s"
        result = self.db.execute_query(sql, (record_id,))
        if result:
            return self._process_record(result[0])
        return None
    
    def find_all(self, conditions: Dict[str, Any] = None, order_by: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """查找所有记录"""
        sql = f"SELECT * FROM `{self.table_name}`"
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                if value is None:
                    where_clauses.append(f"`{key}` IS NULL")
                else:
                    where_clauses.append(f"`{key}` = %s")
                    params.append(value)
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        result = self.db.execute_query(sql, tuple(params))
        return [self._process_record(record) for record in result]
    
    def count(self, conditions: Dict[str, Any] = None) -> int:
        """统计记录数量"""
        sql = f"SELECT COUNT(*) as count FROM `{self.table_name}`"
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                if value is None:
                    where_clauses.append(f"`{key}` IS NULL")
                else:
                    where_clauses.append(f"`{key}` = %s")
                    params.append(value)
            
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
        
        result = self.db.execute_query(sql, tuple(params))
        return result[0]['count'] if result else 0
    
    def exists(self, record_id: Union[str, int]) -> bool:
        """检查记录是否存在"""
        sql = f"SELECT 1 FROM `{self.table_name}` WHERE `id` = %s LIMIT 1"
        result = self.db.execute_query(sql, (record_id,))
        return len(result) > 0
    
    def insert(self, data: Dict[str, Any]) -> Union[str, int]:
        """插入记录"""
        data = self._prepare_data_for_insert(data)
        
        fields = list(data.keys())
        placeholders = ["%s"] * len(fields)
        values = [self._serialize_field_value(data[field]) for field in fields]
        
        sql = f"INSERT INTO `{self.table_name}` (`{'`, `'.join(fields)}`) VALUES ({', '.join(placeholders)})"
        
        insert_id = self.db.execute_insert(sql, tuple(values))
        
        # 如果表有自增ID，返回插入ID；否则返回主键值
        if 'id' in data:
            return data['id']
        return insert_id
    
    def update(self, record_id: Union[str, int], data: Dict[str, Any]) -> int:
        """更新记录"""
        if not data:
            return 0
        
        data = self._prepare_data_for_update(data)
        
        set_clauses = []
        values = []
        
        for field, value in data.items():
            set_clauses.append(f"`{field}` = %s")
            values.append(self._serialize_field_value(value))
        
        values.append(record_id)
        
        sql = f"UPDATE `{self.table_name}` SET {', '.join(set_clauses)} WHERE `id` = %s"
        
        return self.db.execute_update(sql, tuple(values))
    
    def delete(self, record_id: Union[str, int]) -> int:
        """删除记录"""
        sql = f"DELETE FROM `{self.table_name}` WHERE `id` = %s"
        return self.db.execute_update(sql, (record_id,))
    
    def batch_insert(self, data_list: List[Dict[str, Any]]) -> int:
        """批量插入记录"""
        if not data_list:
            return 0
        
        # 准备数据
        processed_data_list = [self._prepare_data_for_insert(data) for data in data_list]
        
        # 使用第一条记录的字段作为模板
        fields = list(processed_data_list[0].keys())
        placeholders = ["%s"] * len(fields)
        
        sql = f"INSERT INTO `{self.table_name}` (`{'`, `'.join(fields)}`) VALUES ({', '.join(placeholders)})"
        
        # 准备批量参数
        params_list = []
        for data in processed_data_list:
            values = [self._serialize_field_value(data.get(field)) for field in fields]
            params_list.append(tuple(values))
        
        return self.db.execute_batch(sql, params_list)
    
    def _process_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """处理从数据库查询出的记录"""
        if not record:
            return record
        
        processed = {}
        for key, value in record.items():
            processed[key] = self._deserialize_field_value(key, value)
        
        return processed
    
    def _serialize_field_value(self, value: Any) -> Any:
        """序列化字段值用于数据库存储"""
        if value is None:
            return None
        
        # JSON字段处理
        if isinstance(value, (dict, list)):
            return json_serialize(value)
        
        # datetime字段处理
        if isinstance(value, datetime):
            return format_datetime(value)
        
        return value
    
    def _deserialize_field_value(self, field_name: str, value: Any) -> Any:
        """反序列化字段值从数据库读取"""
        if value is None:
            return None
        
        # JSON字段处理
        if field_name in self._get_json_fields():
            return json_deserialize(value)
        
        # datetime字段处理  
        if field_name in self._get_datetime_fields():
            if isinstance(value, datetime):
                return value.isoformat()
            return format_datetime(parse_datetime(str(value)))
        
        return value
    
    def _prepare_data_for_insert(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备插入数据"""
        prepared = data.copy()
        
        # 添加创建时间
        if 'created_at' in self._get_table_fields() and 'created_at' not in prepared:
            prepared['created_at'] = datetime.now()
        
        # 添加更新时间
        if 'updated_at' in self._get_table_fields() and 'updated_at' not in prepared:
            prepared['updated_at'] = datetime.now()
        
        return prepared
    
    def _prepare_data_for_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备更新数据"""
        prepared = data.copy()
        
        # 更新时间
        if 'updated_at' in self._get_table_fields():
            prepared['updated_at'] = datetime.now()
        
        # 移除不允许更新的字段
        if 'id' in prepared:
            del prepared['id']
        if 'created_at' in prepared:
            del prepared['created_at']
        
        return prepared
    
    @abstractmethod
    def _get_table_fields(self) -> List[str]:
        """获取表字段列表"""
        pass
    
    @abstractmethod
    def _get_json_fields(self) -> List[str]:
        """获取JSON字段列表"""
        pass
    
    @abstractmethod 
    def _get_datetime_fields(self) -> List[str]:
        """获取datetime字段列表"""
        pass


class KeyValueDAO(BaseDAO):
    """键值对存储DAO基类"""
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """获取键值"""
        record = self.find_by_key(key)
        if record:
            return record.get('value', default)
        return default
    
    def set_value(self, key: str, value: Any) -> bool:
        """设置键值"""
        if self.exists_by_key(key):
            return self.update_by_key(key, {'value': value}) > 0
        else:
            return self.insert({'key': key, 'value': value}) is not None
    
    def find_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """根据key查找记录"""
        sql = f"SELECT * FROM `{self.table_name}` WHERE `{self._get_key_field()}` = %s"
        result = self.db.execute_query(sql, (key,))
        if result:
            return self._process_record(result[0])
        return None
    
    def exists_by_key(self, key: str) -> bool:
        """检查key是否存在"""
        sql = f"SELECT 1 FROM `{self.table_name}` WHERE `{self._get_key_field()}` = %s LIMIT 1"
        result = self.db.execute_query(sql, (key,))
        return len(result) > 0
    
    def update_by_key(self, key: str, data: Dict[str, Any]) -> int:
        """根据key更新记录"""
        if not data:
            return 0
        
        data = self._prepare_data_for_update(data)
        
        set_clauses = []
        values = []
        
        for field, value in data.items():
            set_clauses.append(f"`{field}` = %s")
            values.append(self._serialize_field_value(value))
        
        values.append(key)
        
        sql = f"UPDATE `{self.table_name}` SET {', '.join(set_clauses)} WHERE `{self._get_key_field()}` = %s"
        
        return self.db.execute_update(sql, tuple(values))
    
    def delete_by_key(self, key: str) -> int:
        """根据key删除记录"""
        sql = f"DELETE FROM `{self.table_name}` WHERE `{self._get_key_field()}` = %s"
        return self.db.execute_update(sql, (key,))
    
    @abstractmethod
    def _get_key_field(self) -> str:
        """获取key字段名"""
        pass