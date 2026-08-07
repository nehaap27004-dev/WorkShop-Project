from django.db import models
from django.core.validators import MinValueValidator
from accounts_app.models import LedgerCreation, PaymentBillDetails, ReceiptBillDetails
from item_master.models import Customer
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta
import datetime

class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)    
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    

class Manufacturer(models.Model):
    manufacturer_name = models.CharField(max_length=100, unique=True)
    manufacturer_logo = models.ImageField(upload_to='manufacturer_logos/', null=True, blank=True)

    # single Vehicle Type per manufacturer
    vehicle_type = models.ForeignKey(
        'VehicleCategory',
        on_delete=models.PROTECT,
        related_name='manufacturers',
        null=True,
        blank=True,
        verbose_name="Vehicle Type"
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.manufacturer_name

    class Meta:
        verbose_name = "Manufacturer"
        verbose_name_plural = "Manufacturers"
        ordering = ['manufacturer_name']

 
        
class VehicleCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.category_name

    class Meta:
        verbose_name = "Vehicle Category"
        verbose_name_plural = "Vehicle Categories" 
        ordering = ['category_name'] 
        
class VehicleModel(models.Model):
    FUEL_TYPES = [
        ('Gasoline', 'Gasoline'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('Full Hybrid', 'Full Hybrid'),
        ('Plug-in Hybrid Diesel', 'Plug-in Hybrid Diesel'),
        ('Plug-in Hybrid Gasoline', 'Plug-in Hybrid Diesel Gasoline'),
        ('CNG', 'CNG'),
        ('LPG', 'LPG'),
        ('Hydrogen', 'Hydrogen'),
        
    ]

    TRANSMISSION_TYPES = [
        ('Manual', 'Manual'),
        ('Automatic', 'Automatic'),
        ('Semi-Automatic', 'Semi-Automatic'),
    ]


    model_name = models.CharField(max_length=255)
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT)  # Foreign key to Manufacturer
    vehicle_category = models.ForeignKey(VehicleCategory, on_delete=models.PROTECT)  # Foreign key to VehicleCategory
    seat_number = models.IntegerField(default=0, null=True, blank=True)
    door_number = models.IntegerField(default=0, null=True, blank=True)
    model_colour = models.CharField(max_length=50, null=True, blank=True)
    model_range = models.IntegerField(default=0, null=True, blank=True)
    model_year = models.IntegerField(default=0, null=True, blank=True)  # Year as a positive integer
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPES, default='Gasoline')  # Fuel type with choices
    CO2_emission = models.DecimalField(max_digits=6, decimal_places=3, default=0)  # CO2 emission in g/km
    CO2_standard = models.CharField(max_length=50, null=True, blank=True)  
    model_transmission = models.CharField(max_length=20, choices=TRANSMISSION_TYPES, default='Manual')  # Transmission type with choices
    model_power = models.DecimalField(max_digits=6, decimal_places=3, default=0)  # Power in kW
    model_horse_power = models.DecimalField(max_digits=6, decimal_places=3, default=0)  # Horsepower
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.manufacturer.manufacturer_name} - {self.model_name} "    
    
    class Meta:
        verbose_name = "Vehicle Model"
        verbose_name_plural = "Vehicle Models" 
        ordering = ['model_name']
        constraints = [
            models.UniqueConstraint(fields=['manufacturer', 'model_name'], name='unique_model_per_manufacturer')
        ]


class VehicleVariant(models.Model):
    variant_name = models.CharField(max_length=255)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, related_name='variants')
    engine_code = models.CharField(max_length=100, blank=True, null=True)
    trim = models.CharField(max_length=100, blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle_model.manufacturer.manufacturer_name} {self.vehicle_model.model_name} {self.variant_name}"

    class Meta:
        verbose_name = "Vehicle Variant"
        verbose_name_plural = "Vehicle Variants"
        ordering = ['variant_name']
        constraints = [
            models.UniqueConstraint(fields=['vehicle_model', 'variant_name'], name='unique_variant_per_model')
        ]


