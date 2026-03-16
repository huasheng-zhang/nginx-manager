# 路由规则无法访问问题排查与解决方案

## 问题描述

在nginx-manager中配置了路由规则，但是通过代理节点无法访问后端服务。

**示例配置：**
- 规则名称：test
- 所属节点：nginx-1
- 域名：113.45.19.124
- 路径：/
- 类型：代理转发
- 状态：启用

## 根本原因

**重要发现**：nginx-manager目前没有自动将数据库中的路由规则转换为Nginx配置文件并应用到Nginx服务器的功能。

路由规则只是保存在数据库中，但没有生成实际的Nginx配置，因此Nginx无法按照规则进行代理转发。

## 解决方案

### 方案1：使用新创建的配置生成功能（推荐）

我已经为你创建了配置生成和应用功能。请按照以下步骤操作：

#### 步骤1：检查路由规则配置

首先，确保你的路由规则配置完整：

```bash
cd C:\Users\admin\WorkBuddy\20260313103247
python test_config_generation.py
```

**常见问题：**
- ❌ 路由规则缺少"上游主机"（upstream_host）
- ❌ 路由规则缺少"上游端口"（upstream_port）

**解决方法：**
1. 登录nginx-manager Web界面
2. 进入"路由规则"页面
3. 编辑你的路由规则
4. 填写完整的后端服务信息：
   - **上游主机**：后端服务器的IP地址或域名（如：192.168.1.200）
   - **上游端口**：后端服务的端口（如：8080）

#### 步骤2：通过API应用配置

使用curl或任何API工具调用配置同步API：

