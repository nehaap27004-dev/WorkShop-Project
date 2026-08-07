from datetime import datetime

from django.db import models
from django.urls import reverse
from accounts_app.models import LedgerCreation
from item_master.models import Item
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal


class ServiceCategory(models.Model):
    name        = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_on  = models.DateTimeField(auto_now_add=True)
    updated_on  = models.DateTimeField(auto_now=True)
    created_by  = models.IntegerField(null=True, blank=True)
    updated_by  = models.IntegerField(null=True, blank=True)

    def service_count(self):
        return 0

    def __str__(self):
        return self.name

    class Meta:
        ordering   = ['name']
        verbose_name        = 'Service Category'
        verbose_name_plural = 'Service Categories'
      


class WorkshopVehicle(models.Model):

    FUEL_CHOICES = [
        ('petrol',   'Petrol'),
        ('diesel',   'Diesel'),
        ('electric', 'Electric'),
        ('hybrid',   'Hybrid'),
        ('cng',      'CNG'),
        ('lpg',      'LPG'),
        ('other',    'Other'),
    ]

    STATUS_CHOICES = [
        ('active',   'Active'),
        ('inactive', 'Inactive'),
        ('sold',     'Sold'),
        ('scrapped', 'Scrapped'),
    ]

    # ── Customer (required) ───────────────────────────────────
    customer = models.ForeignKey(
        'accounts_app.LedgerCreation',
        on_delete=models.PROTECT,
        related_name='workshop_vehicles',
        verbose_name='Customer / Owner'
    )

    # ── Vehicle Information ───────────────────────────────────
    vehicle_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Vehicle Number',
        help_text='Auto-generated: VH-00001'
    )
    vehicle_type = models.ForeignKey(
        'fleet_app.VehicleCategory',
        on_delete=models.PROTECT,
        null=True,      
        blank=True,
        related_name='workshop_vehicles',
        verbose_name='Vehicle Type'
    )
    registration_number = models.CharField(
        max_length=30,
        unique=True,
        verbose_name='Registration / Plate No'
    )
    chassis_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Chassis Number'
    )
    engine_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Engine Number'
    )
    manufacturer = models.ForeignKey(
        'fleet_app.Manufacturer',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='workshop_vehicles',
        verbose_name='Manufacturer'
    )
    vehicle_model = models.ForeignKey(
        'fleet_app.VehicleModel',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='workshop_vehicles',
        verbose_name='Model'
    )
    year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Model Year'
    )
    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Color'
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_CHOICES,
        blank=True,
        null=True,
        verbose_name='Fuel Type'
    )
    odometer = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Current Odometer (km)'
    )
    vehicle_image = models.ImageField(
        upload_to='workshop_vehicles/images/',
        blank=True,
        null=True,
        verbose_name='Vehicle Image'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notes'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )

    # ── Registration Details ──────────────────────────────────
    registration_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Registration Date'
    )
    registration_expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Registration Expiry Date'
    )

    # ── Insurance Details ─────────────────────────────────────
    insurance_policy_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Insurance Policy Number'
    )
    insurance_expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Insurance Expiry Date'
    )

    # ── Service Tracking ──────────────────────────────────────
    last_service_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Last Service Date'
    )
    next_service_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Next Service Date'
    )
    service_interval = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Service Interval (km)',
        help_text='e.g. 5000 means alert every 5000 km'
    )

    # ── Meta ─────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)

    # ── Status Helpers ────────────────────────────────────────
    def get_service_status(self):
        from django.utils import timezone
        from datetime import timedelta
        if not self.next_service_date:
            return 'unknown'
        today = timezone.now().date()
        if self.next_service_date < today:
            return 'overdue'
        if self.next_service_date <= today + timedelta(days=30):
            return 'due_soon'
        return 'ok'

    def get_insurance_status(self):
        from django.utils import timezone
        from datetime import timedelta
        if not self.insurance_expiry_date:
            return 'unknown'
        today = timezone.now().date()
        if self.insurance_expiry_date < today:
            return 'expired'
        if self.insurance_expiry_date <= today + timedelta(days=30):
            return 'expiring'
        return 'ok'

    def get_registration_status(self):
        from django.utils import timezone
        from datetime import timedelta
        if not self.registration_expiry_date:
            return 'unknown'
        today = timezone.now().date()
        if self.registration_expiry_date < today:
            return 'expired'
        if self.registration_expiry_date <= today + timedelta(days=30):
            return 'expiring'
        return 'ok'

    def __str__(self):
        mfr = self.manufacturer.manufacturer_name if self.manufacturer else ''
        mdl = self.vehicle_model.model_name if self.vehicle_model else ''
        return f"{self.registration_number} — {mfr} {mdl}".strip()

    class Meta:
        ordering            = ['-created_on']
        verbose_name        = 'Workshop Vehicle'
        verbose_name_plural = 'Workshop Vehicles'





