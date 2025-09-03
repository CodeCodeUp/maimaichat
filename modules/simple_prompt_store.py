"""
简单的提示词存储模块 - 类似TopicStore的实现
"""

import json
import logging
import os
from threading import Lock
from datetime import datetime
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class PromptStore:
    """简单的提示词文件存储"""
    
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.lock = Lock()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认提示词数据"""
        if not os.path.exists(self.storage_file):
            default_prompts = {
                "默认提示词": "你是一个资深新媒体编辑，擅长将话题梳理成适合脉脉的内容。",
                "专业分析": "你是一位行业专家和资深分析师。请基于用户提供的话题，撰写一篇专业、深入的分析文章，适合在脉脉平台发布。",
                "经验分享": "你是一位经验丰富的职场人士。请围绕用户给定的话题，分享实用的职场经验和心得体会。"
            }
            self.save_prompts(default_prompts)
            logger.info("已创建默认提示词文件")
    
    def load_prompts(self) -> Dict[str, str]:
        """加载所有提示词"""
        try:
            with self.lock:
                if os.path.exists(self.storage_file):
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        logger.info(f"已加载 {len(data)} 个提示词")
                        return data
                else:
                    logger.warning("提示词文件不存在")
                    return {}
        except Exception as e:
            logger.error(f"加载提示词失败: {e}")
            return {}
    
    def save_prompts(self, prompts: Dict[str, str]) -> bool:
        """保存所有提示词"""
        try:
            with self.lock:
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(prompts, f, ensure_ascii=False, indent=2)
                logger.info(f"已保存 {len(prompts)} 个提示词")
                return True
        except Exception as e:
            logger.error(f"保存提示词失败: {e}")
            return False