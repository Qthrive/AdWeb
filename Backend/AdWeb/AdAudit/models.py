from django.db import models
from django.utils import timezone


class Review(models.Model):
    reviewId = models.AutoField(primary_key=True)
    adId = models.IntegerField()
    reviewerId = models.IntegerField()
    STATUS_CHOICES = (
        ('通过', '通过'),
        ('驳回', '驳回')
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    comment = models.TextField()
    reviewTime = models.DateTimeField(default=timezone.now)

    def recordReviewResult(self):
        self.save()


class Ad(models.Model):
    # 广告 ID，自动递增主键
    id = models.AutoField(primary_key=True)
    # 广告名称
    name = models.CharField(max_length=200)
    # 广告状态，可选值为待审核、通过、驳回
    STATUS_CHOICES = (
        ('待审核', '待审核'),
        ('通过', '通过'),
        ('驳回', '驳回')
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='待审核')
    # 广告创建时间，自动记录创建时的时间
    create_time = models.DateTimeField(auto_now_add=True)
    # 广告更新时间，自动记录更新时的时间
    update_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


from django.db import models

# Create your models here.
