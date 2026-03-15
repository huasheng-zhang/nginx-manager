from django.contrib import admin
from .models import (
    NginxNode, RouteRule, RateLimitRule, 
    RedirectRule, IPBlockRule, NginxConfig
)


@admin.register(NginxNode)
class NginxNodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'host', 'port', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'host', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'host', 'port', 'status', 'description')
        }),
        ('配置信息', {
            'fields': ('config_path',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(RouteRule)
class RouteRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'node', 'domain', 'path', 'rule_type', 'is_active', 'created_at']
    list_filter = ['rule_type', 'is_active', 'created_at', 'node']
    search_fields = ['name', 'domain', 'path']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'node', 'is_active')
        }),
        ('匹配规则', {
            'fields': ('domain', 'path', 'rule_type')
        }),
        ('代理转发配置', {
            'fields': ('upstream_host', 'upstream_port'),
            'classes': ('collapse',)
        }),
        ('静态文件配置', {
            'fields': ('root_path',),
            'classes': ('collapse',)
        }),
        ('重定向配置', {
            'fields': ('redirect_url', 'redirect_type'),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(RateLimitRule)
class RateLimitRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'node', 'limit_by', 'requests_per_second', 'burst', 'is_active', 'created_at']
    list_filter = ['limit_by', 'is_active', 'created_at', 'node']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RedirectRule)
class RedirectRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'node', 'source_domain', 'source_path', 'target_url', 'redirect_type', 'is_active', 'created_at']
    list_filter = ['redirect_type', 'is_active', 'created_at', 'node']
    search_fields = ['name', 'source_domain', 'target_url']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(IPBlockRule)
class IPBlockRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'node', 'ip_address', 'subnet_mask', 'action', 'is_active', 'created_at']
    list_filter = ['action', 'is_active', 'created_at', 'node']
    search_fields = ['name', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(NginxConfig)
class NginxConfigAdmin(admin.ModelAdmin):
    list_display = ['node', 'version', 'created_by', 'created_at']
    list_filter = ['created_at', 'node']
    search_fields = ['node__name', 'version']
    readonly_fields = ['created_at']
