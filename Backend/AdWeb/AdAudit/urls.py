from django.urls import path
from . import views

app_name = 'adaudit'

urlpatterns = [
    path('', views.ad_list, name='ad_list'),
    path('ad/<int:ad_id>/review/', views.ad_review, name='ad_review'),
] 