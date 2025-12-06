from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from accounts_app.common import check_privilege
from fleet_app.common import  create_ledger_postings_for_hire, create_ledger_postings_for_invoice, delete_ledger_postings_for_hire, delete_ledger_postings_for_invoice
from fleet_app.models import *
from fleet_app.forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.forms import modelformset_factory
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

from django.db import transaction
from decimal import Decimal
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import reverse_lazy
from item_master.models import Customer
from django.db.models import OuterRef, Subquery
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from num2words import num2words
from fleet_app.reports import create_invoice_pdf, create_simplequotation_pdf, create_timesheet_pdf

# Create your views here.

@login_required(login_url='accounts_app:admin_login')
def fleet_home(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'fleet_home.html', {"vehicles": vehicles})

@login_required(login_url='accounts_app:admin_login')
def manufacturer_list(request):
    manufacturers = Manufacturer.objects.all().order_by('manufacturer_name')
    return render(request, 'manufacturer_list.html', {'manufacturers': manufacturers})


@login_required(login_url='accounts_app:admin_login')
def manufacturer_create(request):
    if request.method == 'POST':
        form = ManufacturerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:manufacturer_list')
    else:
        form = ManufacturerForm()
    return render(request, 'manufacturer_create.html', {'form': form})


@login_required(login_url='accounts_app:admin_login')
def manufacturer_edit(request, pk):
    manufacturer = get_object_or_404(Manufacturer, pk=pk)
    if request.method == 'POST':
        form = ManufacturerForm(request.POST, request.FILES, instance=manufacturer)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:manufacturer_list')
    else:
        form = ManufacturerForm(instance=manufacturer)
    return render(request, 'manufacturer_update.html', {'form': form, 'manufacturer': manufacturer})

def manufacturer_delete(request, pk):
    manufacturer = get_object_or_404(Manufacturer, pk=pk)
    if request.method == "POST":
        manufacturer.delete()
        messages.success(request, "Manufacturer deleted successfully!")
    return redirect("fleet_app:manufacturer_list")

@login_required(login_url='accounts_app:admin_login')
def create_vehicle_category(request):
    if request.method == 'POST':
        form = VehicleCategoryForm(request.POST)
        if form.is_valid():
            form.save()  # Save the category to the database
            return redirect('fleet_app:create_vehicle_category')  # Redirect to the same page after saving
    else:
        form = VehicleCategoryForm()

    categories = VehicleCategory.objects.all()  # Get all categories
    return render(request, 'vehicle_category_list.html', {'form': form, 'categories': categories})

# Edit
def vehicle_category_edit(request, pk):
    category = get_object_or_404(VehicleCategory, pk=pk)
    if request.method == 'POST':
        form = VehicleCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehicle category updated successfully!")
            return redirect('fleet_app:create_vehicle_category')
    else:
        form = VehicleCategoryForm(instance=category)

    categories = VehicleCategory.objects.all()
    return render(request, 'vehicle_category_list.html', {
        'form': form,
        'categories': categories,
        'edit_category': category  # Pass category to highlight in template if needed
    })


# Delete
def vehicle_category_delete(request, pk):
    category = get_object_or_404(VehicleCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Vehicle category deleted successfully!")
    return redirect('fleet_app:create_vehicle_category')


@login_required(login_url='accounts_app:admin_login')
def vehicle_model_list(request):
    manufacturer_id = request.GET.get('manufacturer_id')
    if manufacturer_id:
        vehicle_models = VehicleModel.objects.filter(manufacturer_id=manufacturer_id)
    else:
        vehicle_models = VehicleModel.objects.all()

    manufacturers = Manufacturer.objects.all()
    return render(request, 'vehicle_model_list.html', {
        'vehicle_models': vehicle_models,
        'manufacturers': manufacturers
    })



@login_required(login_url='accounts_app:admin_login')
def get_models_by_manufacturer(request):
    manufacturer_id = request.GET.get('manufacturer_id')
    if manufacturer_id:
        models = VehicleModel.objects.filter(manufacturer_id=manufacturer_id)
    else:
        models = VehicleModel.objects.all()
    
    models = models.select_related('manufacturer', 'vehicle_category').values(
        'id', 
        'model_name', 
        'manufacturer__manufacturer_name',
        'vehicle_category__category_name'
    )
    return JsonResponse(list(models), safe=False)


@login_required(login_url='accounts_app:admin_login')
def create_vehicle_model(request):
    if request.method == 'POST':
        form = VehicleModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:vehicle_model_list')  # Redirect to list after saving
    else:
        form = VehicleModelForm()

    return render(request, 'vehicle_model_form.html', {'form': form})


@login_required(login_url='accounts_app:admin_login')
def update_vehicle_model(request, model_id):
    # Get the vehicle model instance or return 404 if not found
    vehicle_model = get_object_or_404(VehicleModel, id=model_id)

    if request.method == 'POST':
        # Bind the form with POST data and the existing instance
        form = VehicleModelForm(request.POST, instance=vehicle_model)
        if form.is_valid():
            form.save()  # Save the updated model
            return redirect('fleet_app:vehicle_model_list')  # Redirect to the model list after saving
    else:
        # Populate the form with the existing instance data
        form = VehicleModelForm(instance=vehicle_model)

    # Render the update template
    return render(request, 'update_vehicle_model.html', {'form': form, 'vehicle_model': vehicle_model})

def delete_vehicle_model(request, pk):
    vehicle_model = get_object_or_404(VehicleModel, pk=pk)
    if request.method == "POST":
        vehicle_model.delete()
        messages.success(request, "Vehicle model deleted successfully!")
        return redirect("fleet_app:vehicle_model_list")  
    return redirect("fleet_app:vehicle_model_list")

@login_required(login_url='accounts_app:admin_login')
def create_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:driver_list')  # You can redirect to any view after saving, adjust accordingly
    else:
        form = DriverForm()

    return render(request, 'driver_form.html', {'form': form})


@login_required(login_url='accounts_app:admin_login')
def driver_list(request):
    drivers = Driver.objects.all()  # Get all drivers from the database
    return render(request, 'driver_list.html', {'drivers': drivers})


@login_required(login_url='accounts_app:admin_login')
def update_driver(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)  # Fetch the driver or return 404
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)  # Pass the driver instance
        if form.is_valid():
            form.save()
            return redirect('fleet_app:driver_list')  # Redirect to the driver list after updating
    else:
        form = DriverForm(instance=driver)

    return render(request, 'driver_form.html', {'form': form})



