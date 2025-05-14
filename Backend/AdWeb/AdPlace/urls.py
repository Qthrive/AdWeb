from django.urls import path
from . import views

app_name = 'adplace'

urlpatterns = [
    path('placements/', views.placement_list, name='placement_list'),
    path('placements/create/', views.placement_create, name='placement_create'),
    path('placements/<int:placement_id>/edit/', views.placement_edit, name='placement_edit'),
    path('placements/<int:placement_id>/delete/', views.placement_delete, name='placement_delete'),
    path('ads/create/', views.create_ad, name='create_ad'),
    # API接口
    path('api/ads/<int:ad_id>/impression/', views.record_impression, name='record_impression'),
    path('api/ads/<int:ad_id>/click/', views.record_click, name='record_click'),
]