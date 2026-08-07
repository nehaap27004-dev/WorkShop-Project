from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from accounts_app.common import check_admin_override, check_privilege
from accounts_app.models import LedgerPosting, PaymentBillMaster, ReceiptBillMaster, Groups
from audit_app.common import log_activity
from fleet_app.common import  *
from fleet_app.models import *
from fleet_app.forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import HttpResponse
from django.forms import modelformset_factory, modelform_factory
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from django.views.decorators.http import require_http_methods
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
from fleet_app.reports import *
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from datetime import datetime 
from datetime import date
from .accounting_utils import *
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import  FleetCustomer, VehicleCategory, LicensePlateCode, Staff


# Create your views here.

@login_required(login_url='accounts_app:admin_login')
def fleet_home(request):

    vehicles = Vehicle.objects.all()

    total_invoices = Invoice.objects.aggregate(
        total=Sum('grand_total')
    )['total'] or 0

    client_outstanding = get_group_outstanding(29)
    supplier_outstanding = get_group_outstanding(28)

    context = {
        'total_invoices': total_invoices,
        'total_client_outstanding': format_dr_cr(client_outstanding),
        'total_supplier_outstanding': format_dr_cr(supplier_outstanding),
        'total_expense': get_group_outstanding(16),
    }

    return render(request, 'fleet_home.html', context)
    
def get_group_outstanding(*group_ids):
    """
    Returns SUM(debit - credit) for given group ids (including subgroups)
    """

    ledgers = get_ledgers_by_group_ids(*group_ids)

    totals = LedgerPosting.objects.filter(
        ledger__in=ledgers,
        IsDeleted=False
    ).aggregate(
        total_debit=Sum('debit'),
        total_credit=Sum('credit')
    )

    total_debit = totals['total_debit'] or Decimal('0.000')
    total_credit = totals['total_credit'] or Decimal('0.000')

    return total_debit - total_credit

def format_dr_cr(amount):
    """
    If amount > 0  → show Dr
    If amount < 0  → show Cr
    """
    amount = amount or Decimal('0.000')

    if amount < 0:
        return f"{abs(amount):.3f} Cr"
    elif amount > 0:
        return f"{amount:.3f} Dr"
    else:
        return "0.000"


@login_required(login_url='accounts_app:admin_login')
def manufacturer_list(request):
    manufacturers = Manufacturer.objects.select_related('vehicle_type').order_by('manufacturer_name')
    return render(request, 'manufacturer_list.html', {'manufacturers': manufacturers})

@login_required(login_url='accounts_app:admin_login')
def manufacturer_create(request):
    if request.method == 'POST':
        form = ManufacturerForm(request.POST, request.FILES)
        if form.is_valid():
            manufacturer = form.save()

            # ✅ CREATE LOG
            log_activity(
                user=request.user,
                screen_name="Manufacturer Master",
                action_type="CREATE",
                remark=f"Manufacturer '{manufacturer.manufacturer_name}' created"
            )

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
            manufacturer = form.save()

            # ✅ UPDATE LOG
            log_activity(
                user=request.user,
                screen_name="Manufacturer Master",
                action_type="UPDATE",
                remark=f"Manufacturer '{manufacturer.manufacturer_name}' updated"
            )

            return redirect('fleet_app:manufacturer_list')
    else:
        form = ManufacturerForm(instance=manufacturer)

    return render(request, 'manufacturer_update.html', {
        'form': form,
        'manufacturer': manufacturer
    })

from django.db.models import ProtectedError
@login_required(login_url='accounts_app:admin_login')
def manufacturer_delete(request, pk):
    manufacturer = get_object_or_404(Manufacturer, pk=pk)

    if request.method == "POST":
        name = manufacturer.manufacturer_name

        try:
            manufacturer.delete()

            log_activity(
                user=request.user,
                screen_name="Manufacturer Master",
                action_type="DELETE",
                remark=f"Manufacturer '{name}' deleted"
            )

            messages.success(request, "Manufacturer deleted successfully!")
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete '{name}' because it has vehicle models linked to it. "
                f"Delete or reassign those vehicle models first."
            )

    return redirect("fleet_app:manufacturer_list")

@login_required(login_url='accounts_app:admin_login')
def create_vehicle_category(request):
    if request.method == 'POST':
        form = VehicleCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()  # Save the category

            # ✅ CREATE LOG
            log_activity(
                user=request.user,
                screen_name="Vehicle Category Master",
                action_type="CREATE",
                remark=f"Vehicle category '{category.category_name}' created"
            )

            return redirect('fleet_app:create_vehicle_category')
    else:
        form = VehicleCategoryForm()

    categories = VehicleCategory.objects.all()
    return render(request, 'vehicle_category_list.html', {
        'form': form,
        'categories': categories
    })

# Edit
@login_required(login_url='accounts_app:admin_login')
def vehicle_category_edit(request, pk):
    category = get_object_or_404(VehicleCategory, pk=pk)

    if request.method == 'POST':
        form = VehicleCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()

            # ✅ UPDATE LOG
            log_activity(
                user=request.user,
                screen_name="Vehicle Category Master",
                action_type="UPDATE",
                remark=f"Vehicle category '{category.category_name}' updated"
            )

            messages.success(request, "Vehicle category updated successfully!")
            return redirect('fleet_app:create_vehicle_category')
    else:
        form = VehicleCategoryForm(instance=category)

    categories = VehicleCategory.objects.all()
    return render(request, 'vehicle_category_list.html', {
        'form': form,
        'categories': categories,
        'edit_category': category
    })


# Delete
def vehicle_category_delete(request, pk):
    category = get_object_or_404(VehicleCategory, pk=pk)

    if request.method == 'POST':
        name = category.category_name
        category.delete()

        # ✅ DELETE LOG
        log_activity(
            user=request.user,
            screen_name="Vehicle Category Master",
            action_type="DELETE",
            remark=f"Vehicle category '{name}' deleted"
        )

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
def get_manufacturers_by_vehicle_type(request):
    category_id = request.GET.get('vehicle_category_id')
    if category_id:
        manufacturers = Manufacturer.objects.filter(vehicle_type_id=category_id)
    else:
        manufacturers = Manufacturer.objects.all()

    data = manufacturers.values('id', 'manufacturer_name').order_by('manufacturer_name')
    return JsonResponse(list(data), safe=False)


@login_required(login_url='accounts_app:admin_login')
def add_manufacturer_ajax(request):
    if request.method == 'POST':
        manufacturer_name = request.POST.get('manufacturer_name', '').strip()
        manufacturer_logo = request.FILES.get('manufacturer_logo')
        vehicle_type_id = request.POST.get('vehicle_type')

        if not manufacturer_name:
            return JsonResponse({'success': False, 'error': 'Manufacturer name is required.'})
        if Manufacturer.objects.filter(manufacturer_name__iexact=manufacturer_name).exists():
            return JsonResponse({'success': False, 'error': 'This manufacturer already exists.'})

        manufacturer = Manufacturer.objects.create(
            manufacturer_name=manufacturer_name,
            manufacturer_logo=manufacturer_logo,
            vehicle_type_id=vehicle_type_id if vehicle_type_id else None
        )

        log_activity(
            user=request.user,
            screen_name="Manufacturer Master",
            action_type="CREATE",
            remark=f"Manufacturer '{manufacturer.manufacturer_name}' created via AJAX"
        )
        return JsonResponse({
            'success': True,
            'manufacturer_id': manufacturer.id,
            'manufacturer_name': manufacturer.manufacturer_name
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='accounts_app:admin_login')
def add_vehicle_category_ajax(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        if not category_name:
            return JsonResponse({'success': False, 'error': 'Category name is required.'})
        if VehicleCategory.objects.filter(category_name__iexact=category_name).exists():
            return JsonResponse({'success': False, 'error': 'This category already exists.'})

        category = VehicleCategory.objects.create(category_name=category_name)

        log_activity(
            user=request.user,
            screen_name="Vehicle Category Master",
            action_type="CREATE",
            remark=f"Vehicle category '{category.category_name}' created via AJAX"
        )
        return JsonResponse({'success': True, 'category_id': category.id, 'category_name': category.category_name})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required(login_url='accounts_app:admin_login')
def add_manufacturer_ajax(request):
    if request.method == 'POST':
        manufacturer_name = request.POST.get('manufacturer_name', '').strip()
        manufacturer_logo = request.FILES.get('manufacturer_logo')
        vehicle_category_ids = request.POST.getlist('vehicle_categories')  # from checkboxes

        if not manufacturer_name:
            return JsonResponse({'success': False, 'error': 'Manufacturer name is required.'})
        if Manufacturer.objects.filter(manufacturer_name__iexact=manufacturer_name).exists():
            return JsonResponse({'success': False, 'error': 'This manufacturer already exists.'})

        manufacturer = Manufacturer.objects.create(
            manufacturer_name=manufacturer_name,
            manufacturer_logo=manufacturer_logo
        )
        if vehicle_category_ids:
            manufacturer.vehicle_categories.set(vehicle_category_ids)

        log_activity(
            user=request.user,
            screen_name="Manufacturer Master",
            action_type="CREATE",
            remark=f"Manufacturer '{manufacturer.manufacturer_name}' created via AJAX"
        )
        return JsonResponse({
            'success': True,
            'manufacturer_id': manufacturer.id,
            'manufacturer_name': manufacturer.manufacturer_name
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='accounts_app:admin_login')
def get_variants_by_model(request):
    model_id = request.GET.get('model_id')
    if model_id:
        variants = VehicleVariant.objects.filter(vehicle_model_id=model_id)
    else:
        variants = VehicleVariant.objects.all()

    data = variants.values('id', 'variant_name')
    return JsonResponse(list(data), safe=False)


@login_required(login_url='accounts_app:admin_login')
def get_registrations_by_variant(request):
    variant_id = request.GET.get('variant_id')
    if variant_id:
        registrations = VehicleRegistration.objects.filter(variant_id=variant_id)
    else:
        registrations = VehicleRegistration.objects.all()

    data = registrations.values('id', 'registration_number')
    return JsonResponse(list(data), safe=False)


@login_required(login_url='accounts_app:admin_login')
def create_vehicle_model(request):
    if request.method == 'POST':
        form = VehicleModelForm(request.POST)
        if form.is_valid():
            vehicle_model = form.save()
            log_activity(
                user=request.user,
                screen_name="Vehicle Model Master",
                action_type="CREATE",
                remark=f"Vehicle model '{vehicle_model.model_name}' created"
            )
            return redirect('fleet_app:vehicle_model_list')
    else:
        form = VehicleModelForm()

    return render(request, 'vehicle_model_form.html', {
        'form': form,
        'vehicle_categories': VehicleCategory.objects.all(),   # NEW
    })

@login_required(login_url='accounts_app:admin_login')
def update_vehicle_model(request, model_id):
    vehicle_model = get_object_or_404(VehicleModel, id=model_id)

    if request.method == 'POST':
        form = VehicleModelForm(request.POST, instance=vehicle_model)
        if form.is_valid():
            vehicle_model = form.save()

            # ✅ UPDATE LOG
            log_activity(
                user=request.user,
                screen_name="Vehicle Model Master",
                action_type="UPDATE",
                remark=f"Vehicle model '{vehicle_model.model_name}' updated"
            )

            return redirect('fleet_app:vehicle_model_list')
    else:
        form = VehicleModelForm(instance=vehicle_model)

    return render(request, 'update_vehicle_model.html', {
        'form': form,
        'vehicle_model': vehicle_model
    })

def delete_vehicle_model(request, pk):
    vehicle_model = get_object_or_404(VehicleModel, pk=pk)

    if request.method == "POST":
        name = vehicle_model.model_name
        vehicle_model.delete()

        # ✅ DELETE LOG
        log_activity(
            user=request.user,
            screen_name="Vehicle Model Master",
            action_type="DELETE",
            remark=f"Vehicle model '{name}' deleted"
        )

        messages.success(request, "Vehicle model deleted successfully!")

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
        is_edit = True
    else:
        vehicle = None
        is_edit = False

    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            saved_vehicle = form.save()

            # ✅ CREATE / UPDATE LOG
            log_activity(
                user=request.user,
                screen_name="Vehicle Master",
                action_type="UPDATE" if is_edit else "CREATE",
                remark=(
                    f"Vehicle '{saved_vehicle.vehicle_name}' updated"
                    if is_edit else
                    f"Vehicle '{saved_vehicle.vehicle_name}' created"
                )
            )

            return redirect('fleet_app:vehicle_list')
    else:
        form = VehicleForm(instance=vehicle)

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
    """
    Display all vehicles with optional P&L summary.
    Supports filtering by ownership and supplier.
    """
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
    
    # ✅ ADD P&L SUMMARY (Optional - can be toggled via URL parameter)
    # Usage: ?show_pl=true (default) or ?show_pl=false to disable
    show_pl_preview = request.GET.get('show_pl', 'true').lower() == 'true'
    
    if show_pl_preview:
        # Calculate P&L for current month
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        # Add P&L summary to each vehicle
        for vehicle in vehicles:
            try:
                summary = get_vehicle_profit_loss_summary(
                    vehicle, 
                    start_date=month_start,
                    end_date=today
                )
                # Attach summary to vehicle object for template use
                vehicle.pl_summary = summary
            except Exception as e:
                # If P&L calculation fails for this vehicle, just skip it
                # This ensures one vehicle's error doesn't break the entire page
                print(f"Warning: Could not calculate P&L for vehicle {vehicle.id}: {e}")
                vehicle.pl_summary = None
    
    context = {
        'vehicles': vehicles,
        'suppliers': suppliers,
        'show_pl_preview': show_pl_preview,  # Pass to template
    }
    
    return render(request, 'vehicle_list.html', context)

def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if request.method == "POST":
        reg_no = vehicle.registration_no
        vehicle.delete()

        # ✅ DELETE LOG
        log_activity(
            user=request.user,
            screen_name="Vehicle Master",
            action_type="DELETE",
            remark=f"Vehicle '{vehicle_name}' deleted"
        )

        messages.success(request, "Vehicle deleted successfully!")

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

    
TIMESHEET_MENU_ID = 1

def time_sheet_view(request, timesheet_id=None):

    timesheet_instance = None
    existing_details = []

    if timesheet_id:
        timesheet_instance = get_object_or_404(TimeSheet, id=timesheet_id)
        existing_details = TimeSheetDetail.objects.filter(
            timesheet=timesheet_instance
        ).order_by('date')

    if request.method == 'POST':

        # 🔐 DETERMINE ACTION
        action = "can_edit" if timesheet_id else "can_add"

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            TIMESHEET_MENU_ID,
            action
        )

        if not has_permission:
            # 🔐 TRY ADMIN OVERRIDE
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

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

            # ✅ AUDIT LOG (CREATE / UPDATE)
            log_activity(
                user=request.user,
                screen_name="Timesheet",
                action_type="UPDATE" if timesheet_id else "CREATE",
                remark=(
                    f"Timesheet {timesheet.voucher_no} updated"
                    if timesheet_id else
                    f"Timesheet {timesheet.voucher_no} created"
                )
            )


            if timesheet_id:
                success_message = f"Timesheet #{timesheet.voucher_no} updated successfully!"
            else:
                success_message = f"Timesheet #{timesheet.voucher_no} created successfully!"

            # ✅ Return JSON with PDF URL instead of PDF directly
            return JsonResponse({
                "success": True,
                "message": success_message,
                "pdf_url": reverse('fleet_app:timesheet_pdf', args=[timesheet.id])
            })

        # ✅ Return validation errors as JSON
        return JsonResponse({
            "success": False,
            "message": "Please fix the errors and try again.",
            "errors": {
                "form": timesheet_form.errors,
                "formset": detail_formset.errors
            }
        }, status=400)

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

def timesheet_pdf_view(request, timesheet_id):
    """Generate and return PDF for a timesheet"""
    timesheet = get_object_or_404(TimeSheet, id=timesheet_id)
    return create_timesheet_pdf(timesheet)

@require_http_methods(["POST"])
def timesheet_delete(request, timesheet_id):

    TIMESHEET_MENU_ID = 1

    # 🔐 CHECK DELETE PRIVILEGE
    has_permission = check_privilege(
        request.user,
        TIMESHEET_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    try:
        with transaction.atomic():
            timesheet = TimeSheet.objects.get(id=timesheet_id)
            voucher_no = timesheet.voucher_no

            timesheet.delete()  # ❗ real delete

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Timesheet",
                action_type="DELETE",
                remark=f"Timesheet {voucher_no} deleted"
            ))

        return JsonResponse({
            'success': True,
            'message': f'Timesheet {voucher_no} deleted successfully'
        })

    except TimeSheet.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Timesheet not found'
        }, status=404)

