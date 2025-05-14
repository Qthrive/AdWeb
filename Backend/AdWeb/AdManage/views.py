from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from .models import Campaign
from AdPlace.models import Ad, AdPlacement
from Payment.services import PaymentService
from django.db.models import Sum
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from Users.models import Notification

@login_required
def platform_home(request):
    """广告主平台首页"""
    user = request.user
    # 获取用户的广告活动
    campaigns = Campaign.objects.filter(advertiser=user).order_by('-created_at')
    # 获取用户的广告
    ads = Ad.objects.filter(advertiser=user).order_by('-created_at')
    
    # 计算总预算和已消耗
    total_budget = sum(campaign.budget for campaign in campaigns)
    total_spent = sum(ad.calculate_remaining_budget() for ad in ads)
    
    context = {
        'campaigns': campaigns,
        'ads': ads,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'balance': user.balance,
    }
    return render(request, 'AdManage/platform_home.html', context)

@login_required
def campaign_list(request):
    """广告活动列表"""
    campaigns = Campaign.objects.filter(advertiser=request.user).order_by('-created_at')
    paginator = Paginator(campaigns, 10)  # 每页显示10条
    page = request.GET.get('page')
    campaigns = paginator.get_page(page)
    return render(request, 'AdManage/campaign_list.html', {'campaigns': campaigns})

@login_required
def campaign_create(request):
    """创建广告活动"""
    if request.method == 'POST':
        name = request.POST.get('name')
        budget = request.POST.get('budget')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            campaign = Campaign.objects.create(
                name=name,
                advertiser=request.user,
                budget=budget,
                start_date=start_date,
                end_date=end_date
            )
            messages.success(request, '广告活动创建成功！')
            return redirect('admanage:campaign_detail', campaign_id=campaign.id)
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
    
    return render(request, 'AdManage/campaign_create.html')

@login_required
def campaign_detail(request, campaign_id):
    """广告活动详情"""
    campaign = get_object_or_404(Campaign, id=campaign_id, advertiser=request.user)
    ads = Ad.objects.filter(campaign=campaign).order_by('-created_at')
    
    # 计算活动数据
    total_spent = sum(ad.calculate_remaining_budget() for ad in ads)
    remaining_budget = campaign.calculate_remaining_budget()
    
    context = {
        'campaign': campaign,
        'ads': ads,
        'total_spent': total_spent,
        'remaining_budget': remaining_budget,
    }
    return render(request, 'AdManage/campaign_detail.html', context)

