from django.urls import path, include
from . import views

app_name = 'adplace'  # 命名空间

urlpatterns = [
    path('create/', views.create_ad, name='create_ad'),
    path('list/', views.ad_list, name='ad_list')
]