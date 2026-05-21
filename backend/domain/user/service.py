"""
MOD-USER: 用户与权限模块 - 服务接口

用户生命周期管理、角色与权限管理、登录认证、RBAC 权限校验。
"""

from typing import Optional, Tuple, List
from datetime import datetime

from sqlalchemy import or_

from domain.user.models import User, Role, Permission
from domain.user.dto import (
    UserDTO, UserProfileDTO, RoleDTO, RoleDetailDTO,
    PermissionDTO, UserCreateDTO, UserUpdateDTO,
    RoleCreateDTO, RoleUpdateDTO, PaginatedResult
)
from infrastructure.auth import hash_password, verify_password, create_token
from infrastructure.exceptions import ValidationError, NotFoundError, ConflictError
from extensions import db


# ============================================================================
# 认证相关
# ============================================================================

def authenticate(username: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    """
    验证用户名密码，返回 (用户信息字典, JWT Token)。
    失败时返回 (None, None)。
    """
    user = User.query.filter_by(username=username, is_active=True).first()
    if not user:
        return None, None
    if not verify_password(user.password_hash, password):
        return None, None

    permissions = []
    if user.user_type == 'admin':
        perm_codes = set()
        for role in user.roles:
            for p in role.permissions:
                perm_codes.add(p.code)
        permissions = sorted(list(perm_codes))

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


def get_current_user(user_id: int) -> Optional[UserDTO]:
    """根据用户ID获取当前用户基本信息。"""
    user = User.query.get(user_id)
    if not user:
        return None
    return _user_to_dto(user)


# ============================================================================
# 用户统计（供其他模块调用）
# ============================================================================

def get_user_profile(user_id: int) -> Optional[UserProfileDTO]:
    """
    获取用户完整 Profile，含活跃预约数、违约次数统计。
    被学生端 /student/profile 调用。
    """
    user = User.query.get(user_id)
    if not user:
        return None

    active_reservations = get_user_active_reservation_count(user_id)
    total_violations = get_user_total_violations(user_id)

    return UserProfileDTO(
        id=user.id,
        username=user.username,
        name=user.name,
        department=user.department,
        email=user.email,
        active_reservations=active_reservations,
        total_violations=total_violations
    )


def get_user_active_reservation_count(user_id: int) -> int:
    """
    获取用户当前进行中的预约数量。
    被预约模块在创建预约前调用，用于校验 max_active_reservations 限制。
    """
    user = User.query.get(user_id)
    if not user:
        return 0
    return user.reservations.filter(
        User.reservations.property.mapper.class_.status.in_(['reserved', 'checked_in'])
    ).count()


def get_user_total_violations(user_id: int) -> int:
    """获取用户累计违约次数。"""
    user = User.query.get(user_id)
    if not user:
        return 0
    return user.violations.count()


# ============================================================================
# 用户管理
# ============================================================================

def create_user(data: UserCreateDTO) -> UserDTO:
    """
    创建用户（学生或管理员）。
    约束：username 全局唯一。
    """
    existing = User.query.filter_by(username=data.username).first()
    if existing:
        raise ConflictError(f'用户名 {data.username} 已存在')

    if data.user_type not in ('student', 'admin'):
        raise ValidationError(f'无效的用户类型: {data.user_type}')

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        name=data.name,
        user_type=data.user_type,
        department=data.department,
        email=data.email,
        is_active=True
    )
    db.session.add(user)
    db.session.commit()
    return _user_to_dto(user)


def update_user(user_id: int, data: UserUpdateDTO) -> UserDTO:
    """
    更新用户基本信息（姓名、院系、邮箱、状态等）。
    不涉及密码修改与角色修改。
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f'用户 {user_id} 不存在')

    if data.name is not None:
        user.name = data.name
    if data.department is not None:
        user.department = data.department
    if data.email is not None:
        user.email = data.email

    user.updated_at = datetime.utcnow()
    db.session.commit()
    return _user_to_dto(user)


def delete_user(user_id: int) -> None:
    """
    注销用户（软删除，is_active 设为 False）。
    约束：不可删除超级管理员。
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f'用户 {user_id} 不存在')

    # 检查是否为超级管理员（通过角色名判断）
    role_names = {r.name for r in user.roles}
    if 'super_admin' in role_names:
        raise ConflictError('不可删除超级管理员')

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.session.commit()


def get_user(user_id: int) -> Optional[UserDTO]:
    """获取单个用户详情。"""
    user = User.query.get(user_id)
    if not user:
        return None
    return _user_to_dto(user)