@login_required
def campaign_edit(request, campaign_id):
    """编辑广告活动"""
    campaign = get_object_or_404(Campaign, id=campaign_id, advertiser=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        budget = request.POST.get('budget')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        try:
            campaign.name = name
            campaign.budget = budget
            campaign.start_date = start_date
            campaign.end_date = end_date
            campaign.save()
            messages.success(request, '广告活动更新成功！')
            return redirect('admanage:campaign_detail', campaign_id=campaign.id)
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    return render(request, 'AdManage/campaign_edit.html', {'campaign': campaign})

@login_required
def campaign_delete(request, campaign_id):
    """删除广告活动"""
    campaign = get_object_or_404(Campaign, id=campaign_id, advertiser=request.user)
    
    if request.method == 'POST':
        try:
            campaign.status = 'deleted'
            campaign.save()
            messages.success(request, '广告活动已删除！')
            return redirect('admanage:campaign_list')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return render(request, 'AdManage/campaign_confirm_delete.html', {'campaign': campaign})

@login_required
def ad_create(request, campaign_id):
    """创建广告"""
    campaign = get_object_or_404(Campaign, id=campaign_id, advertiser=request.user)
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            name = request.POST.get('name')
            ad_placement_id = request.POST.get('ad_placement')
            budget = request.POST.get('budget')
            daily_limit = request.POST.get('daily_limit')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            target_url = request.POST.get('target_url')
            description = request.POST.get('description')
            
            # 处理时间
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d %H:%M'))
                end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d %H:%M'))
            except ValueError as e:
                raise ValueError('日期格式错误，请使用正确的日期格式')
            
            # 获取广告位
            ad_placement = get_object_or_404(AdPlacement, id=ad_placement_id)
            
            # 处理广告素材
            file_path = None
            if ad_placement.placement_type != 'text':  # 非文字广告才需要图片
                creative = request.FILES.get('creative')
                if not creative:
                    raise ValueError('请上传广告素材')
                
                # 保存广告素材
                file_name = f'ads/{campaign.id}/{timezone.now().strftime("%Y%m%d%H%M%S")}_{creative.name}'
                file_path = default_storage.save(file_name, ContentFile(creative.read()))
            
            # 创建广告
            ad = Ad.objects.create(
                name=name,
                campaign=campaign,
                advertiser=request.user,
                placement=ad_placement,
                budget=budget,
                daily_limit=daily_limit,
                start_date=start_date,
                end_date=end_date,
                target_url=target_url,
                description=description,
                image=file_path if file_path else None,  # 文字广告时 image 为 None
                status='pending'  # 初始状态为待审核
            )
            
            messages.success(request, '广告创建成功，等待审核')
            return redirect('admanage:campaign_detail', campaign_id=campaign.id)
            
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
            # 如果保存失败且上传了文件，删除已上传的文件
            if 'file_path' in locals() and file_path:
                default_storage.delete(file_path)
    
    # 获取可用的广告位
    ad_placements = AdPlacement.objects.all()
    
    context = {
        'campaign': campaign,
        'ad_placements': ad_placements,
    }
    return render(request, 'AdManage/ad_create.html', context)

@login_required
def ad_detail(request, campaign_id, ad_id):
    """广告详情页面"""
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        ad = Ad.objects.get(id=ad_id, campaign=campaign)
        
        # 计算广告统计数据
        ad.impressions = ad.get_impressions()
        ad.clicks = ad.get_clicks()
        ad.ctr = ad.get_ctr()
        ad.cpc = ad.get_cpc()
        
        # 获取预算状态
        budget_status = PaymentService.get_ad_budget_status(ad)

        # 查询未读预算预警通知
        notifications = Notification.objects.filter(user=request.user, title__icontains=ad.name, status='unread')
        
        context = {
            'campaign': campaign,
            'ad': ad,
            'budget_status': budget_status,
            'notifications': notifications,
        }
        return render(request, 'AdManage/ad_detail.html', context)
    except Campaign.DoesNotExist:
        messages.error(request, '广告活动不存在')
        return redirect('admanage:campaign_list')
    except Ad.DoesNotExist:
        messages.error(request, '广告不存在')
        return redirect('admanage:campaign_detail', campaign_id=campaign_id)

@login_required
def ad_edit(request, campaign_id, ad_id):
    """编辑广告"""
    try:
        campaign = Campaign.objects.get(id=campaign_id, advertiser=request.user)
        ad = Ad.objects.get(id=ad_id, campaign=campaign)
        
        if request.method == 'POST':
            try:
                # 获取表单数据
                name = request.POST.get('name')
                ad_placement_id = request.POST.get('ad_placement')
                budget = request.POST.get('budget')
                start_date = request.POST.get('start_date')
                end_date = request.POST.get('end_date')
                target_url = request.POST.get('target_url')
                description = request.POST.get('description')
                status = request.POST.get('status')
                
                # 获取广告位
                ad_placement = get_object_or_404(AdPlacement, id=ad_placement_id)
                
                # 更新广告信息
                ad.name = name
                ad.placement = ad_placement
                ad.budget = budget
                ad.start_date = start_date
                ad.end_date = end_date
                ad.target_url = target_url
                ad.description = description
                ad.status = status
                
                # 处理新的广告素材（如果有）
                creative = request.FILES.get('creative')
                if creative:
                    # 删除旧的素材文件
                    if ad.image:
                        default_storage.delete(ad.image.path)
                    
                    # 保存新的素材文件
                    file_name = f'ads/{campaign.id}/{timezone.now().strftime("%Y%m%d%H%M%S")}_{creative.name}'
                    file_path = default_storage.save(file_name, ContentFile(creative.read()))
                    ad.image = file_path
                
                ad.save()
                messages.success(request, '广告更新成功！')
                return redirect('admanage:ad_detail', campaign_id=campaign.id, ad_id=ad.id)
                
            except Exception as e:
                messages.error(request, f'更新失败：{str(e)}')
                # 如果保存失败且上传了新文件，删除新文件
                if 'file_path' in locals():
                    default_storage.delete(file_path)
        
        # 获取可用的广告位
        ad_placements = AdPlacement.objects.all()
        
        context = {
            'campaign': campaign,
            'ad': ad,
            'ad_placements': ad_placements,
        }
        return render(request, 'AdManage/ad_edit.html', context)
        
    except Campaign.DoesNotExist:
        messages.error(request, '广告活动不存在')
        return redirect('admanage:campaign_list')
    except Ad.DoesNotExist:
        messages.error(request, '广告不存在')
        return redirect('admanage:campaign_detail', campaign_id=campaign_id)

@login_required
def ad_delete(request, campaign_id, ad_id):
    """删除广告"""
    try:
        campaign = Campaign.objects.get(id=campaign_id, advertiser=request.user)
        ad = Ad.objects.get(id=ad_id, campaign=campaign)
        
        if request.method == 'POST':
            try:
                # 删除广告素材文件
                if ad.image:
                    default_storage.delete(ad.image.path)
                
                # 删除广告记录
                ad.delete()
                messages.success(request, '广告已成功删除！')
                return redirect('admanage:campaign_detail', campaign_id=campaign.id)
                
            except Exception as e:
                messages.error(request, f'删除失败：{str(e)}')
        
        context = {
            'campaign': campaign,
            'ad': ad,
        }
        return render(request, 'AdManage/ad_delete.html', context)
        
    except Campaign.DoesNotExist:
        messages.error(request, '广告活动不存在')
        return redirect('admanage:campaign_list')
    except Ad.DoesNotExist:
        messages.error(request, '广告不存在')
        return redirect('admanage:campaign_detail', campaign_id=campaign_id)

@login_required
def ad_stats(request, campaign_id, ad_id):
    """广告数据统计"""
    try:
        campaign = Campaign.objects.get(id=campaign_id, advertiser=request.user)
        ad = Ad.objects.get(id=ad_id, campaign=campaign)
        
        # 获取时间范围
        date_range = request.GET.get('date_range', 'last7days')
        today = timezone.now().date()
        
        if date_range == 'today':
            start_date = today
            end_date = today
        elif date_range == 'yesterday':
            start_date = today - timezone.timedelta(days=1)
            end_date = start_date
        elif date_range == 'last7days':
            start_date = today - timezone.timedelta(days=7)
            end_date = today
        elif date_range == 'last30days':
            start_date = today - timezone.timedelta(days=30)
            end_date = today
        else:  # custom
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            if not start_date or not end_date:
                start_date = today - timezone.timedelta(days=7)
                end_date = today
            else:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # 获取当前时间范围的数据
        current_data = ad.get_stats(start_date, end_date)
        
        # 获取上一时间范围的数据（用于计算环比）
        days_diff = (end_date - start_date).days + 1
        prev_start_date = start_date - timezone.timedelta(days=days_diff)
        prev_end_date = start_date - timezone.timedelta(days=1)
        prev_data = ad.get_stats(prev_start_date, prev_end_date)
        
        # 计算环比变化
        def calculate_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round((current - previous) / previous * 100, 2)
        
        # 准备图表数据
        dates = []
        impressions = []
        clicks = []
        costs = []
        daily_data = []
        
        current_date = start_date
        while current_date <= end_date:
            daily_stats = ad.get_daily_stats(current_date)
            dates.append(current_date.strftime('%Y-%m-%d'))
            impressions.append(daily_stats['impressions'])
            clicks.append(daily_stats['clicks'])
            costs.append(float(daily_stats['cost']))
            
            daily_data.append({
                'date': current_date,
                'impressions': daily_stats['impressions'],
                'clicks': daily_stats['clicks'],
                'ctr': daily_stats['ctr'],
                'cost': daily_stats['cost'],
                'cpc': daily_stats['cpc']
            })
            
            current_date += timezone.timedelta(days=1)
        
        context = {
            'campaign': campaign,
            'ad': ad,
            'date_range': date_range,
            'start_date': start_date,
            'end_date': end_date,
            'total_impressions': current_data['impressions'],
            'total_clicks': current_data['clicks'],
            'ctr': current_data['ctr'],
            'total_cost': current_data['cost'],
            'impression_change': calculate_change(current_data['impressions'], prev_data['impressions']),
            'click_change': calculate_change(current_data['clicks'], prev_data['clicks']),
            'ctr_change': calculate_change(float(current_data['ctr'].rstrip('%')), float(prev_data['ctr'].rstrip('%'))),
            'cost_change': calculate_change(float(current_data['cost']), float(prev_data['cost'])),
            'dates': dates,
            'impressions': impressions,
            'clicks': clicks,
            'costs': costs,
            'daily_data': daily_data,
        }
        
        return render(request, 'AdManage/ad_stats.html', context)
        
    except Campaign.DoesNotExist:
        messages.error(request, '广告活动不存在')
        return redirect('admanage:campaign_list')
    except Ad.DoesNotExist:
        messages.error(request, '广告不存在')
        return redirect('admanage:campaign_detail', campaign_id=campaign_id)