```bash
# 获取节点ID
curl -X GET http://your-nginx-manager/api/v1/agent/nodes/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预览配置（不应用）
curl -X GET http://your-nginx-manager/api/v1/agent/nodes/1/preview/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 应用配置到节点
curl -X POST http://your-nginx-manager/api/v1/agent/nodes/1/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 步骤3：验证配置

1. 检查Nginx配置是否生成正确：
```bash
# 在Nginx节点上执行
nginx -t
```

2. 查看Nginx错误日志：
```bash
tail -f /var/log/nginx/error.log
```

3. 测试访问：
```bash
curl -v http://113.45.19.124/
```

### 方案2：手动配置Nginx（临时解决方案）

如果自动配置功能有问题，可以手动配置Nginx：

#### 步骤1：连接到Nginx节点

```bash
ssh root@nginx-node-ip
```

#### 步骤2：编辑Nginx配置

```bash
vi /etc/nginx/nginx.conf
```

#### 步骤3：添加server块

```nginx
http {
    # ... 其他配置 ...

    server {
        listen 80;
        server_name 113.45.19.124;

        location / {
            proxy_pass http://YOUR_BACKEND_HOST:YOUR_BACKEND_PORT;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

**注意替换：**
- `YOUR_BACKEND_HOST`：你的后端服务IP或域名
- `YOUR_BACKEND_PORT`：你的后端服务端口

#### 步骤4：测试并应用配置

```bash
# 测试配置
nginx -t

# 重载Nginx
nginx -s reload
```

### 方案3：完整的自动配置流程（开发建议）

为了实现完全自动化，建议添加以下功能：

1. **规则保存时自动触发配置生成**（使用Django signals）
2. **定时同步配置**（使用Celery beat）
3. **配置版本管理**（回滚功能）
4. **批量应用配置**

示例代码：

```python
# 在models.py中添加signal
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=RouteRule)
def apply_route_rule_on_save(sender, instance, **kwargs):
    """保存路由规则后自动应用配置"""
    from .config_generator import sync_node_config
    sync_node_config(instance.node_id)
```

## 详细的排查步骤

### 1. 检查路由规则配置

在nginx-manager服务器上执行：

```python
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nginx_manager.settings')
django.setup()

from nginx.models import RouteRule

# 查看所有路由规则
rules = RouteRule.objects.all()
for rule in rules:
    print(f"规则: {rule.name}")
    print(f"  节点: {rule.node.name}")
    print(f"  域名: {rule.domain}")
    print(f"  路径: {rule.path}")
    print(f"  类型: {rule.rule_type}")
    print(f"  上游: {rule.upstream_host}:{rule.upstream_port}")
    print(f"  状态: {'启用' if rule.is_active else '禁用'}")
    print("-" * 50)
```

### 2. 检查Nginx节点状态

```python
from nginx.models import NginxNode
from nginx.agent import create_nginx_agent

nodes = NginxNode.objects.all()
for node in nodes:
    print(f"节点: {node.name}")
    print(f"  主机: {node.host}:{node.port}")
    print(f"  SSH: {node.ssh_username}@{node.host}:{node.ssh_port}")
    print(f"  状态: {node.get_status_display()}")
    
    # 测试连接
    agent = create_nginx_agent(node)
    if agent.connect():
        print("  ✓ SSH连接成功")
        agent.disconnect()
    else:
        print("  ❌ SSH连接失败")
```

### 3. 手动测试后端服务

在Nginx节点上测试后端服务是否可达：

```bash
# 测试后端服务
curl -v http://backend-host:backend-port/

# 检查DNS解析
nslookup backend-host

# 检查端口连通性
telnet backend-host backend-port
```

### 4. 检查Nginx日志

```bash
# 查看错误日志
tail -n 50 /var/log/nginx/error.log

# 查看访问日志
tail -n 50 /var/log/nginx/access.log
```

### 5. 检查防火墙

```bash
# 检查防火墙状态
firewall-cmd --state

# 查看开放的端口
firewall-cmd --list-ports

# 临时关闭防火墙测试（生产环境慎用）
systemctl stop firewalld
```

## 常见问题与解决

### 问题1：upstream_host 和 upstream_port 为空

**症状**：配置生成失败，提示缺少上游服务器

**解决**：在Web界面编辑路由规则，填写后端服务的IP和端口

### 问题2：SSH连接失败

**症状**：无法应用配置到Nginx节点

**解决**：
1. 检查SSH端口是否开放
2. 验证SSH用户名和密码/密钥
3. 确认Nginx节点IP地址正确

### 问题3：Nginx配置测试失败

**症状**：nginx -t 报错

**解决**：
1. 检查配置语法
2. 查看错误信息
3. 恢复备份配置：`cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf`

### 问题4：后端服务无法访问

**症状**：Nginx返回502 Bad Gateway

**解决**：
1. 确认后端服务正在运行
2. 检查后端服务端口是否正确
3. 检查Nginx节点到后端服务的网络连通性
4. 检查后端的防火墙设置

### 问题5：域名解析失败

**症状**：server_name 无效或无法访问

**解决**：
1. 使用IP地址代替域名测试
2. 检查DNS设置
3. 确保域名指向正确的Nginx节点IP

## 配置示例

### 示例1：代理到后端API服务

```python
# 路由规则配置
{
    "name": "api-proxy",
    "domain": "113.45.19.124",
    "path": "/api/",
    "rule_type": "proxy",
    "upstream_host": "192.168.1.200",  # 后端API服务器
    "upstream_port": 8080,              # 后端API端口
    "is_active": True
}
```

访问：http://113.45.19.124/api/users -> 代理到 http://192.168.1.200:8080/api/users

### 示例2：代理到Web应用

```python
# 路由规则配置
{
    "name": "web-app",
    "domain": "113.45.19.124",
    "path": "/",
    "rule_type": "proxy",
    "upstream_host": "192.168.1.201",  # Web应用服务器
    "upstream_port": 3000,              # Web应用端口
    "is_active": True
}
```

访问：http://113.45.19.124/ -> 代理到 http://192.168.1.201:3000/

### 示例3：静态文件服务

```python
# 路由规则配置
{
    "name": "static-files",
    "domain": "113.45.19.124",
    "path": "/static/",
    "rule_type": "static",
    "root_path": "/var/www/static",     # 静态文件目录
    "is_active": True
}
```

访问：http://113.45.19.124/static/image.png -> 返回 /var/www/static/image.png

## 验证成功的标准

1. ✅ 路由规则配置完整（upstream_host和upstream_port已填写）
2. ✅ Nginx配置生成成功
3. ✅ Nginx配置测试通过（nginx -t）
4. ✅ Nginx服务已重载（nginx -s reload）
5. ✅ 防火墙允许访问Nginx端口（80/443）
6. ✅ 可以通过curl访问后端服务
7. ✅ 浏览器可以正常访问代理地址

## 技术支持

如果问题仍然存在，请提供以下信息：

1. 路由规则的完整配置（包括upstream_host和upstream_port）
2. Nginx节点的SSH连接测试结果
3. 手动生成的Nginx配置（test_config_generation.py的输出）
4. Nginx错误日志内容
5. curl访问的详细输出（curl -v http://113.45.19.124/）

## 总结

**核心问题**：路由规则需要转换为Nginx配置并应用到Nginx服务器

**解决方案**：
1. 确保路由规则配置完整（特别是upstream_host和upstream_port）
2. 使用配置生成功能生成Nginx配置
3. 应用配置到Nginx节点
4. 验证配置并测试访问

**推荐流程**：
配置规则 → 生成配置 → 测试配置 → 应用配置 → 验证访问