class VehicleRegistration(models.Model):
    variant = models.ForeignKey(VehicleVariant, on_delete=models.PROTECT, related_name='registrations')
    registration_number = models.CharField(max_length=30, unique=True)
    registration_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    chassis_number = models.CharField(max_length=50, blank=True, null=True)
    engine_number = models.CharField(max_length=50, blank=True, null=True)
    document = models.FileField(upload_to='vehicle_docs/registrations/', blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.registration_number

    class Meta:
        verbose_name = "Vehicle Registration"
        verbose_name_plural = "Vehicle Registrations"
        ordering = ['registration_number']
        constraints = [
            models.UniqueConstraint(fields=['variant', 'registration_number'], name='unique_registration_per_variant')
        ]


class FleetCustomer(models.Model):
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
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
        
    def __str__(self):
        return self.customer_name
    
    class Meta:
        verbose_name = "Fleet Customer"
        verbose_name_plural = "Fleet Customers"
        ordering = ['customer_name']
        
#supplier company        
class RentalCompany(models.Model):
    company_name = models.CharField(max_length=255, help_text="Name of the rental company")
    company_logo = models.ImageField(upload_to='rentalcompany_logos/', null=True, blank=True)
    company_mobile = models.CharField(max_length=20, help_text="Primary contact person")
    company_phone = models.CharField(null=True, blank=True,max_length=20, help_text="Phone number")
    company_email = models.EmailField(help_text="Email address")
    company_address_1 = models.TextField(null=True, blank=True,help_text="Address of the company") 
    company_address_2 = models.TextField(null=True, blank=True, help_text="Address of the company")
    company_country = models.CharField(null=True, blank=True,max_length=255, help_text="Country of the company")
    company_state = models.CharField(null=True, blank=True,max_length=255, help_text="State of the company") 
    company_city = models.CharField(null=True, blank=True,max_length=255, help_text="City of the company") 
    company_zipcode = models.CharField(null=True, blank=True,max_length=255, help_text="Zipcode of the company")
    company_website = models.URLField(null=True, blank=True, help_text="Company website")
    company_description = models.TextField(null=True, blank=True, help_text="Company description")
    company_VAT = models.CharField(null=True, blank=True,max_length=255, help_text="Company VAT number")
    company_TRN_or_CRN = models.CharField(null=True, blank=True,max_length=255, help_text="Company TRN or CRN number")
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    def __str__(self):
        return self.company_name
    
    class Meta:
        db_table = 'RentalCompany'
        verbose_name_plural = 'RentalCompany'            
        

class StaffCategory(models.Model):
    name = models.CharField(max_length=100)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name        

        
class Driver(models.Model):
    driver_name = models.CharField(max_length=255)  # Driver's name
    driver_company = models.ForeignKey(RentalCompany, on_delete=models.PROTECT, null=True, blank=True)  # Foreign key to RentalCompany
    driver_address = models.TextField(max_length=255, null=True, blank=True)  # Driver's address
    driver_email = models.EmailField(unique=True, null=True, blank=True)  # Driver's email, unique to prevent duplicates
    driver_mobile = models.CharField(max_length=15, null=True, blank=True)  # Driver's mobile number
    driver_phone = models.CharField(max_length=15, null=True, blank=True)  # Optional field for landline/phone number
    driver_license_no = models.CharField(max_length=255, null=True, blank=True)  # Driver's license number
    driver_license_expiry_date = models.DateField(null=True, blank=True)  # Driver's license expiry date
    residential_id_no = models.CharField(max_length=255, null=True, blank=True, unique=True)  # Driver's residential ID number
    residential_id_expiry_date = models.DateField(null=True, blank=True)  # Driver's residential ID expiry date
    def __str__(self):
        return self.driver_name

    class Meta:
        verbose_name = "Driver"
        verbose_name_plural = "Drivers"
        ordering = ['driver_name']   
        
class Staff(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('Permanent', 'Permanent'),
        ('Temporary', 'Temporary'),
        ('Contract', 'Contract'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Resigned', 'Resigned'),
        ('Terminated', 'Terminated'),
    ]
    
    LICENSE_TYPE_CHOICES = [
        ('Private', 'Private'),
        ('Commercial', 'Commercial'),
        ('Heavy Vehicle', 'Heavy Vehicle'),
        ('Motorcycle', 'Motorcycle'),
    ]

    staff_category = models.ForeignKey(StaffCategory, on_delete=models.SET_NULL, null=True, blank=True)
    staff_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    civil_id_or_passport_no = models.CharField(max_length=50)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=10, choices=EMPLOYMENT_TYPE_CHOICES, null=True, blank=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    allowances = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    bank_account_no = models.CharField(max_length=30, null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, null=True, blank=True)
    emergency_contact_number = models.CharField(max_length=20, null=True, blank=True)
    visa_expiry_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(null=True, blank=True)
    
    passport_expiry_date = models.DateField(null=True, blank=True)
    resident_id_number = models.CharField(max_length=50, null=True, blank=True)
    resident_id_expiry_date = models.DateField(null=True, blank=True)
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, null=True, blank=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)
    staff_image = models.ImageField(upload_to='staff_images/', null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    

    def __str__(self):
        return f"{self.staff_id} - {self.full_name}"
            

# Model for License Plate Code
class LicensePlateCode(models.Model):
    code = models.CharField(max_length=10, unique=True)  
    description = models.CharField(max_length=100, blank=True, null=True)  
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = "License Plate Code"
        verbose_name_plural = "License Plate Codes"
        ordering = ['code']

class Vehicle(models.Model):

    customer = models.ForeignKey(
        'accounts_app.LedgerCreation',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='vehicles',
        verbose_name="Customer / Owner"
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vehicles',
        verbose_name='Manufacturer'
    )
    variant = models.ForeignKey(
        'VehicleVariant',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vehicles',
        verbose_name='Vehicle Variant'
    )
    registration = models.ForeignKey(
        'VehicleRegistration',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='vehicles',
        verbose_name='Vehicle Registration'
    )
    FUEL_CHOICES = [
        ('petrol',   'Petrol'),
        ('diesel',   'Diesel'),
        ('electric', 'Electric'),
        ('hybrid',   'Hybrid'),
        ('cng',      'CNG'),
    ]

    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES,blank=True, null=True)
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT)  # Foreign key to VehicleModel
    vehicle_name = models.CharField(max_length=255, null=True, blank=True)  
    license_plate_code = models.ForeignKey(LicensePlateCode, on_delete=models.PROTECT, null=True, blank=True)  # ForeignKey to LicensePlateCode
    license_plate_number = models.CharField(max_length=50, null=True, blank=True)
    vehicle_image = models.ImageField(upload_to='vehicle_image/', null=True, blank=True)
    vehicle_registration_date = models.DateField(null=True, blank=True)  # Vehicle registration date
    vehicle_cancellation_date = models.DateField(null=True, blank=True)  # Optional cancellation date
    RC_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Registration Certificate number (unique)
    RC_file = models.FileField(upload_to='RC_upload/', null=True, blank=True)
    RC_expiry_date = models.DateField(null=True, blank=True)  # Registration Certificate expiry date
    chassis_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Chassis number (unique)
    last_odometer = models.PositiveIntegerField(validators=[MinValueValidator(0)], null=True, blank=True)  # Odometer reading (cannot be negative)
    #we use vehicle_category as vehicle type in templates
    vehicle_category = models.ForeignKey(VehicleCategory, on_delete=models.PROTECT)  # Foreign key to VehicleCategory
    engine_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Engine number (unique)
    
    
    insurance_policy_number = models.CharField(max_length=100,
                                   blank=True, null=True)
    insurance_expiry_date   = models.DateField(blank=True, null=True)
    insurance_certificate   = models.FileField(
                                   upload_to='vehicle_docs/insurance/',
                                   blank=True, null=True)
 
    registration_renewed_date = models.DateField(blank=True, null=True)
    registration_expiry_date  = models.DateField(blank=True, null=True)
    registration_document     = models.FileField(
                                     upload_to='vehicle_docs/registration/',
                                     blank=True, null=True)
 
    fitness_test_date          = models.DateField(blank=True, null=True)
    fitness_test_expiry_date   = models.DateField(blank=True, null=True)
    fitness_test_certificate   = models.FileField(
                                      upload_to='vehicle_docs/fitness/',
                                      blank=True, null=True)
 
    last_service_date     = models.DateField(blank=True, null=True)
    service_due_date       = models.DateField(blank=True, null=True)
    service_interval_km    = models.PositiveIntegerField(
                                  blank=True, null=True,
                                  help_text="e.g. 5000 (service every 5000 km)")
 
    model_year = models.IntegerField(null=True, blank=True)  # Manufacturing year
    capacity = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Capacity (e.g. tonnage)
    purchase_value = models.DecimalField(max_digits=20, decimal_places=3, null=True, blank=True)  # Purchase value
    vat = models.BooleanField(default=False)  # VAT applicable
    description = models.TextField(null=True, blank=True)  # Additional description

    is_owned = models.BooleanField(default=True)
    supplier = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.SET_NULL, null=True, blank=True)

    STATUS_CHOICES = [
        ('1', 'Free'),
        ('2', 'Hired'),
        ('3', 'Service'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='1', null=True, blank=True)

    replacement_value = models.DecimalField(max_digits=20, decimal_places=3, null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    

    def __str__(self):
        return self.vehicle_name or "Unnamed Vehicle"

    class Meta:
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ['model'] 
        
            

      #supplier vehicle  
class RentalCompanyVehicle(models.Model):
    FUEL_TYPES = [
        ('Gasoline', 'Gasoline'),
        ('Diesel', 'Diesel'),
        ('Electric', 'Electric'),
        ('Full Hybrid', 'Full Hybrid'),
        ('Plug-in Hybrid Diesel', 'Plug-in Hybrid Diesel'),
        ('Plug-in Hybrid Gasoline', 'Plug-in Hybrid Diesel Gasoline'),
        ('CNG', 'CNG'),
        ('LPG', 'LPG'),
        ('Hydrogen', 'Hydrogen'),
        
    ]

    TRANSMISSION_TYPES = [
        ('Manual', 'Manual'),
        ('Automatic', 'Automatic'),
        ('Semi-Automatic', 'Semi-Automatic'),
    ]
    
    company = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, null=True, blank=True)
    vehicle_name = models.CharField(max_length=255, null=True, blank=True)  
    contact_person = models.CharField(max_length=255, help_text="Primary contact person", null=True, blank=True)
    vehicle_driver = models.ForeignKey(Driver, on_delete=models.PROTECT, null=True, blank=True) 
    vehicle_driver_mobile = models.CharField(max_length=15, help_text="Driver mobile number", null=True, blank=True)
    vehicle_manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, null=True, blank=True)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, null=True, blank=True) 
    model_colour = models.CharField(max_length=50, null=True, blank=True)
    model_year = models.IntegerField(null=True, blank=True)
    Vehicle_image = models.ImageField(upload_to='rentalcompany_vehicle/', null=True, blank=True)
    vehicle_category = models.ForeignKey(VehicleCategory, on_delete=models.PROTECT, help_text="Category of the vehicle", null=True, blank=True)
    license_plate_code = models.ForeignKey(LicensePlateCode, on_delete=models.PROTECT, null=True, blank=True)  # ForeignKey to LicensePlateCode
    license_plate_number = models.CharField(max_length=50, null=True, blank=True)
    RC_number = models.CharField(max_length=50, null=True, blank=True)
    RC_epx_date = models.DateField(null=True, blank=True)
    fuel_type = models.CharField(max_length=50, choices=FUEL_TYPES, default='Gasoline')
    vehicle_transmission = models.CharField(max_length=50, choices=TRANSMISSION_TYPES, default='Manual')
    chassis_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Chassis number (unique)
    last_odometer = models.PositiveIntegerField(validators=[MinValueValidator(0)], null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    def __str__(self):
        return f"{self.company} - {self.vehicle_model} ({self.vehicle_name})" 
        
    class Meta:
        db_table = 'RentalCompany_Vehicle'
        verbose_name_plural = 'RentalCompany_Vehicle'    
  
        
class Vendor(models.Model):
    
    VENDOR_TYPES = [
        ('General', 'General'),
        ('Service', 'Service'),
        
    ]
    
    vendor_name = models.CharField(max_length=255, help_text="Name of the rental company")
    vendor_type = models.CharField(max_length=50, choices=VENDOR_TYPES, default='General')
    vendor_image = models.ImageField(upload_to='workshop_images/', null=True, blank=True)
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
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    def __str__(self):
        return self.vendor_name
    
    class Meta:
        db_table = 'Fleet_Vendor'
        verbose_name_plural = 'Fleet_Vendor'        

class Vouchers(models.Model):
    VoucherType = models.CharField(max_length=50)
    VoucherName = models.CharField(max_length=100)
    Suffix = models.CharField(max_length=20, null=True, blank=True)
    Prefix = models.CharField(max_length=20, null=True, blank=True)
    MinLength = models.PositiveIntegerField(default=5)
    StartingNo = models.PositiveIntegerField(default=1)
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, null=True, blank=True, related_name='fleet_vouchers')
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    def get_next_voucher_number(self, model_cls=None, number_field=None):
        """Generate the next voucher number for this voucher type"""
        if model_cls and number_field:
            from jobcard_app.utils import generate_voucher_number
            return generate_voucher_number(self.VoucherType, model_cls, number_field, default_prefix=self.Prefix or "")

        from django.apps import apps
        from django.db.models import ForeignKey
        from django.db.models.deletion import PROTECT, SET_NULL
        
        all_voucher_numbers = []

        # Loop through all installed models
        for model in apps.get_models():
            # Check if model has both fields
            if hasattr(model, 'voucher_no') and hasattr(model, 'voucherType'):
                try:
                    # Ensure voucherType is a ForeignKey to THIS model
                    field = model._meta.get_field('voucherType')
                    if isinstance(field, ForeignKey) and field.remote_field.model == type(self):
                        # Only then try to query
                        vouchers = model.objects.filter(voucherType=self).values_list('voucher_no', flat=True)
                        all_voucher_numbers.extend(vouchers)
                except Exception:
                    continue  # skip any models that don't match cleanly

        # If no existing vouchers found
        if not all_voucher_numbers:
            current_number = self.StartingNo
        else:
            # Extract numbers safely
            max_number = self.StartingNo - 1
            for voucher_no in all_voucher_numbers:
                number_part = str(voucher_no)
                if self.Prefix:
                    number_part = number_part.replace(self.Prefix, '', 1)
                if getattr(self, 'Suffix'):
                    number_part = number_part.replace(self.Suffix, '')

                try:
                    number = int(''.join(filter(str.isdigit, number_part)))
                    max_number = max(max_number, number)
                except ValueError:
                    continue
            current_number = max_number + 1

        # Format with zero padding
        formatted_number = str(current_number).zfill(self.MinLength)

        # Handle None or empty Prefix/Suffix cleanly
        prefix = self.Prefix if self.Prefix else ""
        suffix = self.Suffix if hasattr(self, 'Suffix') and self.Suffix else ""

        # Construct final voucher number
        voucher_number = f"{prefix}{formatted_number}{suffix}"
        return voucher_number


    

    def __str__(self):
     return f"{self.VoucherName}"
        
