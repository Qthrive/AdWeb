from django.test import TestCase
from .models import Review, Ad
from .services import ReviewService


class ReviewTestCase(TestCase):
    def setUp(self):
        self.review_service = ReviewService()
        # 创建模拟的待审核广告
        Ad.objects.create(id=1, status='待审核')
        Ad.objects.create(id=2, status='待审核')

    def test_get_pending_ads(self):
        # 测试获取待审核广告
        pending_ads = self.review_service.getPendingAds()
        self.assertEqual(len(pending_ads), 2)

    def test_process_review(self):
        # 测试处理审核
        review = Review(adId=1, reviewerId=1, status='通过', comment='审核通过')
        result = self.review_service.processReview(review)
        self.assertEqual(result, True)
        ad = Ad.objects.get(id=1)
        self.assertEqual(ad.status, '通过')

    def test_get_review_history(self):
        # 测试获取审核历史
        review = Review(adId=1, reviewerId=1, status='通过', comment='审核通过')
        review.recordReviewResult()
        history = self.review_service.getReviewHistory()
        self.assertEqual(len(history), 1)


from django.test import TestCase

# Create your tests here.
