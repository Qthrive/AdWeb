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
from Users.models import Notification, User
from Payment.models import Invoice
import os
from django.conf import settings
from django.http import JsonResponse, FileResponse, Http404
import shutil
import time
from django.urls import reverse

@login_required
def platform_home(request):
    """广告主平台首页"""
    user = request.user
    
    # 如果是管理员，显示管理员界面
    if user.is_staff:
        # 获取待审核用户
        pending_users = User.objects.filter(audit_status='pending', user_type='advertiser').order_by('-date_joined')
        
        # 获取待审核广告
        pending_ads = Ad.objects.filter(status='pending').order_by('-created_at')
        
        # 获取待处理发票申请
        pending_invoices = Invoice.objects.filter(status='pending').order_by('-created_at')
        
        context = {
            'pending_users': pending_users,
            'pending_ads': pending_ads,
            'pending_invoices': pending_invoices,
        }
    else:
        # 普通广告主界面
        # 获取用户的广告活动
        campaigns = Campaign.objects.filter(advertiser=user).order_by('-created_at')
        
        # 检查并更新过期的广告活动状态
        status_updated = False
        for campaign in campaigns:
            if campaign.check_and_update_status():
                status_updated = True
                
        # 如果有状态更新，重新获取活动列表以反映最新状态
        if status_updated:
            campaigns = Campaign.objects.filter(advertiser=user).order_by('-created_at')
            messages.info(request, '系统已自动更新已过期广告活动的状态')
        
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
    # 获取用户的广告活动
    campaigns = Campaign.objects.filter(advertiser=request.user).order_by('-created_at')
    
    # 检查并更新过期的广告活动状态
    status_updated = False
    for campaign in campaigns:
        if campaign.check_and_update_status():
            status_updated = True
    
    # 如果有状态更新，重新获取活动列表以反映最新状态
    if status_updated:
        campaigns = Campaign.objects.filter(advertiser=request.user).order_by('-created_at')
        messages.info(request, '系统已自动更新已过期广告活动的状态')
    
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
    
    # 检查并更新广告活动状态
    if campaign.check_and_update_status():
        messages.info(request, '该广告活动已过期，状态已更新为"已结束"')
        # 重新获取更新后的活动
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
                status='pending'  # 初始状态为待审核
            )

            # 处理广告素材
            if ad_placement.placement_type != 'text':  # 非文字广告才需要图片
                creative = request.FILES.get('creative')
                if not creative:
                    ad.delete()  # 删除已创建的广告记录
                    raise ValueError('请上传广告素材')
                
                # 验证文件类型
                if not creative.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    ad.delete()
                    raise ValueError('只支持JPG、PNG和GIF格式的图片')
                
                # 验证文件大小
                if creative.size > 2 * 1024 * 1024:  # 2MB
                    ad.delete()
                    raise ValueError('图片大小不能超过2MB')
                
                try:
                    # 生成唯一的图片名称
                    import uuid
                    image_name = f"image-{uuid.uuid4().hex[:8]}{os.path.splitext(creative.name)[1]}"
                    
                    # 1. 首先保存到media目录（Django默认行为）
                    ad.image = creative
                    ad.save()
                    
                    # 2. 获取保存后的文件路径
                    image_path = ad.image.path
                    
                    # 3. 确保文件权限正确
                    os.chmod(image_path, 0o644)
                    
                    # 4. 直接保存到static目录
                    static_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'test-{os.path.basename(ad.image.name)}')
                    shutil.copy2(image_path, static_image_path)
                    
                    # 5. 强制刷新缓存标识
                    ad.updated_at = timezone.now()
                    ad.save(update_fields=['updated_at'])
                    
                    print(f"图片已保存到: {image_path}")
                    print(f"图片副本已保存到: {static_image_path}")
                except Exception as e:
                    print(f"图片处理时出错: {str(e)}")
                    raise ValueError(f"图片处理失败: {str(e)}")
            
            messages.success(request, '广告创建成功，等待审核')
            return redirect('admanage:campaign_detail', campaign_id=campaign.id)
            
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
    
    # 获取可用的广告位
    ad_placements = AdPlacement.objects.all()
    
    context = {
        'campaign': campaign,
        'ad_placements': ad_placements,
    }
    return render(request, 'AdManage/ad_create.html', context)

