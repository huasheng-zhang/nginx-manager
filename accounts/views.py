import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Count, Q

from .models import UserActionLog, LoginAttempt
from .permissions import get_user_permissions, UserGroupMembership
from nginx.models import NginxNode, RouteRule, RateLimitRule
from monitoring.models import AccessLog, ErrorLog, Alert


def login_view(request):
    """登录视图"""
    if request.user.is_authenticated:
        return redirect('accounts:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 记录登录尝试
        attempt = LoginAttempt.objects.create(
            username=username,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
            status='failure'
        )
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # 更新登录尝试记录
            attempt.status = 'success'
            attempt.save()
            
            # 记录用户操作日志
            UserActionLog.objects.create(
                user=user,
                action='login',
                resource_type='auth',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                details={'username': username}
            )
            
            messages.success(request, '登录成功！')
            return redirect('accounts:home')
        else:
            attempt.failure_reason = '用户名或密码错误'
            attempt.save()
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """登出视图"""
    if request.user.is_authenticated:
        # 记录用户操作日志
        UserActionLog.objects.create(
            user=request.user,
            action='logout',
            resource_type='auth',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )
        
        logout(request)
        messages.success(request, '已成功登出')
    
    return redirect('accounts:login')


class DashboardView(TemplateView):
    """仪表板视图"""
    template_name = 'dashboard/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        permissions = get_user_permissions(request.user)
        if not permissions.get('can_view_dashboard', False):
            messages.error(request, '您没有权限访问仪表板')
            return redirect('accounts:login')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 用户权限
        context['user_permissions'] = get_user_permissions(self.request.user)
        
        # 统计数据
        context['total_nodes'] = NginxNode.objects.count()
        context['active_nodes'] = NginxNode.objects.filter(status='active').count()
        context['total_routes'] = RouteRule.objects.filter(is_active=True).count()
        context['total_rate_limits'] = RateLimitRule.objects.filter(is_active=True).count()
        
        # 最近访问日志
        context['recent_access_logs'] = AccessLog.objects.select_related('node').order_by('-time_local')[:10]
        
        # 未处理告警
        context['active_alerts'] = Alert.objects.filter(status='firing').select_related('rule', 'node').order_by('-started_at')[:10]
        
        # 最近错误日志
        context['recent_errors'] = ErrorLog.objects.select_related('node').order_by('-time_local')[:10]
        
        return context


def dashboard_data_api(request):
    """仪表板数据API"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    permissions = get_user_permissions(request.user)
    if not permissions.get('can_view_dashboard', False):
        return JsonResponse({'error': '无权限'}, status=403)
    
    # 获取最近7天的请求统计数据
    from django.utils import timezone
    from datetime import timedelta
    from monitoring.models import MetricData
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    # 每日请求统计
    daily_stats = []
    current = start_date
    while current <= end_date:
        next_day = current + timedelta(days=1)
        count = AccessLog.objects.filter(time_local__range=[current, next_day]).count()
        daily_stats.append({
            'date': current.strftime('%Y-%m-%d'),
            'count': count
        })
        current = next_day
    
    # 状态码分布
    status_codes = list(AccessLog.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # Top IP地址
    top_ips = list(AccessLog.objects.values('remote_addr').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # Top URL
    top_urls = list(AccessLog.objects.values('request_uri').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    data = {
        'daily_stats': daily_stats,
        'status_codes': status_codes,
        'top_ips': top_ips,
        'top_urls': top_urls,
    }
    
    return JsonResponse(data)


def user_profile_view(request):
    """用户资料视图"""
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    return render(request, 'accounts/profile.html', {
        'user': request.user,
        'permissions': get_user_permissions(request.user)
    })