@login_required(login_url='accounts_app:admin_login')
# Create or Update Vehicle
def create_or_update_vehicle(request, pk=None):
    if pk:
        vehicle = get_object_or_404(Vehicle, pk=pk)
    else:
        vehicle = None

    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            saved_vehicle = form.save()

            

            return redirect('fleet_app:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)

    # ✅ Add these lines to pass data for modal dropdowns
    manufacturers = Manufacturer.objects.all()
    categories = VehicleCategory.objects.all()
    fuel_choices = VehicleModel._meta.get_field('fuel_type').choices
    transmission_choices = VehicleModel._meta.get_field('model_transmission').choices


    return render(request, 'vehicle_form.html', {
        'form': form,
        'vehicle': vehicle,
        'manufacturers': manufacturers,
        'categories': categories,
        'fuel_choices': fuel_choices,
        'transmission_choices': transmission_choices,
    })



@login_required(login_url='accounts_app:admin_login')
def vehicle_list(request):
    vehicles = Vehicle.objects.all()
    
    # Filter by ownership
    ownership = request.GET.get('ownership')
    if ownership == 'owned':
        vehicles = vehicles.filter(is_owned=True)
    elif ownership == 'supplier':
        vehicles = vehicles.filter(is_owned=False)
    
    # Filter by supplier
    supplier_id = request.GET.get('supplier_id')
    if supplier_id:
        vehicles = vehicles.filter(supplier_id=supplier_id)
    
    # Get all suppliers for the filter dropdown
    suppliers = LedgerCreation.objects.filter(
        vehicle__isnull=False
    ).distinct().order_by('ledger_name')
    
    context = {
        'vehicles': vehicles,
        'suppliers': suppliers,
    }
    return render(request, 'vehicle_list.html', context)


def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == "POST":
        vehicle.delete()
        messages.success(request, "Vehicle deleted successfully!")
        return redirect("fleet_app:vehicle_list")  # Replace with your vehicle list view name
    return redirect("fleet_app:vehicle_list")


def vehicle_list_home(request):
    vehicles = Vehicle.objects.all()  
    return render(request, 'fleet_home.html', {'vehicles': vehicles})


@login_required(login_url='accounts_app:admin_login')
# List view to display all rental companies
def rentalcompany_list(request):
    companies = RentalCompany.objects.all()
    return render(request, 'rentalcompany_list.html', {'companies': companies})


@login_required(login_url='accounts_app:admin_login')
# Create or update a rental company
def create_or_update_rentalcompany(request, pk=None):
    # If a primary key (pk) is provided, update; otherwise, create a new one
    if pk:
        rentalcompany = get_object_or_404(RentalCompany, pk=pk)  # Fetch the company for updating
    else:
        rentalcompany = None  # No company to update, create a new one

    if request.method == 'POST':
        form = RentalCompanyForm(request.POST, request.FILES, instance=rentalcompany)
        if form.is_valid():
            form.save()  # Save or update the rental company
            return redirect('fleet_app:rentalcompany_list')  # Redirect to the list view after saving
    else:
        form = RentalCompanyForm(instance=rentalcompany)

    return render(request, 'rentalcompany_form.html', {'form': form})

def rentalcompany_delete(request, pk):
    company = get_object_or_404(RentalCompany, pk=pk)

    if request.method == "POST":
        company_name = company.company_name
        company.delete()
        messages.success(request, f"{company_name} deleted successfully.")
        return redirect("fleet_app:rentalcompany_list")  # Adjust to your list view

    return redirect("fleet_app:rentalcompany_list")




@login_required(login_url='accounts_app:admin_login')
# List view: Shows a list of all RentalCompanyVehicle objects
def rentalcompanyvehicle_list(request):
    vehicles = RentalCompanyVehicle.objects.all()
    return render(request, 'rentalcompanyvehicle_list.html', {'vehicles': vehicles})


@login_required(login_url='accounts_app:admin_login')
def rentalcompanyvehicle_create_update(request, pk=None):
    vehicle = get_object_or_404(RentalCompanyVehicle, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = RentalCompanyVehicleForm(request.POST, request.FILES, instance=vehicle)
        
        if 'save' in request.POST:  # Only save if the save button was clicked
            if form.is_valid():
                form.save()
                return redirect('fleet_app:rentalcompanyvehicle_list')
        else:
            # This is just for updating the driver list, don't validate yet
            pass
    else:
        form = RentalCompanyVehicleForm(instance=vehicle)

    # The form's __init__ method will handle filtering drivers based on the selected company

    return render(request, 'rentalcompanyvehicle_form.html', {
        'form': form,
        'vehicle': vehicle,
    })

def rentalcompanyvehicle_delete(request, pk):
    vehicle = get_object_or_404(RentalCompanyVehicle, pk=pk)
    if request.method == "POST":
        vehicle.delete()
        messages.success(request, f"{vehicle.vehicle_name or vehicle.vehicle_model.model_name} deleted successfully.")
        return redirect('fleet_app:rentalcompanyvehicle_list')



@login_required(login_url='accounts_app:admin_login')
#filter vehicles by company name 
def company_vehicles(request, company_id):
    company = get_object_or_404(RentalCompany, pk=company_id)
    vehicles = RentalCompanyVehicle.objects.filter(company=company)
    
    context = {
        'company': company,
        'vehicles': vehicles
    }
    return render(request, 'company_vehicles.html', context)


def supplier_vehicles(request, pk):
    company = get_object_or_404(RentalCompany, pk=pk)
    vehicles = Vehicle.objects.filter(supplier=company)

    return render(request, "supplier_vehicles.html", {
        "company": company,
        "vehicles": vehicles
    })


@login_required(login_url='accounts_app:admin_login')
def vendor_create_update(request, pk=None):
    # If a primary key (pk) is provided, we're editing an existing record
    if pk:
        vendor = get_object_or_404(Vendor, pk=pk)
    else:
        vendor = None
    
    if request.method == 'POST':
        form = VendorForm(request.POST, request.FILES, instance=vendor)
        if form.is_valid():
            form.save()
            if pk:
                messages.success(request, 'vendor updated successfully!')
            else:
                messages.success(request, 'vendor created successfully!')
            return redirect('fleet_app:vendor_list')  # Redirect to the workshop list view after saving
        else:
            messages.error(request, 'There was an error submitting the form.')
    else:
        form = VendorForm(instance=vendor)
    
    return render(request, 'vendor_form.html', {
        'form': form,
        'vendor': vendor
    })


@login_required(login_url='accounts_app:admin_login')
# View for listing all Workshops
def vendor_list(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor_list.html', {
        'vendors': vendors
    })
    
    
    
@login_required(login_url='accounts_app:admin_login')
def general_vendor_list(request):
    vendors = Vendor.objects.filter(vendor_type='General')
    return render(request, 'vendor_list.html', {'vendors': vendors})


@login_required(login_url='accounts_app:admin_login')
def service_vendor_list(request):
    vendors = Vendor.objects.filter(vendor_type='Service')
    return render(request, 'vendor_list.html', {'vendors': vendors})  

# def time_sheet_view(request):
#     if request.method == 'POST':
#         form = TimeSheetForm(request.POST)
#         if form.is_valid():
#             # Save the form data to the database (optional but recommended)
#             timesheet = form.save()

#             # Process the form data to generate a PDF
#             buffer = io.BytesIO()
#             p = canvas.Canvas(buffer, pagesize=A4)
            
#             # Extract the data from the form
#             data = form.cleaned_data

#             # Set up PDF layout with two columns: left and right
#             p.setFont("Helvetica", 12)

#             # Left Column (starting from x = 100, y = 780)
#             p.drawString(100, 780, f"Vehicle Registration No: {data['vehicle_reg_no']}")
#             p.drawString(100, 760, f"Vehicle Name: {data['vehicle_name']}")
#             p.drawString(100, 740, f"Project Location: {data['project_location']}")
#             p.drawString(100, 720, f"Client: {data['client']}")
#             p.drawString(100, 700, f"Duration: {data['duration']}")

#             # Right Column (starting from x = 400, y = 780)
#             p.drawString(400, 780, f"PO Reference No: {data['PO_reference_no']}")
#             p.drawString(400, 760, f"Description: {data['description']}")
#             p.drawString(400, 740, f"Date: {data['date']}")
#             p.drawString(400, 720, f"Driver Name: {data['driver_name']}")
#             p.drawString(400, 700, f"Operator Name: {data['operator_name']}")
            
#             # Add headings with underline
#             p.line(50, 580, 550, 580)
#             p.drawString(50, 560, "Date")
#             p.drawString(100, 560, "S. Time")
#             p.drawString(150, 560, "E. Time")
#             p.drawString(200, 560, "Break Hrs")
#             p.drawString(270, 560, "Total Hrs Worked")
#             p.drawString(370, 560, "OT")
#             p.drawString(400, 560, "Job Location")
#             p.drawString(490, 560, "Signature")

#             # Footer section
#             p.drawString(50, 100, "Total Days: ____________")
#             p.drawString(50, 80, "Total Hrs: ____________")
#             p.drawString(50, 60, "Supervisor Signature: ____________")

#             # Right footer section
#             p.drawString(400, 100, "Signature: ____________")
#             p.drawString(400, 80, "Name & Phone: ____________")
#             p.drawString(400, 60, "Name Of Company: ____________")

#             # Finalize the PDF and save
#             p.showPage()
#             p.save()

#             # Return the PDF as a response
#             buffer.seek(0)
#             response = HttpResponse(buffer, content_type='application/pdf')
#             response['Content-Disposition'] = 'attachment; filename="timesheet.pdf"'
#             return response

#     else:
#         form = TimeSheetForm()

#     return render(request, 'timesheet_form.html', {'form': form})

def time_sheet_view(request, timesheet_id=None):

    MENU_ID = 1  # Timesheet menu

    # -------------------------------
    # 🔐 1. Privilege Check (Create)
    # -------------------------------
    if timesheet_id is None:
        if not check_privilege(request.user, MENU_ID, "can_add"):
            messages.error(request, "You do not have permission to create a Timesheet.")
            return redirect("/")  # or any safe page

    # ---------------------------------
    # 🔐 2. Privilege Check (Edit)
    # ---------------------------------
    else:
        if not check_privilege(request.user, MENU_ID, "can_edit"):
            messages.error(request, "You do not have permission to edit a Timesheet.")
            return redirect("/")

    # Determine if we're editing or creating
    timesheet_instance = None
    existing_details = []

    if timesheet_id:
        timesheet_instance = get_object_or_404(TimeSheet, id=timesheet_id)
        existing_details = TimeSheetDetail.objects.filter(
            timesheet=timesheet_instance
        ).order_by('date')

    if request.method == 'POST':

        timesheet_form = TimeSheetForm(request.POST, instance=timesheet_instance)
        detail_formset = TimeSheetDetailFormSet(
            request.POST,
            prefix='details',
            instance=timesheet_instance
        )

        if timesheet_form.is_valid() and detail_formset.is_valid():
            timesheet = timesheet_form.save()
            detail_formset.instance = timesheet
            detail_formset.save()

            if timesheet_id:
                messages.success(request, f"Timesheet #{timesheet.voucher_no} updated successfully!")
            else:
                messages.success(request, f"Timesheet #{timesheet.voucher_no} created successfully!")

            return create_timesheet_pdf(timesheet)

        else:
            messages.error(request, "Please fix the errors and try again.")
            return render(request, 'timesheet_form.html', {
                'timesheet_form': timesheet_form,
                'detail_formset': detail_formset,
                'timesheet_instance': timesheet_instance,
                'existing_details': existing_details,
                'is_edit_mode': timesheet_id is not None,
            })

    else:
        timesheet_form = TimeSheetForm(instance=timesheet_instance)
        detail_formset = TimeSheetDetailFormSet(
            queryset=TimeSheetDetail.objects.none(),
            prefix='details'
        )

    return render(request, 'timesheet_form.html', {
        'timesheet_form': timesheet_form,
        'detail_formset': detail_formset,
        'timesheet_instance': timesheet_instance,
        'existing_details': existing_details,
        'is_edit_mode': timesheet_id is not None,
    })

from django.views.decorators.http import require_http_methods
    
@require_http_methods(["POST"])
def timesheet_delete(request, timesheet_id):

    MENU_ID = 1

    # 🔐 Permission check
    if not check_privilege(request.user, MENU_ID, "can_delete"):
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete this Timesheet.'
        }, status=403)

    try:
        timesheet = TimeSheet.objects.get(id=timesheet_id)
        voucher_no = timesheet.voucher_no
        timesheet.delete()

        return JsonResponse({
            'success': True,
            'message': f'Timesheet {voucher_no} deleted successfully'
        })

    except TimeSheet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Timesheet not found'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting timesheet: {str(e)}'
        }, status=500)
        
        
        
