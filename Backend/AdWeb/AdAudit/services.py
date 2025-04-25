from .models import Review
from django.db.models import Q
import time


class ReviewService:
    def getPendingAds(self):
        # 这里假设 Ad 模型有一个 status 字段表示广告状态，'待审核' 为待审核状态
        # 你需要根据实际情况修改
        from .models import Ad
        pending_ads = Ad.objects.filter(status='待审核').values_list('id', flat=True)
        return list(pending_ads)

    def processReview(self, review):
        try:
            review.recordReviewResult()
            # 模拟更新广告状态
            from .models import Ad
            ad = Ad.objects.get(id=review.adId)
            ad.status = review.status
            ad.save()
            return True
        except Exception as e:
            return False

    def getReviewHistory(self):
        reviews = Review.objects.all().values()
        return list(reviews)
