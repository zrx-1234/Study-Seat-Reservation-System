"""
MOD-SYS: 系统配置模块 - 服务接口

系统全局参数的配置与读取。采用键值对存储，支持运行时热更新。
"""

from typing import Optional, List

from domain.system.models import SystemConfig
from domain.system.dto import ConfigDTO, ConfigUpdateDTO
from infrastructure.cache import get_config_cache, clear_config_cache
from infrastructure.exceptions import ValidationError
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
    """
    读取指定配置项的值（字符串类型）。
    优先读取进程内缓存，缓存未命中时查库并回填缓存。
    :param key: 配置项键名
    :return: 配置值，若不存在则返回 None
    """
    cache = get_config_cache()
    if key in cache:
        return cache[key]

    config = SystemConfig.query.filter_by(config_key=key).first()
    if config:
        cache[key] = config.config_value
        return config.config_value
    return None


def get_config_as_int(key: str, default: int = 0) -> int:
    """
    读取指定配置项并转为整数。
    被预约模块、定时任务频繁调用，内部带缓存避免频繁查库。
    :param key: 配置项键名
    :param default: 配置不存在或转换失败时的默认值
    :return: 整数值
    """
    value = get_config(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_all_configs() -> List[ConfigDTO]:
    """
    返回全部系统配置列表（管理端配置页面调用）。
    :return: ConfigDTO 列表
    """
    configs = SystemConfig.query.order_by(SystemConfig.config_key).all()
    return [
        ConfigDTO(
            key=c.config_key,
            value=c.config_value,
            description=c.description or ''
        )
        for c in configs
    ]


def set_config(key: str, value: str, description: str = None) -> ConfigDTO:
    """
    更新指定配置项的值。
    :param key: 配置项键名，必须在预定义白名单中
    :param value: 配置值
    :param description: 可选描述
    :return: 更新后的 ConfigDTO
    :raises ValidationError: 当 key 不在白名单中时
    """
    if key not in VALID_CONFIG_KEYS:
        raise ValidationError(f'Invalid config key: {key}')

    config = SystemConfig.query.filter_by(config_key=key).first()
    if config:
        config.config_value = value
        if description is not None:
            config.description = description
    else:
        config = SystemConfig(
            config_key=key,
            config_value=value,
            description=description
        )
        db.session.add(config)
    db.session.commit()

    # 清除相关缓存，确保下次读取拿到最新值
    cache = get_config_cache()
    cache.pop(key, None)

    return ConfigDTO(
        key=config.config_key,
        value=config.config_value,
        description=config.description or ''
    )


def batch_set_configs(items: List[ConfigUpdateDTO]) -> List[ConfigDTO]:
    """
    批量更新配置项。任一配置项校验失败则全部回滚。
    :param items: 配置更新 DTO 列表
    :return: 更新后的 ConfigDTO 列表
    :raises ValidationError: 当任一 key 不在白名单中时
    """
    # 先统一校验，避免部分写入后失败
    keys = [item.key for item in items]
    invalid = [k for k in keys if k not in VALID_CONFIG_KEYS]
    if invalid:
        raise ValidationError(f'Invalid config keys: {invalid}')

    results = []
    try:
        for item in items:
            config = SystemConfig.query.filter_by(config_key=item.key).first()
            if config:
                config.config_value = item.value
                if item.description is not None:
                    config.description = item.description
            else:
                config = SystemConfig(
                    config_key=item.key,
                    config_value=item.value,
                    description=item.description
                )
                db.session.add(config)
            results.append(ConfigDTO(
                key=config.config_key,
                value=config.config_value,
                description=config.description or ''
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    # 全部成功后统一清缓存
    cache = get_config_cache()
    for item in items:
        cache.pop(item.key, None)

    return results


def init_default_configs():
    """
    初始化默认配置（seed.py 调用）。
    已存在的配置不会被覆盖。
    """
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
