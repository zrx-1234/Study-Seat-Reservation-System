"""
MOD-ROOM: 自习室与座位模块 - 服务接口
"""

from typing import Optional, List
from datetime import date, time

from domain.room.models import StudyRoom, Seat, SignInCode
from extensions import db

# ============================================================================
# 自习室管理（待实现）
# ============================================================================

def create_room(data: dict):
    """登记新自习室"""
    # TODO: 实现
    pass


def update_room(room_id: int, data: dict):
    """更新自习室"""
    # TODO: 实现
    pass


def delete_room(room_id: int):
    """注销自习室"""
    # TODO: 实现（需调用 reservation 模块取消未来预约）
    pass


def get_room(room_id: int):
    """获取自习室详情"""
    # TODO: 实现
    pass


def list_rooms(room_type: str = None, is_active: bool = None, keyword: str = None, page: int = 1, per_page: int = 20):
    """分页查询自习室列表"""
    query = StudyRoom.query
    if room_type:
        query = query.filter(StudyRoom.room_type == room_type)
    if is_active is not None:
        query = query.filter(StudyRoom.is_active == is_active)
    if keyword:
        query = query.filter(StudyRoom.name.contains(keyword) | StudyRoom.location.contains(keyword))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [{'id': r.id, 'name': r.name, 'location': r.location, 'room_type': r.room_type,
                   'open_time': str(r.open_time), 'close_time': str(r.close_time), 'available_seats': 0}
                  for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages
    }


# ============================================================================
# 座位管理（待实现）
# ============================================================================

def create_seats(room_id: int, seats_data: List[dict]):
    """批量登记座位"""
    # TODO: 实现
    pass


def update_seat(seat_id: int, data: dict):
    """更新座位"""
    # TODO: 实现
    pass


def delete_seat(seat_id: int):
    """注销座位"""
    # TODO: 实现（需调用 reservation 模块取消未来预约）
    pass


def list_seats(room_id: int, status: str = None, page: int = 1, per_page: int = 20):
    """分页查询某自习室的座位列表"""
    # TODO: 实现
    pass


def get_seat(seat_id: int):
    """获取单个座位详情"""
    # TODO: 实现
    pass


# ============================================================================
# 座位可用性计算（待实现）
# ============================================================================

def get_seat_availability(seat_id: int, query_date: date) -> List[dict]:
    """计算指定座位在某一天的可用时间段列表"""
    # TODO: 实现
    pass


def search_seats(query_date: date, start_time: time = None, end_time: time = None,
                 has_window: bool = None, has_plug: bool = None, room_type: str = None,
                 department: str = None, page: int = 1, per_page: int = 20):
    """按条件搜索座位"""
    # TODO: 实现
    pass


def get_available_seat_count(room_id: int, query_date: date) -> int:
    """获取某自习室在某天的可用座位数量"""
    # TODO: 实现
    return 0


# ============================================================================
# 动态签到码管理（待实现）
# ============================================================================

def generate_sign_in_code(room_id: int, valid_date: date):
    """为指定自习室生成指定日期的动态签到码"""
    # TODO: 实现
    pass


def validate_sign_in_code(room_id: int, code: str, valid_date: date) -> bool:
    """验证签到码是否有效"""
    # TODO: 实现
    return False


def get_sign_in_code(room_id: int, valid_date: date) -> Optional[str]:
    """获取指定教室指定日期的当前有效签到码"""
    # TODO: 实现
    pass


# ============================================================================
# 统计（待实现）
# ============================================================================

def get_room_stats() -> dict:
    """返回自习室与座位的全局统计"""
    # TODO: 实现
    return {'total_rooms': 0, 'total_seats': 0}


def get_room_seats(room_id: int, query_date: date = None):
    """查询指定自习室的座位及可用时间段"""
    room = StudyRoom.query.get(room_id)
    if not room:
        return None

    seats = Seat.query.filter_by(room_id=room_id, status='available').all()
    return {
        'room': {'id': room.id, 'name': room.name},
        'seats': [{'id': s.id, 'seat_number': s.seat_number, 'has_window': s.has_window,
                   'has_plug': s.has_plug, 'status': s.status, 'available_slots': []}
                  for s in seats]
    }
