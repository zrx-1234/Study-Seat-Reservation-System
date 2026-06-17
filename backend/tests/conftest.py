"""
pytest配置与共享固件
"""
import pytest
from flask import Flask
from extensions import db, jwt, init_extensions
from infrastructure.exceptions import register_error_handlers
from infrastructure.auth import register_jwt_callbacks, create_token


@pytest.fixture(autouse=True)
def isolate_ai_env(monkeypatch):
    """隔离AI相关环境变量，避免测试误调用真实LLM。"""
    monkeypatch.setenv('LLM_PROVIDER', 'mock')
    monkeypatch.setenv('USE_LLM_REPLY', 'false')
    monkeypatch.setenv('AI_RATE_LIMIT_PER_USER', '30')
    monkeypatch.setenv('AI_RATE_LIMIT_WINDOW', '60')


@pytest.fixture
def app():
    """测试用Flask应用固件"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-unit-tests'

    init_extensions(app)
    register_jwt_callbacks(jwt)
    register_error_handlers(app)

    # 导入所有模型，确保FK关系被SQLAlchemy识别
    with app.app_context():
        _import_all_models()

    # 注册AI蓝色图
    from api.ai import ai_bp
    app.register_blueprint(ai_bp)

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


def _import_all_models():
    """导入所有领域模型，确保db.create_all()能解析FK引用"""
    from domain.user.models import User, Role, Permission
    from domain.room.models import StudyRoom, Seat, SignInCode
    from domain.reservation.models import Reservation, ViolationRecord
    from domain.notification.models import Notification
    from domain.system.models import SystemConfig


@pytest.fixture
def client(app):
    """测试用客户端固件"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """测试用数据库会话固件"""
    with app.app_context():
        yield db.session
        db.session.rollback()


@pytest.fixture
def auth_token(app):
    """生成测试用JWT token"""
    with app.app_context():
        return create_token(identity='1', additional_claims={
            'user_type': 'student',
            'permissions': []
        })


@pytest.fixture
def auth_headers(auth_token):
    """带JWT token的请求头"""
    return {'Authorization': f'Bearer {auth_token}'}
