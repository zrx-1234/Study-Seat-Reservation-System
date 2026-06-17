"""
AI模块服务测试
"""
from datetime import date, time

import pytest

from domain.ai.dto import ActionResultDTO, IntentDTO
from domain.ai import service


def _seat_result(count=6):
    return ActionResultDTO(
        success=True,
        data={
            'available_count': count,
            'recommendations': [
                {
                    'room_name': '理科图书馆301',
                    'seat_number': 'A01',
                    'has_window': True,
                    'has_plug': False
                }
            ]
        }
    )


def test_mock_provider_does_not_call_llm_reply(monkeypatch):
    """mock模式下即使开启USE_LLM_REPLY也不调用LLM"""
    monkeypatch.setenv('LLM_PROVIDER', 'mock')
    monkeypatch.setenv('USE_LLM_REPLY', 'true')

    def fail_if_called(*args, **kwargs):
        raise AssertionError('不应在mock模式下调用LLM')

    monkeypatch.setattr(service, '_generate_reply_with_llm', fail_if_called)

    intent = IntentDTO('query_empty_seat', 0.9, {})
    reply = service.generate_reply(_seat_result(), '今晚有空座吗', intent)

    assert '找到 6 个可用座位' in reply
    assert '理科图书馆301 A01' in reply


def test_openai_provider_uses_llm_reply(monkeypatch):
    """openai模式且开启USE_LLM_REPLY时调用LLM生成回复"""
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('USE_LLM_REPLY', 'true')
    monkeypatch.setattr(
        service,
        '_generate_reply_with_llm',
        lambda user_message, data, intent_type: 'LLM reply'
    )

    intent = IntentDTO('query_empty_seat', 0.9, {})
    reply = service.generate_reply(_seat_result(), '今晚有空座吗', intent)

    assert reply == 'LLM reply'


def test_llm_reply_failure_falls_back_to_template(monkeypatch):
    """LLM生成失败时降级为模板回复"""
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('USE_LLM_REPLY', 'true')

    def raise_error(*args, **kwargs):
        raise Exception('LLM不可用')

    monkeypatch.setattr(service, '_generate_reply_with_llm', raise_error)

    intent = IntentDTO('query_empty_seat', 0.9, {})
    reply = service.generate_reply(_seat_result(), '今晚有空座吗', intent)

    assert '找到 6 个可用座位' in reply
    assert '理科图书馆301 A01' in reply


def test_chitchat_uses_llm_reply_when_enabled(monkeypatch):
    """闲聊在启用真实provider时可使用LLM回复"""
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('USE_LLM_REPLY', 'true')
    monkeypatch.setattr(
        service,
        '_generate_reply_with_llm',
        lambda user_message, data, intent_type: '你好，我是AI助手'
    )

    action_result = ActionResultDTO(success=True, data={'reply': '你好！有什么可以帮您的吗？'})
    intent = IntentDTO('chitchat', 0.8, {})

    assert service.generate_reply(action_result, '你好', intent) == '你好，我是AI助手'


def test_query_empty_seat_uses_reservation_search(monkeypatch):
    """查询空座位应调用预约模块的真实座位搜索接口并适配payload"""
    captured = {}

    def fake_search_seats(**kwargs):
        captured.update(kwargs)
        return {
            'items': [
                {
                    'id': 9,
                    'seat_number': 'A01',
                    'room_id': 3,
                    'room_name': '理科图书馆301',
                    'has_window': True,
                    'has_plug': False,
                    'status': 'available',
                    'available_slots': ['18:00-22:00'],
                }
            ],
            'total': 1,
            'page': 1,
            'per_page': 20,
            'pages': 1,
        }

    from domain.reservation import service as resv_service
    monkeypatch.setattr(resv_service, 'search_seats', fake_search_seats)

    result = service._handle_query_empty_seat({
        'date': '2026-06-18',
        'start_time': '18:00',
        'end_time': '22:00',
        'has_window': 'true',
        'has_plug': False,
    }, user_id=1)

    assert result.success is True
    assert captured['query_date'] == date(2026, 6, 18)
    assert captured['start_time'] == time(18, 0)
    assert captured['end_time'] == time(22, 0)
    assert captured['has_window'] is True
    assert captured['has_plug'] is False
    assert result.data['available_count'] == 1
    assert result.data['recommendations'][0]['seat_id'] == 9
    assert result.data['recommendations'][0]['room_name'] == '理科图书馆301'


def test_query_empty_seat_empty_result_does_not_use_mock(monkeypatch):
    """真实查询为空时应返回空推荐而不是固定mock座位"""
    from domain.reservation import service as resv_service
    monkeypatch.setattr(resv_service, 'search_seats', lambda **kwargs: {
        'items': [],
        'total': 0,
        'page': 1,
        'per_page': 20,
        'pages': 0,
    })

    result = service._handle_query_empty_seat({}, user_id=1)

    assert result.success is True
    assert result.data['available_count'] == 0
    assert result.data['recommendations'] == []


def test_query_my_reservation_uses_active_reservations(monkeypatch):
    """查询我的预约应调用预约模块的进行中预约接口"""
    reservations = [
        {
            'id': 1,
            'seat_number': 'A05',
            'room_name': '理科图书馆301',
            'start_time': '2026-06-18T14:00:00',
            'end_time': '2026-06-18T16:00:00',
            'status': 'reserved',
        },
        {
            'id': 2,
            'seat_number': 'B01',
            'room_name': '主图书馆自习区',
            'start_time': '2026-06-19T09:00:00',
            'end_time': '2026-06-19T10:00:00',
            'status': 'checked_in',
        },
    ]

    from domain.reservation import service as resv_service
    monkeypatch.setattr(resv_service, 'get_user_active_reservations', lambda user_id: reservations)

    result = service._handle_query_my_reservation(user_id=1)

    assert result.success is True
    assert result.data['reservation_count'] == 2
    assert result.data['reservations'] == reservations


def test_query_room_info_uses_student_room_list(monkeypatch):
    """查询自习室信息应调用学生端房间列表服务"""
    captured = {}
    rooms = [
        {'id': 1, 'name': '理科图书馆301', 'location': '理科楼3层', 'available_seats': 8},
    ]

    def fake_list_rooms_for_student(**kwargs):
        captured.update(kwargs)
        return {'items': rooms}

    from domain.reservation import service as resv_service
    monkeypatch.setattr(resv_service, 'list_rooms_for_student', fake_list_rooms_for_student)

    result = service._handle_query_room_info({'date': '2026-06-18', 'room_type': 'public'})

    assert result.success is True
    assert captured['query_date'] == date(2026, 6, 18)
    assert captured['room_type'] == 'public'
    assert result.data['room_count'] == 1
    assert result.data['rooms'] == rooms


def test_query_notification_uses_notification_list(monkeypatch):
    """查询通知应调用通知模块的未读通知列表"""
    captured = {}

    def fake_list_notifications(**kwargs):
        captured.update(kwargs)
        return {
            'items': [{'id': 1, 'content': '预约即将开始', 'is_read': False}],
            'total': 1,
            'page': 1,
            'per_page': 5,
            'pages': 1,
            'unread_count': 3,
        }

    from domain.notification import service as notif_service
    monkeypatch.setattr(notif_service, 'list_notifications', fake_list_notifications)

    result = service._handle_query_notification(user_id=1)

    assert result.success is True
    assert captured == {'user_id': 1, 'is_read': False, 'page': 1, 'per_page': 5}
    assert result.data['unread_count'] == 3
    assert result.data['latest_notification'] == '预约即将开始'
    assert result.data['notifications'][0]['content'] == '预约即将开始'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