def get_next_timesheet_no(request):
    last_timesheet = TimeSheet.objects.order_by('-timesheet_no').first()
    next_timesheet_no = 1 if not last_timesheet else last_timesheet.timesheet_no + 1
    return JsonResponse({'next_timesheet_no': next_timesheet_no})     

def get_vehicle_reg_no(request, vehicle_id):
    try:
        vehicle = Vehicle.objects.select_related('license_plate_code').get(id=vehicle_id)
        return JsonResponse({
            'license_plate_number': vehicle.license_plate_number,
            'license_plate_code': vehicle.license_plate_code.code if vehicle.license_plate_code else None
        }, status=200)
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)



# View to create VehicleQuotation and VehicleQuotationItems
def create_fleet_quotation(request):
    QuotationItemFormSet = modelformset_factory(
        FleetQuotationItem, form=FleetQuotationItemForm, extra=0, can_delete=True
    )
    vehicles = Vehicle.objects.all()
    customers = Customer.objects.all()

    if request.method == 'POST':
        quotation_form = FleetQuotationForm(request.POST, request.FILES)
        quotation_items_formset = QuotationItemFormSet(request.POST)

        if quotation_form.is_valid() and quotation_items_formset.is_valid():
            fleet_quotation = quotation_form.save()
            items = quotation_items_formset.save(commit=False)
            for item in items:
                item.vehicle_quotation = fleet_quotation
                item.save()
            return redirect('fleet_app:vehicle_quotation_list')
    else:
        quotation_form = FleetQuotationForm()
        quotation_items_formset = QuotationItemFormSet(queryset=FleetQuotationItem.objects.none())

    return render(request, 'fleet_quotation_form.html', {
        'quotation_form': quotation_form,
        'quotation_items_formset': quotation_items_formset,
        'vehicles': vehicles,
        'customers': customers,
    })
    
