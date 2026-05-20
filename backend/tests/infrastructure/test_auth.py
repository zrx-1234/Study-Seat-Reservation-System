"""
INF-AUTH 测试：认证与加密模块
覆盖密码哈希、JWT Token、RBAC装饰器、JWT错误回调
"""

import pytest
from datetime import timedelta
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, jwt_required, decode_token

from infrastructure.auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user_id,
    get_jwt_claims,
    register_jwt_callbacks,
    require_permission,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def jwt_app():
    """提供带JWT配置的Flask应用"""
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-32-bytes-long-ok'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    jwt = JWTManager()
    jwt.init_app(app)
    register_jwt_callbacks(jwt)

    @app.route('/me')
    @jwt_required()
    def me():
        return jsonify(user_id=get_current_user_id())

    @app.route('/claims')
    @jwt_required()
    def claims():
        return jsonify(claims=get_jwt_claims())

    @app.route('/admin-only')
    @require_permission('user:manage')
    def admin_only():
        return jsonify(ok=True)

    return app


@pytest.fixture
def jwt_client(jwt_app):
    return jwt_app.test_client()


# ============================================================================
# 1. 密码工具测试
# ============================================================================

class TestPasswordTools:
    """测试密码哈希与验证"""

    def test_hash_password_not_plain(self):
        """哈希后的密码不应等于明文"""
        hashed = hash_password('my_password')
        assert hashed != 'my_password'
        assert isinstance(hashed, str)

    def test_hash_password_different_salts(self):
        """两次哈希同一密码应得到不同结果"""
        hashed1 = hash_password('my_password')
        hashed2 = hash_password('my_password')
        assert hashed1 != hashed2

    def test_verify_password_correct(self):
        """验证正确密码返回True"""
        hashed = hash_password('my_password')
        assert verify_password(hashed, 'my_password') is True

    def test_verify_password_wrong(self):
        """验证错误密码返回False"""
        hashed = hash_password('my_password')
        assert verify_password(hashed, 'wrong_password') is False

    def test_verify_password_empty(self):
        """验证空密码返回False"""
        hashed = hash_password('my_password')
        assert verify_password(hashed, '') is False


# ============================================================================
# 2. JWT Token 创建与解析测试
# ============================================================================

class TestTokenCreation:
    """测试Token创建"""

    def test_create_token_returns_string(self, jwt_app):
        with jwt_app.app_context():
            token = create_token('42')
            assert isinstance(token, str)
            assert len(token) > 0

    def test_create_token_contains_identity(self, jwt_app):
        with jwt_app.app_context():
            token = create_token('42')
            decoded = decode_token(token)
            assert decoded['sub'] == '42'

    def test_create_token_contains_additional_claims(self, jwt_app):
        with jwt_app.app_context():
            token = create_token('42', {'user_type': 'admin', 'permissions': ['user:manage']})
            decoded = decode_token(token)
            assert decoded['user_type'] == 'admin'
            assert decoded['permissions'] == ['user:manage']

    def test_create_token_identity_is_string(self, jwt_app):
        """identity应被强制转为字符串"""
        with jwt_app.app_context():
            token = create_token(42)
            decoded = decode_token(token)
            assert decoded['sub'] == '42'


class TestTokenParsing:
    """测试Token解析（通过HTTP请求）"""

    def test_get_current_user_id_from_valid_token(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            token = create_token('42', {'user_type': 'student'})
        resp = jwt_client.get('/me', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        assert resp.get_json()['user_id'] == 42

    def test_get_jwt_claims_from_valid_token(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            token = create_token('1', {'user_type': 'admin', 'permissions': ['user:manage']})
        resp = jwt_client.get('/claims', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        claims = resp.get_json()['claims']
        assert claims['sub'] == '1'
        assert claims['user_type'] == 'admin'
        assert 'user:manage' in claims['permissions']

    def test_no_token_returns_401(self, jwt_client):
        resp = jwt_client.get('/me')
        assert resp.status_code == 401
        assert '未认证' in resp.get_json()['message']

    def test_invalid_token_returns_401(self, jwt_client):
        resp = jwt_client.get('/me', headers={'Authorization': 'Bearer invalid-token'})
        assert resp.status_code == 401
        assert '无效' in resp.get_json()['message']

    def test_expired_token_returns_401(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            original_expires = jwt_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            jwt_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=-1)
            expired_token = create_token('1', {'user_type': 'student'})
            jwt_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = original_expires

        resp = jwt_client.get('/me', headers={'Authorization': f'Bearer {expired_token}'})
        assert resp.status_code == 401
        assert '过期' in resp.get_json()['message']


# ============================================================================
# 3. JWT 错误回调测试
# ============================================================================

class TestJWTCallbacks:
    """测试JWT错误回调已正确注册"""

    def test_unauthorized_callback_format(self, jwt_client):
        resp = jwt_client.get('/me')
        json = resp.get_json()
        assert json['code'] == 401
        assert json['data'] is None
        assert '未认证' in json['message']

    def test_invalid_token_callback_format(self, jwt_client):
        resp = jwt_client.get('/me', headers={'Authorization': 'Bearer bad.token.here'})
        json = resp.get_json()
        assert json['code'] == 401
        assert json['data'] is None
        assert '无效' in json['message']

    def test_expired_token_callback_format(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            original_expires = jwt_app.config['JWT_ACCESS_TOKEN_EXPIRES']
            jwt_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=-1)
            expired_token = create_token('1')
            jwt_app.config['JWT_ACCESS_TOKEN_EXPIRES'] = original_expires

        resp = jwt_client.get('/me', headers={'Authorization': f'Bearer {expired_token}'})
        json = resp.get_json()
        assert json['code'] == 401
        assert json['data'] is None
        assert '过期' in json['message']


# ============================================================================
# 4. RBAC 装饰器测试
# ============================================================================

class TestRequirePermission:
    """测试权限装饰器"""

    def test_allows_admin_with_permission(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            token = create_token('1', {'user_type': 'admin', 'permissions': ['user:manage']})
        resp = jwt_client.get('/admin-only', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True

    def test_blocks_student(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            token = create_token('1', {'user_type': 'student', 'permissions': []})
        resp = jwt_client.get('/admin-only', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 403
        assert '仅管理员可操作' in resp.get_json()['message']

    def test_blocks_admin_without_permission(self, jwt_client, jwt_app):
        with jwt_app.app_context():
            token = create_token('1', {'user_type': 'admin', 'permissions': ['room:manage']})
        resp = jwt_client.get('/admin-only', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 403
        assert '缺少 user:manage' in resp.get_json()['message']

    def test_blocks_no_token(self, jwt_client):
        resp = jwt_client.get('/admin-only')
        assert resp.status_code == 401
