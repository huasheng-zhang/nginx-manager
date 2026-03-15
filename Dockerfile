# 使用 Python 3.11  slim 版本作为基础镜像
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=nginx_manager.settings_production

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gcc \
        python3-dev \
        libpq-dev \
        ssh \
        openssh-client \
        cron \
        curl \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 安装 gunicorn 用于生产环境
RUN pip install --no-cache-dir gunicorn psycopg2-binary redis celery

# 复制项目代码
COPY . /app/

# 创建静态文件和媒体文件目录
RUN mkdir -p /app/staticfiles /app/media /app/logs

# 收集静态文件（在生产环境中运行）
# RUN python manage.py collectstatic --noinput

# 创建非 root 用户
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app

# 切换到非 root 用户
USER django

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# 启动命令
CMD ["./docker-entrypoint.sh"]
