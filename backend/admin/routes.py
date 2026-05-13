from flask import Blueprint, request

from common.auth import authenticate_user, get_current_user, require_permission
from common.utils import success_response, error_response

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


# ============================================================================
# 3.1 认证相关
# ============================================================================

@admin_bp.route('/auth/login', methods=['POST'])
def login():
    """管理员登录"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return error_response('用户名和密码不能为空', code=400)

    user, token = authenticate_user(username, password)
    if not user or user.user_type != 'admin':
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
            'roles': [{'id': r.id, 'name': r.name} for r in user.roles]
        }
    })


# ============================================================================
# 3.2 仪表盘
# ============================================================================

@admin_bp.route('/dashboard/stats', methods=['GET'])
@require_permission('stat:view')
def dashboard_stats():
    """管理端首页统计数据"""
    # TODO: 实现统计查询
    return success_response(data={
        'total_rooms': 0,
        'total_seats': 0,
        'today_reservations': 0,
        'today_violations': 0,
        'active_users': 0
    })


# ============================================================================
# 3.3 RBAC 权限管理
# ============================================================================

@admin_bp.route('/roles', methods=['GET'])
@require_permission('role:manage')
def list_roles():
    """角色列表（分页）"""
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/roles', methods=['POST'])
@require_permission('role:manage')
def create_role():
    """创建角色"""
    # TODO: 实现创建角色
    return success_response(data=None)


@admin_bp.route('/roles/<int:id>', methods=['GET'])
@require_permission('role:manage')
def get_role(id):
    """角色详情（含权限列表）"""
    # TODO: 实现角色详情
    return success_response(data=None)


@admin_bp.route('/roles/<int:id>', methods=['PUT'])
@require_permission('role:manage')
def update_role(id):
    """更新角色"""
    # TODO: 实现更新角色
    return success_response(data=None)


@admin_bp.route('/roles/<int:id>', methods=['DELETE'])
@require_permission('role:manage')
def delete_role(id):
    """删除角色（如角色下仍有用户，返回 409 冲突）"""
    # TODO: 实现删除角色
    return success_response(data=None)


@admin_bp.route('/permissions', methods=['GET'])
@require_permission('role:manage')
def list_permissions():
    """权限列表（全量，不分页）"""
    # TODO: 实现全量查询
    return success_response(data={'items': []})


# ============================================================================
# 3.4 用户管理（管理员账号）
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@require_permission('user:manage')
def list_users():
    """管理员用户列表（分页）"""
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/users', methods=['POST'])
@require_permission('user:manage')
def create_user():
    """创建管理员账号"""
    # TODO: 实现创建管理员
    return success_response(data=None)


@admin_bp.route('/users/<int:id>', methods=['GET'])
@require_permission('user:manage')
def get_user(id):
    """管理员详情"""
    # TODO: 实现管理员详情
    return success_response(data=None)


@admin_bp.route('/users/<int:id>', methods=['PUT'])
@require_permission('user:manage')
def update_user(id):
    """更新管理员信息及角色分配"""
    # TODO: 实现更新管理员
    return success_response(data=None)


@admin_bp.route('/users/<int:id>', methods=['DELETE'])
@require_permission('user:manage')
def delete_user(id):
    """删除管理员账号"""
    # TODO: 实现删除管理员
    return success_response(data=None)


# ============================================================================
# 3.5 自习室管理
# ============================================================================

@admin_bp.route('/rooms', methods=['GET'])
@require_permission('room:manage')
def list_rooms():
    """自习室列表（分页）"""
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/rooms', methods=['POST'])
@require_permission('room:manage')
def create_room():
    """登记自习室"""
    # TODO: 实现创建自习室
    return success_response(data=None)


@admin_bp.route('/rooms/<int:id>', methods=['GET'])
@require_permission('room:manage')
def get_room_detail(id):
    """自习室详情"""
    # TODO: 实现自习室详情
    return success_response(data=None)


@admin_bp.route('/rooms/<int:id>', methods=['PUT'])
@require_permission('room:manage')
def update_room(id):
    """更新自习室信息"""
    # TODO: 实现更新自习室
    return success_response(data=None)


@admin_bp.route('/rooms/<int:id>', methods=['DELETE'])
@require_permission('room:manage')
def delete_room(id):
    """注销自习室（is_active 设为 false，并自动取消未来预约）"""
    # TODO: 实现注销自习室
    return success_response(data=None)


# ============================================================================
# 3.6 座位管理
# ============================================================================

@admin_bp.route('/rooms/<int:room_id>/seats', methods=['GET'])
@require_permission('seat:manage')
def list_seats(room_id):
    """某自习室的座位列表（分页）"""
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/rooms/<int:room_id>/seats', methods=['POST'])
@require_permission('seat:manage')
def create_seats(room_id):
    """批量登记座位"""
    # TODO: 实现批量创建座位
    return success_response(data=None)


@admin_bp.route('/seats/<int:id>', methods=['PUT'])
@require_permission('seat:manage')
def update_seat(id):
    """更新座位（状态、标记）"""
    # TODO: 实现更新座位
    return success_response(data=None)


@admin_bp.route('/seats/<int:id>', methods=['DELETE'])
@require_permission('seat:manage')
def delete_seat(id):
    """注销座位（status 设为 retired）"""
    # TODO: 实现注销座位
    return success_response(data=None)


# ============================================================================
# 3.7 预约与违约管理
# ============================================================================

@admin_bp.route('/reservations', methods=['GET'])
@require_permission('reservation:manage')
def list_reservations():
    """全局预约记录查询（分页）"""
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/reservations', methods=['POST'])
@require_permission('reservation:manage')
def create_reservation():
    """代理预约（为学生预约座位）"""
    # TODO: 实现代理预约
    return success_response(data=None)


@admin_bp.route('/reservations/<int:id>/cancel', methods=['POST'])
@require_permission('reservation:manage')
def cancel_reservation(id):
    """管理员取消预约"""
    # TODO: 实现管理员取消预约
    return success_response(data=None)


@admin_bp.route('/violations', methods=['GET'])
@require_permission('violation:view')
def list_violations():
    """违约记录列表（分页）"""
    # TODO: 实现分页查询
    return success_response(data={'items': [], 'total': 0, 'page': 1, 'per_page': 20, 'pages': 0})


@admin_bp.route('/violations/export', methods=['GET'])
@require_permission('violation:view')
def export_violations():
    """导出违约记录（CSV/Excel）"""
    # TODO: 实现导出
    return success_response(data=None)


# ============================================================================
# 3.8 系统配置
# ============================================================================

@admin_bp.route('/configs', methods=['GET'])
@require_permission('system:config')
def list_configs():
    """系统参数列表（全量，不分页）"""
    # TODO: 实现全量查询
    return success_response(data={'items': []})


@admin_bp.route('/configs/<string:key>', methods=['PUT'])
@require_permission('system:config')
def update_config(key):
    """更新系统参数"""
    # TODO: 实现更新配置
    return success_response(data=None)
