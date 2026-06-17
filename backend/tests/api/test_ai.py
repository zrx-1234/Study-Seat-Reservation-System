"""
AI助手API测试
覆盖: POST /api/v1/ai/chat, GET /api/v1/ai/history, POST /api/v1/ai/clear
"""
import pytest
import json


class TestAIChatAuth:
    """测试聊天接口认证"""

    def test_chat_without_token_returns_401(self, client):
        """未携带JWT应返回401"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'})
        assert resp.status_code == 401

    def test_chat_with_invalid_token_returns_401(self, client):
        """携带无效JWT应返回401"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'},
                           headers={'Authorization': 'Bearer invalid-token'})
        assert resp.status_code == 401


class TestAIChatBasic:
    """测试聊天接口基本功能"""

    def test_chat_empty_message(self, client, auth_headers):
        """空消息应返回400"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': ''},
                           headers=auth_headers)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['code'] == 400

    def test_chat_missing_message(self, client, auth_headers):
        """缺少message字段应返回400"""
        resp = client.post('/api/v1/ai/chat',
                           json={},
                           headers=auth_headers)
        assert resp.status_code == 400

    def test_chat_greeting_returns_reply(self, client, auth_headers):
        """打招呼应返回文本回复"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert 'reply' in data['data']
        assert len(data['data']['reply']) > 0
        assert 'session_id' in data['data']

    def test_chat_returns_action_field(self, client, auth_headers):
        """响应应包含action字段"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'},
                           headers=auth_headers)
        data = resp.get_json()
        assert data['data']['action'] in ('text', 'search_seats',
                                          'show_reservations', 'error')

    def test_chat_returns_rate_limit_headers(self, client, auth_headers):
        """响应头应包含限流信息"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'},
                           headers=auth_headers)
        assert 'X-RateLimit-Limit' in resp.headers
        assert 'X-RateLimit-Remaining' in resp.headers

    def test_chat_uses_rate_limit_window_config(self, client, auth_headers, monkeypatch):
        """响应头应使用配置的限流窗口"""
        monkeypatch.setenv('AI_RATE_LIMIT_WINDOW', '10')
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'},
                           headers=auth_headers)
        assert resp.headers['X-RateLimit-Window'] == '10'


class TestSeatQueryIntent:
    """测试座位查询意图"""

    def test_query_empty_seat(self, client, auth_headers):
        """查询空座位应返回search_seats动作"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '今晚有空座吗'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['action'] == 'search_seats'
        payload = data['data']['payload']
        assert 'available_count' in payload
        assert 'recommendations' in payload
        assert len(payload['recommendations']) > 0

    def test_query_seat_with_window_preference(self, client, auth_headers):
        """查询靠窗座位"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '帮我找靠窗的座位'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['action'] == 'search_seats'

    def test_query_seat_with_plug_preference(self, client, auth_headers):
        """查询有插座的座位"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '有插座的座位'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['action'] == 'search_seats'


class TestReservationIntent:
    """测试预约查询意图"""

    def test_query_my_reservation(self, client, auth_headers):
        """查询我的预约应返回show_reservations动作"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '我的预约'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['action'] == 'show_reservations'
        payload = data['data']['payload']
        assert 'reservation_count' in payload
        assert 'reservations' in payload

    def test_query_today_reservation(self, client, auth_headers):
        """查询今日预约"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '我今天定了哪里的座位'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['action'] == 'show_reservations'


class TestOtherIntents:
    """测试其他意图类型"""

    def test_query_room_info(self, client, auth_headers):
        """查询自习室信息"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '有哪些自习室'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['action'] == 'text'
        assert 'reply' in data['data']

    def test_system_faq(self, client, auth_headers):
        """系统帮助"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '怎么预约座位'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'reply' in data['data']

    def test_unknown_intent(self, client, auth_headers):
        """无法识别的意图应返回文本回复"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '今天天气怎么样'},
                           headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'reply' in data['data']