class TimeSheet(models.Model):
    voucher_no = models.CharField(max_length=50, unique=True)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=8)
    vehicle_reg_no = models.CharField(max_length=20)
    vehicle_name = models.ForeignKey(Vehicle, on_delete=models.PROTECT, null=True, blank=True)
    project_location = models.CharField(max_length=100)
    client = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, null=True, blank=True)
    duration = models.CharField(max_length=20)
    PO_reference_no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    driver_name = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name='driver_name')
    operator_name = models.ForeignKey(Staff, on_delete=models.PROTECT, null=True, blank=True, related_name='operator_name')
    
    enable_header = models.BooleanField(default=True)
    enable_footer = models.BooleanField(default=True)
    enable_signature = models.BooleanField(default=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    

    def __str__(self):
        return f"TimeSheet for {self.vehicle_reg_no} - {self.date}"        
    
class TimeSheetDetail(models.Model):
    timesheet = models.ForeignKey(TimeSheet, related_name="details", on_delete=models.PROTECT)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_hours = models.DecimalField(max_digits=20, decimal_places=3, default=0.00)
    total_hours_worked = models.DecimalField(max_digits=20, decimal_places=3, default=0.00)
    ot = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True, default=0.00) 
    job_location = models.CharField(max_length=100, blank=True, null=True )
    signature = models.CharField(max_length=100, blank=True, null=True)
    
    
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"TimeSheetDetail for {self.timesheet.vehicle_reg_no} - {self.date}"
    
