"""
INF-CACHE: 缓存模块
提供进程内缓存，支持TTL过期
"""

import time
from typing import Optional, Any

# ============================================================================
# 配置专用缓存（兼容旧接口）
# ============================================================================

_config_cache = {}


def get_config_cache():
    """获取配置缓存字典（兼容旧接口）"""
    return _config_cache


def clear_config_cache():
    """清空配置缓存（兼容旧接口）"""
    _config_cache.clear()


# ============================================================================
# 通用缓存（支持TTL）
# ============================================================================

_cache_store = {}


def cache_get(key: str, default=None) -> Any:
    """
    从缓存获取值
    :param key: 缓存键
    :param default: 键不存在或已过期时的默认值
    """
    entry = _cache_store.get(key)
    if entry is None:
        return default
    expire_at, value = entry
    if expire_at is not None and time.time() > expire_at:
        cache_delete(key)
        return default
    return value


def cache_set(key: str, value: Any, ttl_seconds: Optional[int] = None):
    """
    设置缓存值
    :param key: 缓存键
    :param value: 缓存值
    :param ttl_seconds: 过期时间（秒），None表示永不过期
    """
    expire_at = time.time() + ttl_seconds if ttl_seconds is not None else None
    _cache_store[key] = (expire_at, value)


def cache_delete(key: str):
    """删除指定缓存键"""
    _cache_store.pop(key, None)


def cache_clear():
    """清空所有通用缓存"""
    _cache_store.clear()


def cache_keys():
    """返回当前所有有效的缓存键列表（不含已过期的）"""
    now = time.time()
    valid_keys = []
    expired_keys = []
    for key, (expire_at, _) in list(_cache_store.items()):
        if expire_at is not None and now > expire_at:
            expired_keys.append(key)
        else:
            valid_keys.append(key)
    for key in expired_keys:
        _cache_store.pop(key, None)
    return valid_keys
