from django.contrib import admin
from accounts_app.models import  *
from django.contrib.auth.admin import UserAdmin


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_admin')
    search_fields = ('name',)
    list_filter = ('is_admin',)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'user_role', 'is_active', 'is_staff')
    list_filter = ('is_active', 'is_staff', 'user_role')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'address', 'place')}),
        ('Role & Permissions', {'fields': ('user_role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email', 'phone', 'address', 'place',
                'user_role', 'password1', 'password2', 'is_active', 'is_staff'
            )
        }),
    )


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'group')
    search_fields = ('name', 'group')
    list_filter = ('group',)


@admin.register(UserPrivilege)
class UserPrivilegeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user_role', 'menu', 'can_add', 'can_edit', 'can_delete', 'can_read',
        'can_cancel', 'can_email', 'can_print', 'can_export', 'can_sms'
    )
    list_filter = ('user_role', 'menu')
    search_fields = ('user_role__name', 'menu__name')
    
    
    
@admin.register(Subgroup)
class SubgroupAdmin(admin.ModelAdmin):
    list_display = ('sub_group_name', 'sub_group_description')
    search_fields = ('sub_group_name',)
    ordering = ('sub_group_name',)

@admin.register(LedgerCreation)
class LedgerCreationAdmin(admin.ModelAdmin):
    list_display = ('id','ledger_name', 'sub_group', 'opening_balance', 'types', 'remark', 'trn_number')
    search_fields = ('ledger_name', 'trn_number')
    list_filter = ('sub_group', 'types')
    ordering = ('ledger_name',)
    readonly_fields = ('trn_number',)  # If you want to make 'trn_number' read-only
    
class LocalPaymentItemsInline(admin.TabularInline):
    model = LocalPaymentItems
    extra = 1
    fields = ('invoice_date', 'invoice_no', 'ledger', 'description', 'amount')

@admin.register(LocalPayment)
class LocalPaymentAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'date', 'party', 'payment_mode', 'net_amount')
    list_filter = ('date', 'payment_mode')
    search_fields = ('voucher_no', 'party', 'reference_no', 'party_VAT_no')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                ('date', 'voucher_no'),
                ('payment_mode', 'party'),
                ('reference_no', 'party_VAT_no')
            )
        }),
        ('Notes', {
            'fields': ('remark', 'note')
        }),
        ('Amount Details', {
            'fields': (('taxable_amount', 'VAT_amount', 'net_amount'),)
        })
    )
    
    inlines = [LocalPaymentItemsInline]

@admin.register(LocalPaymentItems)
class LocalPaymentItemsAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'invoice_date', 'ledger', 'amount', 'localpayment')
    list_filter = ('invoice_date', 'ledger')
    search_fields = ('invoice_no', 'description', 'localpayment__voucher_no')
    
@admin.register(LocalPaymentCheque)
class LocalPaymentChequeAdmin(admin.ModelAdmin):
    list_display = ('cheque_no', 'cheque_date', 'issuing_bank_name', 'cheque_status', 'reference_no')
    search_fields = ('cheque_no', 'issuing_bank_name', 'reference_no')
    list_filter = ('cheque_status', 'cheque_date', 'issuing_bank_name')
    date_hierarchy = 'cheque_date'
    ordering = ('-cheque_date',)    
    
    
class ReceiptItemsInline(admin.TabularInline):
    model = ReceiptItems
    extra = 1
    fields = ('ledger', 'description', 'amount')
    readonly_fields = ('amount',)


