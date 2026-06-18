"""
MOD-ROOM: 自习室与座位模块 - 服务接口
"""

import random
import string
from datetime import datetime, time, date, timedelta
from typing import Optional, List

from domain.room.models import StudyRoom, Seat, SignInCode

FIXED_SIGN_IN_CODE = '123456'
from domain.room.dto import (
    RoomDTO, RoomDetailDTO, RoomCreateDTO, RoomUpdateDTO,
    SeatDTO, SeatCreateDTO, SeatUpdateDTO,
    TimeSlotDTO, SeatSearchResultDTO, SignInCodeDTO, RoomStatsDTO,
)
from extensions import db
from infrastructure.exceptions import ValidationError, NotFoundError, ConflictError


# ============================================================================
# 辅助函数
# ============================================================================

def _parse_time_str(value) -> Optional[time]:
    """将字符串转为 time 对象，支持 HH:MM 和 HH:MM:SS"""
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        parts = value.split(':')
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        if len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    raise ValidationError(f'无效的时间格式: {value}')


def _time_to_str(t: time) -> str:
    """将 time 对象转为 HH:MM:SS 字符串"""
    if t is None:
        return None
    return t.strftime('%H:%M:%S')


def _room_to_dto(room: StudyRoom) -> RoomDTO:
    return RoomDTO(
        id=room.id,
        name=room.name,
        location=room.location,
        capacity=room.capacity,
        room_type=room.room_type,
        open_time=_time_to_str(room.open_time),
        close_time=_time_to_str(room.close_time),
        available_seats=None,
    )


def _room_to_detail_dto(room: StudyRoom) -> RoomDetailDTO:
    return RoomDetailDTO(
        id=room.id,
        name=room.name,
        location=room.location,
        capacity=room.capacity,
        room_type=room.room_type,
        department=room.department,
        open_time=_time_to_str(room.open_time),
        close_time=_time_to_str(room.close_time),
        is_active=room.is_active,
        seat_count=room.seats.count(),
    )


def _seat_to_dto(seat: Seat) -> SeatDTO:
    return SeatDTO(
        id=seat.id,
        room_id=seat.room_id,
        seat_number=seat.seat_number,
        has_window=seat.has_window,
        has_plug=seat.has_plug,
        status=seat.status,
    )


def _sign_in_code_to_dto(code: SignInCode) -> SignInCodeDTO:
    return SignInCodeDTO(
        id=code.id,
        room_id=code.room_id,
        code=code.code,
        valid_date=code.valid_date,
        expires_at=code.expires_at.isoformat(),
    )


def _paginated_result(pagination):
    """统一分页结果格式"""
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


# ============================================================================
# 自习室管理
# ============================================================================

def create_room(data: dict) -> RoomDTO:
    """登记新自习室。约束：name 全局唯一。"""
    name = data.get('name')
    if not name:
        raise ValidationError('自习室名称不能为空')

    if StudyRoom.query.filter_by(name=name).first():
        raise ConflictError(f'自习室名称已存在: {name}')

    open_time = _parse_time_str(data.get('open_time', '07:00:00'))
    close_time = _parse_time_str(data.get('close_time', '22:00:00'))

    room = StudyRoom(
        name=name,
        location=data.get('location'),
        capacity=data.get('capacity', 0),
        room_type=data.get('room_type', 'public'),
        department=data.get('department'),
        open_time=open_time,
        close_time=close_time,
        is_active=True,
    )
    db.session.add(room)
    db.session.commit()
    return _room_to_dto(room)


