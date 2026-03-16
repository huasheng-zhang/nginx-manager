# 自动配置同步 - 快速参考

## 问题回答

**问：创建路由规则并点击保存时，是否会触发nginx配置生成并应用？**

**答：是的！** 现在会自动触发配置同步。

## 如何使用

### 1. 创建规则（自动触发）

在Web界面创建路由规则 → 点击"保存" → **自动**生成配置 → **自动**应用到Nginx节点

### 2. 修改规则（自动触发）

编辑路由规则 → 点击"保存" → **自动**更新配置 → **自动**重载Nginx

### 3. 删除规则（自动触发）

删除路由规则 → 确认删除 → **自动**移除配置 → **自动**重载Nginx

### 4. 切换启用/禁用（自动触发）

点击状态切换按钮 → **自动**应用或移除配置

## 技术实现

### 涉及的文件

```
nginx/
├── signals.py                          # Signal处理器（自动触发核心）
├── config_generator.py                 # 配置生成器
│   └── sync_node_config()             # 同步单个节点
│   └── sync_all_nodes()               # 同步所有节点
├── apps.py                             # 应用配置，加载signals
├── api.py                              # API接口（手动触发）
│   └── sync_node_config_api()         # API端点
│   └── preview_node_config_api()      # 预览配置
└── models.py                           # 数据模型

nginx_manager/
└── settings.py                         # 日志配置

logs/
└── nginx_manager.log                   # 自动同步日志
```

### Signal处理器

监听以下模型的变更：
- `RouteRule` - 路由规则
- `RateLimitRule` - 限流规则
- `RedirectRule` - 重定向规则
- `IPBlockRule` - IP封禁规则

**触发时机：**
- `post_save` - 创建或更新后
- `post_delete` - 删除后

### 自动同步流程

```
用户操作（Web界面）
    ↓
Django ORM 保存/删除数据
    ↓
触发 post_save / post_delete Signal
    ↓
调用 sync_node_config(node_id)
    ↓
[1] 连接Nginx节点（SSH）
[2] 生成Nginx配置
[3] 测试配置语法（nginx -t）
[4] 备份原配置
[5] 应用新配置
[6] 重载Nginx（nginx -s reload）
[7] 更新节点状态
    ↓
完成（记录日志）
```

## 日志查看

### 实时查看自动同步日志

```bash
# Linux/macOS
tail -f logs/nginx_manager.log

# Windows PowerShell
type logs\nginx_manager.log
```

### 日志示例

**创建规则：**
```
INFO 2026-03-16 10:30:15 signals 规则变更触发配置同步: 路由规则 'api-proxy' 已创建，正在同步节点 1
INFO 2026-03-16 10:30:18 config_generator 为节点 nginx-1 生成Nginx配置
INFO 2026-03-16 10:30:20 config_generator Nginx配置应用成功: nginx-1
INFO 2026-03-16 10:30:20 signals 节点 1 配置同步成功（由路由规则 'api-proxy' 创建触发）
```

**更新规则：**
```
INFO 2026-03-16 10:35:10 signals 规则变更触发配置同步: 路由规则 'api-proxy' 已更新，正在同步节点 1
INFO 2026-03-16 10:35:12 config_generator 为节点 nginx-1 生成Nginx配置
INFO 2026-03-16 10:35:14 config_generator Nginx配置应用成功: nginx-1
INFO 2026-03-16 10:35:14 signals 节点 1 配置同步成功（由路由规则 'api-proxy' 更新触发）
```

**删除规则：**
```
INFO 2026-03-16 10:40:05 signals 规则变更触发配置同步: 路由规则 'api-proxy' 已删除，正在同步节点 1
INFO 2026-03-16 10:40:08 config_generator 为节点 nginx-1 生成Nginx配置
INFO 2026-03-16 10:40:10 config_generator Nginx配置应用成功: nginx-1
INFO 2026-03-16 10:40:10 signals 节点 1 配置同步成功（由路由规则 'api-proxy' 删除触发）
```

## 手动触发方式

### 方法1：API调用（可选）

虽然自动触发已足够，但仍提供API手动触发：

```bash
# 同步指定节点
curl -X POST http://localhost:8000/api/v1/agent/nodes/1/sync/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 预览配置（不应用）
curl -X GET http://localhost:8000/api/v1/agent/nodes/1/preview/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 方法2：批量同步

```bash
python manage.py shell
```

```python
from nginx.config_generator import sync_all_nodes
results = sync_all_nodes()
print(results)
```

或运行测试脚本：
```bash
python test_auto_sync.py
```

## 故障排查

### 问题：自动同步未触发

**检查Signal是否加载：**

```python
# python manage.py shell
from django.db.models.signals import post_save
from nginx.models import RouteRule

# 检查是否连接
post_save.receivers
```

**检查apps.py：**

```python
# nginx/apps.py
def ready(self):
    import nginx.signals  # 确保这行存在
```

### 问题：配置同步失败

**查看详细错误日志：**

```bash
tail -f logs/nginx_manager.log | grep ERROR
```

常见原因：
- SSH连接失败（检查SSH配置）
- Nginx配置语法错误（检查规则配置）
- 权限不足（检查文件权限）

## 配置建议

### 日志级别

在 `nginx_manager/settings.py` 中调整日志级别：

```python
'nginx': {
    'level': 'INFO',  # 改为DEBUG查看更详细日志
}
```

### 备份策略

每次自动同步都会备份原配置：
- 备份位置：`/etc/nginx/nginx.conf.backup`
- 如需恢复：
  ```bash
  ssh nginx-node "cp /etc/nginx/nginx.conf.backup /etc/nginx/nginx.conf"
  ssh nginx-node "nginx -s reload"
  ```

## 测试验证

运行测试脚本验证自动同步功能：

```bash
cd C:\Users\admin\WorkBuddy\20260313103247
python test_auto_sync.py
```

测试内容包括：
1. 创建测试规则 → 验证自动同步
2. 更新测试规则 → 验证自动同步
3. 删除测试规则 → 验证自动同步
4. 批量同步所有节点

## 总结

| 操作 | 是否自动触发 | 触发时机 |
|------|------------|---------|
| 创建路由规则 | ✅ 是 | 点击"保存"后 |
| 修改路由规则 | ✅ 是 | 点击"保存"后 |
| 删除路由规则 | ✅ 是 | 确认删除后 |
| 切换启用/禁用 | ✅ 是 | 点击切换后 |
| 创建限流规则 | ✅ 是 | 点击"保存"后 |
| 修改限流规则 | ✅ 是 | 点击"保存"后 |
| 创建重定向规则 | ✅ 是 | 点击"保存"后 |
| 修改重定向规则 | ✅ 是 | 点击"保存"后 |
| 创建IP封禁规则 | ✅ 是 | 点击"保存"后 |
| 修改IP封禁规则 | ✅ 是 | 点击"保存"后 |

**结论：** 是的，现在在nginx-manager页面创建路由规则并点击保存时，会自动触发nginx配置生成并且应用到Nginx节点！

---

**版本**：Auto Sync v1.0  
**创建日期**：2026-03-16  
**适用**：nginx-manager with Django Signals
