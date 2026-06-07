# 自习座位预约系统 — 生产部署指南

> 容器化部署方案：Docker Compose 一键编排 **MySQL + Flask 后端 + 统一 Nginx 网关（含三个前端）**

---

## 1. 部署架构

```
                        ┌──────────────────────────┐
                        │      公网用户             │
                        └────────────┬─────────────┘
                                     │ HTTP :80
                                     ▼
                ┌─────────────────────────────────────────────┐
                │     ssr-gateway (Nginx)                     │
                │   ─ /          → landing 入口页              │
                │   ─ /admin/    → 管理端 SPA                 │
                │   ─ /student/  → 学生端 SPA                 │
                │   ─ /ai/       → AI 端 SPA                  │
                │   ─ /api/*     → 反代到 backend:5000        │
                └────────────────────┬────────────────────────┘
                                     │ ssr-net 内部网络
                ┌────────────────────▼────────────────────────┐
                │    ssr-backend (Gunicorn + Flask)           │
                │   ─ 4 worker 进程                            │
                │   ─ 启动时自动 migrate + seed                │
                └────────────────────┬────────────────────────┘
                                     │ ssr-net 内部网络
                ┌────────────────────▼────────────────────────┐
                │    ssr-mysql (MySQL 8.0)                    │
                │   ─ 数据卷 mysql_data 持久化                 │
                └─────────────────────────────────────────────┘
```

### URL 访问路径

| URL | 说明 | 当前状态 |
|------|------|---------|
| `http://<IP>/` | 项目 landing 入口页 | ✅ 已上线 |
| `http://<IP>/admin/` | 管理后台 | ✅ 已上线 |
| `http://<IP>/student/` | 学生端 | ⚠️ 开发中（仅登录页 + 占位） |
| `http://<IP>/ai/` | AI 智能助手 | ⚠️ 开发中（仅登录页 + 占位） |
| `http://<IP>/api/v1/*` | 后端 REST API | ✅ 部分接口完成 |

---

## 2. 服务器准备

### 2.1 系统要求
- Ubuntu 20.04+ / Debian 11+
- ≥ 2 vCPU、≥ 2 GB 内存、≥ 20 GB 磁盘
- 公网 IP，安全组放行 **80** 端口（如需 HTTPS 再开 443）

### 2.2 安装 Docker 和 Docker Compose

```bash
# 更新 apt
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sudo bash

# 启动 Docker 并设置开机自启
sudo systemctl enable --now docker

# （可选）将当前用户加入 docker 组，避免每次 sudo
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

---

## 3. 上传项目代码

### 方式 A：Git 克隆（推荐）
```bash
cd /opt
sudo git clone <你的仓库地址> study-seat-reservation
sudo chown -R $USER:$USER study-seat-reservation
cd study-seat-reservation
```

### 方式 B：本地打包上传
```bash
# 本地（Windows PowerShell 或 Git Bash）
tar -czf ssr.tar.gz --exclude=node_modules --exclude=__pycache__ --exclude=.git Study-Seat-Reservation-System
scp ssr.tar.gz user@<服务器IP>:/opt/

# 服务器
cd /opt && tar -xzf ssr.tar.gz && cd Study-Seat-Reservation-System
```

---

## 4. 配置环境变量

```bash
# 复制示例文件
cp .env.example .env

# 用编辑器修改 .env，**必须** 替换所有 "please-change" 字段
nano .env
```

生成强密钥的方法（任选一种）：
```bash
# 方法 1：openssl
openssl rand -hex 32

# 方法 2：python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

`.env` 关键字段说明：

| 变量 | 说明 | 示例 |
|------|------|------|
| `HTTP_PORT` | Nginx 对外端口 | `80` |
| `SECRET_KEY` | Flask session 密钥 | 64 字符随机串 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 64 字符随机串 |
| `DB_ROOT_PASSWORD` | MySQL root 密码 | 强密码 |
| `DB_USER` / `DB_PASSWORD` | 应用专用数据库账号 | `ssr_user` / 强密码 |
| `DB_NAME` | 数据库名 | `seat_reservation` |