@login_required
def ad_detail(request, campaign_id, ad_id):
    """广告详情"""
    campaign = get_object_or_404(Campaign, id=campaign_id)
    ad = get_object_or_404(Ad, id=ad_id, campaign=campaign)
    
    # 检查并添加图片调试信息
    image_debug = None
    if ad.image:
        # 创建备份路径 - 同步检查或创建静态文件副本
        try:
            image_name = os.path.basename(ad.image.name)
            image_path = ad.image.path
            static_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'test-{image_name}')
            
            # 检查静态文件是否存在，不存在则创建
            if not os.path.exists(static_image_path) and os.path.exists(image_path):
                shutil.copy2(image_path, static_image_path)
                print(f"已创建静态图片副本: {static_image_path}")
            
            # 提供多种图片访问路径
            direct_media_url = f"/direct-media/ads/images/{image_name}"
            static_url = f"/static/images/test-{image_name}"
            serve_api_url = reverse('admanage:serve_ad_image', kwargs={'ad_id': ad.id})
            
            # 检查文件状态
            image_debug = {
                'url': ad.image.url,
                'name': ad.image.name,
                'path': image_path if hasattr(ad.image, 'path') else 'No path available',
                'exists': ad.image.storage.exists(ad.image.name),
                'direct_media_url': direct_media_url,
                'static_url': static_url,
                'serve_api_url': serve_api_url
            }
        except Exception as e:
            print(f"创建图片路径信息时出错: {str(e)}")
            # 保留原始调试信息
            image_debug = {
                'url': ad.image.url,
                'name': ad.image.name,
                'path': ad.image.path if hasattr(ad.image, 'path') else 'No path available',
                'exists': ad.image.storage.exists(ad.image.name)
            }
    
    # 获取广告统计数据
    impressions = ad.get_impressions()
    clicks = ad.get_clicks()
    ctr = ad.get_ctr()
    
    # 计算预算使用情况
    budget_status = {
        'daily_limit': ad.daily_limit,
        'today_spent': 0,  # 这里需要实现实际消费计算
        'daily_usage_ratio': 0,
        'is_daily_warning': False,
        'total_budget': ad.budget,
        'total_spent': 0,  # 需要实现
        'total_usage_ratio': 0,
        'is_total_warning': False
    }
    
    # 临时计算，实际应该从消费记录中计算
    if budget_status['daily_limit'] > 0:
        budget_status['daily_usage_ratio'] = (budget_status['today_spent'] / budget_status['daily_limit']) * 100
    if budget_status['total_budget'] > 0:
        budget_status['total_usage_ratio'] = (budget_status['total_spent'] / budget_status['total_budget']) * 100
    
    budget_status['is_daily_warning'] = budget_status['daily_usage_ratio'] > 80
    budget_status['is_total_warning'] = budget_status['total_usage_ratio'] > 80
    
    # 统计数据
    stats = {
        'impressions': impressions,
        'clicks': clicks,
        'ctr': ctr,
        'cpc': 0  # 点击成本，需要计算
    }
    
    # 检查是否有预算预警通知
    notifications = Notification.objects.filter(
        user=request.user,
        status='unread',
        title__contains='预算预警'
    )[:5]
    
    context = {
        'campaign': campaign,
        'ad': ad,
        'stats': stats,
        'budget_status': budget_status,
        'notifications': notifications,
        'image_debug': image_debug,  # 添加图片调试信息
    }
    
    return render(request, 'AdManage/ad_detail.html', context)

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
                daily_limit = request.POST.get('daily_limit')
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
                ad.daily_limit = daily_limit
                ad.target_url = target_url
                ad.description = description
                ad.status = status
                
                # 处理时间
                try:
                    ad.start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d %H:%M'))
                    ad.end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d %H:%M'))
                except ValueError as e:
                    raise ValueError('日期格式错误，请使用正确的日期格式')
                
                # 处理新的广告素材（如果有）
                creative = request.FILES.get('creative')
                if creative:
                    # 验证文件类型
                    if not creative.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        raise ValueError('只支持JPG、PNG和GIF格式的图片')
                    
                    # 验证文件大小
                    if creative.size > 2 * 1024 * 1024:  # 2MB
                        raise ValueError('图片大小不能超过2MB')
                    
                    try:
                        # 如果有旧图片，先获取路径准备删除
                        old_image_path = None
                        old_static_path = None
                        if ad.image:
                            old_image_path = ad.image.path
                            old_image_name = os.path.basename(ad.image.name)
                            old_static_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'test-{old_image_name}')
                        
                        # 保存新的素材文件
                        ad.image = creative
                        ad.save()
                        
                        # 获取新图片路径
                        image_path = ad.image.path
                        image_name = os.path.basename(ad.image.name)
                        
                        # 确保文件权限正确
                        os.chmod(image_path, 0o644)
                        
                        # 保存到static目录
                        static_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'test-{image_name}')
                        shutil.copy2(image_path, static_image_path)
                        
                        # 删除旧文件
                        if old_image_path and os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                                print(f"已删除旧图片: {old_image_path}")
                            except Exception as e:
                                print(f"删除旧图片出错: {str(e)}")
                        
                        # 删除旧的静态文件
                        if old_static_path and os.path.exists(old_static_path):
                            try:
                                os.remove(old_static_path)
                                print(f"已删除旧的静态图片: {old_static_path}")
                            except Exception as e:
                                print(f"删除旧的静态图片出错: {str(e)}")
                        
                        # 强制刷新缓存
                        ad.updated_at = timezone.now()
                        ad.save(update_fields=['updated_at'])
                        
                        print(f"新图片已保存到: {image_path}")
                        print(f"新图片副本已保存到: {static_image_path}")
                    except Exception as e:
                        print(f"图片处理时出错: {str(e)}")
                        raise ValueError(f"图片处理失败: {str(e)}")
                
                ad.save()
                messages.success(request, '广告更新成功！')
                return redirect('admanage:ad_detail', campaign_id=campaign.id, ad_id=ad.id)
                
            except Exception as e:
                messages.error(request, f'更新失败：{str(e)}')
        
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