class FleetQuotation(models.Model):
    quotation_no = models.IntegerField(unique=True)
    company_name = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='fleet_quotations', blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_address = models.TextField(blank=True, null=True)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='fleet_quotations', blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    terms_and_condition = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.quotation_no:
            last_quotation = FleetQuotation.objects.order_by('-quotation_no').first()
            if last_quotation:
                self.quotation_no = last_quotation.quotation_no + 1
            else:
                self.quotation_no = 1
        super(FleetQuotation, self).save(*args, **kwargs)
    

    def __str__(self):
        return self.quotation_no
    
    
    
class FleetQuotationItem(models.Model):
    UNIT_CHOICES = [
        ('Hr', 'Hour'),
        ('Day', 'Day'),
        ('Month', 'Month'),
    ]

    vehicle_quotation = models.ForeignKey(FleetQuotation, on_delete=models.PROTECT, related_name='items')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name='fleet_quotation_items')
    details = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(default=1, null=True, blank=True)
    
    # Change these fields to be nullable and blank
    rate_per_hr = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, default=0)
    rate_per_day = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, default=0)
    rate_per_month = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True, default=0)
    
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='Hr', blank=True, null=True)
    no_of_unit = models.IntegerField(default=1, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
     return str(self.quotation_no)

    
class RepairAndMaintenance(models.Model):
    PAYMENT_MODES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('credit', 'Credit'),
    ]
    
    voucher_no = models.IntegerField(unique=True)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=10)
    bill_no = models.CharField(max_length=20)
    date = models.DateField()
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODES)
    party = models.CharField(max_length=100)
    reference_no = models.CharField(max_length=50, blank=True, null=True)
    VAT_no = models.CharField(max_length=50, blank=True, null=True)
    date_on_bill = models.DateField(blank=True, null=True)
    vehicle_name = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="repair_maintenance")
    vehicle_driver = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="vehicle_driver")
    grand_total_amount = models.DecimalField(max_digits=10, decimal_places=3)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no:
            last_voucher = RepairAndMaintenance.objects.order_by('-voucher_no').first()
            if last_voucher:
                self.voucher_no = last_voucher.voucher_no + 1
            else:
                self.voucher_no = 1
        super(RepairAndMaintenance, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.voucher_no} - {self.party}"


class RepairAndMaintenanceItem(models.Model):
    repair_and_maintenance = models.ForeignKey(RepairAndMaintenance, on_delete=models.PROTECT, related_name="items")
    narration = models.TextField(blank=True, null=True)
    bill_amount = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    VAT_amount = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Item for {self.repair_and_maintenance.voucher_no}"    
    
class FleetContract(models.Model):
    voucher_no = models.CharField(max_length=50, unique=True)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=7)
    contract_no = models.CharField(max_length=100, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    date = models.DateField()
    end_date = models.DateField()
    operator_1 = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name='operator_1', blank=True, null=True)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='contracts', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    
'''
class VehicleMaster(models.Model):

    customer = models.ForeignKey(
        'fleet_app.FleetCustomer',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vehicles'
    )
    vehicle_name = models.CharField(max_length=255)
    license_plate_code = models.CharField(max_length=50)
    license_plate_number = models.CharField(max_length=50)
    vehicle_driver = models.CharField(max_length=255)
    vehicle_category = models.CharField(max_length=255)
    RC_number = models.CharField(max_length=100)
    contract_no = models.CharField(max_length=100)
    contract_start_date = models.CharField(max_length=50)  # Store as CharField for report consistency
    contract_end_date = models.CharField(max_length=50)    # Store as CharField for report consistency
    customer_name = models.CharField(max_length=255)
    vehicle_image = models.ImageField(upload_to='vehicle_images/', null=True, blank=True)
    
    
    

    def __str__(self):
        return f"{self.vehicle_name} - {self.contract_no}"

    class Meta:
        verbose_name = "Vehicle Master"
        verbose_name_plural = "Vehicle Masters"
        ordering = ['vehicle_name']    
        
class Document(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file_path = models.FileField(upload_to='documents/', null=True, blank=True)
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    upload_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    reminder_date = models.DateTimeField(null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title        
       ''' 
        
