#!/bin/bash

# Nginx Manager Docker 入口脚本

set -e

echo "========================================"
echo "Nginx Manager 启动中..."
echo "========================================"

# 等待数据库就绪
echo "等待数据库就绪..."
until nc -z -w 2 $DB_HOST $DB_PORT; do
  echo "数据库连接失败，等待 2 秒后重试..."
  sleep 2
done
echo "数据库已就绪！"

# 等待 Redis 就绪
echo "等待 Redis 就绪..."
until nc -z -w 2 $REDIS_HOST $REDIS_PORT; do
  echo "Redis 连接失败，等待 2 秒后重试..."
  sleep 2
done
echo "Redis 已就绪！"

# 执行数据库迁移
echo "执行数据库迁移..."
python manage.py migrate --noinput

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput --clear

# 创建超级用户（如果不存在）
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "创建超级用户..."
    python manage.py createsuperuser --noinput --username $DJANGO_SUPERUSER_USERNAME --email $DJANGO_SUPERUSER_PASSWORD 2>/dev/null || echo "超级用户已存在"
fi

# 加载初始数据（如果需要）
# echo "加载初始数据..."
# python manage.py loaddata initial_data.json 2>/dev/null || echo "初始数据已加载或不存在"

# 启动应用
echo "========================================"
echo "启动 Gunicorn WSGI 服务器..."
echo "========================================"

# 使用 gunicorn 启动 Django 应用
exec gunicorn nginx_manager.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info \
    --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'
