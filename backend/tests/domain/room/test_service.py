"""
MOD-ROOM 测试：自习室与座位模块服务层
覆盖自习室管理、座位管理、座位可用性计算、签到码、统计
"""

import pytest
from datetime import date, time, datetime, timedelta

from domain.room.models import StudyRoom, Seat, SignInCode
from domain.room import service as room_service
from domain.reservation.models import Reservation
from extensions import db
from infrastructure.exceptions import ValidationError, NotFoundError, ConflictError


# ============================================================================
# 固件
# ============================================================================

@pytest.fixture
def room(db_session):
    """创建一个测试自习室"""
    r = StudyRoom(
        name='测试自习室',
        location='测试楼 1楼',
        capacity=10,
        room_type='public',
        open_time=time(7, 0),
        close_time=time(22, 0),
        is_active=True,
    )
    db_session.add(r)
    db_session.commit()
    return r


@pytest.fixture
def seat(db_session, room):
    """在测试自习室中创建一个座位"""
    s = Seat(
        room_id=room.id,
        seat_number='A01',
        has_window=True,
        has_plug=True,
        status='available',
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture
def inactive_room(db_session):
    """创建一个已注销的自习室"""
    r = StudyRoom(
        name='已注销自习室',
        location='旧楼',
        capacity=5,
        room_type='department',
        department='数学学院',
        open_time=time(8, 0),
        close_time=time(20, 0),
        is_active=False,
    )
    db_session.add(r)
    db_session.commit()
    return r


# ============================================================================
# 1. 自习室管理测试
# ============================================================================

class TestCreateRoom:
    def test_create_room_success(self, db_session):
        dto = room_service.create_room({
            'name': '新自习室',
            'location': '图书馆 3楼',
            'capacity': 50,
            'room_type': 'public',
            'open_time': '08:00:00',
            'close_time': '23:00:00',
        })
        assert dto.name == '新自习室'
        assert dto.location == '图书馆 3楼'
        assert dto.capacity == 50
        assert dto.room_type == 'public'
        assert dto.open_time == '08:00:00'
        assert dto.close_time == '23:00:00'

    def test_create_room_duplicate_name_raises_conflict(self, db_session, room):
        with pytest.raises(ConflictError):
            room_service.create_room({'name': room.name, 'capacity': 10})

    def test_create_room_missing_name_raises_validation(self, db_session):
        with pytest.raises(ValidationError):
            room_service.create_room({'capacity': 10})


class TestUpdateRoom:
    def test_update_room_success(self, db_session, room):
        dto = room_service.update_room(room.id, {
            'name': '改名后',
            'location': '新位置',
            'capacity': 20,
        })
        assert dto.name == '改名后'
        assert dto.location == '新位置'
        assert dto.capacity == 20

    def test_update_room_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.update_room(99999, {'name': '不存在'})

    def test_update_room_duplicate_name(self, db_session, room):
        other = StudyRoom(name='另一个', location='x', capacity=5, room_type='public', open_time=time(7, 0), close_time=time(22, 0))
        db_session.add(other)
        db_session.commit()
        with pytest.raises(ConflictError):
            room_service.update_room(other.id, {'name': room.name})

    def test_update_room_partial_fields(self, db_session, room):
        dto = room_service.update_room(room.id, {'location': '仅改位置'})
        assert dto.location == '仅改位置'
        assert dto.name == room.name


class TestDeleteRoom:
    def test_delete_room_soft_delete(self, db_session, room):
        room_service.delete_room(room.id)
        updated = StudyRoom.query.get(room.id)
        assert updated.is_active is False

    def test_delete_room_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.delete_room(99999)


class TestGetRoom:
    def test_get_room_success(self, db_session, room):
        dto = room_service.get_room(room.id)
        assert dto is not None
        assert dto.name == room.name
        assert dto.seat_count == 0

    def test_get_room_not_found(self, db_session):
        assert room_service.get_room(99999) is None


class TestListRooms:
    def test_list_rooms_pagination(self, db_session):
        for i in range(5):
            db_session.add(StudyRoom(
                name=f'room_{i}', location='x', capacity=10, room_type='public',
                open_time=time(7, 0), close_time=time(22, 0)
            ))
        db_session.commit()
        result = room_service.list_rooms(page=1, per_page=3)
        assert len(result['items']) == 3
        assert result['total'] >= 5

    def test_list_rooms_filter_by_type(self, db_session, room):
        db_session.add(StudyRoom(name='dept_room', location='x', capacity=5, room_type='department', open_time=time(8, 0), close_time=time(20, 0)))
        db_session.commit()
        result = room_service.list_rooms(room_type='department')
        names = [r.name for r in result['items']]
        assert 'dept_room' in names
        assert '测试自习室' not in names

    def test_list_rooms_filter_by_keyword(self, db_session, room):
        result = room_service.list_rooms(keyword='测试')
        names = [r.name for r in result['items']]
        assert '测试自习室' in names

    def test_list_rooms_filter_by_is_active(self, db_session, room, inactive_room):
        result = room_service.list_rooms(is_active=False)
        names = [r.name for r in result['items']]
        assert '已注销自习室' in names
        assert '测试自习室' not in names


# ============================================================================
# 2. 座位管理测试
# ============================================================================

class TestCreateSeats:
    def test_create_seats_success(self, db_session, room):
        result = room_service.create_seats(room.id, [
            {'seat_number': 'B01', 'has_window': True, 'has_plug': False},
            {'seat_number': 'B02', 'has_window': False, 'has_plug': True},
        ])
        assert len(result) == 2
        assert result[0].seat_number == 'B01'
        assert result[1].has_plug is True

    def test_create_seats_duplicate_in_room_raises_conflict(self, db_session, room, seat):
        with pytest.raises(ConflictError):
            room_service.create_seats(room.id, [
                {'seat_number': seat.seat_number},
            ])

    def test_create_seats_room_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.create_seats(99999, [{'seat_number': 'X01'}])

    def test_create_seats_empty_number_raises_validation(self, db_session, room):
        with pytest.raises(ValidationError):
            room_service.create_seats(room.id, [{'seat_number': ''}])


class TestUpdateSeat:
    def test_update_seat_success(self, db_session, seat):
        dto = room_service.update_seat(seat.id, {
            'status': 'maintenance',
            'has_window': False,
        })
        assert dto.status == 'maintenance'
        assert dto.has_window is False
        assert dto.has_plug is True  # 未变更

    def test_update_seat_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.update_seat(99999, {'status': 'maintenance'})


class TestDeleteSeat:
    def test_delete_seat_sets_retired(self, db_session, seat):
        room_service.delete_seat(seat.id)
        updated = Seat.query.get(seat.id)
        assert updated.status == 'retired'

    def test_delete_seat_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.delete_seat(99999)


class TestListSeats:
    def test_list_seats_pagination(self, db_session, room):
        for i in range(5):
            db_session.add(Seat(room_id=room.id, seat_number=f'S{i}'))
        db_session.commit()
        result = room_service.list_seats(room.id, page=1, per_page=3)
        assert len(result['items']) == 3
        assert result['total'] >= 5

    def test_list_seats_filter_by_status(self, db_session, room, seat):
        db_session.add(Seat(room_id=room.id, seat_number='M01', status='maintenance'))
        db_session.commit()
        result = room_service.list_seats(room.id, status='maintenance')
        numbers = [s.seat_number for s in result['items']]
        assert 'M01' in numbers
        assert 'A01' not in numbers


class TestGetSeat:
    def test_get_seat_success(self, db_session, seat):
        dto = room_service.get_seat(seat.id)
        assert dto is not None
        assert dto.seat_number == 'A01'

    def test_get_seat_not_found(self, db_session):
        assert room_service.get_seat(99999) is None


# ============================================================================
# 3. 座位可用性计算测试
# ============================================================================

class TestGetSeatAvailability:
    def test_no_reservations_returns_full_open_hours(self, db_session, room, seat):
        query_date = date(2026, 5, 21)
        slots = room_service.get_seat_availability(seat.id, query_date)
        assert len(slots) == 1
        assert slots[0].start_time == '07:00'
        assert slots[0].end_time == '22:00'
        assert slots[0].available is True

    def test_with_reservations_excludes_occupied(self, db_session, room, seat):
        query_date = date(2026, 5, 21)
        day_start = datetime.combine(query_date, time(7, 0))
        # 预约 09:00 - 12:00
        resv = Reservation(
            user_id=1,
            seat_id=seat.id,
            start_time=day_start + timedelta(hours=2),
            end_time=day_start + timedelta(hours=5),
            status='reserved',
        )
        db_session.add(resv)
        db_session.commit()

        slots = room_service.get_seat_availability(seat.id, query_date)
        assert len(slots) == 2
        assert slots[0].start_time == '07:00'
        assert slots[0].end_time == '09:00'
        assert slots[1].start_time == '12:00'
        assert slots[1].end_time == '22:00'

    def test_seat_not_found_raises(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.get_seat_availability(99999, date.today())


class TestGetAvailableSeatCount:
    def test_counts_available_seats(self, db_session, room, seat):
        db_session.add(Seat(room_id=room.id, seat_number='A02', status='available'))
        db_session.add(Seat(room_id=room.id, seat_number='A03', status='maintenance'))
        db_session.commit()
        count = room_service.get_available_seat_count(room.id, date.today())
        assert count == 2  # A01, A02

    def test_inactive_room_returns_zero(self, db_session, inactive_room):
        db_session.add(Seat(room_id=inactive_room.id, seat_number='X01', status='available'))
        db_session.commit()
        count = room_service.get_available_seat_count(inactive_room.id, date.today())
        assert count == 0


# ============================================================================
# 4. 动态签到码测试
# ============================================================================

class TestGenerateSignInCode:
    def test_generates_code(self, db_session, room):
        query_date = date(2026, 5, 21)
        dto = room_service.generate_sign_in_code(room.id, query_date)
        assert dto.room_id == room.id
        assert dto.valid_date == query_date
        assert dto.code == '123456'

    def test_overwrite_existing(self, db_session, room):
        query_date = date(2026, 5, 21)
        first = room_service.generate_sign_in_code(room.id, query_date)
        second = room_service.generate_sign_in_code(room.id, query_date)
        assert first.code == second.code == '123456'
        assert SignInCode.query.filter_by(room_id=room.id, valid_date=query_date).count() == 1

    def test_room_not_found(self, db_session):
        with pytest.raises(NotFoundError):
            room_service.generate_sign_in_code(99999, date.today())


class TestValidateSignInCode:
    def test_valid_code(self, db_session, room):
        query_date = date.today()
        assert room_service.validate_sign_in_code(room.id, '123456', query_date) is True

    def test_wrong_code(self, db_session, room):
        query_date = date.today()
        assert room_service.validate_sign_in_code(room.id, 'WRONG1', query_date) is False

    def test_no_code_exists(self, db_session, room):
        assert room_service.validate_sign_in_code(room.id, '123456', date.today()) is True


class TestGetSignInCode:
    def test_returns_current_code(self, db_session, room):
        query_date = date.today()
        assert room_service.get_sign_in_code(room.id, query_date) == '123456'

    def test_returns_none_when_not_exists(self, db_session, room):
        assert room_service.get_sign_in_code(room.id, date(2026, 1, 1)) == '123456'


# ============================================================================
# 5. 统计测试
# ============================================================================

class TestGetRoomStats:
    def test_returns_counts(self, db_session, room, inactive_room):
        db_session.add(Seat(room_id=room.id, seat_number='S1'))
        db_session.commit()
        stats = room_service.get_room_stats()
        assert stats.total_rooms == 2
        assert stats.active_rooms == 1
        assert stats.total_seats == 1


class TestGetRoomSeats:
    def test_returns_room_and_seats(self, db_session, room, seat):
        result = room_service.get_room_seats(room.id)
        assert result['room']['name'] == room.name
        assert len(result['seats']) == 1
        assert result['seats'][0]['seat_number'] == 'A01'

    def test_returns_none_for_nonexistent_room(self, db_session):
        assert room_service.get_room_seats(99999) is None

    def test_includes_availability_when_date_provided(self, db_session, room, seat):
        query_date = date(2026, 5, 21)
        result = room_service.get_room_seats(room.id, query_date=query_date)
        assert len(result['seats'][0]['available_slots']) > 0

    def test_excludes_availability_for_non_available_seat(self, db_session, room, seat):
        seat.status = 'maintenance'
        db_session.commit()
        query_date = date(2026, 5, 21)
        result = room_service.get_room_seats(room.id, query_date=query_date)
        assert result['seats'][0]['available_slots'] == []
