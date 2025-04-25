from django.contrib import admin
from .models import Ad, AdPlacement

# Register your models here.
@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ('advertiser', 'placement_type', 'status', 'start_date')
    list_filter = ('status', 'placement_type')
    search_fields = ('advertiser__username', 'placement_type')
    ordering = ('-created_at',)

@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ('placement_type', 'ad_count')
    search_fields = ('placement_type',)

    def ad_count(self, obj):
        return obj.ad_set.count()
    ad_count.short_description = '广告数量'