---

## 5. 一键启动

```bash
# 构建镜像并后台启动所有服务（首次构建会拉取 Node/Python/MySQL/Nginx 镜像，约 5-10 分钟）
docker compose up -d --build

# 查看启动状态（等待约 30 秒，MySQL 初始化较慢）
docker compose ps

# 查看实时日志
docker compose logs -f backend
docker compose logs -f gateway
```

健康判断：
- `ssr-mysql` 状态显示 `(healthy)`
- `ssr-backend` 日志出现 `🚀 启动 Gunicorn 服务...` 和 `Listening at: http://0.0.0.0:5000`
- `ssr-gateway` 日志出现 `start worker process`

---

## 6. 访问验证

### 6.1 浏览器访问
打开 `http://<你的公网IP>/`，进入 landing 入口页，点击对应卡片进入各端。

### 6.2 默认登录账号
| 用户名 | 密码 | 适用端口 |
|--------|------|---------|
| `admin` | `123456` | 管理端（超级管理员） |
| `teacher01` | `123456` | 管理端（普通管理员） |
| `2025123456` | `123456` | 学生端 / AI 端 |

> **⚠️ 安全提示**：上线后**立即**修改默认密码！

### 6.3 API 健康检查
```bash
curl http://<你的公网IP>/api/v1/admin/auth/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'
```
应返回 200 和 `access_token`。

---

## 7. 常用运维命令

```bash
# 查看所有容器状态
docker compose ps

# 查看日志（最近 100 行）
docker compose logs --tail=100 backend
docker compose logs --tail=100 gateway
docker compose logs --tail=100 mysql

# 进入后端容器
docker compose exec backend bash

# 进入 MySQL 容器
docker compose exec mysql mysql -u root -p

# 重启某个服务
docker compose restart backend

# 仅重新构建 gateway（前端代码更新后）
docker compose up -d --build gateway

# 仅重新构建 backend（后端代码更新后）
docker compose up -d --build backend

# 停止所有服务（保留数据）
docker compose down

# 停止并删除所有数据（⚠️ 慎用）
docker compose down -v

# 更新代码后重新部署
git pull
docker compose up -d --build
```

---

## 8. 前端开发与部署模式说明

### 8.1 三个前端的 base 路径

每个前端项目的 `vite.config.js` 已配置 `base` 字段：

| 前端 | `base` | 部署后访问路径 |
|------|--------|---------------|
| `frontend/admin` | `/admin/` | `http://<IP>/admin/` |
| `frontend/student` | `/student/` | `http://<IP>/student/` |
| `frontend/ai` | `/ai/` | `http://<IP>/ai/` |

### 8.2 本地开发（不变）

各前端依然可以独立 `npm run dev`：

```bash
# 管理端：http://localhost:8080
cd frontend/admin && npm install && npm run dev

# 学生端：http://localhost:3000
cd frontend/student && npm install && npm run dev

# AI 端：http://localhost:3001
cd frontend/ai && npm install && npm run dev
```

> 开发服务器内不带 `/admin/` 等前缀；Vite 的 `base` 配置只在生产构建时生效。

### 8.3 学生端 / AI 端的临时占位

当前学生端和 AI 端业务页面尚未开发完成，所有受保护路由统一渲染 `Placeholder.vue` 占位页，标注负责小组和进度。
对应小组开发完成后，只需用真实业务组件替换路由的 `component: Placeholder` 即可，不影响部署架构。

---

## 9. 数据库备份

### 9.1 手动备份
```bash
docker compose exec -T mysql \
  mysqldump -u root -p${DB_ROOT_PASSWORD} seat_reservation \
  > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 9.2 自动备份（cron）
```bash
# 编辑 crontab
crontab -e

