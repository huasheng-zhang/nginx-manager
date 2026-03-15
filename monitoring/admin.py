from django.contrib import admin
from .models import (
    AccessLog, ErrorLog, MetricData,
    AlertRule, Alert, LogAnalysisReport
)


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['remote_addr', 'status', 'time_local', 'request_method', 'request_uri', 'node']
    list_filter = ['status', 'time_local', 'request_method', 'node']
    search_fields = ['remote_addr', 'request_uri', 'http_user_agent']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ['node', 'log_level', 'time_local', 'message']
    list_filter = ['log_level', 'time_local', 'node']
    search_fields = ['message', 'client', 'server']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(MetricData)
class MetricDataAdmin(admin.ModelAdmin):
    list_display = ['node', 'timestamp', 'active_connections', 'requests_per_second', 'avg_response_time']
    list_filter = ['timestamp', 'node']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'node', 'metric', 'comparison', 'threshold', 'duration', 'severity', 'is_active']
    list_filter = ['severity', 'is_active', 'metric', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['rule', 'node', 'status', 'severity', 'started_at', 'resolved_at']
    list_filter = ['status', 'severity', 'started_at', 'node']
    search_fields = ['message']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(LogAnalysisReport)
class LogAnalysisReportAdmin(admin.ModelAdmin):
    list_display = ['node', 'report_type', 'start_time', 'end_time', 'total_requests', 'generated_at']
    list_filter = ['report_type', 'generated_at', 'node']
    search_fields = ['node__name']
    readonly_fields = ['generated_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
