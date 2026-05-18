"""
INF-AUTH: 认证与加密模块
提供JWT工具、密码哈希等纯技术能力（不依赖业务Model）
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import (
    create_access_token, get_jwt_identity, verify_jwt_in_request, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash

# ============================================================================
# 密码工具
# ============================================================================

def hash_password(password: str) -> str:
    """密码哈希"""
    return generate_password_hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    """验证密码"""
    return check_password_hash(password_hash, password)

# ============================================================================
# JWT Token 工具
# ============================================================================

def create_token(identity: str, additional_claims: dict = None) -> str:
    """
    创建JWT Token
    :param identity: 用户标识（通常是用户ID字符串）
    :param additional_claims: 额外的Claims（如user_type, permissions）
    """
    return create_access_token(identity=str(identity), additional_claims=additional_claims or {})

def get_current_user_id() -> int:
    """
    获取当前用户ID（从JWT解析）
    必须在受保护的路由中调用
    """
    verify_jwt_in_request()
    return int(get_jwt_identity())

def get_jwt_claims() -> dict:
    """
    获取当前JWT的完整Claims
    """
    verify_jwt_in_request()
    return get_jwt()

# ============================================================================
# JWT 错误回调（在应用初始化时注册到jwt对象）
# ============================================================================

def register_jwt_callbacks(jwt_instance):
    """
    注册JWT错误回调
    :param jwt_instance: flask_jwt_extended.JWTManager 实例
    """

    @jwt_instance.unauthorized_loader
    def unauthorized_callback(err_str):
        return jsonify(code=401, message='未认证: {}'.format(err_str), data=None), 401

    @jwt_instance.invalid_token_loader
    def invalid_token_callback(err_str):
        return jsonify(code=401, message='无效的 Token: {}'.format(err_str), data=None), 401

    @jwt_instance.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify(code=401, message='Token 已过期, 请重新登录', data=None), 401

# ============================================================================
# RBAC 装饰器（临时保留，后续可能移入 domain/user 或保持在这里）
# ============================================================================

def require_permission(permission_code: str):
    """
    路由装饰器：要求当前用户拥有指定权限代码。
    学生端接口不需要此装饰器，仅用于管理端。
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_type = claims.get('user_type')
            permissions = claims.get('permissions', [])

            if user_type != 'admin':
                return jsonify(code=403, message='无权限: 仅管理员可操作', data=None), 403

            if permission_code not in permissions:
                return jsonify(code=403, message='无权限: 缺少 {}'.format(permission_code), data=None), 403

            return fn(*args, **kwargs)
        return wrapper
    return decorator