class SimpleQuotation(models.Model):
    voucher_no = models.CharField(max_length=50, unique=True)
    quotation_no = models.CharField(max_length=100, blank=True, null=True)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=9)
    date = models.DateField(default=timezone.now)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='quotations')
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True)
    terms_and_condition = models.TextField(blank=True, null=True, default=(
            "Hire Period	: Start from the Mobilization to return back to Silver Line Yard in Al Rumais, Muscat.\n"
            "Offer Validity	: 7 Days from the Quotation Date.\n"
            "Minimum Hire	: One month.\n"
            "Payment Terms	: 60 Days Credit    \n"
            "Usage		: 10 Hrs per day basis \n"
            "Availability	: Subject to availability at the time of order\n"
            "Insurance	: Clients Responsibility\n"
            "Transportation	: Clients Responsibility\n"
            "Notes	: Any additional accessories and certificates not mentioned above will be charged              separately, if required.\n"
            "For order confirmation, please send the LPO and under sign the Rental Agreement with stamp to infooman@silverlinerental.com.\n"
            "Please mention our quotation reference number on the LPO.\n\n"
            "&nbsp;\n"
            "Terms & Conditions:\n"
            "&nbsp;\n"
            "1. Hire starts from the departure of the equipment from our yard and continues until its return in good condition and working order\n"
            "2. Loading and offloading of the equipment at the site under hirer & also all civil works related to this hire are the responsibility of the hirer and must be completed prior the delivery\n"
            "3. Gate pass/permissions required from any authority for delivering the equipment is responsible by the hirer\n"
            "4. Repair/maintenance is under Silver Line Global Business. (Sites Transport and Passes for Technician arranged by Hirer).\n"
            "5. Fuel by the hirer\n"
            "6. Fuel will be filled before starting the equipment. Breakdown due to airlock of the equipment and any damage/breakdown caused by the negligence on the part of the hirer will be charged on per call plus cost of parts and repairs.\n"
            "7. Use only good quality diesel in the equipment. Breakdown due to the usage of the contaminated diesel will be charged to the hirer.\n"
            "8. Off hire should be intimidated by e-mail (infooman@silverlinerental.com) at least 2 days prior to the off hire\n"
            "9. Hirer will be responsible in case of any theft from the site.\n"
            "10. Hirer must check oil/coolant/diesel levels before starting every day as per hirer’s responsibility.\n"
            "11. Commissioning and Decommissioning of the equipment by hirer. If hirer requested, Silver Line Rental will provide Engineer/Technician will be quoted separately.\n"
            "12. Silver Line Global Business will not be responsible for any consequential loss.\n"
            "13. Unless expressly agreed between the owner and the hirer, the equipment hired is for onshore use in the Oman only. Should the hirer remove hired equipment outside Oman, only the hirer is responsible for keeping the subject equipment and shall be charged for full replacement/repair cost in the event of loss or damage.\n"
            "14. Rental rates: a) Any hire duration completed below 7 days will be charged on daily rates. Monthly rate applies for minimum 30 days’ hire period. Only chargeable daily or weekly rate shall be advised in case of any early termination of the hire. \n"
            "b) Any hire period completed below the minimum guaranteed hire period for which a special rate was offered, the normal hire charges shall apply and the final invoice will be adjusted accordingly to reflect the rate difference from the hire start date.\n"
            "15. If the machines get held back in the site due to some reason after off-hire, Silverline reserves the right to invoice the machine till the machine is released from the site. The machine(s) will be invoiced as per the LPO.\n"
            "16. Silver line management will not hold any responsibility for the damages occurring by the usage of the equipment/operator on the worksite.\n"
            "17. The hirer is strictly not allowed to back charge if an unfortunate event like an accident, fire, delay in works caused by the machine, or the breakdowns caused due to   improper handling and usage of the machines.\n"
            "18. It is the sole responsibility of the hiring company that had issued the LPO, to report to the ROP, Silverline authorities, and other related departments in case of a theft. If the machine is lost or stolen after the hire, the hirer is responsible to pay the replacement value of the machine depicted in the hire contract, which will be provided to the hirer after the delivery. Silverline reserves the right to invoice the machines, till the replacement value is paid or the machines are returned to Silverline yard.\n"
            "19. The hirer responsible for damages of the equipment during the transportation if transportation under the hirer scope.\n"
            "20. In case of breakdown or major failure which unable to rectify at the site by Silver Line technician within 24 hours, then hirer need to arrange the transportation to silver line yard for the replacement of the machine, if equipment is available.   \n"
            "We would like to thank you for taking time to approach our company and giving us an opportunity to quote for your requirement. In case if any clarification is required, please feel free to contact us."
        ))
    remark = models.TextField(blank=True, null=True)
    attention = models.CharField(max_length=255, blank=True, null=True)
    attention_contact = models.CharField(max_length=255, blank=True, null=True)
    
    enable_header = models.BooleanField(default=True)
    enable_footer = models.BooleanField(default=True)
    enable_signature = models.BooleanField(default=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    

    def __str__(self):
        return f"Quotation {self.voucher_no} - {self.customer}"


class SimpleQuotationDetails(models.Model):
    PERIOD_CHOICES = [
        ('Hour', 'Hour'),
        ('Day', 'Day'),
        ('Week', 'Week'),
        ('Month', 'Month'),
    ]
    quotation = models.ForeignKey(SimpleQuotation, on_delete=models.CASCADE, related_name='details')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, null=True, blank=True, related_name='simple_quotation_details')
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    rent = models.DecimalField(max_digits=20, decimal_places=3)  
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=3)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='Hour', blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.rent})"   


