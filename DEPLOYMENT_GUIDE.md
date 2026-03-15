# Nginx Manager 生产环境部署指南

## 概述

本文档描述了如何使用 Docker 和 Docker Compose 将 Nginx Manager 部署到生产环境。

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 2+ CPU 核心
- 20GB+ 磁盘空间

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd nginx-manager
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要的配置：

```env
# Django 设置
SECRET_KEY=your-secret-key-here-change-in-production
DJANGO_ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost,127.0.0.1
DJANGO_ADMIN_URL=admin

# 数据库设置
DB_PASSWORD=strong-db-password-123

# Redis 设置
REDIS_PASSWORD=strong-redis-password-456

# 超级用户设置（首次启动时创建）
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@your-domain.com
DJANGO_SUPERUSER_PASSWORD=strong-admin-password-789

# 邮件设置（用于告警）
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Nginx Manager <noreply@your-domain.com>
ADMIN_EMAIL=admin@your-domain.com

# SSH 设置
SSH_CONNECT_TIMEOUT=10
SSH_COMMAND_TIMEOUT=30

# 监控设置
MONITORING_DATA_RETENTION_DAYS=30
LOG_DATA_RETENTION_DAYS=7

# 钉钉/企业微信告警（可选）
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
DINGTALK_SECRET=your-dingtalk-secret
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

**生成安全的 SECRET_KEY：**

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 3. 构建和启动服务

```bash
# 构建 Docker 镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f web
```

### 4. 验证部署

访问以下 URL 验证部署是否成功：

- 应用主页：http://localhost:8000/
- 管理后台：http://localhost:8000/admin/
- 健康检查：http://localhost:8000/health/

## 生产环境高级配置

### 使用 Nginx 反向代理（推荐）

生产环境建议使用 Nginx 作为反向代理：

```bash
# 使用包含 Nginx 的配置启动
docker-compose --profile with_nginx up -d
```

配置 SSL 证书（将证书文件放在 `./docker/nginx/ssl/`）：

```bash
mkdir -p docker/nginx/ssl
# 将您的证书文件复制到该目录
# fullchain.pem 和 privkey.pem
```

编辑 `docker/nginx/conf.d/app.conf` 配置 SSL。

### 数据备份

#### 自动备份脚本

创建 `backup.sh`：

```bash
#!/bin/bash

# 备份目录
BACKUP_DIR="/backup/nginx-manager"
mkdir -p $BACKUP_DIR

# 备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="nginx_manager_$DATE.sql"

# 备份 PostgreSQL 数据库
docker-compose exec -T db pg_dump -U nginx_user nginx_manager > "$BACKUP_DIR/$BACKUP_FILE"

# 压缩备份文件
gzip "$BACKUP_DIR/$BACKUP_FILE"

# 删除 7 天前的备份
find $BACKUP_DIR -name "nginx_manager_*.sql.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_DIR/${BACKUP_FILE}.gz"
```

添加定时任务：

```bash
chmod +x backup.sh
# 每天凌晨 2 点备份
(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/backup.sh") | crontab -
```

#### 恢复备份

```bash
# 解压备份文件
gunzip nginx_manager_20240101_020000.sql.gz

# 恢复数据库
docker-compose exec -T db psql -U nginx_user nginx_manager < nginx_manager_20240101_020000.sql
```

### 日志管理

日志文件位于 `./logs/` 目录：

- `django.log` - Django 应用日志
- `error.log` - 错误日志
- `access.log` - Gunicorn 访问日志

配置 Logrotate（自动日志轮转）：

```bash
# /etc/logrotate.d/nginx-manager
/path/to/nginx-manager/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 django django
    postrotate
        docker kill --signal=USR1 $(docker ps -q -f name=nginx_manager_web) 2>/dev/null || true
    endscript
}
```

### 性能调优

#### Gunicorn 调优

编辑 `docker-compose.yml` 中的 web 服务：

```yaml
web:
  command: >
    gunicorn nginx_manager.wsgi:application
      --bind 0.0.0.0:8000
      --workers 8  # CPU 核心数 * 2 + 1
      --worker-class gthread
      --threads 4
      --worker-connections 1000
      --timeout 120
      --keep-alive 5
      --max-requests 1000
      --max-requests-jitter 50
```

#### PostgreSQL 调优

编辑 `docker-compose.yml` 中的 db 服务：

```yaml
db:
  command: >
    postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c checkpoint_timeout=10min
      -c max_connections=200
