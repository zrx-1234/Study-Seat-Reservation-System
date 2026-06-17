# AI助手模块 - 部署指南

> 版本: v1.0  
> 更新日期: 2026-06-05

---

## 部署前准备

### 1. 依赖检查

确保已安装以下依赖：

```bash
cd backend

# 核心依赖
pip install flask flask-jwt-extended flask-sqlalchemy flask-migrate flask-cors

# AI模块依赖
pip install python-dotenv openai

# 测试依赖
pip install pytest pytest-cov
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

`requirements.txt` 已包含 OpenAI SDK。启用真实 API 前请配置 `.env`，不要提交真实 API key。

### 2. 环境配置

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
vim .env
```

---

## 开发环境部署

### 1. 本地开发

```bash
# 1. 启动后端
cd backend
python app.py

# 2. 运行测试
pytest tests/domain/ai/ -v

# 3. 测试API
curl -X POST http://localhost:5000/api/v1/ai/chat \
  -H "Authorization: Bearer TOKEN" \
  -d '{"message": "今晚有空座吗"}'
```

### 2. 使用Mock模式

默认配置使用Mock模式，无需外部API：

```bash
# .env
LLM_PROVIDER=mock
```

优点：
- ✅ 无需API key
- ✅ 响应速度快
- ✅ 适合开发调试
- ✅ 不产生API费用

---

## 生产环境部署

### 1. 配置清单

#### 必需配置

```bash
# .env（生产环境）

# Flask配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 数据库
DATABASE_URL=mysql://user:pass@host:3306/dbname

# LLM配置（推荐OpenAI）
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-production-key
OPENAI_MODEL=gpt-3.5-turbo

# 限流配置
AI_RATE_LIMIT_PER_USER=30
AI_RATE_LIMIT_WINDOW=60

# 功能配置
# auto: 关键词低置信度时调用LLM；true: 强制LLM；false: 只用关键词
LLM_INTENT_RECOGNITION=auto
# true: 支持的场景使用LLM生成回复；false: 使用本地模板
USE_LLM_REPLY=false
```

#### 可选配置（Redis）

```bash
# 会话存储（推荐生产环境使用Redis）
SESSION_STORE_TYPE=redis
REDIS_URL=redis://localhost:6379/1
```

### 2. 使用Gunicorn部署

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务（4个worker）
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"