class TestSessionManagement:
    """测试会话管理"""

    def test_session_persistence(self, client, auth_headers):
        """连续两次请求应使用相同session_id"""
        # 第一次
        resp1 = client.post('/api/v1/ai/chat',
                            json={'message': '你好'},
                            headers=auth_headers)
        sid1 = resp1.get_json()['data']['session_id']

        # 第二次，携带session_id
        resp2 = client.post('/api/v1/ai/chat',
                            json={'message': '今晚有空座吗', 'session_id': sid1},
                            headers=auth_headers)
        sid2 = resp2.get_json()['data']['session_id']

        assert sid1 == sid2

    def test_multiple_rounds_conversation(self, client, auth_headers):
        """多轮对话测试"""
        messages = ['你好', '今晚有空座吗', '我的预约']
        session_id = None

        for msg in messages:
            body = {'message': msg}
            if session_id:
                body['session_id'] = session_id

            resp = client.post('/api/v1/ai/chat',
                               json=body, headers=auth_headers)
            assert resp.status_code == 200
            data = resp.get_json()
            session_id = data['data']['session_id']
            assert session_id is not None


class TestHistoryEndpoint:
    """测试历史记录接口"""

    def test_get_history_missing_session_id(self, client, auth_headers):
        """缺少session_id应返回400"""
        resp = client.get('/api/v1/ai/history', headers=auth_headers)
        assert resp.status_code == 400

    def test_get_history_after_chat(self, client, auth_headers):
        """聊天后获取历史应有消息"""
        # 先发一条消息
        chat_resp = client.post('/api/v1/ai/chat',
                                json={'message': '你好'},
                                headers=auth_headers)
        sid = chat_resp.get_json()['data']['session_id']

        # 获取历史
        resp = client.get(f'/api/v1/ai/history?session_id={sid}',
                          headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'messages' in data['data']
        assert len(data['data']['messages']) >= 2  # user + assistant

    def test_history_not_authenticated(self, client):
        """未认证获取历史应返回401"""
        resp = client.get('/api/v1/ai/history?session_id=test')
        assert resp.status_code == 401


class TestClearSession:
    """测试清除会话"""

    def test_clear_session(self, client, auth_headers):
        """清除会话后历史应为空"""
        # 先发消息
        chat_resp = client.post('/api/v1/ai/chat',
                                json={'message': '你好'},
                                headers=auth_headers)
        sid = chat_resp.get_json()['data']['session_id']

        # 确认有历史
        hist_resp = client.get(f'/api/v1/ai/history?session_id={sid}',
                               headers=auth_headers)
        assert len(hist_resp.get_json()['data']['messages']) >= 2

        # 清除
        clear_resp = client.post('/api/v1/ai/clear',
                                 json={'session_id': sid},
                                 headers=auth_headers)
        assert clear_resp.status_code == 200

        # 验证已清空
        hist_resp2 = client.get(f'/api/v1/ai/history?session_id={sid}',
                                headers=auth_headers)
        assert len(hist_resp2.get_json()['data']['messages']) == 0

    def test_clear_without_session_id(self, client, auth_headers):
        """不提供session_id也应正常返回"""
        resp = client.post('/api/v1/ai/clear',
                           json={},
                           headers=auth_headers)
        assert resp.status_code == 200

    def test_clear_not_authenticated(self, client):
        """未认证清除应返回401"""
        resp = client.post('/api/v1/ai/clear',
                           json={'session_id': 'test'})
        assert resp.status_code == 401


class TestResponseFormat:
    """测试响应格式一致性"""

    def test_response_structure(self, client, auth_headers):
        """验证响应遵循统一格式"""
        resp = client.post('/api/v1/ai/chat',
                           json={'message': '你好'},
                           headers=auth_headers)
        data = resp.get_json()

        # 统一响应格式: code, message, data
        assert 'code' in data
        assert 'message' in data
        assert 'data' in data

        # data中应包含: reply, action, payload, session_id
        inner = data['data']
        assert 'reply' in inner
        assert 'action' in inner
        assert 'payload' in inner
        assert 'session_id' in inner
