"""
Nginx管理Agent模块
通过SSH连接到Nginx节点执行管理命令
"""

import paramiko
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class NginxStatus(Enum):
    """Nginx状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    output: str
    error: str
    return_code: int


class NginxAgent:
    """
    Nginx管理Agent
    负责通过SSH连接到Nginx节点并执行管理命令
    """
    
    def __init__(self, host: str, port: int = 22, username: str = "root", 
                 password: Optional[str] = None, key_path: Optional[str] = None):
        """
        初始化Nginx Agent
        
        Args:
            host: Nginx节点主机地址
            port: SSH端口，默认22
            username: SSH用户名
            password: SSH密码（可选）
            key_path: SSH私钥路径（可选）
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self.client = None
        
    def connect(self) -> bool:
        """
        建立SSH连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if self.key_path:
                # 使用SSH密钥连接
                private_key = paramiko.RSAKey.from_private_key_file(self.key_path)
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=10
                )
            else:
                # 使用密码连接
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=10
                )
            
            logger.info(f"成功连接到Nginx节点: {self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"连接Nginx节点失败 {self.host}:{self.port}: {str(e)}")
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.client:
            self.client.close()
            logger.info(f"断开与Nginx节点的连接: {self.host}")
    
    def execute_command(self, command: str) -> CommandResult:
        """
        在远程节点上执行命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            CommandResult: 命令执行结果
        """
        if not self.client:
            if not self.connect():
                return CommandResult(
                    success=False,
                    output="",
                    error="SSH连接失败",
                    return_code=-1
                )
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
            return_code = stdout.channel.recv_exit_status()
            
            success = return_code == 0
            
            if success:
                logger.info(f"命令执行成功 [{self.host}]: {command}")
            else:
                logger.error(f"命令执行失败 [{self.host}]: {command}, 错误: {error}")
            
            return CommandResult(
                success=success,
                output=output,
                error=error,
                return_code=return_code
            )
            
        except Exception as e:
            logger.error(f"执行命令时发生异常 [{self.host}]: {command}, 错误: {str(e)}")
            return CommandResult(
                success=False,
                output="",
                error=f"执行异常: {str(e)}",
                return_code=-1
            )
    
    def check_nginx_status(self) -> Tuple[NginxStatus, str]:
        """
        检查Nginx运行状态
        
        Returns:
            Tuple[NginxStatus, str]: (状态, 状态信息)
        """
        # 检查Nginx进程
        result = self.execute_command("ps aux | grep nginx | grep -v grep")
        if not result.success or not result.output:
            return NginxStatus.INACTIVE, "Nginx未运行"
        
        # 检查Nginx配置
        result = self.execute_command("nginx -t 2>&1")
        if not result.success:
            return NginxStatus.ERROR, f"配置错误: {result.error}"
        
        # 检查Nginx是否在监听端口
        result = self.execute_command("netstat -tlnp | grep nginx")
        if not result.success or not result.output:
            result = self.execute_command("ss -tlnp | grep nginx")
        
        if result.success and result.output:
            return NginxStatus.ACTIVE, "Nginx运行正常"
        else:
            return NginxStatus.ERROR, "Nginx进程存在但未监听端口"
    
    def start_nginx(self) -> CommandResult:
        """启动Nginx服务"""
        # 检查是否已经运行
        status, _ = self.check_nginx_status()
        if status == NginxStatus.ACTIVE:
            return CommandResult(
                success=True,
                output="Nginx已经在运行中",
                error="",
                return_code=0
            )
        
        # 尝试启动Nginx
        result = self.execute_command("nginx")
        if result.success:
            # 验证是否启动成功
            import time
            time.sleep(2)
            status, message = self.check_nginx_status()
            if status == NginxStatus.ACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx启动成功",
                    error="",
                    return_code=0
                )
            else:
                return CommandResult(
                    success=False,
                    output="",
                    error=f"Nginx启动失败: {message}",
                    return_code=1
                )
        
        # 如果nginx命令失败，尝试使用systemctl
        result = self.execute_command("systemctl start nginx")
        if result.success:
            time.sleep(2)
            status, message = self.check_nginx_status()
            if status == NginxStatus.ACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx通过systemctl启动成功",
                    error="",
                    return_code=0
                )
        
        # 如果systemctl失败，尝试使用service
        result = self.execute_command("service nginx start")
        if result.success:
            time.sleep(2)
            status, message = self.check_nginx_status()
            if status == NginxStatus.ACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx通过service启动成功",
                    error="",
                    return_code=0
                )
        
        return CommandResult(
            success=False,
            output="",
            error="无法启动Nginx，请检查Nginx是否已安装",
            return_code=1
        )
    
    def stop_nginx(self) -> CommandResult:
        """停止Nginx服务"""
        # 尝试多种停止方式
        
        # 1. 使用nginx -s quit
        result = self.execute_command("nginx -s quit")
        if result.success:
            import time
            time.sleep(2)
            status, _ = self.check_nginx_status()
            if status == NginxStatus.INACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx已正常停止",
                    error="",
                    return_code=0
                )
        
        # 2. 使用systemctl
        result = self.execute_command("systemctl stop nginx")
        if result.success:
            time.sleep(2)
            status, _ = self.check_nginx_status()
            if status == NginxStatus.INACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx通过systemctl停止成功",
                    error="",
                    return_code=0
                )
        
        # 3. 使用service
        result = self.execute_command("service nginx stop")
        if result.success:
            time.sleep(2)
            status, _ = self.check_nginx_status()
            if status == NginxStatus.INACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx通过service停止成功",
                    error="",
                    return_code=0
                )
        
        # 4. 强制杀死进程
        result = self.execute_command("pkill -f nginx")
        if result.success:
            time.sleep(2)
            status, _ = self.check_nginx_status()
            if status == NginxStatus.INACTIVE:
                return CommandResult(
                    success=True,
                    output="Nginx进程已强制终止",
                    error="",
                    return_code=0
                )
        
        return CommandResult(
            success=False,
            output="",
            error="无法停止Nginx服务",
            return_code=1
        )
    
    def reload_nginx(self) -> CommandResult:
        """重载Nginx配置"""
        # 先检查配置
        result = self.execute_command("nginx -t 2>&1")
        if not result.success:
            return CommandResult(
                success=False,
                output="",
                error=f"配置检查失败: {result.error}",
                return_code=1
            )
        
        # 重载配置
        result = self.execute_command("nginx -s reload")
        if result.success:
            return CommandResult(
                success=True,
                output="Nginx配置重载成功",
                error="",
                return_code=0
            )
        
        # 如果nginx -s reload失败，尝试systemctl
        result = self.execute_command("systemctl reload nginx")
        if result.success:
            return CommandResult(
                success=True,
                output="Nginx配置通过systemctl重载成功",
                error="",
                return_code=0
            )
        
        # 如果systemctl失败，尝试service
        result = self.execute_command("service nginx reload")
        if result.success:
            return CommandResult(
                success=True,
                output="Nginx配置通过service重载成功",
                error="",
                return_code=0
            )
        
        return CommandResult(
            success=False,
            output="",
            error="无法重载Nginx配置",
            return_code=1
        )
    
    def get_nginx_info(self) -> Dict:
        """
        获取Nginx详细信息
        
        Returns:
            Dict: Nginx信息字典
        """
        info = {
            "version": "",
            "configure_arguments": "",
            "modules": [],
            "config_path": "",
            "error_log_path": "",
            "access_log_path": "",
        }
        
        # 获取版本和配置信息
        result = self.execute_command("nginx -V 2>&1")
        if result.success:
            lines = result.error.split('\n') if result.error else result.output.split('\n')
            for line in lines:
                if "nginx version:" in line.lower():
                    info["version"] = line.strip()
                elif "configure arguments:" in line.lower():
                    info["configure_arguments"] = line.strip()
        
        # 获取配置路径
        result = self.execute_command("nginx -t 2>&1")
        if result.success or result.output:
            lines = (result.output + '\n' + result.error).split('\n')
            for line in lines:
                if "configuration file" in line.lower():
                    info["config_path"] = line.split("configuration file ")[-1].strip()
                    break
        
        # 从配置文件中获取日志路径
        if info["config_path"] and info["config_path"].startswith('/'):
            result = self.execute_command(f"grep -E 'error_log|access_log' {info['config_path']}")
            if result.success:
                lines = result.output.split('\n')
                for line in lines:
                    if 'error_log' in line and not info["error_log_path"]:
                        parts = line.split()
                        if len(parts) >= 2:
                            info["error_log_path"] = parts[1].rstrip(';')
                    elif 'access_log' in line and not info["access_log_path"]:
                        parts = line.split()
                        if len(parts) >= 2:
                            info["access_log_path"] = parts[1].rstrip(';')
        
        return info
    
    def test_connection(self) -> CommandResult:
        """
        测试SSH连接和基本命令执行
        
        Returns:
            CommandResult: 测试结果
        """
        # 测试连接
        if not self.connect():
            return CommandResult(
                success=False,
                output="",
                error="SSH连接失败",
                return_code=1
            )
        
        # 测试基本命令
        result = self.execute_command("echo 'Connection test' && uname -a")
        if result.success:
            return CommandResult(
                success=True,
                output=f"连接成功: {result.output}",
                error="",
                return_code=0
            )
        else:
            return CommandResult(
                success=False,
                output="",
                error=f"命令执行失败: {result.error}",
                return_code=1
            )


def create_nginx_agent(node) -> Optional[NginxAgent]:
    """
    根据Nginx节点对象创建Agent
    
    Args:
        node: NginxNode模型实例
        
    Returns:
        Optional[NginxAgent]: NginxAgent实例或None
    """
    return NginxAgent(
        host=node.host,
        port=node.ssh_port or 22,  # 使用节点配置的SSH端口，默认22
        username=node.ssh_username or 'root',  # 使用节点配置的SSH用户名，默认root
        password=node.ssh_password,  # 使用节点配置的SSH密码
        key_path=node.ssh_key_path  # 使用节点配置的SSH私钥路径
    )
