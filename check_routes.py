#!/usr/bin/env python
"""检查路由规则配置"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nginx_manager.settings')
django.setup()

from nginx.models import RouteRule

print('='*80)
print('当前路由规则配置')
print('='*80)

rules = RouteRule.objects.all()
if not rules:
    print('ERROR: 没有找到路由规则')
    sys.exit(0)

issues = []

for rule in rules:
    print(f'\n规则名称: {rule.name}')
    print(f'  节点: {rule.node.name}')
    print(f'  域名: {rule.domain}')
    print(f'  路径: {rule.path}')
    print(f'  类型: {rule.get_rule_type_display()}')
    print(f'  上游主机: {rule.upstream_host or "ERROR: 未配置"}')
    print(f'  上游端口: {rule.upstream_port or "ERROR: 未配置"}')
    print(f'  状态: {"启用" if rule.is_active else "禁用"}')
    print('-'*80)
    
    if rule.rule_type == 'proxy':
        if not rule.upstream_host:
            issues.append(f"规则 '{rule.name}' 缺少上游主机")
        if not rule.upstream_port:
            issues.append(f"规则 '{rule.name}' 缺少上游端口")

if issues:
    print('\n发现以下问题:')
    for issue in issues:
        print(f'  - {issue}')
    print('\n请编辑路由规则，填写完整的后端服务信息（上游主机和上游端口）')
else:
    print('\n所有代理规则配置完整')
    print('\n可以运行测试脚本生成Nginx配置:')
    print('  python test_config_generation.py')
