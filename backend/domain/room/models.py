"""
MOD-ROOM: 自习室与座位模块 - 数据实体
StudyRoom, Seat, SignInCode
"""

from datetime import datetime
from extensions import db

# ============================================================================
# 实体模型
# ============================================================================

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
    # reservations 关系在 reservation/models.py 中定义

    # 联合唯一约束：同一个自习室内座位编号不能重复
    __table_args__ = (
        db.UniqueConstraint('room_id', 'seat_number', name='uix_room_seat_number'),
    )

    def __repr__(self):
        return f"<Seat {self.seat_number} in Room {self.room_id}>"


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
