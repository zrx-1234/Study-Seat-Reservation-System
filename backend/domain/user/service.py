"""
MOD-USER: 用户与权限模块 - 服务接口
"""

from typing import Optional, Tuple, List
from datetime import datetime

from domain.user.models import User, Role, Permission
from infrastructure.auth import hash_password, verify_password, create_token
from infrastructure.exceptions import ValidationError, ConflictError
from extensions import db

# ============================================================================
# 认证相关
# ============================================================================

def authenticate(username: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    验证用户名密码，返回 (用户信息字典, token) 或 (None, None)
    """
    user = User.query.filter_by(username=username, is_active=True).first()
    if not user:
        return None, None
    if not verify_password(user.password_hash, password):
        return None, None

    # 获取权限
    permissions = []
    if user.user_type == 'admin':
        perm_codes = set()
        for role in user.roles:
            for p in role.permissions:
                perm_codes.add(p.code)
        permissions = list(perm_codes)

    token = create_token(str(user.id), {'user_type': user.user_type, 'permissions': permissions})

    user_dict = {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'user_type': user.user_type,
        'department': user.department,
        'email': user.email
    }
    return user_dict, token


def register_student(username: str, password: str, name: str,
                     department: str = None, email: str = None) -> Tuple[dict, str]:
    """注册学生账号，返回 (用户信息字典, token)。"""
    username = (username or '').strip()
    password = (password or '').strip()
    name = (name or '').strip()
    department = (department or '').strip() or None
    email = (email or '').strip() or None

    if not username or not password or not name:
        raise ValidationError('学号、密码、姓名不能为空')
    if len(password) < 6:
        raise ValidationError('密码长度不能少于 6 位')

    exists = User.query.filter_by(username=username).first()
    if exists:
        raise ConflictError('该学号已注册')

    user = User(
        username=username,
        password_hash=hash_password(password),
        name=name,
        user_type='student',
        department=department,
        email=email,
        is_active=True,
    )
    db.session.add(user)
    db.session.commit()

    user_dict = {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'user_type': user.user_type,
        'department': user.department,
        'email': user.email,
    }
    token = create_token(str(user.id), {'user_type': 'student', 'permissions': []})
    return user_dict, token


def get_current_user(user_id: int) -> Optional[dict]:
    """
    根据用户ID获取当前用户基本信息
    """
    user = db.session.get(User, user_id)
    if not user:
        return None
    return {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'user_type': user.user_type,
        'department': user.department
    }


def get_user_profile(user_id: int) -> dict:
    """
    获取用户完整Profile，含活跃预约数、违约次数统计
    被学生端 /student/profile 调用
    """
    user = db.session.get(User, user_id)
    if not user:
        return None

    # TODO: 实现统计
    return {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'department': user.department,
        'email': user.email,
        'active_reservations': 0,
        'total_violations': 0
    }


def get_user_active_reservation_count(user_id: int) -> int:
    """
    获取用户当前进行中的预约数量
    被预约模块在创建预约前调用
    """
    # TODO: 实现
    return 0


def get_user_total_violations(user_id: int) -> int:
    """
    获取用户累计违约次数
    """
    # TODO: 实现
    return 0


# ============================================================================
# 用户管理（待实现）
# ============================================================================

def create_user(data: dict):
    """创建用户"""
    # TODO: 实现
    pass


def update_user(user_id: int, data: dict):
    """更新用户"""
    # TODO: 实现
    pass


def delete_user(user_id: int):
    """删除用户"""
    # TODO: 实现
    pass


def get_user(user_id: int):
    """获取单个用户"""
    # TODO: 实现
    pass


def list_users(user_type: str = None, role_id: int = None, keyword: str = None, page: int = 1, per_page: int = 20):
    """分页查询用户列表"""
    # TODO: 实现
    pass


# ============================================================================
# 角色与权限管理（待实现）
# ============================================================================

def create_role(data: dict):
    """创建角色"""
    # TODO: 实现
    pass


def update_role(role_id: int, data: dict):
    """更新角色"""
    # TODO: 实现
    pass


def delete_role(role_id: int):
    """删除角色"""
    # TODO: 实现
    pass


def get_role(role_id: int):
    """获取角色详情"""
    # TODO: 实现
    pass


def list_roles(page: int = 1, per_page: int = 20):
    """分页查询角色列表"""
    # TODO: 实现
    pass


def list_permissions():
    """返回全部权限列表（全量）"""
    perms = Permission.query.all()
    return [{'id': p.id, 'name': p.name, 'code': p.code, 'description': p.description} for p in perms]


def assign_roles_to_user(user_id: int, role_ids: List[int]):
    """为用户分配角色"""
    # TODO: 实现
    pass


def check_permission(user_id: int, permission_code: str) -> bool:
    """检查指定用户是否拥有指定权限代码"""
    user = db.session.get(User, user_id)
    if not user or user.user_type != 'admin':
        return False

    for role in user.roles:
        for perm in role.permissions:
            if perm.code == permission_code:
                return True
    return False


def get_user_permissions(user_id: int) -> List[str]:
    """获取用户的全部权限代码列表"""
    user = db.session.get(User, user_id)
    if not user or user.user_type != 'admin':
        return []

    perm_codes = set()
    for role in user.roles:
        for perm in role.permissions:
            perm_codes.add(perm.code)
    return list(perm_codes)
