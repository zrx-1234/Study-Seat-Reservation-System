"""
INF-EXC: 异常与响应模块
提供统一响应格式、领域异常基类、全局异常处理
"""

from flask import jsonify

# ============================================================================
# 统一响应格式
# ============================================================================

def success_response(data=None, message='success', code=200):
    """统一成功响应格式"""
    return jsonify(code=code, message=message, data=data if data is not None {})

def error_response(message='服务器错误', code=500, data=None):
    """统一失败响应格式"""
    return jsonify(code=code, message=message, data=data), code

# ============================================================================
# 领域异常基类
# ============================================================================

class DomainException(Exception):
    """领域异常基类"""
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code
        super().__init__(self.message)

class AuthenticationError(DomainException):
    """认证失败异常"""
    def __init__(self, message: str = '认证失败'):
        super().__init__(message, code=401)

class AuthorizationError(DomainException):
    """授权失败异常"""
    def __init__(self, message: str = '无权限'):
        super().__init__(message, code=403)

class NotFoundError(DomainException):
    """资源不存在异常"""
    def __init__(self, message: str = '资源不存在'):
        super().__init__(message, code=404)

class ConflictError(DomainException):
    """资源冲突异常"""
    def __init__(self, message: str = '资源冲突'):
        super().__init__(message, code=409)

class ValidationError(DomainException):
    """参数校验异常"""
    def __init__(self, message: str = '参数错误'):
        super().__init__(message, code=400)

# ============================================================================
# 全局异常处理器注册
# ============================================================================

def register_error_handlers(app):
    """
    在应用工厂中调用，注册全局异常处理器
    """

    @app.errorhandler(DomainException)
    def handle_domain_exception(err):
        return error_response(message=err.message, code=err.code)

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
