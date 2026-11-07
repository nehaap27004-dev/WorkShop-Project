from django.db.models import Q
from django import forms

from fleet_app.common import filter_voucher_types, get_ledgers_by_group_ids
from .models import *
from django.forms import modelformset_factory
from django.forms import inlineformset_factory
from item_master.models import Customer
from django.utils.translation import gettext_lazy as _
from item_master.models import Item, ItemGroup

class ManufacturerForm(forms.ModelForm):
    class Meta:
        model = Manufacturer
        fields = ['manufacturer_name','vehicle_type', 'manufacturer_logo']

        labels = {
            'manufacturer_name': _("Manufacturer Name"),
            'vehicle_type': _("Vehicle Type"),
            'manufacturer_logo': _("Manufacturer Logo"),
        }
        widgets = {
            'vehicle_type': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

class VehicleCategoryForm(forms.ModelForm):
    class Meta:
        model = VehicleCategory
        fields = ['category_name']

        labels = {
            'category_name': _("Category Name"),
        }

        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter vehicle category name',
                'id': 'id_vehicle_category',
            }),
        }  
        


class VehicleModelForm(forms.ModelForm):
    
    class Meta:
        model = VehicleModel
        fields = [
            'model_name', 'manufacturer', 'vehicle_category', 'seat_number', 'door_number', 
            'model_colour', 'model_range', 'model_year', 'fuel_type', 'CO2_emission', 
            'CO2_standard', 'model_transmission', 'model_power', 'model_horse_power'
        ]
        labels = {
            'model_name': _('Model Name'),
            'manufacturer': _('Manufacturer'),
            'vehicle_category': _('Vehicle Type'),
            'seat_number': _('Number of Seats'),
            'door_number': _('Number of Doors'),
            'model_colour': _('Model Colour'),
            'model_range': _('Range'),
            'model_year': _('Model Year'),
            'fuel_type': _('Fuel Type'),
            'CO2_emission': _('CO2 Emission'),
            'CO2_standard': _('CO2 Standard'),
            'model_transmission': _('Transmission Type'),
            'model_power': _('Power'),
            'model_horse_power': _('Horsepower')
        }
        widgets = {
            'model_name': forms.TextInput(attrs={'placeholder': 'Enter the model name'}),
            'manufacturer': forms.Select(attrs={'placeholder': 'Select manufacturer'}),
            'vehicle_category': forms.Select(attrs={'placeholder': 'Select vehicle category'}),
            'seat_number': forms.NumberInput(attrs={'placeholder': 'Enter number of seats'}),
            'door_number': forms.NumberInput(attrs={'placeholder': 'Enter number of doors'}),
            'model_colour': forms.TextInput(attrs={'placeholder': 'Enter model colour'}),
            'model_range': forms.NumberInput(attrs={}),
            'model_year': forms.NumberInput(attrs={}),
            'fuel_type': forms.Select(attrs={'placeholder': 'Select fuel type'}),
            'CO2_emission': forms.NumberInput(attrs={}),
            'CO2_standard': forms.TextInput(attrs={'placeholder': 'Enter CO2 standard'}),
            'model_transmission': forms.Select(attrs={'placeholder': 'Select transmission type'}),
            'model_power': forms.NumberInput(attrs={'placeholder': 'Enter power (kW)'}),
            'model_horse_power': forms.NumberInput(attrs={'placeholder': 'Enter horsepower (HP)'}),
        }                  
        

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['driver_name', 'driver_company', 'driver_address', 'driver_email', 'driver_mobile', 'driver_phone', 'driver_license_no', 'driver_license_expiry_date', 'residential_id_no', 'residential_id_expiry_date']
        
        labels = {
            'driver_name': 'Name',
            'driver_company': 'Company',
            'driver_address': 'Address',
            'driver_email': 'Email',
            'driver_mobile': 'Mobile Number',
            'driver_phone': 'Phone Number (Optional)',
            'driver_license_no': 'License Number',
            'driver_license_expiry_date': 'License Expiry Date',
            'residential_id_no': 'Residential ID Number',
            'residential_id_expiry_date': 'Residential ID Expiry Date',
        }

        widgets = {
    'driver_name': forms.TextInput(attrs={
        'placeholder': 'Enter full name',
        'class': 'form-control'
    }),
    'driver_company': forms.Select(attrs={
        'placeholder': 'Enter company name',
        'class': 'form-control'
    }),
    'driver_address': forms.Textarea(attrs={
        'placeholder': 'Enter full address',
        'rows': 3,
        'class': 'form-control'
    }),
    'driver_email': forms.EmailInput(attrs={
        'placeholder': 'Enter email address',
        'class': 'form-control'
    }),
    'driver_mobile': forms.TextInput(attrs={
        'placeholder': 'Enter mobile number',
        'class': 'form-control'
    }),
    'driver_phone': forms.TextInput(attrs={
        'placeholder': 'Enter phone number (optional)',
        'class': 'form-control'
    }),
    'driver_license_no': forms.TextInput(attrs={
        'placeholder': 'Enter license number',
        'class': 'form-control'
    }),
    'driver_license_expiry_date': forms.DateInput(attrs={
        'placeholder': 'YYYY-MM-DD',
        'type': 'date',
        'class': 'form-control'
    }),
    'residential_id_no': forms.TextInput(attrs={
        'placeholder': 'Enter residential ID number',
        'class': 'form-control'
    }),
    'residential_id_expiry_date': forms.DateInput(attrs={
        'placeholder': 'YYYY-MM-DD',
        'type': 'date',
        'class': 'form-control'
    }),
}
   
        
from .models import Vehicle

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_category',
            'vehicle_name',
            'model',
            'vehicle_image',
            'license_plate_code',
            'license_plate_number',
            
            'RAS_inspection_date',
            'RAS_inspection_expiry_date',
            'RAS_inspection_certificate',
            'hook_inspection_date',
            'hook_inspection_expiry_date',
            'hook_inspection_certificate',
            'wire_rope_inspection_date',
            'wire_rope_inspection_expiry_date',
            'wire_rope_inspection_certificate',
            'winch_inspection_date',
            'winch_inspection_expiry_date',
            'winch_inspection_certificate',
            'lifting_wire_rope_inspection_date',
            'lifting_wire_rope_inspection_expiry_date',
            'lifting_wire_rope_inspection_certificate',
            'lifting_belt_inspection_date',
            'lifting_belt_inspection_expiry_date',
            'lifting_belt_inspection_certificate',
            
            'vehicle_driver',
            'vehicle_second_driver',
            'driver_assignment_date',
            'vehicle_registration_date',
            'vehicle_cancellation_date',
            'RC_number',
            'RC_file',
            'RC_expiry_date',
            'chassis_number',
            'engine_number',
            'last_odometer',
            'rate_per_hr',
            'rate_per_day',
            'rate_per_week',
            'rate_per_month',
            'replacement_value',
            'model_year',
            'capacity',
            'purchase_value',
            'vat',
            'description',
            'is_owned',
            'supplier',
            'status',
            'item'
            
        ]
        labels = {
            'vehicle_category': _('Equipment Type'),
            'vehicle_name': _('Fleet No'),
            'model': _('Vehicle Model'),
            'vehicle_image': _('Fleet Image'),
            'license_plate_code': _('Reg-Plate Code'),
            'license_plate_number': _('Reg-Plate No'),
            'vehicle_driver': _('Assigned Driver'),
            'vehicle_second_driver': _('Second Driver'),
            'driver_assignment_date': _('Assignment Date'),
            'vehicle_registration_date': _('Registration Date'),
            'vehicle_cancellation_date': _('Cancellation Date'),
            'RC_number': _('Mulki Number'),
            'RC_file': _('RC File'),
            'RC_expiry_date': _('Mulki Expiry Date'),
            'chassis_number': _('Chassis Number'),
            'engine_number': _('Engine Number'),
            'last_odometer': _('Last Odometer'),
            'rate_per_hr' : _('Rate Per Hour'),
            'rate_per_day': _('Rate Per Day'),
            'rate_per_week': _('Rate Per Week'),
            'rate_per_month': _('Rate Per Month'),
            'replacement_value': _('Replacement Value'),
            'model_year': _('Model Year'),
            'capacity': _('Capacity'),
            'purchase_value': _('Purchase Value'),
            'vat': _('VAT'),
            'description': _('Description'),
            'is_owned': _('Owned Vehicle'),
            'supplier': _('Supplier'),
            'status': _('Status'),
            'item' : _('Item')
        }
        
        widgets = {
            'vehicle_category': forms.Select(attrs={'placeholder': 'Select vehicle category', 'class': 'form-control'}),
            'vehicle_name': forms.TextInput(attrs={'placeholder': 'Enter Vehicle Name', 'class': 'form-control'}),
            'model': forms.Select(attrs={'placeholder': 'Select vehicle model', 'class': 'form-control'}),
            'vehicle_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'license_plate_code': forms.Select(attrs={'placeholder': 'License plate code', 'class': 'form-control'}),
            'license_plate_number': forms.TextInput(attrs={'placeholder': 'License plate number', 'class': 'form-control'}),

            'RAS_inspection_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'RAS_inspection_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'RAS_inspection_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'hook_inspection_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'hook_inspection_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'hook_inspection_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'wire_rope_inspection_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'wire_rope_inspection_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'wire_rope_inspection_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'winch_inspection_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'winch_inspection_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'winch_inspection_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'lifting_wire_rope_inspection_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'lifting_wire_rope_inspection_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'lifting_wire_rope_inspection_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'lifting_belt_inspection_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'lifting_belt_inspection_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'lifting_belt_inspection_certificate': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            'vehicle_driver': forms.Select(attrs={'placeholder': 'Assign a driver (optional)', 'class': 'form-control'}),
            'vehicle_second_driver': forms.Select(attrs={'placeholder': 'Assign a second driver (optional)', 'class': 'form-control'}),
            'driver_assignment_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'vehicle_registration_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'vehicle_cancellation_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'RC_number': forms.TextInput(attrs={'placeholder': 'Enter Mulki number', 'class': 'form-control'}),
            'RC_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'RC_expiry_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD', 'type': 'date', 'class': 'form-control'}),
            'chassis_number': forms.TextInput(attrs={'placeholder': 'Enter chassis number', 'class': 'form-control'}),
            'engine_number': forms.TextInput(attrs={'placeholder': 'Enter engine number', 'class': 'form-control'}),
            'last_odometer': forms.NumberInput(attrs={'placeholder': 'Enter last odometer reading', 'class': 'form-control'}),
            'rate_per_hr': forms.NumberInput(attrs={'placeholder': 'Enter rate per hour', 'class': 'form-control'}),
            'rate_per_day': forms.NumberInput(attrs={'placeholder': 'Enter rate per day', 'class': 'form-control'}),
            'rate_per_week': forms.NumberInput(attrs={'placeholder': 'Enter rate per week', 'class': 'form-control'}),
            'rate_per_month': forms.NumberInput(attrs={'placeholder': 'Enter rate per month', 'class': 'form-control'}),
            'replacement_value': forms.NumberInput(attrs={'placeholder': 'Enter replacement value', 'class': 'form-control', 'step': '0.001'}),
            'model_year': forms.NumberInput(attrs={'placeholder': 'Enter model year', 'class': 'form-control'}),
            'capacity': forms.TextInput(attrs={'placeholder': 'Enter chassis number', 'class': 'form-control'}),
            'purchase_value': forms.NumberInput(attrs={'placeholder': 'Enter purchase value', 'class': 'form-control', 'step': '0.001'}),
            'vat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            
            'is_owned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'item' : forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['supplier'].queryset = get_ledgers_by_group_ids(28) 
        


class RentalCompanyForm(forms.ModelForm):
    class Meta:
        model = RentalCompany
        fields = [
            'company_name', 'company_logo', 'company_mobile', 'company_phone',
            'company_email', 'company_address_1', 'company_address_2', 'company_country',
            'company_state', 'company_city', 'company_zipcode', 'company_website', 'company_description',
            'company_VAT', 'company_TRN_or_CRN'
        ]

        labels = {
            'company_name': 'Company Name',
            'company_logo': 'Company Logo',
            'company_mobile': 'Mobile Number',
            'company_phone': 'Phone Number',
            'company_email': 'Email Address',
            'company_address_1': 'Address Line 1',
            'company_address_2': 'Address Line 2',
            'company_country': 'Country',
            'company_state': 'State',
            'company_city': 'City',
            'company_zipcode': 'Zip Code',
            'company_website': 'Website',
            'company_description': 'Description',
            'company_VAT': 'VAT Number',
            'company_TRN_or_CRN': 'TRN or CRN Number'
        }

        widgets = {
    'company_name': forms.TextInput(attrs={
        'placeholder': 'Enter the company name',
        'class': 'form-control'
    }),
    'company_logo': forms.ClearableFileInput(attrs={
        'class': 'form-control'
    }),
    'company_mobile': forms.TextInput(attrs={
        'placeholder': 'Enter mobile number',
        'class': 'form-control'
    }),
    'company_phone': forms.TextInput(attrs={
        'placeholder': 'Enter phone number',
        'class': 'form-control'
    }),
    'company_email': forms.EmailInput(attrs={
        'placeholder': 'Enter email address',
        'class': 'form-control'
    }),
    'company_address_1': forms.Textarea(attrs={
        'placeholder': 'Enter address line 1',
        'rows': 3,
        'class': 'form-control'
    }),
    'company_address_2': forms.Textarea(attrs={
        'placeholder': 'Enter address line 2',
        'rows': 3,
        'class': 'form-control'
    }),
    'company_country': forms.TextInput(attrs={
        'placeholder': 'Enter country',
        'class': 'form-control'
    }),
    'company_state': forms.TextInput(attrs={
        'placeholder': 'Enter state',
        'class': 'form-control'
    }),
    'company_city': forms.TextInput(attrs={
        'placeholder': 'Enter city',
        'class': 'form-control'
    }),
    'company_zipcode': forms.TextInput(attrs={
        'placeholder': 'Enter zip code',
        'class': 'form-control'
    }),
    'company_website': forms.URLInput(attrs={
        'placeholder': 'Enter website URL',
        'class': 'form-control'
    }),
    'company_description': forms.Textarea(attrs={
        'placeholder': 'Enter description',
        'rows': 4,
        'class': 'form-control'
    }),
    'company_VAT': forms.TextInput(attrs={
        'placeholder': 'Enter VAT number',
        'class': 'form-control'
    }),
    'company_TRN_or_CRN': forms.TextInput(attrs={
        'placeholder': 'Enter TRN or CRN number',
        'class': 'form-control'
    })
}



class RentalCompanyVehicleForm(forms.ModelForm):
    class Meta:
        model = RentalCompanyVehicle
        fields = [
            'company', 'vehicle_name', 'contact_person', 'vehicle_driver', 'vehicle_driver_mobile', 'vehicle_manufacturer', 
            'vehicle_model', 'model_colour', 'model_year', 'Vehicle_image', 'vehicle_category', 
            'license_plate_code', 'license_plate_number','RC_number', 'RC_epx_date', 'fuel_type', 'vehicle_transmission', 
            'chassis_number', 'last_odometer'
        ]
        labels = {
            'company': 'Rental Company',
            'vehicle_name': 'Vehicle Name',
            'contact_person': 'Contact Person',
            'vehicle_driver': 'Vehicle Driver Name',
            'vehicle_driver_mobile': 'Driver Mobile Number',
            'vehicle_manufacturer': 'Vehicle Manufacturer',
            'vehicle_model': 'Vehicle Model',
            'model_colour': 'Vehicle Color',
            'model_year': 'Vehicle Manufacturing Year',
            'Vehicle_image': 'Vehicle Image',
            'vehicle_category': 'Vehicle Category',
            'license_plate_code': 'Licenseplate Code',
            'license_plate_number': 'Licenseplate Number',
            'RC_number': 'RC Number',
            'RC_epx_date': 'RC Expiry Date',
            'fuel_type': 'Fuel Type',
            'vehicle_transmission': 'Transmission Type',
            'chassis_number': 'Chassis Number',
            'last_odometer': 'Last Recorded Odometer',
        }
        widgets = {
    'company': forms.Select(attrs={
        'placeholder': 'Select company',
        'class': 'form-control'
    }),
    'vehicle_name': forms.TextInput(attrs={
        'placeholder': 'Enter Vehicle Name',
        'class': 'form-control'
    }),
    'contact_person': forms.TextInput(attrs={
        'placeholder': 'Enter contact person name',
        'class': 'form-control'
    }),
    'vehicle_driver': forms.Select(attrs={
        'placeholder': 'Enter vehicle driver name',
        'class': 'form-control'
    }),
    'vehicle_driver_mobile': forms.TextInput(attrs={
        'placeholder': 'Enter driver mobile number',
        'class': 'form-control'
    }),
    'vehicle_manufacturer': forms.Select(attrs={
        'placeholder': 'Enter vehicle manufacturer',
        'class': 'form-control'
    }),
    'vehicle_model': forms.Select(attrs={
        'placeholder': 'Enter vehicle model',
        'class': 'form-control'
    }),
    'model_colour': forms.TextInput(attrs={
        'placeholder': 'Enter vehicle color',
        'class': 'form-control'
    }),
    'model_year': forms.NumberInput(attrs={
        'placeholder': 'Enter manufacturing year',
        'class': 'form-control'
    }),
    'license_plate_code': forms.Select(attrs={
        'placeholder': 'License plate code',
        'class': 'form-control'
    }),
    'license_plate_number': forms.TextInput(attrs={
        'placeholder': 'License plate number',
        'class': 'form-control'
    }),
    'RC_number': forms.TextInput(attrs={
        'placeholder': 'Enter RC number',
        'class': 'form-control'
    }),
    'RC_epx_date': forms.DateInput(attrs={
        'placeholder': 'Enter RC expiry date',
        'type': 'date',
        'class': 'form-control'
    }),
    'fuel_type': forms.Select(attrs={
        'placeholder': 'Select fuel type',
        'class': 'form-control'
    }),
    'vehicle_transmission': forms.Select(attrs={
        'placeholder': 'Select transmission type',
        'class': 'form-control'
    }),
    'chassis_number': forms.TextInput(attrs={
        'placeholder': 'Enter unique chassis number',
        'class': 'form-control'
    }),
    'last_odometer': forms.NumberInput(attrs={
        'placeholder': 'Enter last recorded odometer value',
        'class': 'form-control'
    }),
}
 
        
    def __init__(self, *args, **kwargs):
        super(RentalCompanyVehicleForm, self).__init__(*args, **kwargs)
        
        # Check if 'company' is in the form data to dynamically filter drivers based on the selected company
        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))  # Get company ID from POST data
                self.fields['vehicle_driver'].queryset = Driver.objects.filter(driver_company_id=company_id)  # Filter drivers by company
            except (ValueError, TypeError):
                self.fields['vehicle_driver'].queryset = Driver.objects.none()  # Invalid input, fallback to empty queryset
        elif self.instance.pk:
            # If the form is initialized with an existing instance, filter drivers by the instance's company
            self.fields['vehicle_driver'].queryset = Driver.objects.filter(driver_company=self.instance.company)
        else:
            self.fields['vehicle_driver'].queryset = Driver.objects.none()  # Default to no drivers if no company is selected
        
        

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'vendor_name', 'vendor_type',  'vendor_image', 'vendor_mobile', 'vendor_phone', 'vendor_email', 
            'vendor_address_1', 'vendor_address_2', 'vendor_country', 'vendor_state', 
            'vendor_city', 'vendor_zipcode', 'vendor_website', 'vendor_description', 
            'vendor_VAT', 'vendor_TRN_or_CRN'
        ]
        
        labels = {
            'vendor_name': 'vendor Name',
            'vendor_type': 'Vendor Type',
            'vendor_image': 'vendor Image',
            'vendor_mobile': 'Mobile',
            'vendor_phone': 'Phone',
            'vendor_email': 'vendor Email',
            'vendor_address_1': 'Address Line 1',
            'vendor_address_2': 'Address Line 2',
            'vendor_country': 'Country',
            'vendor_state': 'State',
            'vendor_city': 'City',
            'vendor_zipcode': 'Zipcode',
            'vendor_website': 'Website',
            'vendor_description': 'Description',
            'vendor_VAT': 'VAT Number',
            'vendor_TRN_or_CRN': 'TRN/CRN Number',
        }
        
        widgets = {
            'vendor_name': forms.TextInput(attrs={'placeholder': 'Enter vendor name'}),
            'vendor_type': forms.Select(attrs={'placeholder': 'Select vendor type'}),
            'vendor_image': forms.ClearableFileInput(),
            'vendor_mobile': forms.TextInput(attrs={'placeholder': 'Enter mobile number'}),
            'vendor_phone': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
            'vendor_email': forms.EmailInput(attrs={'placeholder': 'Enter email address'}),
            'vendor_address_1': forms.Textarea(attrs={'placeholder': 'Enter address line 1', 'rows': 2}),
            'vendor_address_2': forms.Textarea(attrs={'placeholder': 'Enter address line 2', 'rows': 2}),
            'vendor_country': forms.TextInput(attrs={'placeholder': 'Enter country'}),
            'vendor_state': forms.TextInput(attrs={'placeholder': 'Enter state'}),
            'vendor_city': forms.TextInput(attrs={'placeholder': 'Enter city'}),
            'vendor_zipcode': forms.TextInput(attrs={'placeholder': 'Enter zipcode'}),
            'vendor_website': forms.URLInput(attrs={'placeholder': 'Enter vendor website'}),
            'vendor_description': forms.Textarea(attrs={'placeholder': 'Enter vendor description', 'rows': 4}),
            'vendor_VAT': forms.TextInput(attrs={'placeholder': 'Enter VAT number'}),
            'vendor_TRN_or_CRN': forms.TextInput(attrs={'placeholder': 'Enter TRN or CRN number'}),
        }              

