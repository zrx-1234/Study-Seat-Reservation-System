"""
API-ADM 测试：管理端接口模块
覆盖系统配置接口、认证接口及通用响应格式
"""

import pytest
from flask import Flask

from extensions import db, jwt, init_extensions
from infrastructure.exceptions import register_error_handlers
from infrastructure.auth import register_jwt_callbacks
from domain.system.models import SystemConfig
from domain.user.models import User, Role, Permission
from werkzeug.security import generate_password_hash


# ============================================================================
# 固件
# ============================================================================

@pytest.fixture
def admin_app():
    """创建仅包含 v2 API 蓝图的测试应用，内存数据库"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'

    init_extensions(app)
    register_error_handlers(app)
    register_jwt_callbacks(jwt)

    # 仅注册 v2 API 蓝图（避免与旧版蓝图名称冲突）
    from api.admin import admin_bp
    from api.student import student_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def admin_client(admin_app):
    """管理端测试客户端"""
    return admin_app.test_client()


@pytest.fixture
def admin_token(admin_app, admin_client):
    """创建超级管理员并返回 JWT Token"""
    with admin_app.app_context():
        # 创建权限
        perms = [
            Permission(name='系统配置', code='system:config', description='调整系统全局参数'),
            Permission(name='用户管理', code='user:manage', description='管理用户'),
            Permission(name='角色管理', code='role:manage', description='管理角色'),
        ]
        for p in perms:
            db.session.add(p)
        db.session.commit()

        # 创建角色（拥有全部权限）
        role = Role(name='super_admin', description='超级管理员')
        role.permissions = perms
        db.session.add(role)
        db.session.commit()

        # 创建管理员用户
        user = User(
            username='admin',
            password_hash=generate_password_hash('123456'),
            name='系统管理员',
            user_type='admin',
            email='admin@fdu.edu.cn',
            is_active=True
        )
        user.roles = [role]
        db.session.add(user)
        db.session.commit()

        # 登录获取 Token
        resp = admin_client.post('/api/v1/admin/auth/login', json={
            'username': 'admin',
            'password': '123456'
        })
        data = resp.get_json()
        assert data['code'] == 200
        return data['data']['access_token']


# ============================================================================
# 1. 系统配置接口测试
# ============================================================================

class TestListConfigs:
    """GET /api/v1/admin/configs"""

    def test_list_configs_success(self, admin_client, admin_token):
        # 预置配置
        cfg = SystemConfig(config_key='max_reservation_hours', config_value='4', description='测试')
        db.session.add(cfg)
        db.session.commit()

        resp = admin_client.get(
            '/api/v1/admin/configs',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert 'items' in data['data']
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['key'] == 'max_reservation_hours'

    def test_list_configs_empty(self, admin_client, admin_token):
        resp = admin_client.get(
            '/api/v1/admin/configs',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['items'] == []

    def test_list_configs_without_auth(self, admin_client):
        resp = admin_client.get('/api/v1/admin/configs')
        assert resp.status_code == 401

    def test_list_configs_with_insufficient_permission(self, admin_app, admin_client):
        # 创建一个没有 system:config 权限的管理员
        with admin_app.app_context():
            role = Role(name='viewer', description='只读')
            db.session.add(role)
            user = User(
                username='viewer01',
                password_hash=generate_password_hash('123456'),
                name=' Viewer',
                user_type='admin',
                is_active=True
            )
            user.roles = [role]
            db.session.add(user)
            db.session.commit()

            resp = admin_client.post('/api/v1/admin/auth/login', json={
                'username': 'viewer01',
                'password': '123456'
            })
            token = resp.get_json()['data']['access_token']

        resp = admin_client.get(
            '/api/v1/admin/configs',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert resp.status_code == 403


class TestUpdateConfig:
    """PUT /api/v1/admin/configs/<key>"""

    def test_update_config_success(self, admin_client, admin_token):
        resp = admin_client.put(
            '/api/v1/admin/configs/max_reservation_hours',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'value': '6', 'description': '期末考试周调整'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200

        # 数据库验证
        cfg = SystemConfig.query.filter_by(config_key='max_reservation_hours').first()
        assert cfg.config_value == '6'
        assert cfg.description == '期末考试周调整'

    def test_update_config_missing_value(self, admin_client, admin_token):
        resp = admin_client.put(
            '/api/v1/admin/configs/max_reservation_hours',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'description': '缺少value'}
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['code'] == 400
        assert 'value' in data['message']

    def test_update_config_invalid_key(self, admin_client, admin_token):
        resp = admin_client.put(
            '/api/v1/admin/configs/invalid_key',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'value': '123'}
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['code'] == 400

    def test_update_config_without_auth(self, admin_client):
        resp = admin_client.put(
            '/api/v1/admin/configs/max_reservation_hours',
            json={'value': '6'}
        )
        assert resp.status_code == 401


# ============================================================================
# 2. 认证接口测试（管理端登录）
# ============================================================================

class TestAdminAuth:
    """POST /api/v1/admin/auth/login"""

    def test_login_success(self, admin_app, admin_client):
        with admin_app.app_context():
            perm = Permission(name='系统配置', code='system:config')
            db.session.add(perm)
            role = Role(name='super_admin', description='超级管理员')
            role.permissions = [perm]
            db.session.add(role)
            user = User(
                username='admin2',
                password_hash=generate_password_hash('123456'),
                name='管理员',
                user_type='admin',
                is_active=True
            )
            user.roles = [role]
            db.session.add(user)
            db.session.commit()

        resp = admin_client.post('/api/v1/admin/auth/login', json={
            'username': 'admin2',
            'password': '123456'
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert 'access_token' in data['data']
        assert data['data']['user']['user_type'] == 'admin'

    def test_login_wrong_password(self, admin_app, admin_client):
        with admin_app.app_context():
            user = User(
                username='admin3',
                password_hash=generate_password_hash('123456'),
                name='管理员',
                user_type='admin',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()

        resp = admin_client.post('/api/v1/admin/auth/login', json={
            'username': 'admin3',
            'password': 'wrong_password'
        })
        assert resp.status_code == 401

    def test_login_student_rejected(self, admin_app, admin_client):
        with admin_app.app_context():
            user = User(
                username='2025123456',
                password_hash=generate_password_hash('123456'),
                name='张三',
                user_type='student',
                is_active=True
            )
            db.session.add(user)
            db.session.commit()

        resp = admin_client.post('/api/v1/admin/auth/login', json={
            'username': '2025123456',
            'password': '123456'
        })
        assert resp.status_code == 401
        data = resp.get_json()
        assert '用户名或密码错误' in data['message']

    def test_login_missing_fields(self, admin_client):
        resp = admin_client.post('/api/v1/admin/auth/login', json={})
        assert resp.status_code == 400


# ============================================================================
# 3. 角色与权限接口测试
# ============================================================================

class TestRoles:
    """角色 CRUD"""

    def test_create_role_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            perm = Permission(name='测试权限', code='test:perm')
            db.session.add(perm)
            db.session.commit()
            perm_id = perm.id

        resp = admin_client.post(
            '/api/v1/admin/roles',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'name': 'test_role', 'description': '测试角色', 'permission_ids': [perm_id]}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['name'] == 'test_role'

    def test_create_role_duplicate_name(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            db.session.add(Role(name='dup_role', description='重复'))
            db.session.commit()

        resp = admin_client.post(
            '/api/v1/admin/roles',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'name': 'dup_role', 'description': '重复', 'permission_ids': []}
        )
        assert resp.status_code == 409

    def test_get_role_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            perm = Permission(name='P', code='p:1')
            db.session.add(perm)
            role = Role(name='get_role', description='查看测试')
            role.permissions = [perm]
            db.session.add(role)
            db.session.commit()
            role_id = role.id

        resp = admin_client.get(
            f'/api/v1/admin/roles/{role_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['name'] == 'get_role'
        assert len(data['data']['permissions']) == 1

    def test_get_role_not_found(self, admin_client, admin_token):
        resp = admin_client.get(
            '/api/v1/admin/roles/99999',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 404

    def test_update_role_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            role = Role(name='old_name', description='旧描述')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

        resp = admin_client.put(
            f'/api/v1/admin/roles/{role_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'name': 'new_name', 'description': '新描述'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['name'] == 'new_name'

    def test_delete_role_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            role = Role(name='to_delete', description='待删除')
            db.session.add(role)
            db.session.commit()
            role_id = role.id

        resp = admin_client.delete(
            f'/api/v1/admin/roles/{role_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200

    def test_delete_role_with_users_conflict(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            role = Role(name='has_user', description='有用户')
            db.session.add(role)
            user = User(
                username='role_user', password_hash='hash', name='角色用户', user_type='admin'
            )
            user.roles = [role]
            db.session.add(user)
            db.session.commit()
            role_id = role.id

        resp = admin_client.delete(
            f'/api/v1/admin/roles/{role_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 409

    def test_list_roles(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            db.session.add(Role(name='r1', description='R1'))
            db.session.add(Role(name='r2', description='R2'))
            db.session.commit()

        resp = admin_client.get(
            '/api/v1/admin/roles',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert len(data['data']['items']) >= 2


class TestPermissions:
    """权限列表"""

    def test_list_permissions(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            db.session.add(Permission(name='P1', code='p1'))
            db.session.commit()

        resp = admin_client.get(
            '/api/v1/admin/permissions',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert len(data['data']['items']) >= 1


# ============================================================================
# 4. 用户管理接口测试
# ============================================================================

class TestUsers:
    """用户 CRUD"""

    def test_create_user_success(self, admin_client, admin_token):
        resp = admin_client.post(
            '/api/v1/admin/users',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={
                'username': 'new_admin',
                'password': '123456',
                'name': '新管理员',
                'department': '数学学院',
                'email': 'new@fdu.edu.cn',
                'role_ids': []
            }
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['code'] == 200
        assert data['data']['username'] == 'new_admin'
        assert data['data']['user_type'] == 'admin'

    def test_create_user_missing_fields(self, admin_client, admin_token):
        resp = admin_client.post(
            '/api/v1/admin/users',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'username': 'incomplete'}
        )
        assert resp.status_code == 400

    def test_get_user_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            user = User(
                username='get_me', password_hash='hash', name='获取我', user_type='admin'
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        resp = admin_client.get(
            f'/api/v1/admin/users/{user_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['username'] == 'get_me'

    def test_get_user_not_found(self, admin_client, admin_token):
        resp = admin_client.get(
            '/api/v1/admin/users/99999',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 404

    def test_update_user_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            user = User(
                username='upd_me', password_hash='hash', name='原名字', user_type='admin'
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        resp = admin_client.put(
            f'/api/v1/admin/users/{user_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'name': '新名字', 'email': 'updated@fdu.edu.cn'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['name'] == '新名字'
        assert data['data']['email'] == 'updated@fdu.edu.cn'

    def test_update_user_with_roles(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            user = User(
                username='role_user2', password_hash='hash', name='角色测试', user_type='admin'
            )
            role = Role(name='assign_role', description='分配测试')
            db.session.add_all([user, role])
            db.session.commit()
            user_id = user.id
            role_id = role.id

        resp = admin_client.put(
            f'/api/v1/admin/users/{user_id}',
            headers={'Authorization': f'Bearer {admin_token}'},
            json={'role_ids': [role_id]}
        )
        assert resp.status_code == 200

    def test_delete_user_success(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            user = User(
                username='del_me', password_hash='hash', name='删除我', user_type='admin'
            )
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        resp = admin_client.delete(
            f'/api/v1/admin/users/{user_id}',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        # 验证软删除
        with admin_app.app_context():
            u = User.query.get(user_id)
            assert u.is_active is False

    def test_delete_user_not_found(self, admin_client, admin_token):
        resp = admin_client.delete(
            '/api/v1/admin/users/99999',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 404

    def test_list_users(self, admin_app, admin_client, admin_token):
        with admin_app.app_context():
            db.session.add(User(
                username='list_a', password_hash='hash', name='列表A', user_type='admin'
            ))
            db.session.add(User(
                username='list_b', password_hash='hash', name='列表B', user_type='student'
            ))
            db.session.commit()

        resp = admin_client.get(
            '/api/v1/admin/users',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        # 默认只返回 admin
        usernames = [u['username'] for u in data['data']['items']]
        assert 'list_a' in usernames
        assert 'list_b' not in usernames
