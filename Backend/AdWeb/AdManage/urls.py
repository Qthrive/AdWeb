from django.urls import path
from . import views

app_name = 'admanage'

urlpatterns = [
    path('', views.platform_home, name='platform_home'),
]