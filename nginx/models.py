from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


class NginxNode(models.Model):
    """Nginx节点模型"""
    STATUS_CHOICES = [
        ('active', '运行中'),
        ('inactive', '已停止'),
        ('error', '异常'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='节点名称')
    host = models.CharField(max_length=200, verbose_name='主机地址')
    port = models.IntegerField(default=80, verbose_name='端口')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive', verbose_name='状态')
    config_path = models.CharField(max_length=255, verbose_name='配置文件路径', default='/etc/nginx/nginx.conf')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # SSH连接配置
    ssh_port = models.IntegerField(default=22, verbose_name='SSH端口')
    ssh_username = models.CharField(max_length=100, default='root', verbose_name='SSH用户名')
    ssh_password = models.CharField(max_length=255, blank=True, null=True, verbose_name='SSH密码')
    ssh_key_path = models.CharField(max_length=255, blank=True, null=True, verbose_name='SSH私钥路径')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'Nginx节点'
        verbose_name_plural = 'Nginx节点'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.host}:{self.port})"


class RouteRule(models.Model):
    """路由规则模型"""
    RULE_TYPE_CHOICES = [
        ('proxy', '代理转发'),
        ('static', '静态文件'),
        ('redirect', '重定向'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='route_rules')
    domain = models.CharField(max_length=255, verbose_name='域名')
    path = models.CharField(max_length=255, verbose_name='路径匹配')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES, default='proxy', verbose_name='规则类型')
    
    # 代理转发配置
    upstream_host = models.CharField(max_length=255, blank=True, verbose_name='上游主机')
    upstream_port = models.IntegerField(blank=True, null=True, verbose_name='上游端口')
    
    # 静态文件配置
    root_path = models.CharField(max_length=255, blank=True, verbose_name='根目录路径')
    
    # 重定向配置
    redirect_url = models.CharField(max_length=255, blank=True, verbose_name='重定向URL')
    redirect_type = models.IntegerField(default=302, blank=True, verbose_name='重定向类型')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '路由规则'
        verbose_name_plural = '路由规则'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.domain}{self.path}"


class RateLimitRule(models.Model):
    """限流规则模型"""
    LIMIT_BY_CHOICES = [
        ('ip', '按IP'),
        ('user', '按用户'),
        ('server', '按服务器'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='rate_limit_rules')
    limit_by = models.CharField(max_length=20, choices=LIMIT_BY_CHOICES, default='ip', verbose_name='限流维度')
    requests_per_second = models.IntegerField(verbose_name='每秒请求数')
    burst = models.IntegerField(default=0, verbose_name='突发请求数')
    
    # 应用范围
    domains = models.TextField(blank=True, verbose_name='域名列表（逗号分隔）')
    paths = models.TextField(blank=True, verbose_name='路径列表（逗号分隔）')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '限流规则'
        verbose_name_plural = '限流规则'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.requests_per_second} req/s)"


class RedirectRule(models.Model):
    """重定向规则模型"""
    name = models.CharField(max_length=100, verbose_name='规则名称')
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='redirect_rules')
    
    # 匹配条件
    source_domain = models.CharField(max_length=255, verbose_name='源域名')
    source_path = models.CharField(max_length=255, blank=True, verbose_name='源路径')
    
    # 重定向目标
    target_url = models.CharField(max_length=255, verbose_name='目标URL')
    redirect_type = models.IntegerField(default=301, verbose_name='重定向类型', 
                                       help_text='301: 永久重定向, 302: 临时重定向')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '重定向规则'
        verbose_name_plural = '重定向规则'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.source_domain}{self.source_path})"


class IPBlockRule(models.Model):
    """IP封禁规则模型"""
    ACTION_CHOICES = [
        ('deny', '拒绝访问'),
        ('allow', '允许访问'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='ip_block_rules')
    
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    subnet_mask = models.IntegerField(blank=True, null=True, verbose_name='子网掩码',
                                     help_text='例如：24 表示 /24 子网')
    
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, default='deny', verbose_name='操作')
    
    domains = models.TextField(blank=True, verbose_name='域名列表（逗号分隔，为空表示所有域名）')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = 'IP封禁规则'
        verbose_name_plural = 'IP封禁规则'
        ordering = ['-created_at']
        unique_together = ['node', 'ip_address', 'subnet_mask']
    
    def __str__(self):
        subnet = f"/{self.subnet_mask}" if self.subnet_mask else ""
        return f"{self.name} ({self.ip_address}{subnet})"


class NginxConfig(models.Model):
    """Nginx配置备份模型"""
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='config_backups')
    config_content = models.TextField(verbose_name='配置内容')
    version = models.CharField(max_length=50, verbose_name='版本号')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '配置备份'
        verbose_name_plural = '配置备份'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.node.name} - {self.version} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
