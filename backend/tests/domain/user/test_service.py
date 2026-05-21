"""
MOD-USER 测试：用户与权限模块服务层
覆盖认证、用户管理、角色权限管理、统计查询
"""

import pytest
from datetime import datetime, timedelta

from domain.user.models import User, Role, Permission
from domain.user.dto import (
    UserCreateDTO, UserUpdateDTO, RoleCreateDTO, RoleUpdateDTO
)
from domain.user import service as user_service
from domain.reservation.models import Reservation, ViolationRecord
from infrastructure.exceptions import ValidationError, NotFoundError, ConflictError
from infrastructure.auth import verify_password
from extensions import db


# ============================================================================
# 固件
# ============================================================================

@pytest.fixture
def admin_user(db_session):
    """创建一个普通管理员用户（无角色）"""
    user = User(
        username='admin01',
        password_hash='pbkdf2:sha256$dummy',
        name='管理员01',
        user_type='admin',
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def student_user(db_session):
    """创建一个学生用户"""
    user = User(
        username='2025001001',
        password_hash='pbkdf2:sha256$dummy',
        name='学生甲',
        user_type='student',
        department='计算机学院',
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def permission(db_session):
    """创建一个权限"""
    perm = Permission(name='用户管理', code='user:manage', description='管理用户')
    db_session.add(perm)
    db_session.commit()
    return perm


@pytest.fixture
def role(db_session, permission):
    """创建一个角色并绑定权限"""
    r = Role(name='test_admin', description='测试管理员')
    r.permissions = [permission]
    db_session.add(r)
    db_session.commit()
    return r


@pytest.fixture
def super_admin_role(db_session, permission):
    """创建超级管理员角色"""
    r = Role(name='super_admin', description='超级管理员')
    r.permissions = [permission]
    db_session.add(r)
    db_session.commit()
    return r


import time as pytime

@pytest.fixture
def seat_for_resv(db_session):
    """为预约测试创建座位（需要先有自习室）"""
    from domain.room.models import StudyRoom, Seat
    from datetime import time
    room = StudyRoom(
        name='测试自习室', location='测试楼', capacity=10,
        open_time=time(7, 0), close_time=time(22, 0)
    )
    db_session.add(room)
    db_session.flush()
    seat = Seat(room_id=room.id, seat_number='A01')
    db_session.add(seat)
    db_session.commit()
    return seat


# ============================================================================
# 1. authenticate 测试
# ============================================================================

class TestAuthenticate:
    """测试用户认证"""

    def test_authenticate_invalid_user(self, db_session):
        """无效用户应返回 None, None"""
        user, token = user_service.authenticate('invalid_user', 'wrong_password')
        assert user is None
        assert token is None

    def test_authenticate_wrong_password(self, db_session, admin_user):
        from werkzeug.security import generate_password_hash
        admin_user.password_hash = generate_password_hash('correct_password')
        db_session.commit()

        user, token = user_service.authenticate('admin01', 'wrong_password')
        assert user is None
        assert token is None

    def test_authenticate_success(self, db_session, admin_user):
        from werkzeug.security import generate_password_hash
        admin_user.password_hash = generate_password_hash('secret')
        db_session.commit()

        user, token = user_service.authenticate('admin01', 'secret')
        assert user is not None
        assert token is not None
        assert user['username'] == 'admin01'
        assert user['user_type'] == 'admin'

    def test_authenticate_inactive_user(self, db_session, admin_user):
        from werkzeug.security import generate_password_hash
        admin_user.password_hash = generate_password_hash('secret')
        admin_user.is_active = False
        db_session.commit()

        user, token = user_service.authenticate('admin01', 'secret')
        assert user is None
        assert token is None

    def test_authenticate_student(self, db_session, student_user):
        from werkzeug.security import generate_password_hash
        student_user.password_hash = generate_password_hash('student_pass')
        db_session.commit()

        user, token = user_service.authenticate('2025001001', 'student_pass')
        assert user is not None
        assert user['user_type'] == 'student'
        # 学生没有权限
        assert user_service.get_user_permissions(student_user.id) == []


# ============================================================================
# 2. 用户管理测试
# ============================================================================

class TestCreateUser:
    """测试创建用户"""

    def test_create_admin_user(self, db_session):
        dto = user_service.create_user(
            UserCreateDTO(username='new_admin', password='123456', name='新管理员', user_type='admin')
        )
        assert dto.username == 'new_admin'
        assert dto.user_type == 'admin'
        assert dto.is_active is True

        # 验证密码已哈希
        user = User.query.filter_by(username='new_admin').first()
        assert verify_password(user.password_hash, '123456')

    def test_create_student_user(self, db_session):
        dto = user_service.create_user(
            UserCreateDTO(
                username='2025001002', password='123456', name='新学生',
                user_type='student', department='数学学院'
            )
        )
        assert dto.user_type == 'student'
        assert dto.department == '数学学院'

    def test_duplicate_username_raises_conflict(self, db_session, admin_user):
        with pytest.raises(ConflictError):
            user_service.create_user(
                UserCreateDTO(username='admin01', password='123456', name='重复', user_type='admin')
            )

    def test_invalid_user_type_raises_validation(self, db_session):
        with pytest.raises(ValidationError):
            user_service.create_user(
                UserCreateDTO(username='bad', password='123456', name='坏', user_type='teacher')
            )


class TestUpdateUser:
    """测试更新用户"""

    def test_update_name_and_email(self, db_session, admin_user):
        dto = user_service.update_user(
            admin_user.id,
            UserUpdateDTO(name='改名后', email='new@fdu.edu.cn')
        )
        assert dto.name == '改名后'
        assert dto.email == 'new@fdu.edu.cn'

    def test_update_partial_fields(self, db_session, admin_user):
        # 只更新 name，department 和 email 应保持不变
        dto = user_service.update_user(
            admin_user.id,
            UserUpdateDTO(name='仅改名')
        )
        assert dto.name == '仅改名'
        assert dto.department is None  # 原值

    def test_update_nonexistent_user_raises_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            user_service.update_user(99999, UserUpdateDTO(name='不存在'))


class TestDeleteUser:
    """测试删除用户（软删除）"""

    def test_soft_delete_sets_inactive(self, db_session, admin_user):
        user_service.delete_user(admin_user.id)
        user = User.query.get(admin_user.id)
        assert user.is_active is False

    def test_delete_super_admin_raises_conflict(self, db_session, admin_user, super_admin_role):
        admin_user.roles = [super_admin_role]
        db_session.commit()

        with pytest.raises(ConflictError):
            user_service.delete_user(admin_user.id)

    def test_delete_nonexistent_user_raises_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            user_service.delete_user(99999)


class TestGetUser:
    """测试获取单个用户"""

    def test_get_existing_user(self, db_session, admin_user):
        dto = user_service.get_user(admin_user.id)
        assert dto is not None
        assert dto.username == 'admin01'

    def test_get_nonexistent_user(self, db_session):
        assert user_service.get_user(99999) is None


class TestListUsers:
    """测试用户列表查询"""

    def test_pagination(self, db_session):
        for i in range(5):
            db_session.add(User(
                username=f'admin_{i}', password_hash='hash', name=f'管理员{i}', user_type='admin'
            ))
        db_session.commit()

        result = user_service.list_users(user_type='admin', page=1, per_page=3)
        assert len(result.items) == 3
        assert result.total >= 5
        assert result.page == 1
        assert result.per_page == 3

    def test_keyword_search(self, db_session, admin_user):
        db_session.add(User(username='other', password_hash='hash', name='其他', user_type='admin'))
        db_session.commit()

        result = user_service.list_users(keyword='admin01')
        usernames = [u.username for u in result.items]
        assert 'admin01' in usernames

    def test_filter_by_user_type(self, db_session, admin_user, student_user):
        result = user_service.list_users(user_type='student')
        usernames = [u.username for u in result.items]
        assert '2025001001' in usernames
        assert 'admin01' not in usernames

    def test_filter_by_role_id(self, db_session, admin_user, role):
        admin_user.roles = [role]
        db_session.commit()

        result = user_service.list_users(role_id=role.id)
        assert len(result.items) == 1
        assert result.items[0].username == 'admin01'


# ============================================================================
# 3. 角色与权限管理测试
# ============================================================================

class TestCreateRole:
    """测试创建角色"""

    def test_create_role_with_permissions(self, db_session, permission):
        dto = user_service.create_role(
            RoleCreateDTO(name='editor', description='编辑', permission_ids=[permission.id])
        )
        assert dto.name == 'editor'
        assert dto.description == '编辑'

        role = Role.query.filter_by(name='editor').first()
        assert len(role.permissions) == 1

    def test_duplicate_name_raises_conflict(self, db_session, role):
        with pytest.raises(ConflictError):
            user_service.create_role(
                RoleCreateDTO(name='test_admin', description='重复', permission_ids=[])
            )


class TestUpdateRole:
    """测试更新角色"""

    def test_update_name_and_permissions(self, db_session, role, permission):
        # 再创建一个权限用于替换
        perm2 = Permission(name='新权限', code='new:perm')
        db_session.add(perm2)
        db_session.commit()

        dto = user_service.update_role(
            role.id,
            RoleUpdateDTO(name='updated_name', description='已更新', permission_ids=[perm2.id])
        )
        assert dto.name == 'updated_name'

        updated = Role.query.get(role.id)
        assert updated.name == 'updated_name'
        assert len(updated.permissions) == 1
        assert updated.permissions[0].code == 'new:perm'

    def test_update_to_duplicate_name_raises_conflict(self, db_session, role):
        other = Role(name='other_role', description='其他')
        db_session.add(other)
        db_session.commit()

        with pytest.raises(ConflictError):
            user_service.update_role(other.id, RoleUpdateDTO(name='test_admin'))

    def test_update_nonexistent_role_raises_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            user_service.update_role(99999, RoleUpdateDTO(name='不存在'))


class TestDeleteRole:
    """测试删除角色"""

    def test_delete_role_success(self, db_session, role):
        user_service.delete_role(role.id)
        assert Role.query.get(role.id) is None

    def test_delete_role_with_users_raises_conflict(self, db_session, role, admin_user):
        admin_user.roles = [role]
        db_session.commit()

        with pytest.raises(ConflictError):
            user_service.delete_role(role.id)

    def test_delete_nonexistent_role_raises_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            user_service.delete_role(99999)


class TestGetRole:
    """测试获取角色详情"""

    def test_get_existing_role(self, db_session, role, permission):
        dto = user_service.get_role(role.id)
        assert dto is not None
        assert dto.name == 'test_admin'
        assert len(dto.permissions) == 1
        assert dto.permissions[0].code == 'user:manage'

    def test_get_nonexistent_role(self, db_session):
        assert user_service.get_role(99999) is None


class TestListRoles:
    """测试角色列表"""

    def test_pagination(self, db_session):
        for i in range(5):
            db_session.add(Role(name=f'role_{i}', description='测试'))
        db_session.commit()

        result = user_service.list_roles(page=1, per_page=3)
        assert len(result.items) == 3
        assert result.total >= 5


class TestListPermissions:
    """测试权限列表"""

    def test_returns_all_permissions(self, db_session):
        db_session.add(Permission(name='P1', code='p1'))
        db_session.add(Permission(name='P2', code='p2'))
        db_session.commit()

        perms = user_service.list_permissions()
        assert len(perms) >= 2
        codes = [p.code for p in perms]
        assert 'p1' in codes
        assert 'p2' in codes


# ============================================================================
# 4. 角色分配测试
# ============================================================================

class TestAssignRolesToUser:
    """测试为用户分配角色"""

    def test_assign_single_role(self, db_session, admin_user, role):
        user_service.assign_roles_to_user(admin_user.id, [role.id])
        user = User.query.get(admin_user.id)
        assert len(user.roles) == 1
        assert user.roles[0].name == 'test_admin'

    def test_assign_multiple_roles(self, db_session, admin_user, role):
        role2 = Role(name='another', description='另一个')
        db_session.add(role2)
        db_session.commit()

        user_service.assign_roles_to_user(admin_user.id, [role.id, role2.id])
        user = User.query.get(admin_user.id)
        assert len(user.roles) == 2

    def test_assign_empty_list_clears_roles(self, db_session, admin_user, role):
        admin_user.roles = [role]
        db_session.commit()

        user_service.assign_roles_to_user(admin_user.id, [])
        user = User.query.get(admin_user.id)
        assert len(user.roles) == 0

    def test_assign_to_nonexistent_user_raises_not_found(self, db_session, role):
        with pytest.raises(NotFoundError):
            user_service.assign_roles_to_user(99999, [role.id])


# ============================================================================
# 5. 权限校验测试
# ============================================================================

class TestCheckPermission:
    """测试权限检查"""

    def test_admin_with_permission(self, db_session, admin_user, role):
        admin_user.roles = [role]
        db_session.commit()

        assert user_service.check_permission(admin_user.id, 'user:manage') is True

    def test_admin_without_permission(self, db_session, admin_user, role):
        admin_user.roles = [role]
        db_session.commit()

        assert user_service.check_permission(admin_user.id, 'room:manage') is False

    def test_student_always_false(self, db_session, student_user):
        assert user_service.check_permission(student_user.id, 'user:manage') is False

    def test_nonexistent_user(self, db_session):
        assert user_service.check_permission(99999, 'user:manage') is False


class TestGetUserPermissions:
    """测试获取用户权限列表"""

    def test_returns_unique_sorted_codes(self, db_session, admin_user, permission):
        perm2 = Permission(name='P2', code='room:manage')
        db_session.add(perm2)
        role2 = Role(name='multi_role', description='多权限')
        role2.permissions = [permission, perm2]
        db_session.add(role2)
        db_session.commit()

        admin_user.roles = [role2]
        db_session.commit()

        perms = user_service.get_user_permissions(admin_user.id)
        assert 'room:manage' in perms
        assert 'user:manage' in perms

    def test_student_returns_empty(self, db_session, student_user):
        assert user_service.get_user_permissions(student_user.id) == []


# ============================================================================
# 6. 用户统计测试
# ============================================================================

class TestGetUserProfile:
    """测试用户 Profile"""

    def test_returns_profile_with_stats(self, db_session, student_user, seat_for_resv):
        # 创建预约
        resv = Reservation(
            user_id=student_user.id,
            seat_id=seat_for_resv.id,
            start_time=datetime.utcnow() + timedelta(hours=1),
            end_time=datetime.utcnow() + timedelta(hours=3),
            status='reserved'
        )
        db_session.add(resv)
        db_session.flush()  # 获取 resv.id

        # 创建违约记录
        vio = ViolationRecord(
            user_id=student_user.id,
            reservation_id=resv.id,
            violation_time=datetime.utcnow()
        )
        db_session.add(vio)
        db_session.commit()

        profile = user_service.get_user_profile(student_user.id)
        assert profile is not None
        assert profile.username == '2025001001'
        assert profile.active_reservations == 1
        assert profile.total_violations == 1

    def test_nonexistent_user(self, db_session):
        assert user_service.get_user_profile(99999) is None


class TestGetUserActiveReservationCount:
    """测试活跃预约数统计"""

    def test_counts_reserved_and_checked_in(self, db_session, student_user, seat_for_resv):
        # reserved
        r1 = Reservation(user_id=student_user.id, seat_id=seat_for_resv.id,
                         start_time=datetime.utcnow() + timedelta(hours=1),
                         end_time=datetime.utcnow() + timedelta(hours=3), status='reserved')
        # checked_in
        r2 = Reservation(user_id=student_user.id, seat_id=seat_for_resv.id,
                         start_time=datetime.utcnow() - timedelta(hours=1),
                         end_time=datetime.utcnow() + timedelta(hours=2), status='checked_in')
        # completed 不应计入
        r3 = Reservation(user_id=student_user.id, seat_id=seat_for_resv.id,
                         start_time=datetime.utcnow() - timedelta(hours=3),
                         end_time=datetime.utcnow() - timedelta(hours=1), status='completed')
        db_session.add_all([r1, r2, r3])
        db_session.commit()

        assert user_service.get_user_active_reservation_count(student_user.id) == 2

    def test_nonexistent_user(self, db_session):
        assert user_service.get_user_active_reservation_count(99999) == 0


class TestGetUserTotalViolations:
    """测试违约次数统计"""

    def test_counts_violations(self, db_session, student_user, seat_for_resv):
        resv = Reservation(user_id=student_user.id, seat_id=seat_for_resv.id,
                           start_time=datetime.utcnow(), end_time=datetime.utcnow() + timedelta(hours=2),
                           status='violation')
        db_session.add(resv)
        db_session.commit()

        vio = ViolationRecord(user_id=student_user.id, reservation_id=resv.id,
                              violation_time=datetime.utcnow())
        db_session.add(vio)
        db_session.commit()

        assert user_service.get_user_total_violations(student_user.id) == 1

    def test_nonexistent_user(self, db_session):
        assert user_service.get_user_total_violations(99999) == 0


# ============================================================================
# 7. get_current_user 测试
# ============================================================================

class TestGetCurrentUser:
    """测试获取当前用户"""

    def test_returns_user_dto(self, db_session, admin_user):
        dto = user_service.get_current_user(admin_user.id)
        assert dto is not None
        assert dto.id == admin_user.id
        assert dto.username == 'admin01'

    def test_nonexistent_user(self, db_session):
        assert user_service.get_current_user(99999) is None
