from django.db import models
from django.core.validators import MinValueValidator
from accounts_app.models import LedgerCreation
from item_master.models import Customer
from django.utils import timezone


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
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.manufacturer_name

    class Meta:
        verbose_name = "manufacturer_name"
        verbose_name_plural = "manufacturer_name"
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
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)  # Foreign key to Manufacturer
    vehicle_category = models.ForeignKey(VehicleCategory, on_delete=models.CASCADE)  # Foreign key to VehicleCategory
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
        verbose_name_plural = "Vehicle Model" 
        ordering = ['model_name']  
        
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
    driver_company = models.ForeignKey(RentalCompany, on_delete=models.CASCADE, null=True, blank=True)  # Foreign key to RentalCompany
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
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=50)
    civil_id_or_passport_no = models.CharField(max_length=50)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    joining_date = models.DateField()
    employment_type = models.CharField(max_length=10, choices=EMPLOYMENT_TYPE_CHOICES)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=3)
    allowances = models.DecimalField(max_digits=10, decimal_places=3)
    bank_account_no = models.CharField(max_length=30)
    bank_name = models.CharField(max_length=100)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_number = models.CharField(max_length=20)
    visa_expiry_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    remarks = models.TextField(blank=True)
    
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
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE)  # Foreign key to VehicleModel
    vehicle_name = models.CharField(max_length=255, null=True, blank=True)  
    license_plate_code = models.ForeignKey(LicensePlateCode, on_delete=models.CASCADE, null=True, blank=True)  # ForeignKey to LicensePlateCode
    license_plate_number = models.CharField(max_length=50, null=True, blank=True)
    vehicle_image = models.ImageField(upload_to='vehicle_image/', null=True, blank=True)
    vehicle_driver = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True, related_name='vehicle_first_driver')  # Driver assigned to the vehicle
    vehicle_second_driver = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True, related_name='vehicle_second_driver')
    driver_assignment_date = models.DateField(null=True, blank=True)  # Date driver was assigned
    vehicle_registration_date = models.DateField(null=True, blank=True)  # Vehicle registration date
    vehicle_cancellation_date = models.DateField(null=True, blank=True)  # Optional cancellation date
    RC_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Registration Certificate number (unique)
    RC_file = models.FileField(upload_to='RC_upload/', null=True, blank=True)
    RC_expiry_date = models.DateField(null=True, blank=True)  # Registration Certificate expiry date
    chassis_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Chassis number (unique)
    last_odometer = models.PositiveIntegerField(validators=[MinValueValidator(0)], null=True, blank=True)  # Odometer reading (cannot be negative)
    rate_per_hr = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Rate per hour
    rate_per_day = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Rate per day
    rate_per_week = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Rate per week
    rate_per_month = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Rate per month
    rate_per_year = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Rate per year
    #we use vehicle_category as vehicle type in templates
    vehicle_category = models.ForeignKey(VehicleCategory, on_delete=models.CASCADE)  # Foreign key to VehicleCategory
    engine_number = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Engine number (unique)
    
    RAS_inspection_date = models.DateField(null=True, blank=True)  # RAS inspection date
    RAS_inspection_expiry_date = models.DateField(null=True, blank=True)  # RAS inspection expiry date
    RAS_inspection_certificate = models.FileField(upload_to='RAS_inspection_certificate/', null=True, blank=True)
    
    hook_inspection_date = models.DateField(null=True, blank=True)  # Hook inspection date
    hook_inspection_expiry_date = models.DateField(null=True, blank=True)  # Hook inspection expiry date
    hook_inspection_certificate = models.FileField(upload_to='hook_inspection_certificate/', null=True, blank=True)
    
    wire_rope_inspection_date =  models.DateField(null=True, blank=True)  # Wire rope inspection date
    wire_rope_inspection_expiry_date = models.DateField(null=True, blank=True)  # Wire rope inspection expiry date
    wire_rope_inspection_certificate = models.FileField(upload_to='wire_rope_inspection_certificate/', null=True, blank=True)
    
    winch_inspection_date = models.DateField(null=True, blank=True)  # Winch inspection date
    winch_inspection_expiry_date = models.DateField(null=True, blank=True)  # Winch inspection expiry date
    winch_inspection_certificate = models.FileField(upload_to='winch_inspection_certificate/', null=True, blank=True)
    
    lifting_wire_rope_inspection_date = models.DateField(null=True, blank=True)  # Lifting wire rope inspection date
    lifting_wire_rope_inspection_expiry_date = models.DateField(null=True, blank=True)  # Lifting wire rope inspection expiry date
    lifting_wire_rope_inspection_certificate = models.FileField(upload_to='lifting_wire_rope_inspection_certificate/', null=True, blank=True)
    
    lifting_belt_inspection_date = models.DateField(null=True, blank=True)  # Lifting belt inspection date  
    lifting_belt_inspection_expiry_date = models.DateField(null=True, blank=True)  # Lifting belt inspection expiry date
    lifting_belt_inspection_certificate = models.FileField(upload_to='lifting_belt_inspection_certificate/', null=True, blank=True)
    
    is_owned = models.BooleanField(default=True)
    supplier = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.SET_NULL, null=True, blank=True)
    
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
    
    company = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, null=True, blank=True)
    vehicle_name = models.CharField(max_length=255, null=True, blank=True)  
    contact_person = models.CharField(max_length=255, help_text="Primary contact person", null=True, blank=True)
    vehicle_driver = models.ForeignKey(Driver, on_delete=models.CASCADE, null=True, blank=True) 
    vehicle_driver_mobile = models.CharField(max_length=15, help_text="Driver mobile number", null=True, blank=True)
    vehicle_manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, null=True, blank=True)
    vehicle_model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, null=True, blank=True) 
    model_colour = models.CharField(max_length=50, null=True, blank=True)
    model_year = models.IntegerField(null=True, blank=True)
    Vehicle_image = models.ImageField(upload_to='rentalcompany_vehicle/', null=True, blank=True)
    vehicle_category = models.ForeignKey(VehicleCategory, on_delete=models.CASCADE, help_text="Category of the vehicle", null=True, blank=True)
    license_plate_code = models.ForeignKey(LicensePlateCode, on_delete=models.CASCADE, null=True, blank=True)  # ForeignKey to LicensePlateCode
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
    ledger = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, null=True, blank=True, related_name='fleet_vouchers')
    isDefault = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    
    def get_next_voucher_number(self):
        """Generate the next voucher number for this voucher type"""
        from django.apps import apps
        from django.db.models import ForeignKey
        from django.db.models.deletion import PROTECT, CASCADE, SET_NULL
        
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
    vehicle_name = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True)
    project_location = models.CharField(max_length=100)
    client = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, null=True, blank=True)
    duration = models.CharField(max_length=20)
    PO_reference_no = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(default=timezone.now)
    driver_name = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True, related_name='driver_name')
    operator_name = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True, related_name='operator_name')
    
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
    timesheet = models.ForeignKey(TimeSheet, related_name="details", on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    break_hours = models.DecimalField(max_digits=4, decimal_places=3, default=0.00)
    total_hours_worked = models.DecimalField(max_digits=4, decimal_places=3, default=0.00)
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
    company_name = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fleet_quotations', blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_address = models.TextField(blank=True, null=True)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, related_name='fleet_quotations', blank=True, null=True)
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

    vehicle_quotation = models.ForeignKey(FleetQuotation, on_delete=models.CASCADE, related_name='items')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fleet_quotation_items')
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
    vehicle_name = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="repair_maintenance")
    vehicle_driver = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="vehicle_driver")
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
    repair_and_maintenance = models.ForeignKey(RepairAndMaintenance, on_delete=models.CASCADE, related_name="items")
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
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    date = models.DateField()
    end_date = models.DateField()
    operator_1 = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='operator_1', blank=True, null=True)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, related_name='contracts', blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)
    
    
    
