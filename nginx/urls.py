from django.urls import path
from . import views
from . import api

app_name = 'nginx'

urlpatterns = [
    # Nginx节点管理
    path('nodes/', views.NginxNodeListView.as_view(), name='node_list'),
    path('nodes/<int:pk>/', views.NginxNodeDetailView.as_view(), name='node_detail'),
    path('nodes/add/', views.NginxNodeCreateView.as_view(), name='node_add'),
    path('nodes/<int:pk>/edit/', views.NginxNodeUpdateView.as_view(), name='node_edit'),
    path('nodes/<int:pk>/delete/', views.NginxNodeDeleteView.as_view(), name='node_delete'),
    
    # 路由规则管理
    path('routes/', views.RouteRuleListView.as_view(), name='route_list'),
    path('routes/add/', views.RouteRuleCreateView.as_view(), name='route_add'),
    path('routes/<int:pk>/edit/', views.RouteRuleUpdateView.as_view(), name='route_edit'),
    path('routes/<int:pk>/delete/', views.RouteRuleDeleteView.as_view(), name='route_delete'),
    
    # 限流规则管理
    path('rate-limits/', views.RateLimitRuleListView.as_view(), name='rate_limit_list'),
    path('rate-limits/add/', views.RateLimitRuleCreateView.as_view(), name='rate_limit_add'),
    path('rate-limits/<int:pk>/edit/', views.RateLimitRuleUpdateView.as_view(), name='rate_limit_edit'),
    path('rate-limits/<int:pk>/delete/', views.RateLimitRuleDeleteView.as_view(), name='rate_limit_delete'),
    
    # 重定向规则管理
    path('redirects/', views.RedirectRuleListView.as_view(), name='redirect_list'),
    path('redirects/add/', views.RedirectRuleCreateView.as_view(), name='redirect_add'),
    path('redirects/<int:pk>/edit/', views.RedirectRuleUpdateView.as_view(), name='redirect_edit'),
    path('redirects/<int:pk>/delete/', views.RedirectRuleDeleteView.as_view(), name='redirect_delete'),
    
    # IP封禁管理
    path('ip-blocks/', views.IPBlockRuleListView.as_view(), name='ip_block_list'),
    path('ip-blocks/add/', views.IPBlockRuleCreateView.as_view(), name='ip_block_add'),
    path('ip-blocks/<int:pk>/edit/', views.IPBlockRuleUpdateView.as_view(), name='ip_block_edit'),
    path('ip-blocks/<int:pk>/delete/', views.IPBlockRuleDeleteView.as_view(), name='ip_block_delete'),
    
    # API - 原有接口
    path('api/toggle-rule/<str:rule_type>/<int:pk>/', views.toggle_rule_status, name='toggle_rule_status'),
    path('api/nodes/<int:node_id>/<str:action>/', views.manage_nginx_node, name='manage_node'),
    
    # API - 新的RESTful Agent API
    path('api/v1/agent/', api.NginxAgentAPI.as_view(), name='agent_api_root'),
    path('api/v1/agent/nodes/', api.NginxAgentAPI.as_view(), name='agent_api_nodes'),
    path('api/v1/agent/nodes/<int:node_id>/', api.NginxAgentAPI.as_view(), name='agent_api_node_detail'),
    
    # 批量操作API
    path('api/v1/agent/batch/', api.nginx_agent_batch_api, name='agent_api_batch'),
    
    # 健康检查API
    path('api/v1/agent/health/', api.nginx_agent_health_api, name='agent_api_health'),
]
