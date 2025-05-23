from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from AdPlace.models import Ad
from .models import AuditLog

def is_admin(user):
    """检查用户是否为管理员"""
    return user.is_staff

@login_required
@user_passes_test(is_admin)
def ad_list(request):
    """广告审核列表"""
    # 获取筛选参数
    status = request.GET.get('status', '')
    advertiser = request.GET.get('advertiser', '')
    date_range = request.GET.get('date_range', '')
    
    # 构建查询
    ads = Ad.objects.all().order_by('-created_at')
    
    if status:
        ads = ads.filter(status=status)
    if advertiser:
        ads = ads.filter(advertiser__username__icontains=advertiser)
    
    # 时间范围筛选
    today = timezone.now().date()
    if date_range == 'today':
        ads = ads.filter(created_at__date=today)
    elif date_range == 'yesterday':
        yesterday = today - timezone.timedelta(days=1)
        ads = ads.filter(created_at__date=yesterday)
    elif date_range == 'last7days':
        last_week = today - timezone.timedelta(days=7)
        ads = ads.filter(created_at__date__gte=last_week)
    elif date_range == 'last30days':
        last_month = today - timezone.timedelta(days=30)
        ads = ads.filter(created_at__date__gte=last_month)
    
    # 分页
    paginator = Paginator(ads, 10)  # 每页显示10条
    page = request.GET.get('page')
    ads = paginator.get_page(page)
    
    context = {
        'ads': ads,
        'status': status,
        'advertiser': advertiser,
        'date_range': date_range,
    }
    return render(request, 'AdAudit/ad_list.html', context)

@login_required
@user_passes_test(is_admin)
def ad_review(request, ad_id):
    """广告审核详情"""
    ad = get_object_or_404(Ad, id=ad_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('reason')
        
        if not action or not reason:
            messages.error(request, '请选择审核结果并填写审核意见')
            return redirect('adaudit:ad_review', ad_id=ad.id)
        
        try:
            # 更新广告状态
            if action == 'approve':
                ad.status = 'approved'
            else:
                ad.status = 'rejected'
            ad.save()
            
            # 记录审核日志
            AuditLog.objects.create(
                ad=ad,
                admin=request.user,
                action=action,
                reason=reason
            )
            
            messages.success(request, '审核完成')
            return redirect('adaudit:ad_list')
            
        except Exception as e:
            messages.error(request, f'审核失败：{str(e)}')
    
    # 获取审核历史
    audit_logs = AuditLog.objects.filter(ad=ad).order_by('-created_at')
    
    context = {
        'ad': ad,
        'audit_logs': audit_logs,
    }
    return render(request, 'AdAudit/ad_review.html', context)