# List Report
from django.utils.dateparse import parse_date

def timesheet_report(request):

    timesheets = TimeSheet.objects.all().order_by('voucher_no')

    # 📅 Single date filter
    selected_date = request.GET.get('date')

    if selected_date:
        timesheets = timesheets.filter(date=parse_date(selected_date))

    return render(request, 'timesheet_report.html', {
        'timesheets': timesheets,
        'selected_date': selected_date,
    })

def timesheet_pdf_without_header(request, pk):
    """
    Generate timesheet PDF without header image
    Temporarily disables enable_header flag for this view only
    """
    timesheet = get_object_or_404(TimeSheet, pk=pk)
    
    # Store original header setting
    original_header_setting = timesheet.enable_header
    
    # Temporarily disable header for this PDF generation
    timesheet.enable_header = False
    #temporarily disable footer for this PDF generation
    timesheet.enable_footer = False
    
    # Generate PDF
    response = create_timesheet_pdf(timesheet)
    
    # Restore original setting (important: don't save to database)
    timesheet.enable_header = original_header_setting
    
    return response

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

    instance = get_object_or_404(StaffCategory, pk=pk) if pk else None

    if request.method == 'POST':

        # 🗑️ DELETE
        if 'delete' in request.POST:
            instance = get_object_or_404(
                StaffCategory, pk=request.POST.get('delete')
            )
            name = instance.name
            instance.delete()

            # ✅ AUDIT LOG — DELETE
            log_activity(
                user=request.user,
                screen_name="Staff Category",
                action_type="DELETE",
                remark=f"Staff category '{name}' deleted"
            )

            return redirect('fleet_app:staff_category_manage')

        # ➕ CREATE / ✏️ UPDATE
        form = StaffCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            saved = form.save()
            is_edit = pk is not None

            # ✅ AUDIT LOG — CREATE / UPDATE
            log_activity(
                user=request.user,
                screen_name="Staff Category",
                action_type="UPDATE" if is_edit else "CREATE",
                remark=(
                    f"Staff category '{saved.name}' updated"
                    if is_edit else
                    f"Staff category '{saved.name}' created"
                )
            )

            return redirect('fleet_app:staff_category_manage')

    else:
        form = StaffCategoryForm(instance=instance)

    categories = StaffCategory.objects.all()
    return render(request, 'staff_category_manage.html', {
        'form': form,
        'categories': categories,
        'edit_id': pk
    })
    
def staff_manage(request, pk=None):

    instance = get_object_or_404(Staff, pk=pk) if pk else None

    if request.method == 'POST':

        # 🗑️ DELETE
        if 'delete' in request.POST:
            instance = get_object_or_404(
                Staff, pk=request.POST.get('delete')
            )
            name = instance.name
            category = instance.staff_category

            instance.delete()

            # ✅ AUDIT LOG — DELETE
            log_activity(
                user=request.user,
                screen_name="Staff",
                action_type="DELETE",
                remark=(
                    f"Staff '{name}' deleted "
                    f"(Category: {category})"
                )
            )

            return redirect('fleet_app:staff_manage')

        # ➕ CREATE / ✏️ UPDATE
        form = StaffForm(request.POST, instance=instance)
        if form.is_valid():
            saved = form.save()
            is_edit = pk is not None

            # ✅ AUDIT LOG — CREATE / UPDATE
            log_activity(
                user=request.user,
                screen_name="Staff",
                action_type="UPDATE" if is_edit else "CREATE",
                remark=(
                    f"Staff '{saved.full_name}' updated "
                    f"(Category: {saved.staff_category})"
                    if is_edit else
                    f"Staff '{saved.full_name}' created "
                    f"(Category: {saved.staff_category})"
                )
            )

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
    form = DocumentForm(
        request.POST or None,
        request.FILES or None,
        instance=instance
    )

    if request.method == 'POST':

        # 🗑️ DELETE
        if 'delete' in request.POST and instance:
            doc_name = instance.title if hasattr(instance, 'title') else instance.id
            instance.delete()

            # ✅ AUDIT LOG — DELETE
            log_activity(
                user=request.user,
                screen_name="Document",
                action_type="DELETE",
                remark=f"Document '{title}' deleted"
            )

            messages.success(request, "Document deleted.")
            return redirect('fleet_app:document_crud')

        # ➕ CREATE / ✏️ UPDATE
        elif form.is_valid():
            saved_doc = form.save()
            is_edit = instance is not None
            doc_name = saved_doc.title if hasattr(saved_doc, 'title') else saved_doc.id

            # ✅ AUDIT LOG — CREATE / UPDATE
            log_activity(
                user=request.user,
                screen_name="Document",
                action_type="UPDATE" if is_edit else "CREATE",
                remark=(
                    f"Document '{title}' updated"
                    if is_edit else
                    f"Document '{title}' created"
                )
            )

            messages.success(
                request,
                "Document updated." if is_edit else "Document created."
            )
            return redirect('fleet_app:document_crud')

    return render(request, 'document_crud.html', {
        'form': form,
        'documents': documents,
        'instance': instance
    })


SIMPLE_QUOTATION_MENU_ID = 2
def create_simple_quotation(request, quotation_id=None):
    """
    Unified view for creating and editing quotations
    """

    quotation_instance = None
    existing_details = []

    if quotation_id:
        quotation_instance = get_object_or_404(SimpleQuotation, id=quotation_id)
        existing_details = SimpleQuotationDetails.objects.filter(
            quotation=quotation_instance
        ).order_by('id')

    if request.method == 'POST':

        # 🔐 DETERMINE ACTION
        action = "can_edit" if quotation_id else "can_add"

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            SIMPLE_QUOTATION_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        # ✅ FORM PROCESSING
        form = SimpleQuotationForm(request.POST, instance=quotation_instance)
        details_data = request.POST.getlist('details[]')

        if form.is_valid():
            quotation = form.save()

            # 🔄 EDIT MODE – remove old details
            if quotation_id:
                SimpleQuotationDetails.objects.filter(
                    quotation=quotation
                ).delete()

            # ➕ CREATE DETAILS
            for entry in details_data:
                parts = entry.split('|')
                if len(parts) >= 4:
                    vehicle_id = parts[0].strip() or None
                    desc = parts[1].strip()
                    qty = parts[2].strip()
                    rent = parts[3].strip()
                    period = parts[4].strip() if len(parts) >= 5 else 'Hour'
                    tax_amount = parts[5].strip() if len(parts) >= 6 else '0'
                    total_amount = parts[6].strip() if len(parts) >= 7 else '0'

                    if desc and qty and rent:
                        vehicle_instance = None
                        if vehicle_id:
                            try:
                                vehicle_instance = Vehicle.objects.get(id=int(vehicle_id))
                            except:
                                pass

                        SimpleQuotationDetails.objects.create(
                            quotation=quotation,
                            vehicle=vehicle_instance,
                            description=desc,
                            quantity=int(qty),
                            rent=Decimal(rent),
                            period=period,
                            tax_amount=Decimal(tax_amount),
                            total_amount=Decimal(total_amount),
                            created_by=request.user.id
                        )
            
            # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL SAVE
            log_activity(
                user=request.user,
                screen_name="Simple Quotation",
                action_type="UPDATE" if quotation_id else "CREATE",
                remark=(
                    f"Quotation {quotation.voucher_no} updated"
                    if quotation_id else
                    f"Quotation {quotation.voucher_no} created"
                )
            )            

            # ✅ SUCCESS RESPONSE (JSON)
            return JsonResponse({
                "success": True,
                "message": (
                    f"Quotation #{quotation.voucher_no} updated successfully!"
                    if quotation_id else
                    f"Quotation #{quotation.voucher_no} created successfully!"
                ),
                "pdf_url": reverse(
                    'fleet_app:simple_quotation_pdf',
                    args=[quotation.id]
                )
            })

        return JsonResponse({
            "success": False,
            "message": "Please correct the errors in the form",
            "errors": form.errors
        }, status=400)

    # GET REQUEST
    form = SimpleQuotationForm(instance=quotation_instance)

    return render(request, 'create_simple_quotation.html', {
        'form': form,
        'vehicles': Vehicle.objects.all().order_by('vehicle_name'),
        'quotation_instance': quotation_instance,
        'existing_details': existing_details,
        'is_edit_mode': quotation_id is not None,
    })

def simple_quotation_pdf(request, quotation_id):
    """
    Generate and return PDF for Simple Quotation
    """
    quotation = get_object_or_404(SimpleQuotation, id=quotation_id)
    return create_simplequotation_pdf(quotation)


def simple_quotation_list(request):

    quotations = (
        SimpleQuotation.objects
        .select_related('customer')
        .prefetch_related('details')
        .order_by('voucher_no')
    )

    # 📅 Dynamic single date filter
    selected_date = request.GET.get('date')

    if selected_date:
        quotations = quotations.filter(date=parse_date(selected_date))

    return render(request, 'simple_quotation_list.html', {
        'quotations': quotations,
        'selected_date': selected_date,
    })

@require_http_methods(["POST"])
def simple_quotation_delete(request, quotation_id):

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        SIMPLE_QUOTATION_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    try:
        with transaction.atomic():
            quotation = SimpleQuotation.objects.get(id=quotation_id)
            voucher_no = quotation.voucher_no

            quotation.delete()  # ❗ real delete

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Simple Quotation",
                action_type="DELETE",
                remark=f"Quotation {voucher_no} deleted"
            ))

        return JsonResponse({
            "success": True,
            "message": f"Quotation {voucher_no} deleted successfully"
        })

    except SimpleQuotation.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Quotation not found"
        }, status=404)

def simplequotation_pdf_without_header(request, pk):
    """
    Generate simple quotation PDF without header image
    Temporarily disables enable_header flag for this view only
    """
    quotation = get_object_or_404(SimpleQuotation, pk=pk)
    
    # Store original header setting
    original_header_setting = quotation.enable_header
    
    # Temporarily disable header for this PDF generation
    quotation.enable_header = False
    # Temporarily disable footer for this PDF generation
    quotation.enable_footer = False
    
    # Generate PDF
    response = create_simplequotation_pdf(quotation)
    
    # Restore original setting (important: don't save to database)
    quotation.enable_header = original_header_setting
    
    return response

# INVOICE_MENU_ID = 5
# def create_invoice(request, invoice_id=None):

#     vehicles = Vehicle.objects.all().order_by('vehicle_name')

#     invoice_instance = None
#     existing_details = []

#     if invoice_id:
#         invoice_instance = get_object_or_404(Invoice, id=invoice_id)
#         existing_details = InvoiceDetails.objects.filter(
#             invoice=invoice_instance
#         ).select_related('vehicle')

#     if request.method == 'POST':

#         action = "can_edit" if invoice_id else "can_add"

#         has_permission = check_privilege(
#             request.user,
#             INVOICE_MENU_ID,
#             action
#         )

#         if not has_permission:
#             is_admin_ok, msg_or_admin = check_admin_override(request)
#             if not is_admin_ok:
#                 return JsonResponse({
#                     "admin_required": True,
#                     "message": msg_or_admin
#                 }, status=403)

#         invoice_form = InvoiceForm(request.POST, instance=invoice_instance)

#         if invoice_form.is_valid():
#             try:
#                 with transaction.atomic():
#                     invoice = invoice_form.save(commit=False)

#                     grand_total = request.POST.get('grand_total')
#                     invoice.grand_total = float(grand_total) if grand_total else 0.0
                    
#                     # Get invoice type
#                     invoice_type = request.POST.get('invoice_type', 'simple')
#                     invoice.invoice_type = invoice_type
                    
#                     invoice.save()

#                     details_data = request.POST.getlist('details[]')
                    
#                     # NEW: Get contract detail IDs if invoicing from delivery contract
#                     contract_detail_ids = request.POST.getlist('contract_detail_ids[]')

#                     if not details_data:
#                         if not invoice_id:
#                             invoice.delete()
#                         return JsonResponse({
#                             "success": False,
#                             "message": "Please add at least one invoice detail."
#                         }, status=400)

