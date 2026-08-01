from datetime import datetime
from django.db import models
from django.core.validators import MinValueValidator
from django.forms import ValidationError
from django.db.models import Max
import re
import fleet_app




# Create your models here.
class CostCenter(models.Model):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    isDefault = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name}"


class ItemCategory(models.Model):
    category_name = models.CharField(max_length=100)
    isDefault = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # First record must be default
        if not self.pk and ItemCategory.objects.count() == 0:
            self.isDefault = True

        # Ensure only one default
        if self.isDefault:
            ItemCategory.objects.exclude(pk=self.pk).update(isDefault=False)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.isDefault:
            raise ValidationError("Default category cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.category_name
    
    def __str__(self):
        return self.category_name
    
    class Meta:
        db_table = 'item_category'
        verbose_name_plural = "Item Categories"
        ordering = ['category_name']

class ItemManufacturer(models.Model):
    manufacturer_name = models.CharField(max_length=100)
    isDefault = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.manufacturer_name
    
    class Meta:
        db_table = 'item_manufacturer'
        verbose_name_plural = "Item Manufacturers"
        ordering = ['manufacturer_name']  
        
          
class Unit(models.Model):
    unit_code = models.CharField(max_length=10, unique=True, verbose_name="Unit Code")
    unit_name = models.CharField(max_length=50, verbose_name="Unit Name")
    isDefault = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.unit_code
    
    
        
class TAX(models.Model):
    TAX_percent = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    TAX_name = models.CharField(max_length=50, blank=True, null=True)  
    isDefault = models.BooleanField(default=False) 
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)   
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f" {self.TAX_percent}%"
    
        
        

class Item(models.Model):
    ITEM_CLASS_CHOICES = [
        ('General', 'General'),
        ('Raw Material', 'Raw Material'),
        ('Service Item', 'Service Item'),
    ]

    item_name = models.CharField(max_length=100)
    item_code = models.CharField(max_length=50)
    IsItemBarcode = models.BooleanField(default=True)
    barcode_code = models.CharField(max_length=50, null=True, blank=True)
    regional_name = models.CharField(max_length=100, blank=True, null=True)
    item_category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, null=True, blank=True)
    item_manufacturer = models.ForeignKey(ItemManufacturer, on_delete=models.CASCADE, null=True, blank=True)
    TAX = models.ForeignKey(TAX, on_delete=models.CASCADE, null=True, blank=True)
    min_stock = models.PositiveIntegerField(default=0, blank=True, null=True)
    rack = models.CharField(max_length=50, blank=True, null=True)
    purchase_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    sales_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    MRP = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)  # Maximum Retail Price
    item_unit = models.ForeignKey(Unit, on_delete=models.PROTECT)
    uc_factor = models.PositiveIntegerField(default=1, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    item_class = models.CharField(max_length=20, choices=ITEM_CLASS_CHOICES, default='General')
    item_image = models.ImageField(upload_to='items_images/', blank=True, null=True)
    is_base_unit = models.BooleanField(default=True)  
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True)
    MaxStock = models.PositiveIntegerField(default=0, blank=True, null=True)
    Reorder = models.PositiveIntegerField(default=0, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    WholeSalePrice = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    SchemaPerc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    ProfitPerc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    CrediRateRet = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    CreditRateWhol = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    WholeProfitPerc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    Warrenty = models.PositiveIntegerField(default=0, blank=True, null=True)
    IsBatch = models.BooleanField(default=False)
    IsExpiry = models.BooleanField(default=False)
    TaxIncludExclud = models.BooleanField(default=False)
    ProfitPercWholeCredit = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    ProfitPercRetCrdt = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    HSN = models.CharField(max_length=50, blank=True, null=True)
    Rack = models.CharField(max_length=50, blank=True, null=True)
    IsNonInventory = models.BooleanField(default=False)
    SizeId = models.PositiveIntegerField(default=0, blank=True, null=True)
    IsSkipPrint = models.BooleanField(default=False)
    TaxIncludPrchs = models.BooleanField(default=False)
    cess = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    IsProductSerial = models.BooleanField(default=False)
    D1 = models.DateTimeField(auto_now_add=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} - {self.item_code}"
    
        
class ItemAlterUnit(models.Model):
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='alter_units')
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT)
    is_base_unit = models.BooleanField(default=False)
    uc_factor = models.DecimalField(max_digits=10, decimal_places=4 )
    barcode_code = models.CharField(max_length=50,  null=True, blank=True)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sales_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.item_name} - {self.unit} (Base: {self.is_base_unit})"
    