# 后台运行
nohup gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()" > gunicorn.log 2>&1 &
```

### 3. 使用Systemd管理

创建服务文件 `/etc/systemd/system/ai-backend.service`:

```ini
[Unit]
Description=AI Study Seat Reservation Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/study-seat-backend
Environment="PATH=/opt/study-seat-backend/venv/bin"
ExecStart=/opt/study-seat-backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start ai-backend
sudo systemctl enable ai-backend
sudo systemctl status ai-backend
```

### 4. 使用Nginx反向代理

配置文件 `/etc/nginx/sites-available/ai-backend`:

```nginx
upstream ai_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 10M;

    location /api/v1/ai {
        proxy_pass http://ai_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置（AI响应可能较慢）
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/ai-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Docker部署（推荐）

### 1. Dockerfile

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 环境变量
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:create_app()"]
```

### 2. docker-compose.yml

```yaml
version: '3.8'

services:
  ai-backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - LLM_PROVIDER=openai
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=mysql://root:password@db:3306/study_seat
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./backend:/app
    restart: unless-stopped

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=study_seat
    volumes:
      - mysql-data:/var/lib/mysql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  mysql-data:
```

启动：

```bash
docker-compose up -d
```

---

## 监控与维护

### 1. 日志管理

```bash
# 查看实时日志
tail -f gunicorn.log

# 筛选AI模块日志
cat gunicorn.log | grep '"name":"ai"'

# 查看错误日志
cat gunicorn.log | grep '"level":"ERROR"'
```

### 2. 性能监控

关键指标：

- 响应时间（目标: < 3秒）
- LLM调用成功率（目标: > 95%）
- 缓存命中率
- 限流触发次数

### 3. 定期维护

```bash
# 清理过期会话（每天）
# 可添加到crontab
0 2 * * * python -c "from domain.ai.session_store import cleanup; cleanup()"

# 清理限流记录（每天）
0 2 * * * python -c "from domain.ai.rate_limiter import cleanup_rate_limit_records; cleanup_rate_limit_records()"
```

---

## 安全建议

### 1. API密钥管理

- ❌ 不要将API key提交到Git
- ✅ 使用环境变量或密钥管理服务
- ✅ 定期轮换API key
- ✅ 限制API key权限

### 2. 限流配置

```bash
# 生产环境建议的限流配置
AI_RATE_LIMIT_PER_USER=30       # 30次/分钟
AI_RATE_LIMIT_WINDOW=60

# 如果有大量用户，考虑使用Redis限流
SESSION_STORE_TYPE=redis
REDIS_URL=redis://localhost:6379/1
```

### 3. 错误处理

- ✅ 启用LLM降级策略（自动降级到关键词匹配）
- ✅ 设置合理的超时时间
- ✅ 记录详细的错误日志

---

## 成本优化

### 1. 减少LLM调用

```bash
# 启用缓存
# 相同查询使用缓存结果，5分钟有效

# 优先使用关键词匹配
LLM_INTENT_RECOGNITION=auto      # 只在必要时调用LLM

# 禁用LLM生成回复
USE_LLM_REPLY=false              # 使用模板回复
```

### 2. 选择合适的模型

| 模型 | 成本 | 速度 | 推荐场景 |
|------|------|------|---------|
| gpt-3.5-turbo | 低 | 快 | 生产环境推荐 |
| gpt-4 | 高 | 慢 | 高质量要求 |
| Mock | 免费 | 极快 | 开发测试 |

### 3. 监控API使用

```bash
# 查看LLM调用日志
cat gunicorn.log | grep '"message":"LLM API called"'

# 统计调用次数
cat gunicorn.log | grep '"message":"LLM API called"' | wc -l
```

---

## 故障排查

### 问题1: LLM调用失败

**症状**: 所有AI查询返回关键词匹配结果

**排查**:
1. 检查 `OPENAI_API_KEY` 是否正确
2. 检查网络连接
3. 查看错误日志
4. 验证OpenAI账户余额

**解决**: 系统会自动降级，不影响基本功能

### 问题2: 响应时间过长

**症状**: 用户等待时间 > 5秒

**排查**:
1. 检查LLM API响应时间
2. 检查数据库查询性能
3. 查看日志中的 `duration_ms`

**解决**:
- 启用缓存
- 调整超时配置
- 考虑使用更快的模型

### 问题3: 限流频繁触发

**症状**: 用户频繁收到429错误

**排查**:
1. 查看限流日志
2. 统计用户请求频率

**解决**:
- 调高限流阈值
- 使用Redis实现更精确的限流
- 在前端添加请求节流

---

## 更新部署

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 安装新依赖
pip install -r requirements.txt

# 3. 运行测试
pytest tests/domain/ai/ -v

# 4. 重启服务
sudo systemctl restart ai-backend

# 5. 验证
curl -X POST http://localhost:5000/api/v1/ai/chat \
  -H "Authorization: Bearer TOKEN" \
  -d '{"message": "测试消息"}'
```

---

## 回滚方案

```bash
# 1. 回滚代码
git checkout <previous-commit>

# 2. 恢复依赖
pip install -r requirements.txt

# 3. 重启服务
sudo systemctl restart ai-backend
```

---

## 联系支持

- 技术文档: [AI助手模块使用文档.md](./AI助手模块使用文档.md)
- 开发计划: [AI助手模块开发计划.md](./AI助手模块开发计划.md)
- Issue跟踪: GitHub Issues
