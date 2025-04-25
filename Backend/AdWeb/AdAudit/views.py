from django.http import JsonResponse
from .models import Review
from .services import ReviewService


def get_pending_ads(request):
    review_service = ReviewService()
    pending_ads = review_service.getPendingAds()
    return JsonResponse({'pending_ads': pending_ads})


def process_review(request):
    if request.method == 'POST':
        adId = request.POST.get('adId')
        reviewerId = request.POST.get('reviewerId')
        status = request.POST.get('status')
        comment = request.POST.get('comment')
        review = Review(adId=adId, reviewerId=reviewerId, status=status, comment=comment)
        review_service = ReviewService()
        result = review_service.processReview(review)
        if result:
            return JsonResponse({'message': '审核处理成功'})
        else:
            return JsonResponse({'message': '审核处理失败'}, status=400)


def get_review_history(request):
    review_service = ReviewService()
    history = review_service.getReviewHistory()
    return JsonResponse({'review_history': history})


from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
