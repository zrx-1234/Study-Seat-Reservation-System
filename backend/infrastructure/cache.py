"""
INF-CACHE: 缓存模块（预留）
提供进程内缓存或Redis封装
"""

from functools import lru_cache

# 暂时使用简单的内存缓存
_config_cache = {}

def get_config_cache():
    """获取配置缓存"""
    return _config_cache

def clear_config_cache():
    """清空配置缓存"""
    global _config_cache
    _config_cache = {}