class TimeSheetForm(forms.ModelForm):
    class Meta:
        model = TimeSheet
        fields = [
            'voucher_no',
            'voucherType',
            'vehicle_reg_no', 
            'vehicle_name', 
            'project_location', 
            'client', 
            'duration', 
            'PO_reference_no', 
            'description', 
            'date', 
            'driver_name', 
            'operator_name',
            'enable_header',
            'enable_footer',
            'enable_signature',
            
            ]
        
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'voucherType': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'vehicle_reg_no': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_name': forms.Select(attrs={'class': 'form-control'}),
            'project_location': forms.TextInput(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={'class': 'form-control'}),
            'PO_reference_no': forms.TextInput(attrs={'class': 'form-control'}),
            'driver_name': forms.Select(attrs={'class': 'form-control'}),
            'operator_name': forms.Select(attrs={'class': 'form-control'}),
            'enable_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_signature': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
        }
        labels = {
            'voucher_no': _('Voucher No'),
            'voucherType': _('Voucher Type'),
            'date': _('Date'),
            'description': _('Description'),
            'vehicle_reg_no': _('Vehicle reg No'),
            'vehicle_name': _('Fleet No'),
            'project_location': _('Project Location'),
            'client': _('Client'),
            'duration': _('Duration'),
            'PO_reference_no': _('PO ref No'),
            'driver_name': _('Driver Name'),
            'operator_name': _('Operator Name'),
            'enable_header': _('Enable Header'),
            'enable_footer': _('Enable Footer'),
            'enable_signature': _('Enable Signature'),

        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass

        # Voucher type filter 
        filter_voucher_types(self, [8]) 
    
        # client filter by Groups 
        self.fields['client'].queryset = get_ledgers_by_group_ids(29)      
        
        

class TimeSheetDetailForm(forms.ModelForm):
    class Meta:
        model = TimeSheetDetail
        fields = [
            'date', 
            'start_time', 
            'end_time', 
            'break_hours', 
            'total_hours_worked', 
            'ot', 
            'job_location', 
            'signature'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'break_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_hours_worked': forms.NumberInput(attrs={'class': 'form-control'}),
            'ot': forms.NumberInput(attrs={'class': 'form-control'}),
            'job_location': forms.TextInput(attrs={'class': 'form-control'}),
            'signature': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'date': _('Date'),
            'start_time': _('Start Time'),
            'end_time': _('End Time'),
            'break_hours': _('Break Hours'),
            'total_hours_worked': _('Total Hours Worked'),
            'ot': _('OT'),
            'job_location': _('Job Location'),
            'signature': _('Signature'),
        }

TimeSheetDetailFormSet = inlineformset_factory(
    TimeSheet,
    TimeSheetDetail,
    fields=['date', 'start_time', 'end_time', 'break_hours', 'ot', 'total_hours_worked', 'job_location', 'signature'],
    extra=0,  # No extra forms
    can_delete=True,
    validate_min=False,  # Don't require minimum forms
    validate_max=False,  # Don't validate maximum
)

class FleetQuotationForm(forms.ModelForm):
    class Meta:
        model = FleetQuotation
        fields = [
            'quotation_no', 'date', 'company_name', 'company_logo', 'company_address', 
            'customer', 'customer_address', 'text', 'terms_and_condition', 
            'note', 'description'
        ]
        widgets = {
            'quotation_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'company_name': forms.Select(attrs={'class': 'form-control'}),
            'company_logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'placeholder': 'Enter Company Address', 'class': 'form-control', 'rows': 3}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'customer_address': forms.Textarea(attrs={'placeholder': 'Enter Customer Address', 'class': 'form-control', 'rows': 3}),
            'text': forms.Textarea(attrs={'placeholder': 'Enter Text', 'class': 'form-control', 'rows': 3}),
            'terms_and_condition': forms.Textarea(attrs={'placeholder': 'Enter Terms and Conditions', 'class': 'form-control', 'rows': 3}),
            'note': forms.Textarea(attrs={'placeholder': 'Enter Note', 'class': 'form-control', 'rows': 2}),
            'description': forms.Textarea(attrs={'placeholder': 'Enter Description', 'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'quotation_no': 'Quotation ',
            'date': 'Date',
            'company_name': 'Company Name',
            'company_logo': 'Company Logo',
            'company_address': 'Company Address',
            'customer': 'Client',
            'customer_address': 'Customer Address',
            'text': 'Text',
            'terms_and_condition': 'Terms and Conditions',
            'note': 'Note',
            'description': 'Description',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # customer filter by Groups 
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)      


class FleetQuotationItemForm(forms.ModelForm):
    class Meta:
        model = FleetQuotationItem
        fields = [
            'vehicle', 'details', 'quantity', 'rate_per_hr', 'rate_per_day', 
            'rate_per_month', 'unit', 'no_of_unit', 'total_amount'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control vehicle'}),
            'details': forms.Textarea(attrs={
                'placeholder': 'Enter Details', 
                'class': 'form-control details', 
                'rows': 2
            }),
            'quantity': forms.NumberInput(attrs={
                'placeholder': 'Enter Quantity', 
                'class': 'form-control quantity'
            }),
            'rate_per_hr': forms.NumberInput(attrs={
                'placeholder': 'Rate per Hour', 
                'class': 'form-control rate-per-hr'
            }),
            'rate_per_day': forms.NumberInput(attrs={
                'placeholder': 'Rate per Day', 
                'class': 'form-control rate-per-day'
            }),
            'rate_per_month': forms.NumberInput(attrs={
                'placeholder': 'Rate per Month', 
                'class': 'form-control rate-per-month'
            }),
            'unit': forms.Select(attrs={'class': 'form-control unit'}),
            'no_of_unit': forms.NumberInput(attrs={
                'placeholder': 'Enter Number of Units', 
                'class': 'form-control no-of-unit'
            }),
            'total_amount': forms.NumberInput(attrs={
                'placeholder': 'Total Amount', 
                'class': 'form-control total-amount', 
                'readonly': 'readonly'
            }),
        }
        labels = {
            'vehicle': 'Fleet No',
            'details': 'Remarks',
            'quantity': 'Quantity',
            'rate_per_hr': 'Rate/Hr',
            'rate_per_day': 'Rate/Day',
            'rate_per_month': 'Rate/Month',
            'unit': 'Unit',
            'no_of_unit': 'No of Units',
            'total_amount': 'Total ',
        }


FleetQuotationItemFormSet = inlineformset_factory(
    FleetQuotation,             # Parent
    FleetQuotationItem,         # Child
    form=FleetQuotationItemForm,
    extra=1,
    can_delete=True
)


class RepairAndMaintenanceForm(forms.ModelForm):
    class Meta:
        model = RepairAndMaintenance
        fields = [
            'voucher_no',
            'voucherType',
            'bill_no',
            'date',
            'payment_mode',
            'party',
            'reference_no',
            'VAT_no',
            'date_on_bill',
            'vehicle_name',
            'vehicle_driver',
            'grand_total_amount',
        ]
        labels = {
            'voucher_no': _('Voucher Number'),
            'voucherType': _('Voucher Type'),
            'bill_no': _('Bill Number'),
            'date': _('Date'),
            'payment_mode': _('Payment Mode'),
            'party': _('Party Name'),
            'reference_no': _('Reference Number'),
            'VAT_no': _('VAT Number'),
            'date_on_bill': _('Date on Bill'),
            'vehicle_name': _('Fleet No'),
            'vehicle_driver': _('Vehicle Driver'),
            'grand_total_amount': _('Grand Total Amount'),
        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'bill_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter bill number'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'party': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter party name'}),
            'reference_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reference number'}),
            'VAT_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter VAT number'}),
            'date_on_bill': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'vehicle_name': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_driver': forms.Select(attrs={'class': 'form-control'}),
            'grand_total_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter grand total amount'}),
        }


