"""
AI模块单元测试 - LLM客户端测试
"""
import pytest
from domain.ai.llm_client import MockLLMClient, create_llm_client


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


class TestLLMClientFactory:
    """测试LLM客户端工厂"""

    def test_create_mock_client(self):
        """测试创建Mock客户端"""
        client = create_llm_client('mock')
        assert isinstance(client, MockLLMClient)

    def test_create_invalid_provider(self):
        """测试创建不支持的提供商"""
        with pytest.raises(ValueError):
            create_llm_client('invalid_provider')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
