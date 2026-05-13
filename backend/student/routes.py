from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from common.auth import authenticate_user, get_current_user
from common.utils import success_response, error_response

student_bp = Blueprint('student', __name__, url_prefix='/api/v1/student')


# ============================================================================
# 2.1 认证相关
# ============================================================================

@student_bp.route('/auth/login', methods=['POST'])
def login():
    """学生登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error_response('用户名和密码不能为空', code=400)

    user, token = authenticate_user(username, password)
    if not user or user.user_type != 'student':
        return error_response('用户名或密码错误', code=401)

    return success_response(data={
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'user': {
            'id': user.id,
            'username': user.username,
            'name': user.name,
            'user_type': user.user_type,
            'department': user.department
        }
    })


# ============================================================================
# 2.2 个人信息
# ============================================================================

@student_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """获取当前学生个人信息"""
    user = get_current_user()
    # TODO: 统计 active_reservations 和 total_violations
    return success_response(data={
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'department': user.department,
        'email': user.email,
        'active_reservations': 0,
        'total_violations': 0
    })


# ============================================================================
# 2.3 自习室与座位查询
# ============================================================================

@student_bp.route('/rooms', methods=['GET'])
@jwt_required()
def list_rooms():
    """查看可用自习室列表"""
    room_type = request.args.get('room_type')
    date = request.args.get('date')
    # TODO: 实现自习室列表查询
    return success_response(data={'items': []})


@student_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
@jwt_required()
def list_seats(room_id):
    """查询指定自习室的座位及可用时间段"""
    date = request.args.get('date')
    if not date:
        return error_response('date 参数必填', code=400)
    # TODO: 实现座位及可用时段查询
    return success_response(data={
        'room': {'id': room_id, 'name': ''},
        'seats': []
    })


@student_bp.route('/seats/search', methods=['GET'])
@jwt_required()
def search_seats():
    """按条件搜索座位"""
    date = request.args.get('date')
    if not date:
        return error_response('date 参数必填', code=400)
    # TODO: 实现条件搜索座位
    return success_response(data={'items': []})


# ============================================================================
# 2.4 预约管理
# ============================================================================

@student_bp.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    """提交座位预约"""
    data = request.get_json()
    # TODO: 实现预约提交（含冲突检测、4小时限制）
    return success_response(data=None)


@student_bp.route('/reservations', methods=['GET'])
@jwt_required()
def list_reservations():
    """我的预约记录"""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0})


@student_bp.route('/reservations/<int:id>', methods=['GET'])
@jwt_required()
def get_reservation(id):
    """预约详情"""
    # TODO: 实现预约详情
    return success_response(data=None)


@student_bp.route('/reservations/<int:id>/cancel', methods=['POST'])
@jwt_required()
def cancel_reservation(id):
    """取消预约"""
    data = request.get_json() or {}
    reason = data.get('reason')
    # TODO: 实现取消预约
    return success_response(data=None)


# ============================================================================
# 2.5 签到
# ============================================================================

@student_bp.route('/reservations/<int:id>/check-in', methods=['POST'])
@jwt_required()
def check_in(id):
    """预约签到"""
    data = request.get_json()
    code = data.get('code')
    if not code:
        return error_response('签到码不能为空', code=400)
    # TODO: 实现签到逻辑（校验动态码、记录签到时间）
    return success_response(data={'check_in_time': None})


# ============================================================================
# 2.6 通知与违约
# ============================================================================

@student_bp.route('/notifications', methods=['GET'])
@jwt_required()
def list_notifications():
    """通知列表"""
    is_read = request.args.get('is_read')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': page, 'per_page': per_page, 'pages': 0})


@student_bp.route('/notifications/<int:id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(id):
    """标记单条通知为已读"""
    # TODO: 实现标记已读
    return success_response(data=None)


@student_bp.route('/notifications/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    """标记所有通知为已读"""
    # TODO: 实现标记全部已读
    return success_response(data=None)


@student_bp.route('/violations', methods=['GET'])
@jwt_required()
def list_violations():
    """我的违约记录"""
    # TODO: 实现违约记录查询
    return success_response(data={'items': []})