class JobCard(models.Model):

    PRIORITY_CHOICES = [
        ('normal',  'Normal'),
        ('urgent',  'Urgent'),
        ('express', 'Express'),
    ]

    STATUS_CHOICES = [
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('waiting',     'Waiting'),
        ('completed',   'Completed'),
        ('closed',      'Closed'),
        ('cancelled',   'Cancelled'),
    ]

    FUEL_CHOICES = [
        ('empty', 'Empty'),
        ('1/4',   '1/4'),
        ('1/2',   '1/2'),
        ('3/4',   '3/4'),
        ('full',  'Full'),
    ]

    job_number      = models.CharField(max_length=20, unique=True, blank=True,
                          help_text='Auto-generated: JC-00001')
    voucher_number  = models.CharField(max_length=50, blank=True, null=True)
    date            = models.DateField()

    customer = models.ForeignKey(
        'accounts_app.LedgerCreation',
        on_delete=models.PROTECT,
        related_name='job_cards',
        verbose_name='Customer'
    )
    # ADD inside JobCard model
    customer_phone  = models.CharField(
        max_length=30, blank=True,
        verbose_name='Customer Phone')
    vehicle_model   = models.CharField(
        max_length=100, blank=True,
        verbose_name='Vehicle Model')
    workshop_vehicle = models.ForeignKey(
        'WorkshopVehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='jobcards',
        verbose_name='Vehicle'
    )
    advisor = models.ForeignKey(
        'fleet_app.Staff',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='jobcards_advised',
        verbose_name='Service Advisor'
    )

    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    status   = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    delivery_date = models.DateField(null=True, blank=True, verbose_name='Expected Delivery Date')
    mileage       = models.PositiveIntegerField(null=True, blank=True, verbose_name='Current Mileage (km)')
    fuel_level    = models.CharField(max_length=10, choices=FUEL_CHOICES, default='1/2')

    is_active  = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs): 
        if not self.job_number:
            from jobcard_app.utils import generate_voucher_number
            self.job_number = generate_voucher_number('JobCard', JobCard, 'job_number', default_prefix='JC-')
        super().save(*args, **kwargs)

    def get_parts_total(self):
        return sum((p.total_price or 0) for p in self.parts.all())

    def get_labour_total(self):
        return sum((l.amount or 0) for l in self.labours.all())

    def get_grand_total(self):
        return self.get_parts_total() + self.get_labour_total()

    def __str__(self):
        return f"{self.job_number} — {self.customer}"

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Job Card'
        verbose_name_plural = 'Job Cards'


class JobCardComplaint(models.Model):
    """Customer-reported complaints on the job card"""

    TYPE_CHOICES = [
        ('Mechanical', 'Mechanical'),
        ('Electrical', 'Electrical'),
        ('Body',       'Body'),
        ('AC',         'AC'),
        ('Other',      'Other'),
    ]
    STATUS_CHOICES = [
        ('Open',        'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved',    'Resolved'),
    ]

    jobcard              = models.ForeignKey(
        'JobCard', on_delete=models.CASCADE,
        related_name='complaints'
    )
    service_category     = models.ForeignKey(
        'ServiceCategory', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='complaints'
    )
    # Store category name text for display even if category deleted
    category             = models.CharField(max_length=150, blank=True)
    description          = models.CharField(max_length=400)
    type                 = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='Mechanical'
    )
    technician = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_complaints'
    )
    status               = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Open'
    )
    # Link to the inspection this complaint came from (optional)
    source_inspection    = models.ForeignKey(
        'VehicleInspection', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='loaded_complaints'
    )
    order                = models.PositiveIntegerField(default=0)
    created_on           = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.jobcard.job_number}] {self.description[:60]}"

    class Meta:
        ordering = ['order', 'id']


class JobCardFinding(models.Model):
    """Technician-identified findings on the job card"""

    STATUS_CHOICES = [
        ('Pending',   'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Resolved',  'Resolved'),
    ]

    jobcard     = models.ForeignKey(
        'JobCard', on_delete=models.CASCADE,
        related_name='findings'
    )
    description = models.CharField(max_length=400)
    technician = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_findings'
    )
    status      = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending'
    )
    # Link to inspection finding source (optional)
    source_inspection = models.ForeignKey(
        'VehicleInspection', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='loaded_findings'
    )
    order       = models.PositiveIntegerField(default=0)
    created_on  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.jobcard.job_number}] {self.description[:60]}"

    class Meta:
        ordering = ['order', 'id']





class JobCardPart(models.Model):

    WARRANTY_CHOICES = [
        ('', 'None'),
        ('1 Month',   '1 Month'),
        ('3 Months',  '3 Months'),
        ('6 Months',  '6 Months'),
        ('12 Months', '12 Months'),
        ('2 Years',   '2 Years'),
    ]

    jobcard    = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='parts')
    description = models.CharField(max_length=300, blank=True, verbose_name='Item')
    part_number = models.CharField(max_length=100, blank=True, null=True)
    quantity    = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price  = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    warranty    = models.CharField(max_length=20, choices=WARRANTY_CHOICES, blank=True)

    def save(self, *args, **kwargs):
        # Keep the stored total consistent even if a caller forgets to set it
        if self.quantity is not None and self.unit_price is not None:
            self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description[:50] or f"Part #{self.pk}"

    class Meta:
        ordering = ['id']
        verbose_name = 'Job Card Part'


