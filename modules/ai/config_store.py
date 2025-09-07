from typing import Dict, List, Optional
import logging

from modules.database.dao import AIConfigDAO, AIConfigSettingsDAO

logger = logging.getLogger(__name__)

class AIConfigStoreDB:
    """AI配置存储管理类 - 数据库版本"""
    
    def __init__(self):
        self.config_dao = AIConfigDAO()
        self.settings_dao = AIConfigSettingsDAO()
        logger.info("初始化AI配置数据库存储")
    
    def get_current_config_id(self) -> str:
        """获取当前配置ID"""
        try:
            return self.settings_dao.get_current_config_id()
        except Exception as e:
            logger.error(f"获取当前配置ID失败: {e}")
            return ""
    
    def set_current_config_id(self, config_id: str) -> bool:
        """设置当前配置ID"""
        try:
            return self.settings_dao.set_current_config_id(config_id)
        except Exception as e:
            logger.error(f"设置当前配置ID失败: {e}")
            return False
    
    def set_current_config(self, config_id: str) -> bool:
        """设置当前配置 - 兼容性方法"""
        # 先检查配置是否存在
        if not self.get_config(config_id):
            logger.error(f"配置不存在: {config_id}")
            return False
        
        return self.set_current_config_id(config_id)
    
    def get_current_config(self) -> Optional[Dict]:
        """获取当前配置"""
        try:
            current_id = self.get_current_config_id()
            if current_id:
                return self.config_dao.find_by_id(current_id)
            
            # 如果没有设置当前配置，返回第一个启用的配置
            enabled_configs = self.config_dao.find_enabled()
            if enabled_configs:
                return enabled_configs[0]
            
            return None
        except Exception as e:
            logger.error(f"获取当前配置失败: {e}")
            return None
    
    def get_all_configs(self) -> List[Dict]:
        """获取所有配置 - 返回数组格式"""
        try:
            configs = self.config_dao.find_all()
            return configs  # 直接返回数组，不转换为字典
        except Exception as e:
            logger.error(f"获取所有配置失败: {e}")
            return []
    
    def get_config(self, config_id: str) -> Optional[Dict]:
        """获取指定配置"""
        try:
            return self.config_dao.find_by_id(config_id)
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            return None
    
    def add_config(self, config_data: Dict) -> str:
        """添加配置"""
        try:
            # 生成配置ID
            import uuid
            config_id = str(uuid.uuid4())
            
            # 准备配置数据
            insert_data = {
                'id': config_id,
                'name': config_data['name'],
                'description': config_data.get('description', ''),
                'api_key': config_data['api_key'],
                'base_url': config_data['base_url'],
                'main_model': config_data['main_model'],
                'assistant_model': config_data.get('assistant_model', ''),
                'enabled': config_data.get('enabled', True)
            }
            
            result = self.config_dao.insert(insert_data)
            if result:
                logger.info(f"已添加AI配置: {config_data['name']}")
                return config_id
            return ""
        except Exception as e:
            logger.error(f"添加AI配置失败: {e}")
            return ""
    
    def update_config(self, config_id: str, config_data: Dict) -> bool:
        """更新配置"""
        try:
            result = self.config_dao.update(config_id, config_data) > 0
            if result:
                logger.info(f"已更新AI配置: {config_id}")
            return result
        except Exception as e:
            logger.error(f"更新AI配置失败: {e}")
            return False
    
    def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        try:
            config = self.config_dao.find_by_id(config_id)
            if config:
                result = self.config_dao.delete(config_id) > 0
                if result:
                    logger.info(f"已删除AI配置: {config['name']}")
                    
                    # 如果删除的是当前配置，清除当前配置ID
                    if self.get_current_config_id() == config_id:
                        self.set_current_config_id("")
                
                return result
            return False
        except Exception as e:
            logger.error(f"删除AI配置失败: {e}")
            return False
    
    def enable_config(self, config_id: str) -> bool:
        """启用配置"""
        return self.update_config(config_id, {'enabled': True})
    
    def disable_config(self, config_id: str) -> bool:
        """禁用配置"""
        return self.update_config(config_id, {'enabled': False})
    
    def get_enabled_configs(self) -> Dict[str, Dict]:
        """获取所有启用的配置"""
        try:
            configs = self.config_dao.find_enabled()
            return {config['id']: config for config in configs}
        except Exception as e:
            logger.error(f"获取启用配置失败: {e}")
            return {}