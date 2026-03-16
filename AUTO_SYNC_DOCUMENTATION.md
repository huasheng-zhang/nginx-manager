# 自动配置同步功能文档

## 功能概述

从版本更新后，nginx-manager支持**自动配置同步**功能。当您在Web界面创建、修改或删除路由规则、限流规则、重定向规则、IP封禁规则时，系统会自动将变更应用到Nginx节点，无需手动操作。

## 工作原理

### Django Signals 机制

系统使用Django Signals监听模型变更事件，当规则发生变化时自动触发配置同步：

```python
# signals.py 中定义的信号处理器

@receiver(post_save, sender=RouteRule)
def apply_config_on_route_rule_save(sender, instance, created, **kwargs):
    """路由规则保存后自动应用配置"""
    if instance.is_active:
        transaction.on_commit(
            lambda: _sync_node_config_async(instance.node_id, ...)
        )
```

### 触发时机

**自动触发配置同步的场景：**

1. **创建新规则** - 在Web界面点击"保存"按钮后
2. **修改规则** - 编辑规则并点击"保存"按钮后
3. **删除规则** - 点击"删除"按钮并确认后
4. **切换规则状态** - 点击"启用/禁用"切换后

**支持的规则类型：**
- ✅ 路由规则（代理转发、静态文件、重定向）
- ✅ 限流规则
- ✅ 重定向规则
- ✅ IP封禁规则

### 自动触发流程

```
用户操作（保存/删除规则）
    ↓
Django ORM 保存到数据库
    ↓
Signal 触发 post_save / post_delete
    ↓
调用 sync_node_config(node_id)
    ↓
生成 Nginx 配置
    ↓
测试配置语法（nginx -t）
    ↓
备份原配置
    ↓
应用新配置
    ↓
重载 Nginx（nginx -s reload）
    ↓
更新节点状态
```

## 使用说明

### 基本使用（无需任何额外操作）

**配置路由规则：**

1. 登录 nginx-manager Web界面
2. 进入"路由规则"页面
3. 点击"添加路由规则"
4. 填写规则信息：
   - 规则名称：api-proxy
   - 所属节点：nginx-1
   - 域名：api.example.com
   - 路径：/api/
   - 类型：代理转发
   - 上游主机：192.168.1.200
   - 上游端口：8080
   - 状态：启用
5. **点击"保存"按钮**

**自动触发：**
- ✅ 系统检测到规则创建
- ✅ 自动生成Nginx配置
- ✅ 测试配置语法
- ✅ 应用到Nginx-1节点
- ✅ 重载Nginx服务
- ✅ 节点状态更新为"运行中"

**查看日志：**
```bash
# 在 nginx-manager 服务器上执行
tail -f logs/nginx_manager.log
```

日志示例：
```
INFO 2026-03-16 10:30:15 signals 12345 67890 规则变更触发配置同步: 路由规则 'api-proxy' 已创建，正在同步节点 1
INFO 2026-03-16 10:30:18 config_generator 12345 67890 为节点 nginx-1 生成Nginx配置
INFO 2026-03-03-16 10:30:20 config_generator 12345 67890 Nginx配置应用成功: nginx-1
INFO 2026-03-16 10:30:20 signals 12345 67890 节点 1 配置同步成功（由路由规则 'api-proxy' 创建触发）
```

### 修改规则

**操作流程：**

1. 在路由规则列表中找到要修改的规则
2. 点击"编辑"
3. 修改配置（如：上游端口从8080改为9000）
4. **点击"保存"按钮**

**自动触发：**
- 系统检测到规则更新
- 自动重新生成并应用配置
- 无需手动操作

### 删除规则

**操作流程：**

1. 在路由规则列表中找到要删除的规则
2. 点击"删除"
3. 确认删除

**自动触发：**
- 系统检测到规则删除
- 自动更新Nginx配置（移除该规则）
- 重载Nginx服务

### 切换规则状态（启用/禁用）

**操作流程：**

1. 在规则列表中点击"启用/禁用"切换按钮

**自动触发：**
- 状态从"禁用"→"启用"：应用该规则
- 状态从"启用"→"禁用"：移除该规则

## 日志与监控

### 日志文件

系统会将自动同步的操作记录到日志文件中：

**日志位置：**
- nginx-manager 根目录下的 `logs/` 文件夹
- `logs/nginx_manager.log` - Nginx管理相关日志
- `logs/django.log` - Django框架日志

### 日志配置

日志配置在 `nginx_manager/settings.py` 中：

```python
LOGGING = {
    'loggers': {
        'nginx': {
            'handlers': ['nginx_file', 'console'],
            'level': 'INFO',
        },
        'nginx.config_generator': {
            'handlers': ['nginx_file', 'console'],
            'level': 'DEBUG',  # 可以改为DEBUG查看更详细日志
        },
    },
}
```

### 查看实时日志

```bash
# 查看Nginx管理日志
tail -f logs/nginx_manager.log

# 查看所有日志（Linux）
tail -f logs/*.log

# Windows PowerShell
type logs\nginx_manager.log
```

### 日志格式

每条日志包含以下信息：
- 日志级别（INFO, WARNING, ERROR, DEBUG）
- 时间戳
- 模块名称（signals, config_generator, agent）
- 进程ID
- 线程ID
- 日志消息

## 高级配置

### 配置检查点

**禁用自动同步（不推荐）：**

如果需要在某些情况下禁用自动同步，可以临时修改代码：