#                     if invoice_id:
#                         InvoiceDetails.objects.filter(invoice=invoice).delete()

#                     created_detail_ids = []  # Track which contract details were invoiced
                    
#                     for idx, detail_str in enumerate(details_data):
#                         # Parse detail string based on invoice type
#                         if invoice_type == 'complex':
#                             # Format: vehicle_id|location|period|quantity|unit_rate|tax|from_date|to_date
#                             parts = detail_str.split('|')
#                             vehicle_id = parts[0]
#                             location = parts[1]
#                             period = parts[2]
#                             quantity = float(parts[3])
#                             unit_rate = float(parts[4])
#                             tax = float(parts[5])
                            
#                             # Handle optional dates
#                             from_date = None
#                             to_date = None
                            
#                             if len(parts) > 6 and parts[6] and parts[6].strip():
#                                 try:
#                                     from_date = parts[6]
#                                 except:
#                                     from_date = None
                            
#                             if len(parts) > 7 and parts[7] and parts[7].strip():
#                                 try:
#                                     to_date = parts[7]
#                                 except:
#                                     to_date = None
                            
#                             # Calculate amount from quantity × unit_rate
#                             amount = quantity * unit_rate
                            
#                             vehicle = Vehicle.objects.get(id=vehicle_id)
                            
#                             tax_amount = (amount * tax / 100)
#                             total_amount = amount + tax_amount

#                             InvoiceDetails.objects.create(
#                                 invoice=invoice,
#                                 vehicle=vehicle,
#                                 location=location,
#                                 amount=amount,
#                                 tax=tax,
#                                 tax_amount=tax_amount,
#                                 total_amount=total_amount,
#                                 period=period,
#                                 quantity=quantity,
#                                 unit_rate=unit_rate,
#                                 from_date=from_date,
#                                 to_date=to_date,
#                             )
#                         else:
#                             # Simple invoice format: vehicle_id|location|amount|tax
#                             vehicle_id, location, amount, tax = detail_str.split('|')
#                             vehicle = Vehicle.objects.get(id=vehicle_id)

#                             amount = float(amount)
#                             tax = float(tax)
#                             tax_amount = (amount * tax / 100)
#                             total_amount = amount + tax_amount

#                             InvoiceDetails.objects.create(
#                                 invoice=invoice,
#                                 vehicle=vehicle,
#                                 location=location,
#                                 amount=amount,
#                                 tax=tax,
#                                 tax_amount=tax_amount,
#                                 total_amount=total_amount,
#                             )
                        
#                         # NEW: Track contract detail ID for this invoice detail
#                         if contract_detail_ids and idx < len(contract_detail_ids):
#                             contract_detail_id = contract_detail_ids[idx]
#                             if contract_detail_id and contract_detail_id.strip():
#                                 created_detail_ids.append(int(contract_detail_id))
                    
#                     # NEW: Mark delivery contract details as cleared (invoiced)
#                     if created_detail_ids:
#                         DeliveryContractDetails.objects.filter(
#                             id__in=created_detail_ids
#                         ).update(IsCleared=True)
                        
#                         print(f"✅ Marked {len(created_detail_ids)} contract details as invoiced: {created_detail_ids}")

#                     if invoice_id:
#                         delete_ledger_postings_for_invoice(invoice)
#                     create_ledger_postings_for_invoice(invoice)
                    
#                     # ✅ UPDATE VEHICLE PROFIT & LOSS
#                     update_vehicle_profit_loss_for_invoice(invoice)
                    
#                 # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
#                 log_activity(
#                     user=request.user,
#                     screen_name="Invoice",
#                     action_type="UPDATE" if invoice_id else "CREATE",
#                     remark=(
#                         f"Invoice {invoice.invoice_no} updated "
#                         f"with total {invoice.grand_total:.3f}"
#                         if invoice_id else
#                         f"Invoice {invoice.invoice_no} created "
#                         f"with total {invoice.grand_total:.3f}"
#                     )
#                 )    

#                 return JsonResponse({
#                     "success": True,
#                     "message": "Invoice updated successfully!" if invoice_id else "Invoice created successfully!",
#                     "pdf_url": reverse('fleet_app:invoice_pdf', args=[invoice.id])
#                 })
            
#             except Exception as e:
#                 return JsonResponse({
#                     "success": False,
#                     "message": f"Error: {str(e)}"
#                 }, status=400)

#         return JsonResponse({
#             "success": False,
#             "message": "Please correct the errors in the invoice form.",
#             "errors": invoice_form.errors
#         }, status=400)

#     invoice_form = InvoiceForm(instance=invoice_instance)

#     return render(request, 'create_invoice.html', {
#         'invoice_form': invoice_form,
#         'vehicles': vehicles,
#         'invoice_instance': invoice_instance,
#         'existing_details': existing_details,
#         'is_edit_mode': invoice_id is not None,
#     })

INVOICE_MENU_ID = 5
def create_invoice(request, invoice_id=None):

    vehicles = Vehicle.objects.all().order_by('vehicle_name')

    invoice_instance = None
    existing_details = []

    if invoice_id:
        invoice_instance = get_object_or_404(Invoice, id=invoice_id)

        # ✅ CHECK IF Receipt Bill Exists for Edit
        if invoice_instance.is_locked():
            messages.error(request, "This invoice is locked because receipt exists.")
            return redirect('fleet_app:invoice_list')

        existing_details = InvoiceDetails.objects.filter(
            invoice=invoice_instance
        ).select_related('vehicle')

    if request.method == 'POST':

        action = "can_edit" if invoice_id else "can_add"

        has_permission = check_privilege(
            request.user,
            INVOICE_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        invoice_form = InvoiceForm(request.POST, instance=invoice_instance)

        if invoice_form.is_valid():
            try:
                with transaction.atomic():
                    invoice = invoice_form.save(commit=False)

                    grand_total = request.POST.get('grand_total')
                    invoice.grand_total = float(grand_total) if grand_total else 0.0

                    # Get invoice type
                    invoice_type = request.POST.get('invoice_type', 'simple')
                    invoice.invoice_type = invoice_type

                    # ✅ FIX: update cleared status when payment mode changes
                    if invoice.payment_mode == "Cash":
                        invoice.IsCleared = True
                    else:
                        invoice.IsCleared = False

                    invoice.save()

                    details_data = request.POST.getlist('details[]')
                    
                    # NEW: Get contract detail IDs if invoicing from delivery contract
                    contract_detail_ids = request.POST.getlist('contract_detail_ids[]')

                    if not details_data:
                        if not invoice_id:
                            invoice.delete()
                        return JsonResponse({
                            "success": False,
                            "message": "Please add at least one invoice detail."
                        }, status=400)

                    if invoice_id:
                        InvoiceDetails.objects.filter(invoice=invoice).delete()

                    created_detail_ids = []  # Track which contract details were invoiced
                    affected_contracts = set()  # Track which contracts were affected
                    
                    for idx, detail_str in enumerate(details_data):
                        # Parse detail string based on invoice type
                        if invoice_type == 'complex':
                            # Format: vehicle_id|location|period|quantity|unit_rate|tax|from_date|to_date|vehicle_model|description
                            parts = detail_str.split('|')
                            vehicle_id = parts[0]
                            location = parts[1]
                            period = parts[2]
                            quantity = float(parts[3])
                            unit_rate = float(parts[4])
                            tax = float(parts[5])
                            
                            # Handle optional dates
                            from_date = None
                            to_date = None
                            
                            if len(parts) > 6 and parts[6] and parts[6].strip():
                                try:
                                    from_date = parts[6]
                                except:
                                    from_date = None
                            
                            if len(parts) > 7 and parts[7] and parts[7].strip():
                                try:
                                    to_date = parts[7]
                                except:
                                    to_date = None
                            
                            vehicle_model_val = parts[8] if len(parts) > 8 else ''
                            description_val = parts[9] if len(parts) > 9 else ''
                            
                            # Calculate amount from quantity × unit_rate
                            amount = quantity * unit_rate
                            
                            vehicle = Vehicle.objects.get(id=vehicle_id)
                            
                            tax_amount = (amount * tax / 100)
                            total_amount = amount + tax_amount

                            InvoiceDetails.objects.create(
                                invoice=invoice,
                                vehicle=vehicle,
                                vehicle_model=vehicle_model_val,
                                description=description_val,
                                location=location,
                                amount=amount,
                                tax=tax,
                                tax_amount=tax_amount,
                                total_amount=total_amount,
                                period=period,
                                quantity=quantity,
                                unit_rate=unit_rate,
                                from_date=from_date,
                                to_date=to_date,
                            )
                        else:
                            # Simple invoice format: vehicle_id|location|amount|tax|vehicle_model|description
                            parts = detail_str.split('|')
                            vehicle_id = parts[0]
                            location = parts[1]
                            amount = float(parts[2])
                            tax = float(parts[3])
                            vehicle_model_val = parts[4] if len(parts) > 4 else ''
                            description_val = parts[5] if len(parts) > 5 else ''
                            vehicle = Vehicle.objects.get(id=vehicle_id)

                            tax_amount = (amount * tax / 100)
                            total_amount = amount + tax_amount

                            InvoiceDetails.objects.create(
                                invoice=invoice,
                                vehicle=vehicle,
                                vehicle_model=vehicle_model_val,
                                description=description_val,
                                location=location,
                                amount=amount,
                                tax=tax,
                                tax_amount=tax_amount,
                                total_amount=total_amount,
                            )
                        
                        # NEW: Track contract detail ID for this invoice detail
                        if contract_detail_ids and idx < len(contract_detail_ids):
                            contract_detail_id = contract_detail_ids[idx]
                            if contract_detail_id and contract_detail_id.strip():
                                created_detail_ids.append(int(contract_detail_id))
                    
                    # NEW: Mark delivery contract details as cleared (invoiced)
                    if created_detail_ids:
                        # Get the contract details that are being invoiced
                        invoiced_contract_details = DeliveryContractDetails.objects.filter(
                            id__in=created_detail_ids
                        ).select_related('delivery_contract')
                        
                        # Mark them as cleared
                        for detail in invoiced_contract_details:
                            detail.IsCleared = True
                            detail.save()
                            # Track which contracts are affected
                            affected_contracts.add(detail.delivery_contract.id)
                        
                        print(f"✅ Marked {len(created_detail_ids)} contract details as invoiced: {created_detail_ids}")

                    if invoice_id:
                        delete_ledger_postings_for_invoice(invoice)
                    create_ledger_postings_for_invoice(invoice)
                    
                    # ✅ UPDATE VEHICLE PROFIT & LOSS
                    update_vehicle_profit_loss_for_invoice(invoice)
                    
                # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
                log_activity(
                    user=request.user,
                    screen_name="Invoice",
                    action_type="UPDATE" if invoice_id else "CREATE",
                    remark=(
                        f"Invoice {invoice.invoice_no} updated "
                        f"with total {invoice.grand_total:.3f}"
                        if invoice_id else
                        f"Invoice {invoice.invoice_no} created "
                        f"with total {invoice.grand_total:.3f}"
                    )
                )    

                return JsonResponse({
                    "success": True,
                    "message": "Invoice updated successfully!" if invoice_id else "Invoice created successfully!",
                    "pdf_url": reverse('fleet_app:invoice_pdf', args=[invoice.id])
                })
            
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": f"Error: {str(e)}"
                }, status=400)

        return JsonResponse({
            "success": False,
            "message": "Please correct the errors in the invoice form.",
            "errors": invoice_form.errors
        }, status=400)

    invoice_form = InvoiceForm(instance=invoice_instance)

    return render(request, 'create_invoice.html', {
        'invoice_form': invoice_form,
        'vehicles': vehicles,
        'invoice_instance': invoice_instance,
        'existing_details': existing_details,
        'is_edit_mode': invoice_id is not None,
    })

# NEW: API endpoint to get vehicle rates
def get_vehicle_rates(request):
    """
    Returns the hourly, daily, and monthly rates for a given vehicle
    """
    vehicle_id = request.GET.get('vehicle_id')
    
    if not vehicle_id:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle ID is required'
        }, status=400)
    
    try:
        vehicle = Vehicle.objects.get(id=vehicle_id)
        # Build a vehicle model string combining model name and year
        model_parts = []
        if vehicle.model:
            model_parts.append(str(vehicle.model))
        if vehicle.model_year:
            model_parts.append(str(vehicle.model_year))
        vehicle_model_str = ' - '.join(model_parts) if model_parts else ''

        return JsonResponse({
            'success': True,
            'rate_per_hr': str(vehicle.rate_per_hr or 0),
            'rate_per_day': str(vehicle.rate_per_day or 0),
            'rate_per_month': str(vehicle.rate_per_month or 0),
            'description': vehicle.description or '',
            'model_year': str(vehicle.model_year or ''),
            'vehicle_model': vehicle_model_str,
        })
    except Vehicle.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Vehicle not found'
        }, status=404)    

def invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return create_invoice_pdf(invoice)

def invoice_list(request):

    invoices = Invoice.objects.all().order_by('voucher_no')

    # 📅 Dynamic single date filter
    selected_date = request.GET.get('date')

    if selected_date:
        invoices = invoices.filter(date=parse_date(selected_date))

    return render(request, 'invoice_list.html', {
        'invoices': invoices,
        'selected_date': selected_date,
    })
    

@require_http_methods(["POST"])
def invoice_delete(request, invoice_id):
    """Delete invoice with P&L cleanup"""

    has_permission = check_privilege(
        request.user,
        INVOICE_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    try:
        with transaction.atomic():
            invoice = Invoice.objects.get(id=invoice_id)

            # ✅ CHECK IF Receipt Bill Exists
            if invoice.is_locked():
                return JsonResponse({
                    "success": False,
                    "message": "Cannot delete invoice. Receipt already exists."
                }, status=400)
            number = invoice.invoice_no if hasattr(invoice, "invoice_no") else invoice.id
            total = invoice.grand_total

            # ✅ DELETE VEHICLE P&L
            delete_vehicle_profit_loss_for_invoice(invoice)

            # ✅ DELETE LEDGER POSTINGS
            delete_ledger_postings_for_invoice(invoice)

            # ✅ DELETE INVOICE
            invoice.delete()

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Invoice",
                action_type="DELETE",
                remark=f"Invoice {number} deleted with total {total:.3f}"
            ))

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
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": f"Error deleting invoice: {str(e)}"
        }, status=500)
        
        
