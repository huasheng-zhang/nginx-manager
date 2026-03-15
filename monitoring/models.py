from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from nginx.models import NginxNode


class AccessLog(models.Model):
    """访问日志模型"""
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='access_logs')
    
    remote_addr = models.GenericIPAddressField(verbose_name='客户端IP')
    remote_user = models.CharField(max_length=100, blank=True, verbose_name='远程用户')
    
    time_local = models.DateTimeField(verbose_name='访问时间')
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_uri = models.TextField(verbose_name='请求URI')
    server_protocol = models.CharField(max_length=20, verbose_name='协议')
    
    status = models.IntegerField(verbose_name='状态码')
    body_bytes_sent = models.IntegerField(verbose_name='响应体大小')
    
    http_referer = models.TextField(blank=True, verbose_name='Referer')
    http_user_agent = models.TextField(blank=True, verbose_name='User-Agent')
    
    request_time = models.FloatField(verbose_name='请求耗时')
    upstream_response_time = models.FloatField(null=True, blank=True, verbose_name='上游响应时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')
    
    class Meta:
        verbose_name = '访问日志'
        verbose_name_plural = '访问日志'
        ordering = ['-time_local']
        indexes = [
            models.Index(fields=['-time_local']),
            models.Index(fields=['remote_addr']),
            models.Index(fields=['status']),
            models.Index(fields=['node', '-time_local']),
        ]
    
    def __str__(self):
        return f"{self.remote_addr} - {self.status} - {self.time_local.strftime('%Y-%m-%d %H:%M:%S')}"


class ErrorLog(models.Model):
    """错误日志模型"""
    LOG_LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('notice', 'Notice'),
        ('warn', 'Warning'),
        ('error', 'Error'),
        ('crit', 'Critical'),
        ('alert', 'Alert'),
        ('emerg', 'Emergency'),
    ]
    
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='error_logs')
    
    time_local = models.DateTimeField(verbose_name='错误时间')
    log_level = models.CharField(max_length=10, choices=LOG_LEVEL_CHOICES, verbose_name='日志级别')
    
    message = models.TextField(verbose_name='错误消息')
    client = models.GenericIPAddressField(blank=True, null=True, verbose_name='客户端IP')
    server = models.CharField(max_length=255, blank=True, verbose_name='服务器')
    request = models.TextField(blank=True, verbose_name='请求')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')
    
    class Meta:
        verbose_name = '错误日志'
        verbose_name_plural = '错误日志'
        ordering = ['-time_local']
        indexes = [
            models.Index(fields=['-time_local']),
            models.Index(fields=['log_level']),
            models.Index(fields=['node', '-time_local']),
        ]
    
    def __str__(self):
        return f"{self.log_level.upper()} - {self.node.name} - {self.time_local.strftime('%Y-%m-%d %H:%M:%S')}"


class MetricData(models.Model):
    """监控指标数据模型"""
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='metrics')
    
    timestamp = models.DateTimeField(verbose_name='采集时间')
    
    # 连接指标
    active_connections = models.IntegerField(verbose_name='活跃连接数')
    accepted_connections = models.IntegerField(verbose_name='已接受连接数')
    handled_connections = models.IntegerField(verbose_name='已处理连接数')
    
    # 请求指标
    total_requests = models.IntegerField(verbose_name='总请求数')
    requests_per_second = models.FloatField(verbose_name='每秒请求数')
    
    # 响应指标
    reading = models.IntegerField(verbose_name='正在读取')
    writing = models.IntegerField(verbose_name='正在写入')
    waiting = models.IntegerField(verbose_name='等待中')
    
    # 响应时间
    avg_response_time = models.FloatField(verbose_name='平均响应时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')
    
    class Meta:
        verbose_name = '监控指标'
        verbose_name_plural = '监控指标'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['node', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.node.name} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class AlertRule(models.Model):
    """告警规则模型"""
    METRIC_CHOICES = [
        ('active_connections', '活跃连接数'),
        ('requests_per_second', '每秒请求数'),
        ('avg_response_time', '平均响应时间'),
        ('error_rate', '错误率'),
        ('status_5xx_rate', '5xx状态码比例'),
    ]
    
    COMPARISON_CHOICES = [
        ('gt', '大于'),
        ('gte', '大于等于'),
        ('lt', '小于'),
        ('lte', '小于等于'),
        ('eq', '等于'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('critical', '严重'),
        ('emergency', '紧急'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='规则名称')
    description = models.TextField(blank=True, verbose_name='描述')
    
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', 
                            related_name='alert_rules', null=True, blank=True,
                            help_text='为空时表示监控所有节点')
    
    metric = models.CharField(max_length=30, choices=METRIC_CHOICES, verbose_name='监控指标')
    comparison = models.CharField(max_length=10, choices=COMPARISON_CHOICES, verbose_name='比较运算符')
    threshold = models.FloatField(verbose_name='阈值')
    
    duration = models.IntegerField(default=1, verbose_name='持续时间', help_text='持续多少分钟触发告警')
    
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='warning', verbose_name='告警级别')
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '告警规则'
        verbose_name_plural = '告警规则'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_metric_display()} {self.get_comparison_display()} {self.threshold})"


class Alert(models.Model):
    """告警记录模型"""
    STATUS_CHOICES = [
        ('firing', '触发中'),
        ('resolved', '已恢复'),
    ]
    
    SEVERITY_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('critical', '严重'),
        ('emergency', '紧急'),
    ]
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, verbose_name='告警规则', related_name='alerts')
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', related_name='alerts')
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='firing', verbose_name='状态')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, verbose_name='告警级别')
    
    message = models.TextField(verbose_name='告警消息')
    
    started_at = models.DateTimeField(verbose_name='开始时间')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='恢复时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '告警记录'
        verbose_name_plural = '告警记录'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status']),
            models.Index(fields=['severity']),
            models.Index(fields=['node', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.rule.name} - {self.node.name} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"


class LogAnalysisReport(models.Model):
    """日志分析报告模型"""
    REPORT_TYPE_CHOICES = [
        ('daily', '日报'),
        ('weekly', '周报'),
        ('monthly', '月报'),
        ('custom', '自定义'),
    ]
    
    node = models.ForeignKey(NginxNode, on_delete=models.CASCADE, verbose_name='所属节点', 
                            related_name='reports', null=True, blank=True)
    
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, verbose_name='报告类型')
    
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    
    # 统计数据
    total_requests = models.IntegerField(verbose_name='总请求数')
    unique_visitors = models.IntegerField(verbose_name='独立访客数')
    avg_response_time = models.FloatField(verbose_name='平均响应时间')
    error_rate = models.FloatField(verbose_name='错误率')
    
    top_ips = models.JSONField(verbose_name='Top IP列表')
    top_urls = models.JSONField(verbose_name='Top URL列表')
    status_codes = models.JSONField(verbose_name='状态码分布')
    
    report_data = models.JSONField(verbose_name='完整报告数据')
    
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')
    
    class Meta:
        verbose_name = '日志分析报告'
        verbose_name_plural = '日志分析报告'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['-generated_at']),
            models.Index(fields=['node', '-generated_at']),
        ]
    
    def __str__(self):
        node_name = self.node.name if self.node else '所有节点'
        return f"{node_name} - {self.get_report_type_display()} ({self.start_time.strftime('%Y-%m-%d')})"
