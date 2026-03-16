from django import forms
from .models import NginxNode, RouteRule, RateLimitRule, RedirectRule, IPBlockRule


class NginxNodeForm(forms.ModelForm):
    """Nginx节点表单"""
    class Meta:
        model = NginxNode
        fields = ['name', 'host', 'port', 'status', 'config_path', 'description', 
                 'ssh_port', 'ssh_username', 'ssh_password', 'ssh_key_path']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入节点名称'}),
            'host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入主机地址'}),
            'port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '请输入端口号'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'config_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入配置文件路径'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入描述信息'}),
            'ssh_port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'SSH端口，默认22'}),
            'ssh_username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SSH用户名，默认root'}),
            'ssh_password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'SSH密码（可选）'}, render_value=True),
            'ssh_key_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SSH私钥路径，如：/root/.ssh/id_rsa'}),
        }


class RouteRuleForm(forms.ModelForm):
    """路由规则表单"""
    class Meta:
        model = RouteRule
        fields = ['name', 'node', 'domain', 'path', 'rule_type', 
                 'upstream_host', 'upstream_port', 'root_path', 
                 'redirect_url', 'redirect_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'}),
            'node': forms.Select(attrs={'class': 'form-control'}),
            'domain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'example.com'}),
            'path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/api/ or /static/'}),
            'rule_type': forms.Select(attrs={'class': 'form-control'}),
            'upstream_host': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '后端服务器地址'}),
            'upstream_port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '后端服务器端口'}),
            'root_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/var/www/static'}),
            'redirect_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/new-url'}),
            'redirect_type': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '301 or 302'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RateLimitRuleForm(forms.ModelForm):
    """限流规则表单"""
    class Meta:
        model = RateLimitRule
        fields = ['name', 'node', 'limit_by', 'requests_per_second', 'burst', 
                 'domains', 'paths', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'}),
            'node': forms.Select(attrs={'class': 'form-control'}),
            'limit_by': forms.Select(attrs={'class': 'form-control'}),
            'requests_per_second': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '每秒请求数'}),
            'burst': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '突发请求数'}),
            'domains': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'example.com,api.example.com（留空表示所有域名）'}),
            'paths': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': '/api/,/login/（留空表示所有路径）'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RedirectRuleForm(forms.ModelForm):
    """重定向规则表单"""
    class Meta:
        model = RedirectRule
        fields = ['name', 'node', 'source_domain', 'source_path', 
                 'target_url', 'redirect_type', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'}),
            'node': forms.Select(attrs={'class': 'form-control'}),
            'source_domain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '旧域名，如：old.example.com'}),
            'source_path': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '旧路径，如：/old-path（可选）'}),
            'target_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '新URL，如：https://new.example.com/new-path'}),
            'redirect_type': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '301（永久）或 302（临时）'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class IPBlockRuleForm(forms.ModelForm):
    """IP封禁规则表单"""
    class Meta:
        model = IPBlockRule
        fields = ['name', 'node', 'ip_address', 'subnet_mask', 
                 'action', 'domains', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'}),
            'node': forms.Select(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'IP地址，如：192.168.1.100'}),
            'subnet_mask': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '子网掩码（可选），如：24'}),
            'action': forms.Select(attrs={'class': 'form-control'}),
            'domains': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'example.com,api.example.com（留空表示所有域名）'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