class RepairAndMaintenanceItemForm(forms.ModelForm):
    class Meta:
        model = RepairAndMaintenanceItem
        fields = [
            'narration',
            'bill_amount',
            'VAT_amount',
            'total_amount',
        ]
        labels = {
            'narration': _('Narration'),
            'bill_amount': _('Bill Amount'),
            'VAT_amount': _('VAT Amount'),
            'total_amount': _('Total Amount'),
        }
        widgets = {
            'narration': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter narration', 'rows': 3}),
            'bill_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter bill amount'}),
            'VAT_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter VAT amount'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter total amount'}),
        }

class FleetContractForm(forms.ModelForm):
    class Meta:
        model = FleetContract
        fields = [
            'voucher_no', 'contract_no', 'vehicle', 'date', 'end_date', 'operator_1',
            'customer', 'voucherType',
             'note', 'remark',
        ]
        labels = {
            'voucher_no': _('Voucher No'),
            'contract_no': _('Contract Number'),
            'vehicle': _('Fleet'),
            'date': _('Contract Date'),
            'end_date': _('End Date'),
            'operator_1': _('Primary Operator'),
            'customer': _('Client'),
            'note': _('Additional Notes'),
            'remark': _('Remarks'),
        }
        widgets = {
            'voucher_no': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'contract_no': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'operator_1': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),

            
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass

        # Voucher type filter 
        filter_voucher_types(self, [7]) 
    
        # customer filter by Groups 
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)     



