"""
v2架构迁移：此文件保留以向后兼容
新代码请从 infrastructure.exceptions 导入
"""

from flask import jsonify

# 优先导入新的实现
try:
    from infrastructure.exceptions import (
        success_response as new_success_response,
        error_response as new_error_response,
        register_error_handlers as new_register_error_handlers,
        DomainException,
        AuthenticationError,
        AuthorizationError,
        NotFoundError,
        ConflictError,
        ValidationError
    )
except ImportError:
    new_success_response = None
    new_error_response = None
    new_register_error_handlers = None


def success_response(data=None, message='success', code=200):
    """统一成功响应格式（v2桥接）"""
    if new_success_response is not None:
        return new_success_response(data=data, message=message, code=code)
    return jsonify(code=code, message=message, data=data if data is not None else {})


def error_response(message='服务器错误', code=500, data=None):
    """统一失败响应格式（v2桥接）"""
    if new_error_response is not None:
        return new_error_response(message=message, code=code, data=data)
    return jsonify(code=code, message=message, data=data), code


def register_error_handlers(app):
    """全局异常处理器注册（v2桥接）"""
    if new_register_error_handlers is not None:
        new_register_error_handlers(app)
    else:
        _register_old_error_handlers(app)


def _register_old_error_handlers(app):
    """旧的异常处理器（兜底）"""
    @app.errorhandler(400)
    def bad_request(err):
        return error_response(message='请求参数错误', code=400)

    @app.errorhandler(401)
    def unauthorized(err):
        return error_response(message='未认证', code=401)

    @app.errorhandler(403)
    def forbidden(err):
        return error_response(message='无权限', code=403)

    @app.errorhandler(404)
    def not_found(err):
        return error_response(message='资源不存在', code=404)

    @app.errorhandler(405)
    def method_not_allowed(err):
        return error_response(message='请求方法不允许', code=405)

    @app.errorhandler(500)
    def internal_error(err):
        return error_response(message='服务器内部错误', code=500)

    @app.errorhandler(Exception)
    def catch_all(err):
        from werkzeug.exceptions import HTTPException
        if isinstance(err, HTTPException):
            raise err
        return error_response(message=str(err) or '未知错误', code=500)
