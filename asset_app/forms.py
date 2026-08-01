from django import forms
from .models import AssetMaster

class AssetMasterForm(forms.ModelForm):
    class Meta:
        model = AssetMaster
        fields = ['asset_code', 'asset_name', 'vehicle', 'asset_category', 'asset_type', 'description', 'vat']
    
    labels = {
        'asset_code': 'Asset Code',
        'asset_name': 'Asset Name',
        'asset_category': 'Asset Category',
        'asset_type': 'Asset Type',
        'description': 'Description',
        'vat': 'VAT',
        'vehicle': 'Vehicle',
    }
    widgets = {
        'asset_code': forms.TextInput(attrs={'class': 'form-control'}),
        'asset_name': forms.TextInput(attrs={'class': 'form-control'}),
        'asset_category': forms.Select(attrs={'class': 'form-control'}),
        'asset_type': forms.Select(attrs={'class': 'form-control'}),
        'description': forms.Textarea(attrs={'class': 'form-control'}),
        'vat': forms.Select(attrs={'class': 'form-control'}),
        'vehicle': forms.Select(attrs={'class': 'form-control'}),
    }
