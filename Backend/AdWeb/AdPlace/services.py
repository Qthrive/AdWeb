from .models import Ad, AdPlacement
from django.utils import timezone

class AdService:
    @staticmethod
    def create_ad(user,data):
        ad = Ad(
            advertiser=user,
            placement_type=data.get('placement_type'),
            budget=data.get('budget'),
            daily_limit=data.get('daily_limit'),
            image=data.get('image'),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
        )
        ad.full_clean()  # Validate the model instance
        ad.save()
        return ad
    
    @staticmethod
    def update_ad_status(ad_id, new_status):
        ad = Ad.objects.get(id=ad_id)
        ad.status = new_status
        ad.save()

    @staticmethod
    def get_ad_list(user = None, status = None):
        filters = {}
        if user:
            filters['advertiser'] = user
        if status:
            filters['status'] = status
        return Ad.objects.filter(**filters).order_by('-created_at')

    @staticmethod
    def validate_ad_time_range(start_date, end_date):
        if start_date >= end_date:
            raise ValueError("结束日期必须晚于开始日期")
        if start_date < timezone.now():
            raise ValueError("开始日期不能早于当前日期")
        
    