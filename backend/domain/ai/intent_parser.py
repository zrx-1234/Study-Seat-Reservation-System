"""
MOD-AI: 智能助手模块 - 意图识别实现

实现策略（可分层）：
  Level 1: 关键词匹配（保底方案，无需外部依赖）
  Level 2: 大语言模型 + Prompt Engineering（提升体验）
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, date
import re


# ============================================================================
# 意图类型定义
# ============================================================================

INTENT_TYPES = {
    'query_empty_seat': '查询空座位',
    'query_room_info': '查询自习室信息',
    'query_my_reservation': '查询我的预约',
    'query_notification': '查询通知',
    'system_faq': '系统帮助',
    'chitchat': '闲聊',
    'unknown': '无法识别'
}


# ============================================================================
# 槽位提取规则
# ============================================================================

def extract_date(message: str) -> Optional[str]:
    """提取日期槽位"""
    message_lower = message.lower()
    today = date.today()

    if '今天' in message or '今日' in message:
        return today.isoformat()
    elif '明天' in message or '明日' in message:
        return (today + timedelta(days=1)).isoformat()
    elif '后天' in message:
        return (today + timedelta(days=2)).isoformat()
    elif '周末' in message:
        # 找到下一个周六
        days_ahead = 5 - today.weekday()  # 5 = Saturday
        if days_ahead <= 0:
            days_ahead += 7
        return (today + timedelta(days=days_ahead)).isoformat()

    # 匹配 "X月X日" 格式
    date_match = re.search(r'(\d+)月(\d+)日', message)
    if date_match:
        month, day = int(date_match.group(1)), int(date_match.group(2))
        try:
            return date(today.year, month, day).isoformat()
        except ValueError:
            pass

    return None


def extract_time_range(message: str) -> Optional[tuple]:
    """提取时间段槽位"""
    message_lower = message.lower()

    time_ranges = {
        '早上': ('08:00', '12:00'),
        '上午': ('08:00', '12:00'),
        '中午': ('12:00', '14:00'),
        '下午': ('14:00', '18:00'),
        '晚上': ('18:00', '22:00'),
        '今晚': ('18:00', '22:00'),
    }

    for keyword, time_range in time_ranges.items():
        if keyword in message_lower:
            return time_range

    return None


def extract_seat_preferences(message: str) -> Dict[str, bool]:
    """提取座位偏好槽位"""
    prefs = {}
    message_lower = message.lower()

    if '靠窗' in message_lower or '窗边' in message_lower:
        prefs['has_window'] = True

    if '插座' in message_lower or '电源' in message_lower or '充电' in message_lower:
        prefs['has_plug'] = True

    return prefs


# ============================================================================
# Level 1: 关键词匹配意图识别
# ============================================================================

def parse_intent_by_keywords(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    使用关键词匹配识别意图（Level 1）

    Args:
        message: 用户输入消息
        context: 上下文信息（可选）

    Returns:
        dict: {"intent_type": "...", "confidence": 0.8, "slots": {...}}
    """
    message_lower = message.lower()
    context = context or {}

    intent_type = 'unknown'
    confidence = 0.0
    slots = {}

    # 意图匹配优先级：先匹配具体模式，再匹配通用模式
    # 注意：需要先检查更具体的模式，避免被通用关键词错误捕获

    # 1. 闲聊（最具体的关键词）
    if any(kw in message_lower for kw in ['你好', 'hello', 'hi', '谢谢', '再见']):
        intent_type = 'chitchat'
        confidence = 0.9

    # 2. 系统帮助
    elif any(kw in message_lower for kw in ['怎么', '如何', '帮助', 'help', '使用']):
        intent_type = 'system_faq'
        confidence = 0.7

    # 3. 查询通知
    elif any(kw in message_lower for kw in ['通知', '消息', '提醒']):
        intent_type = 'query_notification'
        confidence = 0.8

    # 4. 查询我的预约（在座位查询之前，因为"我定了座位"也包含"座位"）
    elif any(kw in message_lower for kw in ['我的预约', '预约记录', '我预约了', '定了', '订了',
                                              '我有什么预约', '我的座位', '查看预约']):
        intent_type = 'query_my_reservation'
        confidence = 0.85

    # 5. 查询自习室信息（在座位查询之前，因为"有哪些自习室"也包含"自习室"）
    elif any(kw in message_lower for kw in ['哪些自习室', '自习室列表', '有哪些自习室',
                                              '有什么自习室', '图书馆在哪', '图书馆位置']):
        intent_type = 'query_room_info'
        confidence = 0.75

    # 6. 查询空座位（最通用的查询，放在最后）
    elif any(kw in message_lower for kw in ['座位', '空座', '位置', '自习室', '有没有', '还有',
                                              '可用', '空闲', '空的', '空位']):
        intent_type = 'query_empty_seat'
        confidence = 0.7

        # 提取槽位
        date_slot = extract_date(message)
        if date_slot:
            slots['date'] = date_slot

        time_range = extract_time_range(message)
        if time_range:
            slots['start_time'], slots['end_time'] = time_range

        prefs = extract_seat_preferences(message)
        slots.update(prefs)

    else:
        intent_type = 'unknown'
        confidence = 0.0

    return {
        'intent_type': intent_type,
        'confidence': confidence,
        'slots': slots
    }


