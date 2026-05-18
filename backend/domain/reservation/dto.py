"""
MOD-RESV: 预约与签到模块 - DTO定义
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, date


@dataclass
class ReservationDTO:
    id: int
    user_id: int
    seat_id: int
    start_time: datetime
    end_time: datetime
    status: str
    check_in_time: Optional[datetime]
    created_at: datetime


@dataclass
class ReservationDetailDTO:
    id: int
    user: dict
    seat: dict
    room: dict
    start_time: datetime
    end_time: datetime
    status: str
    check_in_time: Optional[datetime]
    created_at: datetime


@dataclass
class ViolationRecordDTO:
    id: int
    user_id: int
    reservation_id: int
    violation_time: datetime
    reason: str
    seat_number: Optional[str]
    room_name: Optional[str]


@dataclass
class ViolationRecordDetailDTO:
    id: int
    user: dict
    reservation: dict
    violation_time: datetime
    reason: str


@dataclass
class ReservationFilterDTO:
    user_id: Optional[int] = None
    room_id: Optional[int] = None
    seat_id: Optional[int] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    keyword: Optional[str] = None


@dataclass
class ViolationFilterDTO:
    user_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    keyword: Optional[str] = None


@dataclass
class ReservationStatsDTO:
    today_reservations: int
    today_violations: int
    active_users: int
