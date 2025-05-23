from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import RegistrationForm, LoginForm, ProfileForm, CustomPasswordChangeForm
from .utils import send_verification_email
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.timezone import now
from .models import ValidationCode, Notification
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.http import HttpResponse
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from .forms import CustomPasswordResetForm
from django.core.paginator import Paginator

User = get_user_model()

# Create your views here.
def user_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                existing_user = User.objects.get(email=email)
                if existing_user.audit_status == 'pending':
                    form.add_error('email', "该邮箱已注册，正在等待管理员审核")
                else:
                    form.add_error('email', "该邮箱已被注册")
            except User.DoesNotExist:
                # 如果用户不存在，创建新用户
                user = form.save(commit=False)
                user.is_active = False  # 设置为未激活，等待审核
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
                    return render(request, 'login.html', {'form': form})
                
                # 检查用户审核状态
                if user.audit_status == 'pending':
                    form.add_error(None, "您的账号正在等待管理员审核")
                    return render(request, 'login.html', {'form': form})
                elif user.audit_status == 'rejected':
                    form.add_error(None, "您的注册申请已被拒绝，原因：" + (user.reject_reason or '未提供原因'))
                    return render(request, 'login.html', {'form': form})
                
                # 登录成功
                auth_login(request, user)
                messages.success(request, f"欢迎回来，{user.username}！")
                next_url = request.POST.get('next', '/')
                return redirect(next_url)
            else:
                form.add_error(None, "无效的邮箱或密码")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'next': request.GET.get('next', '/')})

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
    if request.method == 'POST':
        print("POST 请求数据:", request.POST)  # 添加这行
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            print("表单验证通过:", form.cleaned_data)  # 添加这行
            form.save()
            messages.success(request, "个人资料已成功更新！")
            return redirect('users:profile')
        else:
            print("表单验证失败:", form.errors)  # 添加这行
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})

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
            auth_login(request, user)
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

def registration_sent(request):
    return render(request, 'registration_sent.html')  # 页面提示用户检查邮箱进行验证

def activation_success(request):
    return render(request, 'activation_success.html')  # 激活成功页面

def activation_failed(request):
    return render(request, 'activation_failed.html')  # 激活失败页面

class CustomPasswordResetView(DjangoPasswordResetView):
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        print("PasswordResetForm 验证通过")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("PasswordResetForm 验证失败:", form.errors)
        return super().form_invalid(form)

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
    status = request.GET.get('status', 'pending')  # 默认显示待审核
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
    
    context = {
        'users': users,
        'status': status,
        'email': email,
        'date_range': date_range,
    }
    return render(request, 'Users/register_list.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def register_review(request, user_id):
    """用户注册审核详情"""
    from .utils import send_audit_result_email
    user = get_object_or_404(User, id=user_id)
    
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
                user.is_active = True  # 允许用户登录
                user.is_verified = True  # 标记为已验证
                notification_title = '注册申请已通过'
                notification_content = f'您的注册申请已通过审核。欢迎使用AdWeb广告管理平台！'
            else:
                user.audit_status = 'rejected'
                user.reject_reason = reason
                notification_title = '注册申请被拒绝'
                notification_content = f'您的注册申请未通过审核。原因：{reason}'
            
            user.audit_time = timezone.now()
            user.save()
            
            # 创建通知
            Notification.objects.create(
                user=user,
                title=notification_title,
                content=notification_content,
                status='unread'
            )
            
            # 发送邮件通知
            try:
                send_audit_result_email(user, action, reason)
            except Exception as e:
                messages.warning(request, f'邮件发送失败：{str(e)}，但审核状态已更新')
            
            messages.success(request, '审核完成')
            return redirect('users:register_list')
            
        except Exception as e:
            messages.error(request, f'审核失败：{str(e)}')
    
    context = {
        'user': user,
    }
    return render(request, 'Users/register_detail.html', context)
