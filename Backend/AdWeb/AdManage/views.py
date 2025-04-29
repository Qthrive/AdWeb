from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def platform_home(request):
    print("访问 platform_home")
    print("当前用户:", request.user)
    print("用户是否已认证:", request.user.is_authenticated)
    print("Session 内容:", request.session.items())
    return render(request, 'admanage/platform_home.html')