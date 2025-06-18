from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegistrationForm, LoginForm, ProfileForm, CustomPasswordChangeForm
from .utils import send_verification_email
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.timezone import now
from .models import ValidationCode, Notification, AuditLog, PasswordResetRequest
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView, 
    PasswordResetCompleteView
)
from .forms import CustomPasswordResetForm
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse_lazy

User = get_user_model()

# Create your views here.
def user_register(request):
    if request.method == 'POST':
        # 先检查是否是被拒绝的用户尝试重新注册
        email = request.POST.get('email')
        username = request.POST.get('username')
        
        if email:
            try:
                existing_user = User.objects.get(email=email)
                if existing_user.audit_status == 'rejected':
                    # 如果是被拒绝的用户，先删除旧账号
                    print(f"发现被拒绝的用户，正在删除旧账号: {email}")
                    existing_user.delete()
                    print(f"已删除被拒绝的用户账号: {email}")
            except User.DoesNotExist:
                pass  # 用户不存在，继续处理
        
        # 然后处理表单验证
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # 创建新用户
            user = form.save(commit=False)
            user.is_active = True  # 设置为激活状态，但需要等待审核
            user.audit_status = 'pending'  # 设置为待审核状态
            user.register_ip = request.META.get('REMOTE_ADDR')
            user.device_info = request.META.get('HTTP_USER_AGENT', '')
            user.user_type = 'advertiser'  # 设置为广告主
            user.save()

            # 给管理员发送通知
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title='新用户注册待审核',
                    content=f'新用户 {user.username}（{user.email}）已注册，等待审核。'
                )
            
            # 发送邮件通知用户
            try:
                send_mail(
                    '【AdWeb广告管理平台】注册申请已提交',
                    f'尊敬的{user.username}：\n\n您的注册申请已提交成功，正在等待管理员审核。\n审核结果将通过邮件通知，请耐心等待。\n\n如有疑问，请联系管理员。\n\nAdWeb广告管理平台',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"发送邮件失败: {str(e)}")

            messages.success(request, '注册成功！请等待管理员审核，审核结果将通过邮件通知。')
            return redirect('users:registration_sent')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and user.check_token(token):
        user.is_verified = True
        user.save()
        return redirect('activation_success')  # Redirect to a success page
    else:
        return redirect('activation_failed')  # Redirect to a failure page

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user_type = form.cleaned_data['user_type']
            user = authenticate(request, email=email, password=password)
            
            if user:
                # 检查用户类型是否匹配
                if user_type == 'admin' and not user.is_staff:
                    form.add_error(None, "您不是管理员用户")
                    return render(request, 'login.html', {'form': form})
                elif user_type == 'advertiser' and user.is_staff:
                    form.add_error(None, "请使用管理员登录入口")
                    return render(request, 'login.html', {'form': form, 'user_type': 'admin'})
                
                # 只对广告主检查审核状态
                if user_type == 'advertiser':
                    if not hasattr(user, 'audit_status'):
                        form.add_error(None, "账户状态异常，请联系管理员")
                        return render(request, 'login.html', {'form': form})
                    if user.audit_status == 'pending':
                        form.add_error(None, "您的账号正在等待管理员审核")
                        return render(request, 'login.html', {'form': form})
                    elif user.audit_status == 'rejected':
                        form.add_error(None, "您的注册申请已被拒绝，原因：" + (user.reject_reason or '未提供原因'))
                        return render(request, 'login.html', {'form': form})
                
                # 登录成功
                auth_login(request, user)
                messages.success(request, f"欢迎回来，{user.username}！")
                next_url = request.POST.get('next', None)
                
                # 如果有指定的下一个页面，则重定向到该页面
                if next_url and next_url != '/':
                    return redirect(next_url)
                
                # 否则根据用户类型重定向到不同的默认页面
                if user.is_staff:
                    return redirect('admanage:platform_home')  # 管理员重定向到平台首页
                else:
                    return redirect('admanage:platform_home')  # 广告主也重定向到平台首页
            else:
                form.add_error(None, "无效的邮箱或密码")
                # 保持用户选择的登录类型
                return render(request, 'login.html', {'form': form, 'user_type': user_type})
    else:
        form = LoginForm()
        # 获取URL参数中的用户类型
        user_type = request.GET.get('user_type', 'advertiser')
    return render(request, 'login.html', {'form': form, 'next': request.GET.get('next', '/'), 'user_type': user_type})