def update_room(room_id: int, data: dict) -> RoomDTO:
    """更新自习室信息。"""
    room = StudyRoom.query.get(room_id)
    if not room:
        raise NotFoundError('自习室不存在')

    new_name = data.get('name')
    if new_name is not None and new_name != room.name:
        if StudyRoom.query.filter(StudyRoom.name == new_name, StudyRoom.id != room_id).first():
            raise ConflictError(f'自习室名称已存在: {new_name}')
        room.name = new_name

    if data.get('location') is not None:
        room.location = data['location']
    if data.get('capacity') is not None:
        room.capacity = data['capacity']
    if data.get('room_type') is not None:
        room.room_type = data['room_type']
    if data.get('department') is not None:
        room.department = data['department']
    if data.get('open_time') is not None:
        room.open_time = _parse_time_str(data['open_time'])
    if data.get('close_time') is not None:
        room.close_time = _parse_time_str(data['close_time'])

    db.session.commit()
    return _room_to_dto(room)


def delete_room(room_id: int) -> None:
    """注销自习室（软删除），并取消未来预约。"""
    room = StudyRoom.query.get(room_id)
    if not room:
        raise NotFoundError('自习室不存在')

    room.is_active = False
    db.session.commit()

    # 调用预约模块取消未来预约（接口已存在，即使为 TODO 也正常调用）
    try:
        from domain.reservation import service as reservation_service
        reservation_service.cancel_future_reservations_by_room(room_id)
    except ImportError:
        pass


def get_room(room_id: int) -> Optional[RoomDetailDTO]:
    """获取自习室详情，含座位统计。"""
    room = StudyRoom.query.get(room_id)
    if not room:
        return None
    return _room_to_detail_dto(room)


