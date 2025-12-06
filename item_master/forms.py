from django import forms
from accounts_app.models import Groups
from item_master.models import *
from django.forms import inlineformset_factory, modelformset_factory
from item_master.common import get_ledgers_by_group_ids, filter_voucher_types





class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['category_name']

        labels = {
            'category_name': 'Category Name',
        }
        
        widgets = {
            'category_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter category name'}
            ),
        }

# ItemManufacturerForm
class ItemManufacturerForm(forms.ModelForm):
    class Meta:
        model = ItemManufacturer
        fields = ['manufacturer_name']

        labels = {
            'manufacturer_name': 'Manufacturer Name',
        }
        
        widgets = {
            'manufacturer_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Enter manufacturer name'}
            ),
        }    

# ItemForm
class ItemForm(forms.ModelForm):
    item_unit = forms.ModelChoiceField(
        queryset=Unit.objects.all(),
        to_field_name='unit_code',  # Use unit_code instead of id
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Item
        fields = [
            'item_name',
            'item_code',
            'IsItemBarcode',
            'barcode_code',
            'regional_name',
            'item_category',
            'item_manufacturer',
            'TAX',
            'min_stock',
            'rack',
            'purchase_rate',
            'sales_rate',
            'MRP',
            'item_unit',
            'uc_factor',
            'remarks',
            'item_class',
            'item_image',
            'is_base_unit',
            'cost_center',
            'MaxStock',
            'Reorder',
            'isDeleted',
            'WholeSalePrice',
            'SchemaPerc',
            'ProfitPerc',
            'CrediRateRet',
            'CreditRateWhol',
            'WholeProfitPerc',
            'Warrenty',
            'IsBatch',
            'IsExpiry',
            'TaxIncludExclud',
            'ProfitPercWholeCredit',
            'ProfitPercRetCrdt',
            'HSN',
            'Rack',
            'IsNonInventory',
            'SizeId',
            'IsSkipPrint',
            'TaxIncludPrchs',
            'cess',
            'IsProductSerial',
        ]

        labels = {
            'item_name': 'Item Name',
            'item_code': 'Item Code',
            'barcode_code': 'Barcode',
            'regional_name': 'Regional Name',
            'item_category': 'Item Category',
            'item_manufacturer': 'Manufacturer',
            'TAX': 'Tax',
            'min_stock': 'Minimum Stock',
            'rack': 'Rack',
            'purchase_rate': 'Purchase Rate',
            'sales_rate': 'Sales Rate',
            'MRP': 'Maximum Retail Price',
            'item_unit': 'Item Unit',
            'uc_factor': 'Unit Conversion Factor',
            'remarks': 'Remarks',
            'item_class': 'Item Class',
            'item_image': 'Item Image',
            'is_base_unit': 'Is Base Unit',
            'cost_center': 'Cost Center',
            'MaxStock': 'Maximum Stock',
            'Reorder': 'Reorder Level',
            'isDeleted': 'Mark as Deleted',
            'WholeSalePrice': 'Wholesale Price',
            'SchemaPerc': 'Schema Percentage',
            'ProfitPerc': 'Profit Percentage',
            'CrediRateRet': 'Credit Rate (Retail)',
            'CreditRateWhol': 'Credit Rate (Wholesale)',
            'WholeProfitPerc': 'Wholesale Profit Percentage',
            'Warrenty': 'Warranty (Months)',
            'IsBatch': ' Batch',
            'IsExpiry': ' Expiry',
            'TaxIncludExclud': 'Tax Inclusive/Exclusive',
            'ProfitPercWholeCredit': 'Wholesale Credit Profit %',
            'ProfitPercRetCrdt': 'Retail Credit Profit %',
            'HSN': 'HSN Code',
            'Rack': 'Rack 2 (Extra)',
            'IsNonInventory': 'Non Inventory Item',
            'SizeId': 'Size ID',
            'IsSkipPrint': 'Skip Print',
            'TaxIncludPrchs': 'Tax Included in Purchase',
            'cess': 'Cess (%)',
            'IsProductSerial': 'Has Product Serial?',
        }

        widgets = {
            'item_name': forms.TextInput(attrs={'class': 'form-control'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control'}),
            'IsItemBarcode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'barcode_code': forms.TextInput(attrs={'class': 'form-control'}),
            'regional_name': forms.TextInput(attrs={'class': 'form-control'}),
            'item_category': forms.Select(attrs={'class': 'form-control'}),
            'item_manufacturer': forms.Select(attrs={'class': 'form-control'}),
            'TAX': forms.Select(attrs={'class': 'form-control'}),
            'min_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'rack': forms.TextInput(attrs={'class': 'form-control'}),
            'purchase_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'sales_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'MRP': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_unit': forms.Select(attrs={'class': 'form-control'}),
            'uc_factor': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'item_class': forms.Select(attrs={'class': 'form-control'}),
            'item_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_base_unit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cost_center': forms.Select(attrs={'class': 'form-control'}),
            'MaxStock': forms.NumberInput(attrs={'class': 'form-control'}),
            'Reorder': forms.NumberInput(attrs={'class': 'form-control'}),
            'isDeleted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'WholeSalePrice': forms.NumberInput(attrs={'class': 'form-control'}),
            'SchemaPerc': forms.NumberInput(attrs={'class': 'form-control'}),
            'ProfitPerc': forms.NumberInput(attrs={'class': 'form-control'}),
            'CrediRateRet': forms.NumberInput(attrs={'class': 'form-control'}),
            'CreditRateWhol': forms.NumberInput(attrs={'class': 'form-control'}),
            'WholeProfitPerc': forms.NumberInput(attrs={'class': 'form-control'}),
            'Warrenty': forms.NumberInput(attrs={'class': 'form-control'}),
            'IsBatch': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'IsExpiry': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'TaxIncludExclud': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ProfitPercWholeCredit': forms.NumberInput(attrs={'class': 'form-control'}),
            'ProfitPercRetCrdt': forms.NumberInput(attrs={'class': 'form-control'}),
            'HSN': forms.TextInput(attrs={'class': 'form-control'}),
            'Rack': forms.TextInput(attrs={'class': 'form-control'}),
            'IsNonInventory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'SizeId': forms.NumberInput(attrs={'class': 'form-control'}),
            'IsSkipPrint': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'TaxIncludPrchs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'cess': forms.NumberInput(attrs={'class': 'form-control'}),
            'IsProductSerial': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        
    # Custom validation for item_code uniqueness
    def clean_item_code(self):
        item_code = self.cleaned_data.get('item_code')
        
        return item_code


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'vendor_name', 'vendor_mobile', 'vendor_phone', 'vendor_email', 
            'vendor_address_1', 'vendor_address_2', 'vendor_country', 'vendor_state', 
            'vendor_city', 'vendor_zipcode', 'vendor_website', 'vendor_description', 
            'vendor_VAT', 'vendor_TRN_or_CRN'
        ]
        
        labels = {
            'vendor_name': 'vendor Name',
            'vendor_mobile': 'Mobile',
            'vendor_phone': 'Phone',
            'vendor_email': 'vendor Email',
            'vendor_address_1': 'Address Line 1',
            'vendor_address_2': 'Address Line 2',
            'vendor_country': 'Country',
            'vendor_state': 'State',
            'vendor_city': 'City',
            'vendor_zipcode': 'Zipcode',
            'vendor_website': 'Website',
            'vendor_description': 'Description',
            'vendor_VAT': 'VAT Number',
            'vendor_TRN_or_CRN': 'TRN/CRN Number',
        }
        
        widgets = {
            'vendor_name': forms.TextInput(attrs={'placeholder': 'Enter vendor name'}),
            'vendor_mobile': forms.TextInput(attrs={'placeholder': 'Enter mobile number'}),
            'vendor_phone': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'vendor_email': forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
            'vendor_address_1': forms.Textarea(attrs={'placeholder': 'Enter address line 1', 'rows': 2}),
            'vendor_address_2': forms.Textarea(attrs={'placeholder': 'Enter address line 2', 'rows': 2}),
            'vendor_country': forms.TextInput(attrs={'placeholder': 'Enter country'}),
            'vendor_state': forms.TextInput(attrs={'placeholder': 'Enter state'}),
            'vendor_city': forms.TextInput(attrs={'placeholder': 'Enter city'}),
            'vendor_zipcode': forms.TextInput(attrs={'placeholder': 'Enter zipcode'}),
            'vendor_website': forms.URLInput(attrs={'placeholder': 'Enter vendor website'}),
            'vendor_description': forms.Textarea(attrs={'placeholder': 'Enter vendor description', 'rows': 4}),
            'vendor_VAT': forms.TextInput(attrs={'placeholder': 'Enter VAT number'}),
            'vendor_TRN_or_CRN': forms.TextInput(attrs={'placeholder': 'Enter TRN or CRN number'}),
        }   

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['unit_code', 'unit_name']
        labels = {
            'unit_code': 'Unit Code',
            'unit_name': 'Unit Name',
        }
        widgets = {
            'unit_code': forms.TextInput(attrs={'placeholder': 'Enter Unit Code'}),
            'unit_name': forms.TextInput(attrs={'placeholder': 'Enter Unit Name'}),
        }

class TAXForm(forms.ModelForm):
    class Meta:
        model = TAX
        fields = ['TAX_percent', 'TAX_name']
        labels = {
            'TAX_percent': 'TAX %',
            'TAX_name': 'TAX Name',
        }
        widgets = {
            'TAX_percent': forms.TextInput(attrs={'placeholder': 'Enter TAX %'}),
            'TAX_name': forms.TextInput(attrs={'placeholder': 'Enter TAX Name'}),
        }        
        
class PurchaseVoucherForm(forms.ModelForm):
    class Meta:
        model = PurchaseMaster
        fields = [
            'auto_no',  
            'voucher_no',
            'transaction_date',
            'ledger',
            'payment_mode',
            'remarks',
            'total_net_value',
            'total_tax_amount',
            'discount',
            'payment_terms',
            'grand_total_amount',
            'cost_center',
            'lrNo',
            'transportCompany',
            'Freight',
            'VendorInvNo',
            'InvoiceDate',
            'voucherType',
            
        ]
        widgets = {
            'auto_no': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True,
            }),
            'voucher_no': forms.TextInput(attrs={
                'placeholder': 'Voucher No',
                'class': 'form-control',
                'id': 'id_voucher_no',
                'readonly': True,
                
            }),
            'transaction_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Transaction Date',
                'class': 'form-control'
            }),
            'ledger': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'remarks': forms.TextInput(attrs={
                'placeholder': 'Remarks (optional)',
                'class': 'form-control',
                'rows': 3
            }),
            'total_net_value': forms.NumberInput(attrs={
                'placeholder': 'Total Net Value',
                'class': 'form-control',
                'readonly': True
            }),
            'total_tax_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Tax Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'discount': forms.NumberInput(attrs={
                'placeholder': 'Discount (if any)',
                'class': 'form-control'
            }),
            'payment_terms': forms.TextInput(attrs={
                'placeholder': 'Payment Terms (optional)',
                'class': 'form-control',
                'rows': 3
            }),
            'grand_total_amount': forms.NumberInput(attrs={
                'placeholder': 'Grand Total Amount',
                'class': 'form-control', 
                'readonly': True
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lrNo': forms.TextInput(attrs={
                'placeholder': 'LR No',
                'class': 'form-control'
            }),
            'transportCompany': forms.TextInput(attrs={
                'placeholder': 'Transport Company',
                'class': 'form-control'
            }),
            'Freight': forms.NumberInput(attrs={
                'placeholder': 'Freight',
                'class': 'form-control'
            }),
            'VendorInvNo': forms.TextInput(attrs={
                'placeholder': 'Vendor Invoice No',
                'class': 'form-control'
            }),
            'InvoiceDate': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Invoice Date',
                'class': 'form-control'
            }),
            'voucherType': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_voucherType',
                'onchange': 'updateVoucherNumber()'
            }),
        }
        labels = {
            'auto_no': 'Auto Number',
            'voucher_no': 'Invoice Number',
            'transaction_date': 'Date',
            'ledger': 'Vendor',
            'payment_mode': 'Payment Mode',
            'remarks': 'Remarks',
            'total_net_value': 'Total Net Value',
            'total_tax_amount': 'Total Tax Amount',
            'discount': 'Discount',
            'payment_terms': 'Payment Terms',
            'grand_total_amount': 'Grand Total Amount',
            'cost_center': 'Cost Center',
            'lrNo': 'LR No',
            'transportCompany': 'Transport Company',
            'Freight': 'Freight',
            'VendorInvNo': 'Vendor Invoice No',
            'InvoiceDate': 'Invoice Date',
            'voucherType': 'Voucher Type',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['voucher_no'].required = False

        # ✅ Only for NEW instance (creation)
        if not self.instance.pk:
            if 'voucherType' in self.data:   # POST create
                try:
                    voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                    self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
                except Vouchers.DoesNotExist:
                    pass
            elif self.initial.get('voucherType'):  # GET create
                try:
                    voucher_type = self.initial['voucherType']
                    self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
                except Exception:
                    pass
        else:
            # ✅ Editing: always use instance value
            self.fields['voucher_no'].initial = self.instance.voucher_no

            
        # Ledger filter by Groups cash account & sundry Sundry Creditors 
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(8, 28)

        # Voucher type filter 
        filter_voucher_types(self, [1])    
            
    
        

class PurchaseVoucherItemForm(forms.ModelForm):
    
    
    class Meta:
        model = PurchaseDetail
        fields = ['item_name','item_code', 'barcode_code', 'quantity', 'purchase_rate', 'item_net_amount', 'tax', 'item_tax_amount', 'unit', 'free_quantity', 'MFD', 'EXP', 
                  'sales_rate', 'profit', 'item_total_amount', 'Batch', 'Cost']
        widgets = {
            
            'item_name': forms.Select(attrs={'class': 'form-control', 'id': 'id_item_name'}),  
            'item_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Code'}),  
           
            
            'barcode_code': forms.TextInput(attrs={
                'placeholder': 'Barcode',
                'class': 'form-control'
            }),
            
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Quantity',
                'class': 'form-control'
            }),
            'purchase_rate': forms.NumberInput(attrs={
                'placeholder': 'Purchase Rate',
                'class': 'form-control'
            }),
            'item_net_amount': forms.NumberInput(attrs={
                'placeholder': 'Net Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'tax': forms.NumberInput(attrs={
                'placeholder': 'Tax (%)',
                'class': 'form-control'
            }),
            'item_tax_amount': forms.NumberInput(attrs={
                'placeholder': 'Tax Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'free_quantity': forms.NumberInput(attrs={
                'placeholder': 'Free Quantity',
                'class': 'form-control'
            }),
            'MFD': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Manufacture Date',
                'class': 'form-control',
                'id': 'id_MFD'
            }),
            'EXP': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Expire Date',
                'class': 'form-control',
                'id': 'id_EXP'
            }),
            'sales_rate': forms.NumberInput(attrs={
                'placeholder': 'Sales Rate',
                'class': 'form-control'
            }),
            'profit': forms.NumberInput(attrs={
                'placeholder': 'Profit',
                'class': 'form-control',
                'readonly': True
            }),
            'item_total_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'Batch': forms.Select(attrs={
                'class': 'form-control', 'id': 'id_Batch'
            }),
            
            
        }
        labels = {
            'item_code': 'Item Code',
            'item_name': 'Item Name',
            'barcode_code': 'Barcode',
            'quantity': 'Quantity',
            'purchase_rate': 'Purchase Rate',
            'item_net_amount': 'Net Amount',
            'tax': 'Tax (%)',
            'item_tax_amount': 'Tax Amount',
            'unit': 'Unit',
            'free_quantity': 'Free Quantity',
            'MFD': 'MFD',
            'EXP': 'EXP',
            'sales_rate': 'Sales Rate',
            'profit': 'Profit',
            'item_total_amount': 'Total Amount',
            'Batch': 'Batch',
            
        }  
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields not required
        self.fields['item_code'].required = False
        self.fields['barcode_code'].required = False
        self.fields['MFD'].required = False
        self.fields['EXP'].required = False
        self.fields['Batch'].required = False
        self.fields['free_quantity'].required = False
        self.fields['Cost'].required = False
        
        # Set default values for numeric fields
        if not self.instance.pk:  # New form
            self.fields['quantity'].initial = 1
            self.fields['purchase_rate'].initial = 0.00
            self.fields['item_net_amount'].initial = 0.00
            self.fields['tax'].initial = 0.00
            self.fields['item_tax_amount'].initial = 0.00
            self.fields['sales_rate'].initial = 0.00
            self.fields['profit'].initial = 0.00
            self.fields['item_total_amount'].initial = 0.00
            self.fields['free_quantity'].initial = 0
            self.fields['Cost'].initial = 0.00


