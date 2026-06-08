"""
MOD-RESV: 预约与签到模块 - 服务接口

本模块封装预约的完整业务规则：提交/取消/详情/签到、时间冲突检测、
违约判定与记录、座位可用性计算、统计、定时任务触发。

依赖说明：
- 通过 domain.system.service 读取系统配置；
- 通过 domain.notification.service 发送通知；
- 读取 domain.room 的座位/自习室/签到码数据用于校验与展示。
"""

import csv
import io
from typing import Optional, List
from datetime import datetime, date, time, timedelta

from domain.reservation.models import Reservation, ViolationRecord
from domain.room.models import StudyRoom, Seat, SignInCode
from domain.user.models import User
from domain.system import service as system_service
from domain.notification import service as notification_service
from infrastructure.exceptions import (
    NotFoundError, ConflictError, ValidationError, AuthorizationError,
)
from extensions import db

# 视为“占用座位”的预约状态（用于冲突检测与可用性计算）
ACTIVE_STATUSES = ('reserved', 'checked_in', 'completed')


# ============================================================================
# 内部工具
# ============================================================================

def _now() -> datetime:
    """当前时间（与客户端传入的本地时间保持一致，便于比较）"""
    return datetime.now()


def _is_on_the_hour(dt: datetime) -> bool:
    return dt.minute == 0 and dt.second == 0 and dt.microsecond == 0


def _reservation_to_dict(r: Reservation) -> dict:
    seat = r.seat
    room = seat.study_room if seat else None
    return {
        'id': r.id,
        'seat_id': r.seat_id,
        'seat_number': seat.seat_number if seat else None,
        'room_name': room.name if room else None,
        'start_time': r.start_time.isoformat() if r.start_time else None,
        'end_time': r.end_time.isoformat() if r.end_time else None,
        'status': r.status,
        'check_in_time': r.check_in_time.isoformat() if r.check_in_time else None,
        'created_at': r.created_at.isoformat() if r.created_at else None,
    }


def _reservation_detail_dict(r: Reservation) -> dict:
    seat = r.seat
    room = seat.study_room if seat else None
    user = r.user
    return {
        'id': r.id,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.name,
        } if user else None,
        'seat': {
            'id': seat.id,
            'seat_number': seat.seat_number,
            'has_window': seat.has_window,
            'has_plug': seat.has_plug,
        } if seat else None,
        'room': {
            'id': room.id,
            'name': room.name,
            'location': room.location,
        } if room else None,
        'start_time': r.start_time.isoformat() if r.start_time else None,
        'end_time': r.end_time.isoformat() if r.end_time else None,
        'status': r.status,
        'check_in_time': r.check_in_time.isoformat() if r.check_in_time else None,
        'cancel_reason': r.cancel_reason,
        'created_at': r.created_at.isoformat() if r.created_at else None,
    }


def _violation_to_dict(v: ViolationRecord) -> dict:
    reservation = v.reservation
    seat = reservation.seat if reservation else None
    room = seat.study_room if seat else None
    return {
        'id': v.id,
        'reservation_id': v.reservation_id,
        'violation_time': v.violation_time.isoformat() if v.violation_time else None,
        'reason': v.reason,
        'seat_number': seat.seat_number if seat else None,
        'room_name': room.name if room else None,
    }


def _violation_detail_dict(v: ViolationRecord) -> dict:
    reservation = v.reservation
    user = v.user
    seat = reservation.seat if reservation else None
    room = seat.study_room if seat else None
    return {
        'id': v.id,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.name,
        } if user else None,
        'reservation': {
            'id': reservation.id,
            'seat_number': seat.seat_number if seat else None,
            'room_name': room.name if room else None,
            'start_time': reservation.start_time.isoformat() if reservation else None,
            'end_time': reservation.end_time.isoformat() if reservation else None,
        } if reservation else None,
        'violation_time': v.violation_time.isoformat() if v.violation_time else None,
        'reason': v.reason,
    }