class DeliveryContract(models.Model):
    VOUCHER_PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    
    INVOICE_TYPE_CHOICES = [
        ('simple', 'Simple'),
        ('complex', 'Complex'),
    ]
    
    # Basic fields (same as Invoice)
    voucher_no = models.CharField(max_length=100, unique=True)
    invoice_no = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=12)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='delivery_contracts', blank=True, null=True)
    is_taxable = models.BooleanField(default=True)
    
    payment_mode = models.CharField(max_length=10, choices=VOUCHER_PAYMENT_MODE_CHOICES, default='cash')
    supplier_ref = models.CharField(max_length=255, blank=True, null=True)
    other_ref = models.CharField(max_length=255, blank=True, null=True)
    buyer_order_no = models.CharField(max_length=255, blank=True, null=True)
    dated = models.CharField(max_length=100, blank=True, null=True)
    grand_total = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    IsCleared = models.BooleanField(default=False)
    
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE_CHOICES, default='complex')
    lpo_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    
    # NEW: Additional DeliveryContract-specific fields
    hire_contract_no = models.CharField(max_length=255, null=True, blank=True, )
    hire_contract_date = models.DateField(null=True, blank=True)
    salesman = models.ForeignKey('Staff', on_delete=models.SET_NULL, null=True, blank=True)
    ref_no = models.CharField(max_length=255, null=True, blank=True)
    onhire_date_time = models.DateTimeField(null=True, blank=True)
    site_contact_person = models.CharField(max_length=255, null=True, blank=True)
    contact_no = models.CharField(max_length=50, null=True, blank=True)
    offhire_date_time = models.DateTimeField(null=True, blank=True)
    delivery_person= models.CharField(max_length=255, null=True, blank=True)

    terms_and_condition = models.TextField(blank=True, null=True, default=(
        "Terms & Conditions:\n\n"
        "&nbsp;\n"
        "1. Hire starts from the departure of the equipment from our yard and continues until its return in good condition and working order\n\n"
        "2. Loading and offloading of the equipment at the site under hirer & also all civil works related to this hire are the responsibility of the hirer and must be completed prior the delivery\n\n"
        "3. Gate pass/permissions required from any authority for delivering the equipment is responsible by the hirer\n\n"
        "4. Repair/maintenance is under Silver Line Global Business. (Sites Transport and Passes for Technician arranged by Hirer).\n\n"
        "5. Fuel by the hirer\n\n"
        "6. Fuel will be filled before starting the equipment. Breakdown due to airlock of the equipment and any damage/breakdown caused by the negligence on the part of the hirer will be charged on per call plus cost of parts and repairs.\n\n"
        "7. Use only good quality diesel in the equipment. Breakdown due to the usage of the contaminated diesel will be charged to the hirer.\n\n"
        "8. Off hire should be intimidated by e-mail (infooman@silverlinerental.com) at least 2 days prior to the off hire\n\n"
        "9. Hirer will be responsible in case of any theft from the site.\n\n"
        "10. Hirer must check oil/coolant/diesel levels before starting every day as per hirer's responsibility.\n\n"
        "11. Commissioning and Decommissioning of the equipment by hirer. If hirer requested, Silver Line Rental will provide Engineer/Technician will be quoted separately.\n\n"
        "12. Silver Line Global Business will not be responsible for any consequential loss.\n\n"
        "13. Unless expressly agreed between the owner and the hirer, the equipment hired is for onshore use in the Oman only. Should the hirer remove hired equipment outside Oman, only the hirer is responsible for keeping the subject equipment and shall be charged for full replacement/repair cost in the event of loss or damage.\n\n"
        "14. Rental rates: a) Any hire duration completed below 7 days will be charged on daily rates. Monthly rate applies for minimum 30 days' hire period. Only chargeable daily or weekly rate shall be advised in case of any early termination of the hire.\n\n"
        "b) Any hire period completed below the minimum guaranteed hire period for which a special rate was offered, the normal hire charges shall apply and the final invoice will be adjusted accordingly to reflect the rate difference from the hire start date.\n\n"
        "15. If the machines get held back in the site due to some reason after off-hire, Silverline reserves the right to invoice the machine till the machine is released from the site. The machine(s) will be invoiced as per the LPO.\n\n"
        "16. Silver line management will not hold any responsibility for the damages occurring by the usage of the equipment/operator on the worksite.\n\n"
        "17. The hirer is strictly not allowed to back charge if an unfortunate event like an accident, fire, delay in works caused by the machine, or the breakdowns caused due to improper handling and usage of the machines.\n\n"
        "18. It is the sole responsibility of the hiring company that had issued the LPO, to report to the ROP, Silverline authorities, and other related departments in case of a theft. If the machine is lost or stolen after the hire, the hirer is responsible to pay the replacement value of the machine depicted in the hire contract, which will be provided to the hirer after the delivery. Silverline reserves the right to invoice the machines, till the replacement value is paid or the machines are returned to Silverline yard.\n\n"
        "19. The hirer responsible for damages of the equipment during the transportation if transportation under the hirer scope.\n\n"
        "20. In case of breakdown or major failure which unable to rectify at the site by Silver Line technician, then hirer need to arrange the transportation to silver line yard for the replacement of the machine, if equipment is available.\n\n"
        "21. Insurance for the equipment is hirer responsibility.\n\n"
        "22. The payment for rent shall be made in accordance with the mutual agreement of both parties, as outlined in the rental agreement.\n\n"
        "23. Silver Line Stickers and Service Stickers should not remove from the equipment.\n\n"
        "24. The hirer is responsible for informing the Silver Line in advance if the equipment is moved to other sites."
    ))
    
    enable_header = models.BooleanField(default=True)
    enable_footer = models.BooleanField(default=True)
    enable_signature = models.BooleanField(default=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    def __str__(self):
        return f"Delivery Contract #{self.voucher_no}"


class DeliveryContractDetails(models.Model):
    PERIOD_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
    ]
    
    delivery_contract = models.ForeignKey(DeliveryContract, on_delete=models.CASCADE, related_name='details')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    vehicle_model = models.CharField(max_length=255, null=True, blank=True)  # Stores model name + year
    description = models.TextField(null=True, blank=True)  # Editable description per line
    location = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=20, decimal_places=3)
    tax = models.DecimalField(max_digits=20, decimal_places=3)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=3)
    total_amount = models.DecimalField(max_digits=12, decimal_places=3)
    
    # Complex invoice fields
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit_rate = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    
    # NEW: IsCleared field to track which details have been invoiced
    IsCleared = models.BooleanField(default=False)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.vehicle} - {self.location} - {self.total_amount}"

    
