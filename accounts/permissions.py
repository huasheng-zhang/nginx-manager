"""
权限检查工具
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import UserGroupMembership


def get_user_permissions(user):
    """获取用户的所有权限"""
    if user.is_superuser:
        # 超级用户拥有所有权限
        return {
            'can_view_dashboard': True,
            'can_manage_users': True,
            'can_manage_groups': True,
            'can_view_nodes': True,
            'can_add_nodes': True,
            'can_edit_nodes': True,
            'can_delete_nodes': True,
            'can_manage_node_config': True,
            'can_view_routes': True,
            'can_add_routes': True,
            'can_edit_routes': True,
            'can_delete_routes': True,
            'can_view_rate_limits': True,
            'can_manage_rate_limits': True,
            'can_view_redirects': True,
            'can_manage_redirects': True,
            'can_view_ip_blocks': True,
            'can_manage_ip_blocks': True,
            'can_view_logs': True,
            'can_delete_logs': True,
            'can_view_monitoring': True,
            'can_manage_alerts': True,
            'can_view_reports': True,
            'can_generate_reports': True,
        }
    
    permissions = {}
    memberships = UserGroupMembership.objects.filter(user=user).select_related('permission_group')
    
    # 初始化所有权限为False
    all_permission_keys = [
        'can_view_dashboard', 'can_manage_users', 'can_manage_groups',
        'can_view_nodes', 'can_add_nodes', 'can_edit_nodes', 'can_delete_nodes', 'can_manage_node_config',
        'can_view_routes', 'can_add_routes', 'can_edit_routes', 'can_delete_routes',
        'can_view_rate_limits', 'can_manage_rate_limits',
        'can_view_redirects', 'can_manage_redirects',
        'can_view_ip_blocks', 'can_manage_ip_blocks',
        'can_view_logs', 'can_delete_logs',
        'can_view_monitoring', 'can_manage_alerts',
        'can_view_reports', 'can_generate_reports',
    ]
    
    for key in all_permission_keys:
        permissions[key] = False
    
    # 合并所有权限组的权限
    for membership in memberships:
        group = membership.permission_group
        for key in all_permission_keys:
            if getattr(group, key, False):
                permissions[key] = True
    
    return permissions


def permission_required(permission_key):
    """权限检查装饰器"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            permissions = get_user_permissions(request.user)
            if not permissions.get(permission_key, False):
                messages.error(request, '您没有权限执行此操作')
                return HttpResponseForbidden('您没有权限执行此操作')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class PermissionRequiredMixin:
    """权限检查Mixin类"""
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if self.permission_required:
            permissions = get_user_permissions(request.user)
            if not permissions.get(self.permission_required, False):
                messages.error(request, '您没有权限执行此操作')
                return HttpResponseForbidden('您没有权限执行此操作')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_permissions'] = get_user_permissions(self.request.user)
        return context