def _paginate(query, page: int, per_page: int, mapper):
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [mapper(item) for item in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


# ============================================================================
# 冲突检测与校验
# ============================================================================

def check_time_conflict(seat_id: int, start_time: datetime, end_time: datetime,
                        exclude_reservation_id: int = None) -> bool:
    """检查指定座位在目标时间段是否存在冲突预约。

    冲突定义：两个时间段有交集，且预约状态不属于 cancelled / violation。
    返回 True 表示存在冲突，False 表示可用。
    """
    query = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status.in_(ACTIVE_STATUSES),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    )
    if exclude_reservation_id is not None:
        query = query.filter(Reservation.id != exclude_reservation_id)
    return db.session.query(query.exists()).scalar()


def validate_reservation_duration(start_time: datetime, end_time: datetime) -> tuple:
    """校验预约时长是否符合系统配置的最大预约时长。返回 (是否合法, 错误原因)。"""
    if end_time <= start_time:
        return False, '结束时间必须晚于开始时间，且至少 1 小时'

    max_hours = system_service.get_config_as_int('max_reservation_hours', 4)
    duration_hours = (end_time - start_time).total_seconds() / 3600
    if duration_hours < 1:
        return False, '预约时长至少为 1 小时'
    if duration_hours > max_hours:
        return False, f'单次预约时长不能超过 {max_hours} 小时'
    return True, ''


# ============================================================================
# 预约生命周期
# ============================================================================

def create_reservation(user_id: int, seat_id: int,
                       start_time: datetime, end_time: datetime) -> dict:
    """提交座位预约。

    校验规则：
      1. 起止时间必须为整点小时；
      2. 单次预约时长 <= max_reservation_hours；
      3. 用户进行中预约数 < max_active_reservations；
      4. 目标时间段内无冲突预约；
      5. 座位状态为 available；
      6. 预约时间段在自习室开放时间内。
    """
    if not _is_on_the_hour(start_time) or not _is_on_the_hour(end_time):
        raise ValidationError('预约起止时间必须为整点小时')
    if start_time <= _now():
        raise ValidationError('预约开始时间必须晚于当前时间')

    ok, msg = validate_reservation_duration(start_time, end_time)
    if not ok:
        raise ValidationError(msg)

    seat = db.session.get(Seat, seat_id)
    if not seat:
        raise NotFoundError('座位不存在')
    if seat.status != 'available':
        raise ConflictError('该座位当前不可预约')

    room = seat.study_room
    if room is None or not room.is_active:
        raise ConflictError('该自习室当前不可用')

    # 预约时段须在自习室开放时间内
    if start_time.time() < room.open_time or end_time.time() > room.close_time:
        raise ValidationError(
            f'预约时段须在自习室开放时间内（{room.open_time}~{room.close_time}）'
        )

    # 进行中预约数限制
    max_active = system_service.get_config_as_int('max_active_reservations', 2)
    active_count = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status.in_(('reserved', 'checked_in')),
    ).count()
    if active_count >= max_active:
        raise ConflictError(f'最多同时拥有 {max_active} 个进行中的预约')

    # 时间冲突
    if check_time_conflict(seat_id, start_time, end_time):
        raise ConflictError('该时间段座位已被预约')

    reservation = Reservation(
        user_id=user_id,
        seat_id=seat_id,
        start_time=start_time,
        end_time=end_time,
        status='reserved',
    )
    db.session.add(reservation)
    db.session.commit()

    _safe_notify(
        user_id,
        'system',
        f'预约成功：{room.name} {seat.seat_number}，'
        f'{start_time.strftime("%Y-%m-%d %H:%M")} ~ {end_time.strftime("%H:%M")}',
        related_entity_type='reservation',
        related_entity_id=reservation.id,
    )
    return _reservation_to_dict(reservation)


def create_reservation_on_behalf(admin_id: int, target_username: str, seat_id: int,
                                 start_time: datetime, end_time: datetime) -> dict:
    """管理员代理预约（为学生预约）。校验规则同 create_reservation。"""
    user = User.query.filter_by(username=target_username, is_active=True).first()
    if not user:
        raise NotFoundError('目标用户不存在')
    return create_reservation(user.id, seat_id, start_time, end_time)


