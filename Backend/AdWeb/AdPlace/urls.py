from django.urls import path, include
from . import views


urlpatterns = [
    path('create/', views.create_ad, name='create_ad'),
    path('list/', views.ad_list, name='ad_list')
]