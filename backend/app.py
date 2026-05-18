from flask import Flask

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

    # 注册新的API蓝本（v2架构）
    from api.student import student_bp
    from api.admin import admin_bp
    from api.ai import ai_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)

    # 保留旧的蓝图注册（向后兼容，逐步迁移）
    try:
        from admin import register_blueprints as register_admin
        from student import register_blueprints as register_student
        from ai import register_blueprints as register_ai

        register_admin(app)
        register_student(app)
        register_ai(app)
    except ImportError:
        pass

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
