from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('balance/', views.balance, name='balance'),
    path('recharge/', views.recharge, name='recharge'),
    path('invoice/', views.invoice_request, name='invoice'),
    path('admin/invoice/', views.invoice_admin_list, name='invoice_admin_list'),
    path('admin/invoice/<int:invoice_id>/', views.invoice_admin_review, name='invoice_admin_review'),
] 