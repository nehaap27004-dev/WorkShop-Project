from django import forms
from django.utils.translation import gettext_lazy as _
from .models import *

'''class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file_path', 'staff', 'vehicle', 'status', 'expiry_date', 'reminder_date']
        labels = {
            'title': _('Title'),
            'description': _('Description'),
            'file_path': _('File'),
            'staff': _('Staff'),
            'vehicle': _('Vehicle'),
            'status': _('Status'),
            'expiry_date': _('Expiry Date'),
            'reminder_date': _('Reminder Date'),
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'file_path': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reminder_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }'''

class SkillTagForm(forms.ModelForm):
    class Meta:
        model = SkillTag
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': _('Skill Name'),
            'description': _('Description'),
            'is_active': _('Is Active'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('e.g. AC Diagnostics')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Enter skill description...')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
# jobcard_app/forms.py  -- INVOICE SECTION
# Your template renders every field by hand (name="customer", name="payment_mode", ...),
# so these forms are NOT rendered in the HTML. _save_invoice() uses InvoiceHeaderForm to
# validate/clean the header POST data, which keeps the template UI exactly as it is.
from decimal import Decimal, InvalidOperation

from django import forms
from django.utils import timezone

from .models import Invoice


class InvoiceHeaderForm(forms.ModelForm):
    """Validates the invoice header block (not the line items)."""

    invoice_number = forms.CharField(max_length=20, required=False)   # optional, manual
    voucher_number = forms.CharField(max_length=50, required=False)   # server-assigned
    invoice_date   = forms.DateField(required=False)
    discount_pct   = forms.DecimalField(required=False, min_value=0, max_value=100, decimal_places=2)
    amount_paid    = forms.DecimalField(required=False, min_value=0, decimal_places=3)

    class Meta:
        model = Invoice
        fields = [
            'customer', 'voucher_number', 'invoice_number', 'invoice_date', 'due_date',
            'status', 'payment_mode', 'customer_mobile', 'customer_address',
            'discount_pct', 'amount_paid', 'notes',
        ]

    def clean_invoice_number(self):
        num = (self.cleaned_data.get('invoice_number') or '').strip()
        if not num:
            return None                      # blank -> NULL, so many invoices can have no number
        dup = Invoice.objects.filter(invoice_number=num)
        if self.instance.pk:
            dup = dup.exclude(pk=self.instance.pk)
        if dup.exists():
            raise forms.ValidationError(
                f'Invoice number "{num}" is already in use. Please choose a different number.')
        return num

    def clean_invoice_date(self):
        return self.cleaned_data.get('invoice_date') or timezone.now().date()

    def clean_discount_pct(self):
        return self.cleaned_data.get('discount_pct') or Decimal('0')

    def clean_amount_paid(self):
        return self.cleaned_data.get('amount_paid') or Decimal('0')

    def clean_payment_mode(self):
        return (self.cleaned_data.get('payment_mode') or 'cash').lower()