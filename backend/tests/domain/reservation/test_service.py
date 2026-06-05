"""
预约模块（MOD-RESV）服务测试

覆盖：预约创建校验、冲突检测、取消、签到、违约、可用性计算、
搜索、定时任务与统计。
"""
import pytest
from datetime import datetime, date, time, timedelta

from flask import Flask
from extensions import db, init_extensions

# 导入全部模型以便 create_all 建表
from domain.user.models import User
from domain.room.models import StudyRoom, Seat, SignInCode
from domain.reservation.models import Reservation, ViolationRecord
from domain.notification.models import Notification
from domain.system.models import SystemConfig

from domain.reservation import service as resv
from infrastructure.exceptions import (
    ValidationError, ConflictError, NotFoundError, AuthorizationError,
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-secret-key-for-student-module-123456'
    init_extensions(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def seed(app):
    """创建一名学生、一个开放自习室与一个可用座位。"""
    user = User(username='2025123456', password_hash='x', name='张三', user_type='student')
    room = StudyRoom(name='理科301', location='3楼', room_type='public',
                     open_time=time(7, 0), close_time=time(22, 0), is_active=True)
    db.session.add_all([user, room])
    db.session.flush()
    seat = Seat(room_id=room.id, seat_number='A01', has_window=True, has_plug=True, status='available')
    seat2 = Seat(room_id=room.id, seat_number='A02', has_window=False, has_plug=True, status='available')
    db.session.add_all([seat, seat2])
    db.session.commit()
    return {'user': user, 'room': room, 'seat': seat, 'seat2': seat2}


def _today_at(hour):
    return datetime.combine(date.today() + timedelta(days=1), time(hour, 0))


# ---------------------------------------------------------------------------
# 创建预约
# ---------------------------------------------------------------------------

def test_create_reservation_success(seed):
    r = resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    assert r['status'] == 'reserved'
    assert r['seat_number'] == 'A01'
    assert r['room_name'] == '理科301'


def test_create_reservation_not_on_the_hour(seed):
    start = datetime.combine(date.today(), time(9, 30))
    with pytest.raises(ValidationError):
        resv.create_reservation(seed['user'].id, seed['seat'].id, start, _today_at(11))


def test_create_reservation_exceeds_max_hours(seed):
    with pytest.raises(ValidationError):
        resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(8), _today_at(20))


def test_create_reservation_outside_open_hours(seed):
    with pytest.raises(ValidationError):
        resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(5), _today_at(6))


def test_create_reservation_seat_not_found(seed):
    with pytest.raises(NotFoundError):
        resv.create_reservation(seed['user'].id, 9999, _today_at(9), _today_at(10))


def test_create_reservation_conflict(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    with pytest.raises(ConflictError):
        resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(10), _today_at(12))


def test_create_reservation_max_active(seed):
    # 默认 max_active_reservations = 2
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(10))
    resv.create_reservation(seed['user'].id, seed['seat2'].id, _today_at(9), _today_at(10))
    seat3 = Seat(room_id=seed['room'].id, seat_number='A03', status='available')
    db.session.add(seat3)
    db.session.commit()
    with pytest.raises(ConflictError):
        resv.create_reservation(seed['user'].id, seat3.id, _today_at(11), _today_at(12))


# ---------------------------------------------------------------------------
# 冲突检测
# ---------------------------------------------------------------------------

