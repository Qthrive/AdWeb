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
            'email': '邮箱',
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

# 修改密码表单
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label='旧密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入旧密码'}),
    )

    new_password1 = forms.CharField(
        label='新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入新密码'}),
    )

    new_password2 = forms.CharField(
        label='确认新密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请再次输入新密码'}),
    )

    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')
        labels = {
            'old_password': '旧密码',
            'new_password1': '新密码',
            'new_password2': '确认新密码',
        }

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError("两次输入的密码不一致")
        return new_password2
    
# 修改个人资料表单
class ProfileForm(forms.ModelForm):
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

    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise ValidationError("该邮箱已被注册")
        return email
    
# 其他表单可以根据需要添加
# 例如：重置密码表单、验证邮箱表单等