class JobCardLabour(models.Model):

    jobcard    = models.ForeignKey(JobCard, on_delete=models.CASCADE, related_name='labours')
    technician = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labour_entries'
    )
    description = models.CharField(max_length=300, blank=True)
    hours       = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    rate        = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    amount      = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    def save(self, *args, **kwargs):
        if self.hours is not None and self.rate is not None:
            self.amount = self.hours * self.rate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description[:50] or f"Labour #{self.pk}"

    class Meta:
        ordering = ['id']
        verbose_name = 'Job Card Labour'

# ─────────────────────────────────────────────────────────────
# ADD TO: jobcard_app/models.py
# ─────────────────────────────────────────────────────────────

class Estimate(models.Model):

    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('sent',     'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    estimate_number = models.CharField(
        max_length=20, unique=True, blank=True,
        help_text='Auto-generated: EST-00001')

    jobcard = models.ForeignKey(
        'JobCard', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='estimates',
        verbose_name='Job Card')

    customer = models.ForeignKey(
        'accounts_app.LedgerCreation',
        on_delete=models.PROTECT,
        related_name='estimates',
        verbose_name='Customer')

    vehicle = models.ForeignKey(
        'WorkshopVehicle',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='estimates',
        verbose_name='Vehicle')

    date       = models.DateField()
    status     = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')

    mileage    = models.PositiveIntegerField(null=True, blank=True)
    vin        = models.CharField(max_length=50, blank=True, null=True,
                     verbose_name='VIN / Chassis No')

    advisor = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='estimates_advised')

    tax_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    discount    = models.DecimalField(
        max_digits=10, decimal_places=3, default=0)
    notes       = models.TextField(blank=True)

    is_active  = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.estimate_number:
            from jobcard_app.utils import generate_voucher_number
            self.estimate_number = generate_voucher_number('Estimate', Estimate, 'estimate_number', default_prefix='EST-')
        super().save(*args, **kwargs)

    def get_subtotal(self):
        total = Decimal('0.000')

        for item in self.items.all():
            total += Decimal(str(item.total_price()))

        return total


    def get_tax_amount(self):
        subtotal = self.get_subtotal()
        tax_percent = self.tax_percent or Decimal('0.000')

        return self.get_subtotal() * self.tax_percent / 100  


    def get_grand_total(self):
        subtotal = self.get_subtotal()
        tax = self.get_tax_amount()
        discount = self.discount or Decimal('0.000')

        return subtotal + tax - discount
    def get_parts_total(self):
        return sum((Decimal(str(item.total_price())) for item in self.items.filter(item_type='part')), Decimal('0.000'))

    def get_labour_total(self):
        return sum((Decimal(str(item.total_price())) for item in self.items.filter(item_type='labour')), Decimal('0.000'))

    def __str__(self):
        return f"{self.estimate_number} — {self.customer}"

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Estimate'
        verbose_name_plural = 'Estimates'


class EstimateItem(models.Model):

    TYPE_CHOICES = [
        ('part',   'Part'),
        ('labour', 'Labour'),
    ]


    estimate    = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name='items')
    item_type   = models.CharField(max_length=10, choices=TYPE_CHOICES, default='part')
    item_ref    = models.CharField(max_length=50, blank=True, null=True)
    item_code   = models.CharField(max_length=100, blank=True)
    unit        = models.CharField(max_length=30, blank=True)
    description = models.CharField(max_length=300)
    technician = models.ForeignKey('fleet_app.Staff', on_delete=models.SET_NULL,null=True, blank=True, related_name='estimate_items')
    quantity    = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    hours       = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    unit_price  = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    warranty    = models.CharField(max_length=50, blank=True, null=True)
    order       = models.PositiveIntegerField(default=0)

    def total_price(self):
        if self.item_type == 'labour':
            return float(self.hours or 1) * float(self.unit_price or 0)
        return float(self.quantity or 1) * float(self.unit_price or 0)

    class Meta:
        ordering = ['order', 'id']
   
    
class EstimateComplaint(models.Model):

    TYPE_CHOICES = [
        ('customer',   'Customer Complaint'),
        ('technician', 'Technician Finding'),
    ]

    estimate        = models.ForeignKey(
        Estimate, on_delete=models.CASCADE,
        related_name='complaints')
    complaint_type  = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='customer')
    description     = models.TextField()
    order           = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.get_complaint_type_display()} — {self.description[:50]}"

    class Meta:
        ordering = ['complaint_type', 'order']

