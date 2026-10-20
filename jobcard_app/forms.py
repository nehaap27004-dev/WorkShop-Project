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

from django import forms

from .models import WorkshopVehicle
from accounts_app.models import LedgerCreation
from fleet_app.models import VehicleModel, VehicleCategory


# VehicleModel field that links to VehicleCategory
MODEL_CATEGORY_FIELD = "vehicle_category"


def model_queryset():
    """Return vehicle models with their manufacturer and category available."""
    return VehicleModel.objects.select_related(
        "manufacturer",
        "vehicle_category",
    ).order_by("model_name")
class WorkshopVehicleForm(forms.ModelForm):
    class Meta:
        model = WorkshopVehicle
        # FIX: "is_active" removed. It is a checkbox that the page never draws,
        # so every new vehicle was saved as inactive and vanished from the list.
        # wv_create sets is_active = True and wv_delete sets it to False.
        fields = [
            "customer",
            "registration_number",
            "vehicle_model",
            "vehicle_type",
            "fuel_type",
            "odometer",
            "mileage",
            "year",
            "color",
            "chassis_number",
            "engine_number",
            "vehicle_number",
            "status",
            "notes",
            "vehicle_image",
            "registration_date",
            "registration_expiry_date",
            "insurance_policy_number",
            "insurance_expiry_date",
            "last_service_date",
            "next_service_date",
            "service_interval",
        ]

        widgets = {
            "customer": forms.Select(attrs={"class": "form-select"}),
            "registration_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "vehicle_model": forms.Select(
                attrs={"class": "form-select"}
            ),
            "vehicle_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "fuel_type": forms.Select(
                attrs={"class": "form-select"}
            ),
            "odometer": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
            "mileage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "year": forms.NumberInput(
                attrs={"class": "form-control", "min": "1900"}
            ),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "chassis_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "engine_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "vehicle_number": forms.TextInput(
                attrs={"class": "form-control", "required": "required"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "vehicle_image": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),
            "registration_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "registration_expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "insurance_policy_number": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "insurance_expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "last_service_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "next_service_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "service_interval": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FIX: Vehicle Number is required.
        self.fields["vehicle_number"].required = True

        # FIX: status is not drawn on the create page, so it must not be
        # required there (it defaults to 'active').
        if not self.instance.pk:                # create mode only
            self.fields["status"].required = False
            self.fields["status"].initial = "active"

        # Customer selection
        self.fields["customer"].queryset = LedgerCreation.objects.all()

        # Model selection is populated through Select2/AJAX.
        self.fields["vehicle_model"].queryset = model_queryset()
        self.fields["vehicle_model"].required = True

        # The category comes from WorkshopVehicle.vehicle_type.
        self.fields["vehicle_type"].queryset = VehicleCategory.objects.all()
        self.fields["vehicle_type"].required = False

        # Values used by wv_form.html
        selected_model = self.initial.get("vehicle_model")

        if self.instance and self.instance.pk:
            selected_model = self.instance.vehicle_model_id

        model = None
        if selected_model:
            try:
                model = VehicleModel.objects.select_related(
                    "manufacturer",
                    "vehicle_category",
                ).get(pk=selected_model)
            except (VehicleModel.DoesNotExist, ValueError, TypeError):
                model = None

        self.selected_manufacturer_name = (
            model.manufacturer.manufacturer_name if model else ""
        )

        self.category_locked = bool(
            model and model.vehicle_category_id
        )

    def clean_vehicle_number(self):
        value = (self.cleaned_data.get("vehicle_number") or "").strip().upper()
        if not value:
            raise forms.ValidationError("Vehicle number is required.")
        return value

    def clean_status(self):
        return self.cleaned_data.get("status") or "active"

    def clean(self):
        cleaned_data = super().clean()

        # A selected model determines its manufacturer and category.
        model = cleaned_data.get("vehicle_model")

        if model:
            category = model.vehicle_category
            if category:
                cleaned_data["vehicle_type"] = category

        return cleaned_data