def cancel_reservation(reservation_id: int, cancelled_by: str,
                       reason: str = None, acting_user_id: int = None) -> None:
    """取消预约。

    约束：
      - 只有状态为 'reserved'（未签到）的预约可被 user/admin 取消；
      - admin 取消（违约判定）不受此限制；
      - 学生只能取消自己的预约。
    """
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        raise NotFoundError('预约不存在')

    if cancelled_by == 'user' and acting_user_id is not None:
        if reservation.user_id != acting_user_id:
            raise AuthorizationError('无权取消他人的预约')

    if cancelled_by != 'admin' and reservation.status != 'reserved':
        raise ConflictError('当前状态的预约不可取消')

    reservation.status = 'cancelled'
    reservation.cancelled_by = cancelled_by
    reservation.cancel_reason = reason
    db.session.commit()

    seat = reservation.seat
    room = seat.study_room if seat else None
    _safe_notify(
        reservation.user_id,
        'cancel',
        f'您的预约已取消：{room.name if room else ""} {seat.seat_number if seat else ""}'
        f'{("，原因：" + reason) if reason else ""}',
        related_entity_type='reservation',
        related_entity_id=reservation.id,
    )


def get_reservation(reservation_id: int) -> Optional[dict]:
    """获取预约详情，含用户信息、座位信息、自习室信息。"""
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return None
    return _reservation_detail_dict(reservation)


def complete_reservation(reservation_id: int) -> None:
    """将已签到的预约标记为 completed。"""
    reservation = db.session.get(Reservation, reservation_id)
    if reservation and reservation.status == 'checked_in':
        reservation.status = 'completed'
        db.session.commit()


# ============================================================================
# 查询接口
# ============================================================================

def list_user_reservations(user_id: int, status: str = None,
                           page: int = 1, per_page: int = 20) -> dict:
    """查询指定用户的预约记录（分页）。"""
    query = Reservation.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Reservation.start_time.desc())
    return _paginate(query, page, per_page, _reservation_to_dict)


def list_all_reservations(filters: dict = None, page: int = 1, per_page: int = 20) -> dict:
    """全局预约记录查询（管理端）。支持按用户、自习室、座位、状态、日期范围、关键词筛选。"""
    filters = filters or {}
    query = Reservation.query

    if filters.get('user_id'):
        query = query.filter(Reservation.user_id == filters['user_id'])
    if filters.get('seat_id'):
        query = query.filter(Reservation.seat_id == filters['seat_id'])
    if filters.get('status'):
        query = query.filter(Reservation.status == filters['status'])
    if filters.get('room_id'):
        query = query.join(Seat, Reservation.seat_id == Seat.id).filter(Seat.room_id == filters['room_id'])
    if filters.get('start_date'):
        query = query.filter(Reservation.start_time >= filters['start_date'])
    if filters.get('end_date'):
        end = filters['end_date']
        if isinstance(end, date) and not isinstance(end, datetime):
            end = datetime.combine(end, time(23, 59, 59))
        query = query.filter(Reservation.start_time <= end)
    if filters.get('keyword'):
        kw = f"%{filters['keyword']}%"
        query = query.join(User, Reservation.user_id == User.id).filter(
            db.or_(User.username.like(kw), User.name.like(kw))
        )

    query = query.order_by(Reservation.start_time.desc())
    return _paginate(query, page, per_page, _reservation_detail_dict)


def get_user_active_reservations(user_id: int) -> List[dict]:
    """获取用户所有进行中的预约（状态为 reserved 或 checked_in）。"""
    reservations = Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status.in_(('reserved', 'checked_in')),
    ).order_by(Reservation.start_time.asc()).all()
    return [_reservation_to_dict(r) for r in reservations]


def get_user_active_reservation_count(user_id: int) -> int:
    """获取用户当前进行中的预约数量。"""
    return Reservation.query.filter(
        Reservation.user_id == user_id,
        Reservation.status.in_(('reserved', 'checked_in')),
    ).count()


# ============================================================================
# 签到
# ============================================================================