# ─────────────────────────────────────────────────────────────
# QUOTATION
# ─────────────────────────────────────────────────────────────
class Quotation(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('sent',     'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired',  'Expired'),
    ]

    quotation_number = models.CharField(max_length=50, unique=True, blank=True)
    estimate         = models.ForeignKey(
                           'Estimate',
                           on_delete=models.SET_NULL,
                           null=True, blank=True,
                           related_name='quotations',
                           help_text="Linked estimate (optional)")
    jobcard         = models.ForeignKey(
                           'JobCard',
                           on_delete=models.SET_NULL,
                           null=True, blank=True,
                           related_name='jobcard_quotations')
    

    customer         = models.ForeignKey(
                           'accounts_app.LedgerCreation',
                           on_delete=models.PROTECT,
                           related_name='jobcard_quotations')
    vehicle          = models.ForeignKey(
                           'WorkshopVehicle',
                           on_delete=models.SET_NULL,
                           null=True, blank=True,
                           related_name='jobcard_quotations')
    date             = models.DateField()
    valid_until      = models.DateField(null=True, blank=True)
    status           = models.CharField(max_length=20,
                           choices=STATUS_CHOICES, default='draft')
    mileage          = models.PositiveIntegerField(null=True, blank=True)
    vin              = models.CharField(max_length=50, blank=True, null=True, verbose_name='VIN / Chassis No')
    advisor = models.ForeignKey(
                'fleet_app.Staff', on_delete=models.SET_NULL,
                null=True, blank=True,
                related_name='quotation_advised')
    tax_percent      = models.DecimalField(max_digits=5, decimal_places=2,
                           default=0)
    discount         = models.DecimalField(max_digits=10, decimal_places=2,
                           default=0)
    terms            = models.CharField(max_length=200, blank=True)
    notes            = models.TextField(blank=True)
    created_on       = models.DateTimeField(auto_now_add=True)
    updated_on       = models.DateTimeField(auto_now=True)
    created_by       = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            from jobcard_app.utils import generate_voucher_number
            self.quotation_number = generate_voucher_number('Quotation', Quotation, 'quotation_number', default_prefix='QT-')
        super().save(*args, **kwargs)

    def get_subtotal(self):
        return sum(item.total_price() for item in self.items.all())

    def get_tax_amount(self):
        return self.get_subtotal() * self.tax_percent / 100

    def get_grand_total(self):
        return self.get_subtotal() + self.get_tax_amount() - self.discount

    def parts(self):
        return self.items.filter(item_type='part')

    def labour(self):
        return self.items.filter(item_type='labour')

    def complaints_customer(self):
        return self.complaints.filter(complaint_type='customer')

    def findings_technician(self):
        return self.complaints.filter(complaint_type='technician')

    def __str__(self):
        return f"{self.quotation_number} — {self.customer}"

    class Meta:
        ordering = ['-created_on']
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"


# ─────────────────────────────────────────────────────────────
# QUOTATION ITEM
# ─────────────────────────────────────────────────────────────
class QuotationItem(models.Model):

    TYPE_CHOICES = [
        ('part', 'Part'),
        ('labour', 'Labour'),
    ]

    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='items'
    )

    item_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='part'
    )

    # Item Master reference for spare parts
    item_ref = models.CharField(
        max_length=50,blank=True,null=True
    )

    unit = models.CharField(max_length=30,blank=True)
    description = models.CharField(max_length=300)
    technician = models.ForeignKey('fleet_app.Staff',on_delete=models.SET_NULL,null=True,blank=True,related_name='quotation_items')
    quantity = models.DecimalField(max_digits=10,decimal_places=2,default=1)
    hours = models.DecimalField(max_digits=6,decimal_places=2,default=1)
    unit_price = models.DecimalField(max_digits=12,decimal_places=3,default=0)
    warranty = models.CharField(max_length=50,blank=True)
    order = models.PositiveIntegerField(default=0)

    def total_price(self):
        if self.item_type == 'labour':
            return (self.hours or 0) * (self.unit_price or 0)
        return (self.quantity or 0) * (self.unit_price or 0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.description


# ─────────────────────────────────────────────────────────────
# QUOTATION COMPLAINT
# ─────────────────────────────────────────────────────────────
class QuotationComplaint(models.Model):

    TYPE_CHOICES = [
        ('customer',   'Customer Complaint'),
        ('technician', 'Technician Finding'),
    ]

    MECHTYPE_CHOICES = [
        ('Mechanical',  'Mechanical'),
        ('Electrical',  'Electrical'),
        ('Body',        'Body'),
        ('AC',          'AC'),
        ('Other',       'Other'),
    ]

    STATUS_CHOICES = [
        ('Open',        'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved',    'Resolved'),
    ]

    quotation       = models.ForeignKey(
        Quotation, on_delete=models.CASCADE,
        related_name='complaints')
    complaint_type  = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='customer')
    service_category = models.ForeignKey(
        'ServiceCategory', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='quotation_complaints')
    description     = models.TextField()
    type            = models.CharField(
        max_length=20, choices=MECHTYPE_CHOICES, default='Mechanical')
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Open')
    order           = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.get_complaint_type_display()} — {self.description[:50]}"

    class Meta:
        ordering = ['complaint_type', 'order']