```

### 监控和告警

#### 配置 Prometheus 监控（可选）

1. 在 `.env` 中启用：
   ```env
   ENABLE_PROMETHEUS=True
   ```

2. 访问指标：http://localhost:8000/metrics

#### 配置 uptime 监控

使用 UptimeRobot 或 Pingdom 监控：
- http://your-domain.com/health/

### 安全配置

#### 1. 修改默认密码

首次登录后，立即修改默认管理员密码。

#### 2. 配置防火墙

```bash
# 仅允许必要端口
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH
ufw enable
```

#### 3. 配置 fail2ban

```bash
# 安装 fail2ban
apt-get install fail2ban

# 创建配置
nano /etc/fail2ban/jail.local
```

添加以下内容：

```ini
[nginx-manager]
enabled = true
port = http,https
filter = nginx-manager
logpath = /path/to/nginx-manager/logs/access.log
maxretry = 5
bantime = 3600
findtime = 600
```

创建过滤器：

```bash
nano /etc/fail2ban/filter.d/nginx-manager.conf
```

```ini
[Definition]
failregex = ^<HOST> .* "POST /accounts/login/" 200 .* "Invalid username or password"
ignoreregex =
```

#### 4. 定期更新

```bash
# 更新系统和 Docker
docker-compose down
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# 清理旧镜像
docker image prune -a
```

## 服务管理

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart web

# 查看日志
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f db

# 进入容器
docker-compose exec web bash

# 执行 Django 命令
docker-compose exec web python manage.py <command>

# 查看服务状态
docker-compose ps

# 更新服务
docker-compose pull
docker-compose up -d --no-deps web
```

### 数据库维护

```bash
# 备份数据库
docker-compose exec db pg_dump -U nginx_user nginx_manager > backup.sql

# 进入数据库
docker-compose exec db psql -U nginx_user -d nginx_manager

# 清理旧数据
docker-compose exec web python manage.py cleanup_old_data
```

### Celery 任务管理

```bash
# 查看 Celery Worker 日志
docker-compose logs -f celery_worker

# 查看 Celery Beat 日志
docker-compose logs -f celery_beat

# 清空 Celery 队列
docker-compose exec redis redis-cli -a $REDIS_PASSWORD FLUSHALL

# 重启 Celery
docker-compose restart celery_worker celery_beat
```

## 故障排查

### 常见问题

#### 1. 数据库连接失败

```bash
# 检查数据库状态
docker-compose logs db

# 进入数据库容器
docker-compose exec db psql -U nginx_user -d nginx_manager

# 检查网络连接
docker-compose exec web nc -zv db 5432
```

#### 2. Redis 连接失败

```bash
# 检查 Redis 状态
docker-compose logs redis

# 测试 Redis 连接
docker-compose exec redis redis-cli ping
```

#### 3. 静态文件无法加载

```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput --clear

# 检查静态文件权限
docker-compose exec web ls -la /app/staticfiles/
```

#### 4. 内存不足

```bash
# 检查内存使用
docker stats

# 减少 Gunicorn Worker 数量
docker-compose exec web ps aux | grep gunicorn

# 重启服务释放内存
docker-compose restart
```

### 性能问题排查

```bash
# 查看数据库慢查询
docker-compose exec db psql -U nginx_user -d nginx_manager -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# 查看 Django 性能
docker-compose exec web python manage.py showmigrations

# 分析日志
docker-compose exec web python manage.py analyze_logs
```

## 扩展部署

### 多节点部署

使用 Docker Swarm 或 Kubernetes 进行多节点部署：

#### Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署 Stack
docker stack deploy -c docker-compose.yml nginx-manager

# 查看服务
docker stack services nginx-manager
```

#### Kubernetes

使用提供的 Kubernetes 配置文件：

```bash
# 创建命名空间
kubectl create namespace nginx-manager

# 部署 ConfigMap
kubectl apply -f k8s/configmap.yaml

# 部署 Secrets
kubectl apply -f k8s/secrets.yaml

# 部署应用
kubectl apply -f k8s/deployment.yaml

# 部署服务
kubectl apply -f k8s/service.yaml
```

## 许可证和支持

- 本项目基于 MIT 许可证
- 生产环境部署建议购买商业支持
- 定期备份和更新是生产环境的关键

## 更新日志

### v1.0.0 (2024-01-01)
- 初始生产环境部署方案
- 支持 Docker 和 Docker Compose
- 包含完整的高可用配置

---

**注意**：首次部署后，请立即修改所有默认密码，并配置 SSL 证书。