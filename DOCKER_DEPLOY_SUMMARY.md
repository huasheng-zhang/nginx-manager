# Nginx Manager Docker 部署总结

## 📦 已创建的 Docker 部署文件

### 核心配置文件

1. **Dockerfile**
   - 基于 Python 3.11-slim
   - 包含所有系统依赖（PostgreSQL 客户端、SSH、Cron 等）
   - 使用 Gunicorn 作为 WSGI 服务器
   - 非 root 用户运行，提高安全性

2. **docker-compose.yml**
   - 完整的多服务架构：
     - PostgreSQL 数据库
     - Redis 缓存和消息队列
     - Django Web 应用
     - Celery Worker（异步任务）
     - Celery Beat（定时任务）
     - Nginx 反向代理（可选）
   - 健康检查机制
   - 数据持久化卷

3. **nginx_manager/settings_production.py**
   - 生产环境专用 Django 配置
   - PostgreSQL 数据库配置
   - Redis 缓存配置
   - Celery 异步任务配置
   - 完整的日志系统
   - 性能优化设置
   - 安全配置（HTTPS、Cookie、HSTS）

### 启动脚本

4. **docker-entrypoint.sh**（Linux）
5. **docker-entrypoint.bat**（Windows）
   - 自动等待数据库和 Redis 就绪
   - 自动执行数据库迁移
   - 自动收集静态文件
   - 自动创建超级用户
   - 启动 Gunicorn 服务器

### 配置模板

6. **.env.example**
   - 完整的环境变量配置模板
   - 包含所有必要的配置项
   - 详细的注释说明

7. **docker/nginx/nginx.conf**
   - Nginx 主配置文件
   - 性能优化（Gzip、缓存、连接数）
   - 安全头部设置

8. **docker/nginx/conf.d/app.conf**
   - 应用服务器配置
   - 静态文件和媒体文件处理
   - WebSocket 支持
   - SSL/TLS 配置（已注释）

### 文档和工具

9. **DEPLOYMENT_GUIDE.md**
   - 完整的生产环境部署指南
   - 快速开始步骤
   - 高级配置选项
   - 性能调优指南
   - 故障排查手册

10. **quick-start.sh**
    - 一键启动脚本
    - 环境检查
    - 自动配置

11. **.dockerignore**
    - Docker 构建忽略文件
    - 减少镜像大小
    - 提高构建速度

## 🚀 生产环境部署步骤

### 方式一：快速部署（推荐）

```bash
# 1. 进入项目目录
cd nginx-manager

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置密码和域名

# 3. 运行快速启动脚本
./quick-start.sh
```

### 方式二：手动部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f web

# 4. 检查状态
docker-compose ps
```

### 方式三：使用 Nginx 反向代理

```bash
# 创建 SSL 证书目录
mkdir -p docker/nginx/ssl

# 将证书文件放入 ssl 目录
# fullchain.pem 和 privkey.pem

# 使用 with_nginx 配置启动
docker-compose --profile with_nginx up -d
```

## 🔧 必须修改的配置

### 1. 环境变量 (.env)

在部署前，必须修改以下配置：

```env
# 必须修改！
SECRET_KEY=使用命令生成随机密钥
DB_PASSWORD=强数据库密码
REDIS_PASSWORD=强 Redis 密码
DJANGO_SUPERUSER_PASSWORD=强管理员密码

# 建议修改
DJANGO_ALLOWED_HOSTS=您的域名
ADMIN_EMAIL=管理员邮箱
EMAIL_HOST_USER=邮件发送账号
EMAIL_HOST_PASSWORD=邮件发送密码
```

生成随机密钥：
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2. 域名和 SSL

如果使用 Nginx 反向代理：

1. 编辑 `docker/nginx/conf.d/app.conf`
2. 修改 `server_name` 为您的域名
3. 配置 SSL 证书路径
4. 启用 HTTPS

## 📊 服务架构

```
┌─────────────────┐
│   Nginx (可选)  │  - 反向代理和负载均衡
│   (端口 80/443) │  - SSL/TLS 终端
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Django Web     │  - 主应用
│  (端口 8000)    │  - Gunicorn WSGI
└────────┬────────┘
         │
         ├──────→ ┌─────────────────┐
         │        │  PostgreSQL     │  - 数据持久化
         │        │  (端口 5432)    │  - 主数据库
         │        └─────────────────┘
         │
         ├──────→ ┌─────────────────┐
         │        │  Redis          │  - 缓存
         │        │  (端口 6379)    │  - 消息队列
         │        └─────────────────┘
         │
         ├──────→ ┌─────────────────┐
         │        │  Celery Worker  │  - 异步任务
         │        │                 │  - 日志处理
         │        └─────────────────┘
         │
         └──────→ ┌─────────────────┐
                  │  Celery Beat    │  - 定时任务
                  │                 │  - 监控告警
                  └─────────────────┘