# Create the formset for PurchaseVoucherItem with proper validation
PurchaseVoucherItemFormSet = inlineformset_factory(
    PurchaseMaster,
    PurchaseDetail,
    form=PurchaseVoucherItemForm,
    extra=0,  # Don't show extra empty forms
    can_delete=True,
    min_num=1,  # Require at least one item
    validate_min=True,  # Validate minimum requirement
    fields=[
        'item_name', 'item_code', 'barcode_code', 'quantity', 
        'purchase_rate', 'item_net_amount', 'tax', 'item_tax_amount', 
        'unit', 'free_quantity', 'MFD', 'EXP', 'sales_rate', 
        'profit', 'item_total_amount', 'Batch', 'Cost'
    ]
)


# Custom validation for the formset
class CustomPurchaseVoucherItemFormSet(PurchaseVoucherItemFormSet):
    def clean(self):
        """Add custom validation to the formset"""
        if any(self.errors):
            return
            
        # Check that at least one item exists and is not deleted
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                valid_forms += 1
                
                # Validate required fields for non-deleted forms
                if not form.cleaned_data.get('item_name'):
                    raise forms.ValidationError("Each item must have an item name selected.")
                if not form.cleaned_data.get('quantity') or form.cleaned_data.get('quantity') <= 0:
                    raise forms.ValidationError("Each item must have a valid quantity greater than 0.")
                if not form.cleaned_data.get('purchase_rate') or form.cleaned_data.get('purchase_rate') <= 0:
                    raise forms.ValidationError("Each item must have a valid purchase rate greater than 0.")
        
        if valid_forms == 0:
            raise forms.ValidationError("At least one item is required for the purchase voucher.")

