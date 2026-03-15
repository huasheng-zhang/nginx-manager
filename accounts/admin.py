from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, PermissionGroup, UserGroupMembership,
    UserActionLog, LoginAttempt
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '用户资料'
    
    fields = ('phone', 'department', 'position', 'avatar', 'is_account_manager')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_department', 'get_is_account_manager']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__is_account_manager']
    
    def get_department(self, obj):
        return obj.profile.department if hasattr(obj, 'profile') else ''
    get_department.short_description = '部门'
    
    def get_is_account_manager(self, obj):
        return obj.profile.is_account_manager if hasattr(obj, 'profile') else False
    get_is_account_manager.short_description = '账户管理员'
    get_is_account_manager.boolean = True


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(PermissionGroup)
class PermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description')
        }),
        ('系统权限', {
            'fields': ('can_view_dashboard', 'can_manage_users', 'can_manage_groups')
        }),
        ('Nginx节点权限', {
            'fields': (
                'can_view_nodes', 'can_add_nodes', 'can_edit_nodes', 
                'can_delete_nodes', 'can_manage_node_config'
            )
        }),
        ('路由规则权限', {
            'fields': (
                'can_view_routes', 'can_add_routes', 'can_edit_routes', 'can_delete_routes'
            )
        }),
        ('限流规则权限', {
            'fields': ('can_view_rate_limits', 'can_manage_rate_limits')
        }),
        ('重定向规则权限', {
            'fields': ('can_view_redirects', 'can_manage_redirects')
        }),
        ('IP封禁权限', {
            'fields': ('can_view_ip_blocks', 'can_manage_ip_blocks')
        }),
        ('日志权限', {
            'fields': ('can_view_logs', 'can_delete_logs')
        }),
        ('监控告警权限', {
            'fields': ('can_view_monitoring', 'can_manage_alerts')
        }),
        ('报告权限', {
            'fields': ('can_view_reports', 'can_generate_reports')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserGroupMembership)
class UserGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'permission_group', 'assigned_by', 'assigned_at']
    list_filter = ['permission_group', 'assigned_at']
    search_fields = ['user__username', 'user__email', 'permission_group__name']
    readonly_fields = ['assigned_at']


@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'resource_type', 'resource_name', 'ip_address', 'created_at']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['user__username', 'resource_name', 'ip_address']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ['username', 'ip_address', 'status', 'attempted_at']
    list_filter = ['status', 'attempted_at']
    search_fields = ['username', 'ip_address', 'failure_reason']
    readonly_fields = ['attempted_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
