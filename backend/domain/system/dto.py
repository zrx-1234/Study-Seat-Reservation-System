"""
MOD-SYS: 系统配置模块 - DTO定义
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ConfigDTO:
    key: str
    value: str
    description: str


@dataclass
class ConfigUpdateDTO:
    key: str
    value: str
    description: str