# Use the custom formset
PurchaseVoucherItemFormSet = CustomPurchaseVoucherItemFormSet    


class PurchaseReturnVoucherForm(forms.ModelForm):
    class Meta:
        model = PurchaseReturnMaster
        fields = [
            'auto_no',  
            'voucher_no',
            'transaction_date',
            'ledger',
            'payment_mode',
            'remarks',
            'total_net_value',
            'total_tax_amount',
            'discount',
            'payment_terms',
            'grand_total_amount',
            'cost_center',
            'lrNo',
            'transportCompany',
            'Freight',
            'VendorInvNo',
            'InvoiceDate',
            'voucherType',
            
        ]
        widgets = {
            'auto_no': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True,
            }),
            'voucher_no': forms.TextInput(attrs={
                'placeholder': 'Voucher No',
                'class': 'form-control',
                'id': 'id_voucher_no',
                'readonly': True,
                
            }),
            'transaction_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Transaction Date',
                'class': 'form-control'
            }),
            'ledger': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'remarks': forms.TextInput(attrs={
                'placeholder': 'Remarks (optional)',
                'class': 'form-control',
                'rows': 3
            }),
            'total_net_value': forms.NumberInput(attrs={
                'placeholder': 'Total Net Value',
                'class': 'form-control',
                'readonly': True
            }),
            'total_tax_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Tax Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'discount': forms.NumberInput(attrs={
                'placeholder': 'Discount (if any)',
                'class': 'form-control'
            }),
            'payment_terms': forms.TextInput(attrs={
                'placeholder': 'Payment Terms (optional)',
                'class': 'form-control',
                'rows': 3
            }),
            'grand_total_amount': forms.NumberInput(attrs={
                'placeholder': 'Grand Total Amount',
                'class': 'form-control', 
                'readonly': True
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
            'lrNo': forms.TextInput(attrs={
                'placeholder': 'LR No',
                'class': 'form-control'
            }),
            'transportCompany': forms.TextInput(attrs={
                'placeholder': 'Transport Company',
                'class': 'form-control'
            }),
            'Freight': forms.NumberInput(attrs={
                'placeholder': 'Freight',
                'class': 'form-control'
            }),
            'VendorInvNo': forms.TextInput(attrs={
                'placeholder': 'Vendor Invoice No',
                'class': 'form-control'
            }),
            'InvoiceDate': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Invoice Date',
                'class': 'form-control'
            }),
            'voucherType': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_voucherType',
                'onchange': 'updateVoucherNumber()'
            }),
        }
        labels = {
            'auto_no': 'Auto Number',
            'voucher_no': 'Invoice Number',
            'transaction_date': 'Transaction Date',
            'ledger': 'Vendor',
            'payment_mode': 'Payment Mode',
            'remarks': 'Remarks',
            'total_net_value': 'Total Net Value',
            'total_tax_amount': 'Total Tax Amount',
            'discount': 'Discount',
            'payment_terms': 'Payment Terms',
            'grand_total_amount': 'Grand Total Amount',
            'cost_center': 'Cost Center',
            'lrNo': 'LR No',
            'transportCompany': 'Transport Company',
            'Freight': 'Freight',
            'VendorInvNo': 'Vendor Invoice No',
            'InvoiceDate': 'Invoice Date',
            'voucherType': 'Voucher Type',
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['voucher_no'].required = False

        # ✅ Only for NEW instance (creation)
        if not self.instance.pk:
            if 'voucherType' in self.data:   # POST create
                try:
                    voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                    self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
                except Vouchers.DoesNotExist:
                    pass
            elif self.initial.get('voucherType'):  # GET create
                try:
                    voucher_type = self.initial['voucherType']
                    self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
                except Exception:
                    pass
        else:
            # ✅ Editing: always use instance value
            self.fields['voucher_no'].initial = self.instance.voucher_no

            
        # Ledger filter by Groups cash account & sundry Sundry Creditors 
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(8, 28)

        # Voucher type filter 
        filter_voucher_types(self, [3])    
            
    
        

class PurchaseReturnVoucherItemForm(forms.ModelForm):
    
    
    class Meta:
        model = PurchaseReturnDetail
        fields = ['item_name','item_code', 'barcode_code', 'quantity', 'purchase_rate', 'item_net_amount', 'tax', 'item_tax_amount', 'unit', 'free_quantity', 'MFD', 'EXP', 
                  'sales_rate', 'profit', 'item_total_amount', 'Batch', 'Cost']
        widgets = {
            
            'item_name': forms.Select(attrs={'class': 'form-control', 'id': 'id_item_name'}),  
            'item_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Code'}),  
           
            
            'barcode_code': forms.TextInput(attrs={
                'placeholder': 'Barcode',
                'class': 'form-control'
            }),
            
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Quantity',
                'class': 'form-control'
            }),
            'purchase_rate': forms.NumberInput(attrs={
                'placeholder': 'Purchase Rate',
                'class': 'form-control'
            }),
            'item_net_amount': forms.NumberInput(attrs={
                'placeholder': 'Net Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'tax': forms.NumberInput(attrs={
                'placeholder': 'Tax (%)',
                'class': 'form-control'
            }),
            'item_tax_amount': forms.NumberInput(attrs={
                'placeholder': 'Tax Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'free_quantity': forms.NumberInput(attrs={
                'placeholder': 'Free Quantity',
                'class': 'form-control'
            }),
            'MFD': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Manufacture Date',
                'class': 'form-control',
                'id': 'id_MFD'
            }),
            'EXP': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Expire Date',
                'class': 'form-control',
                'id': 'id_EXP'
            }),
            'sales_rate': forms.NumberInput(attrs={
                'placeholder': 'Sales Rate',
                'class': 'form-control'
            }),
            'profit': forms.NumberInput(attrs={
                'placeholder': 'Profit',
                'class': 'form-control',
                'readonly': True
            }),
            'item_total_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'Batch': forms.Select(attrs={
                'class': 'form-control', 'id': 'id_Batch'
            }),
            
            
        }
        labels = {
            'item_code': 'Item Code',
            'item_name': 'Item Name',
            'barcode_code': 'Barcode',
            'quantity': 'Quantity',
            'purchase_rate': 'Purchase Rate',
            'item_net_amount': 'Net Amount',
            'tax': 'Tax (%)',
            'item_tax_amount': 'Tax Amount',
            'unit': 'Unit',
            'free_quantity': 'Free Quantity',
            'MFD': 'MFD',
            'EXP': 'EXP',
            'sales_rate': 'Sales Rate',
            'profit': 'Profit',
            'item_total_amount': 'Total Amount',
            'Batch': 'Batch',
            
        }  
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields not required
        self.fields['item_code'].required = False
        self.fields['barcode_code'].required = False
        self.fields['MFD'].required = False
        self.fields['EXP'].required = False
        self.fields['Batch'].required = False
        self.fields['free_quantity'].required = False
        self.fields['Cost'].required = False
        
        # Set default values for numeric fields
        if not self.instance.pk:  # New form
            self.fields['quantity'].initial = 1
            self.fields['purchase_rate'].initial = 0.00
            self.fields['item_net_amount'].initial = 0.00
            self.fields['tax'].initial = 0.00
            self.fields['item_tax_amount'].initial = 0.00
            self.fields['sales_rate'].initial = 0.00
            self.fields['profit'].initial = 0.00
            self.fields['item_total_amount'].initial = 0.00
            self.fields['free_quantity'].initial = 0
            self.fields['Cost'].initial = 0.00