def invoice_pdf_without_header(request, pk):
    """
    Generate invoice PDF without header image
    Temporarily disables enable_header flag for this view only
    """
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Store original header setting
    original_header_setting = invoice.enable_header
    
    # Temporarily disable header for this PDF generation
    invoice.enable_header = False
     # Temporarily disable footer for this PDF generation
    invoice.enable_footer = False
    # Generate PDF
    response = create_invoice_pdf(invoice)
    
    # Restore original setting (important: don't save to database)
    invoice.enable_header = original_header_setting
    
    return response

    
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

            # ✅ AUDIT LOG (CREATE / UPDATE)
            log_activity(
                user=request.user,
                screen_name="Company",
                action_type="UPDATE" if company else "CREATE",
                remark=(
                    f"Company {company.name} updated"
                    if company else
                    f"Company {company.name} created"
                )
            )
            
            
            
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
    edit_doc = None

    # 🔵 EDIT MODE
    doc_id = request.GET.get("edit")
    if doc_id:
        edit_doc = get_object_or_404(CompanyDocument, id=doc_id, company=company)

    if request.method == "POST":
        post_doc_id = request.POST.get("doc_id")

        if post_doc_id:
            # 🟡 UPDATE
            edit_doc = get_object_or_404(CompanyDocument, id=post_doc_id, company=company)
            form = CompanyDocumentForm(request.POST, request.FILES, instance=edit_doc)
            msg = "Document updated successfully!"
        else:
            # 🟢 CREATE
            form = CompanyDocumentForm(request.POST, request.FILES)
            msg = "Document uploaded successfully!"

        if form.is_valid():
            doc = form.save(commit=False)
            doc.company = company
            doc.save()
            messages.success(request, msg)
            return redirect("fleet_app:document_list")
    else:
        form = CompanyDocumentForm(instance=edit_doc)

    return render(request, "company_document_list.html", {
        "company": company,
        "documents": documents,
        "doc_form": form,
        "edit_doc": edit_doc,
    })


def document_delete(request, doc_id):
    doc = get_object_or_404(CompanyDocument, id=doc_id)
    doc.delete()
    messages.success(request, "Document deleted successfully!")
    return redirect("fleet_app:document_list")


FLEET_HIRE_MENU_ID = 6
def fleet_hire_create(request, hire_id=None):

    vehicles = Vehicle.objects.filter(is_owned=False)

    hire_instance = None
    existing_details = []

    if hire_id:
        hire_instance = get_object_or_404(FleetHire, id=hire_id)

        # ✅ CHECK IF Payment Bill Exists for Edit
        if hire_instance.is_locked():
            messages.error(request, "This hire is locked because Payment Bill exists.")
            return redirect('fleet_app:fleet_hire_list')
        existing_details = FleetHireDetails.objects.filter(
            fleet_hire=hire_instance
        ).select_related('vehicle')

    if request.method == "POST":

        action = "can_edit" if hire_id else "can_add"

        has_permission = check_privilege(
            request.user,
            FLEET_HIRE_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        form = FleetHireForm(request.POST, instance=hire_instance)

        if form.is_valid():
            try:
                with transaction.atomic():
                    fleet_hire = form.save(commit=False)

                    # Update cleared status
                    if fleet_hire.payment_mode == "Cash":
                        fleet_hire.IsCleared = True
                    else:
                        fleet_hire.IsCleared = False

                    fleet_hire.save()

                    if hire_id:
                        FleetHireDetails.objects.filter(
                            fleet_hire=fleet_hire
                        ).delete()
                        delete_ledger_postings_for_hire(fleet_hire)

                    vehicles_list = request.POST.getlist("details-vehicle[]")
                    reg_nos = request.POST.getlist("details-reg_no[]")
                    start_dates = request.POST.getlist("details-start_date[]")
                    end_dates = request.POST.getlist("details-end_date[]")
                    units = request.POST.getlist("details-unit[]")
                    no_of_units = request.POST.getlist("details-no_of_unit[]")
                    rates = request.POST.getlist("details-rate_per_period[]")

                    for i in range(len(vehicles_list)):
                        if not vehicles_list[i]:
                            continue

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

                    create_ledger_postings_for_hire(fleet_hire)
                    
                    # ✅ UPDATE VEHICLE PROFIT & LOSS
                    update_vehicle_profit_loss_for_hire(fleet_hire)
                    
                # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
                log_activity(
                    user=request.user,
                    screen_name="Fleet Hire",
                    action_type="UPDATE" if hire_id else "CREATE",
                    remark=(
                        f"Fleet Hire {fleet_hire.voucher_no} updated"
                        if hire_id else
                        f"Fleet Hire {fleet_hire.voucher_no} created"
                    )
                )    

                return JsonResponse({
                    "success": True,
                    "message": (
                        "Fleet hire updated successfully!"
                        if hire_id else
                        "Fleet hire created successfully!"
                    )
                })

            except Exception as e:
                if not hire_id and fleet_hire.pk:
                    fleet_hire.delete()

                return JsonResponse({
                    "success": False,
                    "message": f"Unexpected error: {e}"
                }, status=400)

        return JsonResponse({
            "success": False,
            "message": "Please correct the errors below.",
            "errors": form.errors
        }, status=400)

    form = FleetHireForm(instance=hire_instance)

    return render(request, "fleet_hire_form.html", {
        "form": form,
        "vehicle": vehicles,
        "hire_instance": hire_instance,
        "existing_details": existing_details,
        "is_edit_mode": hire_id is not None,
    })

# List of all FleetHire
def fleet_hire_list(request):
    
    hires = FleetHire.objects.all().order_by('-invoice_date', '-voucher_no')
    return render(request, "fleet_hire_list.html", {"hires": hires})

@require_http_methods(["POST"])
def fleet_hire_delete(request, hire_id):
    """Delete fleet hire with P&L cleanup"""

    has_permission = check_privilege(
        request.user,
        FLEET_HIRE_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    try:
        with transaction.atomic():
            hire = FleetHire.objects.get(id=hire_id)

            # ✅ CHECK IF Payment Bill Exists
            if hire.is_locked():
                return JsonResponse({
                    "success": False,
                    "message": "Cannot delete hire. Payment Bill already exists."
                }, status=400)
            voucher = hire.voucher_no if hasattr(hire, "voucher_no") else hire.id

            # ✅ DELETE VEHICLE P&L
            delete_vehicle_profit_loss_for_hire(hire)

            # ✅ DELETE LEDGER POSTINGS
            delete_ledger_postings_for_hire(hire)

            # ✅ DELETE HIRE
            hire.delete()

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Fleet Hire",
                action_type="DELETE",
                remark=f"Fleet Hire {voucher} deleted"
            ))

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
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "message": f"Error deleting fleet hire: {str(e)}"
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



CONTRACT_MENU_ID = 3

def create_fleet_contract(request, pk=None):

    instance = get_object_or_404(FleetContract, pk=pk) if pk else None

    if request.method == "POST":

        action = "can_edit" if pk else "can_add"

        if not check_privilege(request.user, CONTRACT_MENU_ID, action):
            is_admin_ok, msg = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg
                }, status=403)

        form = FleetContractForm(request.POST, instance=instance)

        if form.is_valid():
            contract = form.save()
            
            # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL SAVE
            log_activity(
                user=request.user,
                screen_name="Fleet Contract",
                action_type="UPDATE" if pk else "CREATE",
                remark=(
                    f"Contract {contract.voucher_no} updated"
                    if pk else
                    f"Contract {contract.voucher_no} created"
                )
            )
    
            return JsonResponse({
                "success": True,
                "message": (
                    "Contract updated successfully!"
                    if pk else
                    "Contract created successfully!"
                )
            })

        return JsonResponse({
            "success": False,
            "message": "Please fix the errors",
            "errors": form.errors
        }, status=400)

    # GET request (UNCHANGED)
    form = FleetContractForm(
        instance=instance,
        initial={"date": timezone.now().date()} if not instance else None
    )

    return render(request, "contract_form.html", {
        "form": form,
        "edit_mode": pk is not None,
    })

def fleet_contract_list(request):

    

    contracts = FleetContract.objects.all().order_by('-date')
    return render(request, 'contract_list.html', {'contracts': contracts})


@require_http_methods(["POST"])
def fleet_contract_delete(request, pk):

    CONTRACT_MENU_ID = 3

    # 🔐 CHECK DELETE PRIVILEGE
    has_permission = check_privilege(
        request.user,
        CONTRACT_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    try:
        contract = FleetContract.objects.get(pk=pk)
        num = contract.contract_no if hasattr(contract, "contract_no") else pk

        contract.delete()

        # ✅ DELETE LOG
        log_activity(
            user=request.user,
            screen_name="Fleet Contract",
            action_type="DELETE",
            remark=f"Contract {num} deleted"
        )

        return JsonResponse({
            "success": True,
            "message": f"Contract {num} deleted successfully"
        })

    except FleetContract.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Contract not found"
        }, status=404)



