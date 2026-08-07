from django.contrib import admin
from fleet_app.models import *

class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('manufacturer_name', 'vehicle_type', 'manufacturer_logo_preview')
    search_fields = ('manufacturer_name',)
    list_filter = ('vehicle_type',)

    def manufacturer_logo_preview(self, obj):
        if obj.manufacturer_logo:
            return '<img src="{}" width="100" height="50" style="object-fit:contain;" />'.format(obj.manufacturer_logo.url)
        return "No logo"
    manufacturer_logo_preview.short_description = 'Logo'
    manufacturer_logo_preview.allow_tags = True

admin.site.register(Manufacturer, ManufacturerAdmin)


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')  # Display ID and category name in the list view
    search_fields = ('category_name',)      # Enable search by category name
    ordering = ('category_name',)            # Order by category name
    list_filter = ('category_name',)         # Add filtering options in the admin panel

    # Optional: Customizing the admin form layout
    fieldsets = (
        (None, {
            'fields': ('category_name',)
        }),
    )

    def __str__(self):
        return self.category_name



@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('model_name', 'manufacturer', 'vehicle_category', 'model_year', 'fuel_type', 'model_transmission', 'model_power', 'CO2_emission')
    
    # Fields that are searchable in the admin interface
    search_fields = ('model_name', 'manufacturer__manufacturer_name', 'vehicle_category__category_name', 'model_year', 'fuel_type')
    
    # Fields that can be filtered in the list view
    list_filter = ('fuel_type', 'model_transmission', 'model_year', 'manufacturer', 'vehicle_category')
    
    # Fields that are editable directly in the list view
    list_editable = ('fuel_type', 'model_transmission', 'model_year')

    # Fieldsets to organize the form fields in the detail view
    fieldsets = (
        (None, {
            'fields': ('model_name', 'manufacturer', 'vehicle_category', 'model_year', 'model_colour')
        }),
        ('Specifications', {
            'fields': ('seat_number', 'door_number', 'model_power', 'model_horse_power', 'model_range')
        }),
        ('Fuel & Emissions', {
            'fields': ('fuel_type', 'CO2_emission', 'CO2_standard')
        }),
        ('Transmission', {
            'fields': ('model_transmission',)
        }),
    )
    
    # Ordering the entries by model name in the list view
    ordering = ['model_name']
    


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('driver_name', 'driver_company', 'driver_email', 'driver_mobile', 'driver_phone')
    
    # Fields that are searchable in the admin interface
    search_fields = ('driver_name', 'driver_email', 'driver_mobile', 'driver_company')
    
    # Fields that can be filtered in the list view
    list_filter = ('driver_company',)
    
    # Fields that are editable directly in the list view
    list_editable = ('driver_company', 'driver_mobile', 'driver_phone')
    
    # Fieldsets to organize the form fields in the detail view
    fieldsets = (
        (None, {
            'fields': ('driver_name', 'driver_company', 'driver_address', 'driver_email')
        }),
        ('Contact Details', {
            'fields': ('driver_mobile', 'driver_phone')
        }),
    )
    
    # Ordering the entries by driver name in the list view
    ordering = ['driver_name']

class LicensePlateCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')  # Display fields in the admin list view
    search_fields = ('code', 'description')  # Enable search functionality for code and description
    list_filter = ('code',)  # Add filtering by code in the admin

admin.site.register(LicensePlateCode, LicensePlateCodeAdmin)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):

    list_display = (
        'vehicle_name',
        'model',
        'customer',
        'license_plate_code',
        'license_plate_number',
        'fuel_type',
        'vehicle_registration_date',
        'RC_number',
        'last_odometer',
        'status',
        'is_owned',
        'supplier',
    )

    search_fields = (
        'vehicle_name',
        'license_plate_number',
        'RC_number',
        'chassis_number',
        'engine_number',
        'customer__ledger_name',
    )

    list_filter = (
        'status',
        'fuel_type',
        'vehicle_registration_date',
        'RC_expiry_date',
        'is_owned',
    )

    list_editable = (
        'status',
    )

    fieldsets = (

        ('Basic Information', {
            'fields': (
                'is_owned',
                'supplier',
                'customer',
                'vehicle_category',
                'vehicle_name',
                'model',
                'vehicle_image',
                'status',
            )
        }),

        ('Registration Details', {
            'fields': (
                'license_plate_code',
                'license_plate_number',
                'vehicle_registration_date',
                'vehicle_cancellation_date',
                'RC_number',
                'RC_file',
                'RC_expiry_date',
            )
        }),

        ('Vehicle Information', {
            'fields': (
                'chassis_number',
                'engine_number',
                'fuel_type',
                'last_odometer',
                'capacity',
                'model_year',
            )
        }),

        ('Insurance & Compliance', {
            'fields': (
                'insurance_policy_number',
                'insurance_expiry_date',
                'insurance_certificate',

                'registration_renewed_date',
                'registration_expiry_date',
                'registration_document',

                'fitness_test_date',
                'fitness_test_expiry_date',
                'fitness_test_certificate',
            )
        }),

        ('Service Tracking', {
            'fields': (
                'last_service_date',
                'service_due_date',
                'service_interval_km',
            )
        }),

        ('Financial Details', {
            'fields': (
                'purchase_value',
                'replacement_value',
                'vat',
                'description',
            )
        }),
    )

    ordering = ['vehicle_name']
