"""
MOD-AI: 智能助手模块 - 意图识别实现
"""
from typing import Dict, Any


def parse_intent(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    解析用户自然语言消息，识别意图与提取槽位
    实现策略（可分层）：
      Level 1: 关键词匹配（保底方案，无需外部依赖）
      Level 2: 大语言模型 + Prompt Engineering（提升体验）
    返回意图类型、置信度、提取参数（如日期、偏好条件）
    """
    # TODO: 实现意图识别逻辑
    # 保底实现：关键词匹配
    message_lower = message.lower()

    intent_type = 'unknown'
    slots = {}
    confidence = 0.0

    # 简单关键词匹配示例
    if any(keyword in message_lower for keyword in ['座位', '空座', '自习室', '预约', 'book']):
        intent_type = 'query_empty_seat'
        confidence = 0.6
    elif any(keyword in message_lower for keyword in ['我的预约', '预约记录', 'my reservation']):
        intent_type = 'query_my_reservation'
        confidence = 0.7
    elif any(keyword in message_lower for keyword in ['签到', 'check in']):
        intent_type = 'query_check_in'
        confidence = 0.5
    elif any(keyword in message_lower for keyword in ['通知', 'notification']):
        intent_type = 'query_notification'
        confidence = 0.5
    elif any(keyword in message_lower for keyword in ['你好', 'hello', 'hi', '帮助', 'help']):
        intent_type = 'text'
        confidence = 0.8

    return {
        'intent_type': intent_type,
        'confidence': confidence,
        'slots': slots
    }
