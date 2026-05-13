"""
数据库种子数据脚本
运行方式: python seed.py
注意: 会清空现有数据并重新插入默认值, 仅建议在开发环境执行
"""

import os
from werkzeug.security import generate_password_hash
from app import create_app
from common.models import db, User, Role, Permission, StudyRoom, Seat, SystemConfig


def seed_permissions():
    """初始化权限列表"""
    permissions = [
        Permission(name='用户管理', code='user:manage', description='创建、编辑、删除用户及分配角色'),
        Permission(name='角色管理', code='role:manage', description='创建、编辑、删除角色及分配权限'),
        Permission(name='自习室管理', code='room:manage', description='登记、编辑、注销自习室'),
        Permission(name='座位管理', code='seat:manage', description='登记、编辑、注销座位及特殊标记'),
        Permission(name='预约管理', code='reservation:manage', description='查看、代理预约、取消预约'),
        Permission(name='违约查看', code='violation:view', description='查看违约记录及导出'),
        Permission(name='系统配置', code='system:config', description='调整系统全局参数'),
        Permission(name='数据统计', code='stat:view', description='查看预约率、利用率等统计数据'),
    ]
    for p in permissions:
        existing = Permission.query.filter_by(code=p.code).first()
        if not existing:
            db.session.add(p)
    db.session.commit()
    return Permission.query.all()


def seed_roles(permissions):
    """初始化角色并绑定权限"""
    # 超级管理员: 拥有所有权限
    super_admin = Role.query.filter_by(name='super_admin').first()
    if not super_admin:
        super_admin = Role(name='super_admin', description='超级管理员, 拥有系统全部权限')
        super_admin.permissions = permissions
        db.session.add(super_admin)

    # 普通管理员: 除角色管理和系统配置外的权限
    admin = Role.query.filter_by(name='admin').first()
    if not admin:
        admin = Role(name='admin', description='普通管理员, 负责日常运营')
        excluded = {'role:manage', 'system:config'}
        admin.permissions = [p for p in permissions if p.code not in excluded]
        db.session.add(admin)

    # 只读操作员: 只能查看
    viewer = Role.query.filter_by(name='viewer').first()
    if not viewer:
        viewer = Role(name='viewer', description='只读操作员, 仅可查看数据')
        viewer_codes = {'reservation:manage', 'violation:view', 'stat:view'}
        viewer.permissions = [p for p in permissions if p.code in viewer_codes]
        db.session.add(viewer)

    db.session.commit()
    return [super_admin, admin, viewer]


def seed_users(roles):
    """初始化系统用户"""
    super_admin_role = next(r for r in roles if r.name == 'super_admin')
    admin_role = next(r for r in roles if r.name == 'admin')

    # 超级管理员账号
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('123456'),
            name='系统管理员',
            user_type='admin',
            email='admin@fdu.edu.cn',
            is_active=True,
        )
        admin_user.roles = [super_admin_role]
        db.session.add(admin_user)

    # 普通管理员账号(用于测试)
    normal_admin = User.query.filter_by(username='teacher01').first()
    if not normal_admin:
        normal_admin = User(
            username='teacher01',
            password_hash=generate_password_hash('123456'),
            name='李老师',
            user_type='admin',
            department='计算机学院',
            email='teacher01@fdu.edu.cn',
            is_active=True,
        )
        normal_admin.roles = [admin_role]
        db.session.add(normal_admin)

    # 测试学生账号
    student = User.query.filter_by(username='2025123456').first()
    if not student:
        student = User(
            username='2025123456',
            password_hash=generate_password_hash('123456'),
            name='张三',
            user_type='student',
            department='计算机学院',
            email='2025123456@fdu.edu.cn',
            is_active=True,
        )
        db.session.add(student)

    db.session.commit()


