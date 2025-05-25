from django.contrib import admin
from .models import User, Notification, ValidationCode

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'audit_status', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'audit_status', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('个人信息', {'fields': ('phone', 'company', 'job_title', 'bio')}),
        ('用户状态', {'fields': ('user_type', 'audit_status', 'is_verified', 'balance')}),
        ('权限信息', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('重要日期', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'title', 'content')

@admin.register(ValidationCode)
class ValidationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'expire_at')
    search_fields = ('user__username', 'user__email')
