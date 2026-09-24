from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'user_username',
        'user_role',
        'module',
        'action_type',
        'entity_type',
        'entity_reference',
        'ip_address',
        'device_type',
        'browser',
    )
    list_filter = ('module', 'action_type', 'device_type', 'operating_system', 'created_at')
    search_fields = (
        'user_username',
        'user__username',
        'entity_reference',
        'entity_id',
        'description',
        'remark',
        'ip_address',
    )
    ordering = ('-created_at',)
    readonly_fields = [f.name for f in ActivityLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

