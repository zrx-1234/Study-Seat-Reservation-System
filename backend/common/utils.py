"""
通用工具函数
"""

from flask import jsonify


def success_response(data=None, message='success', code=200):
    """统一成功响应格式"""
    return jsonify(code=code, message=message, data=data if data is not None else {})


def error_response(message='服务器错误', code=500, data=None):
    """统一失败响应格式"""
    return jsonify(code=code, message=message, data=data), code


# ---------------------------------------------------------------------------
# 全局异常处理器注册（在 create_app 中调用）
# ---------------------------------------------------------------------------

def register_error_handlers(app):
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
        # 如果异常已经被上面的 handler 处理过，则不再重复捕获
        from werkzeug.exceptions import HTTPException
        if isinstance(err, HTTPException):
            raise err
        return error_response(message=str(err) or '未知错误', code=500)