class Invoice(models.Model):
    VOUCHER_PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    voucher_no = models.CharField(max_length=100, unique=True)
    invoice_no = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=2)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='invoice_customer', blank=True, null=True)
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name='invoice_ledger', blank=True, null=True)
    is_taxable = models.BooleanField(default=True)

    payment_mode = models.CharField(max_length=10, choices=VOUCHER_PAYMENT_MODE_CHOICES, default='cash')
    supplier_ref = models.CharField(max_length=255, blank=True, null=True)
    other_ref = models.CharField(max_length=255, blank=True, null=True)
    buyer_order_no = models.CharField(max_length=255, blank=True, null=True)
    dated = models.CharField(max_length=100, blank=True, null=True)  # Free text date entry if needed
    grand_total = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    IsCleared = models.BooleanField(default=False)

    invoice_type = models.CharField(max_length=10, choices=[('simple', 'Simple'), ('complex', 'Complex')], default='simple')
    lpo_date = models.DateField(null=True, blank=True)
    hire_contract_no = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    
    enable_header = models.BooleanField(default=True)
    enable_footer = models.BooleanField(default=True)
    enable_signature = models.BooleanField(default=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
            
        # Only auto-set IsCleared for NEW invoices (not existing ones)
        # This allows receipt processing to update IsCleared for existing invoices
        if self.pk is None:  # New invoice
            if self.payment_mode == 'Credit':
                self.IsCleared = False
            else:
                self.IsCleared = True

        super().save(*args, **kwargs)

    def is_locked(self):
        if self.payment_mode != "Credit":
            return False

        return ReceiptBillDetails.objects.filter(
            voucherType=self.voucherType,
            VoucherNo=self.voucher_no
        ).exists()    

    def __str__(self):
        return f"Invoice #{self.voucher_no}"


class InvoiceDetails(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='details')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    vehicle_model = models.CharField(max_length=255, null=True, blank=True)  # Stores model name + year
    description = models.TextField(null=True, blank=True)  # Editable description per line
    location = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=20, decimal_places=3)
    tax = models.DecimalField(max_digits=20, decimal_places=3)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=3)
    total_amount = models.DecimalField(max_digits=12, decimal_places=3)

    PERIOD_CHOICES = [
    ('hourly', 'Hourly'),
    ('daily', 'Daily'),
    ('monthly', 'Monthly'),
    ]
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit_rate = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle} - {self.location} - {self.total_amount}"    



    
    
class CompanyDocument(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="documents")
    name = models.CharField(max_length=255, help_text="Name this document")
    file = models.FileField(upload_to="company_documents/")
    reminder_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"    
    
class FleetHire(models.Model):
    VOUCHER_PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    voucher_no = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=1)
    supplier = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name="fleet_hires")
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.PROTECT, related_name="fleet_hires_ledger", blank=True, null=True)
    invoice_no = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField(default=timezone.now)
    payment_mode = models.CharField(max_length=10, choices=VOUCHER_PAYMENT_MODE_CHOICES, default='cash')
    IsCleared = models.BooleanField(default=False)
    hire_contract = models.CharField(max_length=255, blank=True, null=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    vat = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    other_charges = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.voucher_no and self.voucherType:
            self.voucher_no = self.voucherType.get_next_voucher_number()
        # Only auto-set IsCleared for NEW invoices (not existing ones)
        # This allows receipt processing to update IsCleared for existing invoices
        if self.pk is None:  # New invoice
            if self.payment_mode == 'Credit':
                self.IsCleared = False
            else:
                self.IsCleared = True

        super().save(*args, **kwargs)

    def is_locked(self):
        if self.payment_mode != "Credit":
            return False

        return PaymentBillDetails.objects.filter(
            voucherType=self.voucherType,
            VoucherNo=self.voucher_no
        ).exists()     

        

   

    def __str__(self):
        return f"FleetHire {self.voucher_no} - {self.supplier}"


class FleetHireDetails(models.Model):
    UNIT_CHOICES = [
        ('Hr', 'Hour'),
        ('Day', 'Day'),
        ('Month', 'Month'),
    ]
    fleet_hire = models.ForeignKey(FleetHire, on_delete=models.CASCADE, related_name="details")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="hire_details")
    reg_no = models.CharField(max_length=50)

    start_date = models.DateField()
    end_date = models.DateField()

    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='Hr', blank=True, null=True)
    no_of_unit = models.IntegerField(default=1, blank=True, null=True)
    rate_per_period = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle} ({self.reg_no}) Hire {self.start_date} - {self.end_date}"    
    
class VehicleEMI(models.Model):
    vehicle = models.ForeignKey('Vehicle', on_delete=models.PROTECT, related_name='emis')
    title = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    reminder_day = models.IntegerField(help_text="Day of the month (e.g., 7)")
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    reminder_days_before = models.IntegerField(help_text="Days before due date to start showing warning")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.vehicle}"
    
    @property
    def total_installments(self):
        return self.installments.count()
    
    @property
    def paid_installments(self):
        return self.installments.filter(is_paid=True).count()
    
    @property
    def pending_installments(self):
        return self.installments.filter(is_paid=False).count()
    
    @property
    def progress_percentage(self):
        total = self.total_installments
        if total == 0:
            return 0
        return int((self.paid_installments / total) * 100)