class VehicleInspection(models.Model):
    """Master inspection record"""

    FUEL_CHOICES = [
        ('empty', 'Empty'),
        ('1/4',   '1/4'),
        ('1/2',   '1/2'),
        ('3/4',   '3/4'),
        ('full',  'Full'),
    ]

    # Auto number
    inspection_number = models.CharField(
        max_length=50, unique=True, blank=True)

    # Links
    vehicle   = models.ForeignKey(
        'WorkshopVehicle', on_delete=models.PROTECT,
        related_name='inspections')
    customer  = models.ForeignKey(
        'accounts_app.LedgerCreation', on_delete=models.PROTECT,
        related_name='inspections')
    jobcard  = models.OneToOneField(
        'JobCard', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ws_inspection')

    # General
    inspection_date = models.DateField()
    inspector       = models.ForeignKey(
        'fleet_app.Staff', 
        on_delete=models.SET_NULL,
        null=True, blank=True, 
        related_name='inspections_done',
        verbose_name='Inspector'
        )
    # Odometer, Fuel & Status
    odometer        = models.PositiveIntegerField(null=True, blank=True)
    fuel_level      = models.CharField(
        max_length=10, choices=FUEL_CHOICES, default='1/2')

    STATUS_CHOICES = [
        ('pass',      'Pass / Safe'),
        ('attention', 'Needs Attention'),
        ('fail',       'Failed / Unsafe'),
    ]
    driver_name     = models.CharField(max_length=100, blank=True, null=True, verbose_name='Driver / User Name')
    overall_status  = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pass', verbose_name='Overall Inspection Status')

    # Customer signature
    customer_signed         = models.BooleanField(default=False, verbose_name='Customer Signed')
    customer_signature_note = models.CharField(max_length=255, blank=True, null=True, verbose_name='Signature Note')

    # Exterior remarks
    exterior_remarks = models.TextField(blank=True)

    # Meta
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.inspection_number:
            from jobcard_app.utils import generate_voucher_number
            self.inspection_number = generate_voucher_number('Vehicle Inspection', VehicleInspection, 'inspection_number', default_prefix='VI-')

        if isinstance(self.inspection_date, str):
            self.inspection_date = datetime.strptime(
                self.inspection_date,
                "%Y-%m-%d"
            ).date()

        super().save(*args, **kwargs)

    @property
    def job_card(self):
        return self.jobcard

    @job_card.setter
    def job_card(self, value):
        self.jobcard = value

    def __str__(self):
        return f"{self.inspection_number} — {self.vehicle}"

    class Meta:
        ordering = ['-inspection_date', '-created_on']
        verbose_name        = 'Vehicle Inspection'
        verbose_name_plural = 'Vehicle Inspections'


class ExteriorDamage(models.Model):
    """One record per damage marker on the vehicle diagram"""

    DAMAGE_TYPE_CHOICES = [
        ('dent',    'Dent'),
        ('scratch', 'Scratch'),
        ('paint',   'Paint Damage'),
        ('crack',   'Crack'),
        ('missing', 'Missing Part'),
    ]

    ZONE_CHOICES = [
        ('front',       'Front Bumper'),
        ('bonnet',      'Bonnet'),
        ('front_left',  'Front Left'),
        ('front_right', 'Front Right'),
        ('roof',        'Roof'),
        ('door_left',   'Door Panel (Left)'),
        ('door_right',  'Door Panel (Right)'),
        ('rear_left',   'Rear Left'),
        ('rear_right',  'Rear Right'),
        ('boot',        'Boot / Trunk'),
        ('rear',        'Rear Bumper'),
        ('underbody',   'Underbody'),
    ]

    inspection  = models.ForeignKey(
        VehicleInspection, on_delete=models.CASCADE,
        related_name='exterior_damages')
    zone        = models.CharField(max_length=30, choices=ZONE_CHOICES)
    damage_type = models.CharField(max_length=20, choices=DAMAGE_TYPE_CHOICES)
    notes       = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.get_zone_display()} — {self.get_damage_type_display()}"

    class Meta:
        ordering = ['zone']


class InteriorInspection(models.Model):
    """Interior condition ratings — one record per inspection"""

    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('na',   'N/A'),
    ]

    inspection       = models.OneToOneField(
        VehicleInspection, on_delete=models.CASCADE,
        related_name='interior')

    dashboard        = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    seats            = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    steering_wheel   = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    ac_system        = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    audio_system     = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    windows          = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    seat_belts       = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    floor_carpet     = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    headliner        = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    door_panels      = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')

    def __str__(self):
        return f"Interior — {self.inspection.inspection_number}"


class MechanicalInspection(models.Model):
    """Mechanical condition ratings — one record per inspection"""

    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('na',   'N/A'),
    ]

    inspection = models.OneToOneField(
        VehicleInspection, on_delete=models.CASCADE,
        related_name='mechanical')

    # Engine
    oil_leak        = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    coolant_leak    = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    abnormal_noise  = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')

    # Brakes
    brake_pad       = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    brake_disc      = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')

    # Suspension
    shock_absorbers = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    bushes          = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')

    # Electrical
    battery         = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    starter         = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    lights          = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')

    # Tyres & Wheels
    tyre_fl         = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Front Left Tyre')
    tyre_fr         = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Front Right Tyre')
    tyre_rl         = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Rear Left Tyre')
    tyre_rr         = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Rear Right Tyre')
    tyre_spare      = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Spare Tyre')

    # Fluid Levels & Exhaust
    brake_fluid     = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Brake Fluid Level')
    steering_fluid  = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Power Steering Fluid')
    washer_fluid    = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Washer Fluid Level')
    exhaust_system  = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good', verbose_name='Exhaust System')

    def __str__(self):
        return f"Mechanical — {self.inspection.inspection_number}"


