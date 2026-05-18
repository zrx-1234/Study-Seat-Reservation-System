"""
v2架构迁移：此文件保留以向后兼容
新代码请从 infrastructure/auth.py 或 domain.user.service 导入
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import (
    JWTManager, verify_jwt_in_request, get_jwt as _get_jwt
)

# 优先导入新的实现
try:
    from infrastructure.auth import (
        hash_password, verify_password,
        create_token, get_current_user_id, get_jwt_claims,
        require_permission as new_require_permission
    )
    from domain.user.service import authenticate
    from domain.user.models import User
    from extensions import jwt as new_jwt
except ImportError:
    # 旧实现作为兜底
    from werkzeug.security import check_password_hash
    from flask_jwt_extended import create_access_token, get_jwt_identity
    from common.models import db, User, Permission

    new_jwt = None

jwt = JWTManager()


def init_jwt(app):
    """
    在应用工厂中初始化 JWTManager
    v2架构: 优先使用 extensions.jwt
    """
    if new_jwt is not None:
        # v2架构路径
        jwt.init_app(app)
        from infrastructure.auth import register_jwt_callbacks
        register_jwt_callbacks(jwt)
    else:
        # v1架构路径（兜底）
        jwt.init_app(app)
        _register_old_callbacks()


def _register_old_callbacks():
    """旧的JWT回调（兜底）"""
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
# 登录与 Token（v2桥接）
# ---------------------------------------------------------------------------

def authenticate_user(username: str, password: str):
    """
    验证用户名密码（v2桥接函数）
    返回 (user, token_string) 或 (None, None)
    """
    try:
        # v2架构路径
        user_dict, token = authenticate(username, password)
        if user_dict:
            user = User.query.get(user_dict['id'])
            return user, token
        return None, None
    except (NameError, ImportError):
        # v1架构路径（兜底）
        return _authenticate_user_old(username, password)


def _authenticate_user_old(username: str, password: str):
    """旧的认证实现（兜底）"""
    from werkzeug.security import check_password_hash
    from flask_jwt_extended import create_access_token
    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, None

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
# 当前用户获取（v2桥接）
# ---------------------------------------------------------------------------

def get_current_user():
    """在受保护的路由中获取当前登录用户对象（v2桥接）"""
    try:
        user_id = get_current_user_id()
        return User.query.get(user_id)
    except (NameError, ImportError):
        from flask_jwt_extended import get_jwt_identity
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        return User.query.get(user_id)


# ---------------------------------------------------------------------------
# RBAC 装饰器（v2桥接）
# ---------------------------------------------------------------------------

def require_permission(permission_code: str):
    """
    路由装饰器：要求当前用户拥有指定权限代码（v2桥接）
    """
    try:
        return new_require_permission(permission_code)
    except NameError:
        return _require_permission_old(permission_code)


def _require_permission_old(permission_code: str):
    """旧的权限装饰器（兜底）"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = _get_jwt()
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
    """辅助函数：获取当前 JWT 的完整 claims（v2桥接）"""
    return _get_jwt()
