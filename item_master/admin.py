from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name')
    search_fields = ('category_name',)
    ordering = ('category_name',)
    list_filter = ('category_name',)
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.isDefault:
            return False  # hide delete button for default object
        return super().has_delete_permission(request, obj)
    
@admin.register(ItemManufacturer)
class ItemManufacturerAdmin(admin.ModelAdmin):
    list_display = ['manufacturer_name']
    search_fields = ['manufacturer_name']
    ordering = ['manufacturer_name']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'item_code', 'item_unit', 'barcode_code', 'item_category', 'item_manufacturer', 'cost_center',  'purchase_rate', 'sales_rate', 'MRP', 'min_stock', 'item_class', 'IsItemBarcode']
    search_fields = ['item_name', 'item_code', 'regional_name']
    list_filter = ['item_category', 'item_manufacturer', 'item_class']
    ordering = ['item_name']
    readonly_fields = ['item_code']  # Assuming item_code is auto-generated or unique
    fieldsets = (
        (None, {
            'fields': ('item_name', 'item_code', 'regional_name', 'item_category', 'item_manufacturer', 'min_stock', 'rack', 'IsItemBarcode', 'IsBatch')
        }),
        ('Tax & Pricing', {
            'fields': ('TAX', 'purchase_rate', 'sales_rate', 'MRP')  # Added pricing fields here
        }),
        ('Units', {
            'fields': ('item_unit',)
        }),
        ('Additional Info', {
            'fields': ('remarks', 'item_class', 'item_image')
        }),
    )

@admin.register(ItemAlterUnit)
class ItemAlterUnitAdmin(admin.ModelAdmin):
    list_display = (
        'item', 'unit', 'is_base_unit', 'uc_factor', 
        'barcode_code', 'purchase_rate', 'sales_rate'
    )
    list_filter = ('is_base_unit', 'unit')
    search_fields = ('item__item_name', 'barcode_code')
    list_editable = ('is_base_unit', 'purchase_rate', 'sales_rate')


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['vendor_name', 'vendor_mobile', 'vendor_email', 'vendor_city', 'vendor_state', 'vendor_country']
    search_fields = ['vendor_name', 'vendor_mobile', 'vendor_email', 'vendor_city']
    list_filter = ['vendor_country', 'vendor_state', 'vendor_city']
    ordering = ['vendor_name']    
 
@admin.register(Unit)   
class UnitAdmin(admin.ModelAdmin):
    list_display = ('unit_code', 'unit_name')  # Columns to display in the list view
    search_fields = ('unit_code', 'unit_name')  # Fields that can be searched
    ordering = ('unit_code',)  # Default ordering of the list view
    list_filter = ('unit_name',)    

# @admin.register(VAT)   
# class VATAdmin(admin.ModelAdmin):
#     list_display = ('VAT_percent', 'VAT_name')  # Columns to display in the list view
#     search_fields = ('VAT_percent', 'VAT_name')  # Fields that can be searched
#     ordering = ('VAT_percent',)  # Default ordering of the list view
#     list_filter = ('VAT_name',) 
    

@admin.register(OutstandingReport)
class OutstandingReportAdmin(admin.ModelAdmin):
    list_display = ('bill_no', 'invoice_no', 'debit_amount', 'credit_amount', 'balance_amount')
    search_fields = ( 'bill_no', 'invoice_no')
     
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_mobile', 'customer_email', 'customer_city', 'customer_country')
    search_fields = ('customer_name', 'customer_email')
    list_filter = ('customer_country', 'customer_city') 
    
       
    
class BillByBillAdmin(admin.ModelAdmin):
    list_display = ('outstanding', 'settle_amount', 'settle_date')  # Fields to display in the list view
    list_filter = ('settle_date',)  # Optionally filter by settle date
    search_fields = ('outstanding__bill_no',)  # Search by bill number (ForeignKey relationship)
    date_hierarchy = 'settle_date'  # Add a date hierarchy filter by settle_date
    ordering = ('-settle_date',)  # Optionally order by settle_date descending
    # Optionally, you can add formfields to customize the fields displayed
    fieldsets = (
        (None, {
            'fields': ('outstanding', 'settle_amount', 'settle_date')
        }),
    )

# Register the BillByBill model with the custom admin class
admin.site.register(BillByBill, BillByBillAdmin)    