class FleetCustomerForm(forms.ModelForm):
    class Meta:
        model = FleetCustomer
        fields = [
            'customer_name', 'customer_mobile', 'customer_phone', 'customer_email', 
            'customer_address_1', 'customer_address_2', 'customer_country', 'customer_state', 
            'customer_city', 'customer_zipcode', 'customer_website', 'customer_description', 
            'customer_VAT', 'customer_TRN_or_CRN'
        ]
        
        labels = {
            'customer_name': 'Client Name',
            'customer_mobile': 'Mobile',
            'customer_phone': 'Phone',
            'customer_email': 'Client Email',
            'customer_address_1': 'Address Line 1',
            'customer_address_2': 'Address Line 2',
            'customer_country': 'Country',
            'customer_state': 'State',
            'customervendor_city': 'City',
            'customer_zipcode': 'Zipcode',
            'customer_website': 'Website',
            'customer_description': 'Description',
            'customer_VAT': 'VAT Number',
            'customer_TRN_or_CRN': 'CR Number',
        }
        
        widgets = {
    'customer_name': forms.TextInput(attrs={
        'placeholder': 'Enter customer name',
        'class': 'form-control'
    }),
    'customer_mobile': forms.TextInput(attrs={
        'placeholder': 'Enter mobile number',
        'class': 'form-control'
    }),
    'customer_phone': forms.TextInput(attrs={
        'placeholder': 'Enter phone number',
        'class': 'form-control'
    }),
    'customer_email': forms.EmailInput(attrs={
        'placeholder': 'Enter email address',
        'class': 'form-control'
    }),
    'customer_address_1': forms.Textarea(attrs={
        'placeholder': 'Enter address line 1',
        'rows': 2,
        'class': 'form-control'
    }),
    'customer_address_2': forms.Textarea(attrs={
        'placeholder': 'Enter address line 2',
        'rows': 2,
        'class': 'form-control'
    }),
    'customer_country': forms.TextInput(attrs={
        'placeholder': 'Enter country',
        'class': 'form-control'
    }),
    'customer_state': forms.TextInput(attrs={
        'placeholder': 'Enter state',
        'class': 'form-control'
    }),
    'customer_city': forms.TextInput(attrs={
        'placeholder': 'Enter city',
        'class': 'form-control'
    }),
    'customer_zipcode': forms.TextInput(attrs={
        'placeholder': 'Enter zipcode',
        'class': 'form-control'
    }),
    'customer_website': forms.URLInput(attrs={
        'placeholder': 'Enter customer website',
        'class': 'form-control'
    }),
    'customer_description': forms.Textarea(attrs={
        'placeholder': 'Enter customer description',
        'rows': 4,
        'class': 'form-control'
    }),
    'customer_VAT': forms.TextInput(attrs={
        'placeholder': 'Enter VAT number',
        'class': 'form-control'
    }),
    'customer_TRN_or_CRN': forms.TextInput(attrs={
        'placeholder': ' CRN number',
        'class': 'form-control'
    }),
}



