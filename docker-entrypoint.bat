@echo off
REM Nginx Manager Docker 入口脚本（Windows 版本）

echo ========================================
echo Nginx Manager 启动中...
echo ========================================

REM 等待数据库就绪（简化版）
echo 等待数据库就绪...
timeout /t 5 /nobreak >nul

echo 等待 Redis 就绪...
timeout /t 3 /nobreak >nul

REM 执行数据库迁移
echo 执行数据库迁移...
python manage.py migrate --noinput

REM 收集静态文件
echo 收集静态文件...
python manage.py collectstatic --noinput --clear

REM 创建超级用户（如果不存在）
if defined DJANGO_SUPERUSER_USERNAME if defined DJANGO_SUPERUSER_EMAIL if defined DJANGO_SUPERUSER_PASSWORD (
    echo 创建超级用户...
    python manage.py createsuperuser --noinput --username %DJANGO_SUPERUSER_USERNAME% --email %DJANGO_SUPERUSER_EMAIL% 2>nul || echo 超级用户已存在
)

REM 启动应用
echo ========================================
echo 启动 Gunicorn WSGI 服务器...
echo ========================================

REM 使用 gunicorn 启动 Django 应用
gunicorn nginx_manager.wsgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class gthread --threads 2 --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 50 --access-logfile /app/logs/access.log --error-logfile /app/logs/error.log --log-level info