```

## 🔐 安全建议

### 1. 立即修改默认密码
- 数据库密码
- Redis 密码
- Django 管理员密码
- SSH 密钥

### 2. 配置 SSL/TLS
- 使用 Let's Encrypt 免费证书
- 或购买商业证书
- 启用 HSTS

### 3. 防火墙设置
```bash
# 仅开放必要端口
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH
```

### 4. 定期备份
```bash
# 备份脚本
./backup.sh

# 或使用 cron 定时备份
0 2 * * * /path/to/backup.sh
```

### 5. 日志监控
```bash
# 查看应用日志
docker-compose logs -f web

# 查看错误日志
tail -f logs/error.log
```

## 📈 性能调优

### Gunicorn 调优

根据服务器配置调整：

```yaml
# CPU 核心数 * 2 + 1
workers: 8

# 每个 worker 线程数
threads: 4

# 最大请求数（防止内存泄漏）
max_requests: 1000
```

### PostgreSQL 调优

```yaml
shared_buffers: 256MB
effective_cache_size: 1GB
max_connections: 200
```

### Redis 调优

```yaml
maxmemory: 512mb
maxmemory-policy: allkeys-lru
```

## 🐛 故障排查

### 问题 1：数据库连接失败

**症状**：`Connection refused`

**解决**：
```bash
# 检查数据库状态
docker-compose logs db

# 重启数据库
docker-compose restart db

# 等待 30 秒后重启 web
docker-compose restart web
```

### 问题 2：静态文件无法加载

**症状**：CSS/JS 404 错误

**解决**：
```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput --clear

# 检查 Nginx 配置
docker-compose exec nginx nginx -t
```

### 问题 3：内存不足

**症状**：容器频繁重启

**解决**：
```bash
# 减少 worker 数量
docker-compose exec web ps aux

# 限制容器内存
docker-compose.yml:
  web:
    mem_limit: 2g
```

## 🔄 更新和升级

### 更新应用

```bash
# 1. 停止服务
docker-compose down

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建
docker-compose build --no-cache

# 4. 启动服务
docker-compose up -d

# 5. 清理旧镜像
docker image prune -a
```

### 数据库迁移

```bash
# 自动迁移
docker-compose exec web python manage.py migrate --noinput

# 检查迁移状态
docker-compose exec web python manage.py showmigrations
```

## 📚 常用命令

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

# 进入容器
docker-compose exec web bash

# 执行 Django 命令
docker-compose exec web python manage.py <command>

# 查看状态
docker-compose ps

# 查看资源使用
docker stats
```

## 🎯 访问应用

部署完成后，通过以下地址访问：

- **应用主页**：http://localhost:8000/
- **管理后台**：http://localhost:8000/admin/
- **健康检查**：http://localhost:8000/health/

### 默认管理员账号

首次启动时自动创建：
- **用户名**：admin（可在 .env 中修改）
- **密码**：在 .env 中设置的 `DJANGO_SUPERUSER_PASSWORD`

### 首次登录后必做

1. 修改默认管理员密码
2. 配置 Nginx 节点
3. 设置告警规则
4. 配置 SSL 证书（如使用 Nginx 代理）

## 📞 技术支持

- **文档**：查看 DEPLOYMENT_GUIDE.md 获取详细说明
- **日志**：检查 logs/ 目录下的日志文件
- **问题**：提交 Issue 到项目仓库

---

**重要提示**：
1. 生产环境务必修改所有默认密码
2. 定期备份数据
3. 启用 SSL/TLS 加密
4. 配置防火墙规则
5. 监控日志和性能
