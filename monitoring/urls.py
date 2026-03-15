from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    # 访问日志
    path('access-logs/', views.AccessLogListView.as_view(), name='access_log_list'),
    
    # 错误日志
    path('error-logs/', views.ErrorLogListView.as_view(), name='error_log_list'),
    
    # 监控仪表板
    path('dashboard/', views.MonitoringDashboardView.as_view(), name='dashboard'),
    path('api/monitoring-data/', views.monitoring_data_api, name='monitoring_data_api'),
    
    # 告警规则
    path('alert-rules/', views.AlertRuleListView.as_view(), name='alert_rule_list'),
    path('alert-rules/add/', views.AlertRuleCreateView.as_view(), name='alert_rule_add'),
    path('alert-rules/<int:pk>/edit/', views.AlertRuleUpdateView.as_view(), name='alert_rule_edit'),
    path('alert-rules/<int:pk>/delete/', views.AlertRuleDeleteView.as_view(), name='alert_rule_delete'),
    
    # 告警记录
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    
    # 日志分析报告
    path('reports/', views.LogAnalysisReportListView.as_view(), name='report_list'),
    path('api/generate-report/', views.generate_report_api, name='generate_report_api'),
    path('api/log-analysis/', views.log_analysis_api, name='log_analysis_api'),
]