```python
# nginx/signals.py

@receiver(post_save, sender=RouteRule)
def apply_config_on_route_rule_save(sender, instance, created, **kwargs):
    # if instance.is_active:  # 注释掉这一行
    if False:  # 添加这一行临时禁用
        transaction.on_commit(...)
```

**注意：** 禁用后需要手动调用API或管理命令来应用配置。

### 批量同步

如果需要手动同步所有节点配置：

```bash
python manage.py shell
```

在Python shell中执行：
```python
from nginx.config_generator import sync_all_nodes
results = sync_all_nodes()
print(results)
```

或使用测试脚本：
```bash
python test_auto_sync.py
```

### API手动触发

除了自动触发，仍然可以通过API手动同步：

```bash
# 同步指定节点
curl -X POST http://nginx-manager/api/v1/agent/nodes/1/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预览配置（不应用）
curl -X GET http://nginx-manager/api/v1/agent/nodes/1/preview/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 故障排查

### 问题1：自动同步未触发

**症状：** 保存规则后，Nginx配置未更新

**排查步骤：**

1. **检查日志**
   ```bash
   tail -f logs/nginx_manager.log
   ```

2. **检查Signal是否加载**
   ```python
   # python manage.py shell
   from django.db.models.signals import post_save
   from nginx.models import RouteRule
   from nginx.signals import apply_config_on_route_rule_save
   
   # 检查信号是否连接
   post_save.receivers
   ```

3. **检查Django应用配置**
   ```python
   # nginx/apps.py
   def ready(self):
       import nginx.signals  # 确保这行存在
   ```

4. **检查规则是否启用**
   - 只有 `is_active=True` 的规则才会触发同步
   - 禁用的规则只保存到数据库，不应用到Nginx

### 问题2：配置同步失败

**症状：** 日志显示同步失败

**可能原因：**

1. **SSH连接失败**
   - 检查节点SSH配置
   - 测试手动连接：`ssh user@host`

2. **Nginx配置测试失败**
   - 生成的配置可能有语法错误
   - 查看日志中的具体错误信息
   - 检查规则配置是否完整

3. **权限不足**
   - nginx进程需要有权限读取配置文件
   - 检查配置文件权限：`ls -l /etc/nginx/nginx.conf`

### 问题3：配置未生效

**症状：** 同步成功，但访问未按预期转发

**排查步骤：**

1. **检查Nginx是否重载**
   ```bash
   ps aux | grep nginx
   ```

2. **检查配置文件内容**
   ```bash
   cat /etc/nginx/nginx.conf
   ```

3. **检查Nginx错误日志**
   ```bash
   tail /var/log/nginx/error.log
   ```

4. **测试后端服务**
   ```bash
   curl http://backend-host:backend-port/
   ```

## 最佳实践

### 1. 规则配置建议

- **先创建规则，再启用规则**
  - 创建时可以先禁用（is_active=False）
  - 确认配置无误后再启用

- **小步快跑**
  - 每次只修改一个规则
  - 验证生效后再修改下一个

- **使用描述信息**
  - 为规则添加清晰的描述
  - 记录规则用途和配置说明

### 2. 监控建议

- **实时监控日志**
  ```bash
  tail -f logs/nginx_manager.log | grep -E "(同步|触发|成功|失败)"
  ```

- **监控Nginx状态**
  ```bash
  watch -n 5 'systemctl status nginx'
  ```

- **监控访问日志**
  ```bash
  tail -f /var/log/nginx/access.log
  ```

### 3. 备份策略

- **配置自动备份**
  - 每次应用配置前自动备份（已实现）
  - 备份文件：`/etc/nginx/nginx.conf.backup`

- **定期手动备份**
  ```bash
  cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.manual.backup
  ```

- **版本控制**
  ```bash
  git init /etc/nginx
  git add nginx.conf
  git commit -m "Initial config"
  ```

### 4. 回滚策略

**如果新配置有问题：**

```bash
# 1. 恢复备份配置
ssh nginx-node "cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf"

# 2. 重载Nginx
ssh nginx-node "nginx -s reload"

# 3. 禁用有问题的规则（在Web界面操作）
```

## 性能考虑

### 自动触发频率

- **快速连续变更**：如果在短时间内多次修改规则，系统会依次同步，可能导致多次Nginx重载

- **优化建议**：批量修改时，可以先禁用自动同步，修改完成后再手动同步一次

### 异步处理（未来优化）

当前实现是同步的（会等待配置应用完成）。对于生产环境，建议使用异步任务队列（如Celery）：

```python
# 异步版本示例
from celery import shared_task

@shared_task
def async_sync_node_config(node_id):
    sync_node_config(node_id)

# Signal中调用
transaction.on_commit(
    lambda: async_sync_node_config.delay(instance.node_id)
)
```

## 总结

### 功能特点

✅ **全自动**：保存/删除规则后自动应用配置
✅ **安全**：配置测试通过后才应用，失败自动回滚
✅ **日志完整**：详细记录每次同步操作
✅ **灵活**：支持手动API触发和批量同步
✅ **兼容**：不影响现有手动操作

### 用户收益

- **简化操作**：无需手动同步配置
- **减少错误**：自动测试配置语法
- **实时生效**：保存后立即生效
- **可追溯**：完整日志记录

### 注意事项

- 确保Nginx节点SSH配置正确
- 定期检查日志文件
- 配置变更后验证业务是否正常
- 保持备份策略

---

**文档版本**：1.0  
**最后更新**：2026-03-16  
**适用版本**：nginx-manager with auto-sync support