def get_next_quotation_no(request):
    last_quotation = FleetQuotation.objects.order_by('-quotation_no').first()
    next_quotation_no = 1 if not last_quotation else last_quotation.quotation_no + 1
    return JsonResponse({'next_quotation_no': next_quotation_no})     
    
    
    
def vehicle_quotation_list(request):
    quotations = FleetQuotation.objects.all()
    return render(request, 'vehicle_quotation_list.html', {'quotations': quotations})

def vehicle_quotation_detail(request, pk):
    quotation = get_object_or_404(FleetQuotation, pk=pk)
    items = FleetQuotationItem.objects.filter(vehicle_quotation=quotation)
    return render(request, 'vehicle_quotation_detail.html', {'quotation': quotation, 'items': items})

def fleetquotation_list(request):
    quotations = FleetQuotation.objects.prefetch_related('items')
    return render(request, 'fleetquotation_list.html', {'quotations': quotations})

def fleetquotation_edit(request, pk):
    quotation = get_object_or_404(FleetQuotation, pk=pk)

    if request.method == 'POST':
        form = FleetQuotationForm(request.POST, request.FILES, instance=quotation)
        formset = FleetQuotationItemFormSet(request.POST, instance=quotation)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('fleetquotation_list')
    else:
        form = FleetQuotationForm(instance=quotation)
        formset = FleetQuotationItemFormSet(instance=quotation)

    return render(request, 'fleetquotation_edit.html', {
        'form': form,
        'formset': formset,
        'quotation': quotation
    })

def get_customer_address(request, customer_id):
    try:
        customer = Customer.objects.get(id=customer_id)
        return JsonResponse({'address': customer.customer_address_1}, status=200)
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Customer not found'}, status=404)
    
def get_vehicle_rates(request, vehicle_id):
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        data = {
            'rate_per_hr': vehicle.rate_per_hr,
            'rate_per_day': vehicle.rate_per_day,
            'rate_per_month': vehicle.rate_per_month
        }
        return JsonResponse(data, status=200)
    except Vehicle.DoesNotExist:
        return JsonResponse({'error': 'Vehicle not found'}, status=404)
 
def create_repair_and_maintenance(request):
    RepairAndMaintenanceItemFormSet = modelformset_factory(
        RepairAndMaintenanceItem, form=RepairAndMaintenanceItemForm, extra=0, can_delete=True
    )
    

    if request.method == 'POST':
        maintenance_form = RepairAndMaintenanceForm(request.POST, request.FILES)
        maintenance_items_formset = RepairAndMaintenanceItemFormSet(request.POST)

        if maintenance_form.is_valid() and maintenance_items_formset.is_valid():
            maintenance = maintenance_form.save()
            items = maintenance_items_formset.save(commit=False)
            for item in items:
                item.repair_and_maintenance = maintenance
                item.save()
            return redirect('fleet_app:maintenance_list')
    else:
        maintenance_form = RepairAndMaintenanceForm()
        maintenance_items_formset = RepairAndMaintenanceItemFormSet(queryset=RepairAndMaintenanceItem.objects.none())

    return render(request, 'repair_and_maintenance_form.html', {
        'maintenance_form': maintenance_form,
        'maintenance_items_formset': maintenance_items_formset,
        
    })
    
def get_next_voucher_no(request):
    last_voucher = RepairAndMaintenance.objects.order_by('-voucher_no').first()
    next_voucher_no = 1 if not last_voucher else last_voucher.voucher_no + 1
    return JsonResponse({'next_voucher_no': next_voucher_no})    
    
def maintenance_list(request):
    maintenances = RepairAndMaintenance.objects.all()
    return render(request, 'maintenance_list.html', {'maintenances': maintenances})

def maintenance_detail(request, pk):
    maintenance = get_object_or_404(RepairAndMaintenance, pk=pk)
    items = RepairAndMaintenanceItem.objects.filter(repair_and_maintenance=maintenance)
    return render(request, 'maintenance_detail.html', {'maintenance': maintenance, 'items': items})    



    

def vehicle_master_list(request):
    vehicles = VehicleMaster.objects.all()  # Get all vehicles from VehicleMaster model
    return render(request, 'vehicle_master_list.html', {'vehicles': vehicles})

