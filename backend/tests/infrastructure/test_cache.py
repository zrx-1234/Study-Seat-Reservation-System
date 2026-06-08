"""
INF-CACHE 测试：缓存模块
覆盖通用缓存存取、TTL过期、删除清空、兼容接口
"""

import pytest
from infrastructure.cache import (
    cache_get,
    cache_set,
    cache_delete,
    cache_clear,
    cache_keys,
    get_config_cache,
    clear_config_cache,
    _cache_store,
)


# ============================================================================
# 1. 通用缓存基础操作测试
# ============================================================================

class TestCacheGetSet:
    """测试缓存存取"""

    def test_set_and_get(self):
        cache_set('name', 'Alice')
        assert cache_get('name') == 'Alice'

    def test_get_missing_returns_none(self):
        assert cache_get('non_existent') is None

    def test_get_missing_returns_default(self):
        assert cache_get('non_existent', 'default') == 'default'

    def test_overwrite_existing(self):
        cache_set('key', 'old')
        cache_set('key', 'new')
        assert cache_get('key') == 'new'

    def test_set_complex_value(self):
        cache_set('dict', {'a': 1})
        cache_set('list', [1, 2, 3])
        assert cache_get('dict') == {'a': 1}
        assert cache_get('list') == [1, 2, 3]


class TestCacheDelete:
    """测试缓存删除"""

    def test_delete_removes_key(self):
        cache_set('temp', 123)
        cache_delete('temp')
        assert cache_get('temp') is None

    def test_delete_missing_no_error(self):
        cache_delete('not_exists')  # 不应抛异常


class TestCacheClear:
    """测试缓存清空"""

    def test_clear_removes_all(self):
        cache_set('a', 1)
        cache_set('b', 2)
        cache_clear()
        assert cache_get('a') is None
        assert cache_get('b') is None

    def test_clear_leaves_config_cache_intact(self):
        get_config_cache()['cfg'] = 'value'
        cache_set('a', 1)
        cache_clear()
        assert get_config_cache()['cfg'] == 'value'


# ============================================================================
# 2. TTL 过期测试
# ============================================================================

class TestCacheTTL:
    """测试缓存TTL过期机制"""

    def test_ttl_no_expire(self):
        cache_set('key', 'value', ttl_seconds=3600)
        assert cache_get('key') == 'value'

    def test_ttl_expiration_returns_none(self):
        cache_set('key', 'value', ttl_seconds=60)
        # 手动将过期时间设为过去，验证过期逻辑
        _cache_store['key'] = (0, 'value')
        assert cache_get('key') is None

    def test_ttl_expiration_returns_default(self):
        cache_set('key', 'value', ttl_seconds=60)
        _cache_store['key'] = (0, 'value')
        assert cache_get('key', 'default') == 'default'

    def test_ttl_expiration_removes_key(self):
        cache_set('key', 'value', ttl_seconds=60)
        _cache_store['key'] = (0, 'value')
        cache_get('key')  # 触发过期清理
        assert cache_get('key') is None
        assert 'key' not in _cache_store

    def test_no_ttl_never_expires(self):
        cache_set('key', 'value')
        # None 表示永不过期
        _cache_store['key'] = (None, 'value')
        assert cache_get('key') == 'value'


# ============================================================================
# 3. cache_keys 测试
# ============================================================================

class TestCacheKeys:
    """测试缓存键列表"""

    def test_keys_returns_valid_keys(self):
        cache_set('a', 1, ttl_seconds=60)
        cache_set('b', 2)  # 无TTL
        keys = cache_keys()
        assert 'a' in keys
        assert 'b' in keys

    def test_keys_excludes_expired(self):
        cache_set('a', 1, ttl_seconds=60)
        cache_set('b', 2, ttl_seconds=60)
        _cache_store['a'] = (0, 1)
        _cache_store['b'] = (0, 2)
        keys = cache_keys()
        assert 'a' not in keys
        assert 'b' not in keys

    def test_keys_cleans_up_expired(self):
        cache_set('a', 1, ttl_seconds=60)
        _cache_store['a'] = (0, 1)
        cache_keys()
        # 过期键已被清理
        assert cache_get('a') is None
        assert 'a' not in _cache_store


# ============================================================================
# 4. 配置缓存兼容接口测试
# ============================================================================

class TestConfigCacheCompatibility:
    """测试旧版配置缓存接口"""

    def test_get_config_cache_returns_dict(self):
        cache = get_config_cache()
        assert isinstance(cache, dict)

    def test_config_cache_round_trip(self):
        get_config_cache()['max_hours'] = '4'
        assert get_config_cache()['max_hours'] == '4'

    def test_clear_config_cache(self):
        get_config_cache()['key'] = 'value'
        clear_config_cache()
        assert 'key' not in get_config_cache()

    def test_config_cache_isolated_from_generic_cache(self):
        get_config_cache()['key'] = 'config_value'
        cache_set('key', 'generic_value')
        assert get_config_cache()['key'] == 'config_value'
        assert cache_get('key') == 'generic_value'


# ============================================================================
# 5. 并发安全性说明（无测试，仅文档）
# ============================================================================
# 当前实现使用纯内存字典，非线程安全。
# 在单进程多线程环境（如 Gunicorn sync worker）下需要加锁。
# 后续如需线程安全，可引入 threading.RLock。
