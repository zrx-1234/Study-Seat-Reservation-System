"""
INF-EXC 测试：异常与响应模块
覆盖统一响应格式、领域异常基类、全局异常处理器
"""

import pytest
from flask import Flask
from werkzeug.exceptions import BadRequest, NotFound

from infrastructure.exceptions import (
    success_response,
    error_response,
    DomainException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ValidationError,
    register_error_handlers,
)


@pytest.fixture
def minimal_app():
    """提供一个最小化的 Flask 应用，用于测试 jsonify"""
    app = Flask(__name__)
    with app.app_context():
        yield app


# ============================================================================
# 1. 统一响应格式测试
# ============================================================================

class TestSuccessResponse:
    """测试成功响应"""

    def test_returns_200_by_default(self, minimal_app):
        resp = success_response()
        assert resp.status_code == 200

    def test_default_format(self, minimal_app):
        resp = success_response()
        json = resp.get_json()
        assert json['code'] == 200
        assert json['message'] == 'success'
        assert json['data'] == {}

    def test_custom_data(self, minimal_app):
        resp = success_response(data={'id': 1})
        json = resp.get_json()
        assert json['data'] == {'id': 1}

    def test_custom_message(self, minimal_app):
        resp = success_response(message='创建成功')
        json = resp.get_json()
        assert json['message'] == '创建成功'

    def test_custom_code(self, minimal_app):
        resp = success_response(code=201)
        json = resp.get_json()
        assert json['code'] == 201

    def test_none_data_defaults_to_empty_dict(self, minimal_app):
        resp = success_response(data=None)
        json = resp.get_json()
        assert json['data'] == {}

    def test_list_data_preserved(self, minimal_app):
        resp = success_response(data=[1, 2, 3])
        json = resp.get_json()
        assert json['data'] == [1, 2, 3]


class TestErrorResponse:
    """测试失败响应"""

    def test_returns_500_by_default(self, minimal_app):
        resp, status_code = error_response()
        assert status_code == 500
        # jsonify 生成的 Response 对象本身 status_code 为 200，
        # 实际 HTTP 状态码由元组第二个元素控制
        assert resp.status_code == 200

    def test_default_format(self, minimal_app):
        resp, _ = error_response()
        json = resp.get_json()
        assert json['code'] == 500
        assert json['message'] == '服务器错误'
        assert json['data'] is None

    def test_custom_code_and_message(self, minimal_app):
        resp, status_code = error_response(message='参数错误', code=400, data={'field': 'name'})
        assert status_code == 400
        json = resp.get_json()
        assert json['code'] == 400
        assert json['message'] == '参数错误'
        assert json['data'] == {'field': 'name'}


# ============================================================================
# 2. 领域异常基类测试
# ============================================================================

class TestDomainExceptionHierarchy:
    """测试异常继承结构与属性"""

    def test_base_exception_attributes(self):
        exc = DomainException('出错了', code=422)
        assert exc.message == '出错了'
        assert exc.code == 422
        assert str(exc) == '出错了'

    def test_authentication_error_defaults(self):
        exc = AuthenticationError()
        assert exc.code == 401
        assert exc.message == '认证失败'

    def test_authentication_error_custom_message(self):
        exc = AuthenticationError('Token无效')
        assert exc.message == 'Token无效'
        assert exc.code == 401

    def test_authorization_error_defaults(self):
        exc = AuthorizationError()
        assert exc.code == 403
        assert exc.message == '无权限'

    def test_not_found_error_defaults(self):
        exc = NotFoundError()
        assert exc.code == 404
        assert exc.message == '资源不存在'

    def test_conflict_error_defaults(self):
        exc = ConflictError()
        assert exc.code == 409
        assert exc.message == '资源冲突'

    def test_validation_error_defaults(self):
        exc = ValidationError()
        assert exc.code == 400
        assert exc.message == '参数错误'

    def test_all_inherit_domain_exception(self):
        assert issubclass(AuthenticationError, DomainException)
        assert issubclass(AuthorizationError, DomainException)
        assert issubclass(NotFoundError, DomainException)
        assert issubclass(ConflictError, DomainException)
        assert issubclass(ValidationError, DomainException)


# ============================================================================
# 3. 全局异常处理器测试
# ============================================================================

@pytest.fixture
def app_with_handlers():
    """带异常处理的测试应用"""
    app = Flask(__name__)
    register_error_handlers(app)

    @app.route('/auth-error')
    def auth_error():
        raise AuthenticationError('登录已过期')

    @app.route('/not-found-error')
    def not_found_error():
        raise NotFoundError('用户不存在')

    @app.route('/validation-error')
    def validation_error():
        raise ValidationError('缺少必填字段')

    @app.route('/conflict-error')
    def conflict_error():
        raise ConflictError('座位已被预约')

    @app.route('/generic-error')
    def generic_error():
        raise RuntimeError('数据库连接失败')

    @app.route('/http-exception')
    def http_exception():
        raise BadRequest('原始HTTP异常')

    @app.route('/not-found-route')
    def missing():
        raise NotFound('路由不存在')

    return app


@pytest.fixture
def client(app_with_handlers):
    return app_with_handlers.test_client()


class TestDomainExceptionHandlers:
    """测试领域异常被正确捕获并转为JSON响应"""

    def test_authentication_error_returns_401(self, client):
        resp = client.get('/auth-error')
        assert resp.status_code == 401
        json = resp.get_json()
        assert json['code'] == 401
        assert json['message'] == '登录已过期'
        assert json['data'] is None

    def test_not_found_error_returns_404(self, client):
        resp = client.get('/not-found-error')
        assert resp.status_code == 404
        json = resp.get_json()
        assert json['code'] == 404
        assert json['message'] == '用户不存在'

    def test_validation_error_returns_400(self, client):
        resp = client.get('/validation-error')
        assert resp.status_code == 400
        json = resp.get_json()
        assert json['code'] == 400
        assert json['message'] == '缺少必填字段'

    def test_conflict_error_returns_409(self, client):
        resp = client.get('/conflict-error')
        assert resp.status_code == 409
        json = resp.get_json()
        assert json['code'] == 409
        assert json['message'] == '座位已被预约'


class TestGenericExceptionHandler:
    """测试通用异常捕获"""

    def test_unexpected_exception_returns_500(self, client):
        resp = client.get('/generic-error')
        assert resp.status_code == 500
        json = resp.get_json()
        assert json['code'] == 500
        assert '数据库连接失败' in json['message']

    def test_http_exception_not_swallowed(self, client):
        """HTTPException 不应被 catch_all 捕获，应继续向上抛"""
        # BadRequest(400) 会被 Flask 原生处理为 HTML 响应（因为测试应用未注册 json errorhandler）
        # 关键验证：它没有被 catch_all 转成 500
        resp = client.get('/http-exception')
        # Flask 默认的 HTTPException 处理会返回对应状态码，不是 500
        assert resp.status_code == 400

    def test_404_route_returns_404_not_500(self, client):
        """不存在的路由返回404，不应被 catch_all 转为500"""
        resp = client.get('/not-found-route')
        assert resp.status_code == 404
