"""
API-ADM: 管理端接口模块
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from infrastructure.exceptions import success_response, error_response, ValidationError, NotFoundError, ConflictError
from infrastructure.auth import get_current_user_id, require_permission
from domain.user import service as user_service
from domain.user.dto import UserCreateDTO, UserUpdateDTO, RoleCreateDTO, RoleUpdateDTO
from domain.room import service as room_service
from domain.reservation import service as reservation_service
from domain.system import service as system_service

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

# ============================================================================
# 3.1 认证相关
# ============================================================================

@admin_bp.route('/auth/login', methods=['POST'])
def login():
    """管理员登录"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error_response('用户名和密码不能为空', code=400)

    user_dict, token = user_service.authenticate(username, password)
    if not user_dict or user_dict.get('user_type') != 'admin':
        return error_response('用户名或密码错误', code=401)

    return success_response(data={
        'access_token': token,
        'token_type': 'Bearer',
        'expires_in': 86400,
        'user': user_dict
    })

# ============================================================================
# 3.2 仪表盘
# ============================================================================

@admin_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@require_permission('stat:view')
def dashboard_stats():
    """管理端首页统计数据"""
    room_stats = room_service.get_room_stats()
    resv_stats = reservation_service.get_reservation_stats()

    return success_response(data={
        'total_rooms': getattr(room_stats, 'total_rooms', 0),
        'total_seats': getattr(room_stats, 'total_seats', 0),
        'today_reservations': resv_stats.get('today_reservations', 0) if isinstance(resv_stats, dict) else getattr(resv_stats, 'today_reservations', 0),
        'today_violations': resv_stats.get('today_violations', 0) if isinstance(resv_stats, dict) else getattr(resv_stats, 'today_violations', 0),
        'active_users': resv_stats.get('active_users', 0) if isinstance(resv_stats, dict) else getattr(resv_stats, 'active_users', 0)
    })

# ============================================================================
# 3.3 RBAC 权限管理
# ============================================================================

