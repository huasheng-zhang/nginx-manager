"""
Nginx配置生成器
将数据库中的规则转换为Nginx配置
"""

import logging
from typing import List, Dict, Optional
from django.template import Template, Context
from .models import NginxNode, RouteRule, RateLimitRule, RedirectRule, IPBlockRule

logger = logging.getLogger(__name__)


class NginxConfigGenerator:
    """Nginx配置生成器"""
    
    def __init__(self, node: NginxNode):
        self.node = node
    
    def generate_server_config(self) -> str:
        """生成Nginx server配置"""
        server_blocks = []
        
        # 生成每个域名的server块
        domains = self._get_unique_domains()
        
        for domain in domains:
            server_block = self._generate_server_block(domain)
            server_blocks.append(server_block)
        
        return "\n\n".join(server_blocks) if server_blocks else ""
    
    def _get_unique_domains(self) -> List[str]:
        """获取所有唯一的域名"""
        domains = set()
        
        # 从路由规则获取域名
        route_domains = self.node.route_rules.filter(
            is_active=True
        ).values_list('domain', flat=True).distinct()
        domains.update(route_domains)
        
        # 从重定向规则获取源域名
        redirect_domains = self.node.redirect_rules.filter(
            is_active=True
        ).values_list('source_domain', flat=True).distinct()
        domains.update(redirect_domains)
        
        return list(domains)
    
    def _generate_server_block(self, domain: str) -> str:
        """生成单个server块配置"""
        
        # 基础server块
        server_config = f"""server {{
    listen {self.node.port};
    server_name {domain};
    
"""
        
        # 添加IP封禁规则
        ip_block_config = self._generate_ip_block_config(domain)
        if ip_block_config:
            server_config += ip_block_config + "\n"
        
        # 添加限流规则
        rate_limit_config = self._generate_rate_limit_config(domain)
        if rate_limit_config:
            server_config += rate_limit_config + "\n"
        
        # 添加路由规则
        route_config = self._generate_route_config(domain)
        server_config += route_config
        
        # 添加重定向规则
        redirect_config = self._generate_redirect_config(domain)
        if redirect_config:
            server_config += redirect_config + "\n"
        
        server_config += "}\n"
        
        return server_config
    
    def _generate_ip_block_config(self, domain: str) -> str:
        """生成IP封禁配置"""
        ip_rules = self.node.ip_block_rules.filter(
            is_active=True,
            domains__icontains=domain
        )
        
        if not ip_rules:
            return ""
        
        config_lines = []
        for rule in ip_rules:
            subnet = f"/{rule.subnet_mask}" if rule.subnet_mask else ""
            action = "deny" if rule.action == 'deny' else "allow"
            config_lines.append(f"    {action} {rule.ip_address}{subnet};")
        
        return "\n".join(config_lines)
    
    def _generate_rate_limit_config(self, domain: str) -> str:
        """生成限流配置"""
        rate_limit_rules = self.node.rate_limit_rules.filter(
            is_active=True,
            domains__icontains=domain
        )
        
        if not rate_limit_rules:
            return ""
        
        config_lines = []
        for i, rule in enumerate(rate_limit_rules):
            zone_name = f"rate_limit_{i}"
            config_lines.append(
                f"    limit_req_zone $binary_remote_addr zone={zone_name}:10m rate={rule.requests_per_second}r/s;"
            )
        
        return "\n".join(config_lines)
    
    def _generate_route_config(self, domain: str) -> str:
        """生成路由配置"""
        routes = self.node.route_rules.filter(
            is_active=True,
            domain=domain
        ).order_by('-created_at')
        
        if not routes:
            return "    # 默认404\n    location / {\n        return 404;\n    }\n"
        
        config_lines = []
        for route in routes:
            location_block = self._generate_location_block(route)
            config_lines.append(location_block)
        
        return "\n".join(config_lines)
    
    def _generate_location_block(self, route: RouteRule) -> str:
        """生成location块配置"""
        location_block = f"""    location {route.path} {{
"""
        
        if route.rule_type == 'proxy':
            # 代理转发
            if route.upstream_host and route.upstream_port:
                # 添加限流
                rate_limit_rules = self.node.rate_limit_rules.filter(
                    is_active=True,
                    domains__icontains=route.domain,
                    paths__icontains=route.path
                )
                
                for i, rule in enumerate(rate_limit_rules):
                    location_block += f"        limit_req zone=rate_limit_{i} burst={rule.burst};\n"
                
                location_block += f"""        proxy_pass http://{route.upstream_host}:{route.upstream_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
"""
            else:
                location_block += f"        # 错误：未配置上游服务器\n        return 502;\n"
        
        elif route.rule_type == 'static':
            # 静态文件
            if route.root_path:
                location_block += f"""        root {route.root_path};
        index index.html index.htm;
"""
            else:
                location_block += f"        # 错误：未配置根目录\n        return 404;\n"
        
        elif route.rule_type == 'redirect':
            # 重定向
            if route.redirect_url:
                location_block += f"        return {route.redirect_type} {route.redirect_url};\n"
            else:
                location_block += f"        # 错误：未配置重定向URL\n        return 404;\n"
        
        location_block += "    }\n"
        
        return location_block
    
    def _generate_redirect_config(self, domain: str) -> str:
        """生成重定向配置"""
        redirects = self.node.redirect_rules.filter(
            is_active=True,
            source_domain=domain
        )
        
        if not redirects:
            return ""
        
        config_lines = []
        for redirect in redirects:
            path = redirect.source_path or "/"
            config_lines.append(f"    location {path} {{")
            config_lines.append(f"        return {redirect.redirect_type} {redirect.target_url};")
            config_lines.append("    }")
        
        return "\n".join(config_lines)
    
    def generate_full_config(self) -> str:
        """生成完整的Nginx配置"""
        config = f"""# Nginx configuration generated by nginx-manager
# Node: {self.node.name}
# Generated at: {self.node.updated_at}

user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

events {{
    worker_connections 1024;
}}

http {{
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 2048;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    # 包含所有server配置
{self.generate_server_config()}

}}
"""
        return config


