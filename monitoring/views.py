from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta, datetime

from .models import AccessLog, ErrorLog, MetricData, AlertRule, Alert, LogAnalysisReport
from accounts.permissions import PermissionRequiredMixin, get_user_permissions
from .forms import AlertRuleForm


class AccessLogListView(PermissionRequiredMixin, ListView):
    """访问日志列表视图"""
    model = AccessLog
    template_name = 'monitoring/access_log_list.html'
    context_object_name = 'logs'
    permission_required = 'can_view_logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选条件
        node_id = self.request.GET.get('node')
        status = self.request.GET.get('status')
        ip = self.request.GET.get('ip')
        method = self.request.GET.get('method')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if ip:
            queryset = queryset.filter(remote_addr__contains=ip)
        
        if method:
            queryset = queryset.filter(request_method=method)
        
        if start_date:
            queryset = queryset.filter(time_local__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(time_local__lte=end_date)
        
        return queryset.select_related('node').order_by('-time_local')


class ErrorLogListView(PermissionRequiredMixin, ListView):
    """错误日志列表视图"""
    model = ErrorLog
    template_name = 'monitoring/error_log_list.html'
    context_object_name = 'logs'
    permission_required = 'can_view_logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 筛选条件
        node_id = self.request.GET.get('node')
        log_level = self.request.GET.get('log_level')
        ip = self.request.GET.get('ip')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if log_level:
            queryset = queryset.filter(log_level=log_level)
        
        if ip:
            queryset = queryset.filter(client__contains=ip)
        
        if start_date:
            queryset = queryset.filter(time_local__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(time_local__lte=end_date)
        
        return queryset.select_related('node').order_by('-time_local')


class MonitoringDashboardView(PermissionRequiredMixin, ListView):
    """监控仪表板视图"""
    template_name = 'monitoring/dashboard.html'
    permission_required = 'can_view_monitoring'
    
    def get_queryset(self):
        return MetricData.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 获取最近的数据
        from monitoring.models import NginxNode
        
        context['nodes'] = NginxNode.objects.all()
        
        # 获取最近一小时的监控数据
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=1)
        
        recent_metrics = MetricData.objects.filter(
            timestamp__range=[start_time, end_time]
        ).select_related('node')
        
        context['recent_metrics'] = recent_metrics
        
        return context


def monitoring_data_api(request):
    """监控数据API"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    permissions = get_user_permissions(request.user)
    if not permissions.get('can_view_monitoring', False):
        return JsonResponse({'error': '无权限'}, status=403)
    
    node_id = request.GET.get('node')
    hours = int(request.GET.get('hours', 1))
    
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    queryset = MetricData.objects.filter(
        timestamp__range=[start_time, end_time]
    )
    
    if node_id:
        queryset = queryset.filter(node_id=node_id)
    
    data = list(queryset.values(
        'timestamp', 'node__name', 'active_connections', 
        'requests_per_second', 'avg_response_time', 'reading', 'writing', 'waiting'
    ).order_by('timestamp'))
    
    # 格式化时间
    for item in data:
        item['timestamp'] = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    return JsonResponse({'data': data})


class AlertRuleListView(PermissionRequiredMixin, ListView):
    """告警规则列表视图"""
    model = AlertRule
    template_name = 'monitoring/alert_rule_list.html'
    context_object_name = 'alert_rules'
    permission_required = 'can_manage_alerts'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.GET.get('node')
        severity = self.request.GET.get('severity')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.select_related('node').order_by('-created_at')


class AlertRuleCreateView(PermissionRequiredMixin, CreateView):
    """创建告警规则视图"""
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'monitoring/alert_rule_form.html'
    permission_required = 'can_manage_alerts'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, '告警规则创建成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/monitoring/alert-rules/'


class AlertRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """编辑告警规则视图"""
    model = AlertRule
    form_class = AlertRuleForm
    template_name = 'monitoring/alert_rule_form.html'
    permission_required = 'can_manage_alerts'
    
    def form_valid(self, form):
        messages.success(self.request, '告警规则更新成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/monitoring/alert-rules/'


class AlertRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """删除告警规则视图"""
    model = AlertRule
    template_name = 'monitoring/alert_rule_confirm_delete.html'
    permission_required = 'can_manage_alerts'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '告警规则删除成功！')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/monitoring/alert-rules/'


class AlertListView(PermissionRequiredMixin, ListView):
    """告警记录列表视图"""
    model = Alert
    template_name = 'monitoring/alert_list.html'
    context_object_name = 'alerts'
    permission_required = 'can_view_monitoring'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        node_id = self.request.GET.get('node')
        status = self.request.GET.get('status')
        severity = self.request.GET.get('severity')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.select_related('rule', 'node').order_by('-started_at')


class LogAnalysisReportListView(PermissionRequiredMixin, ListView):
    """日志分析报告列表视图"""
    model = LogAnalysisReport
    template_name = 'monitoring/report_list.html'
    context_object_name = 'reports'
    permission_required = 'can_view_reports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        node_id = self.request.GET.get('node')
        report_type = self.request.GET.get('report_type')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if report_type:
            queryset = queryset.filter(report_type=report_type)
        
        return queryset.select_related('node').order_by('-generated_at')


def generate_report_api(request):
    """生成报告API"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    permissions = get_user_permissions(request.user)
    if not permissions.get('can_generate_reports', False):
        return JsonResponse({'error': '无权限'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': '无效请求'}, status=405)
    
    node_id = request.POST.get('node')
    report_type = request.POST.get('report_type')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    
    try:
        from monitoring.tasks import generate_log_report
        generate_log_report(node_id, report_type, start_date, end_date, request.user)
        
        return JsonResponse({'success': True, 'message': '报告生成任务已提交'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def log_analysis_api(request):
    """日志分析API"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    permissions = get_user_permissions(request.user)
    if not permissions.get('can_view_logs', False):
        return JsonResponse({'error': '无权限'}, status=403)
    
    node_id = request.GET.get('node')
    hours = int(request.GET.get('hours', 24))
    
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=hours)
    
    # 基础统计
    base_query = AccessLog.objects.filter(time_local__range=[start_time, end_time])
    
    if node_id:
        base_query = base_query.filter(node_id=node_id)
    
    total_requests = base_query.count()
    unique_visitors = base_query.values('remote_addr').distinct().count()
    
    # 平均响应时间
    avg_response = base_query.aggregate(avg_time=Avg('request_time'))['avg_time'] or 0
    
    # 错误率
    error_count = base_query.filter(status__gte=400).count()
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
    
    # 状态码分布
    status_codes = list(base_query.values('status').annotate(
        count=Count('id')
    ).order_by('-count')[:20])
    
    # Top IP
    top_ips = list(base_query.values('remote_addr').annotate(
        count=Count('id'),
        avg_time=Avg('request_time')
    ).order_by('-count')[:10])
    
    # Top URL
    top_urls = list(base_query.values('request_uri').annotate(
        count=Count('id'),
        avg_time=Avg('request_time')
    ).order_by('-count')[:10])
    
    # 请求方法分布
    methods = list(base_query.values('request_method').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    data = {
        'total_requests': total_requests,
        'unique_visitors': unique_visitors,
        'avg_response_time': round(avg_response, 3),
        'error_rate': round(error_rate, 2),
        'status_codes': status_codes,
        'top_ips': top_ips,
        'top_urls': top_urls,
        'methods': methods,
    }
    
    return JsonResponse(data)
