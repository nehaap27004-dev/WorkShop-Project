from django import forms
from django.utils.translation import gettext_lazy as _

from fleet_app.common import filter_voucher_types , get_ledgers_by_group_ids
from .models import *
from django.forms import inlineformset_factory
from django.forms import modelformset_factory
from django.contrib.auth.forms import UserCreationForm

from django import forms
from .models import LedgerCreation

class SimpleCustomerForm(forms.ModelForm):

    class Meta:
        model = LedgerCreation
        fields = [
            'ledger_name',
            'mobile',
            'email',
            'address1'
        ]

class MainGroupForm(forms.ModelForm):
    class Meta:
        model = MainGroup
        fields = ['main_group_name', 'nature_of_group', 'main_group_description']
        widgets = {
            'main_group_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'Main Group Name'}),
            'nature_of_group': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Nature of Group'}),
            'main_group_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Main Group Description'}),
        }
        
# Group Form
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['group_name', 'main_group', 'group_description']
        widgets = {
            'group_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'Group Name'}),
            'main_group': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Under'}),
            'group_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Group Description'}),
        }
        
        labels = {
            'sub_group_name': 'Group Name',
            'main_group' : 'Main Group',
            'sub_group_description': 'Group Description',
        }

# Subgroup Form
class SubgroupForm(forms.ModelForm):
    class Meta:
        model = Subgroup
        fields = ['sub_group_name', 'sub_group_description']
        widgets = {
            'sub_group_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'SubGroup Name'}),
            'sub_group_description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SubGroup Description'}),
        }
        
        labels = {
            'sub_group_name': 'SubGroup Name',
            'sub_group_description': 'SubGroup Description',
        }

# LedgerCreation Form
class LedgerCreationForm(forms.ModelForm):
    class Meta:
        model = LedgerCreation
        fields = ['ledger_name', 'groups', 'sub_group', 'opening_balance', 'types', 'remark', 'trn_number',]
        widgets = {
            'ledger_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'Ledger Name'}),
            'groups': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Under'}),
            'sub_group': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Under'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'types': forms.Select(attrs={'class': 'form-control'}),
            'remark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Remark'}),
            'trn_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transaction Number'}),
        }
        
        labels = {
            'ledger_name': _('Ledger Name'),
            'groups': _('Groups'),
            'sub_group': _('Sub Group'),
            'opening_balance': _('Opening Balance'),
            'types': _('Type'),
            'remark': _('Remark'),
            'trn_number': _('TRN No'),
        }
        
