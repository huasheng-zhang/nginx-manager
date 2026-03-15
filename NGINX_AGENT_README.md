# Nginx节点管理Agent使用文档

## 功能概述

Nginx节点管理Agent是一个通过SSH连接到Nginx服务器并执行管理命令的模块，集成在Django Web界面中，可以通过前端页面直接管理Nginx节点。

## 功能特点

- **SSH远程管理**: 通过SSH协议安全连接Nginx节点
- **节点状态监控**: 实时检查Nginx运行状态
- **服务控制**: 支持启动、停止、重启、重载配置等操作
- **配置检查**: 自动检查Nginx配置文件语法
- **多认证方式**: 支持密码认证和SSH密钥认证
- **前端集成**: 无缝集成到现有的Django管理界面

## 安装要求

### Python依赖

```bash
pip install paramiko>=3.0.0
```

已自动添加到 `requirements.txt` 中：
```
Django>=6.0.0
paramiko>=3.0.0
```

### SSH配置

确保Nginx节点服务器：
1. 已安装OpenSSH服务器
2. 允许SSH远程登录
3. 已安装Nginx服务
4. 提供SSH登录凭证（用户名/密码或SSH密钥）

## 配置说明

### SSH认证配置

在 `nginx/agent.py` 文件中，可以配置SSH连接参数：

```python
def create_nginx_agent(node) -> Optional[NginxAgent]:
    """
    根据Nginx节点对象创建Agent
    """
    # 从环境变量或配置文件读取SSH配置
    import os
    
    ssh_username = os.environ.get('NGINX_SSH_USER', 'root')
    ssh_password = os.environ.get('NGINX_SSH_PASSWORD', None)
    ssh_key_path = os.environ.get('NGINX_SSH_KEY_PATH', None)
    
    return NginxAgent(
        host=node.host,
        port=22,  # SSH端口
        username=ssh_username,
        password=ssh_password,
        key_path=ssh_key_path
    )
```

### 配置方式

1. **环境变量方式**（推荐）:
   ```bash
   export NGINX_SSH_USER='root'
   export NGINX_SSH_PASSWORD='your_password'
   # 或者使用SSH密钥
   export NGINX_SSH_KEY_PATH='/path/to/private/key'
   ```

2. **数据库配置方式**（可扩展）:
   可以在 `NginxNode` 模型中添加SSH凭证字段，将认证信息存储在数据库中。

## 使用方法

### 1. 添加Nginx节点

1. 登录Django管理后台
2. 导航到 "Nginx节点" 页面
3. 点击 "添加节点" 按钮
4. 填写节点信息：
   - 节点名称：自定义标识名称
   - 主机地址：Nginx服务器IP或域名
   - 端口：Nginx服务端口（默认80）
   - 配置文件路径：Nginx配置文件路径（默认 `/etc/nginx/nginx.conf`）
   - 描述：可选的节点描述

### 2. 测试节点连接

在节点列表或详情页面，点击 "测试连接" 按钮，验证SSH连接是否正常。

### 3. 检查节点状态

点击 "检查状态" 按钮，系统会：
1. 检查Nginx进程是否在运行
2. 验证Nginx配置文件语法
3. 检查Nginx是否在监听端口
4. 获取Nginx版本和配置信息

### 4. 控制Nginx服务

**启动Nginx**：
- 点击 "启动" 按钮
- 系统会尝试使用 `nginx` 命令启动服务
- 如果失败，会尝试 `systemctl start nginx` 或 `service nginx start`

**停止Nginx**：
- 点击 "停止" 按钮
- 系统会尝试使用 `nginx -s quit` 优雅停止
- 如果失败，会尝试 `systemctl stop nginx` 或 `service nginx stop`

**重启Nginx**：
- 点击 "重启" 按钮
- 先停止服务，等待2秒后重新启动

**重载配置**：
- 点击 "重载配置" 按钮
- 先检查配置文件语法
- 然后使用 `nginx -s reload` 重新加载配置
- 如果失败，会尝试 `systemctl reload nginx`

## API接口

### 节点管理API

