from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import User
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm

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

    phone = forms.CharField(
        label='手机号',
        max_length=11,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入手机号'}),
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'password1', 'password2']
        labels = {
            'email': '邮箱',
            'username': '用户名',
            'password1': '密码',
            'password2': '确认密码',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            existing_user = User.objects.get(email=email)
            if not existing_user.is_verified:
                # 如果用户未验证，允许重新注册
                return email
            else:
                raise ValidationError("该邮箱已被注册且已验证")
        except User.DoesNotExist:
            # 如果用户不存在，正常返回邮箱
            return email
    
# 登录表单
class LoginForm(forms.Form):
    email = forms.EmailField(
        label='邮箱',
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'}),
    )

    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '请输入密码'}),
    )

    user_type = forms.ChoiceField(
        label='用户类型',
        choices=(('advertiser', '广告主'), ('admin', '管理员')),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ('email', 'password', 'user_type')
        labels = {
            'email': '邮箱',
            'password': '密码',
            'user_type': '用户类型',
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
    
class CustomPasswordResetForm(DjangoPasswordResetForm):
    def save(self, domain_override=None, subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=None, from_email=None,
             html_email_template_name=None, extra_email_context=None):
        email = self.cleaned_data['email']
        print(f"尝试重置密码的邮箱: {email}")
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        for user in active_users:
            print(f"找到激活用户: {user.email}, ID: {user.id}")
        return super().save(domain_override, subject_template_name, email_template_name, use_https,
                            token_generator, from_email, html_email_template_name, extra_email_context)
    
# 修改个人资料表单 (仅修改用户名)
class ProfileForm(forms.ModelForm):
    username = forms.CharField(
        label='用户名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
    )

    class Meta:
        model = User
        fields = ('username',)  # 只包含 username 字段
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError("该用户名已被注册")
        return username
    
# 其他表单可以根据需要添加
# 例如：重置密码表单、验证邮箱表单等