class Batch(models.Model):
    BatchNo = models.CharField(max_length=50, null=True, blank=True)
    Item = models.ForeignKey(Item, on_delete=models.CASCADE)
    Mfd = models.DateTimeField(null=True, blank=True)
    Exp = models.DateTimeField(null=True, blank=True)
    barcode_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    IsActive = models.BooleanField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.BatchNo or 'Batch'}"
    
class Vouchers(models.Model):
    VoucherType = models.CharField(max_length=50)
    VoucherName = models.CharField(max_length=100)
    Suffix = models.CharField(max_length=20, null=True, blank=True)
    Prefix = models.CharField(max_length=20, null=True, blank=True)
    MinLength = models.PositiveIntegerField(default=5)
    StartingNo = models.PositiveIntegerField(default=1)
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, null=True, blank=True)
    CostCenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True)
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    def get_next_voucher_number(self):
        """Generate the next voucher number for this voucher type"""
        # Get all models that use this voucher type
        from django.apps import apps
        
        all_voucher_numbers = []
        
        # Get all models that have voucher_no and voucherType fields
        for model in apps.get_models():
            if hasattr(model, 'voucher_no') and hasattr(model, 'voucherType'):
                # Get voucher numbers for this voucher type
                vouchers = model.objects.filter(voucherType=self).values_list('voucher_no', flat=True)
                all_voucher_numbers.extend(vouchers)
        
        if not all_voucher_numbers:
            # No existing vouchers, start with StartingNo
            current_number = self.StartingNo
        else:
            # Extract numbers from existing voucher numbers
            max_number = self.StartingNo - 1
            
            for voucher_no in all_voucher_numbers:
                # Extract number from voucher (remove prefix and suffix)
                number_part = voucher_no
                
                if self.Prefix:
                    number_part = number_part.replace(self.Prefix, '', 1)
                if self.Suffix:
                    number_part = number_part.replace(self.Suffix, '')
                
                # Extract numeric part
                try:
                    number = int(number_part)
                    max_number = max(max_number, number)
                except ValueError:
                    continue
            
            current_number = max_number + 1
        
        # Format the number with zero padding
        formatted_number = str(current_number).zfill(self.MinLength)
        
        # Construct full voucher number
        voucher_number = ""
        if self.Prefix:
            voucher_number += self.Prefix
        voucher_number += formatted_number
        if self.Suffix:
            voucher_number += self.Suffix
            
        return voucher_number

    def __str__(self):
        return f"{self.VoucherType} - {self.VoucherName}"

    def __str__(self):
     return f"{self.VoucherName}"
    
        