@admin.register(DayBookReport)
class DayBookReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'ledger', 'voucher_type', 'debit_amount', 'credit_amount', 'invoice_no')  # Columns to display in the list view
    search_fields = ('ledger', 'voucher_type', 'invoice_no')  # Fields searchable in the admin
    list_filter = ('date', 'voucher_type')  # Filters in the sidebar
    ordering = ('-date',)  # Order by date descending
    
@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'description')  # Columns to display in the list view
    search_fields = ('name', 'code')  # Enables search functionality
    list_filter = ('name',)  # Filters for better navigation
    ordering = ('name',)  # Orders by name in ascending order    
    

    

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('BatchNo', 'Item', 'Mfd', 'Exp', 'IsActive', 'created_on', 'updated_on')
    list_filter = ('IsActive', 'Item')
    search_fields = ('BatchNo', 'Item__name')  # Adjust 'Item__name' based on your Item model field
    
class VouchersAdmin(admin.ModelAdmin):
    list_display = ('VoucherName', 'VoucherType', 'Suffix', 'Prefix', 'MinLength', 'created_on', 'updated_on')
    search_fields = ('VoucherName', 'VoucherType')
    list_filter = ('VoucherType',)
    ordering = ('created_on',)
    readonly_fields = ('created_on', 'updated_on')
admin.site.register(Vouchers, VouchersAdmin)    

class StockAdmin(admin.ModelAdmin):
    list_display = ('voucherDate', 'voucherType', 'voucherNo', 'item', 'batch', 'unit', 'costCenter', 'rate', 'in_quantity', 'out_quantity', 'stock_value', 'created_on', 'updated_on')
    search_fields = ('item__name', 'voucherNo')  # Assuming 'name' is a field in the Item model
    list_filter = ('voucherDate', 'voucherType', 'item', 'batch', 'unit', 'costCenter')
    ordering = ('-created_on',)  # Order by created date descending
    readonly_fields = ('created_on', 'updated_on')
    def get_queryset(self, request):
        # Optionally customize the queryset if needed
        return super().get_queryset(request)
admin.site.register(Stock, StockAdmin)


@admin.register(TAX)
class TAXAdmin(admin.ModelAdmin):
    list_display = ('TAX_percent', 'TAX_name')
    search_fields = ('TAX_name',)
    list_filter = ('TAX_percent',)
    
    
class StockTransferItemInline(admin.TabularInline):
    model = StockTransferItem
    extra = 1
    autocomplete_fields = ['item', 'unit', 'batch']
    fields = ['item', 'unit', 'batch', 'quantity', 'rate']
    show_change_link = True


@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ['voucher_no', 'transfer_date', 'source_cost_center', 'destination_cost_center']
    search_fields = ['voucher_no', 'source_cost_center__name', 'destination_cost_center__name']
    list_filter = ['transfer_date', 'source_cost_center', 'destination_cost_center']
    inlines = [StockTransferItemInline]
    readonly_fields = ['transfer_date']
    autocomplete_fields = ['source_cost_center', 'destination_cost_center']
    ordering = ['-transfer_date']


@admin.register(StockTransferItem)
class StockTransferItemAdmin(admin.ModelAdmin):
    list_display = ['stock_transfer', 'item', 'unit', 'quantity', 'rate']
    search_fields = ['item__item_name', 'stock_transfer__voucher_no']
    autocomplete_fields = ['item', 'unit', 'batch', 'stock_transfer']


from django.contrib import admin
from django.utils.html import format_html
from .models import PurchaseMaster, PurchaseDetail, ItemGrvMaster, ItemGrvDetail

@admin.register(ItemGrvMaster)
class ItemGrvMasterAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'transaction_date', 'IsInvoiced', 'isDeleted')
    list_filter = ('IsInvoiced', 'isDeleted')
    search_fields = ('voucher_no',)
    date_hierarchy = 'transaction_date'

class PurchaseDetailInline(admin.TabularInline):
    model = PurchaseDetail
    extra = 0
    fields = (
        'item_group', 'item_name', 'item_code', 'barcode_code',
        'Batch', 'MFD', 'EXP', 'unit',
        'quantity', 'free_quantity',
        'purchase_rate', 'item_net_amount', 'tax', 'item_tax_amount',
        'sales_rate', 'profit', 'item_total_amount',
        'Cost', 'Cess', 'SerialNo',
    )
    autocomplete_fields = ('item_name', 'Batch')
    show_change_link = True


