"""
MOD-AI: 智能助手模块 - 会话存储
"""
from typing import List, Dict, Any, Optional
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
            'accumulated_slots': {},  # 新增：累积的槽位
            'last_intent': None,       # 新增：上一次的意图
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


# ============================================================================
# 新增：槽位累积功能
# ============================================================================

def get_accumulated_slots(session_id: str) -> Dict[str, Any]:
    """
    获取会话中累积的槽位信息

    Returns:
        dict: 累积的槽位，例如 {"date": "2026-06-06", "has_window": true}
    """
    if session_id in _sessions:
        return _sessions[session_id].get('accumulated_slots', {})
    return {}


def update_accumulated_slots(session_id: str, new_slots: Dict[str, Any]):
    """
    更新会话中的累积槽位

    Args:
        session_id: 会话ID
        new_slots: 新提取的槽位
    """
    if session_id not in _sessions:
        get_or_create_session(session_id)

    # 合并新槽位到累积槽位（新槽位会覆盖旧值）
    _sessions[session_id]['accumulated_slots'].update(new_slots)


def get_last_intent(session_id: str) -> Optional[str]:
    """
    获取上一次的意图类型

    Returns:
        str: 意图类型，如 "query_empty_seat"
    """
    if session_id in _sessions:
        return _sessions[session_id].get('last_intent')
    return None


def set_last_intent(session_id: str, intent_type: str):
    """
    保存当前意图类型

    Args:
        session_id: 会话ID
        intent_type: 意图类型
    """
    if session_id not in _sessions:
        get_or_create_session(session_id)

    _sessions[session_id]['last_intent'] = intent_type