class Vendor(models.Model):
    vendor_name = models.CharField(max_length=255, help_text="Name of the rental company")
    vendor_mobile = models.CharField(max_length=20, help_text="Primary contact person")
    vendor_phone = models.CharField(null=True, blank=True,max_length=20, help_text="Phone number")
    vendor_email = models.EmailField(help_text="Email address")
    vendor_address_1 = models.TextField(null=True, blank=True,help_text="Address of the workshop") 
    vendor_address_2 = models.TextField(null=True, blank=True, help_text="Address of the workshop")
    vendor_country = models.CharField(null=True, blank=True,max_length=255, help_text="Country of the workshop")
    vendor_state = models.CharField(null=True, blank=True,max_length=255, help_text="State of the workshop") 
    vendor_city = models.CharField(null=True, blank=True,max_length=255, help_text="City of the workshop") 
    vendor_zipcode = models.CharField(null=True, blank=True,max_length=255, help_text="Zipcode of the workshop")
    vendor_website = models.URLField(null=True, blank=True, help_text=" website")
    vendor_description = models.TextField(null=True, blank=True, help_text=" description")
    vendor_VAT = models.CharField(null=True, blank=True,max_length=255, help_text="workshop VAT number")
    vendor_TRN_or_CRN = models.CharField(null=True, blank=True,max_length=255, help_text="workshop TRN or CRN number")
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return self.vendor_name
    
    class Meta:
        db_table = 'Item_Vendor'
        verbose_name_plural = 'Item_Vendor'     

        


class PurchaseMaster(models.Model):
    
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    
    auto_no = models.IntegerField(unique=True, blank=True, null=True)  # Auto-increment field
    voucher_no = models.CharField(max_length=100, unique=True, blank=False)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=13)
    transaction_date = models.DateField()
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, default=1)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='Cash')
    VendorInvNo = models.CharField(max_length=100, blank=True, null=True)
    InvoiceDate = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    total_net_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_terms = models.TextField(blank=True, null=True)
    grand_total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, null=True, blank=True, default=1)
    lrNo = models.CharField(max_length=100, blank=True, null=True)
    transportCompany = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    Freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        super().save(*args, **kwargs)
    
    
    

    
    
    def __str__(self):
        return f"Purchase {self.voucher_no}"
    
    class meta:
        db_table = 'purchases'
        verbose_name_plural = 'Purchases'
        ordering = ['auto_no']

class PurchaseDetail(models.Model):
    purchase = models.ForeignKey(PurchaseMaster, related_name='items', on_delete=models.CASCADE)
    item_code = models.CharField(max_length=100, blank=True, null=True)
    item_name = models.ForeignKey(Item, on_delete=models.PROTECT, blank=True, null=True)
    
    barcode_code = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], blank=True, null=True)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    item_net_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    item_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit = models.ForeignKey(Unit, related_name='purchase_unit_details', on_delete=models.PROTECT, blank=True, null=True)
    free_quantity = models.PositiveIntegerField(default=0, blank=True, null=True)
    MFD = models.DateField(blank=True, null=True)
    EXP = models.DateField(blank=True, null=True)
    sales_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sales_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    item_total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    Batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True)
    isexp = models.BooleanField(default=False)
    QtyInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    RateInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    BaseUnit = models.ForeignKey(Unit, related_name='purchase_baseunit_details', on_delete=models.SET_NULL, null=True, blank=True)
    Cess = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    SerialNo = models.CharField(max_length=100, blank=True, null=True)
    Cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} for {self.purchase.voucher_no}"
    
    class meta:
        db_table = 'purchase_items'
        verbose_name_plural = 'Purchase Items'

class PurchaseReturnMaster(models.Model):
    
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    
    auto_no = models.IntegerField(unique=True, blank=True, null=True)  # Auto-increment field
    voucher_no = models.CharField(max_length=100, unique=True, blank=False)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=1)
    transaction_date = models.DateField()
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, default=1)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='Cash')
    VendorInvNo = models.CharField(max_length=100, blank=True, null=True)
    InvoiceDate = models.DateField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    total_net_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_terms = models.TextField(blank=True, null=True)
    grand_total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, null=True, blank=True, default=1)
    lrNo = models.CharField(max_length=100, blank=True, null=True)
    transportCompany = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    Freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        super().save(*args, **kwargs)
    
    
    

    
    
    def __str__(self):
        return f"Purchase {self.voucher_no}"
    
    class meta:
        db_table = 'purchases'
        verbose_name_plural = 'Purchases'
        ordering = ['auto_no']