# Create the formset for PurchaseVoucherItem with proper validation
PurchaseReturnVoucherItemFormSet = inlineformset_factory(
    PurchaseReturnMaster,
    PurchaseReturnDetail,
    form=PurchaseReturnVoucherItemForm,
    extra=0,  # Don't show extra empty forms
    can_delete=True,
    min_num=1,  # Require at least one item
    validate_min=True,  # Validate minimum requirement
    fields=[
        'item_name', 'item_code', 'barcode_code', 'quantity', 
        'purchase_rate', 'item_net_amount', 'tax', 'item_tax_amount', 
        'unit', 'free_quantity', 'MFD', 'EXP', 'sales_rate', 
        'profit', 'item_total_amount', 'Batch', 'Cost'
    ]
)


# Custom validation for the formset
class CustomPurchaseReturnVoucherItemFormSet(PurchaseReturnVoucherItemFormSet):
    def clean(self):
        """Add custom validation to the formset"""
        if any(self.errors):
            return
            
        # Check that at least one item exists and is not deleted
        valid_forms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                valid_forms += 1
                
                # Validate required fields for non-deleted forms
                if not form.cleaned_data.get('item_name'):
                    raise forms.ValidationError("Each item must have an item name selected.")
                if not form.cleaned_data.get('quantity') or form.cleaned_data.get('quantity') <= 0:
                    raise forms.ValidationError("Each item must have a valid quantity greater than 0.")
                if not form.cleaned_data.get('purchase_rate') or form.cleaned_data.get('purchase_rate') <= 0:
                    raise forms.ValidationError("Each item must have a valid purchase rate greater than 0.")
        
        if valid_forms == 0:
            raise forms.ValidationError("At least one item is required for the purchase voucher.")

