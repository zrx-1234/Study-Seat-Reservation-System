from flask import Flask
from admin.routes import admin_bp


def register_blueprints(app: Flask):
    """注册管理端蓝本"""
    app.register_blueprint(admin_bp)