class AccessoriesInspection(models.Model):
    """Accessories checklist — one record per inspection"""

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('missing',   'Missing'),
        ('damaged',   'Damaged'),
    ]

    inspection        = models.OneToOneField(
        VehicleInspection, on_delete=models.CASCADE,
        related_name='accessories')

    spare_wheel       = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    tool_kit          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    service_book      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    remote_key        = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    safety_triangle   = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    floor_mat         = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    jack              = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    fire_extinguisher = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    first_aid_kit     = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')

    def get_available_count(self):
        fields = ['spare_wheel','tool_kit','service_book','remote_key',
                  'safety_triangle','floor_mat','jack','fire_extinguisher','first_aid_kit']
        return sum(1 for f in fields if getattr(self, f) == 'available')

    def get_missing_count(self):
        fields = ['spare_wheel','tool_kit','service_book','remote_key',
                  'safety_triangle','floor_mat','jack','fire_extinguisher','first_aid_kit']
        return sum(1 for f in fields if getattr(self, f) == 'missing')

    def get_damaged_count(self):
        fields = ['spare_wheel','tool_kit','service_book','remote_key',
                  'safety_triangle','floor_mat','jack','fire_extinguisher','first_aid_kit']
        return sum(1 for f in fields if getattr(self, f) == 'damaged')

    def __str__(self):
        return f"Accessories — {self.inspection.inspection_number}"


class InspectionFinding(models.Model):
    """Customer complaints and technician findings"""

    TYPE_CHOICES = [
        ('complaint', 'Customer Complaint'),
        ('finding',   'Technician Finding'),
    ]

    inspection    = models.ForeignKey(
        VehicleInspection, on_delete=models.CASCADE,
        related_name='findings')
    finding_type  = models.CharField(max_length=15, choices=TYPE_CHOICES)
    description   = models.TextField()
    order         = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.get_finding_type_display()} — {self.description[:50]}"

    class Meta:
        ordering = ['finding_type', 'order']
# ─────────────────────────────────────────────────────────────
# ADD TO: jobcard_app/models.py
# Replace the old DeliveryNote model with this complete version
# ─────────────────────────────────────────────────────────────

class DeliveryNote(models.Model):

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('cash',   'Cash'),
        ('card',   'Card'),
        ('bank',   'Bank Transfer'),
        ('credit', 'Credit'),
        ('online', 'Online'),
    ]

    CONDITION_CHOICES = [
        ('Excellent', 'Excellent'),
        ('Good',      'Good'),
        ('Fair',      'Fair'),
        ('Poor',      'Poor'),
    ]

    FUEL_CHOICES = [
        ('Empty', 'Empty'),
        ('1/4',   '1/4'),
        ('1/2',   '1/2'),
        ('3/4',   '3/4'),
        ('Full',  'Full'),
    ]

    # ── Auto Number ───────────────────────────────────────────
    delivery_number = models.CharField(
        max_length=20, unique=True, blank=True,
        help_text='Auto-generated: DN-00001')

    # ── Links ─────────────────────────────────────────────────
    jobcard  = models.ForeignKey(
        'JobCard', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='delivery_notes')
    quotation = models.ForeignKey(
        'Quotation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='delivery_notes')
    estimate  = models.ForeignKey(
        'Estimate', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='delivery_notes')
    customer  = models.ForeignKey(
        'accounts_app.LedgerCreation',
        on_delete=models.PROTECT, related_name='delivery_notes')
    vehicle   = models.ForeignKey(
        'WorkshopVehicle', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='delivery_notes')
    advisor = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='delivery_notes_advised')
    technician = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='delivery_notes_tech')

    # ── Header ────────────────────────────────────────────────
    date            = models.DateField()
    delivery_time   = models.TimeField(null=True, blank=True)
    status          = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_mode    = models.CharField(
        max_length=20, choices=PAYMENT_MODE_CHOICES,
        blank=True, null=True)
    contact_number  = models.CharField(max_length=20, blank=True)
    vehicle_type    = models.CharField(max_length=50, blank=True)
    reg_number      = models.CharField(max_length=30, blank=True)
    driver_name     = models.CharField(max_length=150, blank=True)
    header_remarks  = models.CharField(max_length=200, blank=True)

    # ── Vehicle Condition ─────────────────────────────────────
    exterior_condition   = models.CharField(
        max_length=20, choices=CONDITION_CHOICES, blank=True)
    interior_condition   = models.CharField(
        max_length=20, choices=CONDITION_CHOICES, blank=True)
    fuel_level_out       = models.CharField(
        max_length=10, choices=FUEL_CHOICES, blank=True)
    accessories_returns  = models.CharField(max_length=30, blank=True)
    vehicle_cleanliness  = models.CharField(max_length=30, blank=True)
    odometer_out         = models.PositiveIntegerField(null=True, blank=True)
    condition_remarks    = models.TextField(blank=True)

    # ── Checklist ─────────────────────────────────────────────
    work_completed    = models.BooleanField(default=False)
    quality_checked   = models.BooleanField(default=False)
    road_test         = models.BooleanField(default=False)
    vehicle_washed    = models.BooleanField(default=False)
    spare_wheel       = models.BooleanField(default=False)
    tool_kit          = models.BooleanField(default=False)
    documents_returned = models.BooleanField(default=False)

    # ── Financials ────────────────────────────────────────────
    discount         = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    tax_percent      = models.DecimalField(
        max_digits=5, decimal_places=2, default=0)
    advance_received = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    # ── Notes ─────────────────────────────────────────────────
    notes            = models.TextField(blank=True)
    customer_signed  = models.BooleanField(default=False)

    # ── Meta ──────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            from jobcard_app.utils import generate_voucher_number
            self.delivery_number = generate_voucher_number('Delivery Note', DeliveryNote, 'delivery_number', default_prefix='DN-')
        super().save(*args, **kwargs)

    def get_parts_total(self):
        return sum(
            float(i.quantity) * float(i.rate)
            for i in self.parts.all())

    def get_labour_total(self):
        return sum(
            float(i.hours) * float(i.rate)
            for i in self.labours.all())

    def get_subtotal(self):
        return self.get_parts_total() + self.get_labour_total()

    def get_tax_amount(self):
        return self.get_subtotal() * float(self.tax_percent) / 100

    def get_grand_total(self):
        return (self.get_subtotal()
                - float(self.discount)
                + self.get_tax_amount())

    def get_balance(self):
        return self.get_grand_total() - float(self.advance_received)

    def __str__(self):
        return f"{self.delivery_number} — {self.customer}"

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Delivery Note'
        verbose_name_plural = 'Delivery Notes'