# 每天凌晨 3 点备份
0 3 * * * cd /opt/Study-Seat-Reservation-System && docker compose exec -T mysql mysqldump -u root -p$(grep DB_ROOT_PASSWORD .env | cut -d= -f2) seat_reservation > /opt/backups/ssr_$(date +\%Y\%m\%d).sql
```

### 9.3 恢复
```bash
docker compose exec -T mysql \
  mysql -u root -p${DB_ROOT_PASSWORD} seat_reservation \
  < backup_20260605.sql
```

---

## 10. 故障排查

### 10.1 后端无法连接 MySQL
```bash
# 检查 MySQL 是否就绪
docker compose exec mysql mysqladmin -u root -p${DB_ROOT_PASSWORD} ping

# 在后端容器内测试
docker compose exec backend python -c "
from app import create_app
from extensions import db
app = create_app()
with app.app_context():
    print(db.engine.connect())
"
```

### 10.2 前端 404 或资源加载失败
- 确认 `vite.config.js` 中 `base` 与 Nginx 中的 `location` 路径一致（如 admin 必须是 `/admin/`，末尾斜杠不能少）
- 浏览器开发者工具 → Network 看资源请求路径是否带 `/admin/` 前缀

### 10.3 前端访问不到 API
```bash
# 在 gateway 容器内测试是否能访问后端
docker compose exec gateway wget -qO- \
  --post-data='{"username":"admin","password":"123456"}' \
  --header='Content-Type: application/json' \
  http://backend:5000/api/v1/admin/auth/login
```

### 10.4 docker-entrypoint.sh 报错 "no such file or directory"
通常是 Windows CRLF 换行问题。在服务器上执行：
```bash
sudo apt install -y dos2unix
dos2unix backend/docker-entrypoint.sh
docker compose build backend
docker compose up -d
```
（项目已配置 `.gitattributes` 自动处理，仅在意外情况需手动修复）

### 10.5 端口 80 被占用
```bash
# 查找占用进程
sudo lsof -i:80
# 或停止 nginx/apache 等
sudo systemctl stop nginx
sudo systemctl stop apache2

# 或修改 .env 中的 HTTP_PORT=8080，从 8080 端口访问
```

### 10.6 gateway 镜像构建很慢
首次构建会下载 Node 镜像和三个前端的依赖（约 200-300MB），属正常现象。后续构建会利用缓存层快得多。

---

## 11. 后续 HTTPS 升级（可选）

如未来需要 HTTPS：

1. 域名解析到服务器 IP
2. 安装 Certbot：
   ```bash
   sudo apt install -y certbot
   sudo certbot certonly --standalone -d yourdomain.com
   ```
3. 修改 `gateway/nginx.conf` 添加 443 监听 + SSL 配置
4. 修改 `docker-compose.yml`：
   - 增加 `ports: ["443:443"]`
   - 挂载证书目录 `/etc/letsencrypt:/etc/letsencrypt:ro`
5. `docker compose up -d --force-recreate gateway`

---

## 附：项目结构

```
Study-Seat-Reservation-System/
├── docker-compose.yml          # 服务编排
├── .env.example                # 环境变量模板
├── .env                        # 本地配置（不提交）
├── DEPLOYMENT.md               # 本文档
│
├── backend/                    # Flask 后端
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   ├── gunicorn.conf.py
│   ├── .dockerignore
│   └── ...
│
├── frontend/
│   ├── admin/                  # 管理端（已完成）
│   ├── student/                # 学生端（占位中）
│   └── ai/                     # AI 端（占位中）
│
└── gateway/                    # 统一前端网关
    ├── Dockerfile              # 多阶段构建三个前端
    ├── nginx.conf              # Nginx 配置（按路径分发）
    ├── landing/
    │   └── index.html          # 入口 landing 页
    └── .dockerignore
```
