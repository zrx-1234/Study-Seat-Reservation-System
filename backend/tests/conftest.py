"""
pytest配置与共享固件
"""
import pytest
from flask import Flask
from extensions import db, init_extensions


@pytest.fixture
def app():
    """
    测试用Flask应用固件
    """
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-unit-tests'

    init_extensions(app)

    with app.app_context():
        # 确保所有模型类都被注册到 SQLAlchemy metadata
        from domain.user import models as _user_models  # noqa
        from domain.room import models as _room_models  # noqa
        from domain.reservation import models as _resv_models  # noqa
        from domain.notification import models as _notif_models  # noqa
        from domain.system import models as _sys_models  # noqa
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """
    测试用客户端固件
    """
    return app.test_client()


@pytest.fixture
def db_session(app):
    """
    测试用数据库会话固件
    """
    with app.app_context():
        yield db.session
        db.session.rollback()
