from django.urls import path, reverse_lazy
from . import views
from django.shortcuts import render

app_name = 'users'  # 命名空间

urlpatterns = [
    path('register/', views.user_register, name='register'),  # 注册
    path('login/', views.user_login, name='login'),           # 登录
    path('profile/', views.profile, name='profile'),     # 用户个人信息
    path('change_password/', views.change_password, name='change_password'),
    path('registration_sent/',views.registration_sent, name='registration_sent'),  # 注册成功提示
    path('register/list/', views.register_list, name='register_list'),  # 注册审核列表
    path('register/<int:user_id>/detail/', views.register_review, name='register_detail'),  # 注册审核详情
    path('notifications/', views.notification_list, name='notification_list'),  # 通知列表
    path('logout/', views.user_logout, name='logout'),  # 登出
    path('', views.home, name='home'),  # 定义 home 路由
    path('test_email/', views.test_email, name='test_email'),

    # 密码重置路径
    path('password_reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    path('password_reset/done/', 
         views.CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('reset/done/', 
         views.CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
]