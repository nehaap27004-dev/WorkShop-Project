from django import forms

from fleet_app.common import filter_voucher_types, get_ledgers_by_group_ids
from .models import *
from django.forms import modelformset_factory
from django.forms import inlineformset_factory

from item_master.models import Customer


class ManufacturerForm(forms.ModelForm):
    class Meta:
        model = Manufacturer
        fields = ['manufacturer_name', 'manufacturer_logo']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manufacturer_name'].widget.attrs.update({
            'placeholder': 'Enter manufacturer name'
        })

    manufacturer_name = forms.CharField(
        label='Manufacturer Name',
        max_length=100,
        required=True,
    )
    manufacturer_logo = forms.ImageField(
        label='Manufacturer Logo',
        required=False,
    )


class VehicleCategoryForm(forms.ModelForm):
    class Meta:
        model = VehicleCategory
        fields = ['category_name']
        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'form-control',  # Add a class for styling if needed
                'placeholder': 'Enter vehicle category name',  # Placeholder text
                'id': 'id_vehicle_category',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(VehicleCategoryForm, self).__init__(*args, **kwargs)
        # Customize the labels if needed
        self.fields['category_name'].label = "Category Name"  
        


class VehicleModelForm(forms.ModelForm):
    
    class Meta:
        model = VehicleModel
        fields = [
            'model_name', 'manufacturer', 'vehicle_category', 'seat_number', 'door_number', 
            'model_colour', 'model_range', 'model_year', 'fuel_type', 'CO2_emission', 
            'CO2_standard', 'model_transmission', 'model_power', 'model_horse_power'
        ]
        labels = {
            'model_name': 'Model Name',
            'manufacturer': 'Manufacturer',
            'vehicle_category': 'Vehicle Type',
            'seat_number': 'Number of Seats',
            'door_number': 'Number of Doors',
            'model_colour': 'Model Colour',
            'model_range': 'Range',
            'model_year': 'Model Year',
            'fuel_type': 'Fuel Type',
            'CO2_emission': 'CO2 Emission ',
            'CO2_standard': 'CO2 Standard',
            'model_transmission': 'Transmission Type',
            'model_power': 'Power',
            'model_horse_power': 'Horsepower'
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
            'rate_per_month',
            'is_owned',
            'supplier',
            
        ]
        labels = {
            'vehicle_category': 'Vehicle Category',
            'vehicle_name': 'Vehicle Name',
            'model': 'Vehicle Model',
            'vehicle_image': 'Vehicle Image',
            'license_plate_code': 'Licenseplate Code',
            'license_plate_number': 'Licenseplate Number',
            'vehicle_driver': 'Assigned Driver',
            'vehicle_second_driver': 'Second Driver',
            'driver_assignment_date': 'Driver Assignment Date',
            'vehicle_registration_date': 'Registration Date',
            'vehicle_cancellation_date': 'Cancellation Date',
            'RC_number': 'Mulki Number',
            'RC_file': 'RC File',
            'RC_expiry_date': 'Mulki Expiry Date',
            'chassis_number': 'Chassis Number',
            'engine_number': 'Engine Number',
            'last_odometer': 'Last Odometer Reading',
            'rate_per_hr' : 'Rate Per Hour',
            'rate_per_day': 'Rate Per Day',
            'rate_per_month': 'Rate Per Month',
            'is_owned': 'Is Owned',
            'supplier': 'Supplier',
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
            'rate_per_month': forms.NumberInput(attrs={'placeholder': 'Enter rate per month', 'class': 'form-control'}),
            
            'is_owned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
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
            'date': 'Date',
            'description': 'Description',
            'vehicle_reg_no': 'Vehicle reg No',
            'vehicle_name': 'Fleet No',
            'project_location': 'Project Location',
            'client': 'Client',
            'duration': 'Duration',
            'PO_reference_no': 'PO ref No',
            'driver_name': 'Driver Name',
            'operator_name': 'Operator Name',
            'enable_header': 'Enable Header',
            'enable_footer': 'Enable Footer',
            'enable_signature': 'Enable Signature',

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
            'voucher_no': 'Voucher Number',
            'bill_no': 'Bill Number',
            'date': 'Date',
            'payment_mode': 'Payment Mode',
            'party': 'Party Name',
            'reference_no': 'Reference Number',
            'VAT_no': 'VAT Number',
            'date_on_bill': 'Date on Bill',
            'vehicle_name': 'Fleet No',
            'vehicle_driver': 'Vehicle Driver',
            'grand_total_amount': 'Grand Total Amount',
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
            'narration': 'Narration',
            'bill_amount': 'Bill Amount',
            'VAT_amount': 'VAT Amount',
            'total_amount': 'Total Amount',
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
            'voucher_no': 'Voucher No',
            'contract_no': 'Contract Number',
            'vehicle': 'Fleet',
            'date': 'Contract Date',
            'end_date': 'End Date',
            'operator_1': 'Primary Operator',
            'customer': 'Client',
            'note': 'Additional Notes',
            'remark': 'Remarks',
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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter category name'})
        }
        