# ============================================================================
# Level 2: LLM增强意图识别
# ============================================================================

def parse_intent_by_llm(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    使用LLM识别意图（Level 2）

    TODO: 实现LLM调用逻辑
    当前实现：调用llm_client的parse_intent，并传递上下文
    """
    from domain.ai.llm_client import create_llm_client
    import os

    provider = os.getenv('LLM_PROVIDER', 'mock')
    client = create_llm_client(provider)

    # 准备上下文信息
    history = context.get('history', []) if context else []

    # 如果有历史对话，将其包含在上下文中
    # 注意：这里只传递最近的几条消息，避免token超限
    context_messages = []
    if history:
        recent_history = history[-3:]  # 最近3轮对话
        for msg in recent_history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                context_messages.append({'role': role, 'content': content})

    # 调用LLM进行意图识别
    result = client.parse_intent(message, context_messages)

    return {
        'intent_type': result.get('intent', 'unknown'),
        'confidence': result.get('confidence', 0.5),
        'slots': result.get('slots', {})
    }


# ============================================================================
# 主入口：两级识别策略
# ============================================================================

def parse_intent(message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    解析用户自然语言消息，识别意图与提取槽位

    实现策略：
      1. 始终优先调用 LLM 进行意图识别
      2. 使用关键词规则提取的槽位作为补充
      3. 如果 LLM 调用失败，降级回关键词匹配结果

    Args:
        message: 用户输入消息
        context: 上下文信息（可选）

    Returns:
        dict: {
            "intent_type": "query_empty_seat",
            "confidence": 0.85,
            "slots": {"date": "2026-06-05", "has_window": true}
        }
    """
    # 关键词匹配仅作为槽位补充和LLM失败时的保底方案
    keyword_result = parse_intent_by_keywords(message, context)

    try:
        llm_result = parse_intent_by_llm(message, context)

        # 保留关键词规则稳定提取出的日期/时间/偏好槽位，再用LLM槽位覆盖同名字段
        merged_slots = dict(keyword_result.get('slots', {}))
        merged_slots.update(llm_result.get('slots', {}))
        llm_result['slots'] = merged_slots

        if 'intent_type' not in llm_result:
            llm_result['intent_type'] = 'unknown'
        if 'confidence' not in llm_result:
            llm_result['confidence'] = 0.5

        print(f"使用LLM识别结果: intent={llm_result['intent_type']}, confidence={llm_result['confidence']}")
        return llm_result

    except Exception as e:
        # LLM失败时降级到关键词匹配结果，保证AI助手仍可用
        print(f"LLM意图识别失败，降级到关键词匹配: {e}")
        return keyword_result
