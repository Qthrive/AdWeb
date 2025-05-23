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
    STATUS_CHOICES = [
        ('unread', '未读'),
        ('read', '已读'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name='接收用户')
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
        return f"{self.user.username} - {self.title}"
    
