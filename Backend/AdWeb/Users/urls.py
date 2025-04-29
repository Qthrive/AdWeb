from django.urls import path, reverse_lazy
from . import views
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from . import forms

app_name = 'users'  # 命名空间

urlpatterns = [
    path('register/', views.user_register, name='register'),  # 注册
    path('login/', views.user_login, name='login'),           # 登录
    path('profile/', views.profile, name='profile'),     # 用户个人信息
    path('change_password/', views.change_password, name='change_password'),
    path('registration_sent',views.registration_sent, name='registration_sent'),  # 注册成功后提示用户检查邮箱
    path('activation_success',views.activation_success, name='activation_success'),  # 激活成功
    path('activation_failed',views.activation_failed, name='activation_failed'),  # 激活失败
    path('verify_email/', views.verify_email, name='verify_email'),  # 邮箱验证
    path('logout/', views.user_logout, name='logout'),  # 登出
    path('', views.home, name='home'),  # 定义 home 路由
    path('test_email/', views.test_email, name='test_email'),


    # 内置密码重置视图
    path('password_reset/', views.CustomPasswordResetView.as_view(
        template_name="users/password_reset_form.html",
        email_template_name="users/password_reset_email.html",
        success_url=reverse_lazy('users:password_reset_done'),
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name="users/password_reset_confirm.html",
        success_url=reverse_lazy('users:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
]