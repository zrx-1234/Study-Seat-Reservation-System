from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

load_dotenv(Path(__file__).resolve().parent / '.env')

from common.config import Config
from extensions import init_extensions
from infrastructure.exceptions import register_error_handlers
from infrastructure.auth import register_jwt_callbacks


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    from extensions import jwt
    init_extensions(app)

    # 注册JWT回调
    register_jwt_callbacks(jwt)

    # 注册全局异常处理
    register_error_handlers(app)

    # 注册 v2 架构 API 蓝本
    from api.student import student_bp
    from api.admin import admin_bp
    from api.ai import ai_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)

    # 保留旧的蓝图注册（向后兼容，逐步迁移）
    # 若与新 API 蓝图重名，直接跳过旧蓝图，避免重复注册导致启动失败。
    try:
        from admin import register_blueprints as register_admin
        from student import register_blueprints as register_student
        from ai import register_blueprints as register_ai

        for register_legacy in (register_admin, register_student, register_ai):
            try:
                register_legacy(app)
            except ValueError as err:
                if 'already registered for a different blueprint' not in str(err):
                    raise
    except ImportError:
        pass
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
