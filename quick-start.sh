#!/bin/bash

# Nginx Manager Docker 快速启动脚本

set -e

echo "=========================================="
echo "Nginx Manager Docker 快速启动"
echo "=========================================="

# 检查 Docker 和 Docker Compose
echo "检查环境..."
if ! command -v docker &> /dev/null; then
    echo "错误：未安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误：未安装 Docker Compose"
    exit 1
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "创建配置文件 .env..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "请编辑 .env 文件并设置密码"
        echo "重要：必须修改以下配置："
        echo "  - SECRET_KEY"
        echo "  - DB_PASSWORD"
        echo "  - REDIS_PASSWORD"
        echo "  - DJANGO_SUPERUSER_PASSWORD"
        exit 1
    else
        echo "错误：找不到 .env.example 文件"
        exit 1
    fi
fi

# 构建镜像
echo "构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务就绪
echo "等待服务就绪..."
sleep 30

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 显示访问信息
echo ""
echo "=========================================="
echo "启动完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - 应用主页：http://localhost:8000/"
echo "  - 管理后台：http://localhost:8000/admin/"
echo ""
echo "默认管理员账号："
echo "  - 用户名：admin（可在 .env 中修改）"
echo "  - 密码：在 .env 中设置的 DJANGO_SUPERUSER_PASSWORD"
echo ""
echo "查看日志："
echo "  docker-compose logs -f web"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo ""
echo "=========================================="
