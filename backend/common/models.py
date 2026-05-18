"""
v2架构迁移：此文件保留以向后兼容
新代码请从 domain/<module>/models.py 导入
"""

from extensions import db

# 从新位置重新导出所有模型
try:
    from domain.user.models import (
        User, Role, Permission,
        user_roles, role_permissions
    )
    from domain.room.models import (
        StudyRoom, Seat, SignInCode
    )
    from domain.reservation.models import (
        Reservation, ViolationRecord
    )
    from domain.notification.models import (
        Notification
    )
    from domain.system.models import (
        SystemConfig
    )
except ImportError:
    # 旧实现作为兜底（防止导入失败）
    from datetime import datetime

    # ==================== 关联表 ====================
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

    # ==================== 用户与权限 ====================
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
        reservations = db.relationship('Reservation', back_populates='user', lazy='dynamic')
        violations = db.relationship('ViolationRecord', back_populates='user', lazy='dynamic')
        notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')

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

    # ==================== 自习室与座位 ====================
    class StudyRoom(db.Model):
        __tablename__ = 'study_room'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        name = db.Column(db.String(128), nullable=False, comment='自习室名称')
        location = db.Column(db.String(256), nullable=True, comment='具体位置')
        capacity = db.Column(db.Integer, default=0, comment='容纳人数/座位数')
        room_type = db.Column(
            db.Enum('public', 'department', name='room_type_enum'),
            default='public',
            nullable=False,
            comment='public=全校公共, department=院系专属'
        )
        department = db.Column(db.String(128), nullable=True, comment='院系专属时填写')
        open_time = db.Column(db.Time, default='07:00:00', nullable=False, comment='每日开放起始时间')
        close_time = db.Column(db.Time, default='22:00:00', nullable=False, comment='每日关闭时间')
        is_active = db.Column(db.Boolean, default=True, nullable=False, comment='是否可用（注销则为False）')
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

        # 关系
        seats = db.relationship('Seat', back_populates='study_room', lazy='dynamic', cascade='all, delete-orphan')
        sign_in_codes = db.relationship('SignInCode', back_populates='study_room', lazy='dynamic', cascade='all, delete-orphan')

        def __repr__(self):
            return f"<StudyRoom {self.name}>"

    class Seat(db.Model):
        __tablename__ = 'seat'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        room_id = db.Column(db.Integer, db.ForeignKey('study_room.id'), nullable=False)
        seat_number = db.Column(db.String(32), nullable=False, comment='座位编号')
        has_window = db.Column(db.Boolean, default=False, comment='靠窗')
        has_plug = db.Column(db.Boolean, default=False, comment='有插座')
        status = db.Column(
            db.Enum('available', 'maintenance', 'retired', name='seat_status_enum'),
            default='available',
            nullable=False,
            comment='available=正常, maintenance=维修中, retired=已注销'
        )
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

        # 关系
        study_room = db.relationship('StudyRoom', back_populates='seats')
        reservations = db.relationship('Reservation', back_populates='seat', lazy='dynamic')

        # 联合唯一约束：同一个自习室内座位编号不能重复
        __table_args__ = (
            db.UniqueConstraint('room_id', 'seat_number', name='uix_room_seat_number'),
        )

        def __repr__(self):
            return f"<Seat {self.seat_number} in Room {self.room_id}>"

    # ==================== 预约与违约 ====================
    class Reservation(db.Model):
        __tablename__ = 'reservation'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
        start_time = db.Column(db.DateTime, nullable=False, comment='预约开始时间')
        end_time = db.Column(db.DateTime, nullable=False, comment='预约结束时间')
        status = db.Column(
            db.Enum(
                'reserved',      # 已预约，未签到
                'checked_in',    # 已签到
                'completed',     # 正常结束
                'cancelled',     # 已取消（用户或管理员）
                'violation',     # 违约（超时未签到）
                name='reservation_status_enum'
            ),
            default='reserved',
            nullable=False
        )
        check_in_time = db.Column(db.DateTime, nullable=True, comment='实际签到时间')
        cancelled_by = db.Column(db.Enum('user', 'admin', 'system', name='cancelled_by_enum'), nullable=True)
        cancel_reason = db.Column(db.String(256), nullable=True)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

        # 关系
        user = db.relationship('User', back_populates='reservations')
        seat = db.relationship('Seat', back_populates='reservations')
        violation_record = db.relationship('ViolationRecord', back_populates='reservation', uselist=False)

        def __repr__(self):
            return f"<Reservation {self.id} {self.status}>"

    class ViolationRecord(db.Model):
        __tablename__ = 'violation_record'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False, unique=True)
        violation_time = db.Column(db.DateTime, nullable=False, comment='违约发生时间')
        reason = db.Column(db.String(256), default='超时未签到', nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        # 关系
        user = db.relationship('User', back_populates='violations')
        reservation = db.relationship('Reservation', back_populates='violation_record')

        def __repr__(self):
            return f"<ViolationRecord user={self.user_id}>"

    # ==================== 签到码与通知 ====================
    class SignInCode(db.Model):
        __tablename__ = 'sign_in_code'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        room_id = db.Column(db.Integer, db.ForeignKey('study_room.id'), nullable=False)
        code = db.Column(db.String(64), nullable=False, comment='动态编码或二维码字符串')
        valid_date = db.Column(db.Date, nullable=False, comment='有效日期')
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
        expires_at = db.Column(db.DateTime, nullable=False, comment='过期时间')

        # 关系
        study_room = db.relationship('StudyRoom', back_populates='sign_in_codes')

        # 联合唯一约束：每个教室每天只有一个有效签到码
        __table_args__ = (
            db.UniqueConstraint('room_id', 'valid_date', name='uix_room_date_code'),
        )

        def __repr__(self):
            return f"<SignInCode room={self.room_id} date={self.valid_date}>"

    class Notification(db.Model):
        __tablename__ = 'notification'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        type = db.Column(
            db.Enum('remind', 'check_in_alert', 'violation', 'cancel', 'system', name='notification_type_enum'),
            nullable=False,
            comment='remind=预约提醒, check_in_alert=签到提醒, violation=违约通知, cancel=取消通知, system=系统通知'
        )
        content = db.Column(db.Text, nullable=False)
        is_read = db.Column(db.Boolean, default=False, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

        # 关系
        user = db.relationship('User', back_populates='notifications')

        def __repr__(self):
            return f"<Notification {self.type} to user={self.user_id}>"

    # ==================== 系统配置 ====================
    class SystemConfig(db.Model):
        __tablename__ = 'system_config'

        id = db.Column(db.Integer, primary_key=True, autoincrement=True)
        config_key = db.Column(db.String(64), unique=True, nullable=False, comment='配置项键名')
        config_value = db.Column(db.String(512), nullable=False, comment='配置项值')
        description = db.Column(db.String(256), nullable=True)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

        def __repr__(self):
            return f"<SystemConfig {self.config_key}={self.config_value}>"