class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = '__all__'
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
            'voucherType',]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'enable_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_footer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_signature': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
        labels = {
            'date': 'Date',
            'customer': 'Client',
            'enable_header': 'Enable Header',
            'enable_footer': 'Enable Footer',
            'enable_signature': 'Enable Signature',
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
        fields = ['description', 'quantity', 'rent', 'period']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Item Description'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'period': forms.Select(attrs={'class': 'form-select'}),
        }


# Formset for multiple details
SimpleQuotationDetailsFormSet = inlineformset_factory(
    parent_model=SimpleQuotation,
    model=SimpleQuotationDetails,
    form=SimpleQuotationDetailsForm,
    extra=1,
    can_delete=True
)

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'voucher_no', 'date', "voucherType" ,'customer',
            'payment_mode', 'supplier_ref', 'other_ref',
            'buyer_order_no', 'is_taxable', 'enable_header', 'enable_footer', 'enable_signature',
        ]
        labels = {
            'voucher_no': 'Invoice Number',
            'date': 'Invoice Date',
            'voucherType': 'Voucher Type',
            'customer': 'Client',
            'payment_mode': 'Mode of Payment',
            'supplier_ref': 'Supplier Reference',
            'other_ref': 'Other Reference',
            'buyer_order_no': 'PO',
            'is_taxable': 'Is Taxable',
            'enable_header': 'Enable Header',
            'enable_footer': 'Enable Footer',
            'enable_signature': 'Enable Signature',
        }
        widgets = {
            'voucher_no': forms.TextInput(attrs={'class': 'form-control'}),
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
        filter_voucher_types(self, [2])
        # customer filter by Groups 
        self.fields['customer'].queryset = get_ledgers_by_group_ids(29)   


class InvoiceDetailsForm(forms.ModelForm):
    class Meta:
        model = InvoiceDetails
        fields = [
            'vehicle', 'location', 'amount',
            'tax', 'tax_amount', 'total_amount'
        ]
        labels = {
            'vehicle': 'Vehicle',
            'location': 'Details',
            'amount': 'Amount',
            'tax': 'Tax (%)',
            'tax_amount': 'Tax Amount',
            'total_amount': 'Total Amount',
        }
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
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
            "voucher_no": forms.TextInput(attrs={"class": "form-control"}),
            "supplier": forms.Select(attrs={"class": "form-select"}),
            "invoice_no": forms.TextInput(attrs={"class": "form-control"}),
            "hire_contract": forms.TextInput(attrs={"class": "form-control"}),
            "subtotal": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "vat": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "other_charges": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "grand_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
        
        labels = {
            "invoice_date": "Invoice Date",
            "date": "Date",
            "voucherType": "Voucher Type",
            "payment_mode": "Payment Mode",
            "voucher_no": "Voucher Number",
            "supplier": "Supplier",
            "invoice_no": "Invoice Number",
            "hire_contract": "Hire Contract No",
            "subtotal": "Subtotal",
            "vat": "VAT",
            "other_charges": "Other Charges",
            "grand_total": "Grand Total",   
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
        filter_voucher_types(self, [1])    
        
       # supplier filter by Groups 
        self.fields['supplier'].queryset = get_ledgers_by_group_ids(28)   


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