class CustomerForm(forms.ModelForm):
    class Meta:
        model = LedgerCreation
        fields = [
            'ledger_name', 'opening_balance', 'remark', 'trn_number',
            'email', 'mobile', 'phone_no', 'address1', 'country', 'state',
            'city', 'zipcode', 'description', 'cr_no',
        ]
        widgets = {
            'ledger_name': forms.TextInput(attrs={'class': 'form-control'}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'trn_number': forms.TextInput(attrs={'class': 'form-control'}),
            'cr_no': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'address1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

        labels = {
            'ledger_name': _('Client Name'),
            'opening_balance': _('Opening Balance'),
            'remark': _('Remark'),
            'trn_number': _('VATIN'),
            'cr_no': _('CR No'),
            'email': _('Email'),
            'mobile': _('Mobile'),
            'phone_no': _('Phone No'),
            'address1': _('Address'),
            'country': _('Country'),
            'state': _('State'),
            'city': _('City'),
            'zipcode': _('Zipcode'),
            'description': _('Description'),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.groups_id = 2  # sundry DR - Automatically assign Group ID 
        instance.types = 'DR'    # Always DR
        if commit:
            instance.save()
        return instance        
        

class VendorForm(forms.ModelForm):
    class Meta:
        model = LedgerCreation
        fields = [
            'ledger_name', 'opening_balance', 'remark', 'trn_number',
            'email', 'mobile', 'phone_no', 'address1', 'country', 'state',
            'city', 'zipcode', 'description', 'cr_no',
        ]
        widgets = {
            'ledger_name': forms.TextInput(attrs={'class': 'form-control',}),
            'opening_balance': forms.NumberInput(attrs={'class': 'form-control'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'trn_number': forms.TextInput(attrs={'class': 'form-control'}),
            'cr_no': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'address1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        
        labels = {
            'ledger_name': _('Supplier Name'),
            'opening_balance': _('Opening Balance'),
            'remark': _('Remark'),
            'trn_number': _('VATIN'),
            'cr_no': _('CR No'),
            'email': _('Email'),
            'mobile': _('Mobile'),
            'phone_no': _('Phone No'),
            'address1': _('Address'),
            'country': _('Country'),
            'state': _('VAT No'),
            'city': _('City'),
            'zipcode': _('Zipcode'),
            'description': _('Description'),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.groups_id = 28  # sundry CR - automatically assign group
        instance.types = 'CR'    # Always CR 
        if commit:
            instance.save()
        return instance

class LocalPaymentForm(forms.ModelForm):
    class Meta:
        model = LocalPayment
        fields = ['date', 'voucher_no', 'payment_mode', 'party', 'reference_no',
                 'party_VAT_no', 'remark', 'note', 'taxable_amount', 'VAT_amount', 'net_amount', 'voucherType',  "IsPDC",
                   "ChequeDate", "ChequeNo",]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'voucher_no': forms.TextInput(attrs={'class': 'form-control' , 'readonly': True}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control'}),
            'party_VAT_no': forms.TextInput(attrs={'class': 'form-control'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'taxable_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'VAT_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'net_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'voucherType': forms.HiddenInput(),
            "IsPDC": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ChequeDate": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "ChequeNo": forms.TextInput(attrs={"class": "form-control"}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = fleet_app.Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass
            
        self.fields['payment_mode'].queryset = get_ledgers_by_group_ids(8, 5)    

        # Voucher type filter 
        filter_voucher_types(self, [11])     
        
class LocalPaymentChequeForm(forms.ModelForm):
    class Meta:
        model = LocalPaymentCheque
        fields = ['cheque_no', 'cheque_date', 'issuing_bank_name', 
                 'reference_no', 'cheque_status']
        widgets = {
            'cheque_no': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'issuing_bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_status': forms.Select(attrs={'class': 'form-control'}),
        }        

class LocalPaymentItemForm(forms.ModelForm):
    class Meta:
        model = LocalPaymentItems
        fields = ['invoice_date', 'invoice_no', 'ledger', 'description', 'amount', 'vat_type', 'vat_amount']
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'invoice_no': forms.TextInput(attrs={'class': 'form-control'}),
            'ledger': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_type': forms.Select(attrs={'class': 'form-control'}),
            'vat_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': True}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(12, 16)
                

LocalPaymentItemFormSet = inlineformset_factory(LocalPayment, LocalPaymentItems, form=LocalPaymentItemForm, extra=1)



class ReceiptForm(forms.ModelForm):
    class Meta:
        model = Receipt
        fields = [
            'voucher_no', 'date', 'payment_type',
            'payment_mode', 'reference_no', 'tax_rate',
            'taxable_amount', 'VAT_amount', 'net_amount',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'voucher_no': forms.TextInput(attrs={'placeholder': 'Enter voucher number'}),
            'reference_no': forms.TextInput(attrs={'placeholder': 'Optional'}),
        }


class ReceiptItemForm(forms.ModelForm):
    class Meta:
        model = ReceiptItems
        fields = ['ledger', 'description', 'amount']
        widgets = {
            
            'ledger': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

ReceiptItemFormSet = modelformset_factory(
    ReceiptItems,
    form=ReceiptItemForm,
    extra=1,
    can_delete=True,
)

class ReceiptChequeForm(forms.ModelForm):
    class Meta:
        model = ReceiptCheque
        fields = [
            'cheque_no', 'cheque_date', 'issuing_bank_name',
            'reference_no', 'cheque_status',
        ]
        widgets = {
            'cheque_date': forms.DateInput(attrs={'type': 'date'}),
            'cheque_no': forms.TextInput(attrs={'placeholder': 'Enter cheque number'}),
            'issuing_bank_name': forms.TextInput(attrs={'placeholder': 'Bank name'}),
            'reference_no': forms.TextInput(attrs={'placeholder': 'Optional'}),
        }


class ContraForm(forms.ModelForm):
    class Meta:
        model = Contra
        fields = [
            'date',
            'voucher_no',
            'contra_type',
            'dr_ledger',
            'cr_ledger',
            'cheque_no',
            'cheque_date',
            'amount',
            'remark',
        ]
        labels = {
            'date': 'Date',
            'voucher_no': 'Voucher Number',
            'contra_type': 'Contra Type',
            'dr_ledger': 'Debit Ledger',
            'cr_ledger': 'Credit Ledger',
            'cheque_no': 'Cheque Number',
            'cheque_date': 'Cheque Date',
            'amount': 'Amount',
            'remark': 'Remark',
        }
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Voucher Number'}),
            'contra_type': forms.Select(attrs={'class': 'form-control'}),
            'dr_ledger': forms.Select(attrs={'class': 'form-control'}),
            'cr_ledger': forms.Select(attrs={'class': 'form-control'}),
            'cheque_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Cheque Number'}),
            'cheque_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Amount'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter Remark', 'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define acceptable group names for Cash in Hand and Bank Accounts
        cash_bank_groups = GroupUnder.objects.filter(under_name__in=["Cash in Hand", "Bank Accounts"])
        
        # Filter the LedgerCreation queryset to only include these groups
        self.fields["dr_ledger"].queryset = LedgerCreation.objects.filter(group_under__in=cash_bank_groups)
        self.fields["cr_ledger"].queryset = LedgerCreation.objects.filter(group_under__in=cash_bank_groups) 
        

class JournalForm(forms.ModelForm):
    class Meta:
        model = Journal
        fields = ['date', 'voucher_no', 'dr_ledger', 'cr_ledger', 'due_date', 'amount', 'narration']
        labels = {
            'date': 'Date',
            'voucher_no': 'Voucher Number',
            'dr_ledger': 'Debit Ledger',
            'cr_ledger': 'Credit Ledger',
            'due_date': 'Due Date',
            'amount': 'Amount',
            'narration': 'Narration',
        }
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'voucher_no': forms.TextInput(attrs={'class': 'form-control'}),
            'dr_ledger': forms.Select(attrs={'class': 'form-control'}),
            'cr_ledger': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'narration': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude "Cash in Hand" and "Bank Accounts" from group_under
        excluded_groups = GroupUnder.objects.filter(under_name__in=["Cash in Hand", "Bank Accounts"])
        self.fields['dr_ledger'].queryset = LedgerCreation.objects.exclude(group_under__in=excluded_groups)
        self.fields['cr_ledger'].queryset = LedgerCreation.objects.exclude(group_under__in=excluded_groups)
        
class GroupsForm(forms.ModelForm):
    class Meta:
        model = Groups
        fields = ['groupName', 'group_desc', 'groupId', 'isDefault']
        widgets = {
            'groupName': forms.TextInput(attrs={'class': 'form-control'}),
            'group_desc': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'groupId': forms.Select(attrs={'class': 'form-control'}),
            'isDefault': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'groupName': ' Name',
            'group_desc': 'Description',
            'groupId': 'Parent Group',
            'isDefault': ' Default',
        }
        
class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserRole
        fields = ['name', 'is_admin']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter role name'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }    
        
        labels = {
            'name': ' Name',
            'is_admin': ' Admin',
        }  
        
class CustomUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'phone', 'address', 'place', 'user_role',
            'password1', 'password2'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'place': forms.TextInput(attrs={'class': 'form-control'}),
            'user_role': forms.Select(attrs={'class': 'form-control'}),
        }        
        
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'username': 'Username',
            'email': 'Email',
            'phone': 'Phone',
            'address': 'Address',
            'place': 'Place',
            'user_role': 'User Role',
            'password1': 'Password',
            'password2': 'Confirm Password',
        }  
        
class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['name', 'url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Menu Name'}),
            'url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL'}),
        }        
        
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            "PaymentNo",
            "Date",
            "LedgerDr",
            "voucherType",
            "voucher_no",
            "PaymentMode",
            "LedgerCr",
            "PaymentType",
            "BankTransferID",
            "IsPDC",
            "Cleared",
            "ChequeNo",
            "ChequeDate",
            "Remarks",
            
        ]
        widgets = {
            "voucher_no": forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            "Date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "IsPDC": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "Cleared": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ChequeDate": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "Remarks": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["LedgerDr"].queryset = LedgerCreation.objects.all()
        self.fields["LedgerCr"].queryset = LedgerCreation.objects.all()
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"  
            
    
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = fleet_app.Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass

        # Voucher type filter 
        filter_voucher_types(self, [2])          
        
class ReceiptBillMasterForm(forms.ModelForm):
    class Meta:
        model = ReceiptBillMaster
        fields = ['Date', 'Customer', 'Ledger', 'Remark', 'TrnNo', 'IsPDC', 'ChequeNo', 'ChequeDate', 'ChequeStatus']
        widgets = {
            
            'Date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'Customer': forms.Select(attrs={'class': 'form-control', 'id': 'id_customer'}),
            'Ledger': forms.Select(attrs={'class': 'form-control'}),
            'Remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'TrnNo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'IsPDC': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ChequeNo': forms.TextInput(attrs={'class': 'form-control'}),
            'ChequeDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ChequeStatus': forms.Select(attrs={'class': 'form-control'}),
        }
    
        labels = {
            'Date': 'Date',
            'Customer': 'Customer',
            'Ledger': 'Ledger',
            'Remark': 'Remark',
            'TrnNo': 'TR No',
            'IsPDC': 'Is PDC',
            'ChequeNo': 'Cheque No',
            'ChequeDate': 'Cheque Date',
            'ChequeStatus': 'Cheque Status',
        }    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    # Ledger filter by Groups cash account & sundry Sundry Creditors 
        self.fields['Ledger'].queryset = get_ledgers_by_group_ids(8, 5)    
        self.fields['Customer'].queryset = get_ledgers_by_group_ids(29)   


class ReceiptBillDetailsForm(forms.ModelForm):
    class Meta:
        model = ReceiptBillDetails
        fields = ['voucherType', 'VoucherNo', 'CurrentAmount', 'Amount']
        widgets = {
            'voucherType': forms.HiddenInput(),
            'VoucherNo': forms.HiddenInput(),
            'CurrentAmount': forms.HiddenInput(),
            'Amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Voucher type filter 
    #     filter_voucher_types(self, [5])    


ReceiptBillDetailsFormSet = inlineformset_factory(
    ReceiptBillMaster, ReceiptBillDetails,
    form=ReceiptBillDetailsForm,
    extra=0,
    can_delete=False
)

class PaymentBillMasterForm(forms.ModelForm):
    class Meta:
        model = PaymentBillMaster
        fields = ['Date', 'Supplier', 'Ledger', 'Remark', 'TrnNo', 'IsPDC', 'ChequeNo', 'ChequeDate', 'ChequeStatus']
        widgets = {
            'Date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'Supplier': forms.Select(attrs={'class': 'form-control', 'id': 'id_supplier'}),
            'Ledger': forms.Select(attrs={'class': 'form-control'}),
            'Remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'TrnNo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'IsPDC': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ChequeNo': forms.TextInput(attrs={'class': 'form-control'}),
            'ChequeDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ChequeStatus': forms.Select(attrs={'class': 'form-control'}),
        }
    
        labels = {
            'Date': 'Date',
            'Supplier': 'Supplier',
            'Ledger': 'Ledger',
            'Remark': 'Remark',
            'TrnNo': 'TR No',
            'IsPDC': 'Is PDC',
            'ChequeNo': 'Cheque No',
            'ChequeDate': 'Cheque Date',
            'ChequeStatus': 'Cheque Status',
        }   
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    # Ledger filter by Groups cash account & sundry Sundry Creditors 
        self.fields['Ledger'].queryset = get_ledgers_by_group_ids(8, 5)    
        self.fields['Supplier'].queryset = get_ledgers_by_group_ids(28)   


class PaymentBillDetailsForm(forms.ModelForm):
    class Meta:
        model = PaymentBillDetails
        fields = ['voucherType', 'VoucherNo', 'Amount']
        widgets = {
            'voucherType': forms.HiddenInput(),
            'VoucherNo': forms.HiddenInput(),
            'Amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     # Voucher type filter 
    #     filter_voucher_types(self, [6])     


PaymentBillDetailsFormSet = inlineformset_factory(
    PaymentBillMaster, PaymentBillDetails,
    form=PaymentBillDetailsForm,
    extra=0,
    can_delete=False
)

class PaymentMasterForm(forms.ModelForm):
    class Meta:
        model = PaymentMaster
        fields = ["voucher_no", "voucherType", "Date", "Ledger", "PaidTo", "IsPDC", 
                  "ChequeDate", "ChequeNo", "TotalAmount"]

        labels = {
            "voucher_no": _("Voucher Number"),
            "Date": _("Date"),
            "Ledger": _("Cash/Bank"),
            "PaidTo": _("Paid To"),
            "IsPDC": _("PDC"),
            "ChequeDate": _("Cheque Date"),
            "ChequeNo": _("Cheque Number"),
            "TotalAmount": _("Total Amount"),
        }

        widgets = {
            "voucher_no": forms.TextInput(attrs={"class": "form-control" , 'readonly': True}),
            "voucherType": forms.HiddenInput(),
            "Date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "Ledger": forms.Select(attrs={"class": "form-control"}),
            "PaidTo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Name / Account"}),
            "IsPDC": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ChequeDate": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "ChequeNo": forms.TextInput(attrs={"class": "form-control"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ledger filter by Groups cash account & Bank account
        self.fields['Ledger'].queryset = get_ledgers_by_group_ids(8, 5)
        # Voucher type filter 
        filter_voucher_types(self, [3])    


class PaymentDetailsForm(forms.ModelForm):
    class Meta:
        model = PaymentDetails
        fields = ["Ledger", "Amount", "Desc", "Vehicle"]

        labels = {
            "Ledger": _("Ledger Account"),
            "Amount": _("Amount"),
            "Desc": _("Description"),
            "Vehicle": _("Vehicle"),
        }

        widgets = {
            "Ledger": forms.Select(attrs={"class": "form-control"}),
            "Amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "Desc": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "Vehicle": forms.Select(attrs={"class": "form-control"}),
        }


# Inline formset for Payment Details
PaymentDetailsFormSet = inlineformset_factory(
    PaymentMaster,
    PaymentDetails,
    form=PaymentDetailsForm,
    extra=1,
    can_delete=True
)

class ReceiptMasterForm(forms.ModelForm):
    class Meta:
        model = ReceiptMaster
        fields = ["voucher_no", "voucherType", "Date", "Ledger", "ReceivedFrom", "IsPDC",
                   "ChequeDate", "ChequeNo" , "TotalAmount"]

        labels = {
            "voucher_no": _("Voucher Number"),
            "Date": _("Date"),
            "Ledger": _("Cash/Bank"),
            "ReceivedFrom": _("Received From"),
            "IsPDC": _("PDC"),
            "ChequeDate": _("Cheque Date"),
            "ChequeNo": _("Cheque Number"),
            "TotalAmount": _("Total Amount"),
        }

        widgets = {
            "voucher_no": forms.TextInput(attrs={"class": "form-control" , 'readonly': True}),
            "voucherType": forms.HiddenInput(),
            "Date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "Ledger": forms.Select(attrs={"class": "form-control"}),
            "ReceivedFrom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Customer / Party Name"}),
            "IsPDC": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ChequeDate": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "ChequeNo": forms.TextInput(attrs={"class": "form-control"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ledger filter by Groups cash account & sundry creditors 
        self.fields['Ledger'].queryset = get_ledgers_by_group_ids(8, 5)

        # Voucher type filter 
        filter_voucher_types(self, [4])       


class ReceiptDetailsForm(forms.ModelForm):
    class Meta:
        model = ReceiptDetails
        fields = ["Ledger", "Amount", "Desc"]

        labels = {
            "Ledger": _("Ledger Account"),
            "Amount": _("Amount"),
            "Desc": _("Description"),
        }

        widgets = {
            "Ledger": forms.Select(attrs={"class": "form-control"}),
            "Amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "Desc": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


# Inline formset for Receipt Details
ReceiptDetailsFormSet = inlineformset_factory(
    ReceiptMaster,
    ReceiptDetails,
    form=ReceiptDetailsForm,
    extra=1,
    can_delete=True
)