# Use the custom formset
PurchaseReturnVoucherItemFormSet = CustomPurchaseReturnVoucherItemFormSet    






class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_name', 'customer_mobile', 'customer_phone', 'customer_email', 
            'customer_address_1', 'customer_address_2', 'customer_country', 'customer_state', 
            'customer_city', 'customer_zipcode', 'customer_website', 'customer_description', 
            'customer_VAT', 'customer_TRN_or_CRN'
        ]
        
        labels = {
            'customer_name': 'customer Name',
            'customer_mobile': 'Mobile',
            'customer_phone': 'Phone',
            'customer_email': 'customer Email',
            'customer_address_1': 'Address Line 1',
            'customer_address_2': 'Address Line 2',
            'customer_country': 'Country',
            'customer_state': 'State',
            'customervendor_city': 'City',
            'customer_zipcode': 'Zipcode',
            'customer_website': 'Website',
            'customer_description': 'Description',
            'customer_VAT': 'VAT Number',
            'customer_TRN_or_CRN': 'TRN/CRN Number',
        }
        
        widgets = {
            'customer_name': forms.TextInput(attrs={'placeholder': 'Enter customer name'}),
            'customer_mobile': forms.TextInput(attrs={'placeholder': 'Enter mobile number'}),
            'customer_phone': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'customer_email': forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
            'customer_address_1': forms.Textarea(attrs={'placeholder': 'Enter address line 1', 'rows': 2}),
            'customer_address_2': forms.Textarea(attrs={'placeholder': 'Enter address line 2', 'rows': 2}),
            'customer_country': forms.TextInput(attrs={'placeholder': 'Enter country'}),
            'customer_state': forms.TextInput(attrs={'placeholder': 'Enter state'}),
            'customer_city': forms.TextInput(attrs={'placeholder': 'Enter city'}),
            'customer_zipcode': forms.TextInput(attrs={'placeholder': 'Enter zipcode'}),
            'customer_website': forms.URLInput(attrs={'placeholder': 'Enter customer website'}),
            'customer_description': forms.Textarea(attrs={'placeholder': 'Enter customer description', 'rows': 4}),
            'customer_VAT': forms.TextInput(attrs={'placeholder': 'Enter VAT number'}),
            'customer_TRN_or_CRN': forms.TextInput(attrs={'placeholder': 'Enter TRN or CRN number'}),
        }   

