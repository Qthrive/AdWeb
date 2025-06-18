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
        fields = ['email', 'username', 'password1', 'password2', 'phone']
        labels = {
            'email': '邮箱',
            'username': '用户名',
            'password1': '密码',
            'password2': '确认密码',
            'phone': '手机号',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            existing_user = User.objects.get(email=email)
            # 只有待审核或已批准的用户会导致邮箱验证失败
            if existing_user.audit_status == 'pending':
                raise ValidationError("该邮箱已注册，正在等待管理员审核")
            elif existing_user.audit_status == 'approved':
                raise ValidationError("该邮箱已被注册")
            # 如果是被拒绝的用户，视图函数已经删除了，不应该运行到这里
        except User.DoesNotExist:
            # 如果用户不存在，正常返回邮箱
            pass
        return email
            
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # 由于被拒绝的用户已经在视图函数中被删除，这里只需要检查用户名是否存在
        if User.objects.filter(username=username).exists():
            raise ValidationError("该用户名已被注册")
        return username
    
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
        choices=[('advertiser', '广告主'), ('admin', '管理员')],
        widget=forms.Select(attrs={'class': 'form-control mb-3'}),
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
    email = forms.EmailField(
        label='邮箱',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': '请输入您注册时使用的邮箱',
            'autocomplete': 'email'
        }),
    )
    
    reason = forms.CharField(
        label='重置原因',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': '请简要说明您需要重置密码的原因',
            'rows': '3'
        }),
        required=True
    )
    
    def save(self, request=None, domain_override=None, subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=None, from_email=None,
             html_email_template_name=None, extra_email_context=None):
        email = self.cleaned_data['email']
        reason = self.cleaned_data['reason']
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        
        if active_users.exists():
            user = active_users.first()
            # 创建密码重置请求记录
            from .models import PasswordResetRequest
            from django.utils.crypto import get_random_string
            
            # 生成唯一令牌
            token = get_random_string(64)
            
            # 创建重置请求
            reset_request = PasswordResetRequest.objects.create(
                user=user,
                token=token,
                reason=reason
            )
            
            # 通知管理员
            from .models import Notification
            from django.utils import timezone
            
            # 获取所有管理员
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title='新的密码重置请求',
                    content=f'用户 {user.username}（{user.email}）请求重置密码，请及时审核。'
                )
            
            # 通知用户
            Notification.objects.create(
                user=user,
                title='密码重置请求已提交',
                content='您的密码重置请求已提交，等待管理员审核。审核通过后，您将收到包含重置链接的邮件。'
            )
            
            # 不立即发送邮件，等待管理员审核
            return active_users
            
        return active_users
    
# 修改个人资料表单
class ProfileForm(forms.ModelForm):
    username = forms.CharField(
        label='用户名',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入用户名'}),
    )
    
    email = forms.EmailField(
        label='邮箱',
        required=False,
        disabled=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
    )
    
    phone = forms.CharField(
        label='手机号码',
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入手机号码'}),
    )
    
    company = forms.CharField(
        label='公司名称',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入公司名称'}),
    )
    
    job_title = forms.CharField(
        label='职位',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入您的职位'}),
    )
    
    bio = forms.CharField(
        label='个人简介',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': '请简要介绍自己或您的公司/团队', 
            'rows': '4'
        }),
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'company', 'job_title', 'bio']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError("该用户名已被注册")
        return username
    
# 其他表单可以根据需要添加
# 例如：重置密码表单、验证邮箱表单等