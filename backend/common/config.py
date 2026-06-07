import os


def _build_db_uri():
    """
    优先使用 DATABASE_URL；否则用 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME 组合
    """
    url = os.environ.get('DATABASE_URL')
    if url:
        return url

    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT', '3306')
    user = os.environ.get('DB_USER', 'root')
    password = os.environ.get('DB_PASSWORD', 'password')
    name = os.environ.get('DB_NAME', 'seat_reservation')
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4'


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key'
    SQLALCHEMY_DATABASE_URI = _build_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