def fleet_customer_management(request, customer_id=None):
    if customer_id:
        customer = get_object_or_404(FleetCustomer, id=customer_id)  # For updating an existing customer
    else:
        customer = None  # For creating a new customer

    if request.method == 'POST':
        form = FleetCustomerForm(request.POST, instance=customer)  # Create or Update Customer form
        if form.is_valid():
            customer = form.save()  # Save the customer

            return redirect('fleet_app:fleet_customer_management')  # Redirect to the same page after save
    else:
        form = FleetCustomerForm(instance=customer)

    # Fetch all customers to list them
    customers = FleetCustomer.objects.all()

    return render(request, 'fleet_customer_management.html', {'form': form, 'customers': customers, 'customer': customer})

def fleetcustomer_delete(request, pk):
    customer = get_object_or_404(FleetCustomer, pk=pk)

    if request.method == "POST":
        customer_name = customer.customer_name
        customer.delete()
        messages.success(request, f"Customer {customer_name} deleted successfully.")
        return redirect("fleet_app:fleetcustomer_list")  # make sure you have this list view

    return redirect("fleet_app:fleetcustomer_list")


def staff_category_manage(request, pk=None):
    # Create or update form
    if pk:
        instance = get_object_or_404(StaffCategory, pk=pk)
    else:
        instance = None

    if request.method == 'POST':
        if 'delete' in request.POST:
            instance = get_object_or_404(StaffCategory, pk=request.POST.get('delete'))
            instance.delete()
            return redirect('fleet_app:staff_category_manage')

        form = StaffCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:staff_category_manage')
    else:
        form = StaffCategoryForm(instance=instance)

    # List all categories
    categories = StaffCategory.objects.all()
    return render(request, 'staff_category_manage.html', {
        'form': form,
        'categories': categories,
        'edit_id': pk
    })
    
def staff_manage(request, pk=None):
    # Edit mode
    if pk:
        instance = get_object_or_404(Staff, pk=pk)
    else:
        instance = None

    if request.method == 'POST':
        if 'delete' in request.POST:
            instance = get_object_or_404(Staff, pk=request.POST.get('delete'))
            instance.delete()
            return redirect('fleet_app:staff_manage')

        form = StaffForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:staff_manage')
    else:
        form = StaffForm(instance=instance)

    staffs = Staff.objects.all().select_related('staff_category')
    return render(request, 'staff_manage.html', {
        'form': form,
        'staffs': staffs,
        'edit_id': pk
    })    
    
from django.views.decorators.csrf import csrf_exempt    
import json    

def add_vehicle_category_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        category_name = data.get('category_name')

        if not category_name:
            return JsonResponse({'success': False, 'error': 'Vehicle category name is required.'})

        if VehicleCategory.objects.filter(category_name__iexact=category_name).exists():
            return JsonResponse({'success': False, 'error': 'This vehicle category already exists.'})

        vehicle_category = VehicleCategory.objects.create(category_name=category_name)
        return JsonResponse({'success': True, 'id': vehicle_category.id, 'text': vehicle_category.category_name})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@csrf_exempt
def add_vehicle_model(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            model = VehicleModel.objects.create(
                model_name=data.get('model_name'),
                manufacturer_id=data.get('manufacturer_id'),
                vehicle_category_id=data.get('vehicle_category_id'),
                seat_number=data.get('seat_number') or 0,
                door_number=data.get('door_number') or 0,
                model_colour=data.get('model_colour'),
                model_range=data.get('model_range') or 0,
                model_year=data.get('model_year') or 0,
                fuel_type=data.get('fuel_type'),
                CO2_emission=data.get('CO2_emission') or 0,
                CO2_standard=data.get('CO2_standard'),
                model_transmission=data.get('model_transmission'),
                model_power=data.get('model_power') or 0,
                model_horse_power=data.get('model_horse_power') or 0,
            )
            return JsonResponse({'success': True, 'id': model.id, 'text': str(model)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def add_license_plate_code_modal(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code')
            description = data.get('description')

            if not code:
                return JsonResponse({'success': False, 'error': 'Code is required.'})

            if LicensePlateCode.objects.filter(code__iexact=code).exists():
                return JsonResponse({'success': False, 'error': 'Code already exists.'})

            new_code = LicensePlateCode.objects.create(code=code, description=description)
            return JsonResponse({'success': True, 'id': new_code.id, 'text': new_code.code})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def document_crud_view(request, pk=None):
    documents = Document.objects.all()
    instance = get_object_or_404(Document, pk=pk) if pk else None
    form = DocumentForm(request.POST or None, request.FILES or None, instance=instance)

    if request.method == 'POST':
        if 'delete' in request.POST and instance:
            instance.delete()
            messages.success(request, "Document deleted.")
            return redirect('fleet_app:document_crud')
        elif form.is_valid():
            doc = form.save()
            if instance:
                messages.success(request, "Document updated.")
            else:
                messages.success(request, "Document created.")
            return redirect('fleet_app:document_crud')

    return render(request, 'document_crud.html', {
        'form': form,
        'documents': documents,
        'instance': instance
    })

def create_simple_quotation(request, quotation_id=None):
    """
    Unified view for creating and editing quotations
    - If quotation_id is None: CREATE mode
    - If quotation_id exists: EDIT mode
    """
    MENU_ID = 2

    # 🔐 CREATE MODE → need can_add
    if quotation_id is None:
        if not check_privilege(request.user, MENU_ID, "can_add"):
            messages.error(request, "You do not have permission to create quotations.")
            return redirect("dashboard")

    # 🔐 EDIT MODE → need can_edit
    if quotation_id:
        if not check_privilege(request.user, MENU_ID, "can_edit"):
            messages.error(request, "You do not have permission to edit quotations.")
            return redirect("dashboard")
    
    # Determine if we're editing or creating
    quotation_instance = None
    existing_details = []
    
    if quotation_id:
        # EDIT MODE - Get existing quotation and its details
        quotation_instance = get_object_or_404(SimpleQuotation, id=quotation_id)
        existing_details = SimpleQuotationDetails.objects.filter(
            quotation=quotation_instance
        ).order_by('id')
        
        print(f"\n📝 Edit mode - Quotation #{quotation_instance.voucher_no}")
        print(f"Found {existing_details.count()} existing details:")
        for detail in existing_details:
            print(f"  - Detail ID: {detail.id}, Desc: {detail.description[:30]}, Qty: {detail.quantity}, Rent: {detail.rent}")
    
    if request.method == 'POST':
        # Pass instance for edit, None for create
        form = SimpleQuotationForm(request.POST, instance=quotation_instance)
        details_data = request.POST.getlist('details[]')

        print("\n=== FORM SUBMISSION ===")
        print(f"Details count: {len(details_data)}")
        for i, entry in enumerate(details_data):
            print(f"  Detail {i}: {entry}")

        if form.is_valid():
            quotation = form.save()
            print(f"✅ Saved quotation: {quotation.voucher_no} (ID: {quotation.id})")

            # If editing, delete old details first
            if quotation_id:
                SimpleQuotationDetails.objects.filter(quotation=quotation).delete()
                print("🗑️ Deleted old quotation details")

            # Create new details
            created_count = 0
            for entry in details_data:
                try:
                    parts = entry.split('|')
                    # Expected format: description | quantity | rent | period
                    if len(parts) >= 3:
                        desc = parts[0].strip()
                        qty = parts[1].strip()
                        rent = parts[2].strip()
                        period = parts[3].strip() if len(parts) >= 4 else 'Hour'

                        if desc and qty and rent:
                            SimpleQuotationDetails.objects.create(
                                quotation=quotation,
                                description=desc,
                                quantity=int(qty),
                                rent=Decimal(rent),
                                period=period,
                                created_by=request.user.id if request.user.is_authenticated else None
                            )
                            created_count += 1
                except Exception as e:
                    print(f"❌ Skipping invalid row: {entry} - {e}")
                    continue

            print(f"✅ Created {created_count} quotation details")

            # Success message
            if quotation_id:
                messages.success(request, f"Quotation #{quotation.voucher_no} updated successfully!")
            else:
                messages.success(request, f"Quotation #{quotation.voucher_no} created successfully!")

            # Generate and return PDF
            return create_simplequotation_pdf(quotation)
        else:
            print("❌ Form errors:", form.errors)
            messages.error(request, "Please correct the errors in the form.")

    else:
        # GET request - initialize form
        form = SimpleQuotationForm(instance=quotation_instance)

    return render(request, 'create_simple_quotation.html', {
        'form': form,
        'quotation_instance': quotation_instance,
        'existing_details': existing_details,
        'is_edit_mode': quotation_id is not None,
    })



def simple_quotation_list(request):

    MENU_ID = 2

    if not check_privilege(request.user, MENU_ID, "can_read"):
        messages.error(request, "You do not have permission to view quotations.")
        return redirect("dashboard")

    quotations = SimpleQuotation.objects.select_related('customer').prefetch_related('details').order_by('-date')
    
    return render(request, 'simple_quotation_list.html', {
        'quotations': quotations
    })

@require_http_methods(["POST"])
def simple_quotation_delete(request, quotation_id):

    MENU_ID = 2

    if not check_privilege(request.user, MENU_ID, "can_delete"):
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to delete quotations.'
        }, status=403)

    try:
        quotation = SimpleQuotation.objects.get(id=quotation_id)
        voucher_no = quotation.voucher_no
        quotation.delete()

        return JsonResponse({
            'success': True,
            'message': f'Quotation {voucher_no} deleted successfully'
        })

    except SimpleQuotation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Quotation not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting quotation: {str(e)}'
        }, status=500)