@login_required
def test_media_access(request):
    """测试媒体文件访问"""
    # 获取测试文件路径
    # 测试参数
    file_path = request.GET.get('path', '')
    action = request.GET.get('action', 'check')  # 默认动作为检查
    
    if not file_path:
        return JsonResponse({
            'success': False,
            'message': '请提供要测试的文件路径',
            'debug': {
                'MEDIA_ROOT': str(settings.MEDIA_ROOT),
                'MEDIA_URL': settings.MEDIA_URL,
                'DEBUG': settings.DEBUG
            }
        })
    
    # 处理路径
    if file_path.startswith('/'):
        file_path = file_path[1:]
    
    # 检查文件是否存在
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    file_exists = os.path.exists(full_path)
    file_size = os.path.getsize(full_path) if file_exists else 0
    
    # 获取文件URL
    file_url = request.build_absolute_uri(settings.MEDIA_URL + file_path)
    
    # 执行修复操作
    repair_info = {}
    if action == 'repair' and file_exists:
        try:
            # 1. 创建备份
            backup_path = full_path + '.bak'
            shutil.copy2(full_path, backup_path)
            repair_info['backup_created'] = True
            
            # 2. 尝试修复文件权限
            try:
                os.chmod(full_path, 0o644)  # 设置文件权限为所有用户可读
                repair_info['permissions_fixed'] = True
            except Exception as e:
                repair_info['permissions_error'] = str(e)
            
            # 3. 如果存在同名的静态文件副本，尝试从静态文件恢复
            static_test_path = os.path.join(settings.STATIC_ROOT or os.path.join(settings.BASE_DIR, 'static'), 
                                          'images', 'test-' + os.path.basename(file_path))
            
            if os.path.exists(static_test_path):
                shutil.copy2(static_test_path, full_path)
                repair_info['restored_from_static'] = True
            
            # 4. 验证修复后的文件
            repaired_exists = os.path.exists(full_path)
            repaired_size = os.path.getsize(full_path) if repaired_exists else 0
            
            repair_info['repaired_exists'] = repaired_exists
            repair_info['repaired_size'] = repaired_size
            repair_info['success'] = repaired_exists and repaired_size > 0
            
        except Exception as e:
            repair_info['error'] = str(e)
    
    # 返回结果
    result = {
        'success': True,
        'file_path': file_path,
        'full_path': full_path,
        'file_exists': file_exists,
        'file_size': file_size,
        'file_url': file_url,
        'debug': {
            'MEDIA_ROOT': str(settings.MEDIA_ROOT),
            'MEDIA_URL': settings.MEDIA_URL,
            'DEBUG': settings.DEBUG
        }
    }
    
    if action == 'repair':
        result['repair_info'] = repair_info
    
    return JsonResponse(result)

