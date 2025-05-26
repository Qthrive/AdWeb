from django.urls import path
from . import views

app_name = 'payment'

urlpatterns = [
    path('balance/', views.balance, name='balance'),
    path('recharge/', views.recharge, name='recharge'),
    path('invoice/', views.invoice_request, name='invoice'),
    path('invoice/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoice/<int:invoice_id>/download/', views.invoice_download, name='invoice_download'),
    path('invoice/<int:invoice_id>/cancel/', views.invoice_cancel, name='invoice_cancel'),
    path('invoice/info/', views.invoice_info_manage, name='invoice_info_manage'),
    path('invoice/info/<int:info_id>/edit/', views.invoice_info_edit, name='invoice_info_edit'),
    path('invoice/info/<int:info_id>/delete/', views.invoice_info_delete, name='invoice_info_delete'),
    path('admin/invoice/', views.invoice_admin_list, name='invoice_admin_list'),
    path('admin/invoice/<int:invoice_id>/', views.invoice_admin_review, name='invoice_admin_review'),
    path('admin/invoice/<int:invoice_id>/regenerate/', views.regenerate_invoice_pdf, name='regenerate_invoice_pdf'),
] 