def _validate_sign_in_code(room_id: int, code: str, valid_date: date) -> bool:
    """校验签到码是否有效（room_id + valid_date 唯一，且未过期）。"""
    record = SignInCode.query.filter_by(room_id=room_id, valid_date=valid_date).first()
    if not record:
        return False
    if record.code != code:
        return False
    if record.expires_at and record.expires_at < _now():
        return False
    return True


def check_in(reservation_id: int, code: str, acting_user_id: int = None) -> datetime:
    """预约签到。

    校验：
      1. 预约状态为 reserved；
      2. 当前时间在合理范围内（开始前 remind_before ~ 开始后 no_show_threshold）；
      3. 签到码有效。
    返回实际签到时间，并更新状态为 checked_in。
    """
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        raise NotFoundError('预约不存在')

    if acting_user_id is not None and reservation.user_id != acting_user_id:
        raise AuthorizationError('无权操作他人的预约')

    if reservation.status != 'reserved':
        raise ConflictError('当前状态的预约不可签到')

    now = _now()
    remind_before = system_service.get_config_as_int('remind_before_minutes', 15)
    no_show = system_service.get_config_as_int('no_show_threshold_minutes', 15)
    earliest = reservation.start_time - timedelta(minutes=remind_before)
    latest = reservation.start_time + timedelta(minutes=no_show)
    if now < earliest:
        raise ConflictError('签到尚未开放，请在预约开始前后签到')
    if now > latest:
        raise ConflictError('已超过签到时限')

    seat = reservation.seat
    room_id = seat.room_id if seat else None
    if room_id is None or not _validate_sign_in_code(room_id, code, reservation.start_time.date()):
        raise ValidationError('签到码无效')

    reservation.check_in_time = now
    reservation.status = 'checked_in'
    db.session.commit()
    return now


# ============================================================================
# 违约管理
# ============================================================================

def record_violation(reservation_id: int, reason: str = '超时未签到') -> dict:
    """为指定预约生成违约记录。约束：一个预约只能对应一条违约记录。"""
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        raise NotFoundError('预约不存在')

    existing = ViolationRecord.query.filter_by(reservation_id=reservation_id).first()
    if existing:
        raise ConflictError('该预约已存在违约记录')

    violation = ViolationRecord(
        user_id=reservation.user_id,
        reservation_id=reservation_id,
        violation_time=_now(),
        reason=reason,
    )
    reservation.status = 'violation'
    db.session.add(violation)
    db.session.commit()

    seat = reservation.seat
    room = seat.study_room if seat else None
    _safe_notify(
        reservation.user_id,
        'violation',
        f'违约记录：{room.name if room else ""} {seat.seat_number if seat else ""}，原因：{reason}',
        related_entity_type='reservation',
        related_entity_id=reservation_id,
    )
    return _violation_to_dict(violation)


def list_user_violations(user_id: int, page: int = 1, per_page: int = 20) -> dict:
    """查询指定学生的违约记录。"""
    query = ViolationRecord.query.filter_by(user_id=user_id).order_by(
        ViolationRecord.violation_time.desc()
    )
    return _paginate(query, page, per_page, _violation_to_dict)


def list_all_violations(filters: dict = None, page: int = 1, per_page: int = 20) -> dict:
    """全局违约记录查询（管理端）。"""
    filters = filters or {}
    query = ViolationRecord.query

    if filters.get('user_id'):
        query = query.filter(ViolationRecord.user_id == filters['user_id'])
    if filters.get('start_date'):
        query = query.filter(ViolationRecord.violation_time >= filters['start_date'])
    if filters.get('end_date'):
        end = filters['end_date']
        if isinstance(end, date) and not isinstance(end, datetime):
            end = datetime.combine(end, time(23, 59, 59))
        query = query.filter(ViolationRecord.violation_time <= end)
    if filters.get('keyword'):
        kw = f"%{filters['keyword']}%"
        query = query.join(User, ViolationRecord.user_id == User.id).filter(
            db.or_(User.username.like(kw), User.name.like(kw))
        )

    query = query.order_by(ViolationRecord.violation_time.desc())
    return _paginate(query, page, per_page, _violation_detail_dict)


