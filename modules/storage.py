import json
import os
import threading
import time
import uuid
from typing import Dict, Any, List, Optional

class JsonKVStore:
    """简单的基于JSON文件的KV存储，线程安全。"""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self._write({})
        else:
            # 验证基本可读性
            try:
                _ = self._read()
            except Exception:
                self._write({})

    def _read(self) -> Dict[str, Any]:
        with open(self.filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        tmp = self.filepath + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.filepath)

    def get_all(self) -> Dict[str, Any]:
        with self._lock:
            return self._read()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            data = self._read()
            return data.get(key)

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            data = self._read()
            data[key] = value
            self._write(data)

    def delete(self, key: str) -> None:
        with self._lock:
            data = self._read()
            if key in data:
                del data[key]
                self._write(data)


def new_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time()*1000)}_{uuid.uuid4().hex[:6]}"


class ChatStore:
    """会话存储：保存chat sessions与消息数组。"""
    def __init__(self, filepath: str):
        self.db = JsonKVStore(filepath)

    def list(self) -> List[Dict[str, Any]]:
        all_data = self.db.get_all()
        return [ { 'id': k, **v } for k, v in all_data.items() ]

    def get(self, chat_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get(chat_id)

    def save(self, chat_id: Optional[str], payload: Dict[str, Any]) -> str:
        # payload: {title?, messages: [...], updated_at}
        if not chat_id:
            chat_id = new_id('chat')
        record = {
            'title': payload.get('title') or '',
            'messages': payload.get('messages') or [],
            'updated_at': payload.get('updated_at') or int(time.time())
        }
        self.db.put(chat_id, record)
        return chat_id

    def delete(self, chat_id: str) -> None:
        self.db.delete(chat_id)


class DraftStore:
    """草稿存储：保存标题、内容、topic_url等。"""
    def __init__(self, filepath: str):
        self.db = JsonKVStore(filepath)

    def list(self) -> List[Dict[str, Any]]:
        all_data = self.db.get_all()
        return [ { 'id': k, **v } for k, v in all_data.items() ]

    def get(self, draft_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get(draft_id)

    def save(self, draft_id: Optional[str], payload: Dict[str, Any]) -> str:
        # payload: {title, content, topic_url, updated_at}
        if not draft_id:
            draft_id = new_id('draft')
        record = {
            'title': payload.get('title') or '',
            'content': payload.get('content') or '',
            'topic_url': payload.get('topic_url') or '',
            'updated_at': payload.get('updated_at') or int(time.time())
        }
        self.db.put(draft_id, record)
        return draft_id

    def delete(self, draft_id: str) -> None:
        self.db.delete(draft_id)

