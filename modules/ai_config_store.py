import json
import os
import uuid
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIConfigStore:
    """AI配置存储管理"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.configs = {}
        self.current_config_id = None
        self._ensure_data_dir()
        self.load_configs()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = os.path.dirname(self.config_file)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def load_configs(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.configs = data.get('configs', {})
                    self.current_config_id = data.get('current_config_id')
                logger.info(f"已加载 {len(self.configs)} 个AI配置")
            else:
                # 使用默认配置初始化
                self._init_default_configs()
                self.save_configs()
        except Exception as e:
            logger.error(f"加载AI配置失败: {e}")
            self._init_default_configs()
    
    def _init_default_configs(self):
        """初始化默认配置"""
        self.configs = {
            "tbai": {
                "name": "TBAI",
                "description": "TBAI AI服务",
                "api_key": "sk-RhixfnCsWWIK8N8tqXmuCItASYMRQhLG4Z1ZIYMmDfhcAPKq",
                "base_url": "https://tbai.xin/v1",
                "main_model": "gemini-2.5-pro-search",
                "assistant_model": "gemini-2.5-flash-search",
                "enabled": True
            },
            "lins": {
                "name": "Lins AI",
                "description": "Lins AI服务",
                "api_key": "sk-6vZIDOh3bs03jVZcv8PYMWnaSgzw8azvF0YynVJurreJThhs",
                "base_url": "https://ai.lins.dev/v1",
                "main_model": "gemini-2.5-pro-preview-06-05",
                "assistant_model": "gemini-2.5-flash-search",
                "enabled": True
            }
        }
        self.current_config_id = "tbai"
        logger.info("已初始化默认AI配置")
    
    def save_configs(self):
        """保存配置到文件"""
        try:
            data = {
                'configs': self.configs,
                'current_config_id': self.current_config_id
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("AI配置已保存")
            return True
        except Exception as e:
            logger.error(f"保存AI配置失败: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置（不包含敏感信息）"""
        configs = {}
        for config_id, config_data in self.configs.items():
            configs[config_id] = {
                "name": config_data["name"],
                "description": config_data["description"],
                "base_url": config_data["base_url"],
                "main_model": config_data["main_model"],
                "assistant_model": config_data.get("assistant_model", ""),
                "enabled": config_data["enabled"],
                "is_current": config_id == self.current_config_id
            }
        return configs
    
    def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """获取指定配置（包含API密钥）"""
        return self.configs.get(config_id)
    
    def add_config(self, config_data: Dict[str, Any]) -> str:
        """添加新配置"""
        # 验证必需字段
        required_fields = ['name', 'base_url', 'api_key', 'main_model']
        for field in required_fields:
            if field not in config_data or not config_data[field].strip():
                raise ValueError(f"缺少必需字段: {field}")
        
        # 生成唯一ID
        config_id = str(uuid.uuid4())[:8]
        
        # 确保配置名称唯一
        existing_names = [config['name'] for config in self.configs.values()]
        if config_data['name'] in existing_names:
            raise ValueError("配置名称已存在")
        
        self.configs[config_id] = {
            "name": config_data['name'].strip(),
            "description": config_data.get('description', '').strip(),
            "api_key": config_data['api_key'].strip(),
            "base_url": config_data['base_url'].strip(),
            "main_model": config_data['main_model'].strip(),
            "assistant_model": config_data.get('assistant_model', '').strip(),
            "enabled": config_data.get('enabled', True)
        }
        
        self.save_configs()
        logger.info(f"已添加AI配置: {config_data['name']}")
        return config_id
    
    def update_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        if config_id not in self.configs:
            return False
        
        # 验证必需字段
        required_fields = ['name', 'base_url', 'api_key', 'main_model']
        for field in required_fields:
            if field in config_data and not config_data[field].strip():
                raise ValueError(f"字段不能为空: {field}")
        
        # 检查名称唯一性（排除当前配置）
        if 'name' in config_data:
            existing_names = [config['name'] for cid, config in self.configs.items() if cid != config_id]
            if config_data['name'] in existing_names:
                raise ValueError("配置名称已存在")
        
        # 更新配置
        for key, value in config_data.items():
            if key in ['name', 'description', 'api_key', 'base_url', 'main_model', 'assistant_model']:
                self.configs[config_id][key] = value.strip() if isinstance(value, str) else value
            elif key == 'enabled':
                self.configs[config_id][key] = bool(value)
        
        self.save_configs()
        logger.info(f"已更新AI配置: {config_id}")
        return True
    
    def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        if config_id not in self.configs:
            return False
        
        if len(self.configs) <= 1:
            raise ValueError("至少需要保留一个AI配置")
        
        # 如果删除的是当前配置，切换到其他配置
        if config_id == self.current_config_id:
            remaining_configs = [cid for cid in self.configs.keys() if cid != config_id]
            self.current_config_id = remaining_configs[0]
        
        del self.configs[config_id]
        self.save_configs()
        logger.info(f"已删除AI配置: {config_id}")
        return True
    
    def set_current_config(self, config_id: str) -> bool:
        """设置当前配置"""
        if config_id not in self.configs:
            return False
        
        if not self.configs[config_id]['enabled']:
            raise ValueError("无法切换到已禁用的配置")
        
        self.current_config_id = config_id
        self.save_configs()
        logger.info(f"已切换到AI配置: {config_id}")
        return True
    
    def get_current_config(self) -> Optional[Dict[str, Any]]:
        """获取当前配置"""
        if self.current_config_id:
            return self.configs.get(self.current_config_id)
        return None
    
    def get_current_config_id(self) -> Optional[str]:
        """获取当前配置ID"""
        return self.current_config_id