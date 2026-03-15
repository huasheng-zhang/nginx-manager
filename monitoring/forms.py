from django import forms
from .models import AlertRule


class AlertRuleForm(forms.ModelForm):
    """告警规则表单"""
    class Meta:
        model = AlertRule
        fields = ['name', 'description', 'node', 'metric', 'comparison', 
                 'threshold', 'duration', 'severity', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入规则名称'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '请输入规则描述'}),
            'node': forms.Select(attrs={'class': 'form-control'}),
            'metric': forms.Select(attrs={'class': 'form-control'}),
            'comparison': forms.Select(attrs={'class': 'form-control'}),
            'threshold': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '阈值'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '持续时间（分钟）'}),
            'severity': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
