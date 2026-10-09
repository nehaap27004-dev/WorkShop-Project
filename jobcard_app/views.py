from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, request
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
import logging
import json

from fleet_app.models import FleetCustomer, Vehicle
from item_master.models import Item
from accounts_app   .models import LedgerCreation
from audit_app.common import log_activity
from fleet_app.models import FleetCustomer, Vehicle, Staff, StaffCategory

from datetime import datetime
from .models import (
    VehicleInspection, ExteriorDamage, InteriorInspection,
    MechanicalInspection, AccessoriesInspection,
    InspectionFinding
)
from .models import JobCardVehicle
from .models import (
    JobCard,
    WorkshopVehicle,
)
from .models import (
  
    Invoice,
    
)
from fleet_app.models import VehicleCategory

from fleet_app.models import  Manufacturer, VehicleModel
from fleet_app.models import VehicleCategory

import logging
from decimal import Decimal
 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
 
from accounts_app.models import LedgerCreation
from fleet_app.models import Staff
from .models import (
    DeliveryNoteVehicle, Estimate, EstimateComplaint, EstimateItem, EstimateVehicle,
    Invoice, InvoiceItem, InvoiceVehicle, JobCardVehicle, Quotation, QuotationItem,
    ServiceCategory, ServiceType, SkillTag, ComplaintType,
)
from .models import Invoice, InvoiceItem, InvoiceVehicle, JobCard, WorkshopVehicle
from .utils import get_next_document_number
from .common import (
    PostingError,
    create_ledger_postings_for_invoice,
    delete_ledger_postings_for_invoice,
)
# ─────────────────────────────────────────────────────────────
# SERVICE CATEGORY
# ─────────────────────────────────────────────────────────────
@login_required
def service_category_list(request):
    categories = ServiceCategory.objects.all().order_by('name')
    return render(request, 'jobcard_app/service_category_list.html', {
        'categories': categories,
        'total':      categories.count(),
        'active':     categories.filter(is_active=True).count(),
        'inactive':   categories.filter(is_active=False).count(),
    })


@login_required
def service_category_create(request):
    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active   = request.POST.get('is_active', 'true') == 'true'

        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, 'jobcard_app/service_category_form.html',
                          {'post': request.POST})

        if ServiceCategory.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A category named "{name}" already exists.')
            return render(request, 'jobcard_app/service_category_form.html',
                          {'post': request.POST})

        ServiceCategory.objects.create(
            name        = name,
            description = description,
            is_active   = is_active,
            created_by  = request.user.id if request.user.is_authenticated else None,
        )
        messages.success(request, f'Service category "{name}" created.')
        return redirect('jobcard_app:service_category_list')

    return render(request, 'jobcard_app/service_category_form.html', {})


@login_required
def service_category_edit(request, pk):
    cat = get_object_or_404(ServiceCategory, pk=pk)

    if request.method == 'POST':
        name        = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active   = request.POST.get('is_active', 'true') == 'true'

        if not name:
            messages.error(request, 'Category name is required.')
            return render(request, 'jobcard_app/service_category_form.html',
                          {'cat': cat, 'post': request.POST})

        if ServiceCategory.objects.filter(name__iexact=name).exclude(pk=cat.pk).exists():
            messages.error(request, f'A category named "{name}" already exists.')
            return render(request, 'jobcard_app/service_category_form.html',
                          {'cat': cat, 'post': request.POST})

        cat.name        = name
        cat.description = description
        cat.is_active   = is_active
        cat.updated_by  = request.user.id if request.user.is_authenticated else None
        cat.save()
        messages.success(request, f'Service category "{cat.name}" updated.')
        return redirect('jobcard_app:service_category_list')

    return render(request, 'jobcard_app/service_category_form.html', {'cat': cat})


@login_required
def service_category_delete(request, pk):
    cat = get_object_or_404(ServiceCategory, pk=pk)

    if request.method == 'POST':
        if cat.service_count() > 0:
            messages.error(request, 'Cannot delete a category linked to services.')
        else:
            name = cat.name
            cat.delete()
            messages.success(request, f'Service category "{name}" deleted.')

    return redirect('jobcard_app:service_category_list')

    return render(request, 'jobcard_app/service_category_confirm_delete.html', {'cat': cat})
@login_required
def get_service_categories(request):
    """AJAX: return active service categories as {id, name} pairs."""
    categories = ServiceCategory.objects.filter(
        is_active=True
    ).order_by('name').values('id', 'name')
    return JsonResponse({'categories': list(categories)})


# ─────────────────────────────────────────────────────────────
# SERVICE TYPE
# ─────────────────────────────────────────────────────────────
@login_required
def service_type_list(request):
    category_id = request.GET.get('category_id')
    service_types = ServiceType.objects.select_related('category', 'required_skill').all().order_by('category__name', 'type_name')
    if category_id:
        service_types = service_types.filter(category_id=category_id)
    
    categories = ServiceCategory.objects.all().order_by('name')
    return render(request, 'jobcard_app/service_type_list.html', {
        'service_types': service_types,
        'categories':    categories,
        'selected_category_id': int(category_id) if category_id and category_id.isdigit() else None,
        'total':         service_types.count(),
        'active':        service_types.filter(is_active=True).count(),
        'inactive':      service_types.filter(is_active=False).count(),
    })


@login_required
def service_type_create(request):
    categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
    skills = SkillTag.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        category_id       = request.POST.get('category_id')
        type_name         = request.POST.get('type_name', '').strip()
        code              = request.POST.get('code', '').strip()
        description       = request.POST.get('description', '').strip()
        required_skill_id = request.POST.get('required_skill_id')
        is_active         = request.POST.get('is_active', 'true') == 'true'

        if not category_id:
            messages.error(request, 'Parent Service Category is required.')
            return render(request, 'jobcard_app/service_type_form.html', {
                'categories': categories, 'skills': skills, 'post': request.POST
            })

        if not type_name:
            messages.error(request, 'Service type name is required.')
            return render(request, 'jobcard_app/service_type_form.html', {
                'categories': categories, 'skills': skills, 'post': request.POST
            })

        if ServiceType.objects.filter(category_id=category_id, type_name__iexact=type_name).exists():
            messages.error(request, f'A service type named "{type_name}" already exists in this category.')
            return render(request, 'jobcard_app/service_type_form.html', {
                'categories': categories, 'skills': skills, 'post': request.POST
            })

        ServiceType.objects.create(
            category_id       = category_id,
            type_name         = type_name,
            code              = code,
            description       = description,
            required_skill_id = required_skill_id if required_skill_id else None,
            is_active         = is_active,
        )
        messages.success(request, f'Service type "{type_name}" created successfully.')
        return redirect('jobcard_app:service_type_list')

    return render(request, 'jobcard_app/service_type_form.html', {
        'categories': categories,
        'skills': skills,
    })


@login_required
def service_type_edit(request, pk):
    st = get_object_or_404(ServiceType, pk=pk)
    categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
    skills = SkillTag.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        category_id       = request.POST.get('category_id')
        type_name         = request.POST.get('type_name', '').strip()
        code              = request.POST.get('code', '').strip()
        description       = request.POST.get('description', '').strip()
        required_skill_id = request.POST.get('required_skill_id')
        is_active         = request.POST.get('is_active', 'true') == 'true'

        if not category_id:
            messages.error(request, 'Parent Service Category is required.')
            return render(request, 'jobcard_app/service_type_form.html', {
                'st': st, 'categories': categories, 'skills': skills, 'post': request.POST
            })

        if not type_name:
            messages.error(request, 'Service type name is required.')
            return render(request, 'jobcard_app/service_type_form.html', {
                'st': st, 'categories': categories, 'skills': skills, 'post': request.POST
            })

        if ServiceType.objects.filter(category_id=category_id, type_name__iexact=type_name).exclude(pk=st.pk).exists():
            messages.error(request, f'A service type named "{type_name}" already exists in this category.')
            return render(request, 'jobcard_app/service_type_form.html', {
                'st': st, 'categories': categories, 'skills': skills, 'post': request.POST
            })

        st.category_id       = category_id
        st.type_name         = type_name
        st.code              = code
        st.description       = description
        st.required_skill_id = required_skill_id if required_skill_id else None
        st.is_active         = is_active
        st.save()

        messages.success(request, f'Service type "{st.type_name}" updated successfully.')
        return redirect('jobcard_app:service_type_list')

    return render(request, 'jobcard_app/service_type_form.html', {
        'st': st,
        'categories': categories,
        'skills': skills,
    })


@login_required
def service_type_delete(request, pk):
    st = get_object_or_404(ServiceType, pk=pk)

    if request.method == 'POST':
        name = st.type_name
        st.delete()
        messages.success(request, f'Service type "{name}" deleted.')
        return redirect('jobcard_app:service_type_list')

    return render(request, 'jobcard_app/service_type_confirm_delete.html', {'st': st})


@login_required
def get_service_types(request):
    """AJAX: return active service types filtered by category_id (optional)."""
    category_id = request.GET.get('category_id')
    qs = ServiceType.objects.filter(is_active=True).select_related('required_skill', 'category').order_by('type_name')
    if category_id:
        qs = qs.filter(category_id=category_id)

    st_list = []
    for st in qs:
        st_list.append({
            'id': st.id,
            'type_name': st.type_name,
            'code': st.code or '',
            'category_id': st.category_id,
            'category_name': st.category.name,
            'skill_id': st.required_skill_id or 0,
            'skill_name': st.required_skill.name if st.required_skill else '',
        })
    return JsonResponse({'service_types': st_list})
 
 
@login_required
def ajax_get_categories(request):
    """AJAX: return active service categories as {id, name} pairs."""
    categories = ServiceCategory.objects.filter(
        is_active=True
    ).order_by('name').values('id', 'name')
    return JsonResponse({'categories': list(categories)})
def _inspection_context():
    return {
        'interior_items': [
            ('dashboard',      'Dashboard'),
            ('seats',          'Seats'),
            ('steering_wheel', 'Steering Wheel'),
            ('ac_system',      'AC System'),
            ('audio_system',   'Audio System'),
            ('windows',        'Windows'),
            ('seat_belts',     'Seat Belts'),
            ('floor_carpet',   'Floor Carpet'),
            ('headliner',      'Headliner'),
            ('door_panels',    'Door Panels'),
        ],
        'engine_items': [
            ('oil_leak',       'Oil Leak'),
            ('coolant_leak',   'Coolant Leak'),
            ('abnormal_noise', 'Abnormal Noise'),
        ],
        'suspension_items': [
            ('shock_absorbers', 'Shock Absorbers'),
            ('bushes',          'Bushes'),
        ],
        'brake_items': [
            ('brake_pad',  'Brake Pad Condition'),
            ('brake_disc', 'Brake Disc Condition'),
        ],
        'electrical_items': [
            ('battery', 'Battery'),
            ('starter', 'Starter'),
            ('lights',  'Lights'),
        ],
        'accessory_items': [
            ('spare_wheel',       'Spare Wheel'),
            ('tool_kit',          'Tool Kit'),
            ('service_book',      'Service Book'),
            ('remote_key',        'Remote Key'),
            ('safety_triangle',   'Safety Triangle'),
            ('floor_mat',         'Floor Mat'),
            ('jack',              'Jack'),
            ('fire_extinguisher', 'Fire Extinguisher'),
            ('first_aid_kit',     'First Aid Kit'),
        ],
    }
 
 
def _generate_inspection_number():
    from jobcard_app.utils import generate_voucher_number
    return generate_voucher_number('Vehicle Inspection', VehicleInspection, 'inspection_number', default_prefix='VI-')
 
 
def _save_inspection(request, insp):
    """Save all related inspection records from POST data"""

    # ── Master fields ────────────────────────────────────────
    insp.driver_name     = request.POST.get('driver_name', '').strip()
    insp.overall_status  = request.POST.get('overall_status', 'pass')
 
    # ── Exterior damages ─────────────────────────────────────
    insp.exterior_damages.all().delete()
    zones = request.POST.getlist('damage_zone[]')
    types = request.POST.getlist('damage_type[]')
    for z, t in zip(zones, types):
        if z and t:
            ExteriorDamage.objects.create(
                inspection  = insp,
                zone        = z,
                damage_type = t,
            )
    insp.exterior_remarks = request.POST.get('exterior_remarks', '')
    insp.save()
 
    # ── Interior ─────────────────────────────────────────────
    interior_fields = [
        'dashboard','seats','steering_wheel','ac_system','audio_system',
        'windows','seat_belts','floor_carpet','headliner','door_panels',
    ]
    interior_data = {f: request.POST.get(f, 'good') for f in interior_fields}
    InteriorInspection.objects.update_or_create(
        inspection=insp, defaults=interior_data)
 
    # ── Mechanical, Tyres & Fluids ───────────────────────────
    mech_fields = [
        'oil_leak','coolant_leak','abnormal_noise',
        'brake_pad','brake_disc',
        'shock_absorbers','bushes',
        'battery','starter','lights',
        'tyre_fl','tyre_fr','tyre_rl','tyre_rr','tyre_spare',
        'brake_fluid','steering_fluid','washer_fluid','exhaust_system',
    ]
    mech_data = {f: request.POST.get(f, 'good') for f in mech_fields}
    MechanicalInspection.objects.update_or_create(
        inspection=insp, defaults=mech_data)
 
    # ── Accessories ──────────────────────────────────────────
    acc_fields = [
        'spare_wheel','tool_kit','service_book','remote_key',
        'safety_triangle','floor_mat','jack','fire_extinguisher','first_aid_kit',
    ]
    acc_data = {f: request.POST.get(f, 'available') for f in acc_fields}
    AccessoriesInspection.objects.update_or_create(
        inspection=insp, defaults=acc_data)
 
    # ── Findings ─────────────────────────────────────────────
    insp.findings.all().delete()
    complaints = request.POST.getlist('customer_complaints[]')
    findings   = request.POST.getlist('technician_findings[]')
    for i, c in enumerate(complaints):
        if c.strip():
            InspectionFinding.objects.create(
                inspection   = insp,
                finding_type = 'complaint',
                description  = c.strip(),
                order        = i,
            )
    for i, f in enumerate(findings):
        if f.strip():
            InspectionFinding.objects.create(
                inspection   = insp,
                finding_type = 'finding',
                description  = f.strip(),
                order        = i,
            )
 
    # ── Signature ────────────────────────────────────────────
    insp.customer_signed         = 'customer_signed' in request.POST
    insp.customer_signature_note = request.POST.get('customer_signature_note', '')
    insp.save()
 
    # ── Update vehicle odometer ──────────────────────────────
    if insp.odometer and insp.vehicle:
        v = insp.vehicle
        v.odometer     = insp.odometer
        v.last_service_date = insp.inspection_date
        v.save()
 
 
# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
def inspection_list(request):
    q             = request.GET.get('q', '').strip()
    vehicle_id    = request.GET.get('vehicle', '')
    status_filter = request.GET.get('status', '')
 
    qs = VehicleInspection.objects.select_related(
        'vehicle', 'customer', 'jobcard', 'inspector'
    ).prefetch_related('findings', 'exterior_damages')
 
    if q:
        qs = qs.filter(
            Q(inspection_number__icontains=q) |
            Q(vehicle__registration_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(driver_name__icontains=q)
        )
    if vehicle_id:
        qs = qs.filter(vehicle_id=vehicle_id)
    if status_filter:
        qs = qs.filter(overall_status=status_filter)
 
    vehicles  = WorkshopVehicle.objects.filter(is_active=True).order_by('registration_number')
    customers = LedgerCreation.objects.filter(groups_id=18).order_by('ledger_name')
    today = timezone.now().date()

    return render(request, 'jobcard_app/inspection_list.html', {
        'inspections':    qs,
        'vehicles':       vehicles,
        'customers':      customers,
        'q':              q,
        'vehicle_id':     vehicle_id,
        'status_filter':  status_filter,
        'total':          VehicleInspection.objects.count(),
        'pass_count':     VehicleInspection.objects.filter(overall_status='pass').count(),
        'attention_count':VehicleInspection.objects.filter(overall_status='attention').count(),
        'fail_count':      VehicleInspection.objects.filter(overall_status='fail').count(),
        'with_jobcard':   VehicleInspection.objects.filter(jobcard__isnull=False).count(),
    })
 
 
# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
def inspection_create(request, vehicle_id=None):
    customers = LedgerCreation.objects.filter(
        groups_id=18).order_by('ledger_name')
    inspectors = Staff.objects.filter(
        status='Active',
        staff_category__name__in=['Inspector', 'Technician']
    ).order_by('full_name')
    vehicles  = WorkshopVehicle.objects.filter(is_active=True)
 
    preselected_vehicle  = None
    preselected_customer = None
 
    if vehicle_id:
        preselected_vehicle  = get_object_or_404(WorkshopVehicle, pk=vehicle_id)
        preselected_customer = preselected_vehicle.customer
 
    if request.method == 'POST':
        vid = request.POST.get('vehicle')
        cid = request.POST.get('customer')
 
        if not vid or not cid:
            messages.error(request, 'Vehicle and Customer are required.')
            return redirect('jobcard_app:inspection_create')
 
        vehicle  = get_object_or_404(WorkshopVehicle, pk=vid)
        customer = get_object_or_404(LedgerCreation, pk=cid)
        inspector_id = request.POST.get("inspector")
 
        inspector = None
        if inspector_id:
            inspector = Staff.objects.filter(pk=inspector_id).first()

        insp_no = request.POST.get("inspection_number", "").strip() or None
 
        insp = VehicleInspection(
            inspection_number = insp_no,
            vehicle           = vehicle,
            customer          = customer,
            inspector         = inspector,
            inspection_date   = datetime.strptime(request.POST.get("inspection_date"),"%Y-%m-%d").date(),
            odometer          = request.POST.get('odometer') or None,
            fuel_level        = request.POST.get('fuel_level', '1/2'),
            driver_name       = request.POST.get('driver_name', '').strip(),
            overall_status    = request.POST.get('overall_status', 'pass'),
            created_by        = request.user.id if request.user.is_authenticated else None,
        )
        insp.save()

        veh_type_id  = request.POST.get('veh_type') or None
        veh_mfr_id   = request.POST.get('veh_manufacturer') or None
        veh_model_id = request.POST.get('veh_model') or None
        veh_fuel     = request.POST.get('veh_fuel_type') or None
        veh_color    = request.POST.get('veh_color', '').strip() or None

        if any([veh_type_id, veh_mfr_id, veh_model_id, veh_fuel, veh_color]):
            if veh_type_id:  vehicle.vehicle_type_id = veh_type_id
            if veh_mfr_id:   vehicle.manufacturer_id = veh_mfr_id
            if veh_model_id: vehicle.vehicle_model_id = veh_model_id
            if veh_fuel:      vehicle.fuel_type = veh_fuel
            if veh_color:    vehicle.color = veh_color
            vehicle.save()
 
        _save_inspection(request, insp)
 
        messages.success(
            request,
            f"Inspection {insp.inspection_number} saved successfully!")
        return redirect('jobcard_app:inspection_list')
 
    ctx = _inspection_context()
    ctx.update({
        'customers':            customers,
        'inspectors':           inspectors,
        'vehicles':             vehicles,

# inside the ctx.update({...}) block, add:
        'vehicle_types':        VehicleCategory.objects.all().order_by('category_name'),
        'vehicle_fuel_choices': WorkshopVehicle.FUEL_CHOICES,
        'preselected_vehicle':  preselected_vehicle,
        'preselected_customer': preselected_customer,
        'next_insp_no':         _generate_inspection_number(),
        'today':                timezone.now().date(),
    })
    return render(request, 'jobcard_app/inspection_form.html', ctx)
 
# ─────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
def inspection_edit(request, pk):
    insp      = get_object_or_404(VehicleInspection, pk=pk)
    customers = LedgerCreation.objects.filter(
        groups_id=18).order_by('ledger_name')
    inspectors = Staff.objects.filter(
        status='Active',
        staff_category__name__in=['Inspector', 'Technician']
    ).order_by('full_name')

    vehicles  = WorkshopVehicle.objects.filter(is_active=True)

    try:    interior    = insp.interior
    except: interior    = None
    try:    mechanical  = insp.mechanical
    except: mechanical  = None
    try:    accessories = insp.accessories
    except: accessories = None
 
    complaints = insp.findings.filter(finding_type='complaint').order_by('order')
    findings   = insp.findings.filter(finding_type='finding').order_by('order')
 
    if request.method == 'POST':
        if request.POST.get("inspection_date"):
            insp.inspection_date = datetime.strptime(request.POST.get("inspection_date"),"%Y-%m-%d").date()
        insp.odometer        = request.POST.get('odometer') or None
        insp.fuel_level      = request.POST.get('fuel_level', '1/2')
        inspector_id         = request.POST.get('inspector')
        insp.save()
        _save_inspection(request, insp)
        messages.success(request, f"Inspection {insp.inspection_number} updated successfully.")
        return redirect('jobcard_app:inspection_list')
 
    ctx = _inspection_context()
    ctx.update({
        'vehicle_types':        VehicleCategory.objects.all().order_by('category_name'),
        'vehicle_fuel_choices': WorkshopVehicle.FUEL_CHOICES,
        'insp':        insp,
        'interior':    interior,
        'mechanical':  mechanical,
        'accessories': accessories,

        'complaints':  complaints,
        'findings':    findings,
        'customers':   customers,
        'inspectors':  inspectors,
        'vehicles':    vehicles,
        'edit_mode':   True,
        'today':       timezone.now().date(),
    })
    return render(request, 'jobcard_app/inspection_form.html', ctx)
 
 
# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
def inspection_delete(request, pk):
    insp = get_object_or_404(VehicleInspection, pk=pk)
    if request.method == 'POST':
        num = insp.inspection_number
        insp.delete()
        messages.success(request, f"Inspection {num} deleted.")
        return redirect('jobcard_app:inspection_list')
    return render(request, 'jobcard_app/inspection_confirm_delete.html',
                  {'insp': insp})
 
 
# ─────────────────────────────────────────────────────────────
# AJAX — get vehicles by customer
# ─────────────────────────────────────────────────────────────
def insp_get_vehicles(request):
    cid = request.GET.get('customer_id')
    if not cid:
        return JsonResponse({'vehicles': []})
    qs = WorkshopVehicle.objects.filter(
        customer_id=cid, is_active=True
    ).select_related('vehicle_type', 'manufacturer', 'vehicle_model')

    result = [{
        'id':               v.id,
        'label':            v.vehicle_number,
        'reg':              v.registration_number,
        'vehicle_type_id':  v.vehicle_type_id or '',
        'manufacturer_id':  v.manufacturer_id or '',
        'vehicle_model_id': v.vehicle_model_id or '',
        'color':            v.color or '',
        'odometer':         v.odometer or '',
        'fuel_type':        v.fuel_type or '',
    } for v in qs]
    return JsonResponse({'vehicles': result})




# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@login_required
def jobcard_list(request):
    from django.core.paginator import Paginator
    from django.db.models import Q

    jobs = (
        JobCard.objects
        .select_related(
            'customer',
            'workshop_vehicle',
            'advisor',
            'voucherType'
        )
        .prefetch_related(
            'parts',
            'labours',
            'vehicles',
        )
        .all()
        .order_by('-id')
    )

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        jobs = jobs.filter(
            Q(voucher_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(vehicle_model__icontains=q)
        )

    # Status filter
    status = request.GET.get('status', '').strip()
    if status:
        jobs = jobs.filter(status=status)

    # Priority filter
    priority = request.GET.get('priority', '').strip()
    if priority:
        jobs = jobs.filter(priority=priority)

    # Date filters
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if date_from:
        jobs = jobs.filter(date__gte=date_from)

    if date_to:
        jobs = jobs.filter(date__lte=date_to)

    # Pagination
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Status tabs
    priority_choices = JobCard.PRIORITY_CHOICES

    tabs = []
    for key, label in JobCard.STATUS_CHOICES:
        tabs.append({
            'key': key,
            'label': label,
            'count': JobCard.objects.filter(status=key).count(),
        })

    return render(
        request,
        'jobcard_app/jobcard_list.html',
        {
            'jobs': jobs,
            'page_obj': page_obj,
            'q': q,
            'status': status,
            'priority': priority,
            'date_from': date_from,
            'date_to': date_to,
            'priority_choices': priority_choices,
            'tabs': tabs,
        }
    )

# ─────────────────────────────────────────────────────────────
# CREATE / EDIT (same template renders both)
# ─────────────────────────────────────────────────────────────
def _common_context(job=None):
    return {
        'customers': LedgerCreation.objects.all().order_by('ledger_name'),
        'categories': ServiceCategory.objects.filter(is_active=True).order_by('name'),
        'today': timezone.now().date(),
        'job': job,
        'edit_mode': job is not None,
    }


@login_required
def jobcard_create(request):
    from django.utils import timezone
    from accounts_app.models import LedgerCreation
    from .models import WorkshopVehicle, VehicleInspection
    from .models import ServiceCategory

    customers = LedgerCreation.objects.filter(groups_id=18).order_by('ledger_name')
    items = Item.objects.filter(isDeleted=False).order_by('item_name')
    categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
    inspections = VehicleInspection.objects.select_related('vehicle', 'customer').order_by('-inspection_date', '-created_on')
    technicians = Staff.objects.filter(status='Active', staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    all_staff   = Staff.objects.filter(status='Active').order_by('full_name')
    inspection      = None
    insp_complaints = []
    
    prefill_category = ''


    prefill_findings = []
    from_inspection = request.GET.get('from_inspection')
    if from_inspection:
        inspection = VehicleInspection.objects.filter(pk=from_inspection).first()
        if inspection:
            insp_complaints = inspection.findings.filter(
                finding_type='complaint').order_by('order')
            prefill_findings = list(
                inspection.findings.filter(finding_type='finding')
                .values_list('description', flat=True).order_by('order')
            )

    from jobcard_app.utils import generate_voucher_number
    from fleet_app.models import Vouchers
    voucher_types = Vouchers.objects.all().order_by('VoucherName')
    # Use the selected/default Job Card voucher type
    jobcard_voucher = voucher_types.filter(VoucherName='Repair').first()
    next_job_number = None
    if jobcard_voucher:
        next_job_number = get_next_document_number(
            jobcard_voucher.id,
            JobCard,
            'voucher_number'
        )

    if request.method == 'POST':
        return _save_jobcard(request, job=None)

    items_json = json.dumps([
        {'id': it.id, 'name': it.item_name, 'code': it.item_code or '',
         'rate': float(it.sales_rate or 0)}
        for it in items
    ])

    return render(request, 'jobcard_app/jobcard_form.html', {
        'jobcard':      None,
        'next_job_number': next_job_number,
        'voucher_types': voucher_types,
        'customers':    customers,
        'technicians':  technicians,
        'advisors':     advisors,
        'all_staff':    all_staff,
        'staff':        technicians,
        'items':        items,
        'items_json':   items_json,
        'categories':   categories,
        'inspections':  inspections,
        'inspection':       inspection,
        'prefill_inspection': inspection,
        'insp_complaints':  insp_complaints,
        'prefill_findings': prefill_findings,
        'prefill_category': prefill_category,
        'today':        timezone.now().date(),
        'relational_mapping_json': json.dumps(_get_relational_mapping_dict()),
    })


def get_next_jobcard_number(request):
    """AJAX view to get next Job Card number"""
    voucher_type_id = request.GET.get('voucher_type_id')
    try:
        number = get_next_document_number(voucher_type_id,JobCard,'voucher_number')
        return JsonResponse({'success': True,'job_number': number,'voucher_number': number })
    except ValueError as e:
        return JsonResponse({'success': False,'error': str(e) }, status=400)
@login_required
def get_next_estimate_number(request):
    """Next voucher number for Estimate."""
    from fleet_app.models import Vouchers
    from jobcard_app.utils import generate_voucher_number
    from .models import Estimate

    voucher_type_id = request.GET.get('voucher_type_id')

    if voucher_type_id:
        try:
            vt = Vouchers.objects.get(pk=voucher_type_id)

            num = vt.get_next_voucher_number(
                Estimate,
                'voucher_number'
            )

            return JsonResponse({
                'success': True,
                'job_number': num,
                'voucher_number': num,
            })

        except Vouchers.DoesNotExist:
            pass

    next_num = generate_voucher_number(
        'Estimate',
        Estimate,
        'voucher_number',
        default_prefix='EST-'
    )

    return JsonResponse({
        'success': True,
        'job_number': next_num,
        'voucher_number': next_num,
    })
@login_required
def jobcard_edit(request, pk):
    from .models import ServiceCategory
    from fleet_app.models import Vouchers

    job = get_object_or_404(JobCard, pk=pk)

    if request.method == 'POST':
        return _save_jobcard(request, job=job)

    from accounts_app.models import LedgerCreation
    from django.utils import timezone
    from .models import ServiceCategory
    customers   = LedgerCreation.objects.filter(
                      groups_id=18).order_by('ledger_name')

    categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
    technicians = Staff.objects.filter(
                    status='Active',
                    staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    voucher_types = Vouchers.objects.all().order_by('VoucherName')

    return render(request, 'jobcard_app/jobcard_form.html', {
        'job':          job,
        'jobcard':      job,
        'voucher_types': voucher_types,
        'customers':    customers,
        'technicians':  technicians,
        'advisors':     advisors,
        'categories':   categories,
        'staff':        technicians,
        'today':        timezone.now().date(),
        'edit_mode':    True,
        'relational_mapping_json': json.dumps(_get_relational_mapping_dict()),
    })

@transaction.atomic
def _save_jobcard(request, job=None):
    from django.utils import timezone
    from accounts_app.models import LedgerCreation
    from fleet_app.models import Vouchers
    from .models import (JobCard, JobCardVehicle, JobCardComplaint, JobCardFinding,
                         JobCardPart, JobCardLabour,
                         WorkshopVehicle, VehicleInspection, ServiceCategory,
                         ComplaintType, TechnicianSkill)

    cid      = request.POST.get('customer')

    date       = request.POST.get('date') or timezone.now().date()
    advisor_id = request.POST.get('advisor')
    advisor    = Staff.objects.filter(pk=advisor_id).first() if advisor_id else None

    if not cid:
        messages.error(request, 'Customer is required.')
        return redirect('jobcard_app:jobcard_create')

    customer = get_object_or_404(LedgerCreation, pk=cid)

    # ── Create or update JobCard ──────────────────────────
    is_new_job = (job is None or not getattr(job, 'pk', None))
    old_job_snapshot = None
    if not is_new_job:
        old_job_snapshot = {
            'status': job.status,
            'priority': job.priority,
            'advisor': str(job.advisor) if job.advisor else '',
            'mileage': str(job.mileage or ''),
            'delivery_date': str(job.delivery_date or ''),
        }

    if job is None:
        job = JobCard(created_by=request.user.id)

    vt_id = request.POST.get('voucherType')
    if vt_id:
        job.voucherType = Vouchers.objects.filter(pk=vt_id).first()
    elif not job.voucherType_id:
        job.voucherType = Vouchers.objects.filter(VoucherName='JobCard').first()

    v_num = request.POST.get('voucher_number', '').strip()
    job_num = request.POST.get('job_number', '').strip()

    if v_num:
        job.voucher_number = v_num
    elif job_num:
        job.voucher_number = job_num

    if job_num:
        job.job_number = job_num
    elif v_num:
        job.job_number = v_num

    job.customer          = customer
    job.customer_phone    = request.POST.get('customer_phone', '')
    job.vehicle_model     = request.POST.get('vehicle_model', '')
    job.advisor            = advisor
    job.date               = date
    job.priority            = request.POST.get('priority', 'normal')
    job.status               = request.POST.get('status', 'open')
    job.delivery_date         = request.POST.get('delivery_date') or None
    job.mileage                = request.POST.get('mileage') or None
    job.save()


    source_insp_id = request.POST.get('source_inspection_id') or request.POST.get('from_inspection')
    if source_insp_id:
        insp = VehicleInspection.objects.filter(pk=source_insp_id).first()
        if insp:
            insp.jobcard = job
            insp.save()

    # ── Clear old rows (edit mode) ────────────────────────
    job.vehicles.all().delete()
    job.complaints.all().delete()
    job.findings.all().delete()
    job.parts.all().delete()
    job.labours.all().delete()

    # ── Vehicles table (multiple vehicles per job card) ────
    veh_ids       = request.POST.getlist('jc_vehicle_id[]')
    veh_mileages  = request.POST.getlist('jc_vehicle_mileage[]')
    veh_fuels     = request.POST.getlist('jc_vehicle_fuel[]')
    veh_notes     = request.POST.getlist('jc_vehicle_notes[]')
    first_vehicle = None
    seen_vehicles = set()
    for i, v_id in enumerate(veh_ids):
        if not v_id or v_id in seen_vehicles:
            continue
        seen_vehicles.add(v_id)
        veh = WorkshopVehicle.objects.filter(pk=v_id).first()
        if not veh:
            continue
        if first_vehicle is None:
            first_vehicle = veh

        JobCardVehicle.objects.create(
            jobcard    = job,
            vehicle    = veh,
            mileage    = veh_mileages[i] if i < len(veh_mileages) and veh_mileages[i] else None,
            fuel_level = veh_fuels[i] if i < len(veh_fuels) and veh_fuels[i] else '1/2',
            notes      = veh_notes[i] if i < len(veh_notes) else '',
        )

    # Keep legacy single-vehicle fields in sync (first vehicle in the table)
    job.workshop_vehicle = first_vehicle
    job.mileage = first_vehicle and (
        JobCardVehicle.objects.filter(jobcard=job, vehicle=first_vehicle).first().mileage
    ) or None
    if first_vehicle:
        job.vehicle_model = f"{first_vehicle.manufacturer.manufacturer_name if first_vehicle.manufacturer else ''} " \
                            f"{first_vehicle.vehicle_model.model_name if first_vehicle.vehicle_model else ''}".strip()
    job.save()

    # ── Complaints ────────────────────────────────────────
    categories          = request.POST.getlist('complaint_category_id[]')
    cat_texts           = request.POST.getlist('complaint_category[]')
    complaint_type_ids  = request.POST.getlist('complaint_type_id[]')
    descriptions        = request.POST.getlist('complaint_description[]')
    types               = request.POST.getlist('complaint_type[]')
    tech_ids            = request.POST.getlist('complaint_technician[]')
    statuses            = request.POST.getlist('complaint_status[]')
    complaint_veh_ids   = request.POST.getlist('complaint_vehicle_id[]')
    manual_overrides    = request.POST.getlist('complaint_manual_override[]')

    for i, desc in enumerate(descriptions):
        if not desc.strip():
            continue

        cat_id  = categories[i] if i < len(categories) else None
        cat_obj = ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None
        cat_txt = cat_texts[i] if i < len(cat_texts) else ''

        ct_id  = complaint_type_ids[i] if i < len(complaint_type_ids) else None
        ct_obj = None
        st_obj = None
        if ct_id:
            ct_id_str = str(ct_id).strip()
            if ct_id_str.isdigit():
                ct_obj = ComplaintType.objects.filter(pk=ct_id_str).first()
            elif ct_id_str.startswith('st_'):
                st_pk = ct_id_str.replace('st_', '')
                if st_pk.isdigit():
                    st_obj = ServiceType.objects.filter(pk=st_pk).first()

        tech_id = tech_ids[i] if i < len(tech_ids) else None
        tech    = Staff.objects.filter(pk=tech_id).first() if tech_id else None

        c_veh_id  = complaint_veh_ids[i] if i < len(complaint_veh_ids) else None
        c_veh_obj = WorkshopVehicle.objects.filter(pk=c_veh_id).first() if c_veh_id else first_vehicle

        raw_override = manual_overrides[i] if i < len(manual_overrides) else '0'
        override_flag = (str(raw_override).strip() == '1' or str(raw_override).lower() == 'true')

        req_skill = None
        complaint_title = types[i] if (i < len(types) and types[i]) else 'Mechanical'
        if ct_obj:
            req_skill = ct_obj.required_skill
            complaint_title = ct_obj.complaint_name
        elif st_obj:
            req_skill = st_obj.required_skill
            complaint_title = st_obj.type_name

        type_val = (complaint_title or 'Mechanical')[:200]

        # Validation: If technician selected and complaint/service type requires a skill, check qualification
        if tech and req_skill and not override_flag:
            has_skill = TechnicianSkill.objects.filter(technician=tech, skill=req_skill).exists()
            if not has_skill:
                if is_new_job and job.pk:
                    job.delete()
                messages.error(
                    request,
                    f"Technician '{tech.full_name}' lacks required skill '{req_skill.name}' "
                    f"for complaint '{complaint_title}'. Enable Manual Override to proceed."
                )
                return redirect(request.path)

        JobCardComplaint.objects.create(
            jobcard            = job,
            vehicle            = c_veh_obj,
            service_category   = cat_obj,
            category           = cat_txt,
            complaint_type_ref = ct_obj,
            service_type_ref   = st_obj,
            description        = desc.strip(),
            type               = type_val,
            technician         = tech,
            status             = statuses[i] if i < len(statuses) else 'Open',
            is_manual_override = override_flag,
        )

    # ── Findings ──────────────────────────────────────────
    f_descriptions = request.POST.getlist('finding_description[]')
    f_tech_ids     = request.POST.getlist('finding_technician[]')
    f_statuses     = request.POST.getlist('finding_status[]')
    f_veh_ids      = request.POST.getlist('finding_vehicle_id[]')

    for i, desc in enumerate(f_descriptions):
        if not desc.strip():
            continue

        f_tech_id = f_tech_ids[i] if i < len(f_tech_ids) else None
        tech      = Staff.objects.filter(pk=f_tech_id).first() if f_tech_id else None

        f_veh_id  = f_veh_ids[i] if i < len(f_veh_ids) else None
        f_veh_obj = WorkshopVehicle.objects.filter(pk=f_veh_id).first() if f_veh_id else first_vehicle

        JobCardFinding.objects.create(
            jobcard     = job,
            description = desc.strip(),
            technician  = tech,
            status      = f_statuses[i] if i < len(f_statuses) else 'Pending',
        )

    # ── Parts ─────────────────────────────────────────────
    part_items   = request.POST.getlist('part_item[]')
    part_numbers = request.POST.getlist('part_number[]')
    part_qtys    = request.POST.getlist('part_qty[]')
    part_rates   = request.POST.getlist('part_rate[]')
    part_veh_ids = request.POST.getlist('part_vehicle_id[]')

    for i, desc in enumerate(part_items):
        if not desc.strip():
            continue
        qty  = float(part_qtys[i])  if i < len(part_qtys)  else 1
        rate = float(part_rates[i]) if i < len(part_rates) else 0

        p_veh_id  = part_veh_ids[i] if i < len(part_veh_ids) else None
        p_veh_obj = WorkshopVehicle.objects.filter(pk=p_veh_id).first() if p_veh_id else first_vehicle

        JobCardPart.objects.create(
            jobcard    = job,
            vehicle    = p_veh_obj,
            description = desc.strip(),
            part_number = part_numbers[i] if i < len(part_numbers) else '',
            quantity    = qty,
            unit_price  = rate,
            total_price = qty * rate,
        )

    # ── Labour ────────────────────────────────────────────
    l_tech_ids = request.POST.getlist('labour_technician[]')
    l_descs    = request.POST.getlist('labour_description[]')
    l_hours    = request.POST.getlist('labour_hours[]')
    l_rates    = request.POST.getlist('labour_rate[]')
    l_veh_ids  = request.POST.getlist('labour_vehicle_id[]')

    for i, desc in enumerate(l_descs):
        if not desc.strip():
            continue

        l_tech_id = l_tech_ids[i] if i < len(l_tech_ids) else None
        tech      = Staff.objects.filter(pk=l_tech_id).first() if l_tech_id else None

        l_veh_id  = l_veh_ids[i] if i < len(l_veh_ids) else None
        l_veh_obj = WorkshopVehicle.objects.filter(pk=l_veh_id).first() if l_veh_id else first_vehicle

        hrs   = float(l_hours[i]) if i < len(l_hours) else 1
        rate  = float(l_rates[i]) if i < len(l_rates) else 0
        JobCardLabour.objects.create(
            jobcard    = job,
            vehicle    = l_veh_obj,
            technician  = tech,
            description = desc.strip(),
            hours       = hrs,
            rate        = rate,
            amount      = hrs * rate,
        )

    # ── Link inspection to this job card ─────────────────
    from_insp_id = request.POST.get('from_inspection_id') or request.POST.get('source_inspection_id')
    if from_insp_id:
        try:
            insp = VehicleInspection.objects.get(pk=from_insp_id)
            insp.jobcard = job
            insp.save(update_fields=['jobcard'])
        except VehicleInspection.DoesNotExist:
            pass

    # ── Audit Log Event ──────────────────────────────────
    try:
        from audit_app.services import log_audit_event
        if is_new_job:
            log_audit_event(
                action='CREATE',
                module='JOBCARD',
                entity_type='JobCard',
                entity_id=job.pk,
                entity_reference=job.job_number,
                description=f"Created Job Card #{job.job_number} for customer '{customer.ledger_name}' (Model: {job.vehicle_model or 'N/A'}, Status: {job.status}, Priority: {job.priority}).",
                changes_diff={'initial_state': {
                    'job_number': job.job_number,
                    'customer': str(customer.ledger_name),
                    'vehicle_model': job.vehicle_model,
                    'status': job.status,
                    'priority': job.priority,
                    'advisor': str(advisor) if advisor else '',
                    'mileage': str(job.mileage or ''),
                }},
                user=request.user,
                request=request
            )
        else:
            new_job_snapshot = {
                'status': job.status,
                'priority': job.priority,
                'advisor': str(job.advisor) if job.advisor else '',
                'mileage': str(job.mileage or ''),
                'delivery_date': str(job.delivery_date or ''),
            }
            job_diff = {}
            job_desc_changes = []
            if old_job_snapshot:
                for k, old_v in old_job_snapshot.items():
                    new_v = new_job_snapshot[k]
                    if str(old_v) != str(new_v):
                        job_diff[k] = {'old': old_v, 'new': new_v}
                        job_desc_changes.append(f"{k.replace('_', ' ').title()} changed from '{old_v}' to '{new_v}'")
            
            action = 'STATUS_CHANGE' if (list(job_diff.keys()) == ['status']) else 'UPDATE'
            desc = f"Updated Job Card #{job.job_number}. " + ("; ".join(job_desc_changes) if job_desc_changes else "Items/complaints updated.")
            log_audit_event(
                action=action,
                module='JOBCARD',
                entity_type='JobCard',
                entity_id=job.pk,
                entity_reference=job.job_number,
                description=desc,
                changes_diff=job_diff,
                user=request.user,
                request=request
            )
    except Exception:
        pass

    messages.success(
        request,
        f"Job Card {job.job_number} saved successfully!")
    return redirect('jobcard_app:jobcard_list')


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@login_required
def jobcard_delete(request, pk):
    job = get_object_or_404(JobCard, pk=pk)
    job_number = job.job_number
    job.delete()
    messages.success(request, f'Job Card {job_number} deleted.')
    return redirect('jobcard_app:jobcard_list')

# ─────────────────────────────────────────────────────────────
# AJAX — vehicles belonging to the selected customer
# ─────────────────────────────────────────────────────────────
@login_required
def ajax_wv_by_customer(request):
    customer_id = request.GET.get('customer_id')
    if not customer_id:
        return JsonResponse({'vehicles': []})

    from accounts_app.models import LedgerCreation
    customer_phone = ''
    try:
        cust = LedgerCreation.objects.get(pk=customer_id)
        customer_phone = getattr(cust, 'mobile_number', '') or \
                         getattr(cust, 'contact_number', '') or \
                         getattr(cust, 'phone', '') or ''
    except Exception:
        pass

    qs = WorkshopVehicle.objects.filter(
        customer_id=customer_id,
        is_active=True
    ).select_related('manufacturer', 'vehicle_model', 'vehicle_type')

    result = []
    for v in qs:
        reg_num = v.registration_number or ''
        veh_num = v.vehicle_number or ''
        if reg_num and veh_num and reg_num != veh_num:
            label = f"{reg_num} ({veh_num})"
        else:
            label = reg_num or veh_num

        mfr_name = v.manufacturer.manufacturer_name if v.manufacturer else ''
        model_name = v.vehicle_model.model_name if v.vehicle_model else ''
        mm_label = f"{mfr_name} {model_name}".strip()

        result.append({
            'id':               v.id,
            'label':            label,
            'mm_label':         mm_label,
            'reg':              v.registration_number,
            'veh_number':       v.vehicle_number,
            'vehicle_type_id':  v.vehicle_type_id or '',
            'manufacturer_id':  v.manufacturer_id or '',
            'vehicle_model_id': v.vehicle_model_id or '',
            'color':            v.color or '',
            'odometer':         v.odometer or '',
            'fuel_type':        v.fuel_type or '',
            'customer_phone':   customer_phone,
        })

    return JsonResponse({'vehicles': result, 'customer_phone': customer_phone})


def _get_relational_mapping_dict():
    """
    Returns relational dictionary connecting Service Categories, Service Types,
    Complaint Types, Required Skills, and Technician Skill Assignments.
    """
    from .models import ServiceCategory, ServiceType, ComplaintType, SkillTag, TechnicianSkill
    from fleet_app.models import Staff

    categories = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        'complaint_types__required_skill',
        'service_types__required_skill'
    )
    cat_data = []
    for cat in categories:
        complaints = []
        for ct in cat.complaint_types.filter(is_active=True):
            complaints.append({
                'id': ct.id,
                'name': ct.complaint_name,
                'skill_id': ct.required_skill_id or 0,
                'skill_name': ct.required_skill.name if ct.required_skill else '',
            })
        service_types = []
        for st in cat.service_types.filter(is_active=True):
            service_types.append({
                'id': st.id,
                'name': st.type_name,
                'code': st.code or '',
                'skill_id': st.required_skill_id or 0,
                'skill_name': st.required_skill.name if st.required_skill else '',
            })
        cat_data.append({
            'id': cat.id,
            'name': cat.name,
            'complaints': complaints,
            'service_types': service_types,
        })

    all_service_types = []
    for st in ServiceType.objects.filter(is_active=True).select_related('category', 'required_skill'):
        all_service_types.append({
            'id': st.id,
            'type_name': st.type_name,
            'code': st.code or '',
            'category_id': st.category_id,
            'category_name': st.category.name,
            'skill_id': st.required_skill_id or 0,
            'skill_name': st.required_skill.name if st.required_skill else '',
        })

    technicians = Staff.objects.filter(
        status='Active',
        staff_category__name='Technician'
    ).prefetch_related('technician_skills__skill')
    
    tech_data = []
    for t in technicians:
        skill_ids = [ts.skill_id for ts in t.technician_skills.all()]
        skill_names = [ts.skill.name for ts in t.technician_skills.all()]
        tech_data.append({
            'id': t.id,
            'staff_id': t.staff_id,
            'full_name': t.full_name,
            'skill_ids': skill_ids,
            'skill_names': skill_names,
        })

    skills = list(SkillTag.objects.filter(is_active=True).values('id', 'name'))

    return {
        'categories': cat_data,
        'service_types': all_service_types,
        'technicians': tech_data,
        'skills': skills,
    }


@login_required
def ajax_get_relational_mapping(request):
    return JsonResponse(_get_relational_mapping_dict())
def _save_jobcard_complaints(request, jobcard):
    
    from .models import JobCardComplaint, JobCardFinding, ServiceCategory
    
 
    # Clear existing
    jobcard.complaints.all().delete()
    jobcard.findings.all().delete()
 
    # ── Complaints ────────────────────────────────────────────────────────────
    descriptions  = request.POST.getlist('complaint_description[]')
    cat_ids       = request.POST.getlist('complaint_category_id[]')
    cat_texts     = request.POST.getlist('complaint_category[]')
    types         = request.POST.getlist('complaint_type[]')
    tech_ids      = request.POST.getlist('complaint_technician[]')
    statuses      = request.POST.getlist('complaint_status[]')
    insp_ids      = request.POST.getlist('complaint_inspection_id[]')
 
    for i, desc in enumerate(descriptions):
        if not desc.strip():
            continue
 
        cat_id = cat_ids[i] if i < len(cat_ids) else ''
        category = ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None
 
        
 
        insp_id = insp_ids[i] if i < len(insp_ids) else ''
        from .models import VehicleInspection
        insp = VehicleInspection.objects.filter(pk=insp_id).first() if insp_id else None
 
        JobCardComplaint.objects.create(
            jobcard            = jobcard,
            service_category   = category,
            category           = cat_texts[i] if i < len(cat_texts) else '',
            description        = desc.strip(),
            type               = types[i]    if i < len(types)    else 'Mechanical',
          
            status             = statuses[i] if i < len(statuses) else 'Open',
            source_inspection  = insp,
            order              = i,
        )
 
    # ── Findings ──────────────────────────────────────────────────────────────
    f_descriptions = request.POST.getlist('finding_description[]')
    f_tech_ids     = request.POST.getlist('finding_technician[]')
    f_statuses     = request.POST.getlist('finding_status[]')
    f_insp_ids     = request.POST.getlist('finding_inspection_id[]')
 
    for i, desc in enumerate(f_descriptions):
        if not desc.strip():
            continue

 
        insp_id = f_insp_ids[i] if i < len(f_insp_ids) else ''
        from .models import VehicleInspection
        insp = VehicleInspection.objects.filter(pk=insp_id).first() if insp_id else None
 
        JobCardFinding.objects.create(
            jobcard           = jobcard,
            description       = desc.strip(),
            technician        = tech,
            status            = f_statuses[i] if i < len(f_statuses) else 'Pending',
            source_inspection = insp,
            order             = i,
        )

@login_required
def ajax_get_inspections(request):
    from .models import VehicleInspection

    customer_id = request.GET.get('customer_id', '').strip()
    vehicle_ids_param = request.GET.get('vehicle_ids', '').strip()  # comma-separated

    if not customer_id:
        return JsonResponse({'inspections': []})

    qs = VehicleInspection.objects.select_related(
        'vehicle', 'vehicle__manufacturer', 'vehicle__vehicle_model', 'customer', 'inspector'
    ).prefetch_related('findings').filter(customer_id=customer_id)

    if vehicle_ids_param:
        ids = [v for v in vehicle_ids_param.split(',') if v.strip().isdigit()]
        if ids:
            qs = qs.filter(vehicle_id__in=ids)

    qs = qs.order_by('-inspection_date')[:30]

    result = []
    for insp in qs:
        complaints = [
            {'id': f.id, 'description': f.description}
            for f in insp.findings.filter(finding_type='complaint').order_by('order')
            if f.description and f.description.strip()
        ]
        findings = [
            {'id': f.id, 'description': f.description}
            for f in insp.findings.filter(finding_type='finding').order_by('order')
            if f.description and f.description.strip()
        ]

        vehicle_label = ''
        vehicle_number = ''
        if insp.vehicle:
            mfr   = insp.vehicle.manufacturer.manufacturer_name if insp.vehicle.manufacturer else ''
            model = insp.vehicle.vehicle_model.model_name if insp.vehicle.vehicle_model else ''
            vehicle_label = f"{mfr} {model}".strip()
            if insp.vehicle.year:
                vehicle_label += f" ({insp.vehicle.year})"
            vehicle_label += f" · {insp.vehicle.registration_number}"
            vehicle_number = insp.vehicle.vehicle_number

        result.append({
            'id':                insp.id,
            'inspection_number': insp.inspection_number,
            'date':              insp.inspection_date.strftime('%d %b %Y'),
            'vehicle_id':        insp.vehicle_id or '',
            'vehicle_number':    vehicle_number,
            'vehicle_label':     vehicle_label,
            'odometer':          insp.odometer or '',
            'fuel_level':        insp.fuel_level or '',
            'complaints':        complaints,
            'complaints_count':  len(complaints),
            'findings':          findings,
            'findings_count':    len(findings),
        })

    return JsonResponse({'inspections': result})
# ─────────────────────────────────────────────────────────────
# jobcard_app/views.py — ESTIMATE
# ─────────────────────────────────────────────────────────────
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from accounts_app.models import LedgerCreation
from .models import (
    Estimate, EstimateItem, EstimateComplaint,
    JobCard, WorkshopVehicle,
)


# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_list(request):
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    qs = Estimate.objects.select_related(
        'customer', 'vehicle', 'advisor', 'jobcard'
    ).filter(is_active=True)

    if q:
        qs = qs.filter(
            Q(estimate_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(vehicle__registration_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    return render(request, 'jobcard_app/estimate_list.html', {
        'estimates':      qs,
        'q':              q,
        'status_filter':  status,
        'status_choices': Estimate.STATUS_CHOICES,
        'counts': {
            'all':      Estimate.objects.filter(is_active=True).count(),
            'draft':    Estimate.objects.filter(is_active=True, status='draft').count(),
            'sent':     Estimate.objects.filter(is_active=True, status='sent').count(),
            'approved': Estimate.objects.filter(is_active=True, status='approved').count(),
            'rejected': Estimate.objects.filter(is_active=True, status='rejected').count(),
        },
    })


# ─────────────────────────────────────────────────────────────
# CREATE / EDIT (same template renders both)
# ─────────────────────────────────────────────────────────────
def _common_context(estimate=None):
    return {
        'customers':      LedgerCreation.objects.all().order_by('ledger_name'),
     
        'jobcard':      JobCard.objects.filter(
                              status__in=['open', 'in_progress', 'completed']
                          ).order_by('-created_on'),
        'today':          timezone.now().date(),
        'estimate':       estimate,
        'edit_mode':      estimate is not None,
    }


def _save_estimate(request, estimate=None):
    cid = request.POST.get('customer')
    jid = request.POST.get('loaded_jobcard')
    aid = request.POST.get('advisor')
    date = request.POST.get('date') or timezone.now().date()
 
    if not cid:
        messages.error(request, 'Customer is required.')
        return None
 
    customer = get_object_or_404(LedgerCreation, pk=cid)
    jobcard  = JobCard.objects.filter(pk=jid).first() if jid else None
    advisor  = Staff.objects.filter(pk=aid).first() if aid else None
 
    if estimate is None:
        estimate = Estimate(created_by=request.user.id)
 
    estimate.customer    = customer
    estimate.jobcard    = jobcard
    from fleet_app.models import Vouchers
    vt_id = request.POST.get('voucherType')
    estimate.voucherType = Vouchers.objects.filter(pk=vt_id).first() if vt_id else None
    estimate.voucher_number = request.POST.get('voucher_number', '').strip() or None

    est_num = request.POST.get('estimate_number', '').strip()
    if est_num:
        estimate.estimate_number = est_num
      
    estimate.advisor     = advisor
    estimate.date        = date
    estimate.status      = request.POST.get('status', 'draft')
    estimate.mileage     = request.POST.get('mileage') or None
    estimate.vin         = request.POST.get('vin', '') or None
    estimate.tax_percent = request.POST.get('tax_percent') or 0
    estimate.discount    = request.POST.get('discount') or 0
    estimate.notes       = request.POST.get('notes', '')
    estimate.save()
 

    # ── Clear old items & complaints ──────────────────────
    estimate.vehicles.all().delete()
    estimate.items.all().delete()
    estimate.complaints.all().delete()
    veh_ids      = request.POST.getlist('est_vehicle_id[]')
    veh_mileages = request.POST.getlist('est_vehicle_mileage[]')
    veh_notes    = request.POST.getlist('est_vehicle_notes[]')
    first_vehicle = None
    seen_vehicles = set()
    for i, v_id in enumerate(veh_ids):
        if not v_id or v_id in seen_vehicles:
            continue
        seen_vehicles.add(v_id)
        veh = WorkshopVehicle.objects.filter(pk=v_id).first()
        if not veh:
            continue
        if first_vehicle is None:
            first_vehicle = veh
        EstimateVehicle.objects.create(
            estimate = estimate,
            vehicle  = veh,
            mileage  = veh_mileages[i] if i < len(veh_mileages) and veh_mileages[i] else None,
            notes    = veh_notes[i] if i < len(veh_notes) else '',
        )

    # Keep legacy single-vehicle fields in sync
    estimate.vehicle = first_vehicle
    estimate.mileage = first_vehicle and (
        EstimateVehicle.objects.filter(estimate=estimate, vehicle=first_vehicle).first().mileage
    ) or None
    estimate.save()

    # ── Parts ─────────────────────────────────────────────
    part_ids     = request.POST.getlist('part_item_id[]')
    descriptions = request.POST.getlist('description[]')
    item_refs    = request.POST.getlist('item_ref[]')
    part_nos     = request.POST.getlist('part_number[]')
    item_units   = request.POST.getlist('item_unit[]')
    quantities   = request.POST.getlist('quantity[]')
    unit_prices  = request.POST.getlist('unit_price[]')
    warranties   = request.POST.getlist('part_warranty[]')
    part_veh_ids = request.POST.getlist('part_vehicle_id[]')   # ← add this line
    
    max_len = max(len(descriptions), len(part_ids), len(part_nos), len(quantities))
    for i in range(max_len):
        desc = descriptions[i] if i < len(descriptions) else ''
        p_id = part_ids[i] if i < len(part_ids) else (item_refs[i] if i < len(item_refs) else '')
        p_no = part_nos[i] if i < len(part_nos) else ''
        
        if not desc.strip():
            if p_id:
                try:
                    from item_master.models import ItemMaster
                    item_obj = ItemMaster.objects.filter(pk=p_id).first()
                    if item_obj:
                        desc = item_obj.name
                except Exception:
                    pass
            if not desc.strip() and p_no:
                desc = f"Part {p_no}"
            if not desc.strip():
                continue
        
        qty_val = 1.0
        if i < len(quantities) and quantities[i]:
            try:
                qty_val = float(quantities[i])
            except ValueError:
                qty_val = 1.0

        price_val = 0.0
        if i < len(unit_prices) and unit_prices[i]:
            try:
                price_val = float(unit_prices[i])
            except ValueError:
                price_val = 0.0
        p_veh_id  = part_veh_ids[i] if i < len(part_veh_ids) else None
        p_veh_obj = WorkshopVehicle.objects.filter(pk=p_veh_id).first() if p_veh_id else first_vehicle
        EstimateItem.objects.create(
            estimate    = estimate,
            vehicle     = p_veh_obj,
            item_type   = 'part',
            item_ref    = p_id,
            item_code   = p_no,
            unit        = item_units[i] if i < len(item_units) else '',
            description = desc.strip(),
            quantity    = qty_val,
            unit_price  = price_val,
            warranty    = warranties[i] if i < len(warranties) else '',
            order       = i,
        )
    # ── Labour ────────────────────────────────────────────
    labour_descs  = request.POST.getlist('labour_desc[]')
    labour_techs  = request.POST.getlist('labour_tech[]')
    labour_hours  = request.POST.getlist('labour_hrs[]')
    labour_rates  = request.POST.getlist('labour_rate[]')
    labour_veh_ids = request.POST.getlist('labour_vehicle_id[]')

    for i, desc in enumerate(labour_descs):
        if not desc.strip():
            continue
        tech = Staff.objects.filter(
                pk=labour_techs[i] if i < len(labour_techs) else None).first()

        l_veh_id  = labour_veh_ids[i] if i < len(labour_veh_ids) else None
        l_veh_obj = WorkshopVehicle.objects.filter(pk=l_veh_id).first() if l_veh_id else first_vehicle

        EstimateItem.objects.create(
            estimate    = estimate,
            vehicle     = l_veh_obj,
            item_type   = 'labour',
            description = desc.strip(),
            technician  = tech,
            hours       = float(labour_hours[i]) if i < len(labour_hours) else 1,
            unit_price  = float(labour_rates[i]) if i < len(labour_rates) else 0,
            order       = i,
        )
 
    # ── Customer Complaints ───────────────────────────────
    from .models import ServiceCategory, ComplaintType, ServiceType

    complaint_veh_ids    = request.POST.getlist('customer_complaint_vehicle_id[]')
    complaint_cat_ids    = request.POST.getlist('customer_complaint_cat_id[]')
    complaint_cat_texts  = request.POST.getlist('customer_complaint_cat[]')
    complaint_type_ids   = request.POST.getlist('customer_complaint_type_id[]')
    complaint_type_texts = request.POST.getlist('customer_complaint_type[]')
    complaint_descriptions = request.POST.getlist('customer_complaint[]')
    complaint_tech_ids   = request.POST.getlist('customer_complaint_technician[]')
    complaint_overrides  = request.POST.getlist('customer_complaint_manual_override[]')
    complaint_statuses   = request.POST.getlist('customer_complaint_status[]')

    for i, c in enumerate(complaint_descriptions):
        if c.strip():
            c_veh_id  = complaint_veh_ids[i] if i < len(complaint_veh_ids) else None
            c_veh_obj = WorkshopVehicle.objects.filter(pk=c_veh_id).first() if c_veh_id else first_vehicle

            cat_id  = complaint_cat_ids[i] if i < len(complaint_cat_ids) else None
            cat_obj = ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None

            type_id_raw = complaint_type_ids[i] if i < len(complaint_type_ids) else ''
            ct_obj = None
            if type_id_raw:
                if type_id_raw.startswith('st_'):
                    pass
                else:
                    ct_obj = ComplaintType.objects.filter(pk=type_id_raw).first()

            tech_id = complaint_tech_ids[i] if i < len(complaint_tech_ids) else None
            tech_obj = Staff.objects.filter(pk=tech_id).first() if tech_id else None

            override_flag = (complaint_overrides[i] == '1') if i < len(complaint_overrides) else False

            EstimateComplaint.objects.create(
                estimate            = estimate,
                vehicle             = c_veh_obj,
                service_category    = cat_obj,
                category            = complaint_cat_texts[i] if i < len(complaint_cat_texts) else '',
                complaint_type_ref  = ct_obj,
                complaint_type      = 'customer',
                description         = c.strip(),
                type                = complaint_type_texts[i] if i < len(complaint_type_texts) else 'Mechanical',
                technician          = tech_obj,
                is_manual_override  = override_flag,
                status              = complaint_statuses[i] if i < len(complaint_statuses) else 'Open',
                order               = i,
            )
 
    # ── Technician Findings ───────────────────────────────
    technician_veh_ids = request.POST.getlist('technician_finding_vehicle_id[]')
    for i, f in enumerate(request.POST.getlist('technician_finding[]')):
        if f.strip():
            f_veh_id  = technician_veh_ids[i] if i < len(technician_veh_ids) else None
            f_veh_obj = WorkshopVehicle.objects.filter(pk=f_veh_id).first() if f_veh_id else first_vehicle

            EstimateComplaint.objects.create(
                estimate       = estimate,
                vehicle        = f_veh_obj,
                complaint_type = 'technician',
                description    = f.strip(),
                order          = i,
            )
 
    return estimate
 
 
# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_list(request):
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
 
    qs = Estimate.objects.select_related('customer','vehicle','jobcard').prefetch_related('vehicles__vehicle').filter(is_active=True)
 
    if q:
        qs = qs.filter(
            Q(estimate_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(jobcard__job_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
 
    all_est = Estimate.objects.filter(is_active=True)
    counts = {
        'total':    all_est.count(),
        'draft':    all_est.filter(status='draft').count(),
        'sent':     all_est.filter(status='sent').count(),
        'approved': all_est.filter(status='approved').count(),
        'rejected': all_est.filter(status='rejected').count(),
    }
 
    return render(request, 'jobcard_app/estimate_list.html', {
        'estimates': qs,
        'q':         q,
        'status':    status,
        'counts':    counts,
    })
 
 
# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_create(request):
    
    customers   = LedgerCreation.objects.filter(
                      groups_id=18).order_by('ledger_name')
    technicians = Staff.objects.filter(
                    status='Active',
                    staff_category__name='Technician').order_by('full_name')
    advisors = Staff.objects.filter(status='Active').order_by('full_name')
    categories = ServiceCategory.objects.filter(
                    is_active=True
                ).order_by('name')
    # Pre-fill from job card
    prefill_job = None
    jcid = request.GET.get('from_jobcard')
    if jcid:
        prefill_job = JobCard.objects.select_related(
            'customer', 'workshop_vehicle'
        ).filter(pk=jcid).first()
 
    if request.method == 'POST':
        est = _save_estimate(request)
        if est:
            messages.success(
                request,
                f"Estimate {est.estimate_number} saved!")
            return redirect('jobcard_app:estimate_list')
 
    from jobcard_app.utils import generate_voucher_number
    return render(request, 'jobcard_app/estimate_form.html', {
        'customers':   customers,
        'technicians': technicians,
        'advisors': advisors,      
        'categories': categories,
        'relational_mapping_json': json.dumps(_get_relational_mapping_dict()),

        'prefill_job': prefill_job,
        
        'next_voucher_no': generate_voucher_number('Estimate', Estimate, 'voucher_number', default_prefix='VCH-'),
        'today':       timezone.now().date(),
    })
 
 

 
# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_edit(request, pk):
    est         = get_object_or_404(Estimate, pk=pk)
    customers   = LedgerCreation.objects.filter(
                      groups_id=18).order_by('ledger_name')
    technicians = Staff.objects.filter(
                    status='Active',
                    staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    categories  = ServiceCategory.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        updated = _save_estimate(request, estimate=est)
        if updated:
            messages.success(
                request,
                f"Estimate {est.estimate_number} updated!")
            return redirect('jobcard_app:estimate_list')
 
    parts      = est.items.filter(item_type='part')
    labour     = est.items.filter(item_type='labour')
    complaints = est.complaints.filter(complaint_type='customer')
    findings   = est.complaints.filter(complaint_type='technician')
 
    return render(request, 'jobcard_app/estimate_form.html', {
        'estimate':    est,
        'customers':   customers,
        'technicians': technicians,
        'advisors':    advisors,
        'categories':  categories,
        'relational_mapping_json': json.dumps(_get_relational_mapping_dict()),
        'parts':       parts,
        'labour':      labour,
        'complaints':  complaints,
        'findings':    findings,
        'edit_mode':   True,
        'today':       timezone.now().date(),
    })
@login_required
def ajax_get_all_items(request):
    try:
        from item_master.models import Item
        qs = Item.objects.filter(
            isDeleted=False
        ).select_related('item_unit').order_by('item_name')

        result = [{
            'id':         str(i.id),
            'name':       i.item_name,
            'code':       i.item_code or '',
            'unit':       i.item_unit.unit_name if i.item_unit else 'No',
            'unit_price': float(i.sales_rate or 0),
        } for i in qs]
    except Exception as e:
        print('Items error:', e)
        result = []
    return JsonResponse({'items': result})
 
# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_delete(request, pk):
    est = get_object_or_404(Estimate, pk=pk)
    if request.method == 'POST':
        num = est.estimate_number
        est.is_active = False
        est.save()
        messages.success(request, f"Estimate {num} deleted.")
        return redirect('jobcard_app:estimate_list')
    return render(request, 'jobcard_app/estimate_confirm_delete.html',
                  {'est': est})

                  
@login_required
def ajax_get_jobcard_complaints(request):
    from .models import JobCard, JobCardComplaint

    jc_id = request.GET.get('jobcard_id', '').strip()
    customer_id = request.GET.get('customer_id', '').strip()

    if not customer_id:
        return JsonResponse({'jobcards': [], 'complaints': []})

    # ── Search job cards by customer ──────────────────────
    if not jc_id:
        jcs = JobCard.objects.filter(
            customer_id=customer_id,
            is_active=True
        ).select_related(
            'workshop_vehicle'
        ).order_by('-date')[:15]

        result = []
        for jc in jcs:
            complaints = list(
                jc.complaints.values(
                    'id', 'category', 'description',
                    'type', 'status'
                )
            )
            result.append({
                'id':           jc.id,
                'job_number':   jc.job_number,
                'date':         jc.date.strftime('%d %b %Y'),
                'vehicle':      str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
                'status':       jc.status,
                'complaints':   complaints,
                'count':        len(complaints),
            })
        return JsonResponse({'jobcards': result})

    # ── Get complaints for specific job card ──────────────
    jc = JobCard.objects.filter(pk=jc_id).first()
    if not jc:
        return JsonResponse({'complaints': []})

    complaints = list(
        jc.complaints.values(
            'id', 'category', 'description', 'type', 'status'
        )
    )
    return JsonResponse({'complaints': complaints, 'job_number': jc.job_number})
 
# ─────────────────────────────────────────────────────────────
# AJAX — search job cards for "Load from Job Card"
# ─────────────────────────────────────────────────────────────
@login_required
def jc_search_jobcards(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'jobcards': []})
 
    qs = JobCard.objects.select_related(
        'customer', 'workshop_vehicle'
    ).filter(is_active=True).filter(
        Q(job_number__icontains=q) |
        Q(customer__ledger_name__icontains=q) |
        Q(workshop_vehicle__registration_number__icontains=q)
    )[:10]
 
    result = []
    for jc in qs:
        result.append({
            'id':           jc.id,
            'job_number':   jc.job_number,
            'customer_id':  jc.customer_id,
            'customer_name': jc.customer.ledger_name,
            'vehicle_id':   jc.workshop_vehicle_id or '',
            'vehicle_name': str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
            'mileage':      jc.mileage or '',
            'vin':          '',
            'date':         jc.date.strftime('%d %b %Y'),
        })
    return JsonResponse({'jobcards': result})
 
 
# ─────────────────────────────────────────────────────────────
# AJAX — get vehicles by customer
# ─────────────────────────────────────────────────────────────
@login_required
def jc_get_vehicles(request):
    cid = request.GET.get('customer_id')

    if not cid:
        return JsonResponse({'vehicles': []})

    qs = WorkshopVehicle.objects.filter(
        customer_id=cid,
        is_active=True
    ).select_related('manufacturer', 'vehicle_model')

    result = []

    for v in qs:
        mfr_name  = v.manufacturer.manufacturer_name  if v.manufacturer   else ''
        mdl_name  = v.vehicle_model.model_name        if v.vehicle_model  else ''
        year      = v.year or ''
        reg_no    = v.registration_number or ''
        veh_no    = v.vehicle_number or ''

        vehicle_model_str = f"{mfr_name} {mdl_name}".strip()
        if year:
            vehicle_model_str += f" ({year})"

        # Label: vehicle_number · registration_number
        label_parts = [veh_no]
        if reg_no:
            label_parts.append(reg_no)
        label = ' · '.join(filter(None, label_parts))

        result.append({
            'id':                  v.id,
            'label':               label,
            'vehicle_number':      veh_no,
            'registration_number': reg_no,
            'make':                mfr_name,
            'model':               mdl_name,
            'year':                year,
            'vehicle_model':       vehicle_model_str,
            'mm_label':            vehicle_model_str,
            'manufacturer_id':     v.manufacturer_id  or '',
            'vehicle_model_id':    v.vehicle_model_id or '',
            'fuel_type':           v.fuel_type or '',
            'odometer':            v.odometer  or '',
        })

    return JsonResponse({'vehicles': result})
 
 
# ─────────────────────────────────────────────────────────────
# AJAX — search item master
# ─────────────────────────────────────────────────────────────
@login_required
def jc_get_items(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'items': []})
    try:
        from item_master.models import Item
        qs = Item.objects.filter(
            isDeleted=False
        ).filter(
            Q(item_name__icontains=q) |
            Q(item_code__icontains=q)
        ).select_related('item_unit')[:15]

        result = [{
            'id':         i.id,
            'name':       i.item_name,
            'code':       i.item_code or '',
            'unit':       i.item_unit.unit_name if i.item_unit else '',
            'unit_id':    i.item_unit.id if i.item_unit else '',
            'unit_price': float(i.sales_rate or 0),
        } for i in qs]
    except Exception as e:
        print('Item search error:', e)
        result = []
    return JsonResponse({'items': result})
# ─────────────────────────────────────────────────────────────────────────────
# PRIVATE HELPER — saves quotation from POST data
# ─────────────────────────────────────────────────────────────────────────────
def _save_quotation(request, quotation=None):
    from .models import Quotation, QuotationVehicle, QuotationItem, QuotationComplaint

    cid  = request.POST.get('customer')
    eid  = request.POST.get('loaded_estimate')
    jid  = request.POST.get('loaded_jobcard')
    aid  = request.POST.get('advisor')
    date = request.POST.get('date') or timezone.now().date()
    from fleet_app.models import Vouchers
    vt_id = request.POST.get('voucherType')
    quotation.voucherType = Vouchers    .objects.filter(pk=vt_id).first() if vt_id else None
    quotation.voucher_number = request.POST.get('voucher_number', '').strip() or None
    if not cid:
        messages.error(request, 'Customer is required.')        
        return None

    customer  = get_object_or_404(LedgerCreation, pk=cid)
    estimate  = Estimate.objects.filter(pk=eid).first() if eid else None
    jobcard   = JobCard.objects.filter(pk=jid).first()  if jid else None
    advisor   = Staff.objects.filter(pk=aid).first()    if aid else None

    if quotation is None:
        quotation = Quotation(created_by=request.user.id)

    quotation.customer    = customer
    quotation.estimate    = estimate
    quotation.jobcard     = jobcard
    quotation.advisor     = advisor
    quotation.date        = date
    quotation.status      = request.POST.get('status', 'draft')
    quotation.mileage     = request.POST.get('mileage') or None
    quotation.vin         = request.POST.get('vin', '') or ''
    quotation.tax_percent = request.POST.get('tax_percent') or 0
    quotation.discount    = request.POST.get('discount') or 0
    quotation.notes       = request.POST.get('notes', '')
    quotation.updated_by  = request.user.id
    quotation.save()

    # Clear old records
    quotation.vehicles.all().delete()
    quotation.items.all().delete()
    quotation.complaints.all().delete()

    # ── Vehicles ──────────────────────────────────────────────────────────────
    veh_ids      = request.POST.getlist('qt_vehicle_id[]')
    veh_mileages = request.POST.getlist('qt_vehicle_mileage[]')
    veh_notes    = request.POST.getlist('qt_vehicle_notes[]')
    first_vehicle = None
    seen_vehicles = set()
    for i, v_id in enumerate(veh_ids):
        if not v_id or v_id in seen_vehicles:
            continue
        seen_vehicles.add(v_id)
        veh = WorkshopVehicle.objects.filter(pk=v_id).first()
        if not veh:
            continue
        if first_vehicle is None:
            first_vehicle = veh
        QuotationVehicle.objects.create(
            quotation = quotation,
            vehicle   = veh,
            mileage   = veh_mileages[i] if i < len(veh_mileages) and veh_mileages[i] else None,
            notes     = veh_notes[i] if i < len(veh_notes) else '',
        )

    # Keep legacy header single-vehicle field in sync
    if first_vehicle:
        quotation.vehicle = first_vehicle
        qv_first = QuotationVehicle.objects.filter(quotation=quotation, vehicle=first_vehicle).first()
        if qv_first and qv_first.mileage:
            quotation.mileage = qv_first.mileage
    else:
        # Fallback to single vehicle input if legacy form was used
        vid = request.POST.get('vehicle')
        if vid:
            v_obj = WorkshopVehicle.objects.filter(pk=vid).first()
            if v_obj:
                quotation.vehicle = v_obj
                QuotationVehicle.objects.create(
                    quotation=quotation,
                    vehicle=v_obj,
                    mileage=request.POST.get('mileage') or None
                )
    quotation.save()

    # ── Parts ─────────────────────────────────────────────────────────────────
    part_ids = request.POST.getlist('part_item_id[]')
    descriptions = request.POST.getlist('description[]')
    units = request.POST.getlist('item_unit[]')
    quantities = request.POST.getlist('quantity[]')
    unit_prices = request.POST.getlist('unit_price[]')
    warranties = request.POST.getlist('part_warranty[]')
    part_vehs = request.POST.getlist('part_vehicle_id[]')

    max_len = max(len(part_ids), len(descriptions))
    for i in range(max_len):
        p_id = part_ids[i] if i < len(part_ids) else ''
        desc = descriptions[i] if i < len(descriptions) else ''

        if not desc.strip() and p_id:
            from item_master.models import ItemMaster, Item
            item_obj = ItemMaster.objects.filter(pk=p_id).first() or Item.objects.filter(pk=p_id).first()
            if item_obj:
                desc = getattr(item_obj, 'item_name', '') or str(item_obj)

        if not desc.strip() and not p_id:
            continue

        p_veh_id = part_vehs[i] if i < len(part_vehs) else None
        p_veh_obj = WorkshopVehicle.objects.filter(pk=p_veh_id).first() if p_veh_id else None

        QuotationItem.objects.create(
            quotation=quotation,
            vehicle=p_veh_obj,
            item_type='part',
            item_ref=p_id,
            description=desc.strip(),
            unit=units[i] if i < len(units) else '',
            quantity=quantities[i] if i < len(quantities) else 1,
            unit_price=unit_prices[i] if i < len(unit_prices) else 0,
            warranty=warranties[i] if i < len(warranties) else '',
            order=i,
        )

    # ── Labour ────────────────────────────────────────────────────────────────
    labour_descs = request.POST.getlist('labour_desc[]')
    labour_techs = request.POST.getlist('labour_tech[]')
    labour_hours = request.POST.getlist('labour_hrs[]')
    labour_rates = request.POST.getlist('labour_rate[]')
    labour_vehs  = request.POST.getlist('labour_vehicle_id[]')

    for i, desc in enumerate(labour_descs):
        if not desc.strip():
            continue
        tech = Staff.objects.filter(
            pk=labour_techs[i] if i < len(labour_techs) else None
        ).first()
        l_veh_id = labour_vehs[i] if i < len(labour_vehs) else None
        l_veh_obj = WorkshopVehicle.objects.filter(pk=l_veh_id).first() if l_veh_id else None

        QuotationItem.objects.create(
            quotation   = quotation,
            vehicle     = l_veh_obj,
            item_type   = 'labour',
            description = desc.strip(),
            technician  = tech,
            hours       = float(labour_hours[i]) if i < len(labour_hours) else 1,
            unit_price  = float(labour_rates[i]) if i < len(labour_rates) else 0,
            order       = i,
        )

    # ── Customer Complaints ───────────────────────────────────────────────────
    cmp_descs    = request.POST.getlist('complaint_description[]') or request.POST.getlist('customer_complaint[]')
    cmp_cat_ids  = request.POST.getlist('complaint_category_id[]') or request.POST.getlist('customer_complaint_cat[]')
    cmp_cat_txts = request.POST.getlist('complaint_category[]')
    cmp_type_ids = request.POST.getlist('complaint_type_id[]')
    cmp_types    = request.POST.getlist('complaint_type[]') or request.POST.getlist('customer_complaint_type[]')
    cmp_techs    = request.POST.getlist('complaint_technician[]')
    cmp_statuses = request.POST.getlist('complaint_status[]') or request.POST.getlist('customer_complaint_status[]')
    cmp_overrides= request.POST.getlist('complaint_manual_override[]')
    cmp_vehs     = request.POST.getlist('complaint_vehicle_id[]') or request.POST.getlist('customer_complaint_vehicle_id[]')

    from .models import ComplaintType, ServiceType

    for i, c in enumerate(cmp_descs):
        if c.strip():
            cat_id = cmp_cat_ids[i] if i < len(cmp_cat_ids) else None
            cat_obj = ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None
            c_veh_id = cmp_vehs[i] if i < len(cmp_vehs) else None
            c_veh_obj = WorkshopVehicle.objects.filter(pk=c_veh_id).first() if c_veh_id else None

            tech_id = cmp_techs[i] if i < len(cmp_techs) else None
            tech_obj = Staff.objects.filter(pk=tech_id).first() if tech_id else None

            type_val_raw = cmp_type_ids[i] if i < len(cmp_type_ids) else ''
            ct_ref = None
            st_ref = None
            if type_val_raw:
                if str(type_val_raw).startswith('st_'):
                    st_id = type_val_raw.replace('st_', '')
                    st_ref = ServiceType.objects.filter(pk=st_id).first()
                else:
                    ct_ref = ComplaintType.objects.filter(pk=type_val_raw).first()

            is_override = bool(cmp_overrides[i] == '1') if i < len(cmp_overrides) else False

            QuotationComplaint.objects.create(
                quotation          = quotation,
                vehicle            = c_veh_obj,
                complaint_type     = 'customer',
                description        = c.strip(),
                service_category   = cat_obj,
                category           = cmp_cat_txts[i] if i < len(cmp_cat_txts) else (cat_obj.name if cat_obj else ''),
                type               = cmp_types[i] if i < len(cmp_types) else 'Mechanical',
                technician         = tech_obj,
                complaint_type_ref = ct_ref,
                service_type_ref   = st_ref,
                is_manual_override = is_override,
                status             = cmp_statuses[i] if i < len(cmp_statuses) else 'Open',
                order              = i,
            )

    # ── Technician Findings ───────────────────────────────────────────────────
    for i, f in enumerate(request.POST.getlist('technician_finding[]')):
        if f.strip():
            QuotationComplaint.objects.create(
                quotation      = quotation,
                complaint_type = 'technician',
                description    = f.strip(),
                order          = i,
            )

    return quotation


# ─────────────────────────────────────────────────────────────────────────────
# AJAX — get customer estimates for selection
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def ajax_get_customer_estimates(request):
    customer_id = request.GET.get('customer_id', '').strip()
    est_id = request.GET.get('estimate_id', '').strip()

    if est_id:
        est = Estimate.objects.filter(pk=est_id, is_active=True).first()
        if not est:
            return JsonResponse({'estimates': []})
        return JsonResponse({'estimates': [{
            'id': est.id,
            'estimate_number': est.estimate_number,
            'date': est.date.strftime('%d %b %Y'),
            'customer': str(getattr(est.customer, 'customer_name', None) or getattr(est.customer, 'ledger_name', '')),
            'vehicle': str(est.vehicle) if est.vehicle else '',
            'grand_total': f"{est.get_grand_total():.3f}",
        }]})

    qs = Estimate.objects.filter(is_active=True).select_related('customer', 'vehicle')
    if customer_id:
        qs = qs.filter(customer_id=customer_id)

    estimates = qs.order_by('-created_on')[:25]

    result = []
    for est in estimates:
        cust_name = getattr(est.customer, 'customer_name', None) or getattr(est.customer, 'ledger_name', '')
        result.append({
            'id': est.id,
            'estimate_number': est.estimate_number,
            'date': est.date.strftime('%d %b %Y'),
            'customer': str(cust_name),
            'vehicle': str(est.vehicle) if est.vehicle else '',
            'grand_total': f"{est.get_grand_total():.3f}",
        })

    return JsonResponse({'estimates': result})


# ─────────────────────────────────────────────────────────────────────────────
# AJAX — get estimate data for auto-fill into quotation
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def jc_get_estimate_data(request):
    eid = request.GET.get('estimate_id')
    if not eid:
        return JsonResponse({'found': False})

    try:
        est = Estimate.objects.prefetch_related(
            'items', 'complaints'
        ).get(pk=eid, is_active=True)
    except Estimate.DoesNotExist:
        return JsonResponse({'found': False})

    parts = [{
        'description': i.description,
        'item_ref':    i.item_ref or '',
        'unit':        i.unit or '',
        'quantity':    float(i.quantity),
        'unit_price':  float(i.unit_price),
        'warranty':    i.warranty or '',
    } for i in est.items.filter(item_type='part')]

    labour = [{
        'description':   i.description,
        'technician_id': i.technician_id or '',
        'hours':         float(i.hours or 1),
        'unit_price':    float(i.unit_price),
    } for i in est.items.filter(item_type='labour')]

    complaints = [c.description for c in est.complaints.filter(complaint_type='customer')]
    findings   = [c.description for c in est.complaints.filter(complaint_type='technician')]

    return JsonResponse({
        'found':       True,
        'estimate_id': est.id,
        'est_number':  est.estimate_number,
        'customer_id': est.customer_id,
        'vehicle_id':  est.vehicle_id or '',
        'jobcard_id':  est.jobcard_id or '',
        'advisor_id':  est.advisor_id or '',
        'mileage':     est.mileage or '',
        'vin':         est.vin or '',
        'tax_percent': float(est.tax_percent or 0),
        'discount':    float(est.discount or 0),
        'notes':       est.notes or '',
        'parts':       parts,
        'labour':      labour,
        'complaints':  complaints,
        'findings':    findings,
    })


# ─────────────────────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def quotation_list(request):
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    qs = Quotation.objects.select_related(
        'customer', 'vehicle', 'estimate', 'jobcard'
    )

    if q:
        qs = qs.filter(
            Q(quotation_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(estimate__estimate_number__icontains=q) |
            Q(jobcard__job_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    all_q  = Quotation.objects.filter()
    counts = {
        'total':    all_q.count(),
        'draft':    all_q.filter(status='draft').count(),
        'sent':     all_q.filter(status='sent').count(),
        'approved': all_q.filter(status='approved').count(),
        'rejected': all_q.filter(status='rejected').count(),
    }

    return render(request, 'jobcard_app/quotation_list.html', {
        'quotations': qs,
        'q':          q,
        'status':     status,
        'counts':     counts,
    })


# ─────────────────────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def quotation_create(request):
    customers   = LedgerCreation.objects.filter(
        groups_id=18).order_by('ledger_name')
    technicians = Staff.objects.filter(
        status='Active',
        staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    estimates   = Estimate.objects.filter(
        is_active=True).select_related('customer').order_by('-created_on')[:50]

    # Pre-fill from estimate
    prefill_est = None
    eid = request.GET.get('from_estimate')
    if eid:
        prefill_est = Estimate.objects.select_related(
            'customer', 'vehicle'
        ).prefetch_related('items', 'complaints', 'vehicles__vehicle').filter(pk=eid).first()

    # Pre-fill from job card
    prefill_job = None
    jcid = request.GET.get('from_jobcard')
    if jcid:
        prefill_job = JobCard.objects.select_related(
            'customer', 'workshop_vehicle'
        ).prefetch_related('vehicles__vehicle').filter(pk=jcid).first()

    if request.method == 'POST':
        quot = _save_quotation(request)
        if quot:
            messages.success(
                request,
                f"Quotation {quot.quotation_number} saved!")
            return redirect('jobcard_app:quotation_detail', pk=quot.pk)

    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    categories  = ServiceCategory.objects.filter(is_active=True).order_by('name')
    from jobcard_app.utils import generate_voucher_number
    return render(request, 'jobcard_app/quotation_form.html', {
        'customers':   customers,
        'technicians': technicians,
        'advisors':    advisors,
        'estimates':   estimates,
        'categories':  categories,
        'prefill_est': prefill_est,
        'prefill_job': prefill_job,
        'next_qt_no':  generate_voucher_number('Quotation', Quotation, 'quotation_number', default_prefix='QT-'),
        'today':       timezone.now().date(),
        'relational_mapping_json': json.dumps(_get_relational_mapping_dict()),
    })


# ─────────────────────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def quotation_detail(request, pk):
    quot = get_object_or_404(
        Quotation.objects.select_related(
            'customer', 'vehicle', 'estimate', 'jobcard', 'advisor'
        ).prefetch_related('vehicles__vehicle', 'items__technician', 'items__vehicle', 'complaints__vehicle', 'complaints__technician', 'complaints__service_category'),
        pk=pk
    )
    return render(request, 'jobcard_app/quotation_detail.html', {
        'quotation':  quot,
        'parts':      quot.parts(),
        'labour':     quot.labour(),
        'complaints': quot.complaints_customer(),
        'findings':   quot.findings_technician(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def quotation_edit(request, pk):
    quot        = get_object_or_404(
        Quotation.objects.prefetch_related('vehicles__vehicle', 'items', 'complaints'),
        pk=pk
    )
    customers   = LedgerCreation.objects.filter(
        groups_id=18).order_by('ledger_name')
    technicians = Staff.objects.filter(
        status='Active',
        staff_category__name='Technician').order_by('full_name')
    estimates   = Estimate.objects.filter(
        is_active=True).select_related('customer').order_by('-created_on')[:50]

    if request.method == 'POST':
        updated = _save_quotation(request, quotation=quot)
        if updated:
            messages.success(
                request,
                f"Quotation {quot.quotation_number} updated!")
            return redirect('jobcard_app:quotation_detail', pk=pk)

    categories  = ServiceCategory.objects.filter(is_active=True).order_by('name')
    return render(request, 'jobcard_app/quotation_form.html', {
        'quotation':   quot,
        'customers':   customers,
        'technicians': technicians,
        'estimates':   estimates,
        'categories':  categories,
        'parts':       quot.parts(),
        'labour':      quot.labour(),
        'complaints':  quot.complaints_customer(),
        'findings':    quot.findings_technician(),
        'edit_mode':   True,
        'today':       timezone.now().date(),
        'relational_mapping_json': json.dumps(_get_relational_mapping_dict()),
    })


# ─────────────────────────────────────────────────────────────────────────────
# DELETE (soft)
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def quotation_delete(request, pk):
    quot = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        num = quot.quotation_number
        quot.delete()
        messages.success(request, f"Quotation {num} deleted.")
        return redirect('jobcard_app:quotation_list')
    return render(request, 'jobcard_app/quotation_confirm_delete.html',
                  {'quot': quot})


@login_required
def quotation_status_update(request, pk):
    quot = get_object_or_404(Quotation, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = dict(Quotation.STATUS_CHOICES)
        if new_status in valid_statuses:
            quot.status = new_status
            quot.save(update_fields=['status'])
            messages.success(request, f"Quotation {quot.quotation_number} marked as {valid_statuses[new_status]}.")
        else:
            messages.error(request, 'Invalid status value.')
    return redirect('jobcard_app:quotation_detail', pk=pk)

def get_next_quotation_number(request):
    """AJAX view to get next quotation voucher number"""
    from fleet_app.models import Vouchers
    from jobcard_app.utils import generate_voucher_number
    from .models import Quotation

    voucher_type_id = request.GET.get('voucher_type_id')
    if voucher_type_id:
        try:
            vt = Vouchers.objects.get(pk=voucher_type_id)
            num = vt.get_next_voucher_number(Quotation, 'voucher_number')
            return JsonResponse({'job_number': num, 'success': True})
        except Vouchers.DoesNotExist:
            pass

    next_num = generate_voucher_number('Quotation', Quotation, 'voucher_number', default_prefix='QUA-')
    return JsonResponse({'job_number': next_num, 'success': True})
# ─────────────────────────────────────────────────────────────
# VEHICLE LIST
# ─────────────────────────────────────────────────────────────
def wv_list(request):
    q           = request.GET.get('q', '').strip()
    customer_id = request.GET.get('customer', '')
    fuel_filter = request.GET.get('fuel', '')

    vehicles = WorkshopVehicle.objects.select_related(
        'customer', 'vehicle_type', 'manufacturer', 'vehicle_model'
    ).filter(is_active=True)

    if q:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=q) |
            Q(vehicle_number__icontains=q)      |
            Q(manufacturer__manufacturer_name__icontains=q) |
            Q(vehicle_model__model_name__icontains=q)       |
            Q(chassis_number__icontains=q)      |
            Q(engine_number__icontains=q)       |
            Q(customer__ledger_name__icontains=q)
        )
    if customer_id:
        vehicles = vehicles.filter(customer_id=customer_id)
    if fuel_filter:
        vehicles = vehicles.filter(fuel_type=fuel_filter)

    customers  = LedgerCreation.objects.filter(
        groups_id=18).order_by('ledger_name')
    all_v      = WorkshopVehicle.objects.filter(is_active=True)

    counts = {
        'total':    all_v.count(),
        'active':   all_v.filter(status='active').count(),
        'svc_due':  sum(1 for v in all_v
                        if v.get_service_status() in ('overdue', 'due_soon')),
        'ins_exp':  sum(1 for v in all_v
                        if v.get_insurance_status() in ('expired', 'expiring')),
        'reg_exp':  sum(1 for v in all_v
                        if v.get_registration_status() in ('expired', 'expiring')),
    }

    return render(request, 'jobcard_app/wv_list.html', {
        'vehicles':     vehicles,
        'customers':    customers,
        'q':            q,
        'customer_id':  customer_id,
        'fuel_filter':  fuel_filter,
        'fuel_choices': WorkshopVehicle.FUEL_CHOICES,
        'counts':       counts,
    })


# ─────────────────────────────────────────────────────────────
# VEHICLE CREATE
# customer_id optional — comes from "Add Vehicle" in customer list
# ─────────────────────────────────────────────────────────────
def wv_create(request, customer_id=None):
    customers     = LedgerCreation.objects.filter(groups_id=18).order_by('ledger_name')
    vehicle_types = VehicleCategory.objects.all().order_by('category_name')

    preselected = None
    if customer_id:
        preselected = get_object_or_404(LedgerCreation, id=customer_id)

    if request.method == 'POST':
        cid   = request.POST.get('customer')
        vnum  = request.POST.get('vehicle_number', '').strip()
        vtype = request.POST.get('vehicle_type') or None
        mfr_id = request.POST.get('manufacturer') or None
        model_id = request.POST.get('vehicle_model') or None
        reg   = request.POST.get('registration_number', '').strip()

        errors = []
        if not cid:
            errors.append('Please select a customer.')
        if not vnum:
            errors.append('Vehicle number is required.')
        elif WorkshopVehicle.objects.filter(
                vehicle_number__iexact=vnum, is_active=True).exists():
            errors.append(f"Vehicle number '{vnum}' already exists.")
        if not mfr_id:
            errors.append('Manufacturer is required.')
        if not model_id:
            errors.append('Model is required.')
        if not reg:
            errors.append('Registration number is required.')
        if WorkshopVehicle.objects.filter(
                registration_number__iexact=reg, is_active=True).exists():
            errors.append(f"Vehicle with plate '{reg}' already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'jobcard_app/wv_form.html', {
                'customers':     customers,
                'vehicle_types': vehicle_types,
                'preselected':   preselected,
                'fuel_choices':  WorkshopVehicle.FUEL_CHOICES,
                'today':         timezone.now().date(),
                'post':          request.POST,
            })

        customer = get_object_or_404(LedgerCreation, id=cid)

        v = WorkshopVehicle(
            customer             = customer,
            vehicle_number       = vnum,
            vehicle_type_id      = vtype,
            manufacturer_id      = mfr_id,
            vehicle_model_id     = model_id,
            registration_number  = reg,
            chassis_number       = request.POST.get('chassis_number')       or None,
            engine_number        = request.POST.get('engine_number')        or None,
            year                 = request.POST.get('year')                 or None,
            color                = request.POST.get('color')                or None,
            fuel_type            = request.POST.get('fuel_type')            or None,
            odometer             = request.POST.get('odometer')             or None,
            notes                = request.POST.get('notes', ''),
            status               = request.POST.get('status', 'active'),

            registration_date        = request.POST.get('registration_date')        or None,
            registration_expiry_date = request.POST.get('registration_expiry_date') or None,
            insurance_policy_number  = request.POST.get('insurance_policy_number')  or None,
            insurance_expiry_date    = request.POST.get('insurance_expiry_date')     or None,
            last_service_date        = request.POST.get('last_service_date')        or None,
            next_service_date        = request.POST.get('next_service_date')        or None,
            service_interval         = request.POST.get('service_interval')         or None,

            created_by = request.user.id,
        )
        if request.FILES.get('vehicle_image'):
            v.vehicle_image = request.FILES['vehicle_image']
        v.save()

        messages.success(
            request,
            f"Vehicle {v.vehicle_number} — {v.registration_number} registered successfully!")
        return redirect('jobcard_app:wv_list')

    return render(request, 'jobcard_app/wv_form.html', {
        'customers':     customers,
        'vehicle_types': vehicle_types,
        'preselected':   preselected,
        'fuel_choices':  WorkshopVehicle.FUEL_CHOICES,
        'today':         timezone.now().date(),
    })

# ─────────────────────────────────────────────────────────────
# VEHICLE EDIT
# ─────────────────────────────────────────────────────────────
def wv_edit(request, pk):
    v             = get_object_or_404(WorkshopVehicle, pk=pk)
    customers     = LedgerCreation.objects.filter(groups_id=18).order_by('ledger_name')
    vehicle_types = VehicleCategory.objects.all().order_by('category_name')

    if request.method == 'POST':
        mfr_id   = request.POST.get('manufacturer') or None
        model_id = request.POST.get('vehicle_model') or None

        if not mfr_id or not model_id:
            messages.error(request, 'Manufacturer and Model are required.')
            return render(request, 'jobcard_app/wv_form.html', {
                'v':             v,
                'customers':     customers,
                'vehicle_types': vehicle_types,
                'fuel_choices':  WorkshopVehicle.FUEL_CHOICES,
                'today':         timezone.now().date(),
                'edit_mode':     True,
                'post':          request.POST,
            })

        v.vehicle_type_id      = request.POST.get('vehicle_type') or None
        v.manufacturer_id      = mfr_id
        v.vehicle_model_id     = model_id
        v.chassis_number       = request.POST.get('chassis_number')       or None
        v.engine_number        = request.POST.get('engine_number')        or None
        v.year                 = request.POST.get('year')                 or None
        v.color                = request.POST.get('color')                or None
        v.fuel_type            = request.POST.get('fuel_type')            or None
        v.odometer             = request.POST.get('odometer')             or None
        v.notes                = request.POST.get('notes', '')
        v.status               = request.POST.get('status', 'active')

        v.registration_date        = request.POST.get('registration_date')        or None
        v.registration_expiry_date = request.POST.get('registration_expiry_date') or None
        v.insurance_policy_number  = request.POST.get('insurance_policy_number')  or None
        v.insurance_expiry_date    = request.POST.get('insurance_expiry_date')     or None
        v.last_service_date        = request.POST.get('last_service_date')        or None
        v.next_service_date        = request.POST.get('next_service_date')        or None
        v.service_interval         = request.POST.get('service_interval')         or None

        if request.FILES.get('vehicle_image'):
            v.vehicle_image = request.FILES['vehicle_image']
        v.save()

        messages.success(request, f"Vehicle {v.vehicle_number} updated successfully.")
        return redirect('jobcard_app:wv_list')

    return render(request, 'jobcard_app/wv_form.html', {
        'v':             v,
        'customers':     customers,
        'vehicle_types': vehicle_types,
        'fuel_choices':  WorkshopVehicle.FUEL_CHOICES,
        'today':         timezone.now().date(),
        'edit_mode':     True,
    })

# ─────────────────────────────────────────────────────────────
# VEHICLE DELETE
# ─────────────────────────────────────────────────────────────
def wv_delete(request, pk):
    v = get_object_or_404(WorkshopVehicle, pk=pk)
    if request.method == 'POST':
        num = v.vehicle_number
        reg = v.registration_number
        v.is_active = False  # soft delete
        v.save()
        messages.success(request, f"Vehicle {num} — {reg} removed.")
        return redirect('jobcard_app:wv_list')
    return render(request,
                  'jobcard_app/wv_confirm_delete.html',
                  {'v': v})


# ─────────────────────────────────────────────────────────────
# AJAX — get vehicles by customer
# used in job card form, inspection form dropdowns
# ─────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
# AJAX — search vehicles (for quick lookup)
# ─────────────────────────────────────────────────────────────
def ajax_wv_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'vehicles': []})

    qs = WorkshopVehicle.objects.filter(
        is_active=True, status='active'
    ).filter(
        Q(registration_number__icontains=q) |
        Q(make__icontains=q)                |
        Q(model__icontains=q)               |
        Q(vehicle_number__icontains=q)
    ).select_related('customer')[:10]

    result = [{
        'id':           v.id,
        'vehicle_number': v.vehicle_number,
        'reg':          v.registration_number,
        'make':         v.make,
        'model':        v.model,
        'year':         v.year or '',
        'customer':     v.customer.ledger_name,
        'odometer':     v.odometer or '',
        'fuel':         v.fuel_type or '',
    } for v in qs]

    return JsonResponse({'vehicles': result})   




# ═══════════════════════════════════════════════════════
# DELIVERY NOTE

from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from accounts_app.models import LedgerCreation
from .models import (
    DeliveryNote, DeliveryService, DeliveryPart, DeliveryLabour,
    
)


# ─────────────────────────────────────────────────────────────
# CONTEXT HELPER — checklist items
# ─────────────────────────────────────────────────────────────
def _checklist_items():
    return [
        ('work_completed',     'Work Completed'),
        ('quality_checked',    'Quality Checked'),
        ('road_test',          'Road Test Completed'),
        ('vehicle_washed',     'Vehicle Washed'),
        ('spare_wheel',        'Spare Wheel Available'),
        ('tool_kit',           'Tool Kit Available'),
        ('documents_returned', 'Documents Returned'),
    ]


# ─────────────────────────────────────────────────────────────
# HELPER — save delivery note from POST
# ─────────────────────────────────────────────────────────────
def _save_delivery(request, dn=None):
    from item_master.models import Item, Stock, CostCenter
    from item_master.common import upsert_stock, to_base_qty
    from django.utils import timezone
    from fleet_app.models import Vouchers

    cid = request.POST.get('customer')
    if not cid:
        messages.error(request, 'Customer is required.')
        return None

    customer    = get_object_or_404(LedgerCreation, pk=cid)
    vt_id = request.POST.get('voucherType')
    jobcard_id = request.POST.get('loaded_jobcard')
    jobcard = None
    if jobcard_id:
            jobcard = JobCard.objects.filter(id=jobcard_id).first()

    quotation_id = request.POST.get('loaded_quotation')

    quotation = None
    if quotation_id:
        quotation = Quotation.objects.filter(id=quotation_id).first()
          
    estimate_id = request.POST.get('loaded_estimate')

    estimate = None
    if estimate_id:
        estimate = Estimate.objects.filter(id=estimate_id).first()
    advisor_id = request.POST.get('advisor')
    advisor    = Staff.objects.filter(pk=advisor_id).first() if advisor_id else None
    technician_id = request.POST.get('technician')

    technician = None
    if technician_id:
        technician = Staff.objects.filter(
            id=technician_id
        ).first()
   
 
   

    
    if dn is None:
        dn = DeliveryNote(created_by=request.user.id)

    # ── Header ────────────────────────────────────────────────
    dn.customer         = customer
    
    # ── Voucher type: default to 'Delivery Note' voucher if not sent ────
    if vt_id:
        dn.voucherType = Vouchers.objects.filter(pk=vt_id).first()
    elif not dn.voucherType_id:
        dn.voucherType = Vouchers.objects.filter(VoucherName='Delivery Note').first()

    # ── Auto-generate voucher number if blank on create ─────────────────
    raw_voucher_number = request.POST.get('voucher_number', '').strip()
    if raw_voucher_number:
        dn.voucher_number = raw_voucher_number
    elif not dn.pk:  # new record
        from jobcard_app.utils import generate_voucher_number
        dn.voucher_number = generate_voucher_number('Delivery Note', DeliveryNote, 'voucher_number', default_prefix='DN-')
    dn.jobcard         = jobcard
    dn.quotation        = quotation
    dn.estimate         = estimate
    dn.advisor          = advisor
    dn.technician       = technician
    dn.date             = request.POST.get('date') or timezone.now().date()
    dn.delivery_time    = request.POST.get('delivery_time') or None
    dn.status           = request.POST.get('status', 'draft')
    dn.payment_mode     = request.POST.get('payment_mode') or None
    dn.contact_number   = request.POST.get('contact_number', '')
    dn.vehicle_type     = request.POST.get('vehicle_type', '')
    dn.reg_number       = request.POST.get('reg_number', '')
    dn.driver_name      = request.POST.get('driver_name', '')
    dn.header_remarks   = request.POST.get('header_remarks', '')

    # ── Vehicle condition ─────────────────────────────────────
    dn.exterior_condition  = request.POST.get('exterior_condition', '')
    dn.interior_condition  = request.POST.get('interior_condition', '')
    dn.fuel_level_out      = request.POST.get('fuel_level_out', '')
    dn.accessories_returns = request.POST.get('accessories_returns', '')
    dn.vehicle_cleanliness = request.POST.get('vehicle_cleanliness', '')
    dn.odometer_out        = request.POST.get('odometer_out') or None
    dn.condition_remarks   = request.POST.get('condition_remarks', '')

    # ── Checklist ─────────────────────────────────────────────
    dn.work_completed     = 'work_completed'     in request.POST
    dn.quality_checked    = 'quality_checked'    in request.POST
    dn.road_test          = 'road_test'          in request.POST
    dn.vehicle_washed     = 'vehicle_washed'     in request.POST
    dn.spare_wheel        = 'spare_wheel'        in request.POST
    dn.tool_kit           = 'tool_kit'           in request.POST
    dn.documents_returned = 'documents_returned' in request.POST

    # ── Financials ────────────────────────────────────────────
    dn.discount          = request.POST.get('discount') or 0
    dn.tax_percent       = request.POST.get('tax_percent') or 0
    dn.advance_received  = request.POST.get('advance_received') or 0
    dn.notes             = request.POST.get('notes', '')
    dn.customer_signed   = 'customer_signed' in request.POST
    dn.save()
    dn.vehicles.all().delete()
    dn_veh_ids      = request.POST.getlist('dn_vehicle_id[]')
    dn_veh_mileages = request.POST.getlist('dn_vehicle_mileage[]')
    dn_veh_notes    = request.POST.getlist('dn_vehicle_notes[]')
    first_vehicle = None
    seen_vehicles = set()
    for i, v_id in enumerate(dn_veh_ids):
        if not v_id or v_id in seen_vehicles:
            continue
        seen_vehicles.add(v_id)
        veh = WorkshopVehicle.objects.filter(pk=v_id).first()
        if not veh:
            continue
        if first_vehicle is None:
            first_vehicle = veh
        DeliveryNoteVehicle.objects.create(
            delivery_note = dn,
            vehicle       = veh,
            mileage       = dn_veh_mileages[i] if i < len(dn_veh_mileages) and dn_veh_mileages[i] else None,
            notes         = dn_veh_notes[i] if i < len(dn_veh_notes) else '',
        )

    dn.vehicle = first_vehicle
    dn.save(update_fields=['vehicle'])

    # ── Completed Services ────────────────────────────────────
    dn.services.all().delete()
    svc_descs    = request.POST.getlist('svc_description[]')
    svc_qtys     = request.POST.getlist('svc_qty[]')
    svc_statuses = request.POST.getlist('svc_status[]')
    svc_remarks  = request.POST.getlist('svc_remarks[]')
    svc_vehs     = request.POST.getlist('svc_vehicle_id[]')
    for i, desc in enumerate(svc_descs):
        if desc.strip():
            v_id  = svc_vehs[i] if i < len(svc_vehs) and svc_vehs[i] else None
            v_obj = WorkshopVehicle.objects.filter(pk=v_id).first() if v_id else None
            DeliveryService.objects.create(
                delivery_note = dn,
                vehicle       = v_obj,
                description   = desc.strip(),
                quantity      = float(svc_qtys[i]) if i < len(svc_qtys) and svc_qtys[i] else 1,
                status        = svc_statuses[i] if i < len(svc_statuses) else 'Completed',
                remarks       = svc_remarks[i] if i < len(svc_remarks) else '',
                order         = i,
            )

    dn_vt = dn.voucherType or Vouchers.objects.filter(VoucherName='Delivery Note').first()
    if dn_vt and dn.pk:
        Stock.objects.filter(voucherType=dn_vt, voucherNo=dn.id).delete()

    dn.parts.all().delete()

    # ── Save new part rows ────────────────────────────────
    part_item_ids = request.POST.getlist('part_item_id[]')
    part_names    = request.POST.getlist('part_name[]')
    part_numbers  = request.POST.getlist('part_number[]')
    part_qtys     = request.POST.getlist('part_qty[]')
    part_units    = request.POST.getlist('part_unit[]')
    part_rates    = request.POST.getlist('part_rate[]')
    part_vehs     = request.POST.getlist('part_vehicle_id[]')

    max_parts = max(len(part_item_ids), len(part_names), len(part_numbers), len(part_vehs))
    default_cost_center = CostCenter.objects.filter(isDefault=True).first() or CostCenter.objects.first()
    for i in range(max_parts):
        item_id  = part_item_ids[i] if i < len(part_item_ids) else None
        item_obj = Item.objects.filter(pk=item_id).first() if item_id else None
        name     = part_names[i] if i < len(part_names) else ''
        part_no  = part_numbers[i] if i < len(part_numbers) else ''
        v_id     = part_vehs[i] if i < len(part_vehs) and part_vehs[i] else None
        v_obj    = WorkshopVehicle.objects.filter(pk=v_id).first() if v_id else None

        if not name.strip() and item_obj:
            name = item_obj.item_name
        if not part_no.strip() and item_obj:
            part_no = item_obj.item_code or ''

        if not name.strip() and not item_id:
            continue

        qty  = float(part_qtys[i])  if i < len(part_qtys) and part_qtys[i]   else 1
        rate = float(part_rates[i]) if i < len(part_rates) and part_rates[i] else 0

        DeliveryPart.objects.create(
            delivery_note = dn,
            vehicle       = v_obj,
            item          = item_obj,
            name          = name.strip() or (item_obj.item_name if item_obj else 'Part'),
            item_code     = part_no.strip(),
            quantity      = qty,
            unit          = part_units[i] if i < len(part_units) else 'No',
            rate          = rate,
            order         = i,
        )

        # ── Deduct from stock ─────────────────────────────
        if item_obj and dn_vt:
            try:
                cost_center = item_obj.cost_center or default_cost_center
                base_qty = to_base_qty(item_obj, item_obj.item_unit_id, Decimal(str(qty)))
                upsert_stock(
                    item=item_obj,
                    batch_id=None,
                    base_unit_id=item_obj.item_unit_id,
                    base_qty_delta=-base_qty,
                    rate=Decimal(str(rate)),
                    voucher_date=dn.delivery_date or timezone.now().date(),
                    voucher_type=dn_vt,
                    voucher_id=dn.id,
                    cost_center=cost_center,
                )
            except Exception as e:
                print(f'Stock deduct error for item {item_obj.id}: {e}')

    # ── Save Labour Charges ────────────────────────────────
    dn.labours.all().delete()
    lab_descs = request.POST.getlist('labour_desc[]')
    lab_hrs   = request.POST.getlist('labour_hrs[]')
    lab_rates = request.POST.getlist('labour_rate[]')
    lab_techs = request.POST.getlist('labour_technician[]')
    lab_vehs  = request.POST.getlist('labour_vehicle_id[]')

    for i, desc in enumerate(lab_descs):
        if desc.strip():
            hrs  = float(lab_hrs[i])   if i < len(lab_hrs)   and lab_hrs[i]   else 1
            rate = float(lab_rates[i]) if i < len(lab_rates) and lab_rates[i] else 0
            tech_id = lab_techs[i] if i < len(lab_techs) and lab_techs[i] else None
            tech_obj = None
            if tech_id:
                tech_obj = Staff.objects.filter(id=tech_id).first()
            v_id  = lab_vehs[i] if i < len(lab_vehs) and lab_vehs[i] else None
            v_obj = WorkshopVehicle.objects.filter(pk=v_id).first() if v_id else None
            DeliveryLabour.objects.create(
                delivery_note = dn,
                vehicle       = v_obj,
                technician    = tech_obj,
                description   = desc.strip(),
                hours         = hrs,
                rate          = rate,
                amount        = hrs * rate,
                order         = i,
            )

    return dn



# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_list(request):
    q      = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')

    deliveries = DeliveryNote.objects.select_related(
        'customer', 'jobcard', 'quotation', 'advisor', 'technician'
    ).prefetch_related('vehicles__vehicle').filter(is_active=True)

    if q:
        deliveries = deliveries.filter(
            Q(voucher_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(jobcard__job_number__icontains=q) |
            Q(quotation__quotation_number__icontains=q)
        )

    if status:
        deliveries = deliveries.filter(status=status)

    deliveries = deliveries.order_by('-created_on')

    return render(request, 'jobcard_app/delivery_list.html', {
        'deliveries': deliveries,
        'q': q,
        'status': status,
    })

# ─────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_detail(request, pk):
    dn = get_object_or_404(
        DeliveryNote.objects.select_related(
            'customer', 'vehicle', 'jobcard', 'quotation', 'estimate', 'advisor', 'technician'
        ).prefetch_related(
            'vehicles__vehicle',
            'services__vehicle',
            'parts__vehicle',
            'labours__vehicle', 'labours__technician'
        ),
        pk=pk
    )
    return render(request, 'jobcard_app/delivery_detail.html', {
        'dn':                dn,
        'vehicles':          dn.vehicles.all(),
        'services':          dn.services.all(),
        'parts':             dn.parts.all(),
        'labour':            dn.labours.all(),
        'vehicle_breakdown': dn.get_vehicle_breakdown(),
    })

# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_create(request):
    customers   = LedgerCreation.objects.filter(
                      groups_id=18).order_by('ledger_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    technicians = Staff.objects.filter(
                      status='Active',
                      staff_category__name='Technician').order_by('full_name')
    # Pre-fill from job card
    prefill_jc = None
    jcid = request.GET.get('from_jobcard')
    if jcid:
        prefill_jc = JobCard.objects.select_related(
            'customer', 'workshop_vehicle',
            'advisor'
        ).prefetch_related(
            'complaints', 'parts', 'labours', 'vehicles__vehicle'
        ).filter(pk=jcid).first()

    # Pre-fill from quotation
    prefill_quotation = None
    qid = request.GET.get('from_quotation')
    if qid:
        prefill_quotation = Quotation.objects.select_related(
            'customer', 'vehicle', 'advisor'
        ).prefetch_related(
            'items', 'complaints', 'vehicles__vehicle'
        ).filter(pk=qid).first()

    if request.method == 'POST':
        dn = _save_delivery(request)
        if dn:
            messages.success(
                request,
                f"Delivery Note {dn.voucher_number} saved!")
            return redirect('jobcard_app:delivery_detail', pk=dn.pk)

    from jobcard_app.utils import generate_voucher_number
    from fleet_app.models import Vouchers
    dn_voucher_type = Vouchers.objects.filter(VoucherName='Delivery Note').first()
    return render(request, 'jobcard_app/delivery_form.html', {
        'customers':           customers,
        'advisors':            advisors,
        'technicians':         technicians,
        'checklist_items':     _checklist_items(),
        'prefill_jc':          prefill_jc,
        'prefill_quotation':   prefill_quotation,
        'next_dn_no':          generate_voucher_number('Delivery Note', DeliveryNote, 'voucher_number', default_prefix='DN-'),
        'today':               timezone.now().date(),
        'dn_voucher_type_id':  dn_voucher_type.id if dn_voucher_type else 6,
        'voucher_types':       Vouchers.objects.all().order_by('VoucherName'),
    })


# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_edit(request, pk):
    dn          = get_object_or_404(
        DeliveryNote.objects.prefetch_related('vehicles__vehicle', 'services', 'parts', 'labours'),
        pk=pk
    )
    customers   = LedgerCreation.objects.filter(
                      groups_id=18).order_by('ledger_name')
    advisors    = Staff.objects.filter(
                      status='Active',)
    technicians = Staff.objects.filter(
                      status='Active',
                      staff_category__name='Technician').order_by('full_name')

    if request.method == 'POST':
        updated = _save_delivery(request, dn=dn)
        if updated:
            messages.success(
                request,
                f"Delivery Note {dn.voucher_number} updated!")
            return redirect('jobcard_app:delivery_detail', pk=pk)

    from fleet_app.models import Vouchers
    dn_voucher_type = Vouchers.objects.filter(VoucherName='Delivery Note').first()
    return render(request, 'jobcard_app/delivery_form.html', {
        'dn':                  dn,
        'customers':           customers,
        'advisors':            advisors,
        'technicians':         technicians,
        'checklist_items':     _checklist_items(),
        'services':            dn.services.all(),
        'parts':               dn.parts.all(),
        'labour':              dn.labours.all(),
        'edit_mode':           True,
        'today':               timezone.now().date(),
        'dn_voucher_type_id':  dn_voucher_type.id if dn_voucher_type else 6,
        'voucher_types':       Vouchers.objects.all().order_by('VoucherName'),
    })


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_delete(request, pk):
    dn = get_object_or_404(DeliveryNote, pk=pk)
    if request.method == 'POST':
        num = dn.voucher_number
        dn.is_active = False
        dn.save()
        if dn.voucherType:
            Stock.objects.filter(voucherType=dn.voucherType, voucherNo=dn.id).delete()
        messages.success(request, f"Delivery Note {num} deleted.")
        return redirect('jobcard_app:delivery_list')
    return render(
        request,
        'jobcard_app/delivery_confirm_delete.html',
        {'dn': dn})


@login_required
def ajax_get_jobcard_for_delivery(request):
    """
    Returns job cards and quotations for a customer+vehicle to load into delivery note.
    Returns: services (complaints), parts (with item_id), labour lines, and attached vehicles.
    """
    customer_id = request.GET.get('customer_id', '').strip()
    vehicle_id  = request.GET.get('vehicle_id', '').strip()

    if not customer_id:
        return JsonResponse({'jobcards': [], 'quotations': []})

    try:
        from item_master.models import Item
        items_by_id   = {}
        items_by_code = {}
        items_by_name = {}
        for item in Item.objects.filter(isDeleted=False):
            items_by_id[str(item.id)] = item
            if item.item_code:
                items_by_code[item.item_code.lower()] = item
            if item.item_name:
                items_by_name[item.item_name.lower()] = item

        def _safe_unit(item, fallback='No'):
            if not item:
                return fallback
            try:
                if item.item_unit:
                    return getattr(item.item_unit, 'unit_name', fallback) or fallback
            except Exception:
                pass
            return fallback

        qs = JobCard.objects.select_related(
            'workshop_vehicle', 'advisor'
        ).prefetch_related(
            'complaints', 'parts', 'labours', 'vehicles__vehicle'
        ).filter(
            customer_id=customer_id,
            is_active=True
        )

        if vehicle_id:
            qs = qs.filter(workshop_vehicle_id=vehicle_id)

        qs = qs.order_by('-date')[:15]

        result = []
        for jc in qs:

            # ── Attached Vehicles ─────────────────────────────
            jc_vehs = []
            for jv in jc.vehicles.select_related('vehicle').all():
                if jv.vehicle:
                    jc_vehs.append({
                        'id': str(jv.vehicle_id),
                        'number': jv.vehicle.vehicle_number,
                        'reg': jv.vehicle.registration_number or '',
                        'mileage': jv.mileage or '',
                    })
            if not jc_vehs and jc.workshop_vehicle:
                jc_vehs.append({
                    'id': str(jc.workshop_vehicle_id),
                    'number': jc.workshop_vehicle.vehicle_number,
                    'reg': jc.workshop_vehicle.registration_number or '',
                    'mileage': jc.mileage or '',
                })

            # ── Complaints as services ────────────────────────
            services = []
            for c in jc.complaints.all():
                services.append({
                    'description': c.description or '',
                    'category':    c.category    or '',
                    'status':      'Completed',
                    'vehicle_id':  str(c.vehicle_id) if c.vehicle_id else (str(jc.workshop_vehicle_id) if jc.workshop_vehicle_id else ''),
                })

            # ── Parts ─────────────────────────────────────────
            parts = []
            for p in jc.parts.all():
                code_str = (p.part_number or '').strip()
                name_str = (p.description or '').strip()
                matched_item = (
                    items_by_code.get(code_str.lower()) or
                    items_by_id.get(code_str) or
                    items_by_name.get(name_str.lower())
                ) if (code_str or name_str) else None

                parts.append({
                    'item_id':    str(matched_item.id) if matched_item else '',
                    'name':       name_str or (matched_item.item_name if matched_item else ''),
                    'item_code':  matched_item.item_code if matched_item else code_str,
                    'unit':       _safe_unit(matched_item, 'No'),
                    'quantity':   float(p.quantity   or 1),
                    'rate':       float(p.unit_price or 0),
                    'amount':     float(p.total_price or 0),
                    'vehicle_id': str(p.vehicle_id) if p.vehicle_id else (str(jc.workshop_vehicle_id) if jc.workshop_vehicle_id else ''),
                })

            # ── Labour ────────────────────────────────────────
            labours = []
            for l in jc.labours.all():
                labours.append({
                    'description':   l.description or '',
                    'hours':         float(l.hours or 1),
                    'rate':          float(l.rate  or 0),
                    'amount':        float(l.amount or 0),
                    'technician_id': str(l.technician_id) if l.technician_id else '',
                    'vehicle_id':    str(l.vehicle_id) if l.vehicle_id else (str(jc.workshop_vehicle_id) if jc.workshop_vehicle_id else ''),
                })

            result.append({
                'id':           jc.id,
                'job_number':   jc.job_number,
                'date':         jc.date.strftime('%d %b %Y'),
                'status':       jc.get_status_display(),
                'vehicle':      str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
                'vehicle_id':   jc.workshop_vehicle_id or '',
                'vehicles':     jc_vehs,
                'mileage':      jc.mileage or '',
                'fuel_level':   jc.fuel_level or '',
                'advisor':      jc.advisor.full_name if jc.advisor else '',
                'advisor_id':   jc.advisor_id or '',
                'services':     services,
                'parts':        parts,
                'labours':      labours,
                's_count':      len(services),
                'p_count':      len(parts),
                'l_count':      len(labours),
            })

        # Fetch Quotations for customer/vehicle
        q_qs = Quotation.objects.select_related(
            'vehicle', 'advisor'
        ).prefetch_related(
            'items', 'complaints', 'vehicles__vehicle'
        ).filter(
            customer_id=customer_id
        )
        if vehicle_id:
            q_qs = q_qs.filter(vehicle_id=vehicle_id)

        q_qs = q_qs.order_by('-date')[:15]
        quotations_result = []

        for q in q_qs:
            q_vehs = []
            for qv in q.vehicles.select_related('vehicle').all():
                if qv.vehicle:
                    q_vehs.append({
                        'id': str(qv.vehicle_id),
                        'number': qv.vehicle.vehicle_number,
                        'reg': qv.vehicle.registration_number or '',
                        'mileage': qv.mileage or '',
                    })
            if not q_vehs and q.vehicle:
                q_vehs.append({
                    'id': str(q.vehicle_id),
                    'number': q.vehicle.vehicle_number,
                    'reg': q.vehicle.registration_number or '',
                    'mileage': q.mileage or '',
                })

            q_services = []
            for c in q.complaints.all():
                q_services.append({
                    'description': c.description or '',
                    'category':    getattr(c, 'category', '') or '',
                    'status':      'Completed',
                    'vehicle_id':  str(c.vehicle_id) if c.vehicle_id else (str(q.vehicle_id) if q.vehicle_id else ''),
                })

            q_parts = []
            for i in q.items.filter(item_type='part'):
                code_str = (i.item_ref or i.item_code or '').strip()
                name_str = (i.description or '').strip()
                matched_item = (
                    items_by_code.get(code_str.lower()) or
                    items_by_id.get(code_str) or
                    items_by_name.get(name_str.lower())
                ) if (code_str or name_str) else None

                q_parts.append({
                    'item_id':    str(matched_item.id) if matched_item else (code_str if code_str.isdigit() else ''),
                    'name':       name_str or (matched_item.item_name if matched_item else ''),
                    'item_code':  matched_item.item_code if matched_item else code_str,
                    'unit':       i.unit or _safe_unit(matched_item, 'No'),
                    'quantity':   float(i.quantity or 1),
                    'rate':       float(i.unit_price or 0),
                    'amount':     float(i.quantity or 1) * float(i.unit_price or 0),
                    'vehicle_id': str(i.vehicle_id) if i.vehicle_id else (str(q.vehicle_id) if q.vehicle_id else ''),
                })

            q_labours = []
            for i in q.items.filter(item_type='labour'):
                q_labours.append({
                    'description': i.description or '',
                    'hours':       float(i.hours or 1),
                    'rate':        float(i.unit_price or 0),
                    'amount':      float(i.hours or 1) * float(i.unit_price or 0),
                    'vehicle_id':  str(i.vehicle_id) if i.vehicle_id else (str(q.vehicle_id) if q.vehicle_id else ''),
                })

            quotations_result.append({
                'id':               q.id,
                'quotation_number': q.quotation_number,
                'date':             q.date.strftime('%d %b %Y'),
                'status':           q.get_status_display(),
                'vehicle':          str(q.vehicle) if q.vehicle else '',
                'vehicle_id':       q.vehicle_id or '',
                'vehicles':         q_vehs,
                'advisor':          q.advisor.full_name if q.advisor else '',
                'advisor_id':       q.advisor_id or '',
                'services':         q_services,
                'parts':            q_parts,
                'labours':          q_labours,
                's_count':          len(q_services),
                'p_count':          len(q_parts),
                'l_count':          len(q_labours),
            })

        return JsonResponse({'jobcards': result, 'quotations': quotations_result})
    except Exception as e:
        import traceback
        print(f"Error in ajax_get_jobcard_for_delivery: {e}")
        traceback.print_exc()
        return JsonResponse({'jobcards': [], 'quotations': [], 'error': str(e)})


@login_required
def ajax_get_docs_for_delivery(request):
    """
    Search job cards AND quotations for the Load Document picker
    in delivery note form.
    """
    customer_id = request.GET.get('customer_id', '').strip()
    vehicle_id  = request.GET.get('vehicle_id', '').strip()
    q           = request.GET.get('q', '').strip()

    result = []

    # ── Job Cards ─────────────────────────────────────────
    jc_qs = JobCard.objects.select_related(
        'workshop_vehicle', 'advisor'
    ).prefetch_related(
        'complaints', 'parts', 'labours', 'vehicles__vehicle'
    ).filter(is_active=True)

    if customer_id:
        jc_qs = jc_qs.filter(customer_id=customer_id)
    if vehicle_id:
        jc_qs = jc_qs.filter(workshop_vehicle_id=vehicle_id)
    if q:
        jc_qs = jc_qs.filter(job_number__icontains=q)

    jc_qs = jc_qs.order_by('-date')[:10]

    for jc in jc_qs:
        jc_vehs = [{'id': str(jv.vehicle_id), 'number': jv.vehicle.vehicle_number, 'reg': jv.vehicle.registration_number or ''} for jv in jc.vehicles.select_related('vehicle').all() if jv.vehicle]
        services = [{'description': c.description, 'category': getattr(c, 'category', ''), 'status': 'Completed', 'vehicle_id': str(c.vehicle_id) if c.vehicle_id else ''}
                    for c in jc.complaints.all() if c.description]
        parts    = [{'name': p.description, 'item_code': p.part_number or '',
                     'quantity': float(p.quantity or 1), 'rate': float(p.unit_price or 0),
                     'item_id': '', 'vehicle_id': str(p.vehicle_id) if p.vehicle_id else ''}
                    for p in jc.parts.all() if p.description]
        labours  = [{'description': l.description, 'hours': float(l.hours or 1),
                     'rate': float(l.rate or 0), 'vehicle_id': str(l.vehicle_id) if l.vehicle_id else ''}
                    for l in jc.labours.all() if l.description]

        result.append({
            'type':        'JC',
            'id':          jc.id,
            'number':      jc.job_number,
            'date':        jc.date.strftime('%d %b %Y'),
            'status':      jc.get_status_display(),
            'vehicle':     str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
            'vehicle_id':  jc.workshop_vehicle_id or '',
            'vehicles':    jc_vehs,
            'mileage':     jc.mileage or '',
            'fuel_level':  jc.fuel_level or '',
            'advisor_id':  jc.advisor_id or '',
            'advisor':     jc.advisor.full_name if jc.advisor else '',
            'services':    services,
            'parts':       parts,
            'labours':     labours,
            's_count':     len(services),
            'p_count':     len(parts),
            'l_count':     len(labours),
        })

    # ── Quotations ────────────────────────────────────────
    from .models import Quotation
    qt_qs = Quotation.objects.select_related(
        'vehicle', 'advisor'
    ).prefetch_related(
        'items', 'complaints', 'vehicles__vehicle'
    )

    if customer_id:
        qt_qs = qt_qs.filter(customer_id=customer_id)
    if vehicle_id:
        qt_qs = qt_qs.filter(vehicle_id=vehicle_id)
    if q:
        qt_qs = qt_qs.filter(quotation_number__icontains=q)

    qt_qs = qt_qs.order_by('-date')[:10]

    for qt in qt_qs:
        qt_vehs = [{'id': str(qv.vehicle_id), 'number': qv.vehicle.vehicle_number, 'reg': qv.vehicle.registration_number or ''} for qv in qt.vehicles.select_related('vehicle').all() if qv.vehicle]
        services = [{'description': c.description, 'status': 'Completed', 'vehicle_id': str(c.vehicle_id) if c.vehicle_id else ''}
                    for c in qt.complaints.filter(complaint_type='customer')
                    if c.description]
        parts    = [{'name': i.description, 'item_code': i.item_ref or '',
                     'quantity': float(i.quantity or 1), 'rate': float(i.unit_price or 0),
                     'item_id': i.item_ref or '', 'vehicle_id': str(i.vehicle_id) if i.vehicle_id else ''}
                    for i in qt.items.filter(item_type='part') if i.description]
        labours  = [{'description': i.description, 'hours': float(i.hours or 1),
                     'rate': float(i.unit_price or 0), 'vehicle_id': str(i.vehicle_id) if i.vehicle_id else ''}
                    for i in qt.items.filter(item_type='labour') if i.description]

        result.append({
            'type':       'QT',
            'id':         qt.id,
            'number':     qt.quotation_number,
            'date':       qt.date.strftime('%d %b %Y'),
            'status':     qt.get_status_display(),
            'vehicle':    str(qt.vehicle) if qt.vehicle else '',
            'vehicle_id': qt.vehicle_id or '',
            'vehicles':   qt_vehs,
            'mileage':    qt.mileage or '',
            'advisor_id': qt.advisor_id or '',
            'advisor':    qt.advisor.full_name if qt.advisor else '',
            'services':   services,
            'parts':      parts,
            'labours':    labours,
            's_count':    len(services),
            'p_count':    len(parts),
            'l_count':    len(labours),
        })

    return JsonResponse({'documents': result})
# ═══════════════════════════════════════════════════════
# INVOICE
# ═══════════════════════════════════════════════════════

import logging
from decimal import Decimal, InvalidOperation
 
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
 
from accounts_app.models import LedgerCreation, LedgerPosting
from fleet_app.models import Staff, Vouchers
 
from .forms import InvoiceHeaderForm
from .models import (
    DeliveryNote, Invoice, InvoiceItem, InvoiceVehicle, JobCard, WorkshopVehicle,
)
 
log = logging.getLogger(__name__)
 
INVOICE_VOUCHER_PK = 2         # "Invoice" row in Vouchers
CASH_LEDGER_PK = 23
BANK_LEDGER_PK = 24
DISCOUNT_LEDGER_PK = 10
OTHER_INCOME_LEDGER_PK = 11
OUTPUT_GST_LEDGER_PK = 12
 
 
# ─────────────────────────────────────────────────────────────
# small helpers
# ─────────────────────────────────────────────────────────────
def _num(lst, idx, default):
    """float(lst[idx]) with a safe fallback for missing / blank / bad values."""
    try:
        v = lst[idx] if idx < len(lst) else ''
        return float(v) if str(v).strip() != '' else default
    except (ValueError, TypeError):
        return default
 
 
def _at(lst, idx, default=''):
    return lst[idx].strip() if idx < len(lst) and lst[idx] is not None else default
 
 
def _vehicle(pk):
    return WorkshopVehicle.objects.filter(pk=pk).first() if pk else None
 
 
def _invoice_voucher_type(invoice=None):
    return Vouchers.objects.get(pk=INVOICE_VOUCHER_PK)
 
 
# ─────────────────────────────────────────────────────────────
# AJAX — search delivery notes (for invoice form)
# ─────────────────────────────────────────────────────────────
@login_required
def ajax_search_deliveries(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'deliveries': []})
 
    qs = DeliveryNote.objects.select_related('customer', 'vehicle').filter(is_active=True).filter(
        Q(voucher_number__icontains=q) |
        Q(customer__ledger_name__icontains=q) |
        Q(reg_number__icontains=q)
    )[:10]
 
    result = [{
        'id':             d.id,
        'voucher_number': d.voucher_number,
        'customer_id':    d.customer_id,
        'customer_name':  d.customer.ledger_name,
        'vehicle_id':     d.vehicle_id or '',
        'vehicle_name':   str(d.vehicle) if d.vehicle else '',
        'date':           d.date.strftime('%d %b %Y'),
        'grand_total':    d.get_grand_total(),
    } for d in qs]
    return JsonResponse({'deliveries': result})
 
 
# ═════════════════════════════════════════════════════════════
# INVOICE — SAVE
# ═════════════════════════════════════════════════════════════
def _snapshot(invoice):
    return {
        'status':       invoice.status,
        'payment_mode': invoice.payment_mode,
        'discount_pct': str(invoice.discount_pct or 0),
        'amount_paid':  str(invoice.amount_paid or 0),
        'grand_total':  str(round(invoice.get_grand_total(), 3)) if invoice.pk else '0',
        'customer':     str(invoice.customer) if invoice.customer_id else '',
        'display_number': invoice.display_number,
    }
 
 
def _save_items(invoice, post):
    print("INVOICE ITEM DEBUG:", {
        "lab_desc": post.getlist("lab_desc[]"),
        "lab_hrs": post.getlist("lab_hrs[]"),
        "lab_rate": post.getlist("lab_rate[]"),
        "oth_desc": post.getlist("oth_desc[]"),
        "oth_amt": post.getlist("oth_amt[]"),
    })
    """Rebuild every InvoiceItem (parts, labour, other) from the POSTed arrays."""
    invoice.items.all().delete()
    order = 0
 
    # ── Spare parts ──
    p_veh   = post.getlist('part_vehicle_id[]')
    p_ids   = post.getlist('part_item_id[]')
    p_names = post.getlist('part_name[]')
    p_codes = post.getlist('part_code[]')
    p_qty   = post.getlist('part_qty[]')
    p_unit  = post.getlist('part_unit[]')
    p_rate  = post.getlist('part_rate[]')
    p_disc  = post.getlist('part_disc[]')
    p_tax   = post.getlist('part_tax[]')
 
    try:
        from item_master.models import Item
    except Exception:           # item master not installed
        Item = None
 
    for i in range(max(len(p_ids), len(p_names))):
        item_id = _at(p_ids, i)
        name    = _at(p_names, i)
        code    = _at(p_codes, i)
 
        item_obj = None
        if item_id and Item is not None and item_id.isdigit():
            item_obj = Item.objects.filter(pk=item_id).first()
            if item_obj:
                name = name or item_obj.item_name
                code = code or (item_obj.item_code or '')
        if not name:
            continue                                   # empty row
 
        InvoiceItem.objects.create(
            invoice=invoice, item_type='part',
            vehicle=_vehicle(_at(p_veh, i)),
            item=item_obj, item_ref=item_id or None, item_code=code, description=name,
            quantity=_num(p_qty, i, 1), unit=_at(p_unit, i) or 'Pcs',
            unit_price=_num(p_rate, i, 0), discount_pct=_num(p_disc, i, 0),
            tax_percent=_num(p_tax, i, 8), order=order,
        )
        order += 1
 
    # ── Labour ──
    l_veh  = post.getlist('labour_vehicle_id[]')
    l_desc = post.getlist('lab_desc[]')
    l_tech = post.getlist('lab_tech[]')
    l_hrs  = post.getlist('lab_hrs[]')
    l_rate = post.getlist('lab_rate[]')
    l_tax  = post.getlist('lab_tax[]')
 
    for i, desc in enumerate(l_desc):
        if not desc.strip():
            continue
        tech_id = _at(l_tech, i)
        InvoiceItem.objects.create(
            invoice=invoice, item_type='labour',
            vehicle=_vehicle(_at(l_veh, i)), description=desc.strip(),
            technician=Staff.objects.filter(pk=tech_id).first() if tech_id else None,
            hours=_num(l_hrs, i, 1), unit_price=_num(l_rate, i, 0),
            tax_percent=_num(l_tax, i, 8), quantity=1, order=order,
        )
        order += 1
 
    # ── Other charges ──
    o_veh  = post.getlist('other_vehicle_id[]')
    o_desc = post.getlist('oth_desc[]')
    o_amt  = post.getlist('oth_amt[]')
    o_tax  = post.getlist('oth_tax[]')
 
    for i, desc in enumerate(o_desc):
        if not desc.strip():
            continue
        InvoiceItem.objects.create(
            invoice=invoice, item_type='other',
            vehicle=_vehicle(_at(o_veh, i)), description=desc.strip(),
            quantity=1, unit_price=_num(o_amt, i, 0),
            tax_percent=_num(o_tax, i, 0), order=order,
        )
        order += 1
 
def _save_vehicles(invoice, post):
    invoice.vehicles.all().delete()
    ids      = post.getlist('inv_vehicle_id[]')
    mileages = post.getlist('inv_vehicle_mileage[]')
    notes    = post.getlist('inv_vehicle_notes[]')

    first, seen = None, set()
    for i, v_id in enumerate(ids):
        if not v_id or v_id in seen:
            continue
        seen.add(v_id)
        veh = _vehicle(v_id)
        if not veh:
            continue
        first = first or veh
        mileage = _at(mileages, i)
        InvoiceVehicle.objects.create(
            invoice=invoice, vehicle=veh,
            mileage=int(float(mileage)) if mileage else None,
            notes=_at(notes, i),
        )
    invoice.vehicle = first                             # legacy single-vehicle field
    invoice.save(update_fields=['vehicle'])

def _assign_voucher_number(post, invoice, vt):
    is_new = invoice is None or not invoice.pk
    if is_new:
        post['voucher_number'] = get_next_document_number(vt.pk, Invoice, 'voucher_number')
    else:
        post['voucher_number'] = invoice.voucher_number or get_next_document_number(vt.pk, Invoice, 'voucher_number')

 
def _save_invoice(request, invoice=None):
    """Create or update an invoice from request.POST. Returns the Invoice, or None on error."""
    post = request.POST.copy()                          # mutable copy

    cid = post.get('customer', '').strip()
    if not cid:
        messages.error(request, 'Customer is required.')
        return None
    customer = get_object_or_404(LedgerCreation, pk=cid)

    sel_vt = _invoice_voucher_type()
    post['voucherType'] = str(sel_vt.pk)
    _assign_voucher_number(post, invoice, sel_vt)

    is_new = invoice is None or not invoice.pk
    old_vt = old_snapshot = None
    if not is_new:
        old_vt = invoice.voucherType
        old_snapshot = _snapshot(invoice)
    if invoice is None:
        invoice = Invoice(created_by=request.user.id)
    else:
        invoice.updated_by = request.user.id

    form = InvoiceHeaderForm(post, instance=invoice if invoice.pk else None)
    if not form.is_valid():
        for field, errs in form.errors.items():
            for e in errs:
                label = '' if field == '__all__' else f'{field.replace("_", " ").title()}: '
                messages.error(request, f'{label}{e}')
        return None
    cd = form.cleaned_data

    jc_id = post.get('job_card', '').strip() or post.get('loaded_job_card', '').strip()
    jobcard = JobCard.objects.filter(pk=jc_id).first() if jc_id.isdigit() else None
    adv_id = post.get('advisor', '').strip()
    posted_paid = cd['amount_paid']

    try:
        with transaction.atomic():
            invoice.customer         = customer
            invoice.voucherType      = sel_vt
            invoice.voucher_number   = post['voucher_number']
            invoice.invoice_number   = cd.get('invoice_number') or None
            invoice.jobcard          = jobcard
            invoice.advisor          = Staff.objects.filter(pk=adv_id).first() if adv_id else None
            invoice.invoice_date     = cd['invoice_date']
            invoice.due_date         = cd.get('due_date') or None
            invoice.status           = cd.get('status') or 'draft'
            invoice.payment_mode     = cd['payment_mode']
            invoice.customer_mobile  = cd.get('customer_mobile') or ''
            invoice.customer_address = cd.get('customer_address') or ''
            invoice.vehicle_model    = post.get('vehicle_model', '')
            invoice.discount_pct     = cd['discount_pct']
            invoice.amount_paid      = posted_paid
            invoice.notes            = cd.get('notes') or ''
            invoice.save()

            _save_vehicles(invoice, post)
            _save_items(invoice, post)

            if invoice.payment_mode in ('cash', 'bank') and posted_paid == 0:
                invoice.amount_paid = Decimal(str(round(invoice.get_grand_total(), 3)))
                invoice.save(update_fields=['amount_paid'])

            invoice.update_status()
            _sync_invoice_stock(invoice)

            if old_vt and old_vt.pk != sel_vt.pk:
                delete_ledger_postings_for_invoice(invoice)
            create_ledger_postings_for_invoice(invoice)

            # _sync_invoice_billwise_opening(invoice)   # add later, keyed on voucher_number
    except PostingError as e:
        messages.error(request, f'Accounting posting failed: {e}. Nothing was saved.')
        return None
    except Exception:
        log.exception('Invoice save failed')
        messages.error(request, 'Could not save the invoice. Nothing was changed — please try again.')
        return None

    _audit(request, invoice, is_new, old_snapshot)
    return invoice
def _audit(request, invoice, is_new, old_snapshot):
    try:
        from audit_app.services import log_audit_event
        total = round(invoice.get_grand_total(), 3)
        common = dict(module='INVOICE', entity_type='Invoice', entity_id=invoice.pk,
                      entity_reference=invoice.invoice_number, user=request.user, request=request)
        if is_new:
            log_audit_event(
                action='CREATE',
                description=(f"Created Invoice #{invoice.invoice_number} for customer '{invoice.customer}' "
                             f"(Total: {total:.3f}, Status: {invoice.status}, Mode: {invoice.payment_mode})."),
                changes_diff={'initial_state': {
                    'invoice_number': invoice.invoice_number, 'customer': str(invoice.customer),
                    'status': invoice.status, 'grand_total': total,
                    'amount_paid': float(invoice.amount_paid or 0), 'payment_mode': invoice.payment_mode,
                }},
                **common)
            return
 
        new = _snapshot(invoice)
        diff = {k: {'old': v, 'new': new[k]} for k, v in (old_snapshot or {}).items() if str(v) != str(new[k])}
        changes = [f"{k.replace('_', ' ').title()} changed from '{d['old']}' to '{d['new']}'" for k, d in diff.items()]
        log_audit_event(
            action='STATUS_CHANGE' if list(diff) == ['status'] else 'UPDATE',
            description=f"Updated Invoice #{invoice.display_number}. " + ('; '.join(changes) or 'Line items / notes updated.'),
            changes_diff=diff, **common)
    except Exception:
        log.exception('Invoice audit log failed')
 
 
# ═════════════════════════════════════════════════════════════
# STOCK / LEDGER / BILL-WISE SYNC
# ═════════════════════════════════════════════════════════════
def _sync_invoice_stock(invoice):
    """Issue stock for inventory parts. Cancelled invoices leave no stock rows."""
    try:
        from item_master.models import Stock, CostCenter
        from item_master.common import upsert_stock, to_base_qty
 
        vt = _invoice_voucher_type(invoice)
        if not vt:
            return
        Stock.objects.filter(voucherType=vt, voucherNo=invoice.id).delete()
        if invoice.status == 'cancelled':
            return
 
        default_cc = CostCenter.objects.filter(isDefault=True).first() or CostCenter.objects.first()
        for part in invoice.parts:
            item = part.get_item_obj()
            if not item or getattr(item, 'IsNonInventory', False):
                continue
            qty = Decimal(str(part.quantity or 0))
            if qty <= 0:
                continue
            upsert_stock(
                item=item, batch_id=None, base_unit_id=item.item_unit_id,
                base_qty_delta=-to_base_qty(item, item.item_unit_id, qty),
                rate=Decimal(str(part.unit_price or 0)),
                voucher_date=invoice.invoice_date, voucher_type=vt, voucher_id=invoice.id,
                cost_center=item.cost_center or default_cc,
            )
    except Exception:
        log.exception('Error syncing invoice stock')
 
 

 

 
# ═════════════════════════════════════════════════════════════
# INVOICE — LIST / CREATE / EDIT / DELETE
# ═════════════════════════════════════════════════════════════
def _form_context():
    return {
        'customers':   LedgerCreation.objects.filter(groups_id=18).order_by('ledger_name'),
        'technicians': Staff.objects.filter(status='Active', staff_category__name='Technician').order_by('full_name'),
        'advisors':    Staff.objects.filter(status='Active').order_by('full_name'),
        'today':       timezone.now().date(),
    }
 
 
ARRAY_FIELDS = [
    'inv_vehicle_id', 'inv_vehicle_mileage', 'inv_vehicle_notes',
    'part_item_id', 'part_name', 'part_code', 'part_qty', 'part_unit', 'part_rate', 'part_disc', 'part_tax',
    'lab_desc', 'lab_tech', 'lab_hrs', 'lab_rate', 'lab_tax',
    'oth_desc', 'oth_amt', 'oth_tax',
]
SCALAR_FIELDS = [
    'voucherType', 'voucher_number', 'invoice_number', 'invoice_date', 'due_date', 'payment_mode',
    'job_card_ref', 'job_card', 'status', 'customer', 'customer_mobile', 'customer_address', 'notes',
    'discount_pct', 'amount_paid', 'loaded_delivery_note', 'loaded_job_card',
]
 
 
def _posted_data(request):
    """Everything the user typed, so a failed save re-renders the form instead of wiping it."""
    data = {f: request.POST.get(f, '') for f in SCALAR_FIELDS}
    data.update({f: request.POST.getlist(f + '[]') for f in ARRAY_FIELDS})
    return data
 
 
@login_required
def invoice_list(request):
    q         = request.GET.get('q', '').strip()
    status    = request.GET.get('status', '')
    date_from = request.GET.get('date_from')
    date_to   = request.GET.get('date_to')
    
    qs = Invoice.objects.select_related('customer', 'vehicle', 'jobcard').filter(is_active=True)
    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(jobcard__job_number__icontains=q) |
            Q(voucher_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    if date_from:
        qs = qs.filter(invoice_date__gte=date_from)
    if date_to:
        qs = qs.filter(invoice_date__lte=date_to)
 
    all_invoices = Invoice.objects.filter(is_active=True).prefetch_related('items')
    total_invoiced = total_paid = total_outstanding = 0
    for inv in all_invoices:
        total_invoiced    += inv.get_grand_total()
        total_paid        += float(inv.amount_paid)
        total_outstanding += inv.get_balance_due()
 
    status_counts = {r['status']: r['n'] for r in
                     Invoice.objects.filter(is_active=True).values('status').annotate(n=Count('id'))}
    counts = {'total': sum(status_counts.values())}
    for s in ('draft', 'sent', 'partial', 'paid', 'overdue', 'cancelled'):
        counts[s] = status_counts.get(s, 0)
 
    return render(request, 'jobcard_app/invoice_list.html', {
        'invoices': qs, 'q': q, 'status': status, 'counts': counts,
        'stats': {
            'total_invoiced': total_invoiced, 'total_paid': total_paid,
            'total_outstanding': total_outstanding, 'overdue_count': counts['overdue'],
        },
    })
 
 
@login_required
def invoice_create(request):
    ctx = _form_context()

    prefill_jc = None
    if request.GET.get('from_jobcard'):
        prefill_jc = JobCard.objects.select_related('customer', 'workshop_vehicle', 'advisor').prefetch_related(
            'parts', 'labours', 'complaints').filter(pk=request.GET['from_jobcard']).first()

    prefill_dn = None
    if request.GET.get('from_delivery'):
        prefill_dn = DeliveryNote.objects.select_related('customer', 'vehicle', 'advisor').prefetch_related(
            'parts', 'labours', 'services', 'vehicles__vehicle').filter(pk=request.GET['from_delivery']).first()

    posted_data = None
    if request.method == 'POST':
        inv = _save_invoice(request)
        if inv:
            messages.success(request, f'Invoice {inv.display_number} created!')
            return redirect('jobcard_app:invoice_list')
        posted_data = _posted_data(request)

    sel_vt = _invoice_voucher_type()
    ctx.update({
        'prefill_jc': prefill_jc,
        'prefill_dn': prefill_dn,
        'default_voucher_type': sel_vt,
        'next_voucher_number': get_next_document_number(sel_vt.pk, Invoice, 'voucher_number'),
        'posted_data': posted_data,
    })
    return render(request, 'jobcard_app/invoice_form.html', ctx)
 
@login_required
def invoice_detail(request, pk):
    return redirect('jobcard_app:invoice_edit', pk=pk)
 
 
@login_required
def invoice_edit(request, pk):
    inv = get_object_or_404(Invoice, pk=pk)
    posted_data = None
 
    if request.method == 'POST':
        updated = _save_invoice(request, invoice=inv)
        if updated:
            messages.success(request, f'Invoice {updated.display_number} updated!')
            return redirect('jobcard_app:invoice_list')
        inv = get_object_or_404(Invoice, pk=pk)          # drop unsaved in-memory edits
        posted_data = _posted_data(request)
 
    ctx = _form_context()
    ctx.update({
        'invoice':       inv,
        'parts':         inv.parts,
        'labour':        inv.labours,
        'other_charges': inv.other_charges,
        'edit_mode':     True,
        'posted_data':   posted_data,
    })
    return render(request, 'jobcard_app/invoice_form.html', ctx)
 
 
@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    try:
        with transaction.atomic():
            from item_master.models import Stock
            from accounts_app.models import BillWiseOpening
            vt = _invoice_voucher_type(invoice)
            if vt:
                Stock.objects.filter(voucherType=vt, voucherNo=invoice.id).delete()
                BillWiseOpening.objects.filter(voucherType=vt, InvNo=invoice.invoice_number).delete()
            unpost_invoice(invoice, vt)
            invoice.delete()
        messages.success(request, 'Invoice deleted.')
    except Exception:
        log.exception('Invoice delete failed')
        messages.error(request, 'Could not delete the invoice.')
    return redirect('jobcard_app:invoice_list')
 
 
# ═════════════════════════════════════════════════════════════
# AJAX
# ═════════════════════════════════════════════════════════════
@login_required
def get_next_invoice_number(request):
 
    voucher_type_id = request.GET.get('voucher_type_id')
    try:
        number = get_next_document_number(voucher_type_id,Invoice,'voucher_number')
        return JsonResponse({'success': True,'invoice_number': number,'voucher_number': number })
    except ValueError as e:
        return JsonResponse({'success': False,'error': str(e) }, status=400)


@login_required
def get_next_delivery_number(request):
 
    voucher_type_id = request.GET.get('voucher_type_id')
    try:
        number = get_next_document_number(voucher_type_id,DeliveryNote,'voucher_number')
        return JsonResponse({'success': True,'delivery_number': number,'voucher_number': number })
    except ValueError as e:
        return JsonResponse({'success': False,'error': str(e) }, status=400)
 

def _vehicles_payload(primary, extra_rows, primary_mileage):
    """Merge a document's main vehicle with its attached vehicle rows, de-duplicated."""
    out = []
 
    def model_of(v):
        return str(getattr(v, 'vehicle_model', '') or getattr(v, 'model', '') or '')
 
    if primary:
        out.append({'id': primary.id, 'name': str(primary), 'model': model_of(primary),
                    'mileage': primary_mileage or getattr(primary, 'odometer', None) or ''})
    seen = {v['id'] for v in out}
    for row in extra_rows:
        v = row.vehicle
        if v and v.id not in seen:
            seen.add(v.id)
            out.append({'id': v.id, 'name': str(v), 'model': model_of(v),
                        'mileage': row.mileage or getattr(v, 'odometer', None) or ''})
    return out
 
 
@login_required
def ajax_get_docs_for_invoice(request):
    """Active Delivery Notes and Job Cards for the invoice 'Load Details' picker."""
    from item_master.models import Item
 
    customer_id = request.GET.get('customer_id', '').strip()
    vehicle_param = request.GET.get('vehicle_id', '').strip() or request.GET.get('vehicle_ids', '').strip()
    vehicle_ids = [v.strip() for v in vehicle_param.split(',') if v.strip()]
    q = request.GET.get('q', '').strip()
 
    dn_result, jc_result = [], []
    try:
        items = list(Item.objects.filter(isDeleted=False))
        by_id   = {str(i.id): i for i in items}
        by_code = {i.item_code.lower(): i for i in items if i.item_code}
        by_name = {i.item_name.lower(): i for i in items if i.item_name}
 
        def match(code, name, pk=None):
            code, name = (code or '').strip(), (name or '').strip()
            return ((pk and by_id.get(str(pk))) or by_code.get(code.lower()) or by_id.get(code)
                    or by_name.get(name.lower())) if (pk or code or name) else None
 
        # ── Delivery notes ──
        dn_qs = DeliveryNote.objects.select_related('customer', 'vehicle', 'jobcard').prefetch_related(
            'parts', 'labours__technician', 'services', 'vehicles__vehicle').filter(is_active=True)
        if customer_id:
            dn_qs = dn_qs.filter(customer_id=customer_id)
        if vehicle_ids:
            dn_qs = dn_qs.filter(Q(vehicle_id__in=vehicle_ids) | Q(vehicles__vehicle_id__in=vehicle_ids)).distinct()
        if q:
            dn_qs = dn_qs.filter(
                Q(voucher_number__icontains=q) | Q(customer__ledger_name__icontains=q) |
                Q(contact_number__icontains=q) | Q(customer__mobile__icontains=q) |
                Q(customer__phone_no__icontains=q) | Q(vehicle__registration_number__icontains=q) |
                Q(jobcard__job_number__icontains=q)).distinct()
 
        for dn in dn_qs.order_by('-date', '-id')[:30]:
            parts = []
            for p in dn.parts.all():
                m = match(p.item_code, p.name, p.item_id)
                parts.append({
                    'item_id':     str(m.id) if m else (str(p.item_id) if p.item_id else ''),
                    'part_code':   p.item_code or (m.item_code if m else ''),
                    'description': p.name or (m.item_name if m else ''),
                    'quantity':    float(p.quantity or 1),
                    'unit':        p.unit or 'Pcs',
                    'rate':        float(p.rate or 0),
                    'discount_pct': 0, 'tax_percent': 8,
                    'amount':      float(p.rate or 0) * float(p.quantity or 1),
                })
            labours = [{
                'description': l.description or '',
                'technician_id': str(l.technician_id) if l.technician_id else '',
                'technician_name': l.technician.full_name if l.technician else '',
                'hours': float(l.hours or 1), 'rate': float(l.rate or 0),
                'tax_percent': 8, 'amount': float(l.amount or 0),
            } for l in dn.labours.all()]
 
            vehicles = _vehicles_payload(dn.vehicle, dn.vehicles.all(), getattr(dn, 'odometer_out', None))
            cust = dn.customer
            dn_result.append({
                'id': dn.id, 'number': dn.voucher_number or f'DN-{dn.id}',
                'date': dn.date.strftime('%d %b %Y') if dn.date else '',
                'status': dn.get_status_display(),
                'customer_id': dn.customer_id or '',
                'customer_name': cust.ledger_name if cust else '',
                'customer_mobile': dn.contact_number or (cust.mobile if cust else '') or (cust.phone_no if cust else '') or '',
                'customer_address': (cust.address1 if cust and cust.address1 else ''),
                'payment_mode': dn.payment_mode or '',
                'vehicle_id': dn.vehicle_id or (vehicles[0]['id'] if vehicles else ''),
                'vehicle_name': str(dn.vehicle) if dn.vehicle else (vehicles[0]['name'] if vehicles else ''),
                'vehicles': vehicles,
                'job_card_id': dn.jobcard_id or '',
                'job_number': dn.jobcard.job_number if dn.jobcard else '',
                'parts': parts, 'labours': labours,
                'parts_count': len(parts), 'labours_count': len(labours),
            })
 
        # ── Job cards ──
        jc_qs = JobCard.objects.select_related('customer', 'workshop_vehicle', 'advisor').prefetch_related(
            'parts', 'labours__technician', 'complaints', 'vehicles__vehicle').filter(is_active=True)
        if customer_id:
            jc_qs = jc_qs.filter(customer_id=customer_id)
        if vehicle_ids:
            jc_qs = jc_qs.filter(Q(workshop_vehicle_id__in=vehicle_ids) | Q(vehicles__vehicle_id__in=vehicle_ids)).distinct()
        if q:
            jc_qs = jc_qs.filter(
                Q(job_number__icontains=q) | Q(voucher_number__icontains=q) |
                Q(customer__ledger_name__icontains=q) | Q(customer_phone__icontains=q) |
                Q(customer__mobile__icontains=q) | Q(customer__phone_no__icontains=q) |
                Q(workshop_vehicle__registration_number__icontains=q)).distinct()
 
        for jc in jc_qs.order_by('-date', '-id')[:30]:
            parts = []
            for p in jc.parts.all():
                m = match(p.part_number, p.description)
                parts.append({
                    'item_id':     str(m.id) if m else '',
                    'part_code':   m.item_code if m else (p.part_number or '').strip(),
                    'description': (p.description or '').strip() or (m.item_name if m else ''),
                    'quantity':    float(p.quantity or 1),
                    'unit': 'Pcs',
                    'rate':        float(p.unit_price or 0),
                    'discount_pct': 0, 'tax_percent': 8,
                    'amount':      float(p.total_price or 0),
                })
            labours = [{
                'description': l.description or '',
                'technician_id': str(l.technician_id) if l.technician_id else '',
                'technician_name': l.technician.full_name if l.technician else '',
                'hours': float(l.hours or 1), 'rate': float(l.rate or 0),
                'tax_percent': float(getattr(l, 'tax_percent', 8) or 8),
                'amount': float(l.amount or (float(l.hours or 0) * float(l.rate or 0))),
            } for l in jc.labours.all()]
 
            vehicles = _vehicles_payload(jc.workshop_vehicle, jc.vehicles.all(), jc.mileage)
            cust = jc.customer
            jc_result.append({
                'id': jc.id, 'number': jc.job_number,
                'date': jc.date.strftime('%d %b %Y') if jc.date else '',
                'status': jc.get_status_display(),
                'customer_id': jc.customer_id or '',
                'customer_name': cust.ledger_name if cust else '',
                'customer_mobile': jc.customer_phone or (cust.mobile if cust else '') or (cust.phone_no if cust else '') or '',
                'customer_address': (cust.address1 if cust and cust.address1 else ''),
                'vehicle_id': jc.workshop_vehicle_id or (vehicles[0]['id'] if vehicles else ''),
                'vehicle_name': str(jc.workshop_vehicle) if jc.workshop_vehicle else (vehicles[0]['name'] if vehicles else ''),
                'vehicles': vehicles,
                'parts': parts, 'labours': labours,
                'parts_count': len(parts), 'labours_count': len(labours),
            })
    except Exception:
        log.exception('ajax_get_docs_for_invoice failed')
 
    return JsonResponse({'delivery_notes': dn_result, 'jobcards': jc_result})
 
# ── Skill Tag Master Views ───────────────────────────────────────────────────
from django.utils.translation import gettext_lazy as _
from .forms import SkillTagForm

@login_required
def skill_tag_list(request):
    """
    Skill Tag Master list view allowing view, search, and inline creation/update.
    """
    skills = SkillTag.objects.all().order_by('name')
    form = SkillTagForm()
    edit_id = request.GET.get('edit')
    edit_instance = None
    if edit_id:
        edit_instance = get_object_or_404(SkillTag, pk=edit_id)
        form = SkillTagForm(instance=edit_instance)

    return render(request, 'jobcard_app/skill_tag_list.html', {
        'skills': skills,
        'form': form,
        'edit_instance': edit_instance,
    })

@login_required
def skill_tag_save(request, pk=None):
    """
    Create or update a SkillTag.
    """
    instance = get_object_or_404(SkillTag, pk=pk) if pk else None
    if request.method == 'POST':
        form = SkillTagForm(request.POST, instance=instance)
        if form.is_valid():
            skill = form.save()
            action_str = _("updated") if pk else _("created")
            messages.success(request, f"Skill tag '{skill.name}' {action_str} successfully.")
            return redirect('jobcard_app:skill_tag_list')
        else:
            skills = SkillTag.objects.all().order_by('name')
            return render(request, 'jobcard_app/skill_tag_list.html', {
                'skills': skills,
                'form': form,
                'edit_instance': instance,
            })
    return redirect('jobcard_app:skill_tag_list')

@login_required
def skill_tag_toggle(request, pk):
    """
    Toggle active status of a SkillTag.
    """
    skill = get_object_or_404(SkillTag, pk=pk)
    skill.is_active = not skill.is_active
    skill.save()
    status_str = "activated" if skill.is_active else "deactivated"
    messages.success(request, f"Skill tag '{skill.name}' {status_str} successfully.")
    return redirect('jobcard_app:skill_tag_list')

@login_required
def skill_tag_delete(request, pk):
    """
    Delete a SkillTag.
    """
    skill = get_object_or_404(SkillTag, pk=pk)
    name = skill.name
    skill.delete()
    messages.success(request, f"Skill tag '{name}' deleted successfully.")
    return redirect('jobcard_app:skill_tag_list')

