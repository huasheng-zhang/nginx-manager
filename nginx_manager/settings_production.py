"""
生产环境 Django 设置
基于 settings.py，添加生产环境特定的配置
"""

import os
from pathlib import Path
from .settings import *

# ==============================================================================
# 安全设置
# ==============================================================================

# 从环境变量获取密钥，如果没有则使用默认值（生产环境必须修改！）
SECRET_KEY = os.environ.get('SECRET_KEY') or 'django-insecure-change-this-secret-key-in-production-environment'

# 关闭调试模式
DEBUG = False

# 允许访问的主机（从环境变量获取，或添加你的公网IP）
# 重要：生产环境必须添加你的域名或IP地址
# 注意：如果环境变量存在但为空，会导致ALLOWED_HOSTS为空列表
ALLOWED_HOSTS = []
if os.environ.get('DJANGO_ALLOWED_HOSTS'):
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(',')
else:
    # 默认允许的 hosts
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '110.41.183.3']

# 或者直接在下面配置（更简单）：
# ALLOWED_HOSTS = ['localhost', '127.0.0.1', '110.41.183.3']
# 如果需要允许多个IP或域名，直接添加到列表中

# 强制 HTTPS（生产环境建议开启）
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 安全 Cookie 设置
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ==============================================================================
# 数据库配置
# ==============================================================================

# 使用SQLite（简单部署，适合小型项目）
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 如果使用PostgreSQL（生产推荐），请取消下面注释并安装psycopg2
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get('DB_NAME', 'nginx_manager'),
#         'USER': os.environ.get('DB_USER', 'nginx_user'),
#         'PASSWORD': os.environ.get('DB_PASSWORD', 'your_password'),
#         'HOST': os.environ.get('DB_HOST', 'localhost'),
#         'PORT': os.environ.get('DB_PORT', '5432'),
#         'CONN_MAX_AGE': 60,  # 连接池
#     }
# }

# ==============================================================================
# Redis 缓存配置
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://:{os.environ.get('REDIS_PASSWORD')}@{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

# Session 使用 Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ==============================================================================
# Celery 配置（异步任务）
# ==============================================================================

CELERY_BROKER_URL = f"redis://:{os.environ.get('REDIS_PASSWORD')}@{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')}/0"
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Celery 任务配置
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# ==============================================================================
# 日志配置
# ==============================================================================

LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'monitoring': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'nginx': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ==============================================================================
# 静态文件配置
# ==============================================================================

# 静态文件收集目录
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 静态文件存储后端（使用 CDN 或云存储）
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ==============================================================================
# 文件上传配置
# ==============================================================================

# 文件上传大小限制（10MB）
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# 媒体文件存储后端（生产环境建议使用云存储）
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ==============================================================================
# 邮件配置
# ==============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

ADMINS = [
    ('Admin', os.environ.get('ADMIN_EMAIL', 'admin@example.com')),
]

MANAGERS = ADMINS

# ==============================================================================
# 监控和告警配置
# ==============================================================================

# 健康检查 URL
HEALTH_CHECK_URL = '/health/'

# 监控数据保留时间（天）
MONITORING_DATA_RETENTION_DAYS = int(os.environ.get('MONITORING_DATA_RETENTION_DAYS', '30'))

# 日志数据保留时间（天）
LOG_DATA_RETENTION_DAYS = int(os.environ.get('LOG_DATA_RETENTION_DAYS', '7'))

# ==============================================================================
# 性能优化
# ==============================================================================

# 数据库连接池
CONN_MAX_AGE = 60

# 启用 GZip 压缩
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # 添加 GZip 压缩
] + MIDDLEWARE[1:]

# 模板缓存优化
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# ==============================================================================
# 自定义设置
# ==============================================================================

# SSH 连接超时设置
SSH_CONNECT_TIMEOUT = int(os.environ.get('SSH_CONNECT_TIMEOUT', '10'))
SSH_COMMAND_TIMEOUT = int(os.environ.get('SSH_COMMAND_TIMEOUT', '30'))

# Nginx 管理相关配置
NGINX_CONFIG_BACKUP_DIR = BASE_DIR / 'backups' / 'nginx_configs'
NGINX_CONFIG_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# 报告生成配置
REPORTS_DIR = BASE_DIR / 'media' / 'reports'
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 第三方服务集成（可选）
# ==============================================================================

# 钉钉告警
DINGTALK_WEBHOOK_URL = os.environ.get('DINGTALK_WEBHOOK_URL')
DINGTALK_SECRET = os.environ.get('DINGTALK_SECRET')

# 企业微信告警
WECHAT_WEBHOOK_URL = os.environ.get('WECHAT_WEBHOOK_URL')

# Prometheus 监控
ENABLE_PROMETHEUS = os.environ.get('ENABLE_PROMETHEUS', 'False') == 'True'

# ==============================================================================
# 调试和开发（生产环境应关闭）
# ==============================================================================

if os.environ.get('ENABLE_DEBUG_TOOLBAR', 'False') == 'True':
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
    }
