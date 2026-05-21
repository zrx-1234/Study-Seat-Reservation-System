"""
MOD-SYS: 系统配置模块

对外暴露的 Service API：
    get_config(key) -> Optional[str]
    get_config_as_int(key, default=0) -> int
    get_all_configs() -> List[ConfigDTO]
    set_config(key, value, description=None) -> ConfigDTO
    batch_set_configs(items) -> List[ConfigDTO]
    init_default_configs()
"""

from domain.system.service import (
    get_config,
    get_config_as_int,
    get_all_configs,
    set_config,
    batch_set_configs,
    init_default_configs,
    VALID_CONFIG_KEYS,
)

__all__ = [
    'get_config',
    'get_config_as_int',
    'get_all_configs',
    'set_config',
    'batch_set_configs',
    'init_default_configs',
    'VALID_CONFIG_KEYS',
]