def create_invoice(request, invoice_id=None):
    MENU_ID = 5

    # 🔐 CREATE MODE → need can_add
    if invoice_id is None:
        if not check_privilege(request.user, MENU_ID, "can_add"):
            return redirect("/")

    # 🔐 EDIT MODE → need can_edit
    if invoice_id is not None:
        if not check_privilege(request.user, MENU_ID, "can_edit"):
            return redirect("/")

    vehicles = Vehicle.objects.all().order_by('vehicle_name')

    invoice_instance = None
    existing_details = []

    if invoice_id:
        invoice_instance = get_object_or_404(Invoice, id=invoice_id)
        existing_details = InvoiceDetails.objects.filter(invoice=invoice_instance).select_related('vehicle')

    if request.method == 'POST':
        invoice_form = InvoiceForm(request.POST, instance=invoice_instance)

        if invoice_form.is_valid():
            invoice = invoice_form.save(commit=False)
            grand_total = request.POST.get('grand_total')
            invoice.grand_total = float(grand_total) if grand_total else 0.0
            invoice.save()

            details_data = request.POST.getlist('details[]')

            if not details_data:
                messages.error(request, "Please add at least one invoice detail.")
                if not invoice_id:
                    invoice.delete()
                return redirect('fleet_app:create_invoice')

            if invoice_id:
                InvoiceDetails.objects.filter(invoice=invoice).delete()

            for detail_str in details_data:
                try:
                    vehicle_id, location, amount, tax = detail_str.split('|')
                    vehicle = Vehicle.objects.get(id=vehicle_id)

                    amount = float(amount)
                    tax = float(tax)
                    tax_amount = (amount * tax / 100)
                    total_amount = amount + tax_amount

                    InvoiceDetails.objects.create(
                        invoice=invoice,
                        vehicle=vehicle,
                        location=location,
                        amount=amount,
                        tax=tax,
                        tax_amount=tax_amount,
                        total_amount=total_amount
                    )
                except Exception as e:
                    messages.error(request, "Error saving invoice details.")
                    if not invoice_id:
                        invoice.delete()
                    return redirect('fleet_app:create_invoice')

            if invoice_id:
                delete_ledger_postings_for_invoice(invoice)
            create_ledger_postings_for_invoice(invoice)

            messages.success(request, "Invoice updated successfully!" if invoice_id else "Invoice created successfully!")
            return create_invoice_pdf(invoice)

        else:
            messages.error(request, "Please correct the errors in the invoice form.")

    else:
        invoice_form = InvoiceForm(instance=invoice_instance)

    return render(request, 'create_invoice.html', {
        'invoice_form': invoice_form,
        'vehicles': vehicles,
        'invoice_instance': invoice_instance,
        'existing_details': existing_details,
        'is_edit_mode': invoice_id is not None,
    })
    
def invoice_list(request):
    MENU_ID = 5

    if not check_privilege(request.user, MENU_ID, "can_read"):
        return redirect("/")

    invoices = Invoice.objects.all().order_by('-date')
    return render(request, 'invoice_list.html', {'invoices': invoices})