def list_users(
    user_type: str = None,
    role_id: int = None,
    keyword: str = None,
    page: int = 1,
    per_page: int = 20
) -> PaginatedResult:
    """
    分页查询用户列表。
    keyword 支持按 username 或 name 模糊匹配。
    """
    query = User.query

    if user_type is not None:
        query = query.filter_by(user_type=user_type)

    if role_id is not None:
        query = query.join(User.roles).filter(Role.id == role_id)

    if keyword:
        pattern = f'%{keyword}%'
        query = query.filter(
            or_(User.username.like(pattern), User.name.like(pattern))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return PaginatedResult(
        items=[_user_to_dto(u) for u in pagination.items],
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pagination.pages
    )


# ============================================================================
# 角色与权限管理
# ============================================================================

def create_role(data: RoleCreateDTO) -> RoleDTO:
    """创建角色，绑定初始权限列表。"""
    existing = Role.query.filter_by(name=data.name).first()
    if existing:
        raise ConflictError(f'角色名 {data.name} 已存在')

    role = Role(name=data.name, description=data.description)
    db.session.add(role)

    if data.permission_ids:
        perms = Permission.query.filter(Permission.id.in_(data.permission_ids)).all()
        role.permissions = perms

    db.session.commit()
    return _role_to_dto(role)


def update_role(role_id: int, data: RoleUpdateDTO) -> RoleDTO:
    """更新角色信息及权限列表。"""
    role = Role.query.get(role_id)
    if not role:
        raise NotFoundError(f'角色 {role_id} 不存在')

    if data.name is not None:
        # 检查名称冲突
        existing = Role.query.filter_by(name=data.name).filter(Role.id != role_id).first()
        if existing:
            raise ConflictError(f'角色名 {data.name} 已存在')
        role.name = data.name

    if data.description is not None:
        role.description = data.description

    if data.permission_ids is not None:
        perms = Permission.query.filter(Permission.id.in_(data.permission_ids)).all()
        role.permissions = perms

    db.session.commit()
    return _role_to_dto(role)


def delete_role(role_id: int) -> None:
    """
    删除角色。
    约束：若该角色下仍有用户，抛出 ConflictError。
    """
    role = Role.query.get(role_id)
    if not role:
        raise NotFoundError(f'角色 {role_id} 不存在')

    if role.users:
        raise ConflictError('该角色下仍有用户，无法删除')

    db.session.delete(role)
    db.session.commit()


def get_role(role_id: int) -> Optional[RoleDetailDTO]:
    """获取角色详情，含权限列表。"""
    role = Role.query.get(role_id)
    if not role:
        return None
    return _role_to_detail_dto(role)


def list_roles(page: int = 1, per_page: int = 20) -> PaginatedResult:
    """分页查询角色列表。"""
    pagination = Role.query.order_by(Role.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return PaginatedResult(
        items=[_role_to_dto(r) for r in pagination.items],
        total=pagination.total,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pagination.pages
    )


def list_permissions() -> List[PermissionDTO]:
    """返回全部权限列表（全量，不分页）。"""
    perms = Permission.query.order_by(Permission.id).all()
    return [_perm_to_dto(p) for p in perms]


def assign_roles_to_user(user_id: int, role_ids: List[int]) -> None:
    """为用户分配角色（覆盖式更新）。"""
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f'用户 {user_id} 不存在')

    if role_ids:
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        user.roles = roles
    else:
        user.roles = []

    db.session.commit()


# ============================================================================
# 权限校验
# ============================================================================

def check_permission(user_id: int, permission_code: str) -> bool:
    """
    检查指定用户是否拥有指定权限代码。
    学生类型用户始终返回 False（管理端专用）。
    """
    user = User.query.get(user_id)
    if not user or user.user_type != 'admin':
        return False

    for role in user.roles:
        for perm in role.permissions:
            if perm.code == permission_code:
                return True
    return False


def get_user_permissions(user_id: int) -> List[str]:
    """获取用户的全部权限代码列表（去重）。"""
    user = User.query.get(user_id)
    if not user or user.user_type != 'admin':
        return []

    perm_codes = set()
    for role in user.roles:
        for perm in role.permissions:
            perm_codes.add(perm.code)
    return sorted(list(perm_codes))


# ============================================================================
# 内部辅助函数
# ============================================================================

def _user_to_dto(user: User) -> UserDTO:
    return UserDTO(
        id=user.id,
        username=user.username,
        name=user.name,
        user_type=user.user_type,
        department=user.department,
        email=user.email,
        is_active=user.is_active
    )


def _role_to_dto(role: Role) -> RoleDTO:
    return RoleDTO(
        id=role.id,
        name=role.name,
        description=role.description
    )


def _role_to_detail_dto(role: Role) -> RoleDetailDTO:
    return RoleDetailDTO(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=[_perm_to_dto(p) for p in role.permissions]
    )


def _perm_to_dto(perm: Permission) -> PermissionDTO:
    return PermissionDTO(
        id=perm.id,
        name=perm.name,
        code=perm.code,
        description=perm.description
    )