@admin.register(RentalCompany)
class RentalCompanyAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('company_name', 'company_mobile', 'company_email', 'company_city', 'company_state', 'company_country', 'company_website')

    # Fields to use for searching
    search_fields = ('company_name', 'company_email', 'company_mobile', 'company_city', 'company_state')

    # Fields to use for filtering in the list view
    list_filter = ('company_country', 'company_state', 'company_city')

    # Fields to display in the admin form in sections
    fieldsets = (
        ('Company Details', {
            'fields': ('company_name', 'company_logo', 'company_description')
        }),
        ('Contact Information', {
            'fields': ('company_mobile', 'company_phone', 'company_email', 'company_website')
        }),
        ('Address Information', {
            'fields': ('company_address_1', 'company_address_2', 'company_city', 'company_state', 'company_country', 'company_zipcode')
        }),
    )

    # Optionally, add a display for the company logo if an image is uploaded
    readonly_fields = ['company_logo'] 
    


@admin.register(RentalCompanyVehicle)
class RentalCompanyVehicleAdmin(admin.ModelAdmin):
    list_display = ('company', 'vehicle_model', 'license_plate_code', 'license_plate_number', 'fuel_type', 'vehicle_transmission', 'last_odometer')
    search_fields = ('company__company_name', 'vehicle_model', 'license_plate_code', 'license_plate_number', 'chassis_number')
    list_filter = ('fuel_type', 'vehicle_transmission', 'model_year')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company', 'contact_person')
        }),
        ('Vehicle Details', {
            'fields': (
                'vehicle_manufacturer', 'vehicle_model', 'model_colour', 'model_year',
                'Vehicle_image', 'vehicle_category', 'license_plate_code', 'license_plate_number', 'chassis_number', 
                'last_odometer', 'fuel_type', 'vehicle_transmission'
            )
        }),
        ('Driver and Registration', {
            'fields': ('vehicle_driver', 'vehicle_driver_mobile', 'RC_number', 'RC_epx_date')
        }),
    )
    
    # Optional: To include date hierarchy for quick filtering by rental start date (if applicable)
    # date_hierarchy = 'rental_start_date'

    # Optional: If you have foreign key relations like `company`, you can enable dropdown autocomplete
    autocomplete_fields = ['company', 'vehicle_category']          

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendor_name', 'vendor_type', 'vendor_mobile', 'vendor_phone', 'vendor_email', 'vendor_city', 'vendor_state', 'vendor_country')
    search_fields = ('vendor_name', 'vendor_city', 'vendor_state', 'vendor_country', 'vendor_email')
    list_filter = ('vendor_city', 'vendor_state', 'vendor_country')
    readonly_fields = ('vendor_VAT', 'vendor_TRN_or_CRN')  # Optional: if you want VAT and TRN/CRN to be read-only
    
    # Customize the form layout
    fieldsets = (
        (None, {
            'fields': ('vendor_name', 'vendor_type', 'vendor_image', 'vendor_description')
        }),
        ('Contact Information', {
            'fields': ('vendor_mobile', 'vendor_phone', 'vendor_email', 'vendor_website')
        }),
        ('Address', {
            'fields': ('vendor_address_1', 'vendor_address_2', 'vendor_city', 'vendor_state', 'vendor_country', 'vendor_zipcode')
        }),
        ('Additional Information', {
            'fields': ('vendor_VAT', 'vendor_TRN_or_CRN')
        }),
    )
    
# Inline model for TimeSheetDetail
class TimeSheetDetailInline(admin.TabularInline):
    model = TimeSheetDetail
    extra = 1  # Number of empty forms displayed for new entries
    fields = ['date', 'start_time', 'end_time', 'break_hours', 'total_hours_worked', 'ot', 'job_location', 'signature']
    readonly_fields = ['total_hours_worked']  # Example of a read-only field
    show_change_link = True  # Allows linking to detail page for editing if needed

