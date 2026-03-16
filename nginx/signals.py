"""
Django Signals for nginx app
自动在规则变更时触发配置生成和应用
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import RouteRule, RateLimitRule, RedirectRule, IPBlockRule, NginxNode
from .config_generator import sync_node_config

logger = logging.getLogger(__name__)


@receiver(post_save, sender=RouteRule)
def apply_config_on_route_rule_save(sender, instance, created, **kwargs):
    """
    路由规则保存后自动应用配置
    """
    if instance.is_active:
        # 在事务提交后执行，确保数据已写入数据库
        transaction.on_commit(
            lambda: _sync_node_config_async(instance.node_id, '路由规则', instance.name, created)
        )
    else:
        logger.info(f"路由规则 '{instance.name}' 已保存但处于禁用状态，未应用配置")


@receiver(post_save, sender=RateLimitRule)
def apply_config_on_rate_limit_rule_save(sender, instance, created, **kwargs):
    """
    限流规则保存后自动应用配置
    """
    if instance.is_active:
        transaction.on_commit(
            lambda: _sync_node_config_async(instance.node_id, '限流规则', instance.name, created)
        )
    else:
        logger.info(f"限流规则 '{instance.name}' 已保存但处于禁用状态，未应用配置")


@receiver(post_save, sender=RedirectRule)
def apply_config_on_redirect_rule_save(sender, instance, created, **kwargs):
    """
    重定向规则保存后自动应用配置
    """
    if instance.is_active:
        transaction.on_commit(
            lambda: _sync_node_config_async(instance.node_id, '重定向规则', instance.name, created)
        )
    else:
        logger.info(f"重定向规则 '{instance.name}' 已保存但处于禁用状态，未应用配置")


@receiver(post_save, sender=IPBlockRule)
def apply_config_on_ip_block_rule_save(sender, instance, created, **kwargs):
    """
    IP封禁规则保存后自动应用配置
    """
    if instance.is_active:
        transaction.on_commit(
            lambda: _sync_node_config_async(instance.node_id, 'IP封禁规则', instance.name, created)
        )
    else:
        logger.info(f"IP封禁规则 '{instance.name}' 已保存但处于禁用状态，未应用配置")


@receiver(post_delete, sender=RouteRule)
def apply_config_on_route_rule_delete(sender, instance, **kwargs):
    """
    路由规则删除后自动应用配置
    """
    transaction.on_commit(
        lambda: _sync_node_config_async(instance.node_id, '路由规则', instance.name, False, deleted=True)
    )


@receiver(post_delete, sender=RateLimitRule)
def apply_config_on_rate_limit_rule_delete(sender, instance, **kwargs):
    """
    限流规则删除后自动应用配置
    """
    transaction.on_commit(
        lambda: _sync_node_config_async(instance.node_id, '限流规则', instance.name, False, deleted=True)
    )


@receiver(post_delete, sender=RedirectRule)
def apply_config_on_redirect_rule_delete(sender, instance, **kwargs):
    """
    重定向规则删除后自动应用配置
    """
    transaction.on_commit(
        lambda: _sync_node_config_async(instance.node_id, '重定向规则', instance.name, False, deleted=True)
    )


@receiver(post_delete, sender=IPBlockRule)
def apply_config_on_ip_block_rule_delete(sender, instance, **kwargs):
    """
    IP封禁规则删除后自动应用配置
    """
    transaction.on_commit(
        lambda: _sync_node_config_async(instance.node_id, 'IP封禁规则', instance.name, False, deleted=True)
    )


def _sync_node_config_async(node_id, rule_type, rule_name, created, deleted=False):
    """
    异步同步节点配置
    
    Args:
        node_id: 节点ID
        rule_type: 规则类型
        rule_name: 规则名称
        created: 是否为新创建
        deleted: 是否被删除
    """
    try:
        action = "创建" if created else "更新"
        if deleted:
            action = "删除"
        
        logger.info(f"规则变更触发配置同步: {rule_type} '{rule_name}' 已{action}，正在同步节点 {node_id}")
        
        # 同步配置
        success = sync_node_config(node_id)
        
        if success:
            logger.info(f"节点 {node_id} 配置同步成功（由{rule_type} '{rule_name}' {action}触发）")
        else:
            logger.error(f"节点 {node_id} 配置同步失败（由{rule_type} '{rule_name}' {action}触发）")
            
    except Exception as e:
        logger.error(f"异步同步节点配置失败: {str(e)}")


@receiver(post_save, sender=NginxNode)
def test_node_connection_on_save(sender, instance, created, **kwargs):
    """
    Nginx节点保存后测试连接
    """
    if created:
        from .agent import create_nginx_agent
        
        def test_connection():
            try:
                logger.info(f"测试新节点连接: {instance.name}")
                agent = create_nginx_agent(instance)
                if agent:
                    if agent.connect():
                        logger.info(f"节点 {instance.name} 连接测试成功")
                        instance.status = 'active'
                        instance.save()
                        agent.disconnect()
                    else:
                        logger.warning(f"节点 {instance.name} 连接测试失败")
                        instance.status = 'error'
                        instance.save()
            except Exception as e:
                logger.error(f"测试节点连接失败: {str(e)}")
        
        transaction.on_commit(test_connection)
