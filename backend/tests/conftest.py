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

    init_extensions(app)

    with app.app_context():
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