def export_violations(filters: dict = None, format: str = 'csv') -> bytes:
    """导出违约记录为 CSV 格式，返回二进制内容。"""
    data = list_all_violations(filters, page=1, per_page=100000)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['违约ID', '学号', '姓名', '自习室', '座位', '违约时间', '原因'])
    for item in data['items']:
        user = item.get('user') or {}
        reservation = item.get('reservation') or {}
        writer.writerow([
            item.get('id'),
            user.get('username'),
            user.get('name'),
            reservation.get('room_name'),
            reservation.get('seat_number'),
            item.get('violation_time'),
            item.get('reason'),
        ])
    return buffer.getvalue().encode('utf-8-sig')


# ============================================================================
# 座位可用性计算（供学生端座位查询/搜索使用）
# ============================================================================

def _booked_hours(seat_id: int, query_date: date) -> set:
    """返回某座位在指定日期已被占用的整点小时集合。"""
    day_start = datetime.combine(query_date, time.min)
    day_end = datetime.combine(query_date, time.max)
    reservations = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status.in_(ACTIVE_STATUSES),
        Reservation.start_time < day_end,
        Reservation.end_time > day_start,
    ).all()

    booked = set()
    for r in reservations:
        start_h = r.start_time.hour
        end_h = r.end_time.hour
        if r.end_time.minute or r.end_time.second:
            end_h += 1
        for h in range(start_h, end_h):
            booked.add(h)
    return booked


def _room_hour_range(room: StudyRoom) -> range:
    open_h = room.open_time.hour
    close_h = room.close_time.hour
    if room.close_time.minute or room.close_time.second:
        close_h += 1
    return range(open_h, close_h)


def _merge_slots(free_hours: List[int]) -> List[str]:
    """将连续的空闲小时合并为 'HH:00-HH:00' 时间段字符串列表。"""
    if not free_hours:
        return []
    free_hours = sorted(free_hours)
    slots = []
    seg_start = prev = free_hours[0]
    for h in free_hours[1:]:
        if h == prev + 1:
            prev = h
        else:
            slots.append(f'{seg_start:02d}:00-{prev + 1:02d}:00')
            seg_start = prev = h
    slots.append(f'{seg_start:02d}:00-{prev + 1:02d}:00')
    return slots


def get_seat_availability(seat_id: int, query_date: date) -> List[str]:
    """计算指定座位在某一天的可用时间段列表。"""
    seat = db.session.get(Seat, seat_id)
    if not seat or seat.study_room is None:
        return []
    if seat.status != 'available':
        return []

    today = _now().date()
    if query_date < today:
        return []

    booked = _booked_hours(seat_id, query_date)
    free = [h for h in _room_hour_range(seat.study_room) if h not in booked]

    # 仅保留未来时段：今天只展示当前时间之后可预约的整点小时
    if query_date == today:
        now = _now()
        earliest_hour = now.hour + (1 if (now.minute or now.second or now.microsecond) else 0)
        free = [h for h in free if h >= earliest_hour]

    return _merge_slots(free)


def get_room_seats(room_id: int, query_date: date = None) -> Optional[dict]:
    """查询指定自习室的座位及当天可用时间段（学生端座位选择页）。"""
    room = db.session.get(StudyRoom, room_id)
    if not room:
        return None
    query_date = query_date or _now().date()
    seats = Seat.query.filter_by(room_id=room_id).filter(
        Seat.status != 'retired'
    ).order_by(Seat.seat_number.asc()).all()
    return {
        'room': {'id': room.id, 'name': room.name},
        'seats': [{
            'id': s.id,
            'seat_number': s.seat_number,
            'has_window': s.has_window,
            'has_plug': s.has_plug,
            'status': s.status,
            'available_slots': get_seat_availability(s.id, query_date) if s.status == 'available' else [],
        } for s in seats],
    }


def get_available_seat_count(room_id: int, query_date: date) -> int:
    """获取某自习室在某天的可用座位数量（至少有一个完整小时段可用的座位数）。"""
    seats = Seat.query.filter_by(room_id=room_id, status='available').all()
    count = 0
    for s in seats:
        if get_seat_availability(s.id, query_date):
            count += 1
    return count


