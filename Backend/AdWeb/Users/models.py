from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
# Create your models here.
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', '管理员'),
        ('advertiser', '广告主'),
    )
    
    AUDIT_STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
    )

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
    )
    email = models.EmailField(unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)

    AUDIT_STATUS_CHOICES = [
        ('pending', '待审核'),
        ('approved', '已批准'),
        ('rejected', '已拒绝')
    ]
    audit_status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default='pending')
    audit_time = models.DateTimeField(null=True, blank=True)

    USER_TYPE_CHOICES = [
        ('admin', '管理员'),
        ('advertiser', '广告主')
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='advertiser')

    register_ip = models.GenericIPAddressField(null=True, blank=True)
    device_info = models.TextField(null=True, blank=True)  # 设备信息
    reject_reason = models.TextField(null=True, blank=True)  # 拒绝原因
    
    # 扩展用户资料字段
    phone = models.CharField(max_length=11, blank=True, null=True, verbose_name='手机号码')
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name='公司名称')
    job_title = models.CharField(max_length=50, blank=True, null=True, verbose_name='职位')
    bio = models.TextField(blank=True, null=True, verbose_name='个人简介')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class ValidationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expire_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expire_at


class Notification(models.Model):
    STATUS_CHOICES = (
        ('unread', '未读'),
        ('read', '已读'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unread', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='阅读时间')
    
    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class AuditLog(models.Model):
    """审核日志记录模型"""
    AUDIT_TYPE_CHOICES = (
        ('user_register', '用户注册'),
        ('password_reset', '密码重置'),
    )
    
    ACTION_CHOICES = (
        ('approve', '批准'),
        ('reject', '拒绝'),
    )
    
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES, verbose_name='审核类型')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs', verbose_name='目标用户')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviewed_logs', verbose_name='审核人')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='操作')
    remark = models.TextField(verbose_name='备注', blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='审核时间')
    
    class Meta:
        verbose_name = '审核日志'
        verbose_name_plural = '审核日志'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_audit_type_display()} - {self.target_user.username} - {self.get_action_display()}"

class PasswordResetRequest(models.Model):
    # 密码重置请求状态选项
    STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('completed', '已完成'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_requests')
    token = models.CharField(max_length=100, unique=True, verbose_name='重置令牌')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    reason = models.TextField(verbose_name='重置原因', blank=True)
    admin_remark = models.TextField(verbose_name='管理员备注', blank=True)
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reset_requests')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='批准时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    class Meta:
        verbose_name = '密码重置请求'
        verbose_name_plural = '密码重置请求'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"
    
