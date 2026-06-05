import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{(DATA_DIR / 'seat_reservation.db').as_posix()}"

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key'
    # 默认使用项目内 SQLite 文件，避免强依赖本机 MySQL。
    # 如需切换到 MySQL，可通过环境变量 DATABASE_URL 覆盖。
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or DEFAULT_SQLITE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