@login_required
def serve_ad_image(request, ad_id):
    """直接提供广告图片，优先从静态文件目录获取"""
    try:
        from django.http import FileResponse, Http404
        import os
        
        # 获取广告对象
        ad = get_object_or_404(Ad, id=ad_id)
        
        # 检查图片是否存在
        if not ad.image:
            raise Http404("广告没有图片")
        
        # 获取图片名称
        image_name = os.path.basename(ad.image.name)
        
        # 首先尝试从静态目录获取图片
        static_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'test-{image_name}')
        if os.path.exists(static_image_path):
            # 从静态目录打开文件
            image_file = open(static_image_path, 'rb')
            return FileResponse(image_file)
        
        # 如果静态目录没有，再尝试从媒体目录获取
        media_image_path = os.path.join(settings.MEDIA_ROOT, ad.image.name)
        if os.path.exists(media_image_path):
            # 从媒体目录打开文件
            image_file = open(media_image_path, 'rb')
            return FileResponse(image_file)
        
        # 如果都没有找到，返回占位图片
        placeholder_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'image-placeholder.png')
        if os.path.exists(placeholder_path):
            image_file = open(placeholder_path, 'rb')
            return FileResponse(image_file)
        
        # 如果连占位图片都没有，抛出404错误
        raise Http404("图片文件不存在")
        
    except Exception as e:
        from django.http import HttpResponse
        return HttpResponse(f"提供图片时出错: {str(e)}", status=500)

