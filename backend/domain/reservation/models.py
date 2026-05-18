"""
MOD-RESV: 预约与签到模块 - 数据实体
Reservation, ViolationRecord
"""

from datetime import datetime
from extensions import db

# ============================================================================
# 实体模型
# ============================================================================

class Reservation(db.Model):
    __tablename__ = 'reservation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, comment='预约起始时间')
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
    user = db.relationship('User', backref=db.backref('reservations', lazy='dynamic'))
    seat = db.relationship('Seat', backref=db.backref('reservations', lazy='dynamic'))
    # violation_record 关系在下面定义

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
    user = db.relationship('User', backref=db.backref('violations', lazy='dynamic'))
    reservation = db.relationship('Reservation', backref=db.backref('violation_record', uselist=False))

    def __repr__(self):
        return f"<ViolationRecord user={self.user_id}>"
