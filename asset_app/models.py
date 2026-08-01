from django.db import models
from fleet_app.models import Vehicle
from item_master.models import TAX

# Create your models here.

class AssetMaster(models.Model):

    ASSET_CATEGORY_CHOICES = [
        ('Machinery', 'Machinery'),
        ('IT Equipment', 'IT Equipment'),
        ('Furniture', 'Furniture'),
        ('Tools', 'Tools'),
        ('Building', 'Building'),
        ('Interior', 'Interior'),
    ]

    ASSET_TYPE_CHOICES = [
        ('Vehicle', 'Vehicle'),
        ('Equipment', 'Equipment'),
        ('Machine', 'Machine'),
    ]

    asset_code = models.CharField(max_length=50, unique=True)
    asset_name = models.CharField(max_length=200)
    asset_category = models.CharField(max_length=50, choices=ASSET_CATEGORY_CHOICES)
    asset_type = models.CharField(max_length=50, choices=ASSET_TYPE_CHOICES)
    vehicle = models.ForeignKey('fleet_app.Vehicle', on_delete=models.CASCADE, null=True, blank=True)

    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, null=True, blank=True)

    description = models.TextField(blank=True, null=True)

    vat = models.ForeignKey('item_master.TAX', on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"