@login_required(login_url='accounts_app:admin_login')
def add_manufacturer_ajax(request):
    """AJAX view to add a new manufacturer from vehicle model form"""
    if request.method == 'POST':
        form = ManufacturerForm(request.POST, request.FILES)
        if form.is_valid():
            manufacturer = form.save()
            return JsonResponse({
                'success': True,
                'manufacturer_id': manufacturer.id,
                'manufacturer_name': manufacturer.manufacturer_name
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'success': False,
                'error': 'Please correct the errors in the form.',
                'errors': errors
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def add_vehicle_category_ajax(request):
    """AJAX view to add a new vehicle category from vehicle model form"""
    if request.method == 'POST':
        form = VehicleCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            return JsonResponse({
                'success': True,
                'category_id': category.id,
                'category_name': category.category_name
            })
        else:
            errors = form.errors.as_json()
            return JsonResponse({
                'success': False,
                'error': 'Please correct the errors in the form.',
                'errors': errors
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)




@login_required
def get_notifications(request):
    """
    Get all active notifications for document expiry and reminders
    PRODUCTION SAFE VERSION
    """

    try:
        # 🔐 Auth safety
        if not request.user.is_authenticated:
            return JsonResponse({
                "count": 0,
                "notifications": []
            })

        today = timezone.now().date()
        notifications = []

        # ----------------------------------
        # Helper: safe related_to text
        # ----------------------------------
        def safe_related_to(doc):
            try:
                if getattr(doc, "staff_id", None) and getattr(doc, "staff", None):
                    return f"Staff: {doc.staff.full_name or 'Unknown'}"

                if getattr(doc, "vehicle_id", None) and getattr(doc, "vehicle", None):
                    # handle both possible field names safely
                    plate = (
                        getattr(doc.vehicle, "registration_number", None)
                        or getattr(doc.vehicle, "license_plate_number", None)
                        or "Unknown"
                    )
                    return f"Vehicle: {plate}"

                return "N/A"
            except Exception:
                return "N/A"

        # ==================================
        # 🔹 DOCUMENT MODEL
        # ==================================
        documents = Document.objects.filter(status="active")

        for doc in documents:
            try:
                expiry_date = doc.expiry_date.date() if doc.expiry_date else None
                reminder_date = doc.reminder_date.date() if doc.reminder_date else None

                # 🔴 Expired documents
                if expiry_date and expiry_date <= today:
                    notifications.append({
                        "type": "expiry",
                        "model": "Document",
                        "title": doc.title or "Untitled Document",
                        "date": expiry_date.strftime("%Y-%m-%d"),
                        "days_overdue": max((today - expiry_date).days, 0),
                        "related_to": safe_related_to(doc),
                        "id": doc.id
                    })
                    continue

                # 🟡 Reminder documents
                if reminder_date and reminder_date <= today:
                    if not expiry_date or expiry_date > today:
                        days_until_expiry = (
                            (expiry_date - today).days
                            if expiry_date else None
                        )

                        notifications.append({
                            "type": "reminder",
                            "model": "Document",
                            "title": doc.title or "Untitled Document",
                            "date": reminder_date.strftime("%Y-%m-%d"),
                            "days_until_expiry": days_until_expiry,
                            "related_to": safe_related_to(doc),
                            "id": doc.id
                        })

            except Exception:
                # 🚨 Skip broken document instead of crashing
                continue

        # ==================================
        # 🔹 COMPANY DOCUMENT MODEL
        # ==================================
        company_documents = CompanyDocument.objects.all()

        for doc in company_documents:
            try:
                expiry_date = doc.expiry_date.date() if doc.expiry_date else None
                reminder_date = doc.reminder_date.date() if doc.reminder_date else None

                # 🔴 Expired
                if expiry_date and expiry_date <= today:
                    notifications.append({
                        "type": "expiry",
                        "model": "CompanyDocument",
                        "title": doc.name or "Company Document",
                        "date": expiry_date.strftime("%Y-%m-%d"),
                        "days_overdue": max((today - expiry_date).days, 0),
                        "related_to": f"Company: {doc.company.name if doc.company else 'Unknown'}",
                        "id": doc.id
                    })
                    continue

                # 🟡 Reminder
                if reminder_date and reminder_date <= today:
                    if not expiry_date or expiry_date > today:
                        days_until_expiry = (
                            (expiry_date - today).days
                            if expiry_date else None
                        )

                        notifications.append({
                            "type": "reminder",
                            "model": "CompanyDocument",
                            "title": doc.name or "Company Document",
                            "date": reminder_date.strftime("%Y-%m-%d"),
                            "days_until_expiry": days_until_expiry,
                            "related_to": f"Company: {doc.company.name if doc.company else 'Unknown'}",
                            "id": doc.id
                        })

            except Exception:
                # 🚨 Skip broken company document
                continue

        # ==================================
        # 🔹 SAFE SORTING
        # ==================================
        notifications.sort(
            key=lambda x: (
                x.get("type") != "expiry",
                x.get("date") or "9999-12-31"
            )
        )

        # ==================================
        # 🔹 RESPONSE
        # ==================================
        return JsonResponse({
            "count": len(notifications),
            "notifications": notifications,
            "debug": {
                "today": str(today),
                "total_documents": documents.count(),
                "notification_count": len(notifications),
            }
        })

    except Exception as e:
        # 🚨 Final safety net
        return JsonResponse({
            "error": str(e),
            "count": 0,
            "notifications": []
        }, status=500)


@login_required
def emi_list(request):
    """List all EMI plans with their installments"""
    emis = VehicleEMI.objects.all().prefetch_related('installments')
    
    # Get filter parameters
    title_filter = request.GET.get('title', '')
    vehicle_filter = request.GET.get('vehicle', '')
    status_filter = request.GET.get('status', '')
    
    # Apply filters
    if title_filter:
        emis = emis.filter(title=title_filter)
    
    if vehicle_filter:
        emis = emis.filter(vehicle_id=vehicle_filter)
    
    if status_filter:
        if status_filter == 'completed':
            # EMIs where all installments are paid
            emis = [emi for emi in emis if emi.pending_installments == 0]
        elif status_filter == 'pending':
            # EMIs with at least one pending installment
            emis = [emi for emi in emis if emi.pending_installments > 0]
        elif status_filter == 'active':
            emis = emis.filter(is_active=True)
    
    emis = list(emis) if isinstance(emis, list) else emis.order_by('-created_at')
    
    # Calculate progress for each EMI
    for emi in emis:
        total = emi.installments.count()
        paid = emi.installments.filter(is_paid=True).count()
        emi.progress = f"{paid}/{total}"
        emi.progress_percent = int((paid / total * 100)) if total > 0 else 0
    
    # Get unique titles and vehicles for filter dropdown
    unique_titles = VehicleEMI.objects.values_list('title', flat=True).distinct().order_by('title')
    from .models import Vehicle
    unique_vehicles = Vehicle.objects.filter(emis__isnull=False).distinct().order_by('vehicle_name')
    
    return render(request, 'emi_list.html', {
        'emis': emis,
        'unique_titles': unique_titles,
        'unique_vehicles': unique_vehicles,
    })


@login_required
def manage_emi(request, emi_id=None):
    """Create or edit EMI plan"""
    if emi_id:
        emi_instance = get_object_or_404(VehicleEMI, id=emi_id)
        action_title = "Edit EMI Plan"
    else:
        emi_instance = None
        action_title = "Create New EMI Plan"

    if request.method == 'POST':
        form = VehicleEMIForm(request.POST, instance=emi_instance)
        if form.is_valid():
            saved_emi = form.save()
            
            # If editing, update unpaid installment amounts
            if emi_id:
                EMIInstallment.objects.filter(
                    emi_plan=saved_emi, 
                    is_paid=False
                ).update(amount=saved_emi.amount)
                
                # ✅ AUDIT LOG — UPDATE
                log_activity(
                    user=request.user,
                    screen_name="Vehicle EMI",
                    action_type="UPDATE",
                    remark=(
                        f"EMI plan updated for vehicle "
                        f"{saved_emi.vehicle} | "
                        f"Amount {saved_emi.amount:.2f}, "
                        f"Installments {saved_emi.total_installments}"
                    )
        )
                
                messages.success(request, 'EMI plan updated successfully!')
            else:
                # ✅ AUDIT LOG — CREATE
                log_activity(
                    user=request.user,
                    screen_name="Vehicle EMI",
                    action_type="CREATE",
                    remark=(
                        f"EMI plan created for vehicle "
                        f"{saved_emi.vehicle} | "
                        f"Amount {saved_emi.amount:.2f}, "
                        f"Installments {saved_emi.total_installments}"
                    )
                )
                messages.success(request, f'EMI plan created with {saved_emi.total_installments} installments!')
            
            return redirect('fleet_app:emi_list')
    else:
        form = VehicleEMIForm(instance=emi_instance)

    return render(request, 'emi_form.html', {
        'form': form,
        'action_title': action_title,
        'emi_instance': emi_instance
    })


@login_required
def emi_detail(request, emi_id):
    """View all installments of a specific EMI plan"""
    emi = get_object_or_404(VehicleEMI, id=emi_id)
    installments = emi.installments.all()
    
    # Calculate summary
    total_installments = installments.count()
    paid_installments = installments.filter(is_paid=True).count()
    pending_installments = total_installments - paid_installments
    total_paid_amount = sum(i.amount for i in installments if i.is_paid)
    total_pending_amount = sum(i.amount for i in installments if not i.is_paid)
    
    context = {
        'emi': emi,
        'installments': installments,
        'total_installments': total_installments,
        'paid_installments': paid_installments,
        'pending_installments': pending_installments,
        'total_paid_amount': total_paid_amount,
        'total_pending_amount': total_pending_amount,
    }
    
    return render(request, 'emi_detail.html', context)


@login_required
def mark_installment_paid(request, installment_id):
    """Mark an EMI installment as paid"""
    installment = get_object_or_404(EMIInstallment, id=installment_id)
    
    if request.method == 'POST':
        installment.mark_as_paid()
        
        # ✅ AUDIT LOG — EMI INSTALLMENT PAID
        log_activity(
            user=request.user,
            screen_name="EMI Installment",
            action_type="UPDATE",
            remark=(
                f"EMI installment marked PAID | "
                f"Vehicle: {installment.emi_plan.vehicle} | "
                f"Due: {installment.due_date.strftime('%b %Y')} | "
                f"Amount: {installment.amount:.2f}"
            )
        )
        
        messages.success(request, f'EMI for {installment.due_date.strftime("%B %Y")} marked as paid!')
        
        # Check if AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Payment recorded successfully'
            })
        
        # Get the redirect URL from POST data or default to emi_list
        next_url = request.POST.get('next', 'fleet_app:emi_list')
        return redirect(next_url)
    
    return redirect('fleet_app:emi_list')


@login_required
def mark_installment_unpaid(request, installment_id):
    """Mark an EMI installment as unpaid (for corrections)"""
    installment = get_object_or_404(EMIInstallment, id=installment_id)
    
    if request.method == 'POST':
        installment.is_paid = False
        installment.paid_date = None
        installment.save()
        
        # ✅ AUDIT LOG — EMI INSTALLMENT UNPAID
        log_activity(
            user=request.user,
            screen_name="EMI Installment",
            action_type="UPDATE",
            remark=(
                f"EMI installment marked UNPAID | "
                f"Vehicle: {installment.emi_plan.vehicle} | "
                f"Due: {installment.due_date.strftime('%b %Y')} | "
                f"Amount: {installment.amount:.2f}"
            )
        )
        
        messages.success(request, f'EMI for {installment.due_date.strftime("%B %Y")} marked as unpaid!')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Payment status updated'
            })
        
        next_url = request.POST.get('next', 'fleet_app:emi_list')
        return redirect(next_url)
    
    return redirect('fleet_app:emi_list')


@login_required
def emi_notifications(request):
    """Get all EMI notifications as JSON for AJAX calls"""
    notifications = EMIInstallment.get_all_notifications()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'count': len(notifications),
            'notifications': [
                {
                    'id': n['installment'].id,
                    'message': n['message'],
                    'status': n['status'],
                    'due_date': n['installment'].due_date.strftime('%Y-%m-%d'),
                    'amount': str(n['installment'].amount),
                    'vehicle': str(n['installment'].emi_plan.vehicle),
                }
                for n in notifications
            ]
        }
        return JsonResponse(data)
    
    # Regular page view
    return render(request, 'emi_notifications.html', {
        'notifications': notifications
    })


@login_required
def delete_emi(request, emi_id):
    """Delete an EMI plan and all its installments"""
    emi = get_object_or_404(VehicleEMI, id=emi_id)
    
    if request.method == 'POST':
        title = emi.title
        vehicle = emi.vehicle
        amount = emi.amount
        installments = emi.total_installments
        emi.delete()
        
        # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL DELETE
        log_activity(
            user=request.user,
            screen_name="Vehicle EMI",
            action_type="DELETE",
            remark=(
                f"EMI plan deleted | "
                f"Vehicle: {vehicle} | "
                f"Title: {title} | "
                f"Amount: {amount:.2f} | "
                f"Installments: {installments}"
            )
        )
        
        messages.success(request, f'EMI plan "{title}" deleted successfully!')
        return redirect('fleet_app:emi_list')
    
    return render(request, 'emi_confirm_delete.html', {'emi': emi})


# ============= VEHICLE PROFIT & LOSS REPORT =============
def vehicle_profit_loss_report(request):
    """
    Display profit and loss report for all vehicles or a specific vehicle.
    Supports date range filtering.
    """
    vehicle_id = request.GET.get('vehicle_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Parse dates
    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get vehicles to report on
    if vehicle_id:
        vehicles = Vehicle.objects.filter(id=vehicle_id)
    else:
        vehicles = Vehicle.objects.all()
    
    # Build report data
    vehicle_reports = []
    for vehicle in vehicles:
        # Get entries
        entries = VehicleProfitLoss.objects.filter(Vehicle=vehicle)
        if start_date:
            entries = entries.filter(Date__gte=start_date)
        if end_date:
            entries = entries.filter(Date__lte=end_date)
        entries = entries.order_by('Date', 'id')
        
        # Calculate summary
        summary = get_vehicle_profit_loss_summary(vehicle, start_date, end_date)
        
        vehicle_reports.append({
            'vehicle': vehicle,
            'entries': entries,
            'summary': summary
        })
    
    all_vehicles = Vehicle.objects.all()
    
    context = {
        'vehicle_reports': vehicle_reports,
        'all_vehicles': all_vehicles,
        'selected_vehicle_id': vehicle_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'vehicle_profit_loss_report.html', context)



def vehicle_profit_loss_detail(request, vehicle_id):
    """
    Detailed view of a single vehicle's profit and loss.
    Shows all transactions and running balance.
    """
    vehicle = get_object_or_404(Vehicle, id=vehicle_id)
    
    # Get date filters from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Parse dates if provided
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    # Get all P&L entries for this vehicle
    entries = VehicleProfitLoss.objects.filter(Vehicle=vehicle)
    
    if start_date:
        entries = entries.filter(Date__gte=start_date)
    if end_date:
        entries = entries.filter(Date__lte=end_date)
    
    entries = entries.order_by('Date', 'id')
    
    # Get summary statistics
    summary = get_vehicle_profit_loss_summary(vehicle, start_date, end_date)
    
    # Separate income and expense entries for easier display
    income_entries = entries.filter(Amount__gt=0)
    expense_entries = entries.filter(Amount__lt=0)
    
    context = {
        'vehicle': vehicle,
        'all_entries': entries,
        'income_entries': income_entries,
        'expense_entries': expense_entries,
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'vehicle_profit_loss_detail.html', context)

DELIVERY_CONTRACT_MENU_ID = 12  # Update this based on your menu structure

def create_delivery_contract(request, contract_id=None):
    """
    Create or edit a Delivery Contract
    Similar to Invoice but without ledger posting
    """
    vehicles = Vehicle.objects.filter(status='1').order_by('vehicle_name')
    
    contract_instance = None
    existing_details = []
    
    if contract_id:
        contract_instance = get_object_or_404(DeliveryContract, id=contract_id)
        existing_details = DeliveryContractDetails.objects.filter(
            delivery_contract=contract_instance
        ).select_related('vehicle')
    
    if request.method == 'POST':
        action = "can_edit" if contract_id else "can_add"
        
        has_permission = check_privilege(
            request.user,
            DELIVERY_CONTRACT_MENU_ID,
            action
        )
        
        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)
        
        contract_form = DeliveryContractForm(request.POST, instance=contract_instance)
        
        if contract_form.is_valid():
            try:
                with transaction.atomic():
                    contract = contract_form.save(commit=False)
                    
                    grand_total = request.POST.get('grand_total')
                    contract.grand_total = float(grand_total) if grand_total else 0.0
                    
                    # Get contract type
                    contract_type = request.POST.get('invoice_type', 'simple')
                    contract.invoice_type = contract_type
                    
                    contract.save()
                    
                    details_data = request.POST.getlist('details[]')
                    
                    if not details_data:
                        if not contract_id:
                            contract.delete()
                        return JsonResponse({
                            "success": False,
                            "message": "Please add at least one contract detail."
                        }, status=400)
                    
                    # If editing, reset status of previously hired vehicles to 'Free'
                    if contract_id:
                        old_vehicles = Vehicle.objects.filter(
                            id__in=existing_details.values_list('vehicle_id', flat=True)
                        )
                        for old_vehicle in old_vehicles:
                            old_vehicle.status = '1'  # '1' = Free
                            old_vehicle.save()
                        
                        DeliveryContractDetails.objects.filter(delivery_contract=contract).delete()
                    
                    # Track vehicles to update status
                    vehicles_to_hire = []
                    
                    for detail_str in details_data:
                        # Parse detail string based on contract type
                        if contract_type == 'complex':
                            # Format: vehicle_id|location|period|quantity|unit_rate|tax|from_date|to_date|vehicle_model|description
                            parts = detail_str.split('|')
                            vehicle_id = parts[0]
                            location = parts[1]
                            period = parts[2]
                            quantity = float(parts[3])
                            unit_rate = float(parts[4])
                            tax = float(parts[5])
                            
                            # Handle optional dates
                            from_date = None
                            to_date = None
                            
                            if len(parts) > 6 and parts[6] and parts[6].strip():
                                try:
                                    from_date = parts[6]
                                except:
                                    from_date = None
                            
                            if len(parts) > 7 and parts[7] and parts[7].strip():
                                try:
                                    to_date = parts[7]
                                except:
                                    to_date = None
                            
                            vehicle_model_val = parts[8] if len(parts) > 8 else ''
                            description_val = parts[9] if len(parts) > 9 else ''
                            
                            # Calculate amount from quantity × unit_rate
                            amount = quantity * unit_rate
                            
                            vehicle = Vehicle.objects.get(id=vehicle_id)
                            vehicles_to_hire.append(vehicle)
                            
                            tax_amount = (amount * tax / 100)
                            total_amount = amount + tax_amount
                            
                            DeliveryContractDetails.objects.create(
                                delivery_contract=contract,
                                vehicle=vehicle,
                                vehicle_model=vehicle_model_val,
                                description=description_val,
                                location=location,
                                amount=amount,
                                tax=tax,
                                tax_amount=tax_amount,
                                total_amount=total_amount,
                                period=period,
                                quantity=quantity,
                                unit_rate=unit_rate,
                                from_date=from_date,
                                to_date=to_date,
                                IsCleared=False,  # Not invoiced yet
                            )
                        else:
                            # Simple contract format: vehicle_id|location|amount|tax|vehicle_model|description
                            parts = detail_str.split('|')
                            vehicle_id = parts[0]
                            location = parts[1]
                            amount = float(parts[2])
                            tax = float(parts[3])
                            vehicle_model_val = parts[4] if len(parts) > 4 else ''
                            description_val = parts[5] if len(parts) > 5 else ''
                            vehicle = Vehicle.objects.get(id=vehicle_id)
                            vehicles_to_hire.append(vehicle)
                            
                            tax_amount = (amount * tax / 100)
                            total_amount = amount + tax_amount
                            
                            DeliveryContractDetails.objects.create(
                                delivery_contract=contract,
                                vehicle=vehicle,
                                vehicle_model=vehicle_model_val,
                                description=description_val,
                                location=location,
                                amount=amount,
                                tax=tax,
                                tax_amount=tax_amount,
                                total_amount=total_amount,
                                IsCleared=False,  # Not invoiced yet
                            )
                    
                    # Update vehicle status to 'Hired' for all vehicles in this contract
                    for vehicle in vehicles_to_hire:
                        vehicle.status = '2'  # '2' = Hired
                        vehicle.save()
                    
                   
                    
                   
                    
                # ✅ AUDIT LOG
                log_activity(
                    user=request.user,
                    screen_name="Delivery Contract",
                    action_type="UPDATE" if contract_id else "CREATE",
                    remark=(
                        f"Delivery Contract {contract.invoice_no} updated "
                        f"with total {contract.grand_total:.3f}"
                        if contract_id else
                        f"Delivery Contract {contract.invoice_no} created "
                        f"with total {contract.grand_total:.3f}"
                    )
                )
                
                return JsonResponse({
                    "success": True,
                    "message": "Delivery Contract updated successfully!" if contract_id else "Delivery Contract created successfully!",
                    "pdf_url": reverse('fleet_app:delivery_contract_pdf', args=[contract.id]) 
                })
            except Exception as e:
                import traceback
                print(f"DELIVERY CONTRACT ERROR: {e}")
                print(traceback.format_exc())
                return JsonResponse({
                    "success": False,
                    "message": f"Error: {str(e)}"
                }, status=400)
        
        return JsonResponse({
            "success": False,
            "message": "Please correct the errors in the form.",
            "errors": contract_form.errors
        }, status=400)
    
    contract_form = DeliveryContractForm(instance=contract_instance)
    
    return render(request, 'create_delivery_contract.html', {
        'contract_form': contract_form,
        'vehicles': vehicles,
        'contract_instance': contract_instance,
        'existing_details': existing_details,
        'is_edit_mode': contract_id is not None,
    })