class SalesVoucherForm(forms.ModelForm):
    class Meta:
        model = SalesMaster
        fields = [
            'voucher_no',
            'voucherType',
            'transaction_date',
            'ledger',
            'payment_mode',
            'InvoiceNo',
            'InvoiceDate',
            'PO_number',
            'DO_number',
            'mobile',
            'customer_TRN',
            'vehicle_number',
            'location',
            'terms_and_conditions',
            'remarks',
            'total_net_value',
            'total_tax_amount',
            'discount',
            'grand_total_amount',
            'cost_center',
            'lrNo',
            'transportCompany',
            'Freight',
        ]
        labels = {
            'voucher_no': 'Voucher Number',
            'transaction_date': 'Transaction Date',
            'ledger': 'Ledger',
            'payment_mode': 'Payment Mode',
            'InvoiceNo': 'Invoice No',
            'InvoiceDate': 'Invoice Date',
            'PO_number': 'PO Number',
            'DO_number': 'DO Number',
            'mobile': 'Mobile Number',
            'customer_TRN': 'Customer TRN',
            'vehicle_number': 'Vehicle Number',
            'location': 'Location',
            'terms_and_conditions': 'Terms and Conditions',
            'remarks': 'Remarks',
            'total_net_value': 'Total Net Value',
            'total_tax_amount': 'Total Tax Amount',
            'discount': 'Discount',
            'grand_total_amount': 'Grand Total Amount',
            'cost_center': 'Cost Center',
            'lrNo': 'LR No',
            'transportCompany': 'Transport ',
            'Freight': 'Freight ',
        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'placeholder': 'Enter voucher No', 'readonly': True, 'id': 'id_voucher_no',}),
            'payment_mode': forms.Select(),
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
            'InvoiceDate': forms.DateInput(attrs={'type': 'date'}),
            'ledger': forms.Select(),
            'InvoiceNo': forms.TextInput(attrs={'placeholder': 'Enter invoice number'}),
            'PO_number': forms.TextInput(),
            'DO_number': forms.TextInput(),
            'mobile': forms.TextInput(),
            'customer_TRN': forms.TextInput(),
            'vehicle_number': forms.TextInput(),
            'location': forms.TextInput(),
            'terms_and_conditions': forms.TextInput(),
            'remarks': forms.TextInput(),
            'total_net_value': forms.NumberInput(attrs={'readonly': True}),
            'total_tax_amount': forms.NumberInput(attrs={'readonly': True}),
            'discount': forms.NumberInput(),
            'grand_total_amount': forms.NumberInput(attrs={'readonly': True}),
            'cost_center': forms.Select(),
            'lrNo': forms.TextInput(),
            'transportCompany': forms.TextInput(),
            'Freight': forms.NumberInput(),
            'voucherType': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_voucherType',
                'onchange': 'updateVoucherNumber()'
            })
        }
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass
        
        # Ledger filter by Groups cash account & sundry Sundry Debtors
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(8, 29)

        # Voucher type filter 
        filter_voucher_types(self, [2])    
            
    
        
    
        
        
class SalesVoucherItemForm(forms.ModelForm):
    class Meta:
        model = SalesDetail
        fields = [
            'item_name',
            'item_code',
            'barcode_code',
            'quantity',
            'unit',
            'sales_rate',
            'item_net_amount',
            'tax',
            'item_tax_amount',
            'item_total_amount',
            'Batch',
            'MFD',
            'EXP',
            
        ]
        labels = {
            'item_name': 'Item Name',
            'item_code': 'Item Code',
            'barcode_code': 'Barcode',
            'quantity': 'Quantity',
            'unit': 'Unit',
            'sales_rate': 'Sales Rate',
            'item_net_amount': 'Net Amount',
            'tax': 'Tax (%)',
            'item_tax_amount': 'Tax Amount',
            'item_total_amount': 'Total Amount',
            'Batch': 'Batch',
            'MFD': 'Manufacture Date',
            'EXP': 'Expiry Date',
            'QtyInBaseUnit': 'Qty (Base Unit)',
            'RateInBaseUnit': 'Rate (Base Unit)',
            'BaseUnit': 'Base Unit Name',
        }
        widgets = {
            'item_name': forms.Select(),
            'item_code': forms.TextInput(),
            'barcode_code': forms.TextInput(),
            'quantity': forms.NumberInput(),
            'unit': forms.Select(),
            'sales_rate': forms.NumberInput(),
            'item_net_amount': forms.NumberInput(attrs={'readonly': True}),
            'tax': forms.NumberInput(),
            'item_tax_amount': forms.NumberInput(attrs={'readonly': True}),
            'item_total_amount': forms.NumberInput(attrs={'readonly': True}),
            'Batch': forms.Select(),
            'MFD': forms.DateInput(attrs={'type': 'date'}),
            'EXP': forms.DateInput(attrs={'type': 'date'}),
            
        }

SalesVoucherItemFormSet = inlineformset_factory(
    SalesMaster,                # parent model
    SalesDetail,               # child model
    form=SalesVoucherItemForm, # your custom form
    extra=1,
    can_delete=True
)

class SalesReturnVoucherForm(forms.ModelForm):
    class Meta:
        model = SalesReturnMaster
        fields = [
            'voucher_no',
            'voucherType',
            'transaction_date',
            'ledger',
            'payment_mode',
            'InvoiceNo',
            'InvoiceDate',
            'PO_number',
            'DO_number',
            'mobile',
            'customer_TRN',
            'vehicle_number',
            'location',
            'terms_and_conditions',
            'remarks',
            'total_net_value',
            'total_tax_amount',
            'discount',
            'grand_total_amount',
            'cost_center',
            'lrNo',
            'transportCompany',
            'Freight',
        ]
        labels = {
            'voucher_no': 'Voucher Number',
            'transaction_date': 'Transaction Date',
            'ledger': 'Ledger',
            'payment_mode': 'Payment Mode',
            'InvoiceNo': 'Invoice No',
            'InvoiceDate': 'Invoice Date',
            'PO_number': 'PO Number',
            'DO_number': 'DO Number',
            'mobile': 'Mobile Number',
            'customer_TRN': 'Customer TRN',
            'vehicle_number': 'Vehicle Number',
            'location': 'Location',
            'terms_and_conditions': 'Terms and Conditions',
            'remarks': 'Remarks',
            'total_net_value': 'Total Net Value',
            'total_tax_amount': 'Total Tax Amount',
            'discount': 'Discount',
            'grand_total_amount': 'Grand Total Amount',
            'cost_center': 'Cost Center',
            'lrNo': 'LR No',
            'transportCompany': 'Transport ',
            'Freight': 'Freight ',
        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'placeholder': 'Enter voucher No', 'readonly': True, 'id': 'id_voucher_no',}),
            'payment_mode': forms.Select(),
            'transaction_date': forms.DateInput(attrs={'type': 'date'}),
            'InvoiceDate': forms.DateInput(attrs={'type': 'date'}),
            'ledger': forms.Select(),
            'InvoiceNo': forms.TextInput(attrs={'placeholder': 'Enter invoice number'}),
            'PO_number': forms.TextInput(),
            'DO_number': forms.TextInput(),
            'mobile': forms.TextInput(),
            'customer_TRN': forms.TextInput(),
            'vehicle_number': forms.TextInput(),
            'location': forms.TextInput(),
            'terms_and_conditions': forms.TextInput(),
            'remarks': forms.TextInput(),
            'total_net_value': forms.NumberInput(attrs={'readonly': True}),
            'total_tax_amount': forms.NumberInput(attrs={'readonly': True}),
            'discount': forms.NumberInput(),
            'grand_total_amount': forms.NumberInput(attrs={'readonly': True}),
            'cost_center': forms.Select(),
            'lrNo': forms.TextInput(),
            'transportCompany': forms.TextInput(),
            'Freight': forms.NumberInput(),
            'voucherType': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_voucherType',
                'onchange': 'updateVoucherNumber()'
            })
        }
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass
        
        # Ledger filter by Groups cash account & sundry Sundry Debtors
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(8, 29)

        # Voucher type filter 
        filter_voucher_types(self, [4])    
            
    
        
    
        
        
