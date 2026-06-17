"""
MOD-AI: 智能助手模块 - 服务接口

核心职责：
1. 意图识别 -> 2. 执行动作 -> 3. 生成回复
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta, time as dt_time
import time
from domain.ai.dto import ChatResponseDTO, ChatMessageDTO, IntentDTO, ActionResultDTO
from domain.ai import intent_parser, session_store
from domain.ai.logger import logger


# ============================================================================
# 意图到Action的映射
# ============================================================================

def _map_intent_to_action(intent_type: str) -> str:
    """
    将意图类型映射为API文档定义的action类型

    根据《API接口文档》第4节定义，响应中的action字段应为：
    - text: 纯文本回复
    - search_seats: 查询空座并返回推荐
    - show_reservations: 展示用户当前预约
    - redirect: 引导用户到特定页面
    - error: 错误提示

    Args:
        intent_type: 意图类型

    Returns:
        str: API文档定义的action类型
    """
    mapping = {
        'query_empty_seat': 'search_seats',         # 查询空座 → search_seats
        'query_my_reservation': 'show_reservations', # 查询预约 → show_reservations
        'query_room_info': 'text',                  # 查询自习室 → text
        'query_notification': 'text',               # 查询通知 → text
        'system_faq': 'text',                       # 系统帮助 → text
        'chitchat': 'text',                         # 闲聊 → text
        'unknown': 'text'                           # 未知 → text
    }
    return mapping.get(intent_type, 'text')


# ============================================================================
# AI 助手服务（对外接口）
# ============================================================================

def chat(user_id: int, message: str, session_id: str = None) -> Dict[str, Any]:
    """
    智能助手主入口

    执行流程：
    1. 获取或创建会话上下文
    2. 调用 parse_intent() 解析用户意图（带上下文）
    3. 槽位累积：合并历史槽位和新槽位
    4. 根据意图类型调用对应领域模块
    5. 将数据组装为自然语言回复
    6. 保存本次对话到会话历史
    7. 返回结构化响应

    Args:
        user_id: 当前用户ID
        message: 用户输入消息
        session_id: 会话ID（可选）

    Returns:
        dict: ChatResponseDTO的字典形式
    """
    start_time = time.time()

    try:
        # 1. 获取或创建会话
        session_id, history = session_store.get_or_create_session(session_id)

        # 2. 获取累积的槽位和上一次意图
        accumulated_slots = session_store.get_accumulated_slots(session_id)
        last_intent = session_store.get_last_intent(session_id)

        # 3. 构建上下文（包含历史对话、累积槽位、上次意图）
        context = {
            'history': history[-5:] if history else [],
            'user_id': user_id,
            'session_id': session_id,
            'accumulated_slots': accumulated_slots,
            'last_intent': last_intent
        }

        # 4. 解析意图（传递完整上下文）
        intent_start = time.time()
        intent_result = intent_parser.parse_intent(message, context)
        intent_duration = (time.time() - intent_start) * 1000  # 毫秒

        intent = IntentDTO(
            intent_type=intent_result['intent_type'],
            confidence=intent_result['confidence'],
            slots=intent_result['slots']
        )

        # 记录意图识别
        logger.log_intent_recognition(
            message=message,
            intent=intent.intent_type,
            confidence=intent.confidence,
            method='hybrid',
            duration_ms=intent_duration
        )

        # 5. 槽位累积：如果当前意图与上次意图相同或相关，合并槽位
        final_slots = dict(accumulated_slots)
        if intent.slots:
            final_slots.update(intent.slots)

        # 如果意图变化了，清空槽位重新开始
        if last_intent and intent.intent_type != last_intent:
            final_slots = dict(intent.slots)

        # 更新累积槽位和意图
        session_store.update_accumulated_slots(session_id, final_slots)
        session_store.set_last_intent(session_id, intent.intent_type)

        # 6. 添加用户消息到会话历史
        session_store.add_message_to_session(session_id, 'user', message)

        # 7. 执行意图（使用合并后的槽位）
        intent_with_merged_slots = IntentDTO(
            intent_type=intent.intent_type,
            confidence=intent.confidence,
            slots=final_slots
        )
        action_result = execute_intent(intent_with_merged_slots, user_id)

        # 8. 生成回复
        reply = generate_reply(action_result, message, intent_with_merged_slots)

        # 9. 添加助手回复到会话历史
        session_store.add_message_to_session(session_id, 'assistant', reply)

        # 10. 构造响应
        response = ChatResponseDTO(
            reply=reply,
            action=_map_intent_to_action(intent.intent_type) if action_result.success else 'error',
            payload=action_result.data or {},
            session_id=session_id
        )

        # 记录完整会话
        total_duration = (time.time() - start_time) * 1000
        logger.log_chat_session(
            user_id=user_id,
            session_id=session_id,
            message=message,
            intent=intent.intent_type,
            reply_length=len(reply),
            duration_ms=total_duration
        )

        return response.to_dict()

    except Exception as e:
        # 记录错误
        logger.error(
            'Chat failed',
            user_id=user_id,
            message=message,
            error=str(e)
        )
        raise


def get_session_history(session_id: str) -> List[dict]:
    """
    获取指定会话的历史消息列表

    Args:
        session_id: 会话ID

    Returns:
        list: 消息列表
    """
    history = session_store.get_session_history(session_id)
    return history


def clear_session(session_id: str):
    """
    清除指定会话的历史记录

    Args:
        session_id: 会话ID
    """
    session_store.clear_session(session_id)


# ============================================================================
# 内部核心函数（不对外暴露给非AI模块）
# ============================================================================

def _parse_slot_date(value) -> date:
    """将AI槽位中的日期转为 date；缺省或无法识别时使用今天。"""
    if not value:
        return date.today()

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    text = str(value).strip().lower()
    if text in ('today', '今天', '今日'):
        return date.today()
    if text in ('tomorrow', '明天', '明日'):
        return date.today() + timedelta(days=1)

    try:
        return date.fromisoformat(text)
    except ValueError:
        return date.today()


def _parse_slot_time(value):
    """将AI槽位中的时间转为 time；无法识别时返回 None。"""
    if not value:
        return None

    if isinstance(value, dt_time):
        return value

    try:
        parts = str(value).strip().split(':')
        if len(parts) == 1:
            return dt_time(int(parts[0]), 0)
        if len(parts) >= 2:
            return dt_time(int(parts[0]), int(parts[1]))
    except (TypeError, ValueError):
        return None

    return None


def _parse_slot_bool(value):
    """将AI槽位中的布尔偏好转为 bool/None。"""
    if value is None:
        return None
    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()
    if text in ('true', '1', 'yes', 'y', '是', '有'):
        return True
    if text in ('false', '0', 'no', 'n', '否', '无'):
        return False
    return None


def execute_intent(intent: IntentDTO, user_id: int) -> ActionResultDTO:
    """
    根据解析后的意图，调用对应领域模块执行查询或操作

    Args:
        intent: 意图识别结果
        user_id: 当前用户ID

    Returns:
        ActionResultDTO: 执行结果
    """
    try:
        # 根据不同意图类型调用不同的领域模块
        if intent.intent_type == 'query_empty_seat':
            return _handle_query_empty_seat(intent.slots, user_id)

        elif intent.intent_type == 'query_my_reservation':
            return _handle_query_my_reservation(user_id)

        elif intent.intent_type == 'query_room_info':
            return _handle_query_room_info(intent.slots)

        elif intent.intent_type == 'query_notification':
            return _handle_query_notification(user_id)

        elif intent.intent_type == 'system_faq':
            return _handle_system_faq(intent.slots)

        elif intent.intent_type == 'chitchat':
            return _handle_chitchat(intent.slots)

        else:
            return ActionResultDTO(
                success=False,
                error='无法理解您的意图，请换个说法试试。'
            )

    except Exception as e:
        return ActionResultDTO(
            success=False,
            error=f'处理请求时出错: {str(e)}'
        )


def _handle_query_empty_seat(slots: Dict[str, Any], user_id: int) -> ActionResultDTO:
    """处理查询空座位意图"""
    from domain.reservation import service as resv_service

    try:
        query_date = _parse_slot_date(slots.get('date'))
        start_time = _parse_slot_time(slots.get('start_time'))
        end_time = _parse_slot_time(slots.get('end_time'))

        # 时间槽位不完整时不按时间过滤，避免误筛掉可用座位
        if not (start_time and end_time):
            start_time = None
            end_time = None

        search_result = resv_service.search_seats(
            query_date=query_date,
            start_time=start_time,
            end_time=end_time,
            has_window=_parse_slot_bool(slots.get('has_window')),
            has_plug=_parse_slot_bool(slots.get('has_plug')),
            room_type=slots.get('room_type'),
            department=slots.get('department'),
            page=1,
            per_page=20,
        )

        items = search_result.get('items', [])
        recommendations = [
            {
                'seat_id': item.get('id'),
                'seat_number': item.get('seat_number'),
                'room_id': item.get('room_id'),
                'room_name': item.get('room_name'),
                'room_location': item.get('room_location'),
                'has_window': item.get('has_window'),
                'has_plug': item.get('has_plug'),
                'available_slots': item.get('available_slots', []),
                'status': item.get('status'),
            }
            for item in items
        ]

        result = {
            'date': query_date.isoformat(),
            'available_count': search_result.get('total', len(items)),
            'recommendations': recommendations,
            'items': items,
            'total': search_result.get('total', len(items)),
            'page': search_result.get('page', 1),
            'per_page': search_result.get('per_page', 20),
            'pages': search_result.get('pages', 0),
        }

        return ActionResultDTO(success=True, data=result)

    except Exception as e:
        return ActionResultDTO(success=False, error=f'查询座位时出错: {str(e)}')


def _handle_query_my_reservation(user_id: int) -> ActionResultDTO:
    """处理查询我的预约意图"""
    from domain.reservation import service as resv_service

    try:
        reservations = resv_service.get_user_active_reservations(user_id)
        result = {
            'reservation_count': len(reservations),
            'reservations': reservations,
        }

        return ActionResultDTO(success=True, data=result)

    except Exception as e:
        return ActionResultDTO(success=False, error=str(e))


def _handle_query_room_info(slots: Dict[str, Any]) -> ActionResultDTO:
    """处理查询自习室信息意图"""
    from domain.reservation import service as resv_service

    try:
        query_date = _parse_slot_date(slots.get('date'))
        rooms_result = resv_service.list_rooms_for_student(
            room_type=slots.get('room_type'),
            query_date=query_date,
        )
        rooms = rooms_result.get('items', [])
        result = {
            'date': query_date.isoformat(),
            'room_count': len(rooms),
            'rooms': rooms,
            'items': rooms,
        }

        return ActionResultDTO(success=True, data=result)

    except Exception as e:
        return ActionResultDTO(success=False, error=str(e))


def _handle_query_notification(user_id: int) -> ActionResultDTO:
    """处理查询通知意图"""
    from domain.notification import service as notif_service

    try:
        notifications_result = notif_service.list_notifications(
            user_id=user_id,
            is_read=False,
            page=1,
            per_page=5,
        )
        items = notifications_result.get('items', [])
        result = {
            'unread_count': notifications_result.get('unread_count', 0),
            'latest_notification': items[0].get('content', '') if items else '',
            'notifications': items,
            'items': items,
            'total': notifications_result.get('total', len(items)),
            'page': notifications_result.get('page', 1),
            'per_page': notifications_result.get('per_page', 5),
            'pages': notifications_result.get('pages', 0),
        }

        return ActionResultDTO(success=True, data=result)

    except Exception as e:
        return ActionResultDTO(success=False, error=str(e))


def _handle_system_faq(slots: Dict[str, Any]) -> ActionResultDTO:
    """处理系统帮助意图"""
    faq_content = """
    我可以帮您：
    1. 查询空座位 - 例如："今晚有空座吗？"
    2. 查看我的预约 - 例如："我的预约"
    3. 查询自习室信息 - 例如："有哪些自习室？"
    4. 查看通知 - 例如："有没有新通知？"

    您还想了解什么？
    """

    return ActionResultDTO(
        success=True,
        data={'faq_content': faq_content.strip()}
    )


def _handle_chitchat(slots: Dict[str, Any]) -> ActionResultDTO:
    """处理闲聊意图"""
    chitchat_responses = {
        'greeting': '你好！我是自习室预约助手，可以帮您查询座位和管理预约。',
        'thanks': '不客气！很高兴能帮到您。',
        'goodbye': '再见！祝您学习愉快！'
    }

    return ActionResultDTO(
        success=True,
        data={'reply': chitchat_responses.get('greeting')}
    )


def generate_reply(action_result: ActionResultDTO, user_message: str, intent: IntentDTO) -> str:
    """
    将操作结果转化为自然语言回复

    实现策略：
      - 结构化数据优先使用本地模板（响应快、可控）
      - 复杂/开放式问题使用 LLM 生成回复
      - 使用环境变量控制是否启用LLM生成

    Args:
        action_result: 动作执行结果
        user_message: 用户原始消息
        intent: 识别的意图

    Returns:
        str: 自然语言回复
    """
    import os

    # TODO: 实现回复生成逻辑
    # 当前实现：优先使用模板，可选使用LLM增强

    if not action_result.success:
        return action_result.error or '抱歉，处理您的请求时出错了。'

    data = action_result.data or {}

    # 检查是否启用LLM生成回复
    provider = os.getenv('LLM_PROVIDER', 'mock').strip().lower()
    use_llm_reply = (
        os.getenv('USE_LLM_REPLY', 'false').lower() == 'true'
        and provider != 'mock'
    )

    # 根据意图类型生成不同的回复
    if intent.intent_type == 'query_empty_seat':
        count = data.get('available_count', 0)
        if count > 0:
            # 使用模板生成基础回复
            reply = f"找到 {count} 个可用座位。\n\n"
            recs = data.get('recommendations', [])
            if recs:
                reply += "推荐座位：\n"
                for rec in recs[:3]:  # 最多显示3个
                    reply += f"• {rec['room_name']} {rec['seat_number']}"
                    if rec.get('has_window'):
                        reply += " (靠窗)"
                    if rec.get('has_plug'):
                        reply += " (有插座)"
                    reply += "\n"

            # 如果启用LLM，可以让回复更自然
            if use_llm_reply and count > 5:
                try:
                    reply = _generate_reply_with_llm(user_message, data, intent.intent_type)
                except Exception as e:
                    print(f"LLM生成回复失败，使用模板: {e}")
                    # 保持使用模板生成的回复

            return reply
        else:
            return "抱歉，当前没有符合条件的空座位。您可以调整时间或条件再试试。"

    elif intent.intent_type == 'query_my_reservation':
        count = data.get('reservation_count', 0)
        if count > 0:
            reply = f"您当前有 {count} 个预约：\n\n"
            for res in data.get('reservations', []):
                reply += f"• {res['room_name']} {res['seat_number']}\n"
                reply += f"  时间: {res['start_time']} - {res['end_time']}\n"
            return reply
        else:
            return "您当前没有进行中的预约。"

    elif intent.intent_type == 'query_room_info':
        rooms = data.get('rooms', [])
        if rooms:
            reply = f"共有 {len(rooms)} 个自习室：\n\n"
            for room in rooms:
                reply += f"• {room['name']} - {room['location']}\n"
            return reply
        else:
            return "暂时没有可用的自习室信息。"

    elif intent.intent_type == 'query_notification':
        count = data.get('unread_count', 0)
        if count > 0:
            return f"您有 {count} 条未读通知。最新：{data.get('latest_notification', '')}"
        else:
            return "您目前没有未读通知。"

    elif intent.intent_type == 'system_faq':
        return data.get('faq_content', '我可以帮您查询座位、管理预约。')

    elif intent.intent_type == 'chitchat':
        # 闲聊可以使用LLM生成更自然的回复
        if use_llm_reply:
            try:
                return _generate_reply_with_llm(user_message, data, intent.intent_type)
            except:
                pass
        return data.get('reply', '你好！有什么可以帮您的吗？')

    else:
        return '收到您的消息了。'


def _generate_reply_with_llm(user_message: str, data: Dict[str, Any], intent_type: str) -> str:
    """
    使用LLM生成更自然的回复

    Args:
        user_message: 用户原始消息
        data: 查询结果数据
        intent_type: 意图类型

    Returns:
        str: LLM生成的自然语言回复
    """
    from domain.ai.llm_client import create_llm_client
    import os
    import json

    provider = os.getenv('LLM_PROVIDER', 'mock').strip().lower()
    if provider == 'mock':
        # Mock客户端不适合生成回复，直接返回模板
        raise Exception("Mock客户端不支持生成回复")

    client = create_llm_client(provider)

    # 构建Prompt
    system_prompt = """你是一个友好的自习室预约助手。根据查询结果，用自然、友好的语气回复用户。

要求：
1. 回复简洁明了，不超过3句话
2. 使用友好、口语化的语气
3. 重点突出关键信息
4. 不要编造数据，只使用提供的信息"""

    if intent_type == 'query_empty_seat':
        data_str = json.dumps(data, ensure_ascii=False, indent=2)
        user_prompt = f"""用户问：{user_message}

查询结果：
{data_str}

请根据以上结果，用自然友好的语气回复用户。重点提及可用座位数量和推荐的座位。"""

    elif intent_type == 'chitchat':
        user_prompt = f"""用户说：{user_message}

请用简短、友好的语气回复用户。"""

    else:
        raise Exception(f"不支持为 {intent_type} 生成LLM回复")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # 调用LLM生成回复
    reply = client.chat(messages, temperature=0.7, max_tokens=200)
    return reply.strip()


# ============================================================================
# LLM调用接口（向后兼容）
# ============================================================================

def call_llm(prompt: str, context: List[dict] = None) -> str:
    """
    调用外部大语言模型API

    TODO: 实现LLM调用逻辑
    当前实现：委托给 llm_client 模块
    """
    from domain.ai.llm_client import call_llm as llm_call
    return llm_call(prompt, context)
