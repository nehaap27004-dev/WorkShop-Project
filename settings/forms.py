from django import forms
from .models import *


class SettingsForm(forms.ModelForm):
    class Meta:
        model = GlobalSettings
        fields = [
            # General
            "update_rate_from_purchase",
            "price_list",
            "billbybill",
            "serial_no_tracking_item",
            "costcenter",

            # Sales
            "show_customer_rate",
            "show_vendor_rate",
            "negative_stock",
            "credit_limit",

            # Barcode
            "barcode",
            "batch_expiry",
            "barcode_auto_prefix",
            "barcode_custom_prefix",
            "starting_barcode",
        ]
        labels = {
            # General
            "update_rate_from_purchase": "Update Rate from Purchase",
            "price_list": "Enable Price List",
            "billbybill": "Bill by Bill Adjustment",
            "serial_no_tracking_item": "Item Serial Number Tracking",
            "costcenter": "Enable Cost Center",

            # Sales
            "show_customer_rate": "Show Customer Rate In Sales",
            "show_vendor_rate": "Show Vendor Rate In Purchase",
            "negative_stock": "Negative Stock",
            "credit_limit": "Credit Limit",

            # Barcode
            "barcode": "Enable Barcode",
            "batch_expiry": "Enable Expiry",
            "barcode_auto_prefix": "Auto Prefix",
            "barcode_custom_prefix": "Custom Prefix",
            "starting_barcode": "Starting Barcode",
        }
        widgets = {
            # General Section Boolean Fields
            'update_rate_from_purchase': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'update_rate_from_purchase'
            }),
            'price_list': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'price_list'
            }),
            'billbybill': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'billbybill'
            }),
            'serial_no_tracking_item': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'serial_no_tracking_item'
            }),
            'costcenter': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'costcenter'
            }),
            
            # Sales Section Fields
            'show_customer_rate': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'show_customer_rate'
            }),
            'show_vendor_rate': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'show_vendor_rate'
            }),
            'negative_stock': forms.Select(attrs={
                'class': 'form-select',
                'id': 'negative_stock'
            }),
            'credit_limit': forms.Select(attrs={
                'class': 'form-select',
                'id': 'credit_limit'
            }),
            
            # Barcode Section Fields
            'barcode': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'barcode'
            }),
            'batch_expiry': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'expiry'
            }),
            ' barcode_auto_prefix': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'auto_prifix'
            }),
            ' barcode_custom_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'custom_prefix'
            }),
            'starting_barcode': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'starting_barcode',
                'min': '0'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial readonly state for starting_barcode if auto_prifix is True
        if self.instance and self.instance.barcode_auto_prefix:
            self.fields['starting_barcode'].widget.attrs['readonly'] = True
            
        for field in self.fields.values():
           field.label_suffix = ""  # removes colon   

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['CurrencyName', 'Decimal', 'MajorSymbol', 'MinorSymbol']

        widgets = {
            'CurrencyName': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter currency name (e.g., USD, INR)'
            }),
            'Decimal': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 5,
                'placeholder': 'Number of decimals'
            }),
            'MajorSymbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter major symbol (e.g., $, ₹)'
            }),
            'MinorSymbol': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter minor symbol (¢, p)'
            }),
        }           