def delivery_contract_pdf(request, contract_id):
    """
    Generate PDF for a delivery contract
    """
    contract = get_object_or_404(DeliveryContract, id=contract_id)
    return create_delivery_contract_pdf(contract)    


def delivery_contract_pdf_without_header(request, pk):
    """
    Generate invoice PDF without header image
    Temporarily disables enable_header flag for this view only
    """
    contract = get_object_or_404(DeliveryContract, pk=pk)
    
    # Store original header setting
    original_header_setting = contract.enable_header
    
    # Temporarily disable header for this PDF generation
    contract.enable_header = False
     # Temporarily disable footer for this PDF generation
    contract.enable_footer = False
    # Generate PDF
    response = create_delivery_contract_pdf(contract)
    
    # Restore original setting (important: don't save to database)
    contract.enable_header = original_header_setting
    
    return response


def get_delivery_contract_details(request):
    """
    Fetch uncleared delivery contract details for a specific contract
    Used when creating an invoice from a delivery contract
    """
    contract_id = request.GET.get('contract_id')
    
    if not contract_id:
        return JsonResponse({
            'success': False,
            'message': 'Contract ID is required'
        }, status=400)
    
    try:
        # Get the specific contract
        contract = DeliveryContract.objects.get(id=contract_id)
        
        # Get all uncleared details for this contract
        contract_details = DeliveryContractDetails.objects.filter(
            delivery_contract=contract
            
        ).select_related('vehicle').order_by('created_on')
        
        details_list = []
        for detail in contract_details:
            details_list.append({
                'id': detail.id,
                'contract_no': contract.invoice_no,
                'vehicle_id': detail.vehicle.id,
                'vehicle_name': detail.vehicle.vehicle_name,
                'vehicle_model': detail.vehicle_model or '',
                'description': detail.description or '',
                'location': detail.location,
                'amount': str(detail.amount),
                'tax': str(detail.tax),
                'tax_amount': str(detail.tax_amount),
                'total_amount': str(detail.total_amount),
                'period': detail.period or '',
                'quantity': str(detail.quantity) if detail.quantity else '0',
                'unit_rate': str(detail.unit_rate) if detail.unit_rate else '0',
                'from_date': detail.from_date.strftime('%Y-%m-%d') if detail.from_date else '',
                'to_date': detail.to_date.strftime('%Y-%m-%d') if detail.to_date else '',
            })
        
        return JsonResponse({
            'success': True,
            'details': details_list,
            'contract_no':  contract.voucher_no,
            # ✅ NEW: Contract header fields to auto-fill Invoice
            'supplier_ref':    contract.supplier_ref or '',
            'hire_contract_no': contract.voucher_no or '',
            'location':        contract.location or '',
            'buyer_order_no':  contract.buyer_order_no or '',
            'other_ref':       contract.ref_no or '',
        })
    
    except DeliveryContract.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Delivery Contract not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
        
def get_customer_contracts(request):
    """
    Get all delivery contracts for a specific customer
    Returns contract list for dropdown
    """
    customer_id = request.GET.get('customer_id')
    
    if not customer_id:
        return JsonResponse({
            'success': False,
            'message': 'Customer ID is required'
        }, status=400)
    
    try:
        # Get all contracts for this customer (regardless of IsCleared status)
        contracts = DeliveryContract.objects.filter(
            customer_id=customer_id
        ).order_by('-date', '-created_on')
        
        contracts_list = []
        for contract in contracts:
            # Count uncleared details
            uncleared_count = DeliveryContractDetails.objects.filter(
                delivery_contract=contract,
                IsCleared=False
            ).count()
            
            total_count = DeliveryContractDetails.objects.filter(
                delivery_contract=contract
            ).count()
            
            contracts_list.append({
                'id': contract.id,
                'contract_no': contract.invoice_no or contract.voucher_no,
                'voucher_no': contract.voucher_no,
                'date': contract.date.strftime('%d-%m-%Y'),
                'hire_contract_no': contract.hire_contract_no or '',
                'uncleared_count': uncleared_count,
                'total_count': total_count,
            })
        
        return JsonResponse({
            'success': True,
            'contracts': contracts_list
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)        


def delivery_contract_list(request):
    """
    Simple list of all delivery contracts
    """
    # Check permission
    has_permission = check_privilege(request.user, 13, "can_read")
    
    if not has_permission:
        return render(request, 'no_permission.html')
    
    # Get all contracts ordered by date (newest first)
    contracts = DeliveryContract.objects.all().select_related(
        'customer', 'salesman'
    ).order_by('-date', '-created_on')
    
    context = {
        'contracts': contracts,
    }
    
    return render(request, 'delivery_contract_list.html', context)

def delete_delivery_contract(request, contract_id):
    """
    Delete a delivery contract (with permission check)
    """
    if request.method == 'POST':
        has_permission = check_privilege(request.user, 13, "can_delete")
        
        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)
        
        try:
            contract = get_object_or_404(DeliveryContract, id=contract_id)
            
            # Check if any details have been invoiced
            invoiced_details = DeliveryContractDetails.objects.filter(
                delivery_contract=contract,
                IsCleared=True
            ).count()
            
            if invoiced_details > 0:
                return JsonResponse({
                    "success": False,
                    "message": f"Cannot delete contract. {invoiced_details} detail(s) have already been invoiced."
                }, status=400)
            
            voucher_no = contract.voucher_no
            contract.delete()
            
            # Audit log
            log_activity(
                user=request.user,
                screen_name="Delivery Contract",
                action_type="DELETE",
                remark=f"Deleted Delivery Contract {voucher_no}"
            )
            
            return JsonResponse({
                "success": True,
                "message": "Delivery Contract deleted successfully!"
            })
        
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error: {str(e)}"
            }, status=400)
    
    return JsonResponse({
        "success": False,
        "message": "Invalid request method"
    }, status=405)

OFFHIRE_MENU_ID = 13  # Update this based on your menu structure


def create_offhire(request, offhire_id=None):
    """
    Create or edit an OffHire record
    """
    customers = LedgerCreation.objects.all().order_by('ledger_name')
    
    offhire_instance = None
    existing_details = []
    
    if offhire_id:
        offhire_instance = get_object_or_404(OffHire, id=offhire_id)
        existing_details = OffHireDetails.objects.filter(
            offhire=offhire_instance
        ).select_related('vehicle', 'delivery_contract_detail')
    
    if request.method == 'POST':
        action = "can_edit" if offhire_id else "can_add"
        
        has_permission = check_privilege(
            request.user,
            OFFHIRE_MENU_ID,
            action
        )
        
        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)
        
        offhire_form = OffHireForm(request.POST, instance=offhire_instance)
        
        if offhire_form.is_valid():
            try:
                with transaction.atomic():
                    offhire = offhire_form.save(commit=False)
                    offhire.save()
                    
                    details_data = request.POST.getlist('details[]')
                    
                    if not details_data:
                        if not offhire_id:
                            offhire.delete()
                        return JsonResponse({
                            "success": False,
                            "message": "Please add at least one offhire detail."
                        }, status=400)
                    
                    # If editing, reset status of previously offhired vehicles back to 'Hired'
                    if offhire_id:
                        old_vehicles = Vehicle.objects.filter(
                            id__in=existing_details.values_list('vehicle_id', flat=True)
                        )
                        for old_vehicle in old_vehicles:
                            old_vehicle.status = '2'  # '2' = Hired (revert back)
                            old_vehicle.save()
                        
                        OffHireDetails.objects.filter(offhire=offhire).delete()
                    
                    # Track vehicles to update status to 'Free'
                    vehicles_to_free = []
                    
                    for detail_str in details_data:
                        # Format: contract_detail_id|vehicle_id|location|period|quantity|unit_rate|from_date|to_date|amount|tax|meter_reading|fuel_level|vehicle_condition|remarks|offhire_datetime
                        parts = detail_str.split('|')
                        
                        contract_detail_id = parts[0]
                        vehicle_id = parts[1]
                        location = parts[2]
                        period = parts[3]
                        quantity = float(parts[4]) if parts[4] else 0
                        unit_rate = float(parts[5]) if parts[5] else 0
                        from_date = parts[6] if parts[6] else None
                        to_date = parts[7] if parts[7] else None
                        amount = float(parts[8])
                        tax = float(parts[9])
                        meter_reading = float(parts[10]) if parts[10] else None
                        fuel_level = parts[11] if parts[11] else ''
                        vehicle_condition = parts[12] if parts[12] else ''
                        remarks = parts[13] if parts[13] else ''
                        offhire_datetime = parts[14] if parts[14] else None
                        
                        vehicle = Vehicle.objects.get(id=vehicle_id)
                        vehicles_to_free.append(vehicle)
                        
                        contract_detail = DeliveryContractDetails.objects.get(id=contract_detail_id)
                        
                        tax_amount = (amount * tax / 100)
                        total_amount = amount + tax_amount
                        
                        OffHireDetails.objects.create(
                            offhire=offhire,
                            delivery_contract_detail=contract_detail,
                            vehicle=vehicle,
                            location=location,
                            amount=amount,
                            tax=tax,
                            tax_amount=tax_amount,
                            total_amount=total_amount,
                            period=period,
                            quantity=quantity,
                            unit_rate=unit_rate,
                            from_date=from_date,
                            to_date=to_date,
                            meter_reading=meter_reading,
                            fuel_level=fuel_level,
                            vehicle_condition=vehicle_condition,
                            remarks=remarks,
                            offhire_date_time=offhire_datetime if offhire_datetime else offhire.offhire_date_time,
                        )
                    
                    # Update vehicle status to 'Free' for all offhired vehicles
                    for vehicle in vehicles_to_free:
                        vehicle.status = '1'  # '1' = Free
                        vehicle.save()
                    
                # ✅ AUDIT LOG
                log_activity(
                    user=request.user,
                    screen_name="OffHire",
                    action_type="UPDATE" if offhire_id else "CREATE",
                    remark=(
                        f"OffHire {offhire.voucher_no} updated for contract {offhire.delivery_contract.voucher_no}"
                        if offhire_id else
                        f"OffHire {offhire.voucher_no} created for contract {offhire.delivery_contract.voucher_no}"
                    )
                )
                
                return JsonResponse({
                    "success": True,
                    "message": "OffHire updated successfully!" if offhire_id else "OffHire created successfully!",
                    # "pdf_url": reverse('fleet_app:offhire_pdf', args=[offhire.id])  # Add if you have PDF generation
                })
            
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": f"Error: {str(e)}"
                }, status=400)
        
        return JsonResponse({
            "success": False,
            "message": "Please correct the errors in the form.",
            "errors": offhire_form.errors
        }, status=400)
    
    offhire_form = OffHireForm(instance=offhire_instance)
    
    return render(request, 'create_offhire.html', {
        'offhire_form': offhire_form,
        'customers': customers,
        'offhire_instance': offhire_instance,
        'existing_details': existing_details,
        'is_edit_mode': offhire_id is not None,
    })

