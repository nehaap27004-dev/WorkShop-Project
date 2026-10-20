
from django.contrib import admin
from .models import InvoiceTemplate


@admin.register(InvoiceTemplate)
class InvoiceTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "template_path",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    list_editable = ("is_active",)
