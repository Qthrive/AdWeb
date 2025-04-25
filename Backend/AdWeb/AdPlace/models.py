from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import os
# Create your models here.
class Ad(models.Model):
    STATUS_CHOICES = [
        ('pending','待审核'),
        ('active','投放中'),
        ('ended','已结束'),
        ('rejected','已拒绝'),
        ('deleted','已删除')
    ]
    PLACEMENT_CHOICES = [
        ('banner','横幅广告'),
        ('sidebar','侧边栏广告'),
        ('popup','弹窗广告'),
        ('text','文字广告'),
    ]
    # 广告ID
    advertiser = models.ForeignKey('Users.User', on_delete=models.CASCADE, related_name='ads')
    # 类型
    placement_type = models.CharField(max_length=20, choices=PLACEMENT_CHOICES, default='banner')
    # 预算
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    # daily_limit
    daily_limit = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 上传广告图片
    image = models.ImageField(
        upload_to='ads/images/',
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ]
    )
    # 开始时间
    start_date = models.DateTimeField()
    # 结束时间
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def validate_image_format(self):
        valid_formats = ['jpg', 'jpeg', 'png']
        if not any(self.image.name.endswith(ext) for ext in valid_formats):
            raise ValidationError(f"Unsupported image format. Supported formats: {', '.join(valid_formats)}")
    
    def calculate_remaining_budget(self):
        # 计算剩余预算
        spent = self.transaction_set.aggregate(total = models.Sum('amount'))['total'] or 0
        return max(0, self.budget - spent)
    
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
    placement_type = models.CharField(max_length=20, choices=Ad.PLACEMENT_CHOICES, default='banner')
    # 区域大小
    dimension = models.CharField(max_length=20, blank=True, null=True)
    # price_per_day
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)

    @classmethod
    def get_available_placements(cls):
        # 获取所有可用广告位
        return cls.objects.filter(placement_type__in=[choice[0] for choice in cls.PLACEMENT_CHOICES])