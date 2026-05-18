"""
MOD-NOTIF: 通知模块 - 服务接口
"""

from typing import Optional, List

from domain.notification.models import Notification
from extensions import db

# ============================================================================
# 通知服务（待实现）
# ============================================================================

def send_notification(user_id: int, notification_type: str, content: str,
                      related_entity_type: str = None, related_entity_id: int = None):
    """
    创建并发送一条通知
    """
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        content=content,
        is_read=False
    )
    db.session.add(notif)
    db.session.commit()

    return {
        'id': notif.id,
        'user_id': notif.user_id,
        'type': notif.type,
        'content': notif.content,
        'is_read': notif.is_read,
        'created_at': notif.created_at.isoformat()
    }


def list_notifications(user_id: int, is_read: bool = None, page: int = 1, per_page: int = 20):
    """查询用户的通知列表（分页）"""
    query = Notification.query.filter_by(user_id=user_id)
    if is_read is not None:
        query = query.filter_by(is_read=is_read)

    pagination = query.order_by(Notification.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [{'id': n.id, 'type': n.type, 'content': n.content, 'is_read': n.is_read,
                   'created_at': n.created_at.isoformat()} for n in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }


def mark_as_read(notification_id: int, user_id: int):
    """标记单条通知为已读"""
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()


def mark_all_as_read(user_id: int) -> int:
    """标记用户所有通知为已读，返回更新数量"""
    count = Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return count


def get_unread_count(user_id: int) -> int:
    """获取用户未读通知数量"""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
