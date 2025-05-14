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