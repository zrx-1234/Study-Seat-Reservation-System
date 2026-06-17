"""
AI模块单元测试 - LLM客户端测试
"""
import sys
import types

import pytest
from domain.ai.llm_client import MockLLMClient, OpenAIClient, create_llm_client


class TestMockLLMClient:
    """测试Mock LLM客户端"""

    def setup_method(self):
        """初始化测试"""
        self.client = MockLLMClient()

    def test_chat_about_seats(self):
        """测试关于座位的聊天"""
        messages = [{"role": "user", "content": "今晚有空座吗？"}]
        response = self.client.chat(messages)

        assert isinstance(response, str)
        assert len(response) > 0
        assert '座位' in response or '推荐' in response

    def test_parse_intent_seat_query(self):
        """测试意图识别 - 查询座位"""
        result = self.client.parse_intent("明天晚上有空座吗")

        assert result['intent'] == 'query_empty_seat'
        assert result['confidence'] > 0.8
        assert 'slots' in result

    def test_parse_intent_reservation_query(self):
        """测试意图识别 - 查询预约"""
        result = self.client.parse_intent("我的预约")

        assert result['intent'] == 'query_my_reservation'
        assert result['confidence'] > 0.9

    def test_parse_intent_notification_query(self):
        """测试意图识别 - 查询通知"""
        result = self.client.parse_intent("有没有新通知")

        assert result['intent'] == 'query_notification'
        assert result['confidence'] > 0.8


class TestOpenAIClient:
    """测试OpenAI客户端"""

    def test_create_openai_client_uses_env_model(self, monkeypatch):
        """测试工厂函数读取OPENAI_MODEL"""
        monkeypatch.setenv('OPENAI_API_KEY', 'sk-test')
        monkeypatch.setenv('OPENAI_MODEL', 'test-model')

        client = create_llm_client('openai')

        assert isinstance(client, OpenAIClient)
        assert client.model == 'test-model'

    def test_create_openai_client_without_api_key(self, monkeypatch):
        """测试缺少OpenAI API Key时抛出明确错误"""
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)

        with pytest.raises(ValueError, match='OPENAI_API_KEY'):
            create_llm_client('openai')

    def test_openai_chat_uses_sdk_parameters(self, monkeypatch):
        """测试OpenAI调用参数，不访问真实网络"""
        captured = {}

        class FakeCompletions:
            def create(self, **kwargs):
                captured.update(kwargs)
                message = types.SimpleNamespace(content='测试回复')
                choice = types.SimpleNamespace(message=message)
                return types.SimpleNamespace(choices=[choice])

        class FakeChat:
            def __init__(self):
                self.completions = FakeCompletions()

        class FakeOpenAI:
            def __init__(self, api_key=None, base_url=None):
                captured['api_key'] = api_key
                captured['base_url'] = base_url
                self.chat = FakeChat()

        fake_openai = types.SimpleNamespace(OpenAI=FakeOpenAI)
        monkeypatch.setitem(sys.modules, 'openai', fake_openai)
        monkeypatch.setenv('OPENAI_BASE_URL', 'https://example.test/v1')

        client = OpenAIClient(api_key='sk-test', model='test-model')
        response = client.chat(
            [{"role": "user", "content": "你好"}],
            temperature=0.1,
            max_tokens=123,
            timeout=5
        )

        assert response == '测试回复'
        assert captured['api_key'] == 'sk-test'
        assert captured['base_url'] == 'https://example.test/v1'
        assert captured['model'] == 'test-model'
        assert captured['messages'] == [{"role": "user", "content": "你好"}]
        assert captured['temperature'] == 0.1
        assert captured['max_tokens'] == 123
        assert captured['timeout'] == 5

    def test_openai_parse_intent_from_markdown_json(self, monkeypatch):
        """测试解析Markdown JSON代码块"""
        client = OpenAIClient(api_key='sk-test', model='test-model')
        monkeypatch.setattr(
            client,
            'chat',
            lambda *args, **kwargs: '```json\n{"intent":"query_empty_seat","confidence":0.91,"slots":{"date":"today"}}\n```'
        )

        result = client.parse_intent("今天有空座吗")

        assert result['intent'] == 'query_empty_seat'
        assert result['confidence'] == 0.91
        assert result['slots'] == {'date': 'today'}


class TestLLMClientFactory:
    """测试LLM客户端工厂"""

    def test_create_mock_client(self):
        """测试创建Mock客户端"""
        client = create_llm_client('mock')
        assert isinstance(client, MockLLMClient)

    def test_create_mock_client_with_none_provider(self):
        """测试空提供商默认创建Mock客户端"""
        client = create_llm_client(None)
        assert isinstance(client, MockLLMClient)

    def test_create_invalid_provider(self):
        """测试创建不支持的提供商"""
        with pytest.raises(ValueError):
            create_llm_client('invalid_provider')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