class ReceiptChequeInline(admin.TabularInline):
    model = ReceiptCheque
    extra = 1
    fields = ('cheque_no', 'cheque_date', 'issuing_bank_name', 'reference_no', 'cheque_status')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'date', 'payment_type', 'payment_mode', 'net_amount')
    list_filter = ('payment_type', 'payment_mode', 'date')
    search_fields = ('voucher_no', 'ledger_name')
    date_hierarchy = 'date'
    inlines = [ReceiptItemsInline, ReceiptChequeInline]

    fieldsets = (
        ('Receipt Details', {
            'fields': ('voucher_no', 'date', 'payment_type', 'payment_mode', 'reference_no')
        }),
        ('Tax Information', {
            'fields': ('tax_rate', 'taxable_amount', 'VAT_amount', 'net_amount'),
        }),
    )
    readonly_fields = ('taxable_amount', 'VAT_amount', 'net_amount')


@admin.register(ReceiptItems)
class ReceiptItemsAdmin(admin.ModelAdmin):
    list_display = ('receipt', 'ledger', 'description', 'amount')
    search_fields = ('receipt__voucher_no', 'ledger__name')


@admin.register(ReceiptCheque)
class ReceiptChequeAdmin(admin.ModelAdmin):
    list_display = ('receipt', 'cheque_no', 'cheque_date', 'issuing_bank_name', 'cheque_status')
    list_filter = ('cheque_status',)
    search_fields = ('cheque_no', 'issuing_bank_name', 'receipt__voucher_no')    
    
@admin.register(Contra)
class ContraAdmin(admin.ModelAdmin):
    list_display = (
        'date', 
        'voucher_no', 
        'contra_type', 
        'dr_ledger', 
        'cr_ledger', 
        'amount'
    )
    list_filter = ('contra_type', 'date')
    search_fields = ('voucher_no', 'dr_ledger__ledger_name', 'cr_ledger__ledger_name')
    date_hierarchy = 'date'
    fieldsets = (
        ('Contra Details', {
            'fields': ('date', 'voucher_no', 'contra_type', 'dr_ledger', 'cr_ledger')
        }),
        ('Transaction Details', {
            'fields': ('cheque_no', 'cheque_date', 'amount', 'remark'),
            'classes': ('collapse',),
        }),
    )    
    
class JournalAdmin(admin.ModelAdmin):
    list_display = ('date', 'voucher_no', 'dr_ledger', 'cr_ledger', 'amount', 'due_date', 'narration')
    search_fields = ('voucher_no', 'dr_ledger__ledger_name', 'cr_ledger__ledger_name', 'narration')
    list_filter = ('date', 'dr_ledger', 'cr_ledger')
    ordering = ('-date',)
    date_hierarchy = 'date'

admin.site.register(Journal, JournalAdmin)   

@admin.register(Groups)
class GroupsAdmin(admin.ModelAdmin):
    list_display = ('id', 'groupName', 'groupId', 'natureOfGroup', 'isDefault')
    list_filter = ('isDefault',)
    search_fields = ('groupName', 'group_desc')
    readonly_fields = ('natureOfGroup',)

    def has_change_permission(self, request, obj=None):
        if obj and obj.isDefault:
            return False
        return super().has_change_permission(request, obj=obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.isDefault:
            return False
        return super().has_delete_permission(request, obj=obj) 


@admin.register(LedgerPosting)
class LedgerPostingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'date', 'VoucherType', 'VoucherNo', 'ledger',
        'debit', 'credit', 'CostCenter', 'FY', 'IsDeleted',
        'created_on', 'updated_on'
    )
    list_filter = ('VoucherType', 'ledger', 'CostCenter', 'IsDeleted', 'FY')
    search_fields = (
        'VoucherNo',
        'ledger__ledger_name',
        'VoucherType__VoucherName',
    )
    date_hierarchy = 'date'
    readonly_fields = ('created_on', 'updated_on', 'created_by', 'updated_by')
    ordering = ('-date',)
    list_per_page = 25    
    
# Inline configuration for ReceiptBillDetails
class ReceiptBillDetailsInline(admin.TabularInline):
    model = ReceiptBillDetails
    extra = 0
    fields = ('voucherType', 'VoucherNo', 'Amount')
    readonly_fields = ('voucherType',)
    autocomplete_fields = ()
    show_change_link = True