class SalesReturnVoucherItemForm(forms.ModelForm):
    class Meta:
        model = SalesReturnDetail
        fields = [
            'item_name',
            'item_code',
            'barcode_code',
            'quantity',
            'unit',
            'sales_rate',
            'item_net_amount',
            'tax',
            'item_tax_amount',
            'item_total_amount',
            'Batch',
            'MFD',
            'EXP',
            
        ]
        labels = {
            'item_name': 'Item Name',
            'item_code': 'Item Code',
            'barcode_code': 'Barcode',
            'quantity': 'Quantity',
            'unit': 'Unit',
            'sales_rate': 'Sales Rate',
            'item_net_amount': 'Net Amount',
            'tax': 'Tax (%)',
            'item_tax_amount': 'Tax Amount',
            'item_total_amount': 'Total Amount',
            'Batch': 'Batch',
            'MFD': 'Manufacture Date',
            'EXP': 'Expiry Date',
            'QtyInBaseUnit': 'Qty (Base Unit)',
            'RateInBaseUnit': 'Rate (Base Unit)',
            'BaseUnit': 'Base Unit Name',
        }
        widgets = {
            'item_name': forms.Select(),
            'item_code': forms.TextInput(),
            'barcode_code': forms.TextInput(),
            'quantity': forms.NumberInput(),
            'unit': forms.Select(),
            'sales_rate': forms.NumberInput(),
            'item_net_amount': forms.NumberInput(attrs={'readonly': True}),
            'tax': forms.NumberInput(),
            'item_tax_amount': forms.NumberInput(attrs={'readonly': True}),
            'item_total_amount': forms.NumberInput(attrs={'readonly': True}),
            'Batch': forms.Select(),
            'MFD': forms.DateInput(attrs={'type': 'date'}),
            'EXP': forms.DateInput(attrs={'type': 'date'}),
            
        }

SalesReturnVoucherItemFormSet = inlineformset_factory(
    SalesReturnMaster,                # parent model
    SalesReturnDetail,               # child model
    form=SalesReturnVoucherItemForm, # your custom form
    extra=1,
    can_delete=True
)



class BillSettlementForm(forms.ModelForm):
    class Meta:
        model = BillByBill
        fields = ['settle_amount']
        
class CostCenterForm(forms.ModelForm):
    class Meta:
        model = CostCenter
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Cost Center Name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Cost Center Code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Description'}),
        }        
        