class VehicleMaster(models.Model):
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
    file_path = models.FileField(upload_to='documents/')
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
        
        
class SimpleQuotation(models.Model):
    voucher_no = models.CharField(max_length=50, unique=True)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=9)
    date = models.DateField(default=timezone.now)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, related_name='quotations', blank=True, null=True)
    
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
        ('Month', 'Month'),
    ]
    quotation = models.ForeignKey(SimpleQuotation, on_delete=models.CASCADE, related_name='details')
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    rent = models.DecimalField(max_digits=6, decimal_places=3)  
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='Hour', blank=True, null=True)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.rent})"        
    
class Invoice(models.Model):
    VOUCHER_PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('Credit', 'Credit'),
    ]
    voucher_no = models.CharField(max_length=100, unique=True)
    date = models.DateField(default=timezone.now)
    voucherType = models.ForeignKey(Vouchers, on_delete=models.PROTECT, default=2)
    customer = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, related_name='invoice', blank=True, null=True)
    is_taxable = models.BooleanField(default=True)

    payment_mode = models.CharField(max_length=10, choices=VOUCHER_PAYMENT_MODE_CHOICES, default='cash')
    supplier_ref = models.CharField(max_length=255, blank=True, null=True)
    other_ref = models.CharField(max_length=255, blank=True, null=True)
    buyer_order_no = models.CharField(max_length=255, blank=True, null=True)
    dated = models.CharField(max_length=100, blank=True, null=True)  # Free text date entry if needed
    grand_total = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    IsCleared = models.BooleanField(default=False)
    
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

    def __str__(self):
        return f"Invoice #{self.voucher_no}"


class InvoiceDetails(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='details')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    location = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    tax = models.DecimalField(max_digits=5, decimal_places=3)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=3)
    total_amount = models.DecimalField(max_digits=12, decimal_places=3)
    
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(null=True, blank=True)   
    updated_by = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle} - {self.location} - {self.total_amount}"    
    
    
class CompanyDocument(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="documents")
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
    supplier = models.ForeignKey('accounts_app.LedgerCreation', on_delete=models.CASCADE, related_name="fleet_hires")
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

   

    def __str__(self):
        return f"FleetHire {self.voucher_no} - {self.supplier}"


class FleetHireDetails(models.Model):
    UNIT_CHOICES = [
        ('Hr', 'Hour'),
        ('Day', 'Day'),
        ('Month', 'Month'),
    ]
    fleet_hire = models.ForeignKey(FleetHire, on_delete=models.CASCADE, related_name="details")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="hire_details")
    reg_no = models.CharField(max_length=50)

    start_date = models.DateField()
    end_date = models.DateField()

    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='Hr', blank=True, null=True)
    no_of_unit = models.IntegerField(default=1, blank=True, null=True)
    rate_per_period = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    

    def __str__(self):
        return f"{self.vehicle} ({self.reg_no}) Hire {self.start_date} - {self.end_date}"    