@admin.register(PurchaseMaster)
class PurchaseMasterAdmin(admin.ModelAdmin):
    list_display = (
        'voucher_no', 'auto_no', 'transaction_date', 'ledger',
        'voucherType', 'payment_mode', 'grand_total_amount',
        'IsCleared', 'linked_grv', 'isDeleted',
    )
    list_filter = (
        'payment_mode', 'IsCleared', 'isDeleted', 'voucherType',
        'cost_center', 'transaction_date',
    )
    search_fields = (
        'voucher_no', 'VendorInvNo', 'ledger__ledger_name',
        'item_grv__voucher_no',
    )
    date_hierarchy = 'transaction_date'
    ordering = ('-auto_no',)
    readonly_fields = ('auto_no', 'created_on', 'updated_on')
    autocomplete_fields = ('ledger', 'item_grv')
    inlines = [PurchaseDetailInline]

    fieldsets = (
        ('Voucher Info', {
            'fields': (
                'voucher_no', 'auto_no', 'voucherType', 'transaction_date',
                'ledger', 'payment_mode', 'cost_center',
            )
        }),
        ('Vendor Invoice', {
            'fields': ('VendorInvNo', 'InvoiceDate', 'item_grv')
        }),
        ('Freight / Transport', {
            'fields': ('lrNo', 'transportCompany', 'Freight'),
            'classes': ('collapse',),
        }),
        ('Totals', {
            'fields': (
                'total_net_value', 'total_tax_amount',
                'discount', 'grand_total_amount',
            )
        }),
        ('Status', {
            'fields': ('IsCleared', 'isDeleted', 'remarks', 'payment_terms')
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',),
        }),
    )

    def linked_grv(self, obj):
        if obj.item_grv_id:
            return format_html(
                '<span style="color:#2e7d32;">✔ {}</span>', obj.item_grv.voucher_no
            )
        return '—'
    linked_grv.short_description = 'GRV'


@admin.register(PurchaseDetail)
class PurchaseDetailAdmin(admin.ModelAdmin):
    list_display = (
        'purchase', 'item_group', 'item_name', 'item_code', 'Batch',
        'quantity', 'purchase_rate', 'tax', 'item_total_amount',
    )
    list_filter = ('item_group', 'unit', 'isexp')
    search_fields = (
        'purchase__voucher_no', 'item_name__item_name',
        'item_code', 'barcode_code', 'SerialNo',
    )
    autocomplete_fields = ('purchase', 'item_name', 'Batch', 'unit', 'BaseUnit')
    readonly_fields = ('created_on', 'updated_on')    

class OpeningStockDetailInline(admin.TabularInline):
    model = OpeningStockDetail
    extra = 0
    fields = (
        'item_group',
        'item_code',
        'item_name',
        'barcode_code',
        'quantity',
        'purchase_rate',
        'item_net_amount',
        'tax',
        'item_tax_amount',
        'unit',
        'item_total_amount',
        'QtyInBaseUnit',
        'RateInBaseUnit',
        'BaseUnit',
        'SerialNo',
        'Cost',
    )
    readonly_fields = ('created_on', 'updated_on')
    show_change_link = True


@admin.register(OpeningStockMaster)
class OpeningStockMasterAdmin(admin.ModelAdmin):
    list_display = (
        'voucher_no',
        'voucherType',
        'transaction_date',
        'cost_center',
        'total_net_value',
        'total_tax_amount',
        'grand_total_amount',
        'IsCleared',
        'created_on',
    )

    list_filter = (
        'voucherType',
        'transaction_date',
        'cost_center',
        'IsCleared',
    )

    search_fields = (
        'voucher_no',
        'remarks',
        'items__item_code',       # Search by Item Code
        'items__barcode_code',    # Search by Barcode
        'items__item_name__item_name',  # Search by Item Name
    )

    date_hierarchy = 'transaction_date'

    inlines = [OpeningStockDetailInline]

    ordering = ('-transaction_date', '-id')


@admin.register(OpeningStockDetail)
class OpeningStockDetailAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'opening_stock',
        'item_code',
        'item_name',
        'barcode_code',
        'quantity',
        'purchase_rate',
        'item_total_amount',
        'SerialNo',
    )

    search_fields = (
        'item_code',
        'barcode_code',
        'item_name__item_name',
        'opening_stock__voucher_no',
    )

    list_filter = (
        'item_group',
        'unit',
        'BaseUnit',
    )

    list_select_related = (
        'opening_stock',
        'item_name',
        'item_group',
        'unit',
        'BaseUnit',
    )

    ordering = ('-id',)    