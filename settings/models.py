from django.db import models

# Create your models here.
class GlobalSettings(models.Model):
    NEGATIVE_STOCK_CHOICES = (
        (1, "Allow"),
        (2, "Warning Only"),
        (3, "Block"),
    )

    CREDIT_LIMIT_CHOICES = (
        (1, "Allow"),
        (2, "Warning Only"),
        (3, "Block"),
    )

    # Boolean fields
    update_rate_from_purchase = models.BooleanField(default=False)
    price_list = models.BooleanField(default=False)
    billbybill = models.BooleanField(default=False)
    serial_no_tracking_item = models.BooleanField(default=False)
    costcenter = models.BooleanField(default=False)
    show_customer_rate = models.BooleanField(default=False)
    show_vendor_rate = models.BooleanField(default=False)
    barcode = models.BooleanField(default=False)
    batch_expiry = models.BooleanField(default=False)
    barcode_auto_prefix = models.BooleanField(default=False)
    barcode_custom_prefix = models.CharField(max_length=10, blank=True, null=True)

    # Choice fields (int values)
    negative_stock = models.IntegerField(
        choices=NEGATIVE_STOCK_CHOICES,
        default=1,
    )
    credit_limit = models.IntegerField(
        choices=CREDIT_LIMIT_CHOICES,
        default=1,
    )

    # Integer field
    starting_barcode = models.IntegerField(default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    

    def __str__(self):
        return f"Settings (Negative Stock: {self.get_negative_stock_display()}, Credit Limit: {self.get_credit_limit_display()})"
    
class Currency(models.Model):
    CurrencyName = models.CharField(max_length=50, unique=True)
    Decimal = models.PositiveSmallIntegerField(default=3)   # Number of decimal places 
    MajorSymbol = models.CharField(max_length=10, blank=True, null=True)  # e.g., $
    MinorSymbol = models.CharField(max_length=10, blank=True, null=True)  

    def __str__(self):
        return f"{self.CurrencyName} ({self.MajorSymbol})"    