def test_check_time_conflict(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    assert resv.check_time_conflict(seed['seat'].id, _today_at(10), _today_at(12)) is True
    assert resv.check_time_conflict(seed['seat'].id, _today_at(11), _today_at(12)) is False


def test_validate_reservation_duration(seed):
    ok, _ = resv.validate_reservation_duration(_today_at(9), _today_at(11))
    assert ok is True
    bad, msg = resv.validate_reservation_duration(_today_at(9), _today_at(20))
    assert bad is False and msg


# ---------------------------------------------------------------------------
# 取消
# ---------------------------------------------------------------------------

def test_cancel_reservation_success(seed):
    r = resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    resv.cancel_reservation(r['id'], cancelled_by='user', reason='临时有事', acting_user_id=seed['user'].id)
    detail = resv.get_reservation(r['id'])
    assert detail['status'] == 'cancelled'
    assert detail['cancel_reason'] == '临时有事'


def test_cancel_reservation_not_owner(seed):
    r = resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    with pytest.raises(AuthorizationError):
        resv.cancel_reservation(r['id'], cancelled_by='user', acting_user_id=99999)


def test_cancel_reservation_not_found(seed):
    with pytest.raises(NotFoundError):
        resv.cancel_reservation(123456, cancelled_by='user', acting_user_id=seed['user'].id)


# ---------------------------------------------------------------------------
# 签到
# ---------------------------------------------------------------------------

def _make_active_reservation(seed, start_offset_minutes=-1):
    now = datetime.now()
    start = now + timedelta(minutes=start_offset_minutes)
    r = Reservation(user_id=seed['user'].id, seat_id=seed['seat'].id,
                    start_time=start, end_time=start + timedelta(hours=2), status='reserved')
    db.session.add(r)
    db.session.commit()
    return r


def test_check_in_success(seed):
    r = _make_active_reservation(seed)
    code = SignInCode(room_id=seed['room'].id, code='ABC123', valid_date=r.start_time.date(),
                      expires_at=datetime.now() + timedelta(days=1))
    db.session.add(code)
    db.session.commit()

    ts = resv.check_in(r.id, 'ABC123', acting_user_id=seed['user'].id)
    assert isinstance(ts, datetime)
    assert db.session.get(Reservation, r.id).status == 'checked_in'


def test_check_in_invalid_code(seed):
    r = _make_active_reservation(seed)
    code = SignInCode(room_id=seed['room'].id, code='ABC123', valid_date=r.start_time.date(),
                      expires_at=datetime.now() + timedelta(days=1))
    db.session.add(code)
    db.session.commit()
    with pytest.raises(ValidationError):
        resv.check_in(r.id, 'WRONG', acting_user_id=seed['user'].id)


def test_check_in_not_owner(seed):
    r = _make_active_reservation(seed)
    with pytest.raises(AuthorizationError):
        resv.check_in(r.id, 'ABC123', acting_user_id=99999)


# ---------------------------------------------------------------------------
# 违约
# ---------------------------------------------------------------------------

def test_record_violation_and_duplicate(seed):
    r = resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    v = resv.record_violation(r['id'])
    assert v['reason'] == '超时未签到'
    assert db.session.get(Reservation, r['id']).status == 'violation'
    with pytest.raises(ConflictError):
        resv.record_violation(r['id'])


def test_list_user_violations(seed):
    r = resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    resv.record_violation(r['id'])
    result = resv.list_user_violations(seed['user'].id)
    assert result['total'] == 1
    assert result['items'][0]['seat_number'] == 'A01'


# ---------------------------------------------------------------------------
# 查询
# ---------------------------------------------------------------------------

def test_list_user_reservations_filter_status(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(10))
    resv.create_reservation(seed['user'].id, seed['seat2'].id, _today_at(9), _today_at(10))
    all_res = resv.list_user_reservations(seed['user'].id)
    assert all_res['total'] == 2
    reserved = resv.list_user_reservations(seed['user'].id, status='reserved')
    assert reserved['total'] == 2
    cancelled = resv.list_user_reservations(seed['user'].id, status='cancelled')
    assert cancelled['total'] == 0


def test_get_user_active_reservations(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(10))
    active = resv.get_user_active_reservations(seed['user'].id)
    assert len(active) == 1


# ---------------------------------------------------------------------------
# 可用性与搜索
# ---------------------------------------------------------------------------

def test_get_seat_availability(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    slots = resv.get_seat_availability(seed['seat'].id, date.today() + timedelta(days=1))
    # 9-11 被占用，应不在可用时段内
    joined = ' '.join(slots)
    assert '07:00-09:00' in joined
    assert '11:00' in joined


def test_search_seats_filter_window(seed):
    result = resv.search_seats(date.today(), has_window=True)
    numbers = [s['seat_number'] for s in result['items']]
    assert 'A01' in numbers
    assert 'A02' not in numbers


def test_search_seats_time_window(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(11))
    # 要求 9-11 的座位，A01 被占用应被过滤
    result = resv.search_seats(date.today(), start_time=time(9, 0), end_time=time(11, 0), has_window=True)
    numbers = [s['seat_number'] for s in result['items']]
    assert 'A01' not in numbers


def test_list_rooms_for_student(seed):
    result = resv.list_rooms_for_student(query_date=date.today() + timedelta(days=1))
    assert result['items'][0]['name'] == '理科301'
    assert result['items'][0]['available_seats'] == 2


# ---------------------------------------------------------------------------
# 定时任务
# ---------------------------------------------------------------------------

def test_process_no_show_violations(seed):
    now = datetime.now()
    r = Reservation(user_id=seed['user'].id, seat_id=seed['seat'].id,
                    start_time=now - timedelta(hours=1), end_time=now + timedelta(hours=1),
                    status='reserved')
    db.session.add(r)
    db.session.commit()
    processed = resv.process_no_show_violations()
    assert r.id in processed
    assert db.session.get(Reservation, r.id).status == 'violation'


def test_complete_expired_reservations(seed):
    now = datetime.now()
    r = Reservation(user_id=seed['user'].id, seat_id=seed['seat'].id,
                    start_time=now - timedelta(hours=3), end_time=now - timedelta(hours=1),
                    status='checked_in')
    db.session.add(r)
    db.session.commit()
    processed = resv.complete_expired_reservations()
    assert r.id in processed
    assert db.session.get(Reservation, r.id).status == 'completed'


def test_process_pre_reservation_reminders(seed):
    now = datetime.now()
    r = Reservation(user_id=seed['user'].id, seat_id=seed['seat'].id,
                    start_time=now + timedelta(minutes=5), end_time=now + timedelta(hours=2),
                    status='reserved')
    db.session.add(r)
    db.session.commit()
    processed = resv.process_pre_reservation_reminders()
    assert r.id in processed
    assert Notification.query.filter_by(user_id=seed['user'].id, type='remind').count() == 1


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------

def test_get_reservation_stats(seed):
    resv.create_reservation(seed['user'].id, seed['seat'].id, _today_at(9), _today_at(10))
    stats = resv.get_reservation_stats(today=date.today() + timedelta(days=1))
    assert stats['today_reservations'] == 1
    assert stats['active_users'] == 1