def list_rooms_for_student(room_type: str = None, query_date: date = None) -> dict:
    """学生端可用自习室列表（仅 is_active，附带可用座位数）。"""
    query_date = query_date or _now().date()
    query = StudyRoom.query.filter_by(is_active=True)
    if room_type:
        query = query.filter_by(room_type=room_type)
    rooms = query.order_by(StudyRoom.name.asc()).all()
    return {
        'items': [{
            'id': r.id,
            'name': r.name,
            'location': r.location,
            'room_type': r.room_type,
            'open_time': str(r.open_time),
            'close_time': str(r.close_time),
            'available_seats': get_available_seat_count(r.id, query_date),
        } for r in rooms]
    }


def search_seats(query_date: date, start_time: time = None, end_time: time = None,
                 has_window: bool = None, has_plug: bool = None, room_type: str = None,
                 department: str = None, page: int = 1, per_page: int = 20) -> dict:
    """按条件搜索座位，返回座位基本信息、所属自习室、可用时间段。"""
    query = Seat.query.join(StudyRoom, Seat.room_id == StudyRoom.id).filter(
        Seat.status == 'available',
        StudyRoom.is_active.is_(True),
    )
    if has_window is not None:
        query = query.filter(Seat.has_window.is_(has_window))
    if has_plug is not None:
        query = query.filter(Seat.has_plug.is_(has_plug))
    if room_type:
        query = query.filter(StudyRoom.room_type == room_type)
    if department:
        query = query.filter(StudyRoom.department == department)

    seats = query.order_by(StudyRoom.name.asc(), Seat.seat_number.asc()).all()

    results = []
    for s in seats:
        slots = get_seat_availability(s.id, query_date)
        if not slots:
            continue
        if start_time is not None and end_time is not None:
            if not _slots_cover_window(slots, start_time, end_time):
                continue
        results.append({
            'id': s.id,
            'seat_number': s.seat_number,
            'room_id': s.room_id,
            'room_name': s.study_room.name,
            'has_window': s.has_window,
            'has_plug': s.has_plug,
            'status': s.status,
            'available_slots': slots,
        })

    total = len(results)
    start_idx = (page - 1) * per_page
    items = results[start_idx:start_idx + per_page]
    pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
    }


def _slots_cover_window(slots: List[str], start_time: time, end_time: time) -> bool:
    """判断可用时段是否完整覆盖 [start_time, end_time) 的每个整点小时。"""
    needed = set(range(start_time.hour, end_time.hour + (1 if (end_time.minute or end_time.second) else 0)))
    free = set()
    for slot in slots:
        s, e = slot.split('-')
        free.update(range(int(s[:2]), int(e[:2])))
    return needed.issubset(free)


# ============================================================================
# 定时任务触发接口（由 reservation/scheduler.py 调用）
# ============================================================================

def process_pre_reservation_reminders() -> List[int]:
    """扫描即将开始的预约，发送预约前提醒通知，返回被处理的预约 id 列表。"""
    minutes = system_service.get_config_as_int('remind_before_minutes', 15)
    now = _now()
    window_end = now + timedelta(minutes=minutes)
    reservations = Reservation.query.filter(
        Reservation.status == 'reserved',
        Reservation.start_time > now,
        Reservation.start_time <= window_end,
    ).all()

    processed = []
    for r in reservations:
        seat = r.seat
        room = seat.study_room if seat else None
        _safe_notify(
            r.user_id, 'remind',
            f'预约提醒：{room.name if room else ""} {seat.seat_number if seat else ""} '
            f'将于 {r.start_time.strftime("%H:%M")} 开始，请按时签到',
            related_entity_type='reservation', related_entity_id=r.id,
        )
        processed.append(r.id)
    return processed


