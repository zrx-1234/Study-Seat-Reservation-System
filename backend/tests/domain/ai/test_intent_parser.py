"""
AI模块单元测试 - 意图识别测试
"""
import pytest
from domain.ai.intent_parser import (
    parse_intent,
    parse_intent_by_keywords,
    extract_date,
    extract_time_range,
    extract_seat_preferences
)
from datetime import date, timedelta


class TestIntentParser:
    """测试意图识别功能"""

    def test_parse_intent_prefers_llm_result(self, monkeypatch):
        """主入口应始终优先使用LLM识别结果"""
        def fake_parse_intent_by_llm(message, context=None):
            return {
                'intent_type': 'query_notification',
                'confidence': 0.99,
                'slots': {'source': 'llm'}
            }

        monkeypatch.setattr(
            'domain.ai.intent_parser.parse_intent_by_llm',
            fake_parse_intent_by_llm
        )

        result = parse_intent('今晚有空座吗')

        assert result['intent_type'] == 'query_notification'
        assert result['confidence'] == 0.99
        assert result['slots']['source'] == 'llm'

    def test_parse_intent_falls_back_to_keywords_when_llm_fails(self, monkeypatch):
        """LLM失败时应降级到关键词识别"""
        def raise_error(message, context=None):
            raise Exception('LLM不可用')

        monkeypatch.setattr('domain.ai.intent_parser.parse_intent_by_llm', raise_error)

        result = parse_intent('今晚有空座吗')

        assert result['intent_type'] == 'query_empty_seat'
        assert result['confidence'] > 0.6
        assert result['slots']['start_time'] == '18:00'
        assert result['slots']['end_time'] == '22:00'

    def test_query_empty_seat_intent(self):
        """测试查询空座位意图"""
        result = parse_intent_by_keywords("今晚有空座吗")

        assert result['intent_type'] == 'query_empty_seat'
        assert result['confidence'] > 0.6

    def test_query_my_reservation_intent(self):
        """测试查询我的预约意图"""
        result = parse_intent_by_keywords("我的预约")

        assert result['intent_type'] == 'query_my_reservation'
        assert result['confidence'] > 0.8

    def test_chitchat_intent(self):
        """测试闲聊意图"""
        result = parse_intent_by_keywords("你好")

        assert result['intent_type'] == 'chitchat'
        assert result['confidence'] > 0.8


class TestSlotExtraction:
    """测试槽位提取功能"""

    def test_extract_date_today(self):
        """测试提取"今天"日期"""
        result = extract_date("今天有空座吗")
        assert result == date.today().isoformat()

    def test_extract_date_tomorrow(self):
        """测试提取"明天"日期"""
        result = extract_date("明天晚上")
        tomorrow = date.today() + timedelta(days=1)
        assert result == tomorrow.isoformat()

    def test_extract_time_range_evening(self):
        """测试提取晚上时间段"""
        result = extract_time_range("今晚有空座吗")
        assert result == ('18:00', '22:00')

    def test_extract_time_range_morning(self):
        """测试提取上午时间段"""
        result = extract_time_range("明天上午")
        assert result == ('08:00', '12:00')

    def test_extract_seat_preferences_window(self):
        """测试提取靠窗偏好"""
        result = extract_seat_preferences("我想找个靠窗的座位")
        assert result.get('has_window') is True

    def test_extract_seat_preferences_plug(self):
        """测试提取插座偏好"""
        result = extract_seat_preferences("有插座的座位")
        assert result.get('has_plug') is True

    def test_extract_multiple_preferences(self):
        """测试提取多个偏好"""
        result = extract_seat_preferences("靠窗有插座的座位")
        assert result.get('has_window') is True
        assert result.get('has_plug') is True


class TestComplexIntent:
    """测试复杂意图识别"""

    def test_intent_with_date_and_time(self):
        """测试带日期和时间的意图"""
        result = parse_intent_by_keywords("明天下午有空座吗")

        assert result['intent_type'] == 'query_empty_seat'
        assert 'date' in result['slots']
        assert 'start_time' in result['slots']
        assert 'end_time' in result['slots']

    def test_intent_with_preferences(self):
        """测试带偏好的意图"""
        result = parse_intent_by_keywords("今晚有靠窗的座位吗")

        assert result['intent_type'] == 'query_empty_seat'
        assert result['slots'].get('has_window') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