class OpeningStockForm(forms.ModelForm):
    class Meta:
        model = OpeningStockMaster
        fields = [
            'auto_no',  # Include auto_no in the fields
            'voucher_no',
            'transaction_date',
            'ledger',
            'payment_mode',
            'remarks',
            'total_net_value',
            'total_tax_amount',
            'discount',
            'payment_terms',
            'grand_total_amount',
            'cost_center',
        ]
        widgets = {
            'auto_no': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True  # Make the field read-only
            }),
            'voucher_no': forms.TextInput(attrs={
                'placeholder': 'Voucher No',
                'class': 'form-control'
            }),
            'transaction_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Transaction Date',
                'class': 'form-control'
            }),
            'ledger': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control'
            }),
            'remarks': forms.TextInput(attrs={
                'placeholder': 'Remarks (optional)',
                'class': 'form-control',
                'rows': 3
            }),
            'total_net_value': forms.NumberInput(attrs={
                'placeholder': 'Total Net Value',
                'class': 'form-control',
                'readonly': True
            }),
            'total_tax_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Tax Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'discount': forms.NumberInput(attrs={
                'placeholder': 'Discount (if any)',
                'class': 'form-control'
            }),
            'payment_terms': forms.TextInput(attrs={
                'placeholder': 'Payment Terms (optional)',
                'class': 'form-control',
                'rows': 3
            }),
            'grand_total_amount': forms.NumberInput(attrs={
                'placeholder': 'Grand Total Amount',
                'class': 'form-control', 
                'readonly': True
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'auto_no': 'Auto Number',
            'voucher_no': 'Voucher Number',
            'transaction_date': 'Transaction Date',
            'ledger': 'Ledger',
            'payment_mode': 'Payment Mode',
            'remarks': 'Remarks',
            'total_net_value': 'Total Net Value',
            'total_tax_amount': 'Total Tax Amount',
            'discount': 'Discount',
            'payment_terms': 'Payment Terms',
            'grand_total_amount': 'Grand Total Amount',
            'cost_center': 'Cost Center',
        }

class OpeningStockItemForm(forms.ModelForm):
    
    
    class Meta:
        model = OpeningStockDetail
        fields = ['item_name','item_code', 'barcode_code', 'quantity', 'purchase_rate', 'item_net_amount', 'tax', 'item_tax_amount', 'unit', 'free_quantity', 'manufacture_date', 'expire_date', 'sales_rate', 'profit', 'item_total_amount']
        widgets = {
            
            'item_name': forms.Select(attrs={'class': 'form-control'}),  
            'item_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item Code'}),  
           
            
            'barcode_code': forms.TextInput(attrs={
                'placeholder': 'Barcode',
                'class': 'form-control'
            }),
            
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Quantity',
                'class': 'form-control'
            }),
            'purchase_rate': forms.NumberInput(attrs={
                'placeholder': 'Purchase Rate',
                'class': 'form-control'
            }),
            'item_net_amount': forms.NumberInput(attrs={
                'placeholder': 'Net Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'tax': forms.NumberInput(attrs={
                'placeholder': 'Tax (%)',
                'class': 'form-control'
            }),
            'item_tax_amount': forms.NumberInput(attrs={
                'placeholder': 'Tax Amount',
                'class': 'form-control',
                'readonly': True
            }),
            'unit': forms.Select(attrs={
                'class': 'form-control'
            }),
            'free_quantity': forms.NumberInput(attrs={
                'placeholder': 'Free Quantity',
                'class': 'form-control'
            }),
            'manufacture_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Manufacture Date',
                'class': 'form-control'
            }),
            'expire_date': forms.DateInput(attrs={
                'type': 'date',
                'placeholder': 'Expire Date',
                'class': 'form-control'
            }),
            'sales_rate': forms.NumberInput(attrs={
                'placeholder': 'Sales Rate',
                'class': 'form-control'
            }),
            'profit': forms.NumberInput(attrs={
                'placeholder': 'Profit',
                'class': 'form-control',
                'readonly': True
            }),
            'item_total_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Amount',
                'class': 'form-control',
                'readonly': True
            }),
        }
        labels = {
            'item_code': 'Item Code',
            'item_name': 'Item Name',
            'barcode_code': 'Barcode',
            'quantity': 'Quantity',
            'purchase_rate': 'Purchase Rate',
            'item_net_amount': 'Net Amount',
            'tax': 'Tax (%)',
            'item_tax_amount': 'Tax Amount',
            'unit': 'Unit',
            'free_quantity': 'Free Quantity',
            'manufacture_date': 'Manufacture Date',
            'expire_date': 'Expire Date',
            'sales_rate': 'Sales Rate',
            'profit': 'Profit',
            'item_total_amount': 'Total Amount',
        }  




class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['BatchNo', 'Item', 'Mfd', 'Exp', 'IsActive', 'barcode_code']
        widgets = {
            'BatchNo': forms.TextInput(attrs={'class': 'form-control'}),
            'Item': forms.Select(attrs={'class': 'form-control'}),
            'Mfd': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'Exp': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'IsActive': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'barcode_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'BatchNo': 'Batch Number',
            'Item': 'Item',
            'Mfd': 'Manufacturing Date',
            'Exp': 'Expiry Date',
            'IsActive': 'Is Active',
            'barcode_code': 'Barcode ',
        }   
        
        
    def clean(self):
        cleaned_data = super().clean()
        batch_no = cleaned_data.get('BatchNo')
        item = cleaned_data.get('Item')
        
        if batch_no and item:
            # Check if this batch number already exists for this item
            queryset = Batch.objects.filter(BatchNo=batch_no, Item=item)
            
            # If updating an existing instance, exclude it from the check
            if self.instance and self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
                
            if queryset.exists():
                raise forms.ValidationError(
                    f"A batch with number '{batch_no}' already exists for this item."
                )
        return cleaned_data           
        
class VouchersForm(forms.ModelForm):
    class Meta:
        model = Vouchers
        fields = ['VoucherType', 'VoucherName', 'Prefix', 'Suffix', 'MinLength', 'StartingNo', 'ledger']
        labels = {
            'VoucherType': 'Voucher Type',
            'VoucherName': 'Voucher Name',
            'Prefix': 'Prefix',
            'Suffix': 'Suffix',
            'MinLength': 'Minimum Length',
            'StartingNo': 'Starting Number',
            'ledger': 'Ledger',
        }
        widgets = {
            'VoucherType': forms.TextInput(attrs={'class': 'form-control'}),
            'VoucherName': forms.TextInput(attrs={'class': 'form-control'}),
            'Prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'Suffix': forms.TextInput(attrs={'class': 'form-control'}),
            'MinLength': forms.NumberInput(attrs={'class': 'form-control'}),
            'StartingNo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ledger': forms.Select(attrs={'class': 'form-control'}),
        }        
        
class StockTransferForm(forms.ModelForm):
    class Meta:
        model = StockTransfer
        fields = ['voucher_no', 'source_cost_center', 'destination_cost_center', 'remarks', 'voucherType']
        
        labels = {
            'voucher_no': 'Invoice No',
            'source_cost_center': 'Source ',
            'destination_cost_center': 'Destination ',
            'remarks': 'Remarks',
        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control'}),
            'source_cost_center': forms.Select(attrs={'class': 'form-control'}),
            'destination_cost_center': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'voucherType': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_voucherType',
                'onchange': 'updateVoucherNumber()'
            }),
            
            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['voucher_no'].required = False

        # ✅ Only for NEW instance (creation)
        if not self.instance.pk:
            if 'voucherType' in self.data:   # POST create
                try:
                    voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                    self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
                except Vouchers.DoesNotExist:
                    pass
            elif self.initial.get('voucherType'):  # GET create
                try:
                    voucher_type = self.initial['voucherType']
                    self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
                except Exception:
                    pass
        else:
            # ✅ Editing: always use instance value
            self.fields['voucher_no'].initial = self.instance.voucher_no

            
        

        # Voucher type filter 
        filter_voucher_types(self, [2])     
        
        
        
        
    

class StockTransferItemForm(forms.ModelForm):
    class Meta:
        model = StockTransferItem
        fields = ['item', 'unit', 'batch', 'quantity', 'rate']
    
    labels = {
        'item': 'Item',
        'unit': 'Unit',
        'batch': 'Batch',
        'quantity': 'Quantity',
        'rate': 'Rate',
    }    
    
    