def get_customer_delivery_contracts_offhire(request):
    """
    AJAX endpoint to get delivery contracts for a customer
    Returns only contracts with hired vehicles
    """
    customer_id = request.GET.get('customer_id')
    
    if not customer_id:
        return JsonResponse({
            'success': False,
            'message': 'Customer ID is required'
        }, status=400)
    
    try:
        # Get delivery contracts for this customer that have hired vehicles
        contracts = DeliveryContract.objects.filter(
            customer_id=customer_id
        ).prefetch_related('details__vehicle')
        
        # Filter to only include contracts with at least one hired vehicle
        contract_list = []
        for contract in contracts:
            hired_count = contract.details.filter(vehicle__status='2').count()
            if hired_count > 0:
                contract_list.append({
                    'id': contract.id,
                    'voucher_no': contract.voucher_no,
                    'invoice_no': contract.invoice_no or '',
                    'date': contract.date.strftime('%Y-%m-%d'),
                    'hired_vehicles': hired_count,
                })
        
        return JsonResponse({
            'success': True,
            'contracts': contract_list
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)

def get_delivery_contract_details_offhire(request):
    """
    AJAX endpoint to get delivery contract details for offhire
    Returns only vehicles with status 'Hired'
    """
    contract_id = request.GET.get('contract_id')
    
    if not contract_id:
        return JsonResponse({
            'success': False,
            'message': 'Contract ID is required'
        }, status=400)
    
    try:
        contract = DeliveryContract.objects.get(id=contract_id)
        
        # Get only details with hired vehicles (status='2')
        details = DeliveryContractDetails.objects.filter(
            delivery_contract=contract,
            vehicle__status='2'  # Only hired vehicles
        ).select_related('vehicle')
        
        details_list = []
        for detail in details:
            details_list.append({
                'id': detail.id,
                'vehicle_id': detail.vehicle.id,
                'vehicle_name': detail.vehicle.vehicle_name,
                'location': detail.location,
                'amount': str(detail.amount),
                'tax': str(detail.tax),
                'tax_amount': str(detail.tax_amount),
                'total_amount': str(detail.total_amount),
                'period': detail.period or '',
                'quantity': str(detail.quantity) if detail.quantity else '',
                'unit_rate': str(detail.unit_rate) if detail.unit_rate else '',
                'from_date': detail.from_date.strftime('%Y-%m-%d') if detail.from_date else '',
                'to_date': detail.to_date.strftime('%Y-%m-%d') if detail.to_date else '',
            })
        
        return JsonResponse({
            'success': True,
            'details': details_list,
            'customer_id': contract.customer.id if contract.customer else None,
            'customer_name': contract.customer.ledger_name if contract.customer else '',
        })
    
    except DeliveryContract.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Delivery contract not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


def offhire_list(request):
    """
    List all offhire records
    """
    offhires = OffHire.objects.all().select_related(
        'delivery_contract', 'customer'
    ).order_by('-date', '-created_on')
    
    return render(request, 'offhire_list.html', {
        'offhires': offhires,
    })

def delete_offhire(request, offhire_id):
    """
    Delete an offhire record (with permission check)
    When deleting, restore vehicle status back to 'Hired'
    """
    if request.method == 'POST':
        has_permission = check_privilege(request.user, OFFHIRE_MENU_ID, "can_delete")
        
        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)
        
        try:
            with transaction.atomic():
                offhire = get_object_or_404(OffHire, id=offhire_id)
                
                # Get all offhire details to restore vehicle status
                offhire_details = OffHireDetails.objects.filter(offhire=offhire).select_related('vehicle')
                
                # Restore vehicle status back to 'Hired' (since they were offhired)
                for detail in offhire_details:
                    vehicle = detail.vehicle
                    vehicle.status = '2'  # '2' = Hired (restore to hired status)
                    vehicle.save()
                
                voucher_no = offhire.voucher_no
                contract_no = offhire.delivery_contract.voucher_no
                
                # Delete the offhire record (details will cascade delete)
                offhire.delete()
                
                # Audit log
                log_activity(
                    user=request.user,
                    screen_name="OffHire",
                    action_type="DELETE",
                    remark=f"Deleted OffHire {voucher_no} for contract {contract_no}. Restored {offhire_details.count()} vehicle(s) to Hired status."
                )
                
                return JsonResponse({
                    "success": True,
                    "message": f"OffHire deleted successfully! {offhire_details.count()} vehicle(s) restored to Hired status."
                })
        
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error: {str(e)}"
            }, status=400)
    
    return JsonResponse({
        "success": False,
        "message": "Invalid request method"
    }, status=405)    




def asset_report(request):
    # Get date filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    today = timezone.now().date()
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    if not start_date and not end_date:
        start_date = today.replace(day=1)
        end_date = today
    
    # ========== VEHICLE COUNTS ==========
    all_vehicles = Vehicle.objects.all()
    
    total_assets = all_vehicles.count()
    on_rent     = all_vehicles.filter(status='2').count()
    available   = all_vehicles.filter(status='1').count()
    in_service  = all_vehicles.filter(status='3').count()
    
    # ========== ACTIVE CONTRACT LOOKUP ==========
    # For every vehicle currently on rent, grab the latest uncleared contract detail
    # so we can show its location and customer.
    active_details = (
        DeliveryContractDetails.objects
        .filter(IsCleared=False, delivery_contract__IsCleared=False)
        .select_related('vehicle', 'delivery_contract', 'delivery_contract__customer')
        .order_by('vehicle_id', '-delivery_contract__date')   # latest contract first
    )

    # Build a dict: vehicle_id → (location, customer_name)
    vehicle_contract_map = {}
    for d in active_details:
        vid = d.vehicle_id
        if vid not in vehicle_contract_map:          # keep only the latest
            customer = d.delivery_contract.customer
            vehicle_contract_map[vid] = {
                'location': d.location or d.delivery_contract.location or '',
                'client':   str(customer) if customer else '',
            }
    
    # ========== FINANCIAL CALCULATIONS & VEHICLE DETAILS ==========
    total_income   = Decimal('0')
    total_expense  = Decimal('0')
    vehicle_details = []
    
    for vehicle in all_vehicles:
        summary = get_vehicle_profit_loss_summary(vehicle, start_date, end_date)
        total_income  += summary['income']
        total_expense += summary['expense']
        
        vehicle_profit = summary['income'] - summary['expense']
        vehicle_margin = (vehicle_profit / summary['income'] * 100) if summary['income'] > 0 else 0

        # Location / Client logic
        if vehicle.status == '2' and vehicle.id in vehicle_contract_map:
            location = vehicle_contract_map[vehicle.id]['location']
            client   = vehicle_contract_map[vehicle.id]['client']
        elif vehicle.status == '1':
            location = 'Own Yard'
            client   = ''
        else:
            location = ''
            client   = ''
        
        vehicle_details.append({
            'vehicle':       vehicle,
            'on_rent':       vehicle.status == '2',
            'available':     vehicle.status == '1',
            'location':      location,
            'client':        client,
            'income':        summary['income'],
            'expense':       summary['expense'],
            'profit':        vehicle_profit,
            'profit_margin': vehicle_margin,
        })
    
    net_profit     = total_income - total_expense
    profit_margin  = (net_profit / total_income * 100) if total_income > 0 else 0
    
    context = {
        'total_assets':  total_assets,
        'on_rent':       on_rent,
        'available':     available,
        'in_service':    in_service,
        'total_income':  total_income,
        'total_expense': total_expense,
        'net_profit':    net_profit,
        'profit_margin': profit_margin,
        'vehicle_details': vehicle_details,
        'start_date':    start_date,
        'end_date':      end_date,
    }
    
    return render(request, 'asset_report.html', context)

def trial_balance_report(request):
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')

    today = timezone.now().date()

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None

    if not start_date and not end_date:
        start_date = today.replace(day=1)
        end_date   = today

    qs = LedgerPosting.objects.filter(date__range=(start_date, end_date))

    aggregated = (
        qs
        .values('ledger__id', 'ledger__ledger_name')
        .annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
        )
        .order_by('ledger__ledger_name')
    )

    ledger_rows  = []
    total_debit  = Decimal('0')
    total_credit = Decimal('0')

    for row in aggregated:
        gross_debit  = row['total_debit']  or Decimal('0')
        gross_credit = row['total_credit'] or Decimal('0')

        # ── NET BALANCE LOGIC ──────────────────────────────────────────
        # Only show the net amount on one side, not both raw totals.
        #   Debit > Credit  →  net shown in Debit  column, Credit blank
        #   Credit > Debit  →  net shown in Credit column, Debit  blank
        #   Equal           →  both blank (zero-balance, skip row)
        net = gross_debit - gross_credit

        if net > Decimal('0'):
            # Net debit balance
            display_debit  = net
            display_credit = None
            total_debit   += net
        elif net < Decimal('0'):
            # Net credit balance
            display_debit  = None
            display_credit = abs(net)
            total_credit  += abs(net)
        else:
            # Perfectly balanced — skip this ledger (nothing to show)
            continue

        ledger_rows.append({
            'ledger_id':   row['ledger__id'],
            'ledger_name': row['ledger__ledger_name'],
            'debit':       display_debit,   # None or positive Decimal
            'credit':      display_credit,  # None or positive Decimal
        })

    context = {
        'ledger_rows':  ledger_rows,
        'total_debit':  total_debit,
        'total_credit': total_credit,
        'start_date':   start_date,
        'end_date':     end_date,
    }
    return render(request, 'trial_balance_report.html', context)


def trial_balance_postings_ajax(request):
    """
    Returns raw individual posting lines for a ledger (drill-down).
    These are intentionally NOT netted — the user sees every transaction.
    """
    ledger_id  = request.GET.get('ledger_id')
    start_date = request.GET.get('start_date')
    end_date   = request.GET.get('end_date')

    if not ledger_id:
        return JsonResponse({'postings': [], 'error': 'No ledger_id provided'})

    today = timezone.now().date()

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None

    if not start_date:
        start_date = today.replace(day=1)
    if not end_date:
        end_date = today

    postings = (
        LedgerPosting.objects
        .filter(ledger_id=ledger_id, date__range=(start_date, end_date))
        .select_related('ledger')
        .order_by('date', 'id')
    )

    rows = []
    for p in postings:
        rows.append({
            'date':        str(p.date),
            'ledger_name': p.ledger.ledger_name,
            'debit':       str(p.debit  or '0'),
            'credit':      str(p.credit or '0'),
        })

    return JsonResponse({'postings': rows})


def get_ledgers_by_group(request):
    group_id = request.GET.get("group_id")

    if not group_id:
        return JsonResponse({"ledgers": []})

    try:
        group_id = int(group_id)
        ledgers  = get_ledgers_by_group_ids(group_id)
        data     = [{"id": l.id, "name": l.ledger_name} for l in ledgers]
        return JsonResponse({"ledgers": data})
    except ValueError:
        return JsonResponse({"ledgers": []})
        
# Balance Sheet
# ── Fixed sections in display order ───────────────────────────────────────────
# side: 'asset' or 'liability' — determines which column the amount appears in
CAPITAL_SECTION_NAME      = 'Capital Accounts'

SECTIONS = [
    {'name': 'Capital Accounts',             'group_id': 7,  'side': 'liability'},
    {'name': 'Current Assets',               'group_id': 9,  'side': 'asset'},
    {'name': 'Fixed Assets',                 'group_id': 15, 'side': 'asset'},
    {'name': 'Investments',                  'group_id': 18, 'side': 'asset'},
    {'name': 'Loans & Advances (Asset)',     'group_id': 19, 'side': 'asset'},
    {'name': 'Suspense Account (Asset)',     'group_id': 30, 'side': 'asset'},
    {'name': 'Current Liabilities',          'group_id': 10, 'side': 'liability'},
    {'name': 'Loans & Liability',            'group_id': 20, 'side': 'liability'},
    {'name': 'Suspense Account (Liability)', 'group_id': 31, 'side': 'liability'},
    {'name': 'Long Term Deposits',           'group_id': 38, 'side': 'liability'},
]


def _display_balance(net, is_asset, led_type):
    """
    Determine the display value for a ledger inside a balance-sheet section.

    Asset sections        → always positive (abs)
    Liability CR ledger   → positive  (increases the liability)
    Liability DR ledger   → negative  (reduces  the liability, e.g. drawings/payments)
    """
    if is_asset:
        return abs(net)
    if led_type == 'DR':
        return -abs(net)
    return net


def _build_bs_sections(ledger_balance):
    """
    Build all balance-sheet sections using the shared ledger_balance dict.
    Returns a list of section dicts ready for the template.
    """
    result = []

    for sec in SECTIONS:
        section_total = Decimal('0')
        groups_data   = []
        is_asset      = (sec['side'] == 'asset')

        try:
            parent_group = Groups.objects.get(pk=sec['group_id'])
        except Groups.DoesNotExist:
            continue

        # Direct ledgers under the parent group
        direct_ledgers = []
        for led in LedgerCreation.objects.filter(groups=parent_group).order_by('ledger_name'):
            net = calc_balance(led, ledger_balance)
            if net != Decimal('0'):
                display_bal = _display_balance(net, is_asset, led.types)
                direct_ledgers.append({'ledger': led, 'balance': display_bal})
                section_total += display_bal

        # Child groups
        for grp in Groups.objects.filter(groupId=parent_group).order_by('groupName'):
            grp_total = Decimal('0')
            ledgers   = []
            for led in LedgerCreation.objects.filter(groups=grp).order_by('ledger_name'):
                net = calc_balance(led, ledger_balance)
                if net != Decimal('0'):
                    display_bal = _display_balance(net, is_asset, led.types)
                    ledgers.append({'ledger': led, 'balance': display_bal})
                    grp_total += display_bal
            if grp_total != Decimal('0'):
                groups_data.append({
                    'group':   grp,
                    'ledgers': ledgers,
                    'total':   grp_total,
                })
                section_total += grp_total

        if section_total != Decimal('0') or sec['name'] == CAPITAL_SECTION_NAME:
            result.append({
                'name':              sec['name'],
                'side':              sec['side'],
                'direct_ledgers':    direct_ledgers,
                'groups':            groups_data,
                'total':             section_total,
                # P&L injection fields (populated below for Capital section only)
                'has_pl':            False,
                'pl_label':          '',
                'pl_amount':         Decimal('0'),
                'pl_is_profit':      False,
                'pl_amount_abs':     Decimal('0'),
                'capital_before_pl': section_total,
            })

    return result


