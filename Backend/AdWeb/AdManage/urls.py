from django.urls import path
from . import views

app_name = 'admanage'

urlpatterns = [
    path('', views.platform_home, name='platform_home'),
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/create/', views.campaign_create, name='campaign_create'),
    path('campaigns/<int:campaign_id>/', views.campaign_detail, name='campaign_detail'),
    path('campaigns/<int:campaign_id>/edit/', views.campaign_edit, name='campaign_edit'),
    path('campaigns/<int:campaign_id>/delete/', views.campaign_delete, name='campaign_delete'),
    path('campaign/<int:campaign_id>/ad/create/', views.ad_create, name='ad_create'),
    path('campaign/<int:campaign_id>/ad/<int:ad_id>/', views.ad_detail, name='ad_detail'),
    path('campaign/<int:campaign_id>/ad/<int:ad_id>/edit/', views.ad_edit, name='ad_edit'),
    path('campaign/<int:campaign_id>/ad/<int:ad_id>/delete/', views.ad_delete, name='ad_delete'),
    path('campaign/<int:campaign_id>/ad/<int:ad_id>/stats/', views.ad_stats, name='ad_stats'),
]