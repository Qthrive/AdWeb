from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import os
from AdManage.models import Campaign
# Create your models here.
class Ad(models.Model):
    STATUS_CHOICES = [
        ('pending','待审核'),
        ('active','投放中'),
        ('ended','已结束'),
        ('rejected','已拒绝'),
        ('deleted','已删除')
    ]

    # 广告名称
    name = models.CharField(max_length=100, verbose_name='广告名称', default='未命名广告')
    # 广告状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    PLACEMENT_CHOICES = [
        ('banner','横幅广告'),
        ('sidebar','侧边栏广告'),
        ('popup','弹窗广告'),
        ('text','文字广告'),
    ]
    # 广告主
    advertiser = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='ads')
    # 广告位
    placement = models.ForeignKey(
        'AdPlacement',
        on_delete=models.CASCADE,
        related_name='ads'
    )
    # 预算
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    # daily_limit
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 上传广告图片
    image = models.ImageField(
        upload_to='ads/images/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        null=True,  # 允许为空
        blank=True  # 允许在表单中为空
    )
    # 目标链接
    target_url = models.URLField(verbose_name='目标链接', default='http://example.com')
    # 广告描述
    description = models.TextField(verbose_name='广告描述', blank=True)
    # 开始时间
    start_date = models.DateTimeField()
    # 结束时间
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='ads', verbose_name='所属活动', null=True, blank=True)

    def validate_image_format(self):
        valid_formats = ['jpg', 'jpeg', 'png']
        if not any(self.image.name.endswith(ext) for ext in valid_formats):
            raise ValidationError(f"Unsupported image format. Supported formats: {', '.join(valid_formats)}")
    
    def calculate_remaining_budget(self):
        # 暂时直接返回预算值，后续实现交易系统后再修改
        return self.budget
    
    # 检查文件夹是否存在
    def check_folder_exists(self):
        folder_path = os.path.join('ads', 'images')
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def get_impressions(self, start_date=None, end_date=None):
        """获取广告展示次数"""
        impressions = self.impressions.all()
        if start_date:
            impressions = impressions.filter(timestamp__date__gte=start_date)
        if end_date:
            impressions = impressions.filter(timestamp__date__lte=end_date)
        return impressions.count()

    def get_clicks(self, start_date=None, end_date=None):
        """获取广告点击次数"""
        clicks = self.clicks.all()
        if start_date:
            clicks = clicks.filter(timestamp__date__gte=start_date)
        if end_date:
            clicks = clicks.filter(timestamp__date__lte=end_date)
        return clicks.count()

    def get_ctr(self, start_date=None, end_date=None):
        """获取点击率 (Click Through Rate)"""
        impressions = self.get_impressions(start_date, end_date)
        clicks = self.get_clicks(start_date, end_date)
        return f"{(clicks / impressions * 100 if impressions > 0 else 0):.2f}%"

    def get_cost(self, start_date=None, end_date=None):
        """获取广告花费"""
        from django.db.models import Sum
        
        # 从展示记录中获取花费
        impressions = self.impressions.all()
        if start_date:
            impressions = impressions.filter(timestamp__date__gte=start_date)
        if end_date:
            impressions = impressions.filter(timestamp__date__lte=end_date)
        imp_cost = impressions.aggregate(total=Sum('cost'))['total'] or 0

        # 从点击记录中获取花费
        clicks = self.clicks.all()
        if start_date:
            clicks = clicks.filter(timestamp__date__gte=start_date)
        if end_date:
            clicks = clicks.filter(timestamp__date__lte=end_date)
        click_cost = clicks.aggregate(total=Sum('cost'))['total'] or 0

        return imp_cost + click_cost
    
    def get_cpc(self, start_date=None, end_date=None):
        """获取平均点击成本 (Cost Per Click)"""
        clicks = self.get_clicks(start_date, end_date)
        cost = self.get_cost(start_date, end_date)
        return f"{(float(cost) / clicks if clicks > 0 else 0):.2f}"

    def get_daily_stats(self, date):
        """获取指定日期的统计数据"""
        from DataShow.models import DailyStats
        try:
            stats = DailyStats.objects.get(ad=self, date=date)
            return {
                'impressions': stats.impressions,
                'clicks': stats.clicks,
                'cost': stats.cost,
                'ctr': f"{(stats.clicks / stats.impressions * 100 if stats.impressions > 0 else 0):.2f}",
                'cpc': f"{(float(stats.cost) / stats.clicks if stats.clicks > 0 else 0):.2f}"
            }
        except DailyStats.DoesNotExist:
            return {
                'impressions': 0,
                'clicks': 0,
                'cost': 0,
                'ctr': '0.00%',
                'cpc': '0.00'
            }

    def get_stats(self, start_date=None, end_date=None):
        """获取指定时间范围的统计数据"""
        return {
            'impressions': self.get_impressions(start_date, end_date),
            'clicks': self.get_clicks(start_date, end_date),
            'cost': self.get_cost(start_date, end_date),
            'ctr': self.get_ctr(start_date, end_date),
            'cpc': self.get_cpc(start_date, end_date)
        }

class AdPlacement(models.Model):
    PLACEMENT_CHOICES = [
        ('banner','横幅广告'),
        ('sidebar','侧边栏广告'),
        ('popup','弹窗广告'),
        ('text','文字广告'),
    ]
    placement_type = models.CharField(
        max_length=20,
        choices=PLACEMENT_CHOICES,  # 使用本类的 PLACEMENT_CHOICES
        default='banner',
        unique=True  # 确保广告位类型唯一
    )
    # 区域大小
    dimension = models.CharField(max_length=20, blank=True, null=True)
    # price_per_day
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.get_placement_type_display()} ({self.dimension} - ¥{self.price_per_day}/天)"

    @classmethod
    def get_available_placements(cls):
        # 获取所有可用广告位
        return cls.objects.all()  # 返回所有广告位，因为 placement_type 是唯一的