def list_rooms(room_type: str = None, is_active: bool = None, keyword: str = None,
               page: int = 1, per_page: int = 20):
    """分页查询自习室列表。"""
    query = StudyRoom.query
    if room_type:
        query = query.filter(StudyRoom.room_type == room_type)
    if is_active is not None:
        query = query.filter(StudyRoom.is_active == is_active)
    if keyword:
        query = query.filter(
            db.or_(
                StudyRoom.name.contains(keyword),
                StudyRoom.location.contains(keyword)
            )
        )

    pagination = query.order_by(StudyRoom.id).paginate(page=page, per_page=per_page, error_out=False)
    items = [_room_to_dto(r) for r in pagination.items]
    for dto in items:
        dto.available_seats = get_available_seat_count(dto.id, date.today())
    return {
        'items': items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


# ============================================================================
# 座位管理
# ============================================================================

def create_seats(room_id: int, seats_data: List[dict]) -> List[SeatDTO]:
    """批量登记座位。约束：同一自习室内 seat_number 唯一。"""
    room = StudyRoom.query.get(room_id)
    if not room:
        raise NotFoundError('自习室不存在')

    # 收集现有编号
    existing_numbers = {s.seat_number for s in Seat.query.filter_by(room_id=room_id).all()}

    seats_to_create = []
    seen_numbers = set()
    for item in seats_data:
        seat_number = item.get('seat_number')
        if not seat_number:
            raise ValidationError('座位编号不能为空')
        if seat_number in existing_numbers or seat_number in seen_numbers:
            raise ConflictError(f'座位编号重复: {seat_number}')
        seen_numbers.add(seat_number)
        seats_to_create.append(Seat(
            room_id=room_id,
            seat_number=seat_number,
            has_window=item.get('has_window', False),
            has_plug=item.get('has_plug', False),
            status='available',
        ))

    db.session.add_all(seats_to_create)
    db.session.commit()
    return [_seat_to_dto(s) for s in seats_to_create]


def update_seat(seat_id: int, data: dict) -> SeatDTO:
    """更新座位信息。"""
    seat = Seat.query.get(seat_id)
    if not seat:
        raise NotFoundError('座位不存在')

    if data.get('seat_number') is not None:
        seat.seat_number = data['seat_number']
    if data.get('has_window') is not None:
        seat.has_window = data['has_window']
    if data.get('has_plug') is not None:
        seat.has_plug = data['has_plug']
    if data.get('status') is not None:
        seat.status = data['status']

    db.session.commit()
    return _seat_to_dto(seat)


def delete_seat(seat_id: int) -> None:
    """注销座位（status 设为 retired）。"""
    seat = Seat.query.get(seat_id)
    if not seat:
        raise NotFoundError('座位不存在')

    seat.status = 'retired'
    db.session.commit()

    try:
        from domain.reservation import service as reservation_service
        reservation_service.cancel_future_reservations_by_seat(seat_id)
    except ImportError:
        pass


def list_seats(room_id: int, status: str = None, page: int = 1, per_page: int = 20):
    """分页查询某自习室的座位列表。"""
    query = Seat.query.filter_by(room_id=room_id)
    if status:
        query = query.filter(Seat.status == status)

    pagination = query.order_by(Seat.seat_number).paginate(page=page, per_page=per_page, error_out=False)
    items = [_seat_to_dto(s) for s in pagination.items]
    return {
        'items': items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


def get_seat(seat_id: int) -> Optional[SeatDTO]:
    """获取单个座位详情。"""
    seat = Seat.query.get(seat_id)
    if not seat:
        return None
    return _seat_to_dto(seat)


# ============================================================================
# 座位可用性计算
# ============================================================================

def get_seat_availability(seat_id: int, query_date: date) -> List[TimeSlotDTO]:
    """
    计算指定座位在某一天的可用时间段列表。
    逻辑：根据自习室开放时间，减去当天已预约/已签到的时间段。
    """
    seat = Seat.query.get(seat_id)
    if not seat:
        raise NotFoundError('座位不存在')

    room = seat.study_room
    if not room or not room.is_active:
        return []

    # 构建当天的开放时间段
    day_start = datetime.combine(query_date, room.open_time)
    day_end = datetime.combine(query_date, room.close_time)

    # 查询当天该座位的已占用预约（reserved 或 checked_in）
    from domain.reservation.models import Reservation
    reservations = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status.in_(['reserved', 'checked_in']),
        Reservation.start_time < day_end,
        Reservation.end_time > day_start,
    ).order_by(Reservation.start_time).all()

    # 构建被占用区间列表
    occupied = []
    for r in reservations:
        occupied_start = max(r.start_time, day_start)
        occupied_end = min(r.end_time, day_end)
        occupied.append((occupied_start, occupied_end))

    # 合并重叠区间
    merged = []
    for start, end in occupied:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    # 计算可用区间
    available_slots = []
    current = day_start
    for occ_start, occ_end in merged:
        if current < occ_start:
            available_slots.append(TimeSlotDTO(
                start_time=current.strftime('%H:%M'),
                end_time=occ_start.strftime('%H:%M'),
                available=True,
            ))
        current = max(current, occ_end)

    if current < day_end:
        available_slots.append(TimeSlotDTO(
            start_time=current.strftime('%H:%M'),
            end_time=day_end.strftime('%H:%M'),
            available=True,
        ))

    return available_slots


def search_seats(query_date: date, start_time: time = None, end_time: time = None,
                 has_window: bool = None, has_plug: bool = None, room_type: str = None,
                 department: str = None, page: int = 1, per_page: int = 20):
    """
    按条件搜索座位。
    返回结果包含：座位基本信息、所属自习室、可用时间段列表。
    """
    query = db.session.query(Seat, StudyRoom).join(
        StudyRoom, Seat.room_id == StudyRoom.id
    ).filter(
        Seat.status == 'available',
        StudyRoom.is_active == True,
    )

    if has_window is not None:
        query = query.filter(Seat.has_window == has_window)
    if has_plug is not None:
        query = query.filter(Seat.has_plug == has_plug)
    if room_type:
        query = query.filter(StudyRoom.room_type == room_type)
    if department:
        query = query.filter(StudyRoom.department == department)

    # 先获取所有匹配座位（不分页，因为需要计算可用性后过滤）
    results = query.order_by(StudyRoom.id, Seat.seat_number).all()

    filtered = []
    for seat, room in results:
        slots = get_seat_availability(seat.id, query_date)
        # 如果指定了时间段，只保留完全包含该时段的座位
        if start_time and end_time:
            req_start = datetime.combine(query_date, start_time)
            req_end = datetime.combine(query_date, end_time)
            fits = False
            for slot in slots:
                slot_start = datetime.combine(query_date, datetime.strptime(slot.start_time, '%H:%M').time())
                slot_end = datetime.combine(query_date, datetime.strptime(slot.end_time, '%H:%M').time())
                if slot_start <= req_start and slot_end >= req_end:
                    fits = True
                    break
            if not fits:
                continue

        filtered.append(SeatSearchResultDTO(
            id=seat.id,
            seat_number=seat.seat_number,
            has_window=seat.has_window,
            has_plug=seat.has_plug,
            room_id=room.id,
            room_name=room.name,
            available_slots=slots,
        ))

    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = filtered[start:end]
    pages = (total + per_page - 1) // per_page if total > 0 else 0

    return {
        'items': page_items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
    }


def get_available_seat_count(room_id: int, query_date: date) -> int:
    """获取某自习室在某天的可用座位数量（至少有一个可用时段）。"""
    seats = Seat.query.filter_by(room_id=room_id, status='available').all()
    count = 0
    for seat in seats:
        slots = get_seat_availability(seat.id, query_date)
        if slots:
            count += 1
    return count


# ============================================================================
# 动态签到码管理
# ============================================================================

def _generate_random_code(length: int = 6) -> str:
    """生成签到码。课程演示版固定为 123456。"""
    return FIXED_SIGN_IN_CODE


def generate_sign_in_code(room_id: int, valid_date: date) -> SignInCodeDTO:
    """为指定自习室生成指定日期的动态签到码。"""
    room = StudyRoom.query.get(room_id)
    if not room:
        raise NotFoundError('自习室不存在')

    code_str = _generate_random_code()
    expires_at = datetime.combine(valid_date + timedelta(days=1), time(0, 0))

    existing = SignInCode.query.filter_by(room_id=room_id, valid_date=valid_date).first()
    if existing:
        existing.code = code_str
        existing.expires_at = expires_at
    else:
        existing = SignInCode(
            room_id=room_id,
            code=code_str,
            valid_date=valid_date,
            expires_at=expires_at,
        )
        db.session.add(existing)

    db.session.commit()
    return _sign_in_code_to_dto(existing)


def validate_sign_in_code(room_id: int, code: str, valid_date: date) -> bool:
    """校验签到码是否有效。课程演示版固定为 123456。"""
    return str(code).strip() == FIXED_SIGN_IN_CODE


def get_sign_in_code(room_id: int, valid_date: date) -> Optional[str]:
    """获取指定教室指定日期的当前有效签到码。课程演示版固定为 123456。"""
    return FIXED_SIGN_IN_CODE


# ============================================================================
# 统计
# ============================================================================

def get_room_stats() -> RoomStatsDTO:
    """返回自习室与座位的全局统计。"""
    total_rooms = StudyRoom.query.count()
    total_seats = Seat.query.count()
    active_rooms = StudyRoom.query.filter_by(is_active=True).count()
    return RoomStatsDTO(
        total_rooms=total_rooms,
        total_seats=total_seats,
        active_rooms=active_rooms,
    )


def get_room_seats(room_id: int, query_date: date = None):
    """查询指定自习室的座位及可用时间段。"""
    room = StudyRoom.query.get(room_id)
    if not room:
        return None

    seats = Seat.query.filter_by(room_id=room_id).order_by(Seat.seat_number).all()
    result = {
        'room': {'id': room.id, 'name': room.name},
        'seats': [],
    }
    for s in seats:
        seat_dict = {
            'id': s.id,
            'seat_number': s.seat_number,
            'has_window': s.has_window,
            'has_plug': s.has_plug,
            'status': s.status,
            'available_slots': [],
        }
        if query_date and s.status == 'available':
            seat_dict['available_slots'] = get_seat_availability(s.id, query_date)
        result['seats'].append(seat_dict)
    return result
