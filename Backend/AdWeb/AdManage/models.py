from django.db import models
from Users.models import User
from django.utils import timezone

class Campaign(models.Model):
    STATUS_CHOICES = [
        ('active', '进行中'),
        ('paused', '已暂停'),
        ('ended', '已结束'),
        ('deleted', '已删除')
    ]

    name = models.CharField(max_length=100, verbose_name='活动名称')
    advertiser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaigns')
    budget = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='总预算')
    start_date = models.DateTimeField(verbose_name='开始时间')
    end_date = models.DateTimeField(verbose_name='结束时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_remaining_budget(self):
        # 计算剩余预算
        spent = sum(ad.calculate_remaining_budget() for ad in self.ads.all())
        return max(0, self.budget - spent)

    def check_and_update_status(self):
        """检查并更新广告活动状态"""
        now = timezone.now()
        # 如果当前状态是active（进行中）或paused（已暂停），且结束时间已过
        if self.status in ['active', 'paused'] and now > self.end_date:
            self.status = 'ended'
            self.save(update_fields=['status'])
            return True
        return False

    class Meta:
        verbose_name = '广告活动'
        verbose_name_plural = '广告活动'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
