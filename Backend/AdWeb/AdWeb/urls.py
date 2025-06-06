"""
URL configuration for AdWeb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('Users.urls', namespace='users')),
    path('adplace/', include('AdPlace.urls', namespace='adplace')),
    path('payment/', include('Payment.urls', namespace='payment')),
    path('adaudit/', include('AdAudit.urls', namespace='adaudit')),
    path('', include('AdManage.urls', namespace='admanage')), # 根路径指向 AdManage
    # path('admanage/', include('AdManage.urls', namespace='admanage')), # 移除这一行
    # path('', user_views.home, name='home'), # 移除原来的根路径指向
]

# 在开发模式下才添加这个配置
if settings.DEBUG:
    # 添加媒体文件的URL配置 - 修改为直接添加，不考虑DEBUG状态
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # 添加静态文件的URL配置
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 为确保媒体文件服务正常，添加一个辅助路径，直接指向媒体文件
# 这行代码无论是否在DEBUG模式下都会生效
urlpatterns += [
    path('direct-media/<path:path>', lambda request, path: serve(request, path, document_root=settings.MEDIA_ROOT), name='direct_media'),
]
