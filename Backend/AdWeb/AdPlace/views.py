from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .forms import AdForm
from .services import AdService
from .models import AdPlacement, Ad
from Payment.services import PaymentService
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Create your views here.

@login_required
def create_ad(request):
    if request.method == 'POST':
        try:
            # 获取表单数据
            data = {
                'placement_type': request.POST.get('placement_type'),
                'budget': request.POST.get('budget'),
                'daily_limit': request.POST.get('daily_limit'),
                'image': request.FILES.get('image'),
                'start_date': request.POST.get('start_date'),
                'end_date': request.POST.get('end_date'),
                'name': request.POST.get('name'),
                'target_url': request.POST.get('target_url'),
            }
            
            # 创建广告
            ad = AdService.create_ad(request.user, data)
            
            # 预扣费用
            PaymentService.create_ad_prepayment(ad)
            
            messages.success(request, '广告创建成功！')
            return redirect('admanage:ad_detail', campaign_id=ad.campaign.id, ad_id=ad.id)
            
        except Exception as e:
            messages.error(request, f'创建广告失败：{str(e)}')
            return redirect('admanage:create_ad')
            
    # GET请求显示创建表单
    placements = AdPlacement.get_available_placements()
    context = {
        'placements': placements,
    }
    return render(request, 'AdPlace/create_ad.html', context)

@login_required
def ad_list(request):
    ads = AdService.get_ad_list(user=request.user)
    return render(request, 'list.html', {'ads': ads})

def is_admin(user):
    """检查用户是否为管理员"""
    return user.is_staff

@login_required
def placement_list(request):
    """广告位列表"""
    # 获取筛选参数
    type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    # 构建查询
    placements = AdPlacement.objects.all().order_by('-created_at')
    
    if type:
        placements = placements.filter(type=type)
    if status:
        placements = placements.filter(status=status)
    if search:
        placements = placements.filter(name__icontains=search)
    
    # 分页
    paginator = Paginator(placements, 9)  # 每页显示9个广告位
    page = request.GET.get('page')
    placements = paginator.get_page(page)
    
    context = {
        'placements': placements,
        'type': type,
        'status': status,
        'search': search,
    }
    return render(request, 'AdPlace/placement_list.html', context)

@login_required
@user_passes_test(is_admin)
def placement_create(request):
    """创建广告位"""
    if request.method == 'POST':
        try:
            placement = AdPlacement.objects.create(
                name=request.POST.get('name'),
                type=request.POST.get('type'),
                width=request.POST.get('width'),
                height=request.POST.get('height'),
                price=request.POST.get('price'),
                description=request.POST.get('description'),
                status=request.POST.get('status'),
                created_by=request.user
            )
            messages.success(request, '广告位创建成功')
            return redirect('adplace:placement_list')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
    
    return render(request, 'AdPlace/placement_edit.html')

@login_required
@user_passes_test(is_admin)
def placement_edit(request, placement_id):
    """编辑广告位"""
    placement = get_object_or_404(AdPlacement, id=placement_id)
    
    if request.method == 'POST':
        try:
            placement.name = request.POST.get('name')
            placement.type = request.POST.get('type')
            placement.width = request.POST.get('width')
            placement.height = request.POST.get('height')
            placement.price = request.POST.get('price')
            placement.description = request.POST.get('description')
            placement.status = request.POST.get('status')
            placement.save()
            
            messages.success(request, '广告位更新成功')
            return redirect('adplace:placement_list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    context = {
        'placement': placement
    }
    return render(request, 'AdPlace/placement_edit.html', context)

@login_required
@user_passes_test(is_admin)
def placement_delete(request, placement_id):
    """删除广告位"""
    placement = get_object_or_404(AdPlacement, id=placement_id)
    
    if request.method == 'POST':
        try:
            placement.delete()
            messages.success(request, '广告位删除成功')
            return redirect('adplace:placement_list')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    context = {
        'placement': placement
    }
    return render(request, 'AdPlace/placement_delete.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def record_impression(request, ad_id):
    """记录广告展示"""
    try:
        ad = get_object_or_404(Ad, id=ad_id, status='active')
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        success = PaymentService.record_impression(ad, ip_address, user_agent)
        
        return JsonResponse({
            'success': success,
            'message': '展示记录成功' if success else '展示记录失败'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def record_click(request, ad_id):
    """记录广告点击"""
    try:
        ad = get_object_or_404(Ad, id=ad_id, status='active')
        impression_id = request.POST.get('impression_id')
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        success = PaymentService.record_click(ad, impression_id, ip_address, user_agent)
        
        return JsonResponse({
            'success': success,
            'message': '点击记录成功' if success else '点击记录失败'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)