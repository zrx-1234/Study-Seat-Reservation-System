"""
学生端 API（API-STU）接口测试
"""
import pytest
from datetime import datetime, date, time, timedelta

from flask import Flask
from extensions import db, init_extensions, jwt

from domain.user.models import User
from domain.room.models import StudyRoom, Seat
from domain.reservation.models import Reservation, ViolationRecord
from domain.notification.models import Notification
from domain.system.models import SystemConfig

from infrastructure.auth import hash_password, register_jwt_callbacks
from infrastructure.exceptions import register_error_handlers
from api.student import student_bp


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-for-student-module-123456'

    init_extensions(app)
    register_jwt_callbacks(jwt)
    register_error_handlers(app)
    app.register_blueprint(student_bp)

    with app.app_context():
        db.create_all()
        _seed()
        yield app
        db.session.remove()
        db.drop_all()


def _seed():
    # 测试种子需可重复执行，避免唯一键冲突导致 500 错误
    student = User.query.filter_by(username='2025123456').first()
    if not student:
        student = User(
            username='2025123456',
            password_hash=hash_password('123456'),
            name='张三',
            user_type='student',
            department='计算机学院',
            email='2025123456@fdu.edu.cn',
            is_active=True,
        )
        db.session.add(student)

    room = StudyRoom.query.filter_by(name='理科301').first()
    if not room:
        room = StudyRoom(
            name='理科301',
            location='3楼',
            room_type='public',
            open_time=time(7, 0),
            close_time=time(22, 0),
            is_active=True,
        )
        db.session.add(room)
        db.session.flush()

    seat = Seat.query.filter_by(room_id=room.id, seat_number='A01').first()
    if not seat:
        seat = Seat(
            room_id=room.id,
            seat_number='A01',
            has_window=True,
            has_plug=True,
            status='available',
        )
        db.session.add(seat)

    db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    resp = client.post('/api/v1/student/auth/login',
                       json={'username': '2025123456', 'password': '123456'})
    token = resp.get_json()['data']['access_token']
    return {'Authorization': f'Bearer {token}'}


def _seat_id():
    return Seat.query.filter_by(seat_number='A01').first().id


def _today_iso(hour):
    return datetime.combine(date.today() + timedelta(days=1), time(hour, 0)).isoformat()


# ---------------------------------------------------------------------------
# 认证
# ---------------------------------------------------------------------------

def test_login_success(client):
    resp = client.post('/api/v1/student/auth/login',
                       json={'username': '2025123456', 'password': '123456'})
    assert resp.status_code == 200
    data = resp.get_json()['data']
    assert data['access_token']
    assert data['user']['user_type'] == 'student'


def test_login_wrong_password(client):
    resp = client.post('/api/v1/student/auth/login',
                       json={'username': '2025123456', 'password': 'bad'})
    assert resp.get_json()['code'] == 401


def test_login_missing_fields(client):
    resp = client.post('/api/v1/student/auth/login', json={'username': '2025123456'})
    assert resp.get_json()['code'] == 400


def test_register_success(client):
    resp = client.post('/api/v1/student/auth/register', json={
        'username': '2025000001',
        'password': '123456',
        'name': '李雷',
        'department': '计算机学院',
        'email': '2025000001@fdu.edu.cn',
    })
    data = resp.get_json()
    assert data['code'] == 200
    assert data['message'] == '注册成功'
    assert data['data']['access_token']
    assert data['data']['user']['username'] == '2025000001'


def test_register_duplicate_username(client):
    resp = client.post('/api/v1/student/auth/register', json={
        'username': '2025123456',
        'password': '123456',
        'name': '张三',
    })
    assert resp.get_json()['code'] == 409


def test_register_short_password(client):
    resp = client.post('/api/v1/student/auth/register', json={
        'username': '2025000002',
        'password': '123',
        'name': '韩梅梅',
    })
    assert resp.get_json()['code'] == 400


def test_protected_requires_token(client):
    resp = client.get('/api/v1/student/profile')
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 个人信息
# ---------------------------------------------------------------------------

def test_profile(client, auth_headers):
    resp = client.get('/api/v1/student/profile', headers=auth_headers)
    data = resp.get_json()['data']
    assert data['username'] == '2025123456'
    assert data['active_reservations'] == 0
    assert data['total_violations'] == 0


# ---------------------------------------------------------------------------
# 自习室与座位
# ---------------------------------------------------------------------------

def test_list_rooms(client, auth_headers):
    query_date = (date.today() + timedelta(days=1)).isoformat()
    resp = client.get(f'/api/v1/student/rooms?date={query_date}', headers=auth_headers)
    items = resp.get_json()['data']['items']
    assert items[0]['name'] == '理科301'
    assert items[0]['available_seats'] == 1


def test_list_room_seats_requires_date(client, auth_headers):
    room_id = StudyRoom.query.first().id
    resp = client.get(f'/api/v1/student/rooms/{room_id}/seats', headers=auth_headers)
    assert resp.get_json()['code'] == 400