def process_check_in_alerts() -> List[int]:
    """扫描已开始但未签到的预约，发送签到提醒通知，返回被处理的预约 id 列表。"""
    minutes = system_service.get_config_as_int('check_in_alert_minutes', 10)
    now = _now()
    reservations = Reservation.query.filter(
        Reservation.status == 'reserved',
        Reservation.start_time <= now,
        Reservation.start_time >= now - timedelta(minutes=minutes),
    ).all()

    processed = []
    for r in reservations:
        _safe_notify(
            r.user_id, 'check_in_alert',
            '签到提醒：您的预约已开始，请尽快签到，否则将记为违约',
            related_entity_type='reservation', related_entity_id=r.id,
        )
        processed.append(r.id)
    return processed


def process_no_show_violations() -> List[int]:
    """扫描超时未签到的预约，自动取消并记录违约，返回被处理的违约预约 id 列表。"""
    threshold = system_service.get_config_as_int('no_show_threshold_minutes', 15)
    now = _now()
    reservations = Reservation.query.filter(
        Reservation.status == 'reserved',
        Reservation.start_time < now - timedelta(minutes=threshold),
    ).all()

    processed = []
    for r in reservations:
        record_violation(r.id, reason='超时未签到')
        processed.append(r.id)
    return processed


def complete_expired_reservations() -> List[int]:
    """将已过结束时间且状态为 checked_in 的预约标记为 completed，返回被处理的预约 id 列表。"""
    now = _now()
    reservations = Reservation.query.filter(
        Reservation.status == 'checked_in',
        Reservation.end_time < now,
    ).all()

    processed = []
    for r in reservations:
        r.status = 'completed'
        processed.append(r.id)
    if processed:
        db.session.commit()
    return processed


# ============================================================================
# 跨模块辅助（供 room 模块注销资源时调用）
# ============================================================================

def cancel_future_reservations_by_room(room_id: int) -> int:
    """取消指定自习室下所有座位的未来预约，返回被取消的预约数量。"""
    now = _now()
    reservations = Reservation.query.join(Seat, Reservation.seat_id == Seat.id).filter(
        Seat.room_id == room_id,
        Reservation.status == 'reserved',
        Reservation.start_time > now,
    ).all()
    count = 0
    for r in reservations:
        r.status = 'cancelled'
        r.cancelled_by = 'system'
        r.cancel_reason = '自习室已注销'
        count += 1
    if count:
        db.session.commit()
    return count


def cancel_future_reservations_by_seat(seat_id: int) -> int:
    """取消指定座位的所有未来预约，返回被取消的预约数量。"""
    now = _now()
    reservations = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.status == 'reserved',
        Reservation.start_time > now,
    ).all()
    count = 0
    for r in reservations:
        r.status = 'cancelled'
        r.cancelled_by = 'system'
        r.cancel_reason = '座位已注销'
        count += 1
    if count:
        db.session.commit()
    return count


# ============================================================================
# 统计（供仪表盘调用）
# ============================================================================

def get_reservation_stats(today: date = None) -> dict:
    """返回预约统计：今日预约数、今日违约数、活跃用户数等。"""
    today = today or _now().date()
    day_start = datetime.combine(today, time.min)
    day_end = datetime.combine(today, time.max)

    today_reservations = Reservation.query.filter(
        Reservation.start_time >= day_start,
        Reservation.start_time <= day_end,
    ).count()

    today_violations = ViolationRecord.query.filter(
        ViolationRecord.violation_time >= day_start,
        ViolationRecord.violation_time <= day_end,
    ).count()

    active_users = db.session.query(Reservation.user_id).filter(
        Reservation.status.in_(('reserved', 'checked_in')),
    ).distinct().count()

    return {
        'today_reservations': today_reservations,
        'today_violations': today_violations,
        'active_users': active_users,
    }


# ============================================================================
# 通知发送（容错包装：通知失败不应阻断主流程）
# ============================================================================

def _safe_notify(user_id: int, notification_type: str, content: str,
                 related_entity_type: str = None, related_entity_id: int = None) -> None:
    """发送通知，失败不阻断主流程。主事务已提交时不执行 rollback。"""
    try:
        notification_service.send_notification(
            user_id, notification_type, content,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
    except Exception:
        # 通知失败仅静默忽略，不阻断预约取消主流程
        # 此处不调用 db.session.rollback()，因为主事务可能已提交
        pass