@require_http_methods(["POST"])
def invoice_delete(request, invoice_id):
    MENU_ID = 5

    if not check_privilege(request.user, MENU_ID, "can_delete"):
        return JsonResponse({
            "success": False,
            "message": "You do not have permission to delete invoices."
        }, status=403)

    try:
        invoice = Invoice.objects.get(id=invoice_id)
        number = invoice.invoice_no if hasattr(invoice, "invoice_no") else invoice.id

        invoice.delete()
        return JsonResponse({
            "success": True,
            "message": f"Invoice {number} deleted successfully"
        })

    except Invoice.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Invoice not found"
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error deleting invoice: {str(e)}"
        }, status=500)

    
# List Report
def timesheet_report(request):

    MENU_ID = 1

    if not check_privilege(request.user, MENU_ID, "can_read"):
        messages.error(request, "You do not have permission to view Timesheets.")
        return redirect("/")

    timesheets = TimeSheet.objects.all()
    return render(request, 'timesheet_report.html', {'timesheets': timesheets})


# Edit both TimeSheet & Details
def edit_timesheet(request, pk):
    timesheet = get_object_or_404(TimeSheet, pk=pk)
    if request.method == 'POST':
        form = TimeSheetForm(request.POST, instance=timesheet)
        formset = TimeSheetDetailFormSet(request.POST, instance=timesheet)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('fleet_app:timesheet_report')
    else:
        form = TimeSheetForm(instance=timesheet)
        formset = TimeSheetDetailFormSet(instance=timesheet)

    return render(request, 'edit_timesheet.html', {
        'form': form,
        'formset': formset,
        'timesheet': timesheet
    })        
    
    
def fleetquotation_list(request):
    quotations = FleetQuotation.objects.all().order_by('-date')
    return render(request, 'fleetquotation_list.html', {'quotations': quotations})    


def fleetquotation_edit(request, pk):
    quotation = get_object_or_404(FleetQuotation, pk=pk)
    if request.method == 'POST':
        form = FleetQuotationForm(request.POST, request.FILES, instance=quotation)
        formset = FleetQuotationItemFormSet(request.POST, instance=quotation)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('fleetquotation_list')
    else:
        form = FleetQuotationForm(instance=quotation)
        formset = FleetQuotationItemFormSet(instance=quotation)
    
    return render(request, 'fleetquotation_edit.html', {
        'form': form,
        'formset': formset,
        'quotation': quotation,
    })
    



def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES, instance=invoice)
        formset = InvoiceDetailsFormSet(request.POST, request.FILES, instance=invoice)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('fleet_app:invoice_list')
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceDetailsFormSet(instance=invoice)

    return render(request, 'invoice_edit.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice
    })  
    
def company_setup(request):
    # Get the only company, or None
    company = Company.objects.first()

    if request.method == "POST":
        if company:
            form = CompanyForm(request.POST, instance=company)
        else:
            form = CompanyForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "Company details saved successfully!")
            return redirect("fleet_app:company_setup")
    else:
        form = CompanyForm(instance=company)

    return render(request, "company_setup.html", {"form": form, "company": company})


def document_list(request):
    company = Company.objects.first()
    if not company:
        messages.warning(request, "Please set up your company first.")
        return redirect("fleet_app:company_setup")

    documents = company.documents.all()

    if request.method == "POST":
        form = CompanyDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.company = company
            doc.save()
            messages.success(request, "Document uploaded successfully!")
            return redirect("fleet_app:document_list")
    else:
        form = CompanyDocumentForm()

    return render(request, "company_document_list.html", {
        "company": company,
        "documents": documents,
        "doc_form": form,
    })


def document_delete(request, doc_id):
    doc = get_object_or_404(CompanyDocument, id=doc_id)
    doc.delete()
    messages.success(request, "Document deleted successfully!")
    return redirect("fleet_app:document_list")

def fleet_hire_create(request, hire_id=None):
    """
    Unified view for creating and editing fleet hire
    - If hire_id is None: CREATE mode
    - If hire_id exists: EDIT mode
    """
    MENU_ID = 6

    # 🔐 CREATE MODE → need can_add
    if hire_id is None:
        if not check_privilege(request.user, MENU_ID, "can_add"):
            
            return redirect("/")

    # 🔐 EDIT MODE → need can_edit
    if hire_id is not None:
        if not check_privilege(request.user, MENU_ID, "can_edit"):
            
            return redirect("/")
    vehicles = Vehicle.objects.filter(is_owned=False)
    
    # Determine if we're editing or creating
    hire_instance = None
    existing_details = []
    
    if hire_id:
        # EDIT MODE - Get existing hire and its details
        hire_instance = get_object_or_404(FleetHire, id=hire_id)
        existing_details = FleetHireDetails.objects.filter(fleet_hire=hire_instance).select_related('vehicle')

    if request.method == "POST":
        # Pass instance for edit, None for create
        form = FleetHireForm(request.POST, instance=hire_instance)

        if form.is_valid():
            try:
                # Save main FleetHire record
                fleet_hire = form.save(commit=False)
                fleet_hire.save()

                # If editing, delete old details first
                if hire_id:
                    FleetHireDetails.objects.filter(fleet_hire=fleet_hire).delete()
                    # Also delete old ledger postings if they exist
                    # delete_ledger_postings_for_hire(fleet_hire)  # You might need this

                # Read dynamic row fields
                vehicles_list = request.POST.getlist("details-vehicle[]")
                reg_nos = request.POST.getlist("details-reg_no[]")
                start_dates = request.POST.getlist("details-start_date[]")
                end_dates = request.POST.getlist("details-end_date[]")
                units = request.POST.getlist("details-unit[]")
                no_of_units = request.POST.getlist("details-no_of_unit[]")
                rates = request.POST.getlist("details-rate_per_period[]")

                # Create new details
                for i in range(len(vehicles_list)):
                    if not vehicles_list[i]:
                        continue   # Skip empty rows

                    rate = float(rates[i]) if rates[i] else 0
                    no_of_unit = int(no_of_units[i]) if no_of_units[i] else 1

                    FleetHireDetails.objects.create(
                        fleet_hire=fleet_hire,
                        vehicle_id=vehicles_list[i],
                        reg_no=reg_nos[i],
                        start_date=start_dates[i],
                        end_date=end_dates[i],
                        unit=units[i],
                        no_of_unit=no_of_unit,
                        rate_per_period=rate,
                    )

                # Create or update ledger posting entries
                if hire_id:
                    # For edit: delete old postings and create new
                    delete_ledger_postings_for_hire(fleet_hire)  # You need to implement this
                create_ledger_postings_for_hire(fleet_hire)

                # Success message
                if hire_id:
                    messages.success(request, "Fleet hire updated successfully!")
                else:
                    messages.success(request, "Fleet hire created successfully!")
                    
                return redirect("fleet_app:fleet_hire_list")

            except Exception as e:
                messages.error(request, f"Unexpected error: {e}")
                if not hire_id:  # Only delete if it's a new hire
                    if fleet_hire.pk:
                        fleet_hire.delete()

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        # GET request - initialize form
        form = FleetHireForm(instance=hire_instance)

    return render(request, "fleet_hire_form.html", {
        "form": form,
        "vehicle": vehicles,
        "hire_instance": hire_instance,      # Pass to template
        "existing_details": existing_details, # Pass to template
        "is_edit_mode": hire_id is not None,  # Helper flag
    })