@admin_bp.route('/roles', methods=['GET'])
@jwt_required()
@require_permission('role:manage')
def list_roles():
    """角色列表（分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result = user_service.list_roles(page=page, per_page=per_page)
    return success_response(data=result)


@admin_bp.route('/roles', methods=['POST'])
@jwt_required()
@require_permission('role:manage')
def create_role():
    """创建角色"""
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    permission_ids = data.get('permission_ids', [])

    if not name:
        return error_response('角色名称不能为空', code=400)

    try:
        dto = user_service.create_role(
            RoleCreateDTO(name=name, description=description, permission_ids=permission_ids)
        )
        return success_response(data=dto)
    except (ValidationError, ConflictError) as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/roles/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('role:manage')
def get_role(id):
    """角色详情（含权限列表）"""
    role = user_service.get_role(id)
    if not role:
        return error_response('角色不存在', code=404)
    return success_response(data=role)


@admin_bp.route('/roles/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('role:manage')
def update_role(id):
    """更新角色"""
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    permission_ids = data.get('permission_ids')

    try:
        dto = user_service.update_role(
            id,
            RoleUpdateDTO(name=name, description=description, permission_ids=permission_ids)
        )
        return success_response(data=dto)
    except NotFoundError as e:
        return error_response(str(e), code=404)
    except (ValidationError, ConflictError) as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/roles/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('role:manage')
def delete_role(id):
    """删除角色（如角色下仍有用户，返回409冲突）"""
    try:
        user_service.delete_role(id)
        return success_response(data=None)
    except NotFoundError as e:
        return error_response(str(e), code=404)
    except ConflictError as e:
        return error_response(str(e), code=409)


@admin_bp.route('/permissions', methods=['GET'])
@jwt_required()
@require_permission('role:manage')
def list_permissions():
    """权限列表（全量，不分页）"""
    perms = user_service.list_permissions()
    return success_response(data={'items': perms})

# ============================================================================
# 3.4 用户管理（管理员账号）
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_permission('user:manage')
def list_users():
    """管理员用户列表（分页）"""
    role_id = request.args.get('role_id', type=int)
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = user_service.list_users(
        user_type='admin', role_id=role_id, keyword=keyword, page=page, per_page=per_page
    )
    return success_response(data=result)


@admin_bp.route('/users', methods=['POST'])
@jwt_required()
@require_permission('user:manage')
def create_user():
    """创建管理员账号"""
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    department = data.get('department')
    email = data.get('email')
    role_ids = data.get('role_ids', [])

    if not username or not password or not name:
        return error_response('用户名、密码和姓名不能为空', code=400)

    try:
        dto = user_service.create_user(
            UserCreateDTO(
                username=username, password=password, name=name,
                user_type='admin', department=department, email=email
            )
        )
        # 分配角色
        if role_ids:
            user_service.assign_roles_to_user(dto.id, role_ids)
            # 重新获取以包含角色信息
            dto = user_service.get_user(dto.id)
        return success_response(data=dto)
    except (ValidationError, ConflictError) as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/users/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('user:manage')
def get_user(id):
    """管理员详情"""
    user = user_service.get_user(id)
    if not user:
        return error_response('用户不存在', code=404)
    return success_response(data=user)


@admin_bp.route('/users/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('user:manage')
def update_user(id):
    """更新管理员信息及角色分配"""
    data = request.get_json() or {}
    name = data.get('name')
    department = data.get('department')
    email = data.get('email')
    role_ids = data.get('role_ids')

    try:
        dto = user_service.update_user(
            id, UserUpdateDTO(name=name, department=department, email=email)
        )
        if role_ids is not None:
            user_service.assign_roles_to_user(id, role_ids)
            dto = user_service.get_user(id)
        return success_response(data=dto)
    except NotFoundError as e:
        return error_response(str(e), code=404)
    except ValidationError as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/users/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('user:manage')
def delete_user(id):
    """删除管理员账号"""
    try:
        user_service.delete_user(id)
        return success_response(data=None)
    except NotFoundError as e:
        return error_response(str(e), code=404)
    except ConflictError as e:
        return error_response(str(e), code=409)

# ============================================================================
# 3.5 自习室管理
# ============================================================================

@admin_bp.route('/rooms', methods=['GET'])
@jwt_required()
@require_permission('room:manage')
def list_rooms():
    """自习室列表（分页）"""
    room_type = request.args.get('room_type') or None
    is_active = request.args.get('is_active')
    # 空字符串应视为"未选择"，不传过滤条件；只有 'true'/'false' 才生效
    if is_active and is_active.strip():
        is_active = is_active.lower() == 'true'
    else:
        is_active = None
    keyword = request.args.get('keyword') or None
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = room_service.list_rooms(room_type=room_type, is_active=is_active, keyword=keyword, page=page, per_page=per_page)
    return success_response(data=result)


@admin_bp.route('/rooms', methods=['POST'])
@jwt_required()
@require_permission('room:manage')
def create_room():
    """登记自习室"""
    data = request.get_json() or {}
    try:
        dto = room_service.create_room(data)
        return success_response(data=dto)
    except (ValidationError, ConflictError) as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/rooms/<int:id>', methods=['GET'])
@jwt_required()
@require_permission('room:manage')
def get_room_detail(id):
    """自习室详情"""
    room = room_service.get_room(id)
    if not room:
        return error_response('自习室不存在', code=404)
    return success_response(data=room)


@admin_bp.route('/rooms/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('room:manage')
def update_room(id):
    """更新自习室信息"""
    data = request.get_json() or {}
    try:
        dto = room_service.update_room(id, data)
        return success_response(data=dto)
    except NotFoundError as e:
        return error_response(str(e), code=404)
    except (ValidationError, ConflictError) as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/rooms/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('room:manage')
def delete_room(id):
    """注销自习室（is_active设为false，并自动取消未来预约）"""
    try:
        room_service.delete_room(id)
        return success_response(data=None)
    except NotFoundError as e:
        return error_response(str(e), code=404)

# ============================================================================
# 3.6 座位管理
# ============================================================================

@admin_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
@jwt_required()
@require_permission('seat:manage')
def list_seats(room_id):
    """某自习室的座位列表（分页）"""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result = room_service.list_seats(room_id=room_id, status=status, page=page, per_page=per_page)
    return success_response(data=result)


@admin_bp.route('/rooms/<int:room_id>/seats', methods=['POST'])
@jwt_required()
@require_permission('seat:manage')
def create_seats(room_id):
    """批量登记座位"""
    data = request.get_json() or {}
    seats = data.get('seats', [])

    # 支持 prefix + count 批量生成
    if not seats and data.get('prefix') and data.get('count'):
        prefix = data.get('prefix')
        start_number = data.get('start_number', 1)
        count = data.get('count')
        has_window = data.get('has_window', False)
        has_plug = data.get('has_plug', False)
        seats = []
        for i in range(count):
            num = start_number + i
            seats.append({
                'seat_number': f'{prefix}{num:02d}',
                'has_window': has_window,
                'has_plug': has_plug,
            })

    if not seats:
        return error_response('座位数据不能为空', code=400)

    try:
        result = room_service.create_seats(room_id, seats)
        return success_response(data=result)
    except NotFoundError as e:
        return error_response(str(e), code=404)
    except (ValidationError, ConflictError) as e:
        return error_response(str(e), code=e.code)


@admin_bp.route('/seats/<int:id>', methods=['PUT'])
@jwt_required()
@require_permission('seat:manage')
def update_seat(id):
    """更新座位（状态、标记）"""
    data = request.get_json() or {}
    try:
        dto = room_service.update_seat(id, data)
        return success_response(data=dto)
    except NotFoundError as e:
        return error_response(str(e), code=404)


@admin_bp.route('/seats/<int:id>', methods=['DELETE'])
@jwt_required()
@require_permission('seat:manage')
def delete_seat(id):
    """注销座位（status设为retired）"""
    try:
        room_service.delete_seat(id)
        return success_response(data=None)
    except NotFoundError as e:
        return error_response(str(e), code=404)

# ============================================================================
# 3.7 预约与违约管理
# ============================================================================

@admin_bp.route('/reservations', methods=['GET'])
@jwt_required()
@require_permission('reservation:manage')
def list_reservations():
    """全局预约记录查询（分页）"""
    status = request.args.get('status') or None
    keyword = request.args.get('keyword') or None
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 解析日期范围
    date_range = request.args.getlist('date_range')
    filters = {'status': status, 'keyword': keyword}
    if date_range and len(date_range) == 2:
        from datetime import date, datetime
        try:
            filters['start_date'] = date.fromisoformat(date_range[0])
            filters['end_date'] = date.fromisoformat(date_range[1])
        except ValueError:
            pass

    result = reservation_service.list_all_reservations(filters=filters, page=page, per_page=per_page)

    # 字段映射：将嵌套对象展开为前端表格所需的扁平字段
    items = []
    for item in result.get('items', []):
        user = item.get('user') or {}
        seat = item.get('seat') or {}
        room = item.get('room') or {}
        items.append({
            'id': item['id'],
            'user_name': user.get('name'),
            'room_name': room.get('name'),
            'seat_number': seat.get('seat_number'),
            'start_time': item.get('start_time'),
            'end_time': item.get('end_time'),
            'status': item.get('status'),
        })

    return success_response(data={
        'items': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    })


@admin_bp.route('/reservations', methods=['POST'])
@jwt_required()
@require_permission('reservation:manage')
def create_reservation():
    """代理预约（为学生预约座位）"""
    # TODO: 实现
    return success_response(data=None)


@admin_bp.route('/reservations/<int:id>/cancel', methods=['POST'])
@jwt_required()
@require_permission('reservation:manage')
def cancel_reservation(id):
    """管理员取消预约"""
    # TODO: 实现
    return success_response(data=None)


@admin_bp.route('/violations', methods=['GET'])
@jwt_required()
@require_permission('violation:view')
def list_violations():
    """违约记录列表（分页）"""
    # TODO: 实现
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/violations/export', methods=['GET'])
@jwt_required()
@require_permission('violation:view')
def export_violations():
    """导出违约记录（CSV/Excel）"""
    # TODO: 实现
    return success_response(data=None)

# ============================================================================
# 3.8 系统配置
# ============================================================================

@admin_bp.route('/configs', methods=['GET'])
@jwt_required()
@require_permission('system:config')
def list_configs():
    """系统参数列表（全量，不分页）"""
    configs = system_service.get_all_configs()
    return success_response(data={'items': configs})


@admin_bp.route('/configs/<string:key>', methods=['PUT'])
@jwt_required()
@require_permission('system:config')
def update_config(key):
    """更新系统参数"""
    data = request.get_json() or {}
    value = data.get('value')
    description = data.get('description')

    if value is None:
        return error_response('value不能为空', code=400)

    try:
        system_service.set_config(key, value, description)
        return success_response(data=None)
    except ValidationError as e:
        return error_response(str(e), code=400)