class StaffCategoryForm(forms.ModelForm):
    class Meta:
        model = StaffCategory
        fields = ['name']

        labels = {
            'name': _('Category Name'),
        }

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'})
        }
        
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = '__all__'

        labels = {
            'staff_category': _('Staff Category'),
            'staff_id': _('Staff ID'),
            'full_name': _('Full Name'),
            'staff_image': _('Staff Image'),
            'gender': _('Gender'),
            'date_of_birth': _('Date of Birth'),
            'nationality': _('Nationality'),
            'civil_id_or_passport_no': _('Civil ID / Passport No'),
            'marital_status': _('Marital Status'),
            'contact_number': _('Contact Number'),
            'email': _('Email'),
            'address': _('Address'),
            'department': _('Department'),
            'job_title': _('Job Title'),
            'joining_date': _('Joining Date'),
            'employment_type': _('Employment Type'),
            'basic_salary': _('Basic Salary'),
            'allowances': _('Allowances'),
            'bank_account_no': _('Bank Account No'),
            'bank_name': _('Bank Name'),
            'emergency_contact_name': _('Emergency Contact Name'),
            'emergency_contact_number': _('Emergency Contact Number'),
            'visa_expiry_date': _('Visa Expiry Date'),
            'contract_end_date': _('Contract End Date'),
            'passport_expiry_date': _('Passport Expiry Date'),
            'resident_id_number': _('Resident ID Number'),
            'resident_id_expiry_date': _('Resident ID Expiry Date'),
            'license_type': _('License Type'),
            'license_number': _('License Number'),
            'license_expiry_date': _('License Expiry Date'),
            'status': _('Status'),
            'remarks': _('Remarks'),
        }

        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'visa_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
            'passport_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'resident_id_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'license_expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'remarks': forms.Textarea(attrs={'rows': 2}),
            'staff_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        
        
class DocumentForm(forms.ModelForm):
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
        }        
        
        
class SimpleQuotationForm(forms.ModelForm):
    class Meta:
        model = SimpleQuotation
        fields = ['date',  'customer', 'enable_header', 'enable_footer', 'enable_signature', 'voucher_no',
            'voucherType', 'quotation_no', 'terms_and_condition', 'remark', 'staff', 'attention', 'attention_contact']
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'enable_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_signature': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter remarks'}),
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'attention': forms.TextInput(attrs={'class': 'form-control'}),
            'attention_contact': forms.TextInput(attrs={'class': 'form-control'}),
            
        }
        
        labels = {
            'quotation_no': _('Quotation No'),
            'voucher_no': _('Voucher No'),
            'voucherType': _('Voucher Type'),
            'date': _('Date'),
            'customer': _('Client'),
            'terms_and_condition': _('Terms and Conditions'),
            'remark': _('Remark'),
            'enable_header': _('Enable Header'),
            'enable_footer': _('Enable Footer'),
            'enable_signature': _('Enable Signature'),
            'staff': _('Staff'),
            'attention': _('Attention'),
            'attention_contact': _('Attention Contact'),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass

        # Voucher type filter 
        filter_voucher_types(self, [9]) 
    
        # customer filter by Groups 
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)       