def balance_sheet(request):
    today = date.today()

    default_from = today.replace(month=1,  day=1).isoformat()
    default_to   = today.replace(month=12, day=31).isoformat()

    from_date = request.GET.get('from_date', default_from)
    to_date   = request.GET.get('to_date',   default_to)

    try:
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj   = datetime.strptime(to_date,   '%Y-%m-%d').date()
    except (ValueError, TypeError):
        from_date_obj = today.replace(month=1,  day=1)
        to_date_obj   = today.replace(month=12, day=31)

    # ── ONE shared DB query covers all ledger movements ───────────────────────
    ledger_balance = get_ledger_balances(from_date_obj, to_date_obj)

    # ── Build all balance-sheet sections ──────────────────────────────────────
    sections = _build_bs_sections(ledger_balance)

    # ── P&L figures using shared build_group_total() ─────────────────────────
    purchase_total         = build_group_total(PURCHASE_GROUP_ID,         ledger_balance)
    sales_total            = build_group_total(SALES_GROUP_ID,            ledger_balance)
    indirect_expense_total = build_group_total(INDIRECT_EXPENSE_GROUP_ID, ledger_balance)
    indirect_income_total  = build_group_total(INDIRECT_INCOME_GROUP_ID,  ledger_balance)

    gross_profit = sales_total - abs(purchase_total)
    net_profit   = gross_profit + indirect_income_total - abs(indirect_expense_total)

    # ── Inject P&L into Capital Accounts ─────────────────────────────────────
    for section in sections:
        if section['name'] == CAPITAL_SECTION_NAME:
            capital_before               = section['total']
            is_profit                    = net_profit >= Decimal('0')
            section['has_pl']            = True
            section['pl_is_profit']      = is_profit
            section['pl_label']          = 'Add: Net Profit (P&L)' if is_profit else 'Less: Net Loss (P&L)'
            section['pl_amount']         = net_profit
            section['pl_amount_abs']     = abs(net_profit)
            section['capital_before_pl'] = capital_before
            section['total']             = capital_before + net_profit
            break

    total_liabilities = sum(s['total'] for s in sections if s['side'] == 'liability')
    total_assets      = sum(s['total'] for s in sections if s['side'] == 'asset')
    difference        = total_assets - total_liabilities

    context = {
        'sections':          sections,
        'total_liabilities': total_liabilities,
        'total_assets':      total_assets,
        'difference':        difference,
        'abs_difference':    abs(difference),
        'from_date':         from_date_obj,
        'to_date':           to_date_obj,
    }
    return render(request, 'balance_sheet.html', context)



# Profit and Loss 
PURCHASE_GROUP_ID         = 23
SALES_GROUP_ID            = 25
INDIRECT_EXPENSE_GROUP_ID = 16
INDIRECT_INCOME_GROUP_ID  = 17
SUNDRY_CREDIT_GROUP_ID    = 28


def profit_and_loss(request):
    today     = date.today()
    from_date = request.GET.get('from_date', today.replace(month=1, day=1).isoformat())
    to_date   = request.GET.get('to_date',   today.isoformat())

    try:
        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
        to_date_obj   = datetime.strptime(to_date,   '%Y-%m-%d').date()
    except (ValueError, TypeError):
        from_date_obj = today.replace(month=1, day=1)
        to_date_obj   = today

    # ── ONE shared DB query covers all ledger movements ───────────────────────
    ledger_balance = get_ledger_balances(from_date_obj, to_date_obj)

    # ── Build group data using shared build_group_data() ─────────────────────
    sundry_credit    = build_group_data(SUNDRY_CREDIT_GROUP_ID,    ledger_balance)
    purchase         = build_group_data(PURCHASE_GROUP_ID,         ledger_balance)
    sales            = build_group_data(SALES_GROUP_ID,            ledger_balance)
    indirect_expense = build_group_data(INDIRECT_EXPENSE_GROUP_ID, ledger_balance)
    indirect_income  = build_group_data(INDIRECT_INCOME_GROUP_ID,  ledger_balance)

    # ── Raw signed totals (before normalization) for financial calculations ───
    purchase_total         = purchase['total']         if purchase         else Decimal('0')
    sales_total            = sales['total']            if sales            else Decimal('0')
    indirect_expense_total = indirect_expense['total'] if indirect_expense else Decimal('0')
    indirect_income_total  = indirect_income['total']  if indirect_income  else Decimal('0')

    # ── Gross Profit / Loss ───────────────────────────────────────────────────
    # abs(purchase_total): handles CR-typed Purchase ledgers returning negative
    # balances — without abs(), 0 - (-150) = +150 shows as Profit not Loss.
    gross_profit        = sales_total - abs(purchase_total)
    gross_section_total = max(abs(purchase_total), abs(sales_total))

    # ── Net Profit / Loss ─────────────────────────────────────────────────────
    net_profit = gross_profit + indirect_income_total - abs(indirect_expense_total)
    gp_bf      = abs(gross_profit)   # b/f figure carried into Section 2

    # ── Section 2 balancing totals ────────────────────────────────────────────
    indirect_debit_total   = abs(indirect_expense_total) + (gp_bf if gross_profit < 0  else Decimal('0'))
    indirect_credit_total  = indirect_income_total        + (gp_bf if gross_profit >= 0 else Decimal('0'))
    indirect_section_total = max(indirect_debit_total, indirect_credit_total)

    # ── Normalize expense groups for display AFTER all maths ─────────────────
    # Ensures ledger rows + group totals always show as positive on screen.
    normalize_for_display(purchase)
    normalize_for_display(indirect_expense)

    context = {
        'from_date':              from_date_obj,
        'to_date':                to_date_obj,
        # Group data
        'sundry_credit':          sundry_credit,
        'purchase':               purchase,
        'sales':                  sales,
        'indirect_expense':       indirect_expense,
        'indirect_income':        indirect_income,
        # Totals (post-normalize for purchase/indirect_expense)
        'purchase_total':         purchase['total']         if purchase         else Decimal('0'),
        'sales_total':            sales_total,
        'indirect_expense_total': indirect_expense['total'] if indirect_expense else Decimal('0'),
        'indirect_income_total':  indirect_income_total,
        # Signed profit values (+ve = profit, -ve = loss)
        'gross_profit':           gross_profit,
        'net_profit':             net_profit,
        # Absolute values for display (always positive)
        'gp_bf':                  gp_bf,
        'net_profit_abs':         abs(net_profit),
        # Section balancing totals
        'gross_section_total':    gross_section_total,
        'indirect_section_total': indirect_section_total,
    }
    return render(request, 'profit_loss.html', context)


# ─────────────────────────────────────────────
# HELPER – read array PODetails from POST
# ─────────────────────────────────────────────
def _get_detail_rows(post):
    """
    Reads parallel arrays from POST.
    Template uses name="details-description[]" etc.
    Django QueryDict.getlist() handles the [] key literally.
    """
    descriptions = post.getlist('details-description[]')
    units_list   = post.getlist('details-units[]')
    quantities   = post.getlist('details-quantity[]')
    rates        = post.getlist('details-rate[]')
    amounts      = post.getlist('details-amount[]')

    # Debug: log what was received (remove after confirming it works)
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"PO POST keys: {list(post.keys())}")
    logger.debug(f"descriptions: {descriptions}")

    rows = []
    for i, desc in enumerate(descriptions):
        desc = desc.strip()
        if not desc:
            continue
        try:
            qty  = Decimal(quantities[i]) if i < len(quantities) else Decimal('0')
            rate = Decimal(rates[i])      if i < len(rates)      else Decimal('0')
            amt  = Decimal(amounts[i])    if i < len(amounts)    else (qty * rate)
            unit = units_list[i]          if i < len(units_list) else ''
        except (InvalidOperation, IndexError):
            continue
        rows.append({
            'description': desc,
            'units':       unit,
            'quantity':    qty,
            'rate':        rate,
            'amount':      amt,
        })
    return rows


# ─────────────────────────────────────────────
# HELPER – recalculate and save totals
# ─────────────────────────────────────────────
def _save_totals(po):
    taxable = sum(d.amount for d in po.po_details.all())
    vat     = (taxable * Decimal('0.05')).quantize(Decimal('0.001'))
    grand   = taxable + vat
    POMaster.objects.filter(pk=po.pk).update(
        taxable_amount=taxable,
        vat_amount=vat,
        grand_total=grand,
    )
    po.refresh_from_db()


# ─────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────
def po_list(request):
    query = request.GET.get('q', '').strip()
    pos   = POMaster.objects.select_related('supplier').order_by('-PO_date', '-id')
    if query:
        pos = pos.filter(
            Q(PO_no__icontains=query) |
            Q(supplier__ledger_name__icontains=query) |
            Q(quote_ref__icontains=query)
        )
    return render(request, 'po_list.html', {'pos': pos, 'query': query})


# ─────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────
def po_create(request):
    if request.method == 'POST':
        form = POMasterForm(request.POST)
        if form.is_valid():
            detail_rows = _get_detail_rows(request.POST)
            if not detail_rows:
                messages.error(request, 'Please add at least one line item.')
            else:
                try:
                    with transaction.atomic():
                        po = form.save()
                        for row in detail_rows:
                            PODetails.objects.create(po_master=po, **row)
                        _save_totals(po)
                    return create_po_pdf(po)
                except Exception as e:
                    messages.error(request, f'Error saving Purchase Order: {e}')
        else:
            messages.error(request, 'Please fix the form errors.')
    else:
        form = POMasterForm()

    return render(request, 'po_form.html', {
        'form':   form,
        'title':  'New Purchase Order',
        'action': 'Create',
    })


# ─────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────
def po_edit(request, pk):
    po = get_object_or_404(POMaster, pk=pk)

    if request.method == 'POST':
        form = POMasterForm(request.POST, instance=po)
        if form.is_valid():
            detail_rows = _get_detail_rows(request.POST)
            if not detail_rows:
                messages.error(request, 'Please add at least one line item.')
            else:
                try:
                    with transaction.atomic():
                        po = form.save()
                        po.po_details.all().delete()
                        for row in detail_rows:
                            PODetails.objects.create(po_master=po, **row)
                        _save_totals(po)
                    return create_po_pdf(po)
                except Exception as e:
                    messages.error(request, f'Error updating Purchase Order: {e}')
        else:
            messages.error(request, 'Please fix the form errors.')
    else:
        form = POMasterForm(instance=po)

    return render(request, 'po_form.html', {
        'form':             form,
        'po':               po,
        'existing_details': po.po_details.all(),
        'title':            f'Edit PO – {po.PO_no}',
        'action':           'Update',
    })


# ─────────────────────────────────────────────
# DELETE  (POST only, no separate page)
# ─────────────────────────────────────────────
def po_delete(request, pk):
    if request.method == 'POST':
        po = get_object_or_404(POMaster, pk=pk)
        po_no = po.PO_no
        po.delete()
        messages.success(request, f'Purchase Order <strong>{po_no}</strong> deleted.')
    return redirect('fleet_app:po_list')


# ─────────────────────────────────────────────
# PDF re-print
# ─────────────────────────────────────────────
def po_pdf(request, pk):
    po = get_object_or_404(POMaster.objects.select_related('supplier'), pk=pk)
    return create_po_pdf(po)



'''
def vehicle_master_list(request):
    vehicles  = VehicleMaster.objects.select_related('customer').all()
    customers = FleetCustomer.objects.all()
    selected_customer = request.GET.get('customer_id')

    if selected_customer:
        vehicles = vehicles.filter(customer_id=selected_customer)

    return render(request, 'fleet_app/vehicle_master_list.html', {
        'vehicles':         vehicles,
        'customers':        customers,
        'selected_customer': selected_customer,
    })


def vehicle_master_create(request):
    customers   = FleetCustomer.objects.all()
    categories  = VehicleCategory.objects.all()
    plate_codes = LicensePlateCode.objects.all()

    if request.method == 'POST':
        customer_id          = request.POST.get('customer')
        vehicle_name         = request.POST.get('vehicle_name')
        license_plate_code   = request.POST.get('license_plate_code')
        license_plate_number = request.POST.get('license_plate_number')
        vehicle_driver       = request.POST.get('vehicle_driver', '')
        vehicle_category     = request.POST.get('vehicle_category', '')
        RC_number            = request.POST.get('RC_number', '')
        contract_no          = request.POST.get('contract_no', '')
        contract_start_date  = request.POST.get('contract_start_date', '')
        contract_end_date    = request.POST.get('contract_end_date', '')

        customer = get_object_or_404(FleetCustomer, id=customer_id)

        vehicle = VehicleMaster(
            customer             = customer,
            vehicle_name         = vehicle_name,
            license_plate_code   = license_plate_code,
            license_plate_number = license_plate_number,
            vehicle_driver       = vehicle_driver,
            vehicle_category     = vehicle_category,
            RC_number            = RC_number,
            contract_no          = contract_no,
            contract_start_date  = contract_start_date,
            contract_end_date    = contract_end_date,
            customer_name        = customer.customer_name,
        )

        if request.FILES.get('vehicle_image'):
            vehicle.vehicle_image = request.FILES['vehicle_image']

        vehicle.save()
        messages.success(request, f"Vehicle '{vehicle_name}' created for {customer.customer_name}!")
        return redirect('fleet_app:vehicle_master_list')

    return render(request, 'fleet_app/vehicle_master_form.html', {
        'customers':   customers,
        'categories':  categories,
        'plate_codes': plate_codes,
    })


def vehicle_master_edit(request, pk):
    vehicle     = get_object_or_404(VehicleMaster, pk=pk)
    customers   = FleetCustomer.objects.all()
    categories  = VehicleCategory.objects.all()
    plate_codes = LicensePlateCode.objects.all()

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        customer    = get_object_or_404(FleetCustomer, id=customer_id)

        vehicle.customer             = customer
        vehicle.customer_name        = customer.customer_name
        vehicle.vehicle_name         = request.POST.get('vehicle_name')
        vehicle.license_plate_code   = request.POST.get('license_plate_code')
        vehicle.license_plate_number = request.POST.get('license_plate_number')
        vehicle.vehicle_driver       = request.POST.get('vehicle_driver', '')
        vehicle.vehicle_category     = request.POST.get('vehicle_category', '')
        vehicle.RC_number            = request.POST.get('RC_number', '')
        vehicle.contract_no          = request.POST.get('contract_no', '')
        vehicle.contract_start_date  = request.POST.get('contract_start_date', '')
        vehicle.contract_end_date    = request.POST.get('contract_end_date', '')

        if request.FILES.get('vehicle_image'):
            vehicle.vehicle_image = request.FILES['vehicle_image']

        vehicle.save()
        messages.success(request, "Vehicle updated!")
        return redirect('fleet_app:vehicle_master_list')

    return render(request, 'fleet_app/vehicle_master_form.html', {
        'customers':   customers,
        'categories':  categories,
        'plate_codes': plate_codes,
        'vehicle':     vehicle,
    })


def vehicle_master_delete(request, pk):
    vehicle = get_object_or_404(VehicleMaster, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, "Vehicle deleted.")
        return redirect('fleet_app:vehicle_master_list')
    return render(request, 'fleet_app/vehicle_master_confirm_delete.html', {'vehicle': vehicle})
    '''