# Admin configuration for TimeSheet
@admin.register(TimeSheet)
class TimeSheetAdmin(admin.ModelAdmin):
    list_display = ['voucher_no', 'vehicle_reg_no', 'vehicle_name', 'project_location', 'client', 'date', 'driver_name', 'enable_header', 'enable_footer', 'enable_signature']
    search_fields = ['vehicle_reg_no', 'vehicle_name', 'client', 'driver_name']
    list_filter = ['date', 'project_location', 'client']
    inlines = [TimeSheetDetailInline]
    fieldsets = (
        (None, {
            'fields': ('vehicle_reg_no', 'vehicle_name', 'project_location', 'client', 'duration')
        }),
        ('Additional Information', {
            'fields': ('PO_reference_no', 'description', 'date', 'driver_name', 'operator_name'),
            'classes': ('collapse',),  # Collapsible section
        }),
    )

# Admin configuration for TimeSheetDetail
@admin.register(TimeSheetDetail)
class TimeSheetDetailAdmin(admin.ModelAdmin):
    list_display = ['timesheet', 'date', 'start_time', 'end_time', 'break_hours', 'total_hours_worked', 'job_location']
    search_fields = ['timesheet__vehicle_reg_no', 'job_location']
    list_filter = ['date', 'job_location']
 
 
 

class FleetQuotationItemInline(admin.TabularInline):
    model = FleetQuotationItem
    extra = 1
    fields = ['vehicle', 'details', 'quantity', 'rate_per_hr', 'total_amount']

@admin.register(FleetQuotation)
class FleetQuotationAdmin(admin.ModelAdmin):
    list_display = ['quotation_no', 'date', 'company_name', 'company_address', 'customer', 'customer_address', 'text', 'terms_and_condition', 'note', 'description']
    search_fields = ['quotation_no', 'company_name', 'customer']
    
    inlines = [FleetQuotationItemInline]

@admin.register(FleetQuotationItem)
class FleetQuotationItemAdmin(admin.ModelAdmin):
    list_display = [ 'vehicle_quotation','vehicle', 'quantity', 'rate_per_hr', 'rate_per_day', 'rate_per_month', 'unit', 'no_of_unit',  'total_amount']
    search_fields = ['vehicle', 'details']
    list_filter = ['unit']
    
class RepairAndMaintenanceItemInline(admin.TabularInline):
    model = RepairAndMaintenanceItem
    extra = 1  # Specifies how many empty forms to show by default in the admin

class RepairAndMaintenanceAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'bill_no', 'date', 'payment_mode', 'party', 'vehicle_name', 'grand_total_amount')
    search_fields = ('voucher_no', 'bill_no', 'party', 'vehicle_name__name')
    list_filter = ('payment_mode', 'date')
    inlines = [RepairAndMaintenanceItemInline]

    def save_model(self, request, obj, form, change):
        # Custom logic to set or modify any field before saving
        super().save_model(request, obj, form, change)

admin.site.register(RepairAndMaintenance, RepairAndMaintenanceAdmin)

class RepairAndMaintenanceItemAdmin(admin.ModelAdmin):
    list_display = ('repair_and_maintenance', 'narration', 'bill_amount', 'VAT_amount', 'total_amount')
    search_fields = ('repair_and_maintenance__voucher_no', 'narration')

admin.site.register(RepairAndMaintenanceItem, RepairAndMaintenanceItemAdmin)    

    
'''
@admin.register(VehicleMaster)
class VehicleMasterAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'customer',
        'vehicle_name', 
        'license_plate_code', 
        'license_plate_number', 
        'vehicle_driver', 
        'vehicle_category', 
        'RC_number', 
        'contract_no', 
        'contract_start_date', 
        'contract_end_date', 
        'customer_name'
    )
    
    # Fields to filter by in the admin interface
    list_filter = ('vehicle_category', 'contract_start_date', 'contract_end_date')
    
    # Fields to search by
    search_fields = ('vehicle_name', 'license_plate_number', 'vehicle_driver', 'customer_name')
    
    # Order records by default
    ordering = ('vehicle_name',)

    # Editable fields in the list view
    list_editable = ('vehicle_driver', 'contract_no', 'contract_start_date', 'contract_end_date')
'''
@admin.register(FleetCustomer)
class FleetCustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_mobile', 'customer_email', 'customer_city', 'customer_country')
    search_fields = ('customer_name', 'customer_email')
    list_filter = ('customer_country', 'customer_city')    
    
class SimpleQuotationDetailsInline(admin.TabularInline):
    model = SimpleQuotationDetails
    extra = 1  # Number of empty rows for new details

