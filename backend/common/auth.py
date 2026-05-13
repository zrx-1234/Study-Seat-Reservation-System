"""
认证与权限模块
提供 JWT 签发、校验、当前用户获取、RBAC 权限校验装饰器
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, get_jwt_identity, verify_jwt_in_request
)
from werkzeug.security import check_password_hash

from common.models import db, User, Permission

jwt = JWTManager()


def init_jwt(app):
    """在应用工厂中初始化 JWTManager"""
    jwt.init_app(app)


# ---------------------------------------------------------------------------
# JWT 错误回调（统一返回 {code, message, data} 格式）
# ---------------------------------------------------------------------------

@jwt.unauthorized_loader
def unauthorized_callback(err_str):
    return jsonify(code=401, message='未认证: {}'.format(err_str), data=None), 401


@jwt.invalid_token_loader
def invalid_token_callback(err_str):
    return jsonify(code=401, message='无效的 Token: {}'.format(err_str), data=None), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify(code=401, message='Token 已过期, 请重新登录', data=None), 401


# ---------------------------------------------------------------------------
# 登录与 Token
# ---------------------------------------------------------------------------

def authenticate_user(username: str, password: str):
    """
    验证用户名密码。
    返回 (user, token_string) 或 (None, None)
    """
    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, None

    # identity 存用户 ID，additional_claims 存用户类型和权限代码列表
    permissions = []
    if user.user_type == 'admin':
        perm_codes = set()
        for role in user.roles:
            for p in role.permissions:
                perm_codes.add(p.code)
        permissions = list(perm_codes)

    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'user_type': user.user_type,
            'permissions': permissions
        }
    )
    return user, token


# ---------------------------------------------------------------------------
# 当前用户获取
# ---------------------------------------------------------------------------

def get_current_user():
    """在受保护的路由中获取当前登录用户对象"""
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


# ---------------------------------------------------------------------------
# RBAC 装饰器
# ---------------------------------------------------------------------------

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


def get_jwt():
    """辅助函数：获取当前 JWT 的完整 claims"""
    from flask_jwt_extended import get_jwt as _get_jwt
    return _get_jwt()
