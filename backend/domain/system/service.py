"""
MOD-SYS: 系统配置模块 - 服务接口
"""

from typing import Optional, List

from domain.system.models import SystemConfig
from infrastructure.cache import get_config_cache, clear_config_cache
from extensions import db

# 预定义配置项白名单
VALID_CONFIG_KEYS = {
    'max_reservation_hours',
    'no_show_threshold_minutes',
    'remind_before_minutes',
    'check_in_alert_minutes',
    'sign_in_code_refresh_hours',
    'max_active_reservations'
}

# ============================================================================
# 系统配置服务
# ============================================================================

def get_config(key: str) -> Optional[str]:
    """读取指定配置项的值（字符串类型）"""
    cache = get_config_cache()
    if key in cache:
        return cache[key]

    config = SystemConfig.query.filter_by(config_key=key).first()
    if config:
        cache[key] = config.config_value
        return config.config_value
    return None


def get_config_as_int(key: str, default: int = 0) -> int:
    """读取指定配置项并转为整数"""
    value = get_config(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_all_configs() -> List[dict]:
    """返回全部系统配置列表（管理端配置页面调用）"""
    configs = SystemConfig.query.all()
    return [{'key': c.config_key, 'value': c.config_value, 'description': c.description} for c in configs]


def set_config(key: str, value: str, description: str = None):
    """更新指定配置项的值"""
    if key not in VALID_CONFIG_KEYS:
        raise ValueError(f'Invalid config key: {key}')

    config = SystemConfig.query.filter_by(config_key=key).first()
    if config:
        config.config_value = value
        if description:
            config.description = description
    else:
        config = SystemConfig(config_key=key, config_value=value, description=description)
        db.session.add(config)
    db.session.commit()

    # 清除缓存
    cache = get_config_cache()
    if key in cache:
        del cache[key]


def batch_set_configs(items: List[dict]):
    """批量更新配置项"""
    for item in items:
        key = item.get('key')
        value = item.get('value')
        description = item.get('description')
        if key and value:
            set_config(key, value, description)


def init_default_configs():
    """初始化默认配置（seed.py调用）"""
    defaults = [
        ('max_reservation_hours', '4', '单次最大预约时长（小时）'),
        ('no_show_threshold_minutes', '15', '超时未签到判定违约阈值（分钟）'),
        ('remind_before_minutes', '15', '预约开始前提醒时间（分钟）'),
        ('check_in_alert_minutes', '10', '预约开始后未签到再次提醒时间（分钟）'),
        ('sign_in_code_refresh_hours', '24', '动态签到码更新周期（小时）'),
        ('max_active_reservations', '2', '学生同时最大进行中的预约数')
    ]

    for key, value, desc in defaults:
        if not SystemConfig.query.filter_by(config_key=key).first():
            config = SystemConfig(config_key=key, config_value=value, description=desc)
            db.session.add(config)
    db.session.commit()
