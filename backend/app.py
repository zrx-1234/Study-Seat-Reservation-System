from flask import Flask
from flask_cors import CORS

from common.config import Config
from common.models import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    # 注册各模块蓝本
    from admin import register_blueprints as register_admin
    from student import register_blueprints as register_student
    from ai import register_blueprints as register_ai

    register_admin(app)
    register_student(app)
    register_ai(app)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
