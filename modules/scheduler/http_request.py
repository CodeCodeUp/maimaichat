import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging

from modules.database.dao import ScheduledRequestDAO

logger = logging.getLogger(__name__)

class ScheduledRequestsStoreDB:
    """定时HTTP请求存储管理类 - 数据库版本"""
    
    def __init__(self):
        self.dao = ScheduledRequestDAO()
        logger.info("初始化定时HTTP请求数据库存储")
    
    def load(self):
        """从数据库加载定时请求配置（兼容原接口）"""
        try:
            count = self.dao.count()
            logger.info(f"已加载 {count} 个定时请求配置")
        except Exception as e:
            logger.error(f"加载定时请求配置失败: {e}")
    
    def save(self):
        """保存到数据库（兼容原接口，实际无需操作）"""
        pass
    
    def add_request(self, name: str, url: str, method: str = 'GET', 
                   headers: Dict = None, cookies: str = None, 
                   data: Dict = None, enabled: bool = True) -> str:
        """添加定时请求配置"""
        request_id = str(uuid.uuid4())
        
        # 解析cookies字符串为字典格式
        cookies_dict = None
        if cookies:
            cookies_dict = self._parse_cookies(cookies)
        
        request_config = {
            "id": request_id,
            "name": name,
            "url": url,
            "method": method.upper(),
            "headers": headers or {},
            "cookies": cookies_dict,
            "data": data,
            "enabled": enabled,
            "last_executed": None,
            "last_result": None,
            "execution_count": 0
        }
        
        try:
            self.dao.insert(request_config)
            logger.info(f"已添加定时请求配置: {name} ({method} {url})")
            return request_id
        except Exception as e:
            logger.error(f"添加定时请求配置失败: {e}")
            raise
    
    def _parse_cookies(self, cookies_str: str) -> Dict:
        """解析cookies字符串为字典格式"""
        cookies_dict = {}
        if not cookies_str:
            return cookies_dict
        
        try:
            # 处理多种cookie格式
            pairs = cookies_str.split(';')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    cookies_dict[key.strip()] = value.strip()
        except Exception as e:
            logger.warning(f"解析cookies失败: {e}, 原始字符串: {cookies_str}")
        
        return cookies_dict
    
    def get_enabled_requests(self) -> List[Dict]:
        """获取所有启用的定时请求配置"""
        try:
            return self.dao.find_enabled()
        except Exception as e:
            logger.error(f"获取启用的请求配置失败: {e}")
            return []
    
    def get_all_requests(self) -> List[Dict]:
        """获取所有定时请求配置"""
        try:
            return self.dao.find_all(order_by='created_at DESC')
        except Exception as e:
            logger.error(f"获取所有请求配置失败: {e}")
            return []
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """获取单个定时请求配置"""
        try:
            return self.dao.find_by_id(request_id)
        except Exception as e:
            logger.error(f"获取请求配置失败: {e}")
            return None
    
    def update_request(self, request_id: str, **kwargs) -> bool:
        """更新定时请求配置"""
        try:
            # 特殊处理cookies字段
            if 'cookies' in kwargs:
                cookies_dict = self._parse_cookies(kwargs['cookies']) if kwargs['cookies'] else None
                kwargs['cookies'] = cookies_dict
            
            # 处理method字段
            if 'method' in kwargs:
                kwargs['method'] = kwargs['method'].upper()
            
            return self.dao.update(request_id, kwargs) > 0
        except Exception as e:
            logger.error(f"更新请求配置失败: {e}")
            return False
    
    def delete_request(self, request_id: str) -> bool:
        """删除定时请求配置"""
        try:
            request = self.dao.find_by_id(request_id)
            if request:
                result = self.dao.delete(request_id) > 0
                if result:
                    logger.info(f"已删除定时请求配置: {request['name']}")
                return result
            return False
        except Exception as e:
            logger.error(f"删除请求配置失败: {e}")
            return False
    
    def update_execution_result(self, request_id: str, success: bool, 
                              result_data: str = None, error: str = None):
        """更新请求执行结果"""
        try:
            return self.dao.update_execution_result(request_id, success, result_data, error)
        except Exception as e:
            logger.error(f"更新执行结果失败: {e}")
            return False
    
    def get_enabled_count(self) -> int:
        """获取启用的请求配置数量"""
        try:
            return self.dao.count({'enabled': 1})
        except Exception as e:
            logger.error(f"获取启用请求数量失败: {e}")
            return 0