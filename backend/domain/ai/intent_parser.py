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

    # 1. 查询空座位
    seat_keywords = ['座位', '空座', '位置', '自习室', '有没有', '还有', '可用']
    if any(kw in message_lower for kw in seat_keywords):
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

    # 2. 查询我的预约
    elif any(kw in message_lower for kw in ['我的预约', '预约记录', '我预约了']):
        intent_type = 'query_my_reservation'
        confidence = 0.85

    # 3. 查询自习室信息
    elif any(kw in message_lower for kw in ['哪些自习室', '自习室列表', '图书馆在哪']):
        intent_type = 'query_room_info'
        confidence = 0.75

    # 4. 查询通知
    elif any(kw in message_lower for kw in ['通知', '消息', '提醒']):
        intent_type = 'query_notification'
        confidence = 0.8

    # 5. 系统帮助
    elif any(kw in message_lower for kw in ['怎么', '如何', '帮助', 'help', '使用']):
        intent_type = 'system_faq'
        confidence = 0.7

    # 6. 闲聊
    elif any(kw in message_lower for kw in ['你好', 'hello', 'hi', '谢谢', '再见']):
        intent_type = 'chitchat'
        confidence = 0.9

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

    实现策略（两级 + 降级）：
      1. 先使用关键词匹配（Level 1）
      2. 如果置信度低于阈值，则使用LLM增强（Level 2）
      3. 如果LLM失败，降级回关键词匹配结果

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
    # TODO: 实现意图识别逻辑
    # 当前实现：关键词匹配为主，LLM作为增强，完善降级策略

    # Level 1: 关键词匹配（保底方案）
    keyword_result = parse_intent_by_keywords(message, context)

    # 决定是否使用LLM增强
    confidence_threshold = 0.6
    use_llm = keyword_result['confidence'] < confidence_threshold

    # 也可以通过环境变量强制启用/禁用LLM
    import os
    llm_enabled = os.getenv('LLM_INTENT_RECOGNITION', 'auto')

    if llm_enabled == 'false':
        # 强制禁用LLM，只使用关键词
        return keyword_result
    elif llm_enabled == 'true':
        # 强制启用LLM
        use_llm = True

    # Level 2: 如果需要，尝试使用LLM增强
    if use_llm:
        try:
            llm_result = parse_intent_by_llm(message, context)

            # 如果LLM结果更可信，使用LLM结果
            if llm_result['confidence'] > keyword_result['confidence']:
                # 但是保留关键词匹配提取的槽位（作为补充）
                # 合并槽位：LLM的槽位 + 关键词的槽位
                merged_slots = dict(keyword_result['slots'])
                merged_slots.update(llm_result['slots'])
                llm_result['slots'] = merged_slots

                print(f"使用LLM识别结果: intent={llm_result['intent_type']}, confidence={llm_result['confidence']}")
                return llm_result
            else:
                # LLM置信度不高，使用关键词结果
                print(f"LLM置信度较低，使用关键词匹配结果")
                return keyword_result

        except Exception as e:
            # LLM失败时降级到关键词匹配结果
            print(f"LLM意图识别失败，降级到关键词匹配: {e}")
            return keyword_result

    # 默认返回关键词匹配结果
    return keyword_result
