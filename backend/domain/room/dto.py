"""
MOD-ROOM: 自习室与座位模块 - DTO定义
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import time, date


@dataclass
class RoomDTO:
    id: int
    name: str
    location: Optional[str]
    capacity: int
    room_type: str
    open_time: str
    close_time: str
    available_seats: Optional[int] = None


@dataclass
class RoomDetailDTO:
    id: int
    name: str
    location: Optional[str]
    capacity: int
    room_type: str
    department: Optional[str]
    open_time: str
    close_time: str
    is_active: bool
    seat_count: int


@dataclass
class RoomCreateDTO:
    name: str
    location: Optional[str]
    capacity: int
    room_type: str
    department: Optional[str] = None
    open_time: str = '07:00:00'
    close_time: str = '22:00:00'


@dataclass
class RoomUpdateDTO:
    name: Optional[str] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    room_type: Optional[str] = None
    department: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None


@dataclass
class SeatDTO:
    id: int
    room_id: int
    seat_number: str
    has_window: bool
    has_plug: bool
    status: str


@dataclass
class SeatCreateDTO:
    seat_number: str
    has_window: bool = False
    has_plug: bool = False


@dataclass
class SeatUpdateDTO:
    seat_number: Optional[str] = None
    has_window: Optional[bool] = None
    has_plug: Optional[bool] = None
    status: Optional[str] = None


@dataclass
class TimeSlotDTO:
    start_time: str
    end_time: str
    available: bool


@dataclass
class SeatSearchResultDTO:
    id: int
    seat_number: str
    has_window: bool
    has_plug: bool
    room_id: int
    room_name: str
    available_slots: List[TimeSlotDTO]


@dataclass
class SignInCodeDTO:
    id: int
    room_id: int
    code: str
    valid_date: date
    expires_at: str


@dataclass
class RoomStatsDTO:
    total_rooms: int
    total_seats: int
    active_rooms: int