# Main admin for ReceiptBillMaster
@admin.register(ReceiptBillMaster)
class ReceiptBillMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'voucher_no', 'voucherType', 'Date', 'Customer', 'Ledger', 'TotalAmount', 'Remark')
    list_filter = ('voucher_no', 'voucherType', 'Date', 'Ledger')
    search_fields = ('Customer__ledger_name', 'Ledger__ledger_name', 'Remark')
    inlines = [ReceiptBillDetailsInline]
    date_hierarchy = 'Date'
    ordering = ('-Date',)
    readonly_fields = ('created_on', 'updated_on', 'created_by', 'updated_by')

    fieldsets = (
        ("Basic Info", {
            "fields": ("voucher_no", "voucherType", "Date", "Customer", "Ledger", "TotalAmount", "Remark")
        }),
        ("Cheque Info", {
            "fields": ("ChequeNo", "ChequeDate", "ChequeStatus"),
            "classes": ("collapse",)
        }),
        ("System Fields", {
            "fields": ("created_on", "updated_on", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )


# Optional: register details separately for viewing
@admin.register(ReceiptBillDetails)
class ReceiptBillDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'BillMaster', 'voucherType', 'VoucherNo', 'CurrentAmount' ,'Amount')
    list_filter = ('voucherType',)
    search_fields = ('VoucherNo', 'BillMaster__Customer__ledger_name')
    ordering = ('-id',)
    




# Inline configuration for PaymentBillDetails
class PaymentBillDetailsInline(admin.TabularInline):
    model = PaymentBillDetails
    extra = 0
    fields = ('voucherType', 'VoucherNo', 'Amount')
    readonly_fields = ('voucherType',)
    autocomplete_fields = ()
    show_change_link = True


# Main admin for PaymentBillMaster
@admin.register(PaymentBillMaster)
class PaymentBillMasterAdmin(admin.ModelAdmin):
    list_display = ('id', 'Date', 'Supplier', 'Ledger', 'TotalAmount', 'Remark')
    list_filter = ('Date', 'Ledger')
    search_fields = ('Customer__ledger_name', 'Ledger__ledger_name', 'Remark')
    inlines = [PaymentBillDetailsInline]
    date_hierarchy = 'Date'
    ordering = ('-Date',)
    readonly_fields = ('created_on', 'updated_on', 'created_by', 'updated_by')

    fieldsets = (
        ("Basic Info", {
            "fields": ("Date", "Supplier", "Ledger", "TotalAmount", "Remark")
        }),
        ("Cheque Info", {
            "fields": ("ChequeNo", "ChequeDate", "ChequeStatus"),
            "classes": ("collapse",)
        }),
        ("System Fields", {
            "fields": ("created_on", "updated_on", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )


# Optional: register details separately for viewing
@admin.register(PaymentBillDetails)
class PaymentBillDetailsAdmin(admin.ModelAdmin):
    list_display = ('id', 'BillMaster', 'voucherType', 'VoucherNo', 'Amount')
    list_filter = ('voucherType',)
    search_fields = ('VoucherNo', 'BillMaster__Supplier__ledger_name')
    ordering = ('-id',)    
    
class PaymentDetailsInline(admin.TabularInline):
    model = PaymentDetails
    extra = 1


@admin.register(PaymentMaster)
class PaymentMasterAdmin(admin.ModelAdmin):
    list_display = ("voucher_no", "Date", "Ledger", "PaidTo", "IsPDC", "Cleared")
    search_fields = ("voucher_no", "PaidTo", "Ledger__LedgerName")
    list_filter = ("IsPDC", "Cleared", "Date")
    inlines = [PaymentDetailsInline]


@admin.register(PaymentDetails)
class PaymentDetailsAdmin(admin.ModelAdmin):
    list_display = ("Payment", "Ledger", "Amount", "Desc")
    search_fields = ("Payment__voucher_no", "Ledger__LedgerName", "Desc")
    list_filter = ("Payment__Date",)
    
class ReceiptDetailsInline(admin.TabularInline):
    model = ReceiptDetails
    extra = 1


@admin.register(ReceiptMaster)
class ReceiptMasterAdmin(admin.ModelAdmin):
    list_display = ("voucher_no", "Date", "Ledger", "ReceivedFrom", "IsPDC", "Cleared")
    search_fields = ("voucher_no", "ReceivedFrom", "Ledger__LedgerName")
    list_filter = ("IsPDC", "Cleared", "Date")
    inlines = [ReceiptDetailsInline]


@admin.register(ReceiptDetails)
class ReceiptDetailsAdmin(admin.ModelAdmin):
    list_display = ("Receipt", "Ledger", "Amount", "Desc")
    search_fields = ("Receipt__voucher_no", "Ledger__LedgerName", "Desc")
    list_filter = ("Receipt__Date",)    

@admin.register(BillWiseOpening)
class BillWiseOpeningAdmin(admin.ModelAdmin):
    # Columns displayed in the admin list view
    list_display = (
        'InvNo',
        'ledger',
        'voucherType',
        'InvDate',
        'po_no',
        'InvAmount',
        'InvBalance',
        'dr_cr',
        'IsCleared',
        'IsClosed',
        'CreatedOn',
    )

    # Filters available in the right sidebar
    list_filter = (
        'dr_cr',
        'IsCleared',
        'IsClosed',
        'voucherType',
        'InvDate',
    )

    # Search functionality across primary fields and ForeignKey fields
    search_fields = (
        'InvNo',
        'po_no',
        'ledger__ledger_name',  # Replace 'ledger_name' with your actual Ledger model field name if different
    )

    # Enables drill-down navigation by date at the top of the list page
    date_hierarchy = 'InvDate'

    # Auto-managed date fields should be read-only in the admin panel
    readonly_fields = ('CreatedOn', 'UpdatedOn')

    # Quick inline editing for boolean flags directly from list view (optional)
    list_editable = ('IsCleared', 'IsClosed')

    # Prevents huge drop-downs if you have thousands of Ledgers or Vouchers
    raw_id_fields = ('ledger', 'voucherType')

    # Logical grouping of fields on the detail edit form
    fieldsets = (
        ('Invoice Details', {
            'fields': ('ledger', 'voucherType', 'InvNo', 'InvDate', 'po_no')
        }),
        ('Amount & Balance', {
            'fields': ('InvAmount', 'InvBalance', 'dr_cr')
        }),
        ('Status Flags', {
            'fields': ('IsCleared', 'IsClosed')
        }),
        ('Audit Metadata', {
            'classes': ('collapse',),  # Collapsible group
            'fields': ('CreatedOn', 'UpdatedOn'),
        }),
    )    

class OpeningVoucherDetailsInline(admin.TabularInline):
    model = OpeningVoucherDetails
    extra = 1
    fields = ('ledger', 'debit_amount', 'credit_amount')


@admin.register(OpeningVoucherMaster)
class OpeningVoucherMasterAdmin(admin.ModelAdmin):
    list_display = ('voucher_no', 'date', 'voucherType', 'cost_conter', 'sales_person', 'remark')
    list_filter = ('date', 'voucherType', 'cost_conter', 'sales_person')
    search_fields = ('voucher_no', 'remark')
    ordering = ('-date', '-id')
    inlines = [OpeningVoucherDetailsInline]


@admin.register(OpeningVoucherDetails)
class OpeningVoucherDetailsAdmin(admin.ModelAdmin):
    list_display = ('opening_voucher', 'ledger', 'debit_amount', 'credit_amount')
    search_fields = ('opening_voucher__voucher_no', 'ledger__ledger_name')
    list_filter = ('opening_voucher',)    