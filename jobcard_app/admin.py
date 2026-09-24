from django.contrib import admin
from .models import JobCard, WorkshopVehicle, Estimate, Quotation, Invoice

@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    list_display = ('id', 'voucher_number', 'voucherType', 'customer', 'date', 'status', 'priority', 'grand_total')
    list_filter = ('status', 'priority', 'voucherType', 'date')
    search_fields = ('voucher_number', 'job_number', 'customer__ledger_name')
    raw_id_fields = ('customer', 'workshop_vehicle', 'advisor', 'voucherType')
    ordering = ('-created_on',)

@admin.register(WorkshopVehicle)
class WorkshopVehicleAdmin(admin.ModelAdmin):
    list_display = ('id', 'registration_number', 'vehicle_number', 'customer', 'insurance_policy_number', 'insurance_expiry_date')
    search_fields = ('registration_number', 'vehicle_number', 'customer__ledger_name')
