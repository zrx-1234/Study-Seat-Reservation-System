# ============================================================
# 统一前端网关镜像
# 多阶段构建：分别构建 admin / student / ai 三个前端
# 最终用 Nginx 托管全部静态资源 + 反代后端 API
# ============================================================

# ---------- 阶段 1：构建 admin 前端 ----------
FROM node:20-alpine AS build-admin
WORKDIR /build
COPY frontend/admin/package*.json ./
RUN npm config set registry https://registry.npmmirror.com && npm install
COPY frontend/admin/ ./
RUN npm run build

# ---------- 阶段 2：构建 student 前端 ----------
FROM node:20-alpine AS build-student
WORKDIR /build
COPY frontend/student/package*.json ./
RUN npm config set registry https://registry.npmmirror.com && npm install
COPY frontend/student/ ./
RUN npm run build

# ---------- 阶段 3：构建 ai 前端 ----------
FROM node:20-alpine AS build-ai
WORKDIR /build
COPY frontend/ai/package*.json ./
RUN npm config set registry https://registry.npmmirror.com && npm install
COPY frontend/ai/ ./
RUN npm run build

# ---------- 阶段 4：Nginx 网关 ----------
FROM nginx:1.25-alpine

# 删除默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 拷贝自定义 Nginx 配置
COPY gateway/nginx.conf /etc/nginx/conf.d/default.conf

# 拷贝三个前端构建产物到对应子目录
COPY --from=build-admin   /build/dist /usr/share/nginx/html/admin
COPY --from=build-student /build/dist /usr/share/nginx/html/student
COPY --from=build-ai      /build/dist /usr/share/nginx/html/ai

# 拷贝 landing 入口页
COPY gateway/landing/index.html /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
