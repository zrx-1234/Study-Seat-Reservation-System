from flask import Flask
from student.routes import student_bp


def register_blueprints(app: Flask):
    """注册学生端蓝本"""
    app.register_blueprint(student_bp)
