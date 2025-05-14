from django.db import models
from AdPlace.models import Ad
from django.utils import timezone

class AdImpression(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='impressions')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        verbose_name = '广告展示'
        verbose_name_plural = '广告展示'
        indexes = [
            models.Index(fields=['ad', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.ad} - {self.timestamp}"

class AdClick(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='clicks')
    impression = models.ForeignKey(AdImpression, on_delete=models.SET_NULL, null=True, related_name='clicks')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)

    class Meta:
        verbose_name = '广告点击'
        verbose_name_plural = '广告点击'
        indexes = [
            models.Index(fields=['ad', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.ad} - {self.timestamp}"

class DailyStats(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '每日统计'
        verbose_name_plural = '每日统计'
        unique_together = ['ad', 'date']
        indexes = [
            models.Index(fields=['ad', 'date']),
        ]

    def __str__(self):
        return f"{self.ad} - {self.date}"

    @classmethod
    def update_stats(cls, ad, date=None):
        if date is None:
            date = timezone.now().date()
        
        stats, created = cls.objects.get_or_create(ad=ad, date=date)
        
        # 更新统计数据
        stats.impressions = AdImpression.objects.filter(
            ad=ad,
            timestamp__date=date
        ).count()
        
        stats.clicks = AdClick.objects.filter(
            ad=ad,
            timestamp__date=date
        ).count()
        
        stats.cost = (
            AdImpression.objects.filter(
                ad=ad,
                timestamp__date=date
            ).aggregate(total=models.Sum('cost'))['total'] or 0
        ) + (
            AdClick.objects.filter(
                ad=ad,
                timestamp__date=date
            ).aggregate(total=models.Sum('cost'))['total'] or 0
        )
        
        stats.save()
        return stats