class EMIInstallment(models.Model):
    emi_plan = models.ForeignKey(VehicleEMI, on_delete=models.PROTECT, related_name='installments')
    due_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=3)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.emi_plan.title} - {self.due_date}"

    @property
    def payment_status(self):
        """Returns: Paid, Due Today, Overdue, Warning, or Upcoming"""
        if self.is_paid:
            return "Paid"
        
        today = timezone.now().date()
        warning_date = self.due_date - datetime.timedelta(days=self.emi_plan.reminder_days_before)
        
        if today > self.due_date:
            return "Overdue"
        elif today == self.due_date:
            return "Due Today"
        elif today >= warning_date:
            return "Warning"
        return "Upcoming"
    
    @property
    def status_color(self):
        """Returns Bootstrap color class"""
        status = self.payment_status
        color_map = {
            'Paid': 'success',
            'Due Today': 'warning',
            'Overdue': 'danger',
            'Warning': 'info',
            'Upcoming': 'secondary'
        }
        return color_map.get(status, 'secondary')
    
    @property
    def notification_message(self):
        """Get notification message for unpaid installments"""
        if self.is_paid:
            return None
        
        today = timezone.now().date()
        days_diff = (self.due_date - today).days
        
        status = self.payment_status
        
        if status == "Overdue":
            days_overdue = (today - self.due_date).days
            return f"⚠️ OVERDUE: {self.emi_plan.title} - {self.amount} ({days_overdue} days overdue)"
        elif status == "Due Today":
            return f"🔴 DUE TODAY: {self.emi_plan.title} - {self.amount}"
        elif status == "Warning":
            return f"⚡ REMINDER: {self.emi_plan.title} - {self.amount} (Due in {days_diff} days)"
        
        return None
    
    def mark_as_paid(self):
        """Mark this installment as paid"""
        self.is_paid = True
        self.paid_date = timezone.now().date()
        self.save()
    
    @classmethod
    def get_all_notifications(cls):
        """Get all pending EMI notifications"""
        today = timezone.now().date()
        notifications = []
        
        unpaid = cls.objects.filter(is_paid=False).select_related('emi_plan', 'emi_plan__vehicle')
        
        for installment in unpaid:
            warning_date = installment.due_date - datetime.timedelta(days=installment.emi_plan.reminder_days_before)
            
            # Show notification if today is on or after warning date
            if today >= warning_date:
                message = installment.notification_message
                if message:
                    notifications.append({
                        'installment': installment,
                        'message': message,
                        'status': installment.payment_status
                    })
        
        return notifications


# SIGNAL - This must be OUTSIDE the class
@receiver(post_save, sender=VehicleEMI)
def create_emi_installments(sender, instance, created, **kwargs):
    """Auto-generate installments when EMI plan is created"""
    if created:
        current_date = instance.start_date
        
        while current_date <= instance.end_date:
            # Handle edge cases where month doesn't have the specified day
            try:
                due_date = current_date.replace(day=instance.reminder_day)
            except ValueError:
                # If reminder_day is 31 but month has fewer days, use last day
                last_day = (current_date + relativedelta(months=1)).replace(day=1) - datetime.timedelta(days=1)
                due_date = last_day
            
            # Only create if due date is within range
            if instance.start_date <= due_date <= instance.end_date:
                EMIInstallment.objects.create(
                    emi_plan=instance,
                    due_date=due_date,
                    amount=instance.amount,
                    is_paid=False
                )
            
            # Move to next month
            current_date = current_date + relativedelta(months=1)

class VehicleProfitLoss(models.Model):
    Vehicle = models.ForeignKey(
        'Vehicle',
        on_delete=models.PROTECT,
        related_name='profit_losses'    
    )
    Date = models.DateField()
    Details = models.CharField(max_length=255)
    Amount = models.DecimalField(max_digits=12, decimal_places=3)
    InvNo = models.CharField(max_length=50)
    InvAmount = models.DecimalField(max_digits=12, decimal_places=3)
    Balance = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)


    def __str__(self):
        return f"{self.Vehicle} - {self.Date}"            

class OffHire(models.Model):
    
    # Basic fields
    voucher_no = models.CharField(max_length=100, unique=True)
    date = models.DateField(default=timezone.now)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=15)  # OffHire voucher type
    
    # Link to delivery contract
    delivery_contract = models.ForeignKey(
        DeliveryContract, 
        on_delete=models.PROTECT, 
        related_name='offhires'
    )
    
    customer = models.ForeignKey(
        'accounts_app.LedgerCreation', 
        on_delete=models.PROTECT, 
        related_name='offhires',
        blank=True, 
        null=True
    )
    
    offhire_date_time = models.DateTimeField(default=timezone.now)
    remarks = models.TextField(blank=True, null=True)
    
    # Audit fields
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"OffHire #{self.voucher_no} - Contract #{self.delivery_contract.voucher_no}"


class OffHireDetails(models.Model):
    offhire = models.ForeignKey(OffHire, on_delete=models.CASCADE, related_name='details')
    
    # Reference to original delivery contract detail
    delivery_contract_detail = models.ForeignKey(
        DeliveryContractDetails,
        on_delete=models.PROTECT,
        related_name='offhire_details',
        help_text="Original contract detail being offhired"
    )
    
    # Vehicle (copied from delivery contract detail for reference)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT)
    location = models.CharField(max_length=255)
    
    # Offhire specific details
    offhire_date_time = models.DateTimeField(default=timezone.now)
    meter_reading = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fuel_level = models.CharField(max_length=50, null=True, blank=True)
    vehicle_condition = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    
    # Copy of contract amounts for reference
    amount = models.DecimalField(max_digits=20, decimal_places=3)
    tax = models.DecimalField(max_digits=20, decimal_places=3)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=3)
    total_amount = models.DecimalField(max_digits=12, decimal_places=3)
    
    # Complex contract fields (if applicable)
    period = models.CharField(max_length=10, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit_rate = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    
    # Audit fields
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"OffHire - {self.vehicle} from {self.offhire.delivery_contract.voucher_no}"        

class POMaster(models.Model):

    PO_no = models.CharField(max_length=50)
    PO_date = models.DateField(default=timezone.now)

    quote_ref = models.CharField(max_length=100, blank=True, null=True)
    quote_ref_date = models.DateField(blank=True, null=True)

    payment_terms1 = models.CharField(max_length=200, blank=True, null=True)
    payment_terms2 = models.CharField(max_length=200, blank=True, null=True)
    kind_attn = models.CharField(max_length=200, blank=True, null=True)

    supplier = models.ForeignKey(
        LedgerCreation,
        on_delete=models.CASCADE
    )

    delivery_date = models.DateField(blank=True, null=True)

    taxable_amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=3, default=0)
    grand_total = models.DecimalField(max_digits=15, decimal_places=3, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.PO_no


class PODetails(models.Model):

    po_master = models.ForeignKey(
        POMaster,
        related_name='po_details',
        on_delete=models.CASCADE
    )

    description = models.CharField(max_length=255)

    units = models.CharField(max_length=50)

    quantity = models.DecimalField(max_digits=15, decimal_places=3)

    rate = models.DecimalField(max_digits=15, decimal_places=3)

    amount = models.DecimalField(max_digits=15, decimal_places=3)

    def __str__(self):
        return self.description        

