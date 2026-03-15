from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import NginxNode, RouteRule, RateLimitRule, RedirectRule, IPBlockRule
from .agent import NginxAgent, create_nginx_agent, NginxStatus
from accounts.permissions import PermissionRequiredMixin, get_user_permissions
from .forms import NginxNodeForm, RouteRuleForm, RateLimitRuleForm, RedirectRuleForm, IPBlockRuleForm
import json


class NginxNodeListView(PermissionRequiredMixin, ListView):
    """Nginx节点列表视图"""
    model = NginxNode
    template_name = 'nginx/node_list.html'
    context_object_name = 'nodes'
    permission_required = 'can_view_nodes'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(host__icontains=search)
            )
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_at')


class NginxNodeDetailView(PermissionRequiredMixin, DetailView):
    """Nginx节点详情视图"""
    model = NginxNode
    template_name = 'nginx/node_detail.html'
    context_object_name = 'node'
    permission_required = 'can_view_nodes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        node = self.object
        
        context['route_rules'] = node.route_rules.filter(is_active=True).order_by('-created_at')[:10]
        context['rate_limit_rules'] = node.rate_limit_rules.filter(is_active=True).order_by('-created_at')[:10]
        context['redirect_rules'] = node.redirect_rules.filter(is_active=True).order_by('-created_at')[:10]
        context['ip_block_rules'] = node.ip_block_rules.filter(is_active=True).order_by('-created_at')[:10]
        
        return context


