"""
MOD-AI: 智能助手模块 - 会话存储
"""
from typing import List, Dict, Any
import uuid
from datetime import datetime

# 内存存储（生产环境建议使用Redis）
_sessions = {}


def get_or_create_session(session_id: str = None) -> tuple[str, List[Dict]]:
    """
    获取或创建会话
    返回 (session_id, history)
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    if session_id not in _sessions:
        _sessions[session_id] = {
            'history': [],
            'created_at': datetime.utcnow().isoformat()
        }

    return session_id, _sessions[session_id]['history']


def get_session_history(session_id: str) -> List[Dict]:
    """
    获取指定会话的历史消息列表
    """
    if session_id in _sessions:
        # 只返回最近的20条消息
        return _sessions[session_id]['history'][-20:]
    return []


def add_message_to_session(session_id: str, role: str, content: str):
    """
    添加消息到会话历史
    """
    session_id, history = get_or_create_session(session_id)
    history.append({
        'role': role,
        'content': content,
        'timestamp': datetime.utcnow().isoformat()
    })
    # 保留最近的20条消息
    _sessions[session_id]['history'] = history[-20:]


def clear_session(session_id: str):
    """
    清除指定会话的历史记录
    """
    if session_id in _sessions:
        del _sessions[session_id]
