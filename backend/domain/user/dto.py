"""
MOD-USER: 用户与权限模块 - DTO定义
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class UserDTO:
    id: int
    username: str
    name: str
    user_type: str
    department: Optional[str] = None
    email: Optional[str] = None


@dataclass
class UserProfileDTO:
    id: int
    username: str
    name: str
    department: Optional[str]
    email: Optional[str]
    active_reservations: int
    total_violations: int


@dataclass
class RoleDTO:
    id: int
    name: str
    description: Optional[str] = None


@dataclass
class RoleDetailDTO:
    id: int
    name: str
    description: Optional[str]
    permissions: List['PermissionDTO']


@dataclass
class PermissionDTO:
    id: int
    name: str
    code: str
    description: Optional[str]


@dataclass
class UserCreateDTO:
    username: str
    password: str
    name: str
    user_type: str
    department: Optional[str] = None
    email: Optional[str] = None


@dataclass
class UserUpdateDTO:
    name: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None


@dataclass
class RoleCreateDTO:
    name: str
    description: Optional[str]
    permission_ids: List[int]


@dataclass
class RoleUpdateDTO:
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


@dataclass
class PaginatedResult:
    items: List
    total: int
    page: int
    per_page: int
    pages: int