# ── Completed Services ────────────────────────────────────────
class DeliveryService(models.Model):

    STATUS_CHOICES = [
        ('Completed',   'Completed'),
        ('In Progress', 'In Progress'),
        ('Pending',     'Pending'),
    ]

    delivery_note = models.ForeignKey(
        DeliveryNote, on_delete=models.CASCADE,
        related_name='services')
    description   = models.CharField(max_length=300)
    quantity      = models.DecimalField(
        max_digits=8, decimal_places=2, default=1)
    status        = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Completed')
    remarks       = models.CharField(max_length=200, blank=True)
    order         = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['order']


# ── Spare Parts Used ──────────────────────────────────────────
class DeliveryPart(models.Model):

    UNIT_CHOICES = [
        ('No',  'No'),
        ('Ltr', 'Ltr'),
        ('Kg',  'Kg'),
        ('Pkt', 'Pkt'),
        ('Set', 'Set'),
    ]

    delivery_note = models.ForeignKey(
        'DeliveryNote', on_delete=models.CASCADE,
        related_name='parts')

    # ── Item Master FK ────────────────────────────────────
    item = models.ForeignKey(
        'item_master.Item',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='delivery_parts',
        verbose_name='Item')

    name      = models.CharField(max_length=300)        # snapshot of item name
    item_code = models.CharField(max_length=100, blank=True)
    quantity  = models.DecimalField(max_digits=10, decimal_places=3, default=1)
    unit      = models.CharField(max_length=10, choices=UNIT_CHOICES, default='No')
    rate      = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    order     = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']


