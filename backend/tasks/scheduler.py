"""
定时任务调度器 - APScheduler 配置与任务注册

在应用工厂中调用 init_scheduler(app) 即可启动后台定时任务。
每个任务在执行时会自动推入 Flask 应用上下文，以便访问数据库。
"""

import atexit
import logging

logger = logging.getLogger(__name__)


def _with_app_context(app, func):
    """包装任务函数，使其在 Flask 应用上下文中执行。"""
    def wrapper():
        with app.app_context():
            try:
                func()
            except Exception:  # 防止单次任务异常导致调度线程崩溃
                logger.exception('定时任务执行失败: %s', getattr(func, '__name__', func))
    return wrapper


def init_scheduler(app):
    """初始化并启动定时任务调度器。

    任务清单（间隔可按需调整）：
      - 预约前提醒：每 1 分钟
      - 签到提醒：每 5 分钟
      - 违约判定：每 5 分钟
      - 完成过期预约：每 30 分钟
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    from domain.reservation import scheduler as resv_scheduler

    scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

    scheduler.add_job(
        _with_app_context(app, resv_scheduler.process_pre_reservation_reminders),
        'interval', minutes=1, id='pre_reservation_reminders', replace_existing=True,
    )
    scheduler.add_job(
        _with_app_context(app, resv_scheduler.process_check_in_alerts),
        'interval', minutes=5, id='check_in_alerts', replace_existing=True,
    )
    scheduler.add_job(
        _with_app_context(app, resv_scheduler.process_no_show_violations),
        'interval', minutes=5, id='no_show_violations', replace_existing=True,
    )
    scheduler.add_job(
        _with_app_context(app, resv_scheduler.complete_expired_reservations),
        'interval', minutes=30, id='complete_expired_reservations', replace_existing=True,
    )

    scheduler.start()
    app.extensions['scheduler'] = scheduler
    atexit.register(lambda: scheduler.shutdown(wait=False))
    logger.info('定时任务调度器已启动')
    return scheduler
