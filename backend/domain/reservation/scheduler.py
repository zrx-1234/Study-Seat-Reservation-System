"""
MOD-RESV: 预约与签到模块 - 定时任务逻辑
供外部调度器（APScheduler）调用。具体业务实现委托给 service 层，
本文件仅作为可被调度器引用的稳定入口。
"""

from domain.reservation import service as resv_service


def process_pre_reservation_reminders():
    """扫描即将开始的预约，发送预约前提醒通知，返回被处理的预约 id 列表。"""
    return resv_service.process_pre_reservation_reminders()


def process_check_in_alerts():
    """扫描已开始但未签到的预约，发送签到提醒通知，返回被处理的预约 id 列表。"""
    return resv_service.process_check_in_alerts()


def process_no_show_violations():
    """扫描超时未签到的预约，自动取消并记录违约，返回被处理的预约 id 列表。"""
    return resv_service.process_no_show_violations()


def complete_expired_reservations():
    """将已过结束时间且状态为 checked_in 的预约标记为 completed。"""
    return resv_service.complete_expired_reservations()