class SimpleQuotationDetailsForm(forms.ModelForm):
    class Meta:
        model = SimpleQuotationDetails
        fields = ['vehicle', 'description', 'quantity', 'rent', 'period', 'tax_amount', 'total_amount']
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Item Description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly':'readonly'}),
        }
        labels = {
            'vehicle': _('Fleet '),
            'description': _('Description'),
            'quantity': _('Quantity'),
            'rent': _('Rent'),
            'period': _('Period'),
            'tax_amount': _('Tax Amount'),
            'total_amount': _('Total Amount'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['period'].initial = "Month"    


# Formset for multiple details
SimpleQuotationDetailsFormSet = inlineformset_factory(
    parent_model=SimpleQuotation,
    model=SimpleQuotationDetails,
    form=SimpleQuotationDetailsForm,
    extra=1,
    can_delete=True
)

class DeliveryContractForm(forms.ModelForm):
    class Meta:
        model = DeliveryContract
        fields = [
            'voucher_no', 'date', 'voucherType', 'customer',
            'payment_mode','other_ref',
            'buyer_order_no', 'is_taxable', 'enable_header', 'enable_footer', 
            'enable_signature', 'invoice_type', 'supplier_ref', 'delivery_person',
            'lpo_date', 'location',
           'salesman', 'ref_no',
            'onhire_date_time', 'site_contact_person', 'contact_no', 'terms_and_condition',
        ]
        labels = {
            'invoice_no': _(' Invoice No'),
            'voucher_no': _('Contract No'),
            'date': _('Contract Date'),
            'voucherType': _('Voucher Type'),
            'customer': _('Client'),
            'payment_mode': _('Mode of Payment'),
            'other_ref': _('Ordered By'),
            'buyer_order_no': _('LPO'),
            'is_taxable': _('Is Taxable'),
            'enable_header': _('Enable Header'),
            'enable_footer': _('Enable Footer'),
            'enable_signature': _('Enable Signature'),
            'invoice_type': _('Contract Type'),
            'lpo_date': _('LPO Date'),
            'location': _('Location'),
            'salesman': _('Salesman'),
            'ref_no': _('Reference No'),
            'onhire_date_time': _('On-Hire Date & Time'),
            'site_contact_person': _('Site Contact Person'),
            'contact_no': _('Contact Number'),
            'supplier_ref': _('Supplier Reference'),
            'terms_and_condition': _('Terms & Conditions'),
            'delivery_person': _('Delivery Person'),

        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'voucherType': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'supplier_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'other_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'buyer_order_no': forms.TextInput(attrs={'class': 'form-control'}),
            'is_taxable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_signature': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invoice_no': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'lpo_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salesman': forms.Select(attrs={'class': 'form-control'}),
            'ref_no': forms.TextInput(attrs={'class': 'form-control'}),
            'onhire_date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'site_contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
            'terms_and_condition': forms.Textarea(attrs={'class': 'form-control'}),
            'delivery_person': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        # Optional fields
        self.fields['lpo_date'].required = False
        self.fields['location'].required = False
        
        self.fields['salesman'].required = False
        self.fields['ref_no'].required = False
        self.fields['onhire_date_time'].required = False
        self.fields['site_contact_person'].required = False
        self.fields['contact_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass
        
        # Voucher type filter - only Delivery Contract (ID: 12)
        filter_voucher_types(self, [12])
        # customer filter by Groups
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)
        


class DeliveryContractDetailsForm(forms.ModelForm):
    class Meta:
        model = DeliveryContractDetails
        fields = [
            'vehicle', 'vehicle_model', 'description', 'location', 'amount',
            'tax', 'tax_amount', 'total_amount',
            'period', 'quantity', 'unit_rate',
            'from_date', 'to_date', 'IsCleared',
        ]
        labels = {
            'vehicle': _('Vehicle'),
            'vehicle_model': _('Equipment Model'),
            'description': _('Description'),
            'location': _('Details'),
            'amount': _('Amount'),
            'tax': _('Tax (%)'),
            'tax_amount': _('Tax Amount'),
            'total_amount': _('Total Amount'),
            'period': _('Period'),
            'quantity': _('Quantity'),
            'unit_rate': _('Unit Rate'),
            'from_date': _('From Date'),
            'to_date': _('To Date'),
            'IsCleared': _('Invoiced'),
        }
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'IsCleared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


DeliveryContractDetailsFormSet = inlineformset_factory(
    parent_model=DeliveryContract,
    model=DeliveryContractDetails,
    form=DeliveryContractDetailsForm,
    extra=1,
    can_delete=True
)

class DeliveryContractSparepartsForm(forms.ModelForm):
    class Meta:
        model = DeliveryContractSpareParts
        fields = [
            'sparepart', 'part_no', 'quantity', 'rate', 'amount', 'warranty', 'condition', 
        ]
        widgets = {
            'sparepart': forms.TextInput(attrs={'class': 'form-control'}),
            'part_no': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'warranty': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
        }


        

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'voucher_no', 'date', "voucherType" ,'customer', 'ledger', 'due_date',
            'payment_mode', 'supplier_ref', 'other_ref',
            'buyer_order_no', 'is_taxable', 'enable_header', 'enable_footer', 'enable_signature', 'invoice_no',
            'hire_contract_no', 'invoice_type', 'location', 'staff', 'lpo_date',
        ]
        labels = {
            'invoice_no': _('Invoice No'),
            'voucher_no': _('Voucher No'),
            'date': _('Invoice Date'),
            'voucherType': _('Voucher Type'),
            'customer': _('Client'),
            'ledger': _('Ledger'),
            'due_date': _('Due Date'),

            'payment_mode': _('Mode of Payment'),
            'supplier_ref': _('Supplier Reference'),
            'other_ref': _('Other Reference'),
            'buyer_order_no': _('PO'),
            'is_taxable': _('Is Taxable'),
            'enable_header': _('Enable Header'),
            'enable_footer': _('Enable Footer'),
            'enable_signature': _('Enable Signature'),
            'invoice_type': _('Invoice Type'),
            'location': _('Location'),
            'lpo_date': _('LPO Date'),
            'staff': _('Staff'),
            'hire_contract_no': _('Hire Contract No'),
        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'voucherType': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'ledger': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'supplier_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'other_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'buyer_order_no': forms.TextInput(attrs={'class': 'form-control'}),
            'is_taxable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_signature': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'lpo_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass
        
        # Ledger filter by Groups cash account & Bank account
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(8, 5, 29)
        # Voucher type filter 
        filter_voucher_types(self, [2])
        # customer filter by Groups 
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)
        
           


class InvoiceDetailsForm(forms.ModelForm):
    class Meta:
        model = InvoiceDetails
        fields = [
            'vehicle', 'vehicle_model', 'description', 'location', 'amount',
            'tax', 'tax_amount', 'total_amount',
            'period', 'quantity', 'unit_rate', 
            'from_date', 'to_date',
        ]
        labels = {
            'vehicle': _('Equipment'),
            'vehicle_model': _('Equipment Model'),
            'description': _('Description'),
            'location': _('Details'),
            'amount': _('Amount'),
            'tax': _('Tax (%)'),
            'tax_amount': _('Tax Amount'),
            'total_amount': _('Total Amount'),
            'period': _('Period'),
            'quantity': _('Quantity'),
            'unit_rate': _('Unit Rate'),
            'from_date': _('From Date'),
            'to_date': _('To Date'),
        }
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'from_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'to_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


InvoiceDetailsFormSet = inlineformset_factory(
    parent_model=Invoice,
    model=InvoiceDetails,
    form=InvoiceDetailsForm,
    extra=1,
    can_delete=True
)

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'website', 'email', 'phone']
        labels = {
            'name': _('Company Name'),
            'website': _('Website'),
            'email': _('Email'),
            'phone': _('Phone'),
        }


class CompanyDocumentForm(forms.ModelForm):
    class Meta:
        model = CompanyDocument
        fields = ['name', 'file', 'reminder_date', 'expiry_date']
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Name'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'reminder_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }


class FleetHireForm(forms.ModelForm):
    class Meta:
        model = FleetHire
        fields = [
            "voucher_no",
            "date",
            "voucherType",
            "payment_mode",
            "supplier",
            'ledger',
            "invoice_no",
            "invoice_date",
            "hire_contract",
            "subtotal",
            "vat",
            "other_charges",
            "grand_total",
        ]
        widgets = {
            "invoice_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "voucherType": forms.Select(attrs={"class": "form-select"}),
            "payment_mode": forms.Select(attrs={"class": "form-select"}),
            "voucher_no": forms.TextInput(attrs={"class": "form-control", 'readonly': True}),
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "ledger": forms.Select(attrs={"class": "form-select"}),
            "invoice_no": forms.TextInput(attrs={"class": "form-control"}),
            "hire_contract": forms.TextInput(attrs={"class": "form-control"}),
            "subtotal": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vat": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "other_charges": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "grand_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
        
        labels = {
            "invoice_date": _("Invoice Date"),
            "date": _("Date"),
            "voucherType": _("Voucher Type"),
            "payment_mode": _("Payment Mode"),
            "voucher_no": _("Voucher Number"),
            "supplier": _("Supplier"),
            "ledger": _("Ledger"),
            "invoice_no": _("Invoice Number"),
            "hire_contract": _("Hire Contract No"),
            "subtotal": _("Subtotal"),
            "vat": _("VAT"),
            "other_charges": _("Other Charges"),
            "grand_total": _("Grand Total"),   
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass

        # Ledger filter by Groups cash account & Bank account
        self.fields['ledger'].queryset = get_ledgers_by_group_ids(8, 5, 28)

        # Voucher type filter 
        filter_voucher_types(self, [1])    
        
       # supplier filter by Groups 
        self.fields['supplier'].queryset = get_ledgers_by_group_ids(28).filter(supplier_type='Rental')  
        


class FleetHireDetailsForm(forms.ModelForm):
    class Meta:
        model = FleetHireDetails
        fields = [
            "vehicle",
            "reg_no",
            "start_date",
            "end_date",
            "unit",
            "no_of_unit",
            "rate_per_period",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-select"}),
            "reg_no": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "unit": forms.Select(attrs={"class": "form-select"}),
            "no_of_unit": forms.NumberInput(attrs={"class": "form-control"}),
            "rate_per_period": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
        labels = {
            "vehicle": _('Equipment'),
            "reg_no": _('Reg No'),
            "start_date": _('Start Date'),
            "end_date": _('End Date'),
            "unit": _('Unit'),
            "no_of_unit": _('Unit'),
            "rate_per_period": _('Rate per Period'),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only non-owned vehicles
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_owned=False)
            
FleetHireDetailsFormSet = inlineformset_factory(
    parent_model=FleetHire,
    model=FleetHireDetails,
    form=FleetHireDetailsForm,
    extra=1,  # number of empty forms shown by default
    can_delete=True,  # allows deleting existing details
)                

class VouchersForm(forms.ModelForm):
    class Meta:
        model = Vouchers
        fields = ['VoucherType', 'VoucherName', 'Prefix', 'Suffix', 'MinLength', 'StartingNo', 'ledger']
        labels = {
            'VoucherType': 'Voucher Type',
            'VoucherName': 'Voucher Name',
            'Prefix': 'Prefix',
            'Suffix': 'Suffix',
            'MinLength': 'Minimum Length',
            'StartingNo': 'Starting Number',
            'ledger': 'Ledger',
        }
        widgets = {
            'VoucherType': forms.TextInput(attrs={'class': 'form-control'}),
            'VoucherName': forms.TextInput(attrs={'class': 'form-control'}),
            'Prefix': forms.TextInput(attrs={'class': 'form-control'}),
            'Suffix': forms.TextInput(attrs={'class': 'form-control'}),
            'MinLength': forms.NumberInput(attrs={'class': 'form-control'}),
            'StartingNo': forms.NumberInput(attrs={'class': 'form-control'}),
            'ledger': forms.Select(attrs={'class': 'form-control'}),
        }        

class VehicleEMIForm(forms.ModelForm):
    class Meta:
        model = VehicleEMI
        fields = [
            'vehicle', 'title', 'start_date', 'end_date', 
            'reminder_day', 'amount', 'reminder_days_before'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Car Loan EMI, Bike Loan',
                'required': True
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'reminder_day': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '31',
                'placeholder': '7',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0',
                'placeholder': '5000.000',
                'required': True
            }),
            'reminder_days_before': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '30',
                'placeholder': '4',
                'required': True
            }),
            
        }
        labels = {
            'vehicle': 'Select Equipment',
            'title': 'EMI Title',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'reminder_day': 'EMI Payment Day (1-31)',
            'amount': 'Monthly Amount',
            'reminder_days_before': 'Warning Days Before Due Date',
            
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError('End date must be after start date.')
        
        return cleaned_data

class OffHireForm(forms.ModelForm):
    class Meta:
        model = OffHire
        fields = [
            'voucher_no',
            'date',
            'voucherType',
            'delivery_contract',
            'customer',
            'offhire_date_time',
            'remarks',
        ]
        widgets = {
            'voucher_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated',
                'readonly': 'readonly'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'voucherType': forms.Select(attrs={
                'class': 'form-control'
            }),
            'delivery_contract': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_delivery_contract'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_customer'
            }),
            'offhire_date_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional remarks...'
            }),
        }
        labels = {
            'voucher_no': 'Voucher No',
            'date': 'OffHire Date',
            'voucherType': 'Voucher Type',
            'delivery_contract': 'Delivery Contract',
            'customer': 'Client',
            'offhire_date_time': 'OffHire Date & Time',
            'remarks': 'Remarks',
        }        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make voucher_no field not required for form validation
        self.fields['voucher_no'].required = False
        
        if not self.instance.pk and 'voucherType' in self.data:
            try:
                voucher_type = Vouchers.objects.get(pk=self.data['voucherType'])
                self.fields['voucher_no'].initial = voucher_type.get_next_voucher_number()
            except:
                pass
        
        # Voucher type filter 
        filter_voucher_types(self, [15])
        # customer filter by Groups
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29) 


class POMasterForm(forms.ModelForm):
    class Meta:
        model = POMaster
        fields = [
            'voucher_no',
            'voucherType',
            'PO_no',
            'PO_date',
            'quote_ref',
            'quote_ref_date',
            'payment_terms1',
            'payment_terms2',
            'supplier',
            'delivery_date',
            'kind_attn',
        ]

        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control'}),
            'voucherType': forms.Select(attrs={'class': 'form-control'}),
            'PO_no': forms.TextInput(attrs={'class': 'form-control'}),
            'PO_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'quote_ref': forms.TextInput(attrs={'class': 'form-control'}),
            'quote_ref_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_terms1': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_terms2': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'kind_attn': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # supplier filter by Groups 
        self.fields['supplier'].queryset = get_ledgers_by_group_ids(28)  

        # Voucher type filter 
        filter_voucher_types(self, [27])
         


class PODetailsForm(forms.ModelForm):
    class Meta:
        model = PODetails
        fields = [
            'description',
            'units',
            'quantity',
            'rate',
            'amount',
        ]

        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'units': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }


PODetailsFormSet = inlineformset_factory(
    POMaster,
    PODetails,
    form=PODetailsForm,
    extra=1,
    can_delete=True
)