@admin.register(SimpleQuotation)
class SimpleQuotationAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'date', 'customer', 'enable_header', 'enable_footer', 'enable_signature')
    search_fields = ('voucher_no', 'customer__name')
    list_filter = ('date',)
    inlines = [SimpleQuotationDetailsInline]

@admin.register(SimpleQuotationDetails)
class SimpleQuotationDetailsAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'description', 'quantity', 'rent')
    search_fields = ('description', 'quotation__quotation_no')    
    
class InvoiceDetailsInline(admin.TabularInline):
    model = InvoiceDetails
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('id','voucher_no', 'date', 'customer', 'grand_total', 'enable_header', 'enable_footer', 'enable_signature')
    search_fields = ('voucher_no', 'customer__name')
    list_filter = ('date',)
    inlines = [InvoiceDetailsInline]

@admin.register(InvoiceDetails)
class InvoiceDetailsAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'vehicle', 'location', 'amount', 'tax', 'tax_amount', 'total_amount')
    search_fields = ('invoice__voucher_no', 'vehicle__vehicle_name')
    list_filter = ('vehicle',)    
    
class FleetHireDetailsInline(admin.TabularInline):
    model = FleetHireDetails
    extra = 1   # number of empty rows shown
    fields = ('vehicle', 'reg_no', 'start_date', 'end_date', 'unit', 'rate_per_period')
    autocomplete_fields = ('vehicle',)  # if you have many vehicles


@admin.register(FleetHire)
class FleetHireAdmin(admin.ModelAdmin):
    list_display = ('id','voucher_no', 'supplier', 'invoice_no', 'invoice_date', 'grand_total', 'payment_mode', 'created_at')
    list_filter = ('supplier', 'invoice_date', 'created_at')
    search_fields = ('voucher_no', 'invoice_no', 'supplier__name')
    date_hierarchy = 'invoice_date'

    inlines = [FleetHireDetailsInline]

    fieldsets = (
        ("Hire Info", {
            "fields": ("voucher_no", "supplier", "invoice_no", "invoice_date", "hire_contract", "payment_mode", "IsCleared")
        }),
        ("Amounts", {
            "fields": ("subtotal", "vat", "other_charges", "grand_total")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(FleetHireDetails)
class FleetHireDetailsAdmin(admin.ModelAdmin):
    list_display = ('fleet_hire', 'vehicle', 'reg_no', 'start_date', 'end_date', 'unit', 'rate_per_period')
    list_filter = ('unit', 'start_date', 'end_date')
    search_fields = ('reg_no', 'vehicle__name', 'fleet_hire__voucher_no')    

'''@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'staff',
        'vehicle',
        'status',
        'upload_date',
        'expiry_date',
        'reminder_date',
    )

    list_filter = (
        'status',
        'staff',
        'vehicle',
        'expiry_date',
    )

    search_fields = (
        'title',
        'description',
        'staff__name',
        'vehicle__registration_no',
    )

    readonly_fields = ('upload_date',)

    ordering = ('-upload_date',)

    date_hierarchy = 'upload_date'

    fieldsets = (
        ('Document Info', {
            'fields': ('title', 'description', 'file_path')
        }),
        ('Linked To', {
            'fields': ('staff', 'vehicle')
        }),
        ('Status & Dates', {
            'fields': ('status', 'upload_date', 'expiry_date', 'reminder_date')
        }),
    )
'''


@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'company',
        'uploaded_at',
        'expiry_date',
        'reminder_date',
    )

    list_filter = (
        'company',
        'expiry_date',
    )

    search_fields = (
        'name',
        'company__name',
    )

    readonly_fields = ('uploaded_at',)

    ordering = ('-uploaded_at',)

    date_hierarchy = 'uploaded_at'

    fieldsets = (
        ('Company Document Info', {
            'fields': ('company', 'name', 'file')
        }),
        ('Dates', {
            'fields': ('uploaded_at', 'expiry_date', 'reminder_date')
        }),
    )    
    
@admin.register(VehicleEMI)
class VehicleEMIAdmin(admin.ModelAdmin):
    # Shows the main details of the plan
    list_display = ('title', 'vehicle', 'amount', 'start_date', 'end_date', 'is_active')
    search_fields = ('title',)

@admin.register(EMIInstallment)
class EMIInstallmentAdmin(admin.ModelAdmin):
    # Shows individual monthly payments
    list_display = ('emi_plan', 'due_date', 'amount', 'is_paid')
    # minimal filters to check what is unpaid
    list_filter = ('is_paid', 'due_date')    