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

    # 注册 v2 架构 API 蓝本
    from api.student import student_bp
    from api.admin import admin_bp
    from api.ai import ai_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