def seed_system_configs():
    """初始化系统默认配置参数"""
    configs = [
        ('max_reservation_hours', '4', '单次最大预约时长(小时)'),
        ('no_show_threshold_minutes', '15', '超时未签到判定为违约的阈值(分钟)'),
        ('remind_before_minutes', '15', '预约开始前提醒时间(分钟)'),
        ('check_in_alert_minutes', '10', '预约开始后未签到再次提醒时间(分钟)'),
        ('sign_in_code_refresh_hours', '24', '动态签到码更新周期(小时)'),
        ('max_active_reservations', '2', '学生同时最大进行中的预约数'),
    ]
    for key, value, desc in configs:
        existing = SystemConfig.query.filter_by(config_key=key).first()
        if not existing:
            db.session.add(SystemConfig(
                config_key=key,
                config_value=value,
                description=desc
            ))
    db.session.commit()


def seed_study_rooms_and_seats():
    """初始化测试用自习室和座位"""
    rooms_data = [
        {
            'name': '理科图书馆 301 自习室',
            'location': '理科图书馆 3楼',
            'capacity': 60,
            'room_type': 'public',
            'department': None,
            'seats': [
                {'seat_number': 'A01', 'has_window': True, 'has_plug': True},
                {'seat_number': 'A02', 'has_window': True, 'has_plug': False},
                {'seat_number': 'A03', 'has_window': False, 'has_plug': True},
                {'seat_number': 'B01', 'has_window': False, 'has_plug': False},
                {'seat_number': 'B02', 'has_window': False, 'has_plug': True},
                {'seat_number': 'B03', 'has_window': False, 'has_plug': True},
            ]
        },
        {
            'name': '计算机学院 201 自习室',
            'location': '计算机楼 2楼',
            'capacity': 40,
            'room_type': 'department',
            'department': '计算机学院',
            'seats': [
                {'seat_number': 'C01', 'has_window': True, 'has_plug': True},
                {'seat_number': 'C02', 'has_window': True, 'has_plug': True},
                {'seat_number': 'C03', 'has_window': False, 'has_plug': False},
                {'seat_number': 'D01', 'has_window': False, 'has_plug': True},
                {'seat_number': 'D02', 'has_window': False, 'has_plug': True},
                {'seat_number': 'D03', 'has_window': False, 'has_plug': False},
            ]
        },
        {
            'name': '文科馆通宵自习室',
            'location': '文科图书馆 B1',
            'capacity': 30,
            'room_type': 'public',
            'department': None,
            'open_time': '00:00:00',
            'close_time': '23:59:59',
            'seats': [
                {'seat_number': 'E01', 'has_window': False, 'has_plug': True},
                {'seat_number': 'E02', 'has_window': False, 'has_plug': True},
                {'seat_number': 'E03', 'has_window': False, 'has_plug': True},
                {'seat_number': 'E04', 'has_window': False, 'has_plug': True},
            ]
        },
    ]

    for room_info in rooms_data:
        existing = StudyRoom.query.filter_by(name=room_info['name']).first()
        if existing:
            continue

        seats_info = room_info.pop('seats')
        room = StudyRoom(**room_info)
        db.session.add(room)
        db.session.flush()  # 获取 room.id

        for s in seats_info:
            seat = Seat(room_id=room.id, **s)
            db.session.add(seat)

    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        print('开始初始化种子数据...')

        # 建表(如果是新数据库)
        db.create_all()
        print('数据库表已创建/更新')

        permissions = seed_permissions()
        print(f'权限数据已初始化, 共 {len(permissions)} 条')

        roles = seed_roles(permissions)
        print(f'角色数据已初始化, 共 {len(roles)} 个角色')

        seed_users(roles)
        print('用户数据已初始化')
        print('  - 超级管理员: admin / 123456')
        print('  - 普通管理员: teacher01 / 123456')
        print('  - 测试学生: 2025123456 / 123456')

        seed_system_configs()
        print('系统默认配置已初始化')

        seed_study_rooms_and_seats()
        print('测试自习室和座位数据已初始化')

        print('种子数据初始化完成!')


if __name__ == '__main__':
    main()