def apply_nginx_config(node: NginxNode, agent) -> bool:
    """
    生成并应用Nginx配置到远程节点
    
    Args:
        node: NginxNode实例
        agent: NginxAgent实例
        
    Returns:
        bool: 是否成功应用
    """
    try:
        # 生成配置
        generator = NginxConfigGenerator(node)
        config_content = generator.generate_full_config()
        
        logger.info(f"为节点 {node.name} 生成Nginx配置")
        
        # 备份现有配置
        backup_result = agent.execute_command(f"cp {node.config_path} {node.config_path}.backup")
        if not backup_result.success:
            logger.warning(f"备份现有配置失败: {backup_result.error}")
        
        # 将新配置写入临时文件
        temp_config_path = "/tmp/nginx.conf.new"
        write_result = agent.execute_command(f"cat > {temp_config_path} << 'EOF'\n{config_content}\nEOF")
        if not write_result.success:
            logger.error(f"写入临时配置失败: {write_result.error}")
            return False
        
        # 测试配置
        test_result = agent.execute_command(f"nginx -t -c {temp_config_path}")
        if not test_result.success:
            logger.error(f"Nginx配置测试失败: {test_result.error}")
            # 删除临时文件
            agent.execute_command(f"rm -f {temp_config_path}")
            return False
        
        # 移动配置文件到正确位置
        move_result = agent.execute_command(f"mv {temp_config_path} {node.config_path}")
        if not move_result.success:
            logger.error(f"移动配置文件失败: {move_result.error}")
            return False
        
        # 重新加载Nginx
        reload_result = agent.reload_nginx()
        if reload_result.success:
            logger.info(f"Nginx配置应用成功: {node.name}")
            return True
        else:
            logger.error(f"Nginx重载失败: {reload_result.error}")
            return False
            
    except Exception as e:
        logger.error(f"应用Nginx配置时发生异常: {str(e)}")
        return False


def sync_node_config(node_id: int) -> bool:
    """
    同步指定节点的配置
    
    Args:
        node_id: NginxNode的ID
        
    Returns:
        bool: 是否成功
    """
    try:
        from .models import NginxNode
        from .agent import create_nginx_agent
        
        node = NginxNode.objects.get(pk=node_id)
        agent = create_nginx_agent(node)
        
        if not agent:
            logger.error(f"无法创建Agent: {node.name}")
            return False
        
        try:
            # 测试连接
            if not agent.connect():
                logger.error(f"无法连接到节点: {node.name}")
                return False
            
            # 应用配置
            success = apply_nginx_config(node, agent)
            
            if success:
                node.status = 'active'
                node.save()
            else:
                node.status = 'error'
                node.save()
            
            return success
            
        finally:
            agent.disconnect()
            
    except Exception as e:
        logger.error(f"同步节点配置失败: {str(e)}")
        return False


def sync_all_nodes() -> Dict[str, any]:
    """
    同步所有节点的配置
    
    Returns:
        Dict: 同步结果统计
    """
    from .models import NginxNode
    
    results = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    try:
        nodes = NginxNode.objects.all()
        results['total'] = nodes.count()
        
        for node in nodes:
            logger.info(f"开始同步节点配置: {node.name}")
            success = sync_node_config(node.id)
            
            results['details'].append({
                'node_id': node.id,
                'node_name': node.name,
                'success': success
            })
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"所有节点同步完成: 成功 {results['success']}/{results['total']}")
        
    except Exception as e:
        logger.error(f"同步所有节点失败: {str(e)}")
    
    return results
