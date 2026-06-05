"""
AI模块 - 请求限流工具

实现简单的内存限流器，防止API滥用
生产环境建议使用Redis实现分布式限流
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class RateLimiter:
    """
    简单的内存限流器

    实现滑动窗口算法
    """

    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, limit: int = 30, window_seconds: int = 60) -> bool:
        """
        检查是否允许请求

        Args:
            key: 限流键（通常是user_id）
            limit: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒）

        Returns:
            bool: True表示允许，False表示超限
        """
        with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)

            # 获取该key的请求记录
            requests = self._requests[key]

            # 清理过期的请求记录
            requests[:] = [ts for ts in requests if ts > window_start]

            # 检查是否超限
            if len(requests) >= limit:
                return False

            # 记录本次请求
            requests.append(now)
            return True

    def get_remaining(self, key: str, limit: int = 30, window_seconds: int = 60) -> int:
        """
        获取剩余可用请求数

        Args:
            key: 限流键
            limit: 限制数
            window_seconds: 窗口大小

        Returns:
            int: 剩余请求数
        """
        with self._lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=window_seconds)

            requests = self._requests[key]
            requests[:] = [ts for ts in requests if ts > window_start]

            return max(0, limit - len(requests))

    def reset(self, key: str):
        """重置指定key的限流记录"""
        with self._lock:
            if key in self._requests:
                del self._requests[key]

    def cleanup_old_records(self, max_age_hours: int = 24):
        """
        清理旧记录，释放内存

        Args:
            max_age_hours: 清理多少小时前的记录
        """
        with self._lock:
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            keys_to_remove = []

            for key, requests in self._requests.items():
                requests[:] = [ts for ts in requests if ts > cutoff]
                if not requests:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._requests[key]


# 全局限流器实例
_rate_limiter = RateLimiter()


def check_rate_limit(user_id: int, limit: int = 30, window: int = 60) -> tuple[bool, int]:
    """
    检查用户是否超过请求限制

    Args:
        user_id: 用户ID
        limit: 限制数（默认30次）
        window: 时间窗口（默认60秒）

    Returns:
        tuple: (是否允许, 剩余次数)
    """
    key = f"ai_chat:{user_id}"
    allowed = _rate_limiter.is_allowed(key, limit, window)
    remaining = _rate_limiter.get_remaining(key, limit, window)
    return allowed, remaining


def reset_rate_limit(user_id: int):
    """重置用户的限流记录"""
    key = f"ai_chat:{user_id}"
    _rate_limiter.reset(key)


def cleanup_rate_limit_records():
    """清理旧的限流记录"""
    _rate_limiter.cleanup_old_records(max_age_hours=24)