@login_required
def fix_all_images(request):
    """确保所有广告图片在静态目录中有副本"""
    from django.http import JsonResponse
    import os
    import shutil
    
    results = []
    fixed_count = 0
    error_count = 0
    
    try:
        # 获取所有有图片的广告
        ads = Ad.objects.exclude(image='')
        
        for ad in ads:
            try:
                # 获取图片信息
                image_path = os.path.join(settings.MEDIA_ROOT, ad.image.name)
                image_name = os.path.basename(ad.image.name)
                static_image_path = os.path.join(settings.BASE_DIR, 'static', 'images', f'test-{image_name}')
                
                result = {
                    'ad_id': ad.id,
                    'ad_name': ad.name,
                    'image_name': image_name,
                    'fixed': False
                }
                
                # 检查媒体文件是否存在
                media_exists = os.path.exists(image_path)
                static_exists = os.path.exists(static_image_path)
                
                # 如果媒体文件存在，确保静态文件也存在
                if media_exists:
                    if not static_exists:
                        # 创建静态文件副本
                        os.makedirs(os.path.dirname(static_image_path), exist_ok=True)
                        shutil.copy2(image_path, static_image_path)
                        result['action'] = '已从媒体文件创建静态副本'
                    else:
                        result['action'] = '静态副本已存在'
                    
                    # 确保文件权限正确
                    os.chmod(image_path, 0o644)
                    os.chmod(static_image_path, 0o644)
                    
                    result['fixed'] = True
                    fixed_count += 1
                # 如果媒体文件不存在但静态文件存在，从静态文件恢复
                elif static_exists:
                    # 确保目标目录存在
                    os.makedirs(os.path.dirname(image_path), exist_ok=True)
                    
                    # 从静态文件恢复
                    shutil.copy2(static_image_path, image_path)
                    os.chmod(image_path, 0o644)
                    
                    result['action'] = '已从静态副本恢复媒体文件'
                    result['fixed'] = True
                    fixed_count += 1
                else:
                    # 两个文件都不存在
                    result['action'] = '图片文件不存在，无法修复'
                    result['fixed'] = False
                    error_count += 1
                
                results.append(result)
            except Exception as e:
                results.append({
                    'ad_id': ad.id,
                    'ad_name': ad.name,
                    'error': str(e),
                    'fixed': False
                })
                error_count += 1
        
        # 返回结果
        return JsonResponse({
            'success': True,
            'total': len(ads),
            'fixed': fixed_count,
            'errors': error_count,
            'results': results
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def test_image_upload(request):
    """测试图片上传"""
    from django.http import JsonResponse
    import os
    import time
    
    context = {
        'uploaded': False,
        'test_results': {}
    }
    
    if request.method == 'POST' and request.FILES.get('test_image'):
        test_file = request.FILES['test_image']
        
        # 添加时间戳防止文件名冲突
        timestamp = int(time.time())
        test_filename = f"test-upload-{timestamp}-{test_file.name}"
        
        # 创建测试结果
        test_results = {
            'original_name': test_file.name,
            'test_filename': test_filename,
            'size': test_file.size,
            'content_type': test_file.content_type,
        }
        
        # 测试方法1: 使用默认存储保存
        try:
            # 保存到media/test/目录
            save_path = f'test/{test_filename}'
            saved_path = default_storage.save(save_path, test_file)
            test_results['method1'] = {
                'success': True,
                'saved_path': saved_path,
                'full_path': os.path.join(settings.MEDIA_ROOT, saved_path),
                'url': os.path.join(settings.MEDIA_URL, saved_path)
            }
        except Exception as e:
            test_results['method1'] = {
                'success': False,
                'error': str(e)
            }
        
        # 测试方法2: 使用ImageField保存
        try:
            # 创建一个临时广告对象
            test_ad = Ad.objects.create(
                name=f"测试广告-{timestamp}",
                advertiser=request.user,
                placement=AdPlacement.objects.first(),
                budget=100,
                daily_limit=10,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=1),
                target_url="http://example.com",
                status='pending'
            )
            
            # 保存图片
            test_file.seek(0)  # 重置文件指针
            test_ad.image.save(test_filename, test_file)
            test_ad.save()
            
            test_results['method2'] = {
                'success': True,
                'ad_id': test_ad.id,
                'image_name': test_ad.image.name,
                'full_path': test_ad.image.path,
                'url': test_ad.image.url,
                'exists': os.path.exists(test_ad.image.path)
            }
        except Exception as e:
            test_results['method2'] = {
                'success': False,
                'error': str(e)
            }
        
        # 测试方法3: 直接手动保存文件
        try:
            # 创建测试目录
            test_dir = os.path.join(settings.MEDIA_ROOT, 'test_manual')
            os.makedirs(test_dir, exist_ok=True)
            
            # 设置文件路径
            manual_path = os.path.join(test_dir, test_filename)
            
            # 手动写入文件
            test_file.seek(0)  # 重置文件指针
            with open(manual_path, 'wb+') as destination:
                for chunk in test_file.chunks():
                    destination.write(chunk)
            
            test_results['method3'] = {
                'success': True,
                'full_path': manual_path,
                'url': os.path.join(settings.MEDIA_URL, 'test_manual', test_filename),
                'exists': os.path.exists(manual_path)
            }
        except Exception as e:
            test_results['method3'] = {
                'success': False,
                'error': str(e)
            }
        
        context['uploaded'] = True
        context['test_results'] = test_results
    
    return render(request, 'AdManage/test_image_upload.html', context)