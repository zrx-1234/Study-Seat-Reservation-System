"""
MOD-ROOM: 自习室与座位模块

对外暴露的 Service API：
    create_room(data) -> RoomDTO
    update_room(room_id, data) -> RoomDTO
    delete_room(room_id) -> None
    get_room(room_id) -> Optional[RoomDetailDTO]
    list_rooms(...) -> PaginatedResult
    create_seats(room_id, seats_data) -> List[SeatDTO]
    update_seat(seat_id, data) -> SeatDTO
    delete_seat(seat_id) -> None
    list_seats(...) -> PaginatedResult
    get_seat(seat_id) -> Optional[SeatDTO]
    get_seat_availability(seat_id, query_date) -> List[TimeSlotDTO]
    search_seats(...) -> PaginatedResult
    get_available_seat_count(room_id, query_date) -> int
    generate_sign_in_code(room_id, valid_date) -> SignInCodeDTO
    validate_sign_in_code(room_id, code, valid_date) -> bool
    get_sign_in_code(room_id, valid_date) -> Optional[str]
    get_room_stats() -> RoomStatsDTO
    get_room_seats(room_id, query_date) -> dict
"""

from domain.room.service import (
    create_room,
    update_room,
    delete_room,
    get_room,
    list_rooms,
    create_seats,
    update_seat,
    delete_seat,
    list_seats,
    get_seat,
    get_seat_availability,
    search_seats,
    get_available_seat_count,
    generate_sign_in_code,
    validate_sign_in_code,
    get_sign_in_code,
    get_room_stats,
    get_room_seats,
)

__all__ = [
    'create_room',
    'update_room',
    'delete_room',
    'get_room',
    'list_rooms',
    'create_seats',
    'update_seat',
    'delete_seat',
    'list_seats',
    'get_seat',
    'get_seat_availability',
    'search_seats',
    'get_available_seat_count',
    'generate_sign_in_code',
    'validate_sign_in_code',
    'get_sign_in_code',
    'get_room_stats',
    'get_room_seats',
]
