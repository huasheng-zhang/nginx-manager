from django.apps import AppConfig


class NginxConfig(AppConfig):
    name = 'nginx'
    
    def ready(self):
        # 导入signals以注册信号处理器
        import nginx.signals