@login_required
def home(request):
    print("当前用户：", request.user)
    print("用户是否已登录：", request.user.is_authenticated)
    print("用户邮箱：", request.user.email if request.user.is_authenticated else "未登录")
    return render(request, 'home.html')

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "您已成功登出。")
    return redirect('users:login')  # Redirect to login page after logout

def verify_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        code = request.POST.get('code')
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return render(request, 'verify_email.html', {'error': "该邮箱已被验证"})
            
            # 验证验证码
            try:
                validation_code = ValidationCode.objects.get(user=user, code=code)
                if validation_code.expire_at > now():
                    # 验证成功
                    user.is_verified = True
                    user.save()
                    validation_code.delete()  # 删除已使用的验证码
                    return redirect('users:activation_success')  # 跳转到激活成功页面
                else:
                    return render(request, 'verify_email.html', {'error': "验证码已过期，请重新获取"})
            except ValidationCode.DoesNotExist:
                return render(request, 'verify_email.html', {'error': "验证码无效，请检查后重试"})
        except User.DoesNotExist:
            return render(request, 'verify_email.html', {'error': "该邮箱未注册"})
    return render(request, 'verify_email.html')

@login_required
def profile(request):
    user = request.user
    # 导入所有需要的模型
    from AdManage.models import Campaign
    from AdPlace.models import Ad
    from Users.models import User
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "个人资料已成功更新！")
            return redirect('users:profile')
    else:
        # 初始化表单时设置邮箱字段的值
        form = ProfileForm(instance=user, initial={'email': user.email})
    
    # 获取用户类型和状态的显示名称
    # 判断用户类型：如果是staff则显示为管理员，否则使用user_type字段
    if user.is_staff:
        user_type_display = '管理员'
    else:
        user_type_display = dict(User.USER_TYPE_CHOICES).get(user.user_type, '未知')
    
    audit_status_display = dict(User.AUDIT_STATUS_CHOICES).get(user.audit_status, '未知')
    
    # 如果是管理员，显示系统统计数据
    if user.is_staff:
        # 系统用户统计
        total_users = User.objects.filter(user_type='advertiser').count()
        pending_users = User.objects.filter(user_type='advertiser', audit_status='pending').count()
        
        # 系统广告统计
        campaign_count = Campaign.objects.all().count()
        ad_count = Ad.objects.all().count()
        
        # 为模板添加额外的管理员统计数据
        context = {
            'form': form,
            'user': user,
            'user_type_display': user_type_display,
            'total_users': total_users,
            'pending_users': pending_users,
            'campaign_count': campaign_count,
            'ad_count': ad_count,
            'register_time': user.date_joined,
            'last_login': user.last_login,
            'is_admin': True,
        }
    else:
        # 普通用户显示个人广告统计
        campaign_count = Campaign.objects.filter(advertiser=user).count()
        ad_count = Ad.objects.filter(advertiser=user).count()
        
        context = {
            'form': form,
            'user': user,
            'user_type_display': user_type_display,
            'audit_status_display': audit_status_display,
            'campaign_count': campaign_count,
            'ad_count': ad_count,
            'register_time': user.date_joined,
            'last_login': user.last_login,
            'is_admin': False,
        }
    
    return render(request, 'users/profile.html', context)

def test_email(request):
    send_mail(
        '测试邮件',
        '这是一封来自 Django 的测试邮件。',
        'qthrive@126.com',  # 发件人
        ['939398252@qq.com'],  # 收件人，替换为你自己的邮箱
        fail_silently=False,
    )
    return HttpResponse("测试邮件已发送，请检查你的邮箱。")

# 密码修改视图
@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "密码已成功修改！")
            return redirect('users:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

def registration_sent(request):
    """注册成功页面，提示用户等待审核"""
    return render(request, 'registration_sent.html')  # 使用根目录下的模板

def activation_success(request):
    return render(request, 'activation_success.html')  # 激活成功页面

def activation_failed(request):
    return render(request, 'activation_failed.html')  # 激活失败页面

# 密码重置视图
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('users:password_reset_done')
    
    def form_valid(self, form):
        """如果表单有效，重定向到成功URL"""
        # 设置额外的选项
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': settings.EMAIL_HOST_USER,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': self.extra_email_context,
        }
        form.save(**opts)
        messages.info(self.request, "如果您输入的邮箱存在于我们的系统中，您将收到一封密码重置邮件。")
        # 直接重定向到成功URL，而不是调用super().form_valid(form)
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """如果表单无效，返回表单错误"""
        return super().form_invalid(form)

