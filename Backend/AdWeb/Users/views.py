from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
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
                if not existing_user.is_verified:
                    # 如果用户未验证，重新发送验证邮件
                    existing_user.is_verified = False  # 设置为未验证
                    send_verification_email(existing_user)
                    return redirect('users:registration_sent')  # 提示用户检查邮箱
                else:
                    form.add_error('email', "该邮箱已被注册且已验证")
            except User.DoesNotExist:
                # 如果用户不存在，正常注册流程
                user = form.save(commit=False)
                user.is_verified = False  # 设置为未验证
                user.save()
                send_verification_email(user)  # 发送验证邮件
                return redirect('users:registration_sent')  # 提示用户检查邮箱
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
            user = authenticate(request, email=email, password=password)
            print("用户认证结果:", user)
            if user:
                print("用户已认证")
                auth_login(request, user)
                print("用户登录成功")
                request.session['last_login'] = timezone.now().isoformat()
                request.session.modified = True
                print("Session Key (after login):", request.session.session_key)
                print("User is authenticated after login:", request.user.is_authenticated)
                next_url = request.POST.get('next', '/')
                print("重定向到:", next_url)
                return redirect(next_url)
            else:
                print("用户认证失败")
                if User.objects.filter(email=email, is_verified=False).exists():
                    form.add_error(None, "您的账号尚未验证，请检查邮箱完成验证")
                else:
                    form.add_error(None, "无效的邮箱或密码")
        else:
            print("表单验证失败")
            print("错误信息:", form.errors)
    else:
        print("GET请求")
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
