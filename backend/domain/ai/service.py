"""
MOD-AI: 智能助手模块 - 服务接口
"""

from typing import Optional, List, Dict, Any

# ============================================================================
# AI 助手服务（待实现）
# ============================================================================

def chat(user_id: int, message: str, session_id: str = None) -> Dict[str, Any]:
    """
    智能助手主入口
    """
    # TODO: 实现意图识别、调用相应服务、生成回复
    return {
        'reply': '你好！我是自习室预约助手。有什么可以帮助你的？',
        'action': 'text',
        'payload': {},
        'session_id': session_id or 'default'
    }


def get_session_history(session_id: str) -> List[dict]:
    """获取指定会话的历史消息列表"""
    # TODO: 实现
    return []


def clear_session(session_id: str):
    """清除指定会话的历史记录"""
    # TODO: 实现
    pass


# ============================================================================
# 内部核心函数（不对外暴露给非AI模块）
# ============================================================================

def parse_intent(message: str, context: dict) -> dict:
    """解析用户自然语言消息，识别意图与提取槽位"""
    # TODO: 实现
    return {'intent': 'unknown', 'confidence': 0, 'slots': {}}


def execute_intent(intent: dict, user_id: int) -> dict:
    """根据解析后的意图，调用对应领域模块执行查询或操作"""
    # TODO: 实现
    return {}


def generate_reply(action_result: dict, user_message: str) -> str:
    """将操作结果转化为自然语言回复"""
    # TODO: 实现
    return '已收到你的消息。'


def call_llm(prompt: str, context: List[dict] = None) -> str:
    """调用外部大语言模型API"""
    # TODO: 实现
    return ''
