"""
通知模块（MOD-NOTIF）服务测试
"""
import pytest

from flask import Flask
from extensions import db, init_extensions

from domain.user.models import User
from domain.notification.models import Notification
from domain.notification import service as notif


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    init_extensions(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def user(app):
    u = User(username='2025123456', password_hash='x', name='张三', user_type='student')
    db.session.add(u)
    db.session.commit()
    return u


def test_send_notification(user):
    result = notif.send_notification(user.id, 'system', '欢迎使用')
    assert result['id'] is not None
    assert result['type'] == 'system'
    assert result['is_read'] is False


def test_send_notification_invalid_type_coerced(user):
    result = notif.send_notification(user.id, 'unknown_type', '内容')
    assert result['type'] == 'system'


def test_list_notifications_with_unread_count(user):
    notif.send_notification(user.id, 'system', 'A')
    notif.send_notification(user.id, 'remind', 'B')
    result = notif.list_notifications(user.id)
    assert result['total'] == 2
    assert result['unread_count'] == 2


def test_list_notifications_filter_is_read(user):
    n1 = notif.send_notification(user.id, 'system', 'A')
    notif.send_notification(user.id, 'remind', 'B')
    notif.mark_as_read(n1['id'], user.id)
    unread = notif.list_notifications(user.id, is_read=False)
    assert unread['total'] == 1


def test_mark_as_read(user):
    n = notif.send_notification(user.id, 'system', 'A')
    notif.mark_as_read(n['id'], user.id)
    assert db.session.get(Notification, n['id']).is_read is True


def test_mark_as_read_only_own(user):
    other = User(username='other', password_hash='x', name='李四', user_type='student')
    db.session.add(other)
    db.session.commit()
    n = notif.send_notification(user.id, 'system', 'A')
    # 他人无法标记
    notif.mark_as_read(n['id'], other.id)
    assert db.session.get(Notification, n['id']).is_read is False


def test_mark_all_as_read(user):
    notif.send_notification(user.id, 'system', 'A')
    notif.send_notification(user.id, 'remind', 'B')
    count = notif.mark_all_as_read(user.id)
    assert count == 2
    assert notif.get_unread_count(user.id) == 0


def test_get_unread_count(user):
    notif.send_notification(user.id, 'system', 'A')
    assert notif.get_unread_count(user.id) == 1
