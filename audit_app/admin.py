from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'user',
        'screen_name',
        'action_type',
    )
    list_filter = ('action_type', 'screen_name')
    search_fields = ('user__username', 'remark')
    ordering = ('-created_at',)
