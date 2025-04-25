from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import User

# 注册表单
class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label='邮箱',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'}),
    )

    username = forms.CharField(
        label='用户名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
    )

    password1 = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'}),
    )

    password2 = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入密码'}),
    )

    class Meta:
        model = User
        fields = ('email', 'username' 'password1', 'password2')
        labels = {
            'username': '用户名',
            'password1': '密码',
            'password2': '确认密码',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("该邮箱已被注册")
        return email
    
# 登录表单
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='邮箱',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'}),
    )

    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'}),
    )

    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {
            'username': '邮箱',
            'password': '密码',
        }