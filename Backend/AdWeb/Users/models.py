from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
# Create your models here.
class User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",  # 添加 related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # 添加 related_name
        blank=True,
    )
    email = models.EmailField(unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class ValidationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    expire_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expire_at
    