class NginxNodeCreateView(PermissionRequiredMixin, CreateView):
    """创建Nginx节点视图"""
    model = NginxNode
    form_class = NginxNodeForm
    template_name = 'nginx/node_form.html'
    permission_required = 'can_add_nodes'
    
    def form_valid(self, form):
        messages.success(self.request, 'Nginx节点创建成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/nodes/'


class NginxNodeUpdateView(PermissionRequiredMixin, UpdateView):
    """编辑Nginx节点视图"""
    model = NginxNode
    form_class = NginxNodeForm
    template_name = 'nginx/node_form.html'
    permission_required = 'can_edit_nodes'
    
    def form_valid(self, form):
        messages.success(self.request, 'Nginx节点更新成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return f'/nginx/nodes/{self.object.pk}/'


class NginxNodeDeleteView(PermissionRequiredMixin, DeleteView):
    """删除Nginx节点视图"""
    model = NginxNode
    template_name = 'nginx/node_confirm_delete.html'
    permission_required = 'can_delete_nodes'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Nginx节点删除成功！')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/nginx/nodes/'


class RouteRuleListView(PermissionRequiredMixin, ListView):
    """路由规则列表视图"""
    model = RouteRule
    template_name = 'nginx/route_list.html'
    context_object_name = 'routes'
    permission_required = 'can_view_routes'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.GET.get('node')
        search = self.request.GET.get('search')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(domain__icontains=search) | Q(path__icontains=search)
            )
        
        return queryset.select_related('node').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from nginx.models import NginxNode
        context['nodes'] = NginxNode.objects.all().order_by('name')
        return context


class RouteRuleCreateView(PermissionRequiredMixin, CreateView):
    """创建路由规则视图"""
    model = RouteRule
    form_class = RouteRuleForm
    template_name = 'nginx/route_form.html'
    permission_required = 'can_add_routes'
    
    def form_valid(self, form):
        messages.success(self.request, '路由规则创建成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/routes/'


class RouteRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """编辑路由规则视图"""
    model = RouteRule
    form_class = RouteRuleForm
    template_name = 'nginx/route_form.html'
    permission_required = 'can_edit_routes'
    
    def form_valid(self, form):
        messages.success(self.request, '路由规则更新成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/routes/'


class RouteRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """删除路由规则视图"""
    model = RouteRule
    template_name = 'nginx/route_confirm_delete.html'
    permission_required = 'can_delete_routes'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '路由规则删除成功！')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/nginx/routes/'


class RateLimitRuleListView(PermissionRequiredMixin, ListView):
    """限流规则列表视图"""
    model = RateLimitRule
    template_name = 'nginx/rate_limit_list.html'
    context_object_name = 'rate_limits'
    permission_required = 'can_view_rate_limits'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.GET.get('node')
        search = self.request.GET.get('search')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.select_related('node').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from nginx.models import NginxNode
        context['nodes'] = NginxNode.objects.all().order_by('name')
        return context


class RateLimitRuleCreateView(PermissionRequiredMixin, CreateView):
    """创建限流规则视图"""
    model = RateLimitRule
    form_class = RateLimitRuleForm
    template_name = 'nginx/rate_limit_form.html'
    permission_required = 'can_manage_rate_limits'
    
    def form_valid(self, form):
        messages.success(self.request, '限流规则创建成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/rate-limits/'


class RateLimitRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """编辑限流规则视图"""
    model = RateLimitRule
    form_class = RateLimitRuleForm
    template_name = 'nginx/rate_limit_form.html'
    permission_required = 'can_manage_rate_limits'
    
    def form_valid(self, form):
        messages.success(self.request, '限流规则更新成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/rate-limits/'


class RateLimitRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """删除限流规则视图"""
    model = RateLimitRule
    template_name = 'nginx/rate_limit_confirm_delete.html'
    permission_required = 'can_manage_rate_limits'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '限流规则删除成功！')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/nginx/rate-limits/'


class RedirectRuleListView(PermissionRequiredMixin, ListView):
    """重定向规则列表视图"""
    model = RedirectRule
    template_name = 'nginx/redirect_list.html'
    context_object_name = 'redirects'
    permission_required = 'can_view_redirects'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.GET.get('node')
        search = self.request.GET.get('search')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(source_domain__icontains=search)
            )
        
        return queryset.select_related('node').order_by('-created_at')


class RedirectRuleCreateView(PermissionRequiredMixin, CreateView):
    """创建重定向规则视图"""
    model = RedirectRule
    form_class = RedirectRuleForm
    template_name = 'nginx/redirect_form.html'
    permission_required = 'can_manage_redirects'
    
    def form_valid(self, form):
        messages.success(self.request, '重定向规则创建成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/redirects/'


class RedirectRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """编辑重定向规则视图"""
    model = RedirectRule
    form_class = RedirectRuleForm
    template_name = 'nginx/redirect_form.html'
    permission_required = 'can_manage_redirects'
    
    def form_valid(self, form):
        messages.success(self.request, '重定向规则更新成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/redirects/'


class RedirectRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """删除重定向规则视图"""
    model = RedirectRule
    template_name = 'nginx/redirect_confirm_delete.html'
    permission_required = 'can_manage_redirects'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, '重定向规则删除成功！')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/nginx/redirects/'


class IPBlockRuleListView(PermissionRequiredMixin, ListView):
    """IP封禁规则列表视图"""
    model = IPBlockRule
    template_name = 'nginx/ip_block_list.html'
    context_object_name = 'ip_blocks'
    permission_required = 'can_view_ip_blocks'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.GET.get('node')
        search = self.request.GET.get('search')
        action = self.request.GET.get('action')
        
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(ip_address__icontains=search)
            )
        
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset.select_related('node').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from nginx.models import NginxNode
        context['nodes'] = NginxNode.objects.all().order_by('name')
        return context


class IPBlockRuleCreateView(PermissionRequiredMixin, CreateView):
    """创建IP封禁规则视图"""
    model = IPBlockRule
    form_class = IPBlockRuleForm
    template_name = 'nginx/ip_block_form.html'
    permission_required = 'can_manage_ip_blocks'
    
    def form_valid(self, form):
        messages.success(self.request, 'IP封禁规则创建成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/ip-blocks/'


class IPBlockRuleUpdateView(PermissionRequiredMixin, UpdateView):
    """编辑IP封禁规则视图"""
    model = IPBlockRule
    form_class = IPBlockRuleForm
    template_name = 'nginx/ip_block_form.html'
    permission_required = 'can_manage_ip_blocks'
    
    def form_valid(self, form):
        messages.success(self.request, 'IP封禁规则更新成功！')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/nginx/ip-blocks/'


class IPBlockRuleDeleteView(PermissionRequiredMixin, DeleteView):
    """删除IP封禁规则视图"""
    model = IPBlockRule
    template_name = 'nginx/ip_block_confirm_delete.html'
    permission_required = 'can_manage_ip_blocks'
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'IP封禁规则删除成功！')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return '/nginx/ip-blocks/'


def toggle_rule_status(request, rule_type, pk):
    """切换规则状态（启用/禁用）"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': '无效请求'}, status=405)
    
    # 根据规则类型获取模型
    model_map = {
        'route': RouteRule,
        'rate_limit': RateLimitRule,
        'redirect': RedirectRule,
        'ip_block': IPBlockRule,
    }
    
    model = model_map.get(rule_type)
    if not model:
        return JsonResponse({'error': '无效的规则类型'}, status=400)
    
    rule = get_object_or_404(model, pk=pk)
    
    # 检查权限
    permission_map = {
        'route': 'can_edit_routes',
        'rate_limit': 'can_manage_rate_limits',
        'redirect': 'can_manage_redirects',
        'ip_block': 'can_manage_ip_blocks',
    }
    
    permissions = get_user_permissions(request.user)
    required_permission = permission_map.get(rule_type)
    
    if not permissions.get(required_permission, False):
        return JsonResponse({'error': '无权限'}, status=403)
    
    # 切换状态
    rule.is_active = not rule.is_active
    rule.save()
    
    return JsonResponse({
        'success': True,
        'is_active': rule.is_active,
        'status_display': '启用' if rule.is_active else '禁用'
    })


@require_POST
def manage_nginx_node(request, node_id, action):
    """
    管理Nginx节点
    
    Args:
        request: HTTP请求
        node_id: Nginx节点ID
        action: 操作类型 (start, stop, reload, restart, status, test)
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': '未登录'}, status=401)
    
    # 检查权限
    permissions = get_user_permissions(request.user)
    if not permissions.get('can_edit_nodes', False):
        return JsonResponse({'error': '无权限管理Nginx节点'}, status=403)
    
    # 获取节点
    node = get_object_or_404(NginxNode, pk=node_id)
    
    # 创建agent
    agent = create_nginx_agent(node)
    if not agent:
        return JsonResponse({
            'error': '无法创建Nginx Agent，请检查SSH配置'
        }, status=500)
    
    try:
        if action == 'test':
            # 测试连接
            result = agent.test_connection()
            if result.success:
                return JsonResponse({
                    'success': True,
                    'message': '连接测试成功',
                    'output': result.output
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': '连接测试失败',
                    'error': result.error
                }, status=500)
        
        elif action == 'status':
            # 检查状态
            status, message = agent.check_nginx_status()
            
            # 更新数据库中的状态
            node.status = status.value
            node.save()
            
            # 获取详细信息
            info = agent.get_nginx_info()
            
            return JsonResponse({
                'success': True,
                'status': status.value,
                'status_display': message,
                'info': info,
                'node_status': node.get_status_display()
            })
        
        elif action == 'start':
            # 启动Nginx
            result = agent.start_nginx()
            if result.success:
                # 更新状态
                node.status = NginxStatus.ACTIVE.value
                node.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Nginx启动成功',
                    'output': result.output
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Nginx启动失败',
                    'error': result.error
                }, status=500)
        
        elif action == 'stop':
            # 停止Nginx
            result = agent.stop_nginx()
            if result.success:
                # 更新状态
                node.status = NginxStatus.INACTIVE.value
                node.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Nginx停止成功',
                    'output': result.output
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Nginx停止失败',
                    'error': result.error
                }, status=500)
        
        elif action == 'reload':
            # 重载配置
            result = agent.reload_nginx()
            if result.success:
                return JsonResponse({
                    'success': True,
                    'message': 'Nginx配置重载成功',
                    'output': result.output
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Nginx配置重载失败',
                    'error': result.error
                }, status=500)
        
        elif action == 'restart':
            # 重启Nginx（先停止再启动）
            stop_result = agent.stop_nginx()
            if not stop_result.success:
                # 如果停止失败，但仍然尝试启动
                pass
            
            import time
            time.sleep(2)
            
            start_result = agent.start_nginx()
            if start_result.success:
                node.status = NginxStatus.ACTIVE.value
                node.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Nginx重启成功',
                    'output': start_result.output
                })
            else:
                node.status = NginxStatus.ERROR.value
                node.save()
                
                return JsonResponse({
                    'success': False,
                    'message': 'Nginx重启失败',
                    'error': start_result.error
                }, status=500)
        
        else:
            return JsonResponse({
                'error': f'无效的操作: {action}'
            }, status=400)
    
    except Exception as e:
        logger.error(f"管理Nginx节点时发生异常: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': '操作过程中发生异常',
            'error': str(e)
        }, status=500)
    
    finally:
        if agent:
            agent.disconnect()