**URL**: `/nginx/api/nodes/<node_id>/<action>/`

**方法**: `POST`

**参数**:
- `node_id`: Nginx节点ID
- `action`: 操作类型
  - `test`: 测试连接
  - `status`: 检查状态
  - `start`: 启动Nginx
  - `stop`: 停止Nginx
  - `restart`: 重启Nginx
  - `reload`: 重载配置

**响应示例**:

```json
// 成功响应
{
    "success": true,
    "message": "Nginx启动成功",
    "output": "Nginx启动成功"
}

// 失败响应
{
    "success": false,
    "message": "Nginx启动失败",
    "error": "错误信息"
}

// 状态检查响应
{
    "success": true,
    "status": "active",
    "status_display": "Nginx运行正常",
    "info": {
        "version": "nginx version: nginx/1.18.0",
        "config_path": "/etc/nginx/nginx.conf",
        "error_log_path": "/var/log/nginx/error.log",
        "access_log_path": "/var/log/nginx/access.log"
    }
}
```

## 前端界面

### 节点列表页面 (`/nginx/nodes/`)

- **搜索筛选**: 支持按节点名称、主机、状态筛选
- **快速操作**: 每个节点提供操作按钮组
  - 查看详情
  - 测试连接
  - 检查状态
  - 启动/停止/重启/重载配置
  - 编辑/删除节点

### 节点详情页面 (`/nginx/nodes/<pk>/`)

- **基本信息**: 显示节点配置和状态
- **节点控制**: 提供完整的控制面板
- **关联规则**: 显示该节点下的所有规则
  - 路由规则
  - 限流规则
  - 重定向规则
  - IP封禁规则

### 状态检查模态框

点击 "检查状态" 后，弹出模态框显示：
- Nginx运行状态
- Nginx版本信息
- 配置文件路径
- 日志文件路径

## 错误处理

### 常见错误及解决方案

1. **SSH连接失败**
   - 检查SSH端口是否开放
   - 验证用户名和密码/SSH密钥
   - 检查防火墙设置

2. **Nginx启动失败**
   - 检查Nginx是否已安装
   - 验证配置文件语法：`nginx -t`
   - 检查端口是否被占用

3. **权限不足**
   - 确保SSH用户有权限执行Nginx命令
   - 检查sudo权限（如需）
   - 验证Nginx配置文件权限

### 日志记录

Agent会记录所有操作日志：
- 成功操作：INFO级别
- 失败操作：ERROR级别
- 异常信息：完整的堆栈跟踪

日志配置：
```python
import logging
logger = logging.getLogger(__name__)
```

## 安全建议

1. **SSH安全**: 使用SSH密钥认证代替密码认证
2. **最小权限**: 使用具有最小必要权限的用户
3. **网络隔离**: 将Nginx管理网络与公网隔离
4. **审计日志**: 记录所有管理操作
5. **凭证管理**: 不要在代码中硬编码密码，使用环境变量或密钥管理系统

## 扩展功能

可以基于Agent扩展以下功能：

1. **批量操作**: 同时管理多个Nginx节点
2. **配置同步**: 从Web界面推送Nginx配置
3. **性能监控**: 收集Nginx性能指标
4. **日志查看**: 实时查看Nginx日志
5. **告警通知**: 节点状态异常时发送通知

## 技术架构

```
Django Web界面
      ↓
  Nginx Views
      ↓
  Nginx Agent (SSH)
      ↓
  Paramiko Library
      ↓
  Nginx Node (SSH Server)
      ↓
  Nginx Commands
```

## 支持的Nginx命令

Agent支持以下Nginx管理方式：

1. **直接命令**
   - `nginx`: 启动Nginx
   - `nginx -s quit`: 优雅停止
   - `nginx -s reload`: 重载配置
   - `nginx -t`: 检查配置

2. **Systemd管理**
   - `systemctl start/stop/reload/restart nginx`
   - `systemctl status nginx`

3. **SysVinit管理**
   - `service nginx start/stop/reload/restart`

Agent会自动尝试不同的管理方式，直到成功为止。