def test_list_room_seats(client, auth_headers):
    room_id = StudyRoom.query.first().id
    query_date = (date.today() + timedelta(days=1)).isoformat()
    resp = client.get(f'/api/v1/student/rooms/{room_id}/seats?date={query_date}',
                      headers=auth_headers)
    data = resp.get_json()['data']
    assert data['room']['name'] == '理科301'
    assert len(data['seats']) == 1
    assert data['seats'][0]['available_slots']


def test_search_seats(client, auth_headers):
    query_date = (date.today() + timedelta(days=1)).isoformat()
    resp = client.get(f'/api/v1/student/seats/search?date={query_date}&has_window=true',
                      headers=auth_headers)
    items = resp.get_json()['data']['items']
    assert any(s['seat_number'] == 'A01' for s in items)


# ---------------------------------------------------------------------------
# 预约
# ---------------------------------------------------------------------------

def test_create_reservation(client, auth_headers):
    resp = client.post('/api/v1/student/reservations', headers=auth_headers, json={
        'seat_id': _seat_id(),
        'start_time': _today_iso(9),
        'end_time': _today_iso(11),
    })
    data = resp.get_json()
    assert data['code'] == 200
    assert data['data']['status'] == 'reserved'


def test_create_reservation_missing_fields(client, auth_headers):
    resp = client.post('/api/v1/student/reservations', headers=auth_headers,
                       json={'seat_id': _seat_id()})
    assert resp.get_json()['code'] == 400


def test_create_reservation_conflict(client, auth_headers):
    payload = {'seat_id': _seat_id(), 'start_time': _today_iso(9), 'end_time': _today_iso(11)}
    client.post('/api/v1/student/reservations', headers=auth_headers, json=payload)
    resp = client.post('/api/v1/student/reservations', headers=auth_headers, json={
        'seat_id': _seat_id(), 'start_time': _today_iso(10), 'end_time': _today_iso(12)})
    assert resp.get_json()['code'] == 409


def test_list_and_get_reservation(client, auth_headers):
    create = client.post('/api/v1/student/reservations', headers=auth_headers, json={
        'seat_id': _seat_id(), 'start_time': _today_iso(9), 'end_time': _today_iso(11)})
    rid = create.get_json()['data']['id']

    lst = client.get('/api/v1/student/reservations', headers=auth_headers)
    assert lst.get_json()['data']['total'] == 1

    detail = client.get(f'/api/v1/student/reservations/{rid}', headers=auth_headers)
    assert detail.get_json()['data']['id'] == rid


def test_cancel_reservation(client, auth_headers):
    create = client.post('/api/v1/student/reservations', headers=auth_headers, json={
        'seat_id': _seat_id(), 'start_time': _today_iso(9), 'end_time': _today_iso(11)})
    rid = create.get_json()['data']['id']
    resp = client.post(f'/api/v1/student/reservations/{rid}/cancel', headers=auth_headers,
                       json={'reason': '临时有事'})
    assert resp.get_json()['code'] == 200
    detail = client.get(f'/api/v1/student/reservations/{rid}', headers=auth_headers)
    assert detail.get_json()['data']['status'] == 'cancelled'


# ---------------------------------------------------------------------------
# 签到
# ---------------------------------------------------------------------------

def test_check_in(client, auth_headers):
    user = User.query.filter_by(username='2025123456').first()
    seat = Seat.query.filter_by(seat_number='A01').first()
    now = datetime.now()
    r = Reservation(user_id=user.id, seat_id=seat.id, start_time=now - timedelta(minutes=1),
                    end_time=now + timedelta(hours=2), status='reserved')
    db.session.add(r)
    db.session.commit()
    rid = r.id

    resp = client.post(f'/api/v1/student/reservations/{rid}/check-in', headers=auth_headers,
                       json={'code': '123456'})
    assert resp.get_json()['code'] == 200
    assert resp.get_json()['data']['check_in_time']


def test_check_in_missing_code(client, auth_headers):
    resp = client.post('/api/v1/student/reservations/1/check-in', headers=auth_headers, json={})
    assert resp.get_json()['code'] == 400


# ---------------------------------------------------------------------------
# 通知与违约
# ---------------------------------------------------------------------------

def test_notifications_flow(client, auth_headers):
    # 创建预约会产生一条 system 通知
    client.post('/api/v1/student/reservations', headers=auth_headers, json={
        'seat_id': _seat_id(), 'start_time': _today_iso(9), 'end_time': _today_iso(11)})

    lst = client.get('/api/v1/student/notifications', headers=auth_headers)
    data = lst.get_json()['data']
    assert data['total'] >= 1
    nid = data['items'][0]['id']

    read = client.put(f'/api/v1/student/notifications/{nid}/read', headers=auth_headers)
    assert read.get_json()['code'] == 200

    read_all = client.put('/api/v1/student/notifications/read-all', headers=auth_headers)
    assert read_all.get_json()['code'] == 200


def test_violations_empty(client, auth_headers):
    resp = client.get('/api/v1/student/violations', headers=auth_headers)
    assert resp.get_json()['data']['total'] == 0
