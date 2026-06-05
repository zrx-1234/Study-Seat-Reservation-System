"""
API-STU: 学生端接口模块

职责：参数解析、JWT 鉴权、调用 Domain Service、序列化统一响应。
不包含业务逻辑，业务规则全部位于 domain 层。
"""

from datetime import datetime, date, time

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from infrastructure.exceptions import success_response, error_response, ValidationError
from infrastructure.auth import get_current_user_id
from domain.user import service as user_service
from domain.reservation import service as reservation_service
from domain.notification import service as notification_service

student_bp = Blueprint('student', __name__, url_prefix='/api/v1/student')


# ============================================================================
# 参数解析辅助
# ============================================================================

def _parse_date(value: str):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError('日期格式不正确，应为 YYYY-MM-DD')


def _parse_datetime(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise ValidationError('时间格式不正确，应为 ISO 8601，如 2025-04-14T09:00:00')


def _parse_time(value: str):
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        raise ValidationError('时间格式不正确，应为 HH:MM')


def _parse_bool(value: str):
    if value is None:
        return None
    return value.lower() in ('true', '1', 'yes')


# ============================================================================
# 2.1 认证相关
# ============================================================================

@student_bp.route('/auth/login', methods=['POST'])
def login():
    """学生登录"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error_response('用户名和密码不能为空', code=400)

    user_dict, token = user_service.authenticate(username, password)
    if not user_dict or user_dict.get('user_type') != 'student':
        return error_response('用户名或密码错误', code=401)

    return success_response(data={
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'user': user_dict
    })


@student_bp.route('/auth/register', methods=['POST'])
def register():
    """学生注册"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    department = data.get('department')
    email = data.get('email')

    user_dict, token = user_service.register_student(
        username=username,
        password=password,
        name=name,
        department=department,
        email=email,
    )
    return success_response(
        data={
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400,
            'user': user_dict,
        },
        message='注册成功',
    )


# ============================================================================
# 2.2 个人信息
# ============================================================================

@student_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """获取当前学生个人信息"""
    user_id = get_current_user_id()
    profile = user_service.get_user_profile(user_id)
    if not profile:
        return error_response('用户不存在', code=404)

    # 补充实时统计（用户模块的统计依赖预约数据，由本模块计算后回填）
    profile['active_reservations'] = reservation_service.get_user_active_reservation_count(user_id)
    profile['total_violations'] = reservation_service.list_user_violations(
        user_id, page=1, per_page=1
    )['total']
    return success_response(data=profile)


# ============================================================================
# 2.3 自习室与座位查询
# ============================================================================

@student_bp.route('/rooms', methods=['GET'])
@jwt_required()
def list_rooms():
    """查看可用自习室列表"""
    room_type = request.args.get('room_type')
    query_date = _parse_date(request.args.get('date'))
    result = reservation_service.list_rooms_for_student(room_type=room_type, query_date=query_date)
    return success_response(data=result)


@student_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
@jwt_required()
def list_seats(room_id):
    """查询指定自习室的座位及可用时间段"""
    query_date = _parse_date(request.args.get('date'))
    if not query_date:
        return error_response('date 参数必填', code=400)

    result = reservation_service.get_room_seats(room_id, query_date)
    if not result:
        return error_response('自习室不存在', code=404)
    return success_response(data=result)


@student_bp.route('/seats/search', methods=['GET'])
@jwt_required()
def search_seats():
    """按条件搜索座位"""
    query_date = _parse_date(request.args.get('date'))
    if not query_date:
        return error_response('date 参数必填', code=400)

    result = reservation_service.search_seats(
        query_date=query_date,
        start_time=_parse_time(request.args.get('start_time')),
        end_time=_parse_time(request.args.get('end_time')),
        has_window=_parse_bool(request.args.get('has_window')),
        has_plug=_parse_bool(request.args.get('has_plug')),
        room_type=request.args.get('room_type'),
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 20, type=int),
    )
    return success_response(data=result)


# ============================================================================
# 2.4 预约管理
# ============================================================================

@student_bp.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """提交座位预约"""
    user_id = get_current_user_id()
    data = request.get_json() or {}

    seat_id = data.get('seat_id')
    start_time = _parse_datetime(data.get('start_time'))
    end_time = _parse_datetime(data.get('end_time'))
    if not seat_id or not start_time or not end_time:
        return error_response('seat_id、start_time、end_time 均为必填', code=400)

    result = reservation_service.create_reservation(user_id, seat_id, start_time, end_time)
    return success_response(data=result)


@student_bp.route('/reservations', methods=['GET'])
@jwt_required()
def list_reservations():
    """我的预约记录"""
    user_id = get_current_user_id()
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = reservation_service.list_user_reservations(user_id, status=status, page=page, per_page=per_page)
    return success_response(data=result)


@student_bp.route('/reservations/<int:id>', methods=['GET'])
@jwt_required()
def get_reservation(id):
    """预约详情"""
    user_id = get_current_user_id()
    result = reservation_service.get_reservation(id)
    if not result:
        return error_response('预约不存在', code=404)
    if result['user'] and result['user']['id'] != user_id:
        return error_response('无权查看他人的预约', code=403)
    return success_response(data=result)


@student_bp.route('/reservations/<int:id>/cancel', methods=['POST'])
@jwt_required()
def cancel_reservation(id):
    """取消预约"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    reason = data.get('reason')
    reservation_service.cancel_reservation(id, cancelled_by='user', reason=reason, acting_user_id=user_id)
    return success_response(data=None, message='预约已取消')


# ============================================================================
# 2.5 签到
# ============================================================================

@student_bp.route('/reservations/<int:id>/check-in', methods=['POST'])
@jwt_required()
def check_in(id):
    """预约签到"""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    code = data.get('code')
    if not code:
        return error_response('签到码不能为空', code=400)

    check_in_time = reservation_service.check_in(id, code, acting_user_id=user_id)
    return success_response(
        data={'check_in_time': check_in_time.isoformat()},
        message='签到成功',
    )


# ============================================================================
# 2.6 通知与违约
# ============================================================================

@student_bp.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    """通知列表"""
    user_id = get_current_user_id()
    is_read = request.args.get('is_read')
    if is_read is not None:
        is_read = is_read.lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = notification_service.list_notifications(user_id, is_read=is_read, page=page, per_page=per_page)
    return success_response(data=result)


@student_bp.route('/notifications/<int:id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(id):
    """标记单条通知为已读"""
    user_id = get_current_user_id()
    notification_service.mark_as_read(id, user_id)
    return success_response(data=None)


@student_bp.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    """标记所有通知为已读"""
    user_id = get_current_user_id()
    count = notification_service.mark_all_as_read(user_id)
    return success_response(data={'updated': count})


@student_bp.route('/violations', methods=['GET'])
@jwt_required()
def list_violations():
    """我的违约记录"""
    user_id = get_current_user_id()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result = reservation_service.list_user_violations(user_id, page=page, per_page=per_page)
    return success_response(data=result)