class PurchaseReturnDetail(models.Model):
    purchase = models.ForeignKey(PurchaseReturnMaster, related_name='items', on_delete=models.CASCADE)
    item_code = models.CharField(max_length=100, blank=True, null=True)
    item_name = models.ForeignKey(Item, on_delete=models.PROTECT, blank=True, null=True)
    
    barcode_code = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], blank=True, null=True)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    item_net_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    item_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit = models.ForeignKey(Unit, related_name='purchaseReturn_unit_details', on_delete=models.PROTECT, blank=True, null=True)
    free_quantity = models.PositiveIntegerField(default=0, blank=True, null=True)
    MFD = models.DateField(blank=True, null=True)
    EXP = models.DateField(blank=True, null=True)
    sales_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sales_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    item_total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    Batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True)
    isexp = models.BooleanField(default=False)
    QtyInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    RateInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    BaseUnit = models.ForeignKey(Unit, related_name='purchaseReturn_baseunit_details', on_delete=models.SET_NULL, null=True, blank=True)
    Cess = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    SerialNo = models.CharField(max_length=100, blank=True, null=True)
    Cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} for {self.purchase.voucher_no}"
    
    class meta:
        db_table = 'purchase_items'
        verbose_name_plural = 'Purchase Items'


        
        
            
class Customer(models.Model):
    customer_name = models.CharField(max_length=255, help_text="Name of the customer")
    customer_mobile = models.CharField(max_length=20, help_text="Primary contact person")
    customer_phone = models.CharField(null=True, blank=True,max_length=20, help_text="Phone number")
    customer_email = models.EmailField(help_text="Email address")
    customer_address_1 = models.TextField(null=True, blank=True,help_text="Address of the customer") 
    customer_address_2 = models.TextField(null=True, blank=True, help_text="Address of the customer")
    customer_country = models.CharField(null=True, blank=True,max_length=255, help_text="Country of the customer")
    customer_state = models.CharField(null=True, blank=True,max_length=255, help_text="State of the customer") 
    customer_city = models.CharField(null=True, blank=True,max_length=255, help_text="City of the customer") 
    customer_zipcode = models.CharField(null=True, blank=True,max_length=255, help_text="Zipcode of the customer")
    customer_website = models.URLField(null=True, blank=True, help_text=" website")
    customer_description = models.TextField(null=True, blank=True, help_text=" description")
    customer_VAT = models.CharField(null=True, blank=True,max_length=255, help_text="customer VAT number")
    customer_TRN_or_CRN = models.CharField(null=True, blank=True,max_length=255, help_text="customer TRN or CRN number")
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.customer_name
    
    class meta:
        db_table = 'customers'
        verbose_name_plural = 'customers'
        
        
        
        
        
            
class SalesMaster(models.Model):
    VOUCHER_PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    
    auto_no = models.IntegerField(unique=True, blank=True, null=True)  # Auto-increment field
    voucher_no = models.CharField(max_length=20, unique=True)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=14)
    transaction_date = models.DateField(default=datetime.now)
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, default=1)
    payment_mode = models.CharField(max_length=10, choices=VOUCHER_PAYMENT_MODE_CHOICES, default='cash')
    InvoiceNo = models.CharField(max_length=100, blank=True, null=True)
    InvoiceDate = models.DateField(blank=True, null=True)
    PO_number = models.CharField(max_length=50, null=True, blank=True)  # Purchase Order number
    DO_number = models.CharField(max_length=50, null=True, blank=True)  # Delivery Order number
    mobile = models.CharField(max_length=15, null=True, blank=True)
    customer_TRN = models.CharField(max_length=20, null=True, blank=True)  # Tax Registration Number
    vehicle_number = models.ForeignKey('fleet_app.Vehicle', on_delete=models.PROTECT, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    terms_and_conditions = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    total_net_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, null=True, blank=True, default=1)
    lrNo = models.CharField(max_length=100, blank=True, null=True)
    transportCompany = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    Freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        super().save(*args, **kwargs)
    
    

    def __str__(self):
        return f"{self.voucher_no} - {self.ledger.ledger_name}"    
            