class RepairMasterForm(forms.ModelForm):

    class Meta:
        model  = RepairMaster
        fields = [
            'voucher_no', 'voucherType', 'date', 'vehicle', 'repair_type',
            'spareparts_total', 'labourcharge_total', 'subtotal',
            'discount', 'vat', 'grand_total',
            'supplier', 'payment_mode', 'description', 'invoice_no', 'invoice_date',
            'category', 'client', 'current_km', 'next_service_km', 'current_hr', 'next_service_hr', 
            'cost_center' , 'staff' , 'ref_voucher_no' , 'remark', 'next_service_date',
        ]
        widgets = {
            'voucher_no': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Auto-generated',
            }),
            'voucherType': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
            'vehicle': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'repair_type': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'id': 'repairType',
                'onchange': 'toggleRepairType()',
            }),
            'spareparts_total': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'readonly': True,
                'id': 'sparePartsTotalInput',
            }),
            'labourcharge_total': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'readonly': True,
                'id': 'labourTotalInput',
            }),
            'subtotal': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'readonly': True,
                'id': 'subtotalInput',
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'id': 'discountInput',
                'oninput': 'calcGrandTotal()',
                'placeholder': '0.000',
            }),
            'vat': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001',
                'id': 'vatInput',
            }),
            'grand_total': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001',
                'id': 'hiddenGrandTotal',
            }),
            'supplier': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'payment_mode': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Repair notes / description...',
            }),
            'invoice_no': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Invoice Number',
            }),
            'invoice_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),

            'category': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'client': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'current_km': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
            }),
            'next_service_km': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
            }),
            'current_hr': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
            }),
            'next_service_hr': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'step': '0.001',
            }),
            'cost_center': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'staff': forms.Select(attrs={
                'class': 'form-control form-control-sm',
            }),
            'ref_voucher_no': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Reference Voucher Number',
            }),
            'remark': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 1,
                'placeholder': 'Notes / remark...',
            }),
            'next_service_date': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
            }),
        }

        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Supplier — only Sundry Creditors (group ID 21), adjust if needed
      
        self.fields['supplier'].queryset = get_ledgers_by_group_ids(28)
        self.fields['client'].queryset = get_ledgers_by_group_ids(29)
        
        self.fields['supplier'].empty_label = '-- Select Supplier --'
        self.fields['supplier'].required = False

        self.fields['vehicle'].empty_label    = '-- Select Equipment --'

        # Voucher type filter 
        filter_voucher_types(self, [10])   

        # Not required on form level — view handles conditional validation
        for field in ['spareparts_total', 'labourcharge_total', 'subtotal',
                      'discount', 'vat', 'payment_mode', 'description']:
            self.fields[field].required = False

    def clean(self):
        cleaned = super().clean()
        repair_type = cleaned.get('repair_type')

        if repair_type == 'Outsourced':
            if not cleaned.get('supplier'):
                self.add_error('supplier', 'Supplier is required for Outsourced repairs.')
            if not cleaned.get('payment_mode'):
                self.add_error('payment_mode', 'Payment mode is required for Outsourced repairs.')
            if not cleaned.get('grand_total'):
                self.add_error('grand_total', 'Grand Total is required for Outsourced repairs.')

        return cleaned


class SparePartsForm(forms.ModelForm):

    class Meta:
        model  = SpareParts
        fields = ['item_group','sparepart', 'part_no', 'quantity', 'rate', 'amount', 'warranty']
        widgets = {
            'item_group': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'id': 'sp_item_group',
            }),
            'sparepart': forms.Select(attrs={
                'class': 'form-control form-control-sm',
                'id': 'sp_sparepart',
            }),
            'part_no': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'id': 'sp_part_no',
                'placeholder': 'Optional',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'min': '0',
                'id': 'sp_quantity',
                'placeholder': '0.000',
                'oninput': 'calcSpareAmount()',
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'min': '0',
                'id': 'sp_rate',
                'placeholder': '0.000',
                'oninput': 'calcSpareAmount()',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001',
                'id': 'sp_amount',
                'placeholder': '0.000',
                'readonly': True,
                'style': 'background:#f8f9fa;',
            }),
            'warranty': forms.CheckboxInput(attrs={
                'id': 'sp_warranty',
                'style': 'width:18px;height:18px;cursor:pointer;',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sparepart'].queryset    = Item.objects.all()
        self.fields['item_group'].queryset = ItemGroup.objects.all()
        
        self.fields['sparepart'].empty_label = '-- Select Item --'
        self.fields['item_group'].empty_label = '-- Select Group --'
        self.fields['part_no'].required  = False
        self.fields['warranty'].required = False


class LabourChargeForm(forms.ModelForm):

    class Meta:
        model  = LabourCharge
        fields = ['description', 'hour', 'rate', 'amount']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'id': 'lc_description',
                'placeholder': 'e.g. Engine overhaul',
            }),
            'hour': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'min': '0',
                'id': 'lc_hour',
                'placeholder': '0.000',
                'oninput': 'calcLabourAmount()',
            }),
            'rate': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001', 'min': '0',
                'id': 'lc_rate',
                'placeholder': '0.000',
                'oninput': 'calcLabourAmount()',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm text-right',
                'step': '0.001',
                'id': 'lc_amount',
                'placeholder': '0.000',
                'readonly': True,
                'style': 'background:#f8f9fa;',
            }),
        }        

class ReplacementMasterForm(forms.ModelForm):
    class Meta:
        model = ReplacementMaster
        fields = [
            'voucher_no',
            'date',
            'voucherType',
            'delivery_contract',
            'customer',
            'replacement_date_time',
            'remarks',
            'delivery_person',
        ]
        widgets = {
            'voucher_no': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Auto-generated',
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'voucherType': forms.Select(attrs={
                'class': 'form-control',
            }),
            'delivery_contract': forms.Select(attrs={
                'class': 'form-control',
            }),
            'customer': forms.Select(attrs={
                'class': 'form-control',
            }),
            'replacement_date_time': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional remarks...',
            }),
            'delivery_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery person name',
            }),
        }        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)      
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)

        # Voucher type filter 
        filter_voucher_types(self, [28])       


class ReturnSparePartsMasterForm(forms.ModelForm):
    class Meta:
        model = ReturnSparePartsMaster
        fields = ['voucher_no', 'date', 'voucherType', 'ledger',]
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'voucherType': forms.Select(attrs={'class': 'form-control', 'id': 'id_voucherType'}),
            'ledger': forms.Select(attrs={'class': 'form-control', 'id': 'id_ledger'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)            
        # Voucher type filter 
        filter_voucher_types(self, [31])      


class ReturnSparePartsDetailsForm(forms.ModelForm):
    class Meta:
        model = ReturnSparePartsDetails
        fields = ['item_group', 'sparepart', 'part_no', 'quantity', 'rate', 'amount', 'condition']
        widgets = {
            'item_group': forms.Select(attrs={'class': 'form-control'}),
            'sparepart': forms.Select(attrs={'class': 'form-control'}),
            'part_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Part No'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'readonly': 'readonly'}),
            'condition': forms.Select(attrs={'class': 'form-control'}),
        }

# rows against one ReturnSparePartsMaster the standard Django way.
ReturnSparePartsDetailsFormSet = inlineformset_factory(
    ReturnSparePartsMaster,
    ReturnSparePartsDetails,
    form=ReturnSparePartsDetailsForm,
    fields=['item_group', 'sparepart', 'part_no', 'quantity', 'rate', 'amount', 'condition'],
    extra=1,
    can_delete=True,
)

class ServiceDepartmentForm(forms.ModelForm):

    class Meta:
        model = ServiceDepartment

        fields = [
            'vehicle',
            'offhire_date',
            'customer',
            'status',
            'staff',
        ]

        labels = {
            'vehicle': 'Equipment',
            'customer': 'Customer',
            'staff': 'Staff',
            'status': 'Status',
        }

        widgets = {
            'vehicle': forms.Select(attrs={
                'class': 'form-control',
            }),

            'offhire': forms.Select(attrs={
                'class': 'form-control',
            }),

            'offhire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),

            'customer': forms.Select(attrs={
                'class': 'form-control',
            }),

            'status': forms.Select(attrs={
                'class': 'form-control',
            }),

            'staff': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only vehicles in 'Service' status ('3').
        # On edit, also keep the job's own vehicle (it may be Free after Move To Yard).
        vehicle_filter = Q(status='3')
        if self.instance and self.instance.pk:
            vehicle_filter |= Q(pk=self.instance.vehicle_id)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(vehicle_filter).order_by('vehicle_name')

        self.fields['vehicle'].empty_label = 'Select Equipment'
        self.fields['customer'].empty_label = 'Select Customer'
        self.fields['staff'].empty_label = 'Select Staff'