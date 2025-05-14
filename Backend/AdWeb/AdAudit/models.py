from django.db import models
from django.conf import settings
from AdPlace.models import Ad

class AuditLog(models.Model):
    """广告审核日志"""
    ACTION_CHOICES = (
        ('approve', '通过'),
        ('reject', '拒绝'),
    )
    
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, verbose_name='广告')
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='审核人')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name='审核结果')
    reason = models.TextField(verbose_name='审核意见')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='审核时间')
    
    class Meta:
        verbose_name = '审核日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.ad.name} - {self.get_action_display()}'