# 密码重置完成视图
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

# 密码重置确认视图
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

# 密码重置完成视图
class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

@login_required
def notification_list(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    paginator = Paginator(notifications, 10)
    page = request.GET.get('page')
    notifications_page = paginator.get_page(page)

    # 标记为已读（通过GET参数或POST）
    mark_read_id = request.GET.get('read')
    if mark_read_id:
        try:
            n = Notification.objects.get(id=mark_read_id, user=user)
            n.status = 'read'
            n.read_at = timezone.now()
            n.save()
        except Notification.DoesNotExist:
            pass
        return redirect('users:notification_list')

    context = {
        'notifications': notifications_page,
    }
    return render(request, 'Users/notification_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def register_list(request):
    """用户注册审核列表"""
    status = request.GET.get('status', '')  # 默认显示所有状态
    email = request.GET.get('email', '')
    date_range = request.GET.get('date_range', '')

    # 构建查询
    users = User.objects.filter(user_type='advertiser').order_by('-date_joined')
    
    if status:
        users = users.filter(audit_status=status)
    if email:
        users = users.filter(email__icontains=email)
    
    # 时间范围筛选
    today = timezone.now().date()
    if date_range == 'today':
        users = users.filter(date_joined__date=today)
    elif date_range == 'yesterday':
        yesterday = today - timezone.timedelta(days=1)
        users = users.filter(date_joined__date=yesterday)
    elif date_range == 'last7days':
        last_week = today - timezone.timedelta(days=7)
        users = users.filter(date_joined__date__gte=last_week)
    elif date_range == 'last30days':
        last_month = today - timezone.timedelta(days=30)
        users = users.filter(date_joined__date__gte=last_month)
    
    # 分页
    paginator = Paginator(users, 10)  # 每页显示10条
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    # 获取各个状态的数量
    pending_count = User.objects.filter(user_type='advertiser', audit_status='pending').count()
    approved_count = User.objects.filter(user_type='advertiser', audit_status='approved').count()
    rejected_count = User.objects.filter(user_type='advertiser', audit_status='rejected').count()
    
    context = {
        'users': users,
        'status': status,
        'email': email,
        'date_range': date_range,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'users/register_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def register_review(request, user_id):
    """用户注册审核详情"""
    user = get_object_or_404(User, id=user_id)
    
    # 获取该用户的审核历史记录
    audit_logs = AuditLog.objects.filter(
        target_user=user,
        audit_type='user_register'
    ).order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('reason')
        
        if not action or not reason:
            messages.error(request, '请选择审核结果并填写审核意见')
            return redirect('users:register_detail', user_id=user.id)
        
        try:
            # 更新用户状态
            if action == 'approve':
                user.audit_status = 'approved'
                user.is_verified = True
                notification_title = '注册申请已通过'
                notification_content = f'您的注册申请已通过审核。欢迎使用AdWeb广告管理平台！'
                email_subject = '【AdWeb广告管理平台】注册申请已通过'
                email_message = f'尊敬的{user.username}：\n\n恭喜您！您的注册申请已通过审核。\n\n您现在可以使用您的账号登录AdWeb广告管理平台，开始投放广告。\n\n如有任何问题，请随时联系我们的客服团队。\n\n祝您使用愉快！\n\nAdWeb广告管理平台团队'
            else:
                user.audit_status = 'rejected'
                user.reject_reason = reason
                notification_title = '注册申请被拒绝'
                notification_content = f'您的注册申请未通过审核。原因：{reason}'
                email_subject = '【AdWeb广告管理平台】注册申请未通过'
                email_message = f'尊敬的{user.username}：\n\n很遗憾，您的注册申请未能通过审核。\n\n拒绝原因：{reason}\n\n如有疑问，请联系我们的客服团队。\n\nAdWeb广告管理平台团队'
            
            user.audit_time = timezone.now()
            user.save()
            
            # 创建审核日志
            AuditLog.objects.create(
                audit_type='user_register',
                target_user=user,
                reviewer=request.user,
                action=action,
                remark=reason
            )
            
            # 创建通知
            Notification.objects.create(
                user=user,
                title=notification_title,
                content=notification_content,
                status='unread'
            )
            
            # 发送邮件通知用户
            try:
                send_mail(
                    email_subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception as e:
                messages.warning(request, f'邮件发送失败：{str(e)}')
            
            messages.success(request, '审核完成')
            return redirect('users:register_list')
            
        except Exception as e:
            messages.error(request, f'审核失败：{str(e)}')
    
    context = {
        'user': user,
        'audit_logs': audit_logs,
    }
    return render(request, 'users/register_detail.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def password_reset_review(request, request_id):
    """密码重置请求审核详情"""
    from .models import PasswordResetRequest, AuditLog
    
    reset_request = get_object_or_404(PasswordResetRequest, id=request_id)
    
    # 获取该用户的密码重置审核历史
    audit_logs = AuditLog.objects.filter(
        target_user=reset_request.user,
        audit_type='password_reset'
    ).order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        remark = request.POST.get('remark', '')
        
        if not action:
            messages.error(request, '请选择审核结果')
            return redirect('users:password_reset_review', request_id=reset_request.id)
        
        try:
            # 更新请求状态
            if action == 'approve':
                reset_request.status = 'approved'
                reset_request.admin_remark = remark
                reset_request.reviewer = request.user
                reset_request.approved_at = timezone.now()
                reset_request.save()
                
                # 创建审核日志
                AuditLog.objects.create(
                    audit_type='password_reset',
                    target_user=reset_request.user,
                    reviewer=request.user,
                    action='approve',
                    remark=remark
                )
                
                # 发送重置邮件
                from django.contrib.auth.tokens import default_token_generator
                from django.utils.http import urlsafe_base64_encode
                from django.utils.encoding import force_bytes
                
                user = reset_request.user
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                
                domain = request.META.get('HTTP_HOST', 'localhost:8000')
                protocol = 'https' if request.is_secure() else 'http'
                
                reset_url = f"{protocol}://{domain}/users/reset/{uid}/{token}/"
                
                email_subject = '【AdWeb广告管理平台】密码重置链接'
                email_message = f'''尊敬的{user.username}：

您的密码重置申请已通过审核。

请点击以下链接来重置您的密码：

{reset_url}

如果点击链接无效，请将链接复制到浏览器地址栏中访问。

此链接将在24小时后失效，请尽快操作。

如果您没有请求重置密码，请忽略此邮件，您的账户将保持安全。

此致，
AdWeb广告管理平台团队'''
                
                # 发送邮件
                try:
                    send_mail(
                        email_subject,
                        email_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                    
                    # 创建通知
                    Notification.objects.create(
                        user=user,
                        title='密码重置申请已通过',
                        content='您的密码重置申请已通过审核，我们已向您的邮箱发送了重置链接，请查收。'
                    )
                    
                    messages.success(request, '审核完成，重置邮件已发送')
                except Exception as e:
                    messages.error(request, f'邮件发送失败：{str(e)}')
                    
            else:  # 拒绝
                reset_request.status = 'rejected'
                reset_request.admin_remark = remark
                reset_request.reviewer = request.user
                reset_request.save()
                
                # 创建审核日志
                AuditLog.objects.create(
                    audit_type='password_reset',
                    target_user=reset_request.user,
                    reviewer=request.user,
                    action='reject',
                    remark=remark
                )
                
                # 创建通知
                Notification.objects.create(
                    user=reset_request.user,
                    title='密码重置申请被拒绝',
                    content=f'您的密码重置申请未通过审核。原因：{remark}'
                )
                
                messages.success(request, '审核完成，已拒绝该请求')
            
            return redirect('users:password_reset_list')
            
        except Exception as e:
            messages.error(request, f'审核失败：{str(e)}')
    
    context = {
        'reset_request': reset_request,
        'audit_logs': audit_logs,
    }
    return render(request, 'users/password_reset_review.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def password_reset_list(request):
    """管理员查看密码重置请求列表"""
    status = request.GET.get('status', 'all')
    
    # 根据状态筛选请求
    if status == 'pending':
        reset_requests = PasswordResetRequest.objects.filter(status='pending')
    elif status == 'approved':
        reset_requests = PasswordResetRequest.objects.filter(status='approved')
    elif status == 'rejected':
        reset_requests = PasswordResetRequest.objects.filter(status='rejected')
    elif status == 'completed':
        reset_requests = PasswordResetRequest.objects.filter(status='completed')
    else:
        reset_requests = PasswordResetRequest.objects.all()
    
    # 分页
    paginator = Paginator(reset_requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取待审核的请求数量（用于显示在导航栏上）
    pending_count = PasswordResetRequest.objects.filter(status='pending').count()
    
    context = {
        'page_obj': page_obj,
        'status': status,
        'pending_count': pending_count,
    }
    
    return render(request, 'users/password_reset_list.html', context)
