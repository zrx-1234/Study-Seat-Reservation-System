"""
AI模块单元测试 - 会话存储测试
"""
import pytest
from domain.ai.session_store import (
    get_or_create_session,
    add_message_to_session,
    get_session_history,
    clear_session,
    get_accumulated_slots,
    update_accumulated_slots,
    get_last_intent,
    set_last_intent
)


class TestSessionStore:
    """测试会话存储功能"""

    def setup_method(self):
        """每个测试前清理"""
        # 注意：实际测试中可能需要清理全局_sessions字典

    def test_create_new_session(self):
        """测试创建新会话"""
        session_id, history = get_or_create_session()

        assert session_id is not None
        assert isinstance(history, list)
        assert len(history) == 0

    def test_get_existing_session(self):
        """测试获取已存在的会话"""
        # 创建会话
        session_id1, _ = get_or_create_session()

        # 再次获取相同会话
        session_id2, _ = get_or_create_session(session_id1)

        assert session_id1 == session_id2

    def test_add_message(self):
        """测试添加消息"""
        session_id, _ = get_or_create_session()

        add_message_to_session(session_id, 'user', '你好')
        add_message_to_session(session_id, 'assistant', '你好！有什么可以帮您的？')

        history = get_session_history(session_id)
        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == '你好'
        assert history[1]['role'] == 'assistant'

    def test_clear_session(self):
        """测试清除会话"""
        session_id, _ = get_or_create_session()
        add_message_to_session(session_id, 'user', '测试消息')

        clear_session(session_id)

        history = get_session_history(session_id)
        assert len(history) == 0


class TestSlotAccumulation:
    """测试槽位累积功能"""

    def test_update_accumulated_slots(self):
        """测试更新累积槽位"""
        session_id, _ = get_or_create_session()

        # 第一次更新
        update_accumulated_slots(session_id, {'date': '2026-06-06'})
        slots = get_accumulated_slots(session_id)
        assert slots['date'] == '2026-06-06'

        # 第二次更新（合并）
        update_accumulated_slots(session_id, {'has_window': True})
        slots = get_accumulated_slots(session_id)
        assert slots['date'] == '2026-06-06'
        assert slots['has_window'] is True

    def test_last_intent(self):
        """测试最后意图记录"""
        session_id, _ = get_or_create_session()

        # 设置意图
        set_last_intent(session_id, 'query_empty_seat')

        # 获取意图
        intent = get_last_intent(session_id)
        assert intent == 'query_empty_seat'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
