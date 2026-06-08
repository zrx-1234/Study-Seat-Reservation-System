# 生产环境后端镜像
ARG DOCKER_MIRROR=docker.1ms.run
FROM ${DOCKER_MIRROR}/library/python:3.11-slim

# 系统依赖（PyMySQL 的 cryptography 需要 build-essential & libffi）
# 使用清华镜像源加速 apt
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null || true \
 && apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        default-libmysqlclient-dev \
        pkg-config \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先拷贝依赖文件，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 拷贝项目代码
COPY . .

# 复制并赋权启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
