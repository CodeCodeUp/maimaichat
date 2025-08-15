import json
import os
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PromptStore:
    """简单的提示词持久化存储（基于JSON文件）"""

    def __init__(self, filepath: str, default_prompts: Dict[str, str]):
        self.filepath = filepath
        self._lock = threading.Lock()
        self._default_prompts = default_prompts or {}
        # 确保目录存在
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        # 如果文件不存在，则初始化
        if not os.path.exists(self.filepath):
            self._write_file(self._default_prompts)
        # 尝试读取一次验证格式
        try:
            _ = self.get_all()
        except Exception as e:
            logger.warning(f"提示词文件损坏，重置为默认：{e}")
            self._write_file(self._default_prompts)

    def _read_file(self) -> Dict[str, str]:
        with open(self.filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 仅保留键值为字符串的项
            return {str(k): str(v) for k, v in data.items()}

    def _write_file(self, data: Dict[str, str]) -> None:
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all(self) -> Dict[str, str]:
        with self._lock:
            return self._read_file()

    def update(self, prompts: Dict[str, str]) -> Dict[str, str]:
        """用传入的prompts覆盖存储（键名为类别，值为模板）。"""
        if not isinstance(prompts, dict):
            raise ValueError('prompts必须是字典')
        normalized = {str(k): str(v) for k, v in prompts.items()}
        with self._lock:
            self._write_file(normalized)
            logger.info("提示词已更新，共 %d 条", len(normalized))
            return normalized

    def reset_to_default(self) -> Dict[str, str]:
        with self._lock:
            self._write_file(self._default_prompts)
            return self._default_prompts.copy()

