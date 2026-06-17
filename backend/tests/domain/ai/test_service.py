"""
AI模块服务测试
"""
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
