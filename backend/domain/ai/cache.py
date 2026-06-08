"""
AI模块 - 简单缓存工具

实现基于内存的LRU缓存
生产环境建议使用Redis
"""
from typing import Any, Optional
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json
import threading


class SimpleCache:
    """
    简单的LRU缓存

    特性:
    - 自动过期
    - LRU淘汰策略
    - 线程安全
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认TTL（秒）
        """
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key not in self._cache:
                return None

            value, expire_at = self._cache[key]

            # 检查是否过期
            if datetime.now() > expire_at:
                del self._cache[key]
                return None

            # LRU: 移到末尾
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存值"""
        with self._lock:
            if ttl is None:
                ttl = self._default_ttl

            expire_at = datetime.now() + timedelta(seconds=ttl)

            # 如果已存在，先删除（为了更新顺序）
            if key in self._cache:
                del self._cache[key]

            # 添加新条目
            self._cache[key] = (value, expire_at)

            # LRU淘汰
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)  # 删除最旧的

    def delete(self, key: str):
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self):
        """清理过期条目"""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, (_, expire_at) in self._cache.items()
                if now > expire_at
            ]
            for key in expired_keys:
                del self._cache[key]


# 全局缓存实例
_intent_cache = SimpleCache(max_size=500, default_ttl=300)  # 5分钟TTL


def make_cache_key(message: str, user_id: Optional[int] = None) -> str:
    """
    生成缓存键

    使用消息内容的hash作为key
    """
    content = f"{message.lower().strip()}"
    if user_id:
        content += f":{user_id}"

    return hashlib.md5(content.encode()).hexdigest()


def get_cached_intent(message: str, user_id: Optional[int] = None) -> Optional[dict]:
    """
    获取缓存的意图识别结果

    Args:
        message: 用户消息
        user_id: 用户ID（可选）

    Returns:
        dict: 缓存的意图结果，或None
    """
    key = make_cache_key(message, user_id)
    return _intent_cache.get(key)


def cache_intent_result(message: str, result: dict, user_id: Optional[int] = None, ttl: int = 300):
    """
    缓存意图识别结果

    Args:
        message: 用户消息
        result: 意图识别结果
        user_id: 用户ID（可选）
        ttl: 缓存时间（秒）
    """
    key = make_cache_key(message, user_id)
    _intent_cache.set(key, result, ttl)


def clear_intent_cache():
    """清空意图缓存"""
    _intent_cache.clear()


def cleanup_intent_cache():
    """清理过期的意图缓存"""
    _intent_cache.cleanup_expired()
