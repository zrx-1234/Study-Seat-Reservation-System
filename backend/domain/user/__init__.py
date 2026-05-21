"""
MOD-USER: 用户与权限模块

对外暴露的 Service API：
    authenticate(username, password) -> Tuple[Optional[dict], Optional[str]]
    get_current_user(user_id) -> Optional[UserDTO]
    get_user_profile(user_id) -> Optional[UserProfileDTO]
    get_user_active_reservation_count(user_id) -> int
    get_user_total_violations(user_id) -> int
    create_user(data) -> UserDTO
    update_user(user_id, data) -> UserDTO
    delete_user(user_id) -> None
    get_user(user_id) -> Optional[UserDTO]
    list_users(...) -> PaginatedResult
    create_role(data) -> RoleDTO
    update_role(role_id, data) -> RoleDTO
    delete_role(role_id) -> None
    get_role(role_id) -> Optional[RoleDetailDTO]
    list_roles(...) -> PaginatedResult
    list_permissions() -> List[PermissionDTO]
    assign_roles_to_user(user_id, role_ids) -> None
    check_permission(user_id, permission_code) -> bool
    get_user_permissions(user_id) -> List[str]
"""

from domain.user.service import (
    authenticate,
    get_current_user,
    get_user_profile,
    get_user_active_reservation_count,
    get_user_total_violations,
    create_user,
    update_user,
    delete_user,
    get_user,
    list_users,
    create_role,
    update_role,
    delete_role,
    get_role,
    list_roles,
    list_permissions,
    assign_roles_to_user,
    check_permission,
    get_user_permissions,
)

__all__ = [
    'authenticate',
    'get_current_user',
    'get_user_profile',
    'get_user_active_reservation_count',
    'get_user_total_violations',
    'create_user',
    'update_user',
    'delete_user',
    'get_user',
    'list_users',
    'create_role',
    'update_role',
    'delete_role',
    'get_role',
    'list_roles',
    'list_permissions',
    'assign_roles_to_user',
    'check_permission',
    'get_user_permissions',
]
