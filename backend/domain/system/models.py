"""
MOD-SYS: 系统配置模块 - 数据实体
SystemConfig
"""

from datetime import datetime
from extensions import db

# ============================================================================
# 实体模型
# ============================================================================

class SystemConfig(db.Model):
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(64), unique=True, nullable=False, comment='配置项键名')
    config_value = db.Column(db.String(512), nullable=False, comment='配置项值')
    description = db.Column(db.String(256), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SystemConfig {self.config_key}={self.config_value}>"