# ── Labour Charges ────────────────────────────────────────────
class DeliveryLabour(models.Model):

    delivery_note = models.ForeignKey(
        DeliveryNote, on_delete=models.CASCADE,
        related_name='labours')
    technician = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='delivery_labour_entries')
    description = models.CharField(max_length=300)
    hours       = models.DecimalField(
        max_digits=6, decimal_places=2, default=1)
    rate        = models.DecimalField(
        max_digits=12, decimal_places=3, default=0)
    amount      = models.DecimalField(
        max_digits=12, decimal_places=3, default=0)
    order       = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        self.amount = float(self.hours or 0) * float(self.rate or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['order']

# ─────────────────────────────────────────────────────────────
# ADD TO: jobcard_app/models.py
# Replace old Invoice model with this complete version
# ─────────────────────────────────────────────────────────────

class Invoice(models.Model):

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('sent',      'Sent'),
        ('paid',      'Paid'),
        ('partial',   'Partially Paid'),
        ('overdue',   'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_MODE_CHOICES = [
        ('cash',   'Cash'),
        ('bank',   'Bank Transfer'),
        ('cheque', 'Cheque'),
        ('card',   'Credit Card'),
        ('pdc',    'PDC'),
    ]

    # ── Auto Number ───────────────────────────────────────────
    invoice_number = models.CharField(
        max_length=20, unique=True, blank=True,
        help_text='Auto-generated: INV-00001')

    # ── Links ─────────────────────────────────────────────────
    jobcard      = models.ForeignKey(
        'JobCard', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices')
    quotation     = models.ForeignKey(
        'Quotation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices')
    estimate      = models.ForeignKey(
        'Estimate', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices')
    delivery_note = models.ForeignKey(
        'DeliveryNote', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices')
    customer      = models.ForeignKey(
        'accounts_app.LedgerCreation',
        on_delete=models.PROTECT,
        related_name='ws_invoices')
    vehicle       = models.ForeignKey(
        'WorkshopVehicle', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices')
    advisor = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invoices_advised')

    # ── Header ────────────────────────────────────────────────
    invoice_date     = models.DateField()
    due_date         = models.DateField(null=True, blank=True)
    status           = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_mode     = models.CharField(
        max_length=20, choices=PAYMENT_MODE_CHOICES,
        default='cash', blank=True)

    # ── Customer extra info ───────────────────────────────────
    customer_mobile  = models.CharField(max_length=30, blank=True)
    customer_address = models.TextField(blank=True)
    vehicle_model    = models.CharField(max_length=100, blank=True)

    # ── Financials ────────────────────────────────────────────
    discount_pct   = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Discount %')
    amount_paid    = models.DecimalField(
        max_digits=12, decimal_places=2, default=0)
    notes          = models.TextField(blank=True)

    # ── Meta ──────────────────────────────────────────────────
    is_active  = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from jobcard_app.utils import generate_voucher_number
            self.invoice_number = generate_voucher_number('Invoice', Invoice, 'invoice_number', default_prefix='INV-')
        super().save(*args, **kwargs)

    # ── Totals ────────────────────────────────────────────────
    def get_parts_subtotal(self):
        return sum(float(i.quantity) * float(i.unit_price) * (1 - float(i.discount_pct) / 100)
                   for i in self.parts.all())

    def get_parts_tax(self):
        return sum(
            float(i.quantity) * float(i.unit_price) *
            (1 - float(i.discount_pct) / 100) *
            float(i.tax_percent) / 100
            for i in self.parts.all())

    def get_parts_total(self):
        return self.get_parts_subtotal() + self.get_parts_tax()

    def get_labour_subtotal(self):
        return sum(float(i.hours) * float(i.rate)
                   for i in self.labours.all())

    def get_labour_tax(self):
        return sum(
            float(i.hours) * float(i.rate) *
            float(i.tax_percent) / 100
            for i in self.labours.all())

    def get_labour_total(self):
        return self.get_labour_subtotal() + self.get_labour_tax()

    def get_other_subtotal(self):
        return sum(float(i.amount) for i in self.other_charges.all())

    def get_other_tax(self):
        return sum(
            float(i.amount) * float(i.tax_percent) / 100
            for i in self.other_charges.all())

    def get_other_total(self):
        return self.get_other_subtotal() + self.get_other_tax()

    def get_subtotal(self):
        return (self.get_parts_subtotal() +
                self.get_labour_subtotal() +
                self.get_other_subtotal())

    def get_total_tax(self):
        return (self.get_parts_tax() +
                self.get_labour_tax() +
                self.get_other_tax())

    def get_grand_total(self):
        before_disc = self.get_subtotal() + self.get_total_tax()
        disc_amt    = before_disc * float(self.discount_pct) / 100
        return before_disc - disc_amt

    def get_balance_due(self):
        return self.get_grand_total() - float(self.amount_paid)

    def update_status(self):
        paid  = float(self.amount_paid)
        grand = self.get_grand_total()
        if paid <= 0:
            self.status = 'sent'
        elif paid >= grand:
            self.status = 'paid'
        else:
            self.status = 'partial'
        self.save()

    def __str__(self):
        return f"{self.invoice_number} — {self.customer}"

    class Meta:
        ordering = ['-created_on']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'


# ── Invoice Parts ─────────────────────────────────────────────
class InvoicePart(models.Model):
    invoice      = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='parts')
    item_ref     = models.CharField(max_length=50, blank=True, null=True)
    item_code    = models.CharField(max_length=100, blank=True)
    description  = models.CharField(max_length=300)
    quantity     = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit         = models.CharField(max_length=20, default='Pcs', blank=True)
    unit_price   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_percent  = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    order        = models.PositiveIntegerField(default=0)

    def get_base(self):
        return float(self.quantity) * float(self.unit_price) * (1 - float(self.discount_pct)/100)

    def get_tax_amount(self):
        return self.get_base() * float(self.tax_percent) / 100

    def total_price(self):
        return self.get_base() + self.get_tax_amount()

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['order', 'id']


# ── Invoice Labour ────────────────────────────────────────────
class InvoiceLabour(models.Model):
    invoice     = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='labours')
    description = models.CharField(max_length=300)
    technician = models.ForeignKey(
        'fleet_app.Staff', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='invoice_labours')
    hours       = models.DecimalField(max_digits=6, decimal_places=2, default=1)
    rate        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=8)
    order       = models.PositiveIntegerField(default=0)

    def get_base(self):
        return float(self.hours) * float(self.rate)

    def get_tax_amount(self):
        return self.get_base() * float(self.tax_percent) / 100

    def total_price(self):
        return self.get_base() + self.get_tax_amount()

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['order', 'id']


# ── Invoice Other Charges ─────────────────────────────────────
class InvoiceOtherCharge(models.Model):
    invoice     = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name='other_charges')
    description = models.CharField(max_length=300)
    amount      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    order       = models.PositiveIntegerField(default=0)

    def get_tax_amount(self):
        return float(self.amount) * float(self.tax_percent) / 100

    def total_price(self):
        return float(self.amount) + self.get_tax_amount()

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['order', 'id']