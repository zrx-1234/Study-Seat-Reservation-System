"""
MOD-NOTIF: 通知模块 - 数据实体
Notification
"""

from datetime import datetime
from extensions import db

# ============================================================================
# 实体模型
# ============================================================================

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
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f"<Notification {self.type} to user={self.user_id}>"
