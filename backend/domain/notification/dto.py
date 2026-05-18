"""
MOD-NOTIF: 通知模块 - DTO定义
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class NotificationDTO:
    id: int
    user_id: int
    type: str
    content: str
    is_read: bool
    created_at: datetime
