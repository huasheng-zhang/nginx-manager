"""
Nginx Agent REST API
提供RESTful接口接收前端指令并执行远程命令
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404

from accounts.permissions import get_user_permissions
from .models import NginxNode
from .agent import create_nginx_agent, NginxAgent, CommandResult

logger = logging.getLogger(__name__)


class NginxAgentAPI(View):
    """
    Nginx Agent REST API
    提供REST接口接收前端指令并执行远程命令
    """
    
    http_method_names = ['get', 'post', 'put', 'delete']
    
    @method_decorator(login_required)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """请求分发，添加认证和缓存控制"""
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, node_id=None):
        """
        GET 请求 - 获取节点信息或状态
        
        Args:
            request: HTTP请求
            node_id: 节点ID（可选）
        """
        try:
            # 检查权限
            permissions = get_user_permissions(request.user)
            if not permissions.get('can_view_nodes', False):
                return JsonResponse({'error': '无权限查看节点'}, status=403)
            
            if node_id:
                # 获取单个节点信息
                node = get_object_or_404(NginxNode, pk=node_id)
                agent = create_nginx_agent(node)
                if not agent:
                    return JsonResponse({'error': '无法创建Agent'}, status=500)
                
                try:
                    # 测试连接
                    result = agent.test_connection()
                    status, message = agent.check_nginx_status()
                    info = agent.get_nginx_info()
                    
                    return JsonResponse({
                        'success': True,
                        'node': {
                            'id': node.id,
                            'name': node.name,
                            'host': node.host,
                            'port': node.port,
                            'status': status.value,
                            'status_display': message,
                            'connection_test': result.success,
                            'info': info
                        }
                    })
                finally:
                    agent.disconnect()
            else:
                # 获取所有节点列表
                nodes = NginxNode.objects.all()
                node_list = []
                
                for node in nodes:
                    node_list.append({
                        'id': node.id,
                        'name': node.name,
                        'host': node.host,
                        'port': node.port,
                        'status': node.status,
                        'status_display': node.get_status_display(),
                        'description': node.description,
                        'created_at': node.created_at.isoformat()
                    })
                
                return JsonResponse({
                    'success': True,
                    'nodes': node_list,
                    'total': len(node_list)
                })
                
        except Exception as e:
            logger.error(f"获取节点信息失败: {str(e)}")
            return JsonResponse({
                'error': f'获取节点信息失败: {str(e)}'
            }, status=500)
    
    def post(self, request, node_id=None):
        """
        POST 请求 - 执行命令或操作
        
        Args:
            request: HTTP请求
            node_id: 节点ID（必需）
        """
        try:
            if not node_id:
                return JsonResponse({'error': '必须提供node_id'}, status=400)
            
            # 检查权限
            permissions = get_user_permissions(request.user)
            if not permissions.get('can_edit_nodes', False):
                return JsonResponse({'error': '无权限管理节点'}, status=403)
            
            # 解析请求体
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({'error': '无效的JSON格式'}, status=400)
            
            # 获取参数
            command = data.get('command')
            action = data.get('action')
            timeout = int(data.get('timeout', 30))
            
            if not command and not action:
                return JsonResponse({'error': '必须提供command或action参数'}, status=400)
            
            # 获取节点
            node = get_object_or_404(NginxNode, pk=node_id)
            agent = create_nginx_agent(node)
            if not agent:
                return JsonResponse({'error': '无法创建Agent'}, status=500)
            
            try:
                if action:
                    # 执行预定义操作
                    return self._execute_action(agent, node, action, timeout)
                else:
                    # 执行自定义命令
                    return self._execute_custom_command(agent, command, timeout)
            finally:
                agent.disconnect()
                
        except Exception as e:
            logger.error(f"执行命令失败: {str(e)}")
            return JsonResponse({
                'error': f'执行命令失败: {str(e)}'
            }, status=500)
    
    def _execute_action(self, agent: NginxAgent, node, action: str, timeout: int):
        """
        执行预定义操作
        
        Args:
            agent: NginxAgent实例
            node: NginxNode对象
            action: 操作类型
            timeout: 超时时间
        """
        action_map = {
            'start': agent.start_nginx,
            'stop': agent.stop_nginx,
            'reload': agent.reload_nginx,
            'restart': agent.restart_nginx,
            'test': agent.test_connection,
            'status': lambda: agent.check_nginx_status(),
        }
        
        if action not in action_map:
            return JsonResponse({'error': f'不支持的操作: {action}'}, status=400)
        
        # 执行操作
        if action in ['status']:
            # status返回tuple
            status, message = action_map[action]()
            return JsonResponse({
                'success': True,
                'action': action,
                'status': status.value,
                'message': message
            })
        else:
            # 其他返回CommandResult
            result = action_map[action]()
            if result.success:
                # 更新节点状态（如果是start/stop/restart）
                if action == 'start' and result.success:
                    node.status = 'active'
                    node.save()
                elif action == 'stop' and result.success:
                    node.status = 'inactive'
                    node.save()
                elif action == 'restart':
                    if result.success:
                        node.status = 'active'
                    else:
                        node.status = 'error'
                    node.save()
                
                return JsonResponse({
                    'success': True,
                    'action': action,
                    'message': result.output,
                    'return_code': result.return_code
                })
            else:
                return JsonResponse({
                    'success': False,
                    'action': action,
                    'error': result.error,
                    'return_code': result.return_code
                }, status=500)
    
    def _execute_custom_command(self, agent: NginxAgent, command: str, timeout: int):
        """
        执行自定义命令
        
        Args:
            agent: NginxAgent实例
            command: 要执行的命令
            timeout: 超时时间
        """
        # 安全限制：禁止执行危险命令
        dangerous_commands = [
            'rm -rf /', 'dd if=', 'mkfs.', ':(){', 'wget', 'curl',
            'nc -l', 'ncat -l', 'bash -i', 'sh -i'
        ]
        
        for dangerous in dangerous_commands:
            if dangerous in command:
                logger.warning(f"尝试执行危险命令被拒绝: {command}")
                return JsonResponse({
                    'error': '命令包含危险操作，已被拒绝'
                }, status=403)
        
        # 执行命令
        result = agent.execute_command(command)
        
        return JsonResponse({
            'success': result.success,
            'command': command,
            'output': result.output,
            'error': result.error,
            'return_code': result.return_code
        })


@csrf_exempt
@require_http_methods(["POST"])
def nginx_agent_batch_api(request):
    """
    批量执行命令的API
    
    请求格式：
    {
        "nodes": [1, 2, 3],  # 节点ID列表
        "command": "nginx -t",  # 要执行的命令
        "action": "status"  # 或预定义操作
    }
    """
    try:
        # 检查权限
        if not request.user.is_authenticated:
            return JsonResponse({'error': '未登录'}, status=401)
        
        permissions = get_user_permissions(request.user)
        if not permissions.get('can_edit_nodes', False):
            return JsonResponse({'error': '无权限执行此操作'}, status=403)
        
        # 解析请求体
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的JSON格式'}, status=400)
        
        node_ids = data.get('nodes', [])
        command = data.get('command')
        action = data.get('action')
        
        if not node_ids:
            return JsonResponse({'error': '必须提供nodes参数'}, status=400)
        
        if not command and not action:
            return JsonResponse({'error': '必须提供command或action参数'}, status=400)
        
        # 执行批量操作
        results = []
        
        for node_id in node_ids:
            try:
                node = get_object_or_404(NginxNode, pk=node_id)
                agent = create_nginx_agent(node)
                
                if not agent:
                    results.append({
                        'node_id': node_id,
                        'node_name': node.name,
                        'success': False,
                        'error': '无法创建Agent'
                    })
                    continue
                
                try:
                    if action:
                        # 执行预定义操作
                        action_map = {
                            'start': agent.start_nginx,
                            'stop': agent.stop_nginx,
                            'reload': agent.reload_nginx,
                            'restart': agent.restart_nginx,
                            'test': agent.test_connection,
                        }
                        
                        if action in action_map:
                            result = action_map[action]()
                            results.append({
                                'node_id': node_id,
                                'node_name': node.name,
                                'success': result.success,
                                'output': result.output,
                                'error': result.error,
                                'return_code': result.return_code
                            })
                        else:
                            results.append({
                                'node_id': node_id,
                                'node_name': node.name,
                                'success': False,
                                'error': f'不支持的操作: {action}'
                            })
                    else:
                        # 执行自定义命令
                        result = agent.execute_command(command)
                        results.append({
                            'node_id': node_id,
                            'node_name': node.name,
                            'success': result.success,
                            'command': command,
                            'output': result.output,
                            'error': result.error,
                            'return_code': result.return_code
                        })
                finally:
                    agent.disconnect()
                    
            except Exception as e:
                results.append({
                    'node_id': node_id,
                    'success': False,
                    'error': f'执行失败: {str(e)}'
                })
        
        # 统计结果
        total = len(results)
        success_count = sum(1 for r in results if r.get('success', False))
        
        return JsonResponse({
            'success': True,
            'batch_id': f"batch_{int(time.time())}",
            'total': total,
            'success_count': success_count,
            'failed_count': total - success_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"批量执行命令失败: {str(e)}")
        return JsonResponse({
            'error': f'批量执行命令失败: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def nginx_agent_health_api(request):
    """
    Agent 健康检查 API
    
    返回 Agent 服务的运行状态
    """
    try:
        # 检查数据库连接
        from django.db import connection
        connection.ensure_connection()
        db_status = "ok"
    except:
        db_status = "error"
    
    try:
        # 检查 Redis 连接
        from django_redis import get_redis_connection
        redis_conn = get_redis_connection("default")
        redis_conn.ping()
        redis_status = "ok"
    except:
        redis_status = "error"
    
    return JsonResponse({
        'status': 'healthy' if db_status == "ok" and redis_status == "ok" else 'unhealthy',
        'database': db_status,
        'redis': redis_status,
        'service': 'nginx_agent_api'
    })