class SalesDetail(models.Model):
    sales_voucher = models.ForeignKey(SalesMaster, related_name='items', on_delete=models.CASCADE)
    item_code = models.CharField(max_length=50, blank=True, null=True)
    item_name = models.ForeignKey(Item, on_delete=models.PROTECT, blank=True, null=True)
    barcode_code = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0, blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, blank=True, null=True, related_name='salesReturn_unit_details')
    sales_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    item_net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)  
    item_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    item_total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    Batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True)
    MFD = models.DateField(blank=True, null=True)
    EXP = models.DateField(blank=True, null=True)
    QtyInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    RateInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    BaseUnit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='salesReturn_baseunit_details')
    
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} - {self.sales_voucher.voucher_no}"     

class SalesReturnMaster(models.Model):
    VOUCHER_PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    
    auto_no = models.IntegerField(unique=True, blank=True, null=True)  # Auto-increment field
    voucher_no = models.CharField(max_length=20, unique=True)
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT, default=2)
    transaction_date = models.DateField(default=datetime.now)
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, default=1)
    payment_mode = models.CharField(max_length=10, choices=VOUCHER_PAYMENT_MODE_CHOICES, default='cash')
    InvoiceNo = models.CharField(max_length=100, blank=True, null=True)
    InvoiceDate = models.DateField(blank=True, null=True)
    PO_number = models.CharField(max_length=50, null=True, blank=True)  # Purchase Order number
    DO_number = models.CharField(max_length=50, null=True, blank=True)  # Delivery Order number
    mobile = models.CharField(max_length=15, null=True, blank=True)
    customer_TRN = models.CharField(max_length=20, null=True, blank=True)  # Tax Registration Number
    vehicle_number = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    terms_and_conditions = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    total_net_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.PROTECT, null=True, blank=True, default=1)
    lrNo = models.CharField(max_length=100, blank=True, null=True)
    transportCompany = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    Freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        super().save(*args, **kwargs)
    
    

    def __str__(self):
        return f"{self.voucher_no} - {self.ledger.ledger_name}"   
     

class SalesReturnDetail(models.Model):
    sales_voucher = models.ForeignKey(SalesReturnMaster, related_name='items', on_delete=models.CASCADE)
    item_code = models.CharField(max_length=50, blank=True, null=True)
    item_name = models.ForeignKey(Item, on_delete=models.PROTECT, blank=True, null=True)
    barcode_code = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0, blank=True, null=True)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, blank=True, null=True, related_name='sales_unit_details')
    sales_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    item_net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, blank=True, null=True)  
    item_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    item_total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    Batch = models.ForeignKey(Batch, on_delete=models.PROTECT, blank=True, null=True)
    MFD = models.DateField(blank=True, null=True)
    EXP = models.DateField(blank=True, null=True)
    QtyInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    RateInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    BaseUnit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_baseunit_details')
    
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item_name} - {self.sales_voucher.voucher_no}"     
           
    
class Stock(models.Model):
    voucherDate = models.DateField()
    voucherType = models.ForeignKey('fleet_app.Vouchers', on_delete=models.PROTECT)
    voucherNo = models.BigIntegerField()  
    item = models.ForeignKey('Item', on_delete=models.PROTECT)  # Adjust 'Item' to your actual model name
    batch = models.ForeignKey('Batch', on_delete=models.PROTECT, null=True, blank=True)  # Adjust 'Batch' accordingly
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT)  # Adjust 'Unit' accordingly
    costCenter = models.ForeignKey('CostCenter', on_delete=models.PROTECT)  # Adjust 'CostCenter' accordingly
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    in_quantity = models.IntegerField(default=0)
    out_quantity = models.IntegerField(default=0)
    stock_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fyId = models.IntegerField(null=True, blank=True) # will change to Fk in future
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f"Stock Entry - Item: {self.item}, Qty: {self.in_quantity}"
    
