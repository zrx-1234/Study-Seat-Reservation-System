"""
MOD-RESV: 预约与签到模块 - 服务接口
"""

from typing import Optional, List
from datetime import datetime, date

from domain.reservation.models import Reservation, ViolationRecord
from extensions import db

# ============================================================================
# 预约生命周期（待实现）
# ============================================================================

def create_reservation(user_id: int, seat_id: int, start_time: datetime, end_time: datetime):
    """提交座位预约"""
    # TODO: 实现冲突检测、时长校验等
    pass


def create_reservation_on_behalf(admin_id: int, target_username: str, seat_id: int,
                                  start_time: datetime, end_time: datetime):
    """管理员代理预约（为学生预约）"""
    # TODO: 实现
    pass


def cancel_reservation(reservation_id: int, cancelled_by: str, reason: str = None):
    """取消预约"""
    # TODO: 实现
    pass


def get_reservation(reservation_id: int):
    """获取预约详情"""
    # TODO: 实现
    pass


def complete_reservation(reservation_id: int):
    """将已签到的预约标记为completed"""
    # TODO: 实现
    pass


# ============================================================================
# 查询接口（待实现）
# ============================================================================

def list_user_reservations(user_id: int, status: str = None, page: int = 1, per_page: int = 20):
    """查询指定用户的预约记录（分页）"""
    # TODO: 实现
    pass


def list_all_reservations(filters: dict, page: int = 1, per_page: int = 20):
    """全局预约记录查询（管理端）"""
    # TODO: 实现
    pass


def get_user_active_reservations(user_id: int) -> List[dict]:
    """获取用户所有进行中的预约"""
    # TODO: 实现
    return []


# ============================================================================
# 签到（待实现）
# ============================================================================

def check_in(reservation_id: int, code: str) -> Optional[datetime]:
    """预约签到"""
    # TODO: 实现（需调用 room 模块验证签到码）
    pass


# ============================================================================
# 冲突检测与校验（待实现）
# ============================================================================

def check_time_conflict(seat_id: int, start_time: datetime, end_time: datetime,
                        exclude_reservation_id: int = None) -> bool:
    """检查指定座位在目标时间段是否存在冲突预约"""
    # TODO: 实现
    return False


def validate_reservation_duration(start_time: datetime, end_time: datetime) -> tuple:
    """校验预约时长是否符合系统配置的最大预约时长"""
    # TODO: 实现
    return (True, "")


# ============================================================================
# 违约管理（待实现）
# ============================================================================

def record_violation(reservation_id: int, reason: str = '超时未签到'):
    """为指定预约生成违约记录"""
    # TODO: 实现
    pass


def list_user_violations(user_id: int, page: int = 1, per_page: int = 20):
    """查询指定学生的违约记录"""
    # TODO: 实现
    pass


def list_all_violations(filters: dict, page: int = 1, per_page: int = 20):
    """全局违约记录查询（管理端）"""
    # TODO: 实现
    pass


def export_violations(filters: dict, format: str = 'csv') -> bytes:
    """导出违约记录为CSV或Excel格式"""
    # TODO: 实现
    pass


# ============================================================================
# 定时任务触发接口（待实现）
# ============================================================================

def process_pre_reservation_reminders() -> List[int]:
    """扫描即将开始的预约，发送预约前提醒通知"""
    # TODO: 实现
    return []


def process_check_in_alerts() -> List[int]:
    """扫描已开始但未签到的预约，发送签到提醒通知"""
    # TODO: 实现
    return []


def process_no_show_violations() -> List[int]:
    """扫描超时未签到的预约，自动取消并记录违约"""
    # TODO: 实现
    return []


def complete_expired_reservations() -> List[int]:
    """将已过结束时间且状态为checked_in的预约标记为completed"""
    # TODO: 实现
    return []


# ============================================================================
# 跨模块辅助（供 room 模块调用）（待实现）
# ============================================================================

def cancel_future_reservations_by_room(room_id: int) -> int:
    """取消指定自习室下所有座位的未来预约"""
    # TODO: 实现
    return 0


def cancel_future_reservations_by_seat(seat_id: int) -> int:
    """取消指定座位的所有未来预约"""
    # TODO: 实现
    return 0


# ============================================================================
# 统计（待实现）
# ============================================================================

def get_reservation_stats(today: date = None) -> dict:
    """返回预约统计"""
    # TODO: 实现
    return {'today_reservations': 0, 'today_violations': 0, 'active_users': 0}
