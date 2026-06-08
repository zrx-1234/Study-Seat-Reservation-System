#!/bin/bash
# 后端容器入口脚本
# 功能：等待数据库就绪 → 初始化种子数据 → 启动 gunicorn

set -e

# 等待 MySQL 就绪
echo "⏳ 等待 MySQL 就绪..."
while ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    echo "MySQL 尚未就绪，等待 2 秒..."
    sleep 2
done
echo "✅ MySQL 已就绪"

# 初始化数据库表
echo "🗄️  创建数据库表..."
flask db init 2>/dev/null || true
flask db migrate -m "initial" 2>/dev/null || true
flask db upgrade 2>/dev/null || true

# 执行种子数据（幂等）
echo "🌱 初始化种子数据..."
python seed.py

# 启动 gunicorn
echo "🚀 启动 Gunicorn 服务..."
exec "$@"