class OutstandingReport(models.Model):
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE)
    bill_no = models.CharField(max_length=20)  
    invoice_no = models.CharField(max_length=100) 
    transaction_type = models.CharField(
        max_length=50,
        choices=[('Purchase', 'Purchase'), ('Payment', 'Payment'), ('Sales', 'Sales'), ('Receipt', 'Receipt')],
        default='Purchase'
    )
    debit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)  
    credit_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)  
    balance_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # Running balance
    settled_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.ledger} - {self.transaction_type} - {self.balance_amount}"  
    

    
class BillByBill(models.Model):
    outstanding = models.ForeignKey(OutstandingReport, on_delete=models.CASCADE)
    settle_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    settle_date = models.DateField(auto_now_add=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settlement for {self.outstanding.bill_no} - {self.settle_amount}"      
    
    
class DayBookReport(models.Model):
    date = models.DateField()
    ledger = models.CharField(max_length=255)  # Assumes ledger is a text field; adjust as needed.
    voucher_type = models.CharField(max_length=50)
    debit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoice_no = models.CharField(max_length=100, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - {self.ledger} ({self.voucher_type})"    
    
    
 
    
  
class OpeningStockMaster(models.Model):
    
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    
    auto_no = models.IntegerField(unique=True, blank=True, null=True)  # Auto-increment field
    voucher_no = models.CharField(max_length=100, unique=True, blank=False)
    transaction_date = models.DateField()
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES, default='Cash')
    
    remarks = models.TextField(blank=True, null=True)
    total_net_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_terms = models.TextField(blank=True, null=True)
    grand_total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, blank=True)  
    lrNo = models.CharField(max_length=100, blank=True, null=True)
    transportCompany = models.CharField(max_length=100, blank=True, null=True)
    isDeleted = models.BooleanField(default=False)
    Freight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    

class OpeningStockDetail(models.Model):
    opening_stock = models.ForeignKey(OpeningStockMaster, related_name='items', on_delete=models.CASCADE)
    item_code = models.CharField(max_length=100, blank=True, null=True)
    item_name = models.ForeignKey(Item, on_delete=models.CASCADE, blank=True, null=True)
    
    barcode_code = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], blank=True, null=True)
    purchase_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    item_net_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    item_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unit = models.ForeignKey('Unit', on_delete=models.CASCADE, blank=True, null=True)
    free_quantity = models.PositiveIntegerField(default=0, blank=True, null=True)
    manufacture_date = models.DateField(blank=True, null=True)
    expire_date = models.DateField(blank=True, null=True)
    sales_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    sales_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    profit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    item_total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) 
    BatchId = models.ForeignKey('Batch', on_delete=models.CASCADE, blank=True, null=True)
    isexp = models.BooleanField(default=False)
    QtyInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    RateInBaseUnit = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    Cess = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    SerialNo = models.CharField(max_length=100, blank=True, null=True)
       
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    
class StockTransfer(models.Model):
    transfer_date = models.DateField(auto_now_add=True)
    voucher_no = models.CharField(max_length=100, unique=True, blank=False)
    source_cost_center = models.ForeignKey('CostCenter', on_delete=models.PROTECT, related_name='stock_outgoing')
    destination_cost_center = models.ForeignKey('CostCenter', on_delete=models.PROTECT, related_name='stock_incoming')
    remarks = models.TextField(blank=True, null=True)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=1)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        super().save(*args, **kwargs)
    

    def __str__(self):
        return f"Transfer {self.voucher_no} on {self.transfer_date}"


class StockTransferItem(models.Model):
    stock_transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('Item', on_delete=models.PROTECT)
    unit = models.ForeignKey('Unit', on_delete=models.PROTECT)
    batch = models.ForeignKey('Batch', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item} ({self.quantity} {self.unit})"
    
    
