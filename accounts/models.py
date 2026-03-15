from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


class UserProfile(models.Model):
    """用户扩展资料模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户', related_name='profile')
    
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    position = models.CharField(max_length=100, blank=True, verbose_name='职位')
    
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name='头像')
    
    is_account_manager = models.BooleanField(default=False, verbose_name='账户管理员',
                                           help_text='是否可以管理用户和用户组')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
    
    def __str__(self):
        return f"{self.user.username} 的资料"


class PermissionGroup(models.Model):
    """权限组模型"""
    name = models.CharField(max_length=100, verbose_name='权限组名称')
    description = models.TextField(blank=True, verbose_name='描述')
    
    # 系统权限
    can_view_dashboard = models.BooleanField(default=True, verbose_name='查看仪表板')
    can_manage_users = models.BooleanField(default=False, verbose_name='管理用户')
    can_manage_groups = models.BooleanField(default=False, verbose_name='管理权限组')
    
    # Nginx节点权限
    can_view_nodes = models.BooleanField(default=True, verbose_name='查看节点')
    can_add_nodes = models.BooleanField(default=False, verbose_name='添加节点')
    can_edit_nodes = models.BooleanField(default=False, verbose_name='编辑节点')
    can_delete_nodes = models.BooleanField(default=False, verbose_name='删除节点')
    can_manage_node_config = models.BooleanField(default=False, verbose_name='管理节点配置')
    
    # 路由规则权限
    can_view_routes = models.BooleanField(default=True, verbose_name='查看路由规则')
    can_add_routes = models.BooleanField(default=False, verbose_name='添加路由规则')
    can_edit_routes = models.BooleanField(default=False, verbose_name='编辑路由规则')
    can_delete_routes = models.BooleanField(default=False, verbose_name='删除路由规则')
    
    # 限流规则权限
    can_view_rate_limits = models.BooleanField(default=True, verbose_name='查看限流规则')
    can_manage_rate_limits = models.BooleanField(default=False, verbose_name='管理限流规则')
    
    # 重定向规则权限
    can_view_redirects = models.BooleanField(default=True, verbose_name='查看重定向规则')
    can_manage_redirects = models.BooleanField(default=False, verbose_name='管理重定向规则')
    
    # IP封禁权限
    can_view_ip_blocks = models.BooleanField(default=True, verbose_name='查看IP封禁')
    can_manage_ip_blocks = models.BooleanField(default=False, verbose_name='管理IP封禁')
    
    # 日志查看权限
    can_view_logs = models.BooleanField(default=True, verbose_name='查看日志')
    can_delete_logs = models.BooleanField(default=False, verbose_name='删除日志')
    
    # 监控告警权限
    can_view_monitoring = models.BooleanField(default=True, verbose_name='查看监控')
    can_manage_alerts = models.BooleanField(default=False, verbose_name='管理告警规则')
    
    # 报告权限
    can_view_reports = models.BooleanField(default=True, verbose_name='查看报告')
    can_generate_reports = models.BooleanField(default=False, verbose_name='生成报告')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '权限组'
        verbose_name_plural = '权限组'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class UserGroupMembership(models.Model):
    """用户组成员关系"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', related_name='group_memberships')
    permission_group = models.ForeignKey(PermissionGroup, on_delete=models.CASCADE, verbose_name='权限组', related_name='memberships')
    
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   verbose_name='分配人', related_name='assigned_memberships')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='分配时间')
    
    class Meta:
        verbose_name = '用户组成员'
        verbose_name_plural = '用户组成员'
        unique_together = ['user', 'permission_group']
    
    def __str__(self):
        return f"{self.user.username} - {self.permission_group.name}"


class UserActionLog(models.Model):
    """用户操作日志模型"""
    ACTION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('view', '查看'),
        ('login', '登录'),
        ('logout', '登出'),
        ('export', '导出'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户', related_name='action_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='操作类型')
    
    resource_type = models.CharField(max_length=50, verbose_name='资源类型')
    resource_id = models.IntegerField(null=True, blank=True, verbose_name='资源ID')
    resource_name = models.CharField(max_length=255, blank=True, verbose_name='资源名称')
    
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')
    
    details = models.JSONField(null=True, blank=True, verbose_name='操作详情')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')
    
    class Meta:
        verbose_name = '用户操作日志'
        verbose_name_plural = '用户操作日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['resource_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.resource_type}"


class LoginAttempt(models.Model):
    """登录尝试记录模型"""
    STATUS_CHOICES = [
        ('success', '成功'),
        ('failure', '失败'),
        ('locked', '已锁定'),
    ]
    
    username = models.CharField(max_length=150, verbose_name='用户名')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='状态')
    
    user_agent = models.TextField(blank=True, verbose_name='User-Agent')
    failure_reason = models.CharField(max_length=100, blank=True, verbose_name='失败原因')
    
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name='尝试时间')
    
    class Meta:
        verbose_name = '登录尝试记录'
        verbose_name_plural = '登录尝试记录'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['-attempted_at']),
            models.Index(fields=['username', '-attempted_at']),
            models.Index(fields=['ip_address', '-attempted_at']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.get_status_display()} - {self.attempted_at.strftime('%Y-%m-%d %H:%M:%S')}"
