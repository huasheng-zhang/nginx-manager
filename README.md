# Nginx集群管理配置系统

基于Django框架开发的Nginx集群管理配置系统，提供Web界面管理Nginx节点、路由规则、限流、重定向、IP封禁等功能。

## 功能特性

### 1. 节点管理
- 实时添加、编辑、删除Nginx节点
- 节点状态监控（运行中、已停止、异常）
- 节点配置信息查看

### 2. 配置管理
- **路由规则**：支持代理转发、静态文件、重定向等多种规则类型
- **限流规则**：按IP、用户、服务器维度配置请求限流
- **重定向规则**：配置URL重定向规则
- **IP封禁**：封禁或允许特定IP访问

### 3. 用户权限系统
- 账号登录验证
- 基于用户组的权限管控
- 细粒度的权限控制（查看、添加、编辑、删除）
- 用户操作日志记录

### 4. 日志分析与监控
- 访问日志查看与筛选
- 错误日志实时监控
- 图表展示请求统计、状态码分布等
- 实时性能监控（连接数、请求速率、响应时间）

### 5. 告警系统
- 自定义告警规则配置
- 多级别告警（信息、警告、严重、紧急）
- 告警记录管理
- 日志分析报告生成

## 技术栈

- **后端**：Python 3.x + Django 6.0
- **数据库**：SQLite（默认），支持MySQL/PostgreSQL
- **前端**：HTML5 + CSS3 + JavaScript + Bootstrap 5
- **图表**：Chart.js
- **图标**：Font Awesome

## 安装与运行

### 环境要求
- Python 3.8+
- Django 6.0+

### 安装步骤

1. **克隆项目**
```bash
git clone <项目地址>
cd nginx-manager
```

2. **安装依赖**
```bash
pip install django
```

3. **数据库迁移**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **创建超级用户**
```bash
python manage.py createsuperuser
```

5. **启动服务**
```bash
python manage.py runserver 0.0.0.0:8000
```

6. **访问系统**
打开浏览器访问：http://localhost:8000

默认管理员账号：
- 用户名：admin
- 密码：admin123

## 使用说明

### 首次使用

1. **登录系统**：使用管理员账号登录
2. **创建权限组**：在后台管理（/admin/）中创建权限组并分配权限
3. **创建用户**：添加普通用户并分配到权限组
4. **添加Nginx节点**：在"Nginx节点"菜单中添加要管理的节点
5. **配置规则**：为节点添加路由、限流、重定向等规则

### 权限说明

系统提供细粒度的权限控制：

- **系统管理**：用户管理、权限组管理
- **节点管理**：查看、添加、编辑、删除节点
- **配置管理**：路由、限流、重定向、IP封禁的管理
- **日志查看**：访问日志、错误日志的查看与删除
- **监控告警**：实时监控查看、告警规则管理
- **报告生成**：日志分析报告的查看与生成

### 配置文件

主要配置文件：`nginx_manager/settings.py`

关键配置项：
- `DATABASES`：数据库配置
- `STATIC_URL`：静态文件URL
- `LOGIN_URL`：登录页面URL
- `LANGUAGE_CODE`：语言设置（已设置为中文）

## 项目结构

```
nginx-manager/
├── accounts/                 # 用户账户管理
│   ├── models.py            # 用户扩展模型
│   ├── views.py             # 视图函数
│   ├── permissions.py       # 权限检查工具
│   └── urls.py              # URL配置
├── nginx/                   # Nginx管理
│   ├── models.py            # 节点、规则模型
│   ├── views.py             # 视图函数
│   ├── forms.py             # 表单定义
│   └── urls.py              # URL配置
├── monitoring/              # 监控和日志
│   ├── models.py            # 日志、监控、告警模型
│   ├── views.py             # 视图函数
│   ├── forms.py             # 表单定义
│   └── urls.py              # URL配置
├── templates/               # 模板文件
│   ├── base.html            # 基础模板
│   ├── accounts/            # 账户相关模板
│   ├── nginx/               # Nginx管理模板
│   └── monitoring/          # 监控相关模板
├── static/                  # 静态文件
├── nginx_manager/           # Django项目配置
│   ├── settings.py          # 配置文件
│   ├── urls.py              # 主URL配置
│   └── wsgi.py              # WSGI配置
├── manage.py                # Django管理脚本
└── db.sqlite3               # 数据库文件
```

## 扩展开发

### 添加新功能

1. **创建新的App**：
```bash
python manage.py startapp new_feature
```

2. **添加模型**：在`models.py`中定义数据模型

3. **创建迁移**：
```bash
python manage.py makemigrations new_feature
python manage.py migrate
```

4. **注册Admin**：在`admin.py`中注册模型

5. **创建视图**：在`views.py`中实现业务逻辑

6. **配置URL**：在`urls.py`中添加路由

7. **创建模板**：在`templates/`目录下创建HTML模板

### 数据库切换

修改`nginx_manager/settings.py`中的DATABASES配置：

```python
# MySQL示例
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nginx_manager',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

然后安装MySQL驱动：
```bash
pip install mysqlclient
```

## 注意事项

1. **生产环境**：开发服务器不适用于生产环境，请使用Gunicorn或uWSGI部署
2. **静态文件**：生产环境需要配置静态文件收集：`python manage.py collectstatic`
3. **安全配置**：生产环境请设置`DEBUG = False`并配置`ALLOWED_HOSTS`
4. **密码安全**：首次登录后请修改默认密码
5. **日志清理**：定期清理历史日志以节省存储空间

## 许可证

MIT License

## 问题反馈

如有问题或建议，请提交Issue或联系开发团队。