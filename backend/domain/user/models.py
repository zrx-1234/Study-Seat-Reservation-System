"""
MOD-USER: 用户与权限模块 - 数据实体
User, Role, Permission, user_roles, role_permissions
"""

from datetime import datetime
from extensions import db

# ============================================================================
# 关联表
# ============================================================================

user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

role_permissions = db.Table(
    'role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

# ============================================================================
# 实体模型
# ============================================================================

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False, comment='学号/工号/账号')
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(64), nullable=False, comment='真实姓名')
    user_type = db.Column(db.Enum('student', 'admin', name='user_type_enum'), nullable=False)
    department = db.Column(db.String(128), nullable=True, comment='所属院系')
    email = db.Column(db.String(128), nullable=True)
    phone = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    # reservations 关系在 reservation/models.py 中定义
    # violations 关系在 reservation/models.py 中定义
    # notifications 关系在 notification/models.py 中定义

    def __repr__(self):
        return f"<User {self.username} ({self.name})>"


class Role(db.Model):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False, comment='角色名称')
    description = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    permissions = db.relationship('Permission', secondary=role_permissions, back_populates='roles')

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(db.Model):
    __tablename__ = 'permission'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False, comment='权限名称')
    code = db.Column(db.String(64), unique=True, nullable=False, comment='权限代码')
    description = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    roles = db.relationship('Role', secondary=role_permissions, back_populates='permissions')

    def __repr__(self):
        return f"<Permission {self.code}>"
