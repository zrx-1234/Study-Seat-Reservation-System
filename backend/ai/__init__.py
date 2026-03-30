from flask import Flask
from ai.assistant import assistant_bp


def register_blueprints(app: Flask):
    """注册AI助手蓝本"""
    app.register_blueprint(assistant_bp)
