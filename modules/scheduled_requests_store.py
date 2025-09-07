import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ScheduledRequestsStore:
    """定时HTTP请求配置存储管理类"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.requests = {}
        self._ensure_file_exists()
        self.load()
    
    def _ensure_file_exists(self):
        """确保存储文件存在"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从文件加载定时请求配置"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.requests = json.load(f)
                logger.info(f"已加载 {len(self.requests)} 个定时请求配置")
        except Exception as e:
            logger.error(f"加载定时请求配置失败: {e}")
            self.requests = {}
            
    def save(self):
        """保存定时请求配置到文件"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.requests, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存 {len(self.requests)} 个定时请求配置")
        except Exception as e:
            logger.error(f"保存定时请求配置失败: {e}")
            raise
    
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
            "created_at": datetime.now().isoformat(),
            "last_executed": None,
            "last_result": None,
            "execution_count": 0
        }
        
        self.requests[request_id] = request_config
        self.save()
        
        logger.info(f"已添加定时请求配置: {name} ({method} {url})")
        return request_id
    
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
        enabled_requests = []
        for request_config in self.requests.values():
            if request_config.get("enabled", True):
                enabled_requests.append(request_config)
        
        # 按创建时间排序
        enabled_requests.sort(key=lambda x: x["created_at"])
        return enabled_requests
    
    def get_all_requests(self) -> List[Dict]:
        """获取所有定时请求配置"""
        requests_list = list(self.requests.values())
        requests_list.sort(key=lambda x: x["created_at"], reverse=True)
        return requests_list
    
    def get_request(self, request_id: str) -> Optional[Dict]:
        """获取单个定时请求配置"""
        return self.requests.get(request_id)
    
    def update_request(self, request_id: str, **kwargs) -> bool:
        """更新定时请求配置"""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        updated = False
        
        # 可更新的字段
        updatable_fields = ['name', 'url', 'method', 'headers', 'data', 'enabled']
        
        for field in updatable_fields:
            if field in kwargs and request.get(field) != kwargs[field]:
                if field == 'method':
                    request[field] = kwargs[field].upper()
                else:
                    request[field] = kwargs[field]
                updated = True
        
        # 特殊处理cookies字段
        if 'cookies' in kwargs:
            cookies_dict = self._parse_cookies(kwargs['cookies']) if kwargs['cookies'] else None
            if request.get('cookies') != cookies_dict:
                request['cookies'] = cookies_dict
                updated = True
        
        if updated:
            request["updated_at"] = datetime.now().isoformat()
            self.save()
            logger.info(f"已更新定时请求配置: {request_id}")
            return True
        
        return False
    
    def delete_request(self, request_id: str) -> bool:
        """删除定时请求配置"""
        if request_id in self.requests:
            request_name = self.requests[request_id]["name"]
            del self.requests[request_id]
            self.save()
            logger.info(f"已删除定时请求配置: {request_name}")
            return True
        return False
    
    def update_execution_result(self, request_id: str, success: bool, 
                              result_data: str = None, error: str = None):
        """更新请求执行结果"""
        if request_id not in self.requests:
            return False
        
        request = self.requests[request_id]
        request["last_executed"] = datetime.now().isoformat()
        request["execution_count"] = request.get("execution_count", 0) + 1
        
        if success:
            request["last_result"] = {
                "success": True,
                "data": result_data,
                "executed_at": request["last_executed"]
            }
        else:
            request["last_result"] = {
                "success": False,
                "error": error,
                "executed_at": request["last_executed"]
            }
        
        self.save()
        return True
    
    def get_enabled_count(self) -> int:
        """获取启用的请求配置数量"""
        return len([r for r in self.requests.values() if r.get("enabled", True)])