# List of all FleetHire
def fleet_hire_list(request):
    MENU_ID = 6

    if not check_privilege(request.user, MENU_ID, "can_read"):
        return redirect("/")
    hires = FleetHire.objects.all().order_by('-invoice_date', '-voucher_no')
    return render(request, "fleet_hire_list.html", {"hires": hires})

@require_http_methods(["POST"])
def fleet_hire_delete(request, hire_id):
    MENU_ID = 6

    # 🔐 DELETE privilege check
    if not check_privilege(request.user, MENU_ID, "can_delete"):
        return JsonResponse({
            "success": False,
            "message": "You do not have permission to delete Fleet Hire entries."
        }, status=403)

    try:
        hire = FleetHire.objects.get(id=hire_id)
        voucher = hire.voucher_no if hasattr(hire, "voucher_no") else hire_id

        hire.delete()

        return JsonResponse({
            "success": True,
            "message": f"Fleet Hire {voucher} deleted successfully"
        })

    except FleetHire.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Fleet Hire not found"
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error deleting Fleet Hire: {str(e)}"
        }, status=500)
        
        
# Detail view for a single FleetHire
def fleet_hire_detail(request, pk):
    fleet_hire = get_object_or_404(FleetHire, pk=pk)
    details = fleet_hire.details.all()  # related_name='details' from FleetHireDetails
    return render(request, "fleet_hire_detail.html", {"fleet_hire": fleet_hire, "details": details})

def fleet_voucher_create_update(request, pk=None):
    if pk:
        voucher = get_object_or_404(Vouchers, pk=pk)
    else:
        voucher = None

    if request.method == 'POST':
        form = VouchersForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('fleet_app:fleet_voucher_list')  # Make sure you define this view too
    else:
        form = VouchersForm(instance=voucher)

    return render(request, 'fleet_voucher_form.html', {'form': form, 'voucher': voucher})

def fleet_voucher_list(request):
    vouchers = Vouchers.objects.all()
    return render(request, 'fleet_voucher_list.html', {'vouchers': vouchers})

def get_next_voucher_number_fleet(request):
    """AJAX view to get next voucher number"""
    print(f"AJAX Request received: {request.GET}")  # Debug print
    
    if request.method == 'GET' and 'voucher_type_id' in request.GET:
        try:
            voucher_type_id = request.GET['voucher_type_id']
            print(f"Looking for voucher type ID: {voucher_type_id}")  # Debug print
            
            voucher_type = Vouchers.objects.get(pk=voucher_type_id)
            print(f"Found voucher type: {voucher_type}")  # Debug print
            
            next_number = voucher_type.get_next_voucher_number()
            print(f"Generated voucher number: {next_number}")  # Debug print
            
            return JsonResponse({
                'voucher_number': next_number,
                'success': True
            })
        except Vouchers.DoesNotExist:
            print(f"Voucher type not found for ID: {voucher_type_id}")  # Debug print
            return JsonResponse({'error': 'Voucher type not found'}, status=404)
        except Exception as e:
            print(f"Error generating voucher number: {str(e)}")  # Debug print
            return JsonResponse({'error': str(e)}, status=500)
    
    print("Invalid request parameters")  # Debug print
    return JsonResponse({'error': 'Invalid request'}, status=400)

def create_fleet_contract(request, pk=None):

    MENU_ID = 3

    # 🔐 CREATE MODE → need can_add
    if pk is None:
        if not check_privilege(request.user, MENU_ID, "can_add"):
            messages.error(request, "You do not have permission to create a contract.")
            return redirect("/")

    # 🔐 EDIT MODE → need can_edit
    if pk is not None:
        if not check_privilege(request.user, MENU_ID, "can_edit"):
            messages.error(request, "You do not have permission to edit contracts.")
            return redirect("/")

    # --------------- Existing logic below ---------------
    instance = get_object_or_404(FleetContract, pk=pk) if pk else None

    if request.method == "POST":
        form = FleetContractForm(request.POST, instance=instance)
        if form.is_valid():
            contract = form.save()

            if pk:
                messages.success(request, "Contract updated successfully!")
                return redirect("fleet_app:edit_fleet_contract", pk=contract.pk)
            else:
                messages.success(request, "Contract created successfully!")
                return redirect("fleet_app:create_fleet_contract")
    else:
        if instance:
            form = FleetContractForm(instance=instance)
        else:
            form = FleetContractForm(initial={"date": timezone.now().date()})

    return render(request, "contract_form.html", {
        "form": form,
        "edit_mode": pk is not None,
    })

def fleet_contract_list(request):

    MENU_ID = 3

    if not check_privilege(request.user, MENU_ID, "can_read"):
        messages.error(request, "You do not have permission to view contract list.")
        return redirect("/")

    contracts = FleetContract.objects.all().order_by('-date')
    return render(request, 'contract_list.html', {'contracts': contracts})


@require_http_methods(["POST"])
def fleet_contract_delete(request, pk):

    MENU_ID = 3

    # 🔐 Delete privilege check
    if not check_privilege(request.user, MENU_ID, "can_delete"):
        return JsonResponse({
            "success": False,
            "message": "You do not have permission to delete contracts."
        }, status=403)

    try:
        contract = FleetContract.objects.get(pk=pk)
        num = contract.contract_no if hasattr(contract, "contract_no") else pk
        contract.delete()

        return JsonResponse({
            "success": True,
            "message": f"Contract {num} deleted successfully"
        })

    except FleetContract.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Contract not found"
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": f"Error deleting contract: {str(e)}"
        }, status=500)
