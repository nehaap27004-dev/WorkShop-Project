from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from sklearn import inspection
import logging
from .models import (
   Estimate, EstimateItem, InvoiceLabour, InvoiceOtherCharge, InvoicePart,Quotation, QuotationItem, ServiceCategory
)
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
from .models import (
    JobCard,
    WorkshopVehicle,
)
from .models import (
  
    Invoice,
    
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
            return redirect('jobcard_app:service_category_list')
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
    customers = LedgerCreation.objects.filter(groups_id=2).order_by('ledger_name')
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
        groups_id=2).order_by('ledger_name')
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
 
        _save_inspection(request, insp)
 
        messages.success(
            request,
            f"Inspection {insp.inspection_number} saved successfully!")
        return redirect('jobcard_app:inspection_detail', pk=insp.pk)
 
    ctx = _inspection_context()
    ctx.update({
        'customers':            customers,
        'inspectors':           inspectors,
        'vehicles':             vehicles,
        'preselected_vehicle':  preselected_vehicle,
        'preselected_customer': preselected_customer,
        'next_insp_no':         _generate_inspection_number(),
        'today':                timezone.now().date(),
    })
    return render(request, 'jobcard_app/inspection_form.html', ctx)
 
# ─────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────
def inspection_detail(request, pk):
    insp = get_object_or_404(
        VehicleInspection.objects.select_related(
            'vehicle', 'customer', 'inspector', 'jobcard'
        ).prefetch_related(
            'exterior_damages', 'findings'
        ),
        pk=pk
    )
 
    try:    interior   = insp.interior
    except: interior   = None
    try:    mechanical = insp.mechanical
    except: mechanical = None
    try:    accessories = insp.accessories
    except: accessories = None
 
    complaints = insp.findings.filter(finding_type='complaint').order_by('order')
    findings   = insp.findings.filter(finding_type='finding').order_by('order')
 
    ctx = _inspection_context()
    ctx.update({
        'insp':        insp,
        'interior':    interior,
        'mechanical':  mechanical,
        'accessories': accessories,
        'complaints':  complaints,
        'findings':    findings,
    })
    return render(request, 'jobcard_app/inspection_detail.html', ctx)
 
 
# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
def inspection_edit(request, pk):
    insp      = get_object_or_404(VehicleInspection, pk=pk)
    customers = LedgerCreation.objects.filter(
        groups_id=2).order_by('ledger_name')
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
        return redirect('jobcard_app:inspection_detail', pk=pk)
 
    ctx = _inspection_context()
    ctx.update({
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
    ).values('id', 'registration_number', 'make',
             'model', 'year', 'odometer', 'fuel_type')
    result = [{
        'id':       v['id'],
        'label':    f"{v['make']} {v['model']}"
                    + (f" {v['year']}" if v['year'] else '')
                    + f" · {v['registration_number']}",
        'reg':      v['registration_number'],
        'make':     v['make'],
        'model':    v['model'],
        'year':     v['year'] or '',
        'odometer': v['odometer'] or '',
        'fuel':     v['fuel_type'] or '',
    } for v in qs]
    return JsonResponse({'vehicles': result})

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def generate_job_number():
    from jobcard_app.utils import generate_voucher_number
    return generate_voucher_number('JobCard', JobCard, 'job_number', default_prefix='JC-')







# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
@login_required
def jobcard_list(request):
    jobs = (
        JobCard.objects
        .select_related('customer', 'workshop_vehicle', 'advisor')
        .all()
    )
    return render(request, 'jobcard_app/jobcard_list.html', {'jobs': jobs})


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

    customers = LedgerCreation.objects.filter(
        groups_id=2).order_by('ledger_name')



    items = Item.objects.filter(isDeleted=False).order_by('item_name')
    categories = ServiceCategory.objects.filter(
                     is_active=True).order_by('name')
    inspections = VehicleInspection.objects.select_related('vehicle', 'customer').order_by('-inspection_date', '-created_on')
    technicians = Staff.objects.filter(
                  status='Active',
                  staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    all_staff   = Staff.objects.filter(status='Active').order_by('full_name')
    inspection      = None
    insp_complaints = []
    insp_findings   = []
    prefill_category = ''
    prefill_findings = []

    from_inspection = request.GET.get('from_inspection')
    if from_inspection:
        try:
            inspection = VehicleInspection.objects.select_related(
                'vehicle', 'customer'
            ).prefetch_related('findings').get(pk=from_inspection)

            insp_complaints = inspection.findings.filter(
                finding_type='complaint').order_by('order')
            insp_findings   = inspection.findings.filter(
                finding_type='finding').order_by('order')
            prefill_findings = [item.description for item in insp_findings if item.description]
        except VehicleInspection.DoesNotExist:
            inspection = None

    if request.method == 'POST':
        return _save_jobcard(request, job=None)

    return render(request, 'jobcard_app/jobcard_form.html', {
        'jobcard':      None,
        'customers':    customers,
        'technicians':  technicians,
        'advisors':     advisors,     
        'all_staff':    all_staff,
        'staff':        technicians,
        'items':        items,
        'categories':   categories,
        'inspections':  inspections,
        'inspection':       inspection,
        'prefill_inspection': inspection,
        'insp_complaints':  insp_complaints,
        'insp_findings':    insp_findings,
        'prefill_findings': prefill_findings,
        'prefill_category': prefill_category,
        'today':        timezone.now().date(),
    })


@login_required
def jobcard_edit(request, pk):
    from .models import ServiceCategory

    
    job = get_object_or_404(JobCard, pk=pk)

    if request.method == 'POST':
        return _save_jobcard(request, job=job)

    from accounts_app.models import LedgerCreation
    from django.utils import timezone
    from .models import ServiceCategory
    customers   = LedgerCreation.objects.filter(
                      groups_id=2).order_by('ledger_name')
    
    categories = ServiceCategory.objects.filter(is_active=True).order_by('name')
    technicians = Staff.objects.filter(
                    status='Active',
                    staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
    return render(request, 'jobcard_app/jobcard_form.html', {
        'job':          job,
        'jobcard':      job,
        

        'customers':    customers,
        'technicians':  technicians,
        'advisors':     advisors,
        'categories':   categories,
        'staff':        technicians,
        'today':        timezone.now().date(),
        'edit_mode':    True,
    })

@transaction.atomic
def _save_jobcard(request, job=None):
    from django.utils import timezone
    from accounts_app.models import LedgerCreation
    from .models import (JobCard, JobCardComplaint, JobCardFinding,
                         JobCardPart, JobCardLabour,
                         WorkshopVehicle, VehicleInspection, ServiceCategory)

    cid      = request.POST.get('customer')
    vid      = request.POST.get('vehicle')

    date       = request.POST.get('date') or timezone.now().date()
    advisor_id = request.POST.get('advisor')
    advisor    = Staff.objects.filter(pk=advisor_id).first() if advisor_id else None

    if not cid:
        messages.error(request, 'Customer is required.')
        return redirect('jobcard_app:jobcard_create')

    customer = get_object_or_404(LedgerCreation, pk=cid)
    vehicle  = WorkshopVehicle.objects.filter(pk=vid).first() if vid else None

    # ── Create or update JobCard ──────────────────────────
    if job is None:
        job = JobCard(created_by=request.user.id)

    job.customer          = customer
    job.customer_phone    = request.POST.get('customer_phone', '')
    job.vehicle_model     = request.POST.get('vehicle_model', '')
    job.workshop_vehicle  = vehicle
    job.advisor            = advisor
    job.date               = date
    job.voucher_number      = request.POST.get('voucher_number', '') or None
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
    job.complaints.all().delete()
    job.findings.all().delete()
    job.parts.all().delete()
    job.labours.all().delete()

    # ── Complaints ────────────────────────────────────────
    categories    = request.POST.getlist('complaint_category_id[]')
    cat_texts     = request.POST.getlist('complaint_category[]')     # text fallback
    descriptions  = request.POST.getlist('complaint_description[]')
    types         = request.POST.getlist('complaint_type[]')
    tech_ids      = request.POST.getlist('complaint_technician[]')
    statuses      = request.POST.getlist('complaint_status[]')

    for i, desc in enumerate(descriptions):
        if not desc.strip():
            continue

        cat_id  = categories[i] if i < len(categories) else None
        cat_obj = ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None
        cat_txt = cat_texts[i] if i < len(cat_texts) else ''

        tech_id = tech_ids[i] if i < len(tech_ids) else None
        tech    = Staff.objects.filter(pk=tech_id).first() if tech_id else None

        JobCardComplaint.objects.create(
            jobcard            = job,
            service_category   = cat_obj,
            category           = cat_txt,
            description        = desc.strip(),
            type               = types[i] if i < len(types) else 'Mechanical',
            technician         = tech,
            status             = statuses[i] if i < len(statuses) else 'Open',
        )

    # ── Findings ──────────────────────────────────────────
    f_descriptions = request.POST.getlist('finding_description[]')
    f_tech_ids     = request.POST.getlist('finding_technician[]')
    f_statuses     = request.POST.getlist('finding_status[]')

    for i, desc in enumerate(f_descriptions):
        if not desc.strip():
            continue

        f_tech_id = f_tech_ids[i] if i < len(f_tech_ids) else None
        tech      = Staff.objects.filter(pk=f_tech_id).first() if f_tech_id else None

        JobCardFinding.objects.create(
            jobcard    = job,
            description = desc.strip(),
            technician  = tech,
            status      = f_statuses[i] if i < len(f_statuses) else 'Pending',
        )

    # ── Parts ─────────────────────────────────────────────
    part_items   = request.POST.getlist('part_item[]')
    part_numbers = request.POST.getlist('part_number[]')
    part_qtys    = request.POST.getlist('part_qty[]')
    part_rates   = request.POST.getlist('part_rate[]')

    for i, desc in enumerate(part_items):
        if not desc.strip():
            continue
        qty  = float(part_qtys[i])  if i < len(part_qtys)  else 1
        rate = float(part_rates[i]) if i < len(part_rates) else 0
        JobCardPart.objects.create(
            jobcard    = job,
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

    for i, desc in enumerate(l_descs):
        if not desc.strip():
            continue

        l_tech_id = l_tech_ids[i] if i < len(l_tech_ids) else None
        tech      = Staff.objects.filter(pk=l_tech_id).first() if l_tech_id else None

        hrs   = float(l_hours[i]) if i < len(l_hours) else 1
        rate  = float(l_rates[i]) if i < len(l_rates) else 0
        JobCardLabour.objects.create(
            jobcard    = job,
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
    vehicles = []
    if customer_id:
        qs = WorkshopVehicle.objects.filter(customer_id=customer_id, is_active=True)
        for v in qs:
            vehicles.append({
                'id': v.id,
                'label': f"{v.registration_number} — {v.make} {v.model}",
                'odometer': v.odometer,
            })
    return JsonResponse({'vehicles': vehicles})
@login_required
def _save_jobcard_complaints(request, jobcard):
    """
    Reads complaint and finding arrays from POST and saves to DB.
    Call this inside jobcard_create and jobcard_edit.
    """
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
    vehicle_id  = request.GET.get('vehicle_id', '').strip()

    if not customer_id:
        return JsonResponse({'inspections': []})

    qs = VehicleInspection.objects.select_related(
        'vehicle', 'customer', 'inspector'
    ).prefetch_related('findings').filter(customer_id=customer_id)

    if vehicle_id:
        qs = qs.filter(vehicle_id=vehicle_id)

    qs = qs.order_by('-inspection_date')[:15]

    result = []
    for insp in qs:
        complaints = list(
            insp.findings.filter(
                finding_type='complaint'
            ).order_by('order').values_list('description', flat=True)
        )
        complaints = [c for c in complaints if c and c.strip()]

        findings = list(
            insp.findings.filter(
                finding_type='finding'
            ).order_by('order').values_list('description', flat=True)
        )
        findings = [f for f in findings if f and f.strip()]

        vehicle_str = ''
        if insp.vehicle:
            vehicle_str = f"{insp.vehicle.make} {insp.vehicle.model}"
            if insp.vehicle.year:
                vehicle_str += f" ({insp.vehicle.year})"
            vehicle_str += f" · {insp.vehicle.registration_number}"

        result.append({
            'id':                insp.id,
            'inspection_number': insp.inspection_number,
            'date':              insp.inspection_date.strftime('%d %b %Y'),
            'vehicle':           vehicle_str,
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
    vid = request.POST.get('vehicle')
    jid = request.POST.get('loaded_jobcard')
    aid = request.POST.get('advisor')
    date = request.POST.get('date') or timezone.now().date()
 
    if not cid:
        messages.error(request, 'Customer is required.')
        return None
 
    customer = get_object_or_404(LedgerCreation, pk=cid)
    vehicle  = WorkshopVehicle.objects.filter(pk=vid).first() if vid else None
    jobcard  = JobCard.objects.filter(pk=jid).first() if jid else None
    advisor  = Staff.objects.filter(pk=aid).first() if aid else None
 
    if estimate is None:
        estimate = Estimate(created_by=request.user.id)
 
    estimate.customer    = customer
    estimate.vehicle     = vehicle
    estimate.jobcard    = jobcard
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
    estimate.items.all().delete()
    estimate.complaints.all().delete()
 
    # ── Parts ─────────────────────────────────────────────
    part_ids     = request.POST.getlist('part_item_id[]')
    descriptions = request.POST.getlist('description[]')
    item_refs    = request.POST.getlist('item_ref[]')
    part_nos     = request.POST.getlist('part_number[]')
    item_units   = request.POST.getlist('item_unit[]')
    quantities   = request.POST.getlist('quantity[]')
    unit_prices  = request.POST.getlist('unit_price[]')
    warranties   = request.POST.getlist('part_warranty[]')
    
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

        EstimateItem.objects.create(
            estimate    = estimate,
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
 
    for i, desc in enumerate(labour_descs):
        if not desc.strip():
            continue
        tech = Staff.objects.filter(
                pk=labour_techs[i] if i < len(labour_techs) else None).first()
        EstimateItem.objects.create(
            estimate    = estimate,
            item_type   = 'labour',
            description = desc.strip(),
            technician  = tech,
            hours       = float(labour_hours[i]) if i < len(labour_hours) else 1,
            unit_price  = float(labour_rates[i]) if i < len(labour_rates) else 0,
            order       = i,
        )
 
    # ── Customer Complaints ───────────────────────────────
    for i, c in enumerate(request.POST.getlist('customer_complaint[]')):
        if c.strip():
            EstimateComplaint.objects.create(
                estimate       = estimate,
                complaint_type = 'customer',
                description    = c.strip(),
                order          = i,
            )
 
    # ── Technician Findings ───────────────────────────────
    for i, f in enumerate(request.POST.getlist('technician_finding[]')):
        if f.strip():
            EstimateComplaint.objects.create(
                estimate       = estimate,
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
 
    qs = Estimate.objects.select_related(
        'customer', 'vehicle', 'jobcard'
    ).filter(is_active=True)
 
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
                      groups_id=2).order_by('ledger_name')
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
            return redirect('jobcard_app:estimate_detail', pk=est.pk)
 
    from jobcard_app.utils import generate_voucher_number
    return render(request, 'jobcard_app/estimate_form.html', {
        'customers':   customers,
        'technicians': technicians,
        'advisors': advisors,      
        'categories': categories,

        'prefill_job': prefill_job,
        'next_est_no': generate_voucher_number('Estimate', Estimate, 'estimate_number', default_prefix='EST-'),
        'today':       timezone.now().date(),
    })
 
 
# ─────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_detail(request, pk):
    est = get_object_or_404(
        Estimate.objects.select_related(
            'customer', 'vehicle', 'jobcard', 'advisor'
        ).prefetch_related('items', 'complaints'),
        pk=pk)
 
    parts      = est.items.filter(item_type='part')
    labour     = est.items.filter(item_type='labour')
    complaints = est.complaints.filter(complaint_type='customer')
    findings   = est.complaints.filter(complaint_type='technician')
 
    return render(request, 'jobcard_app/estimate_detail.html', {
        'est':        est,
        'parts':      parts,
        'labour':     labour,
        'complaints': complaints,
        'findings':   findings,
    })
 
 
# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
@login_required
def estimate_edit(request, pk):
    est         = get_object_or_404(Estimate, pk=pk)
    customers   = LedgerCreation.objects.filter(
                      groups_id=2).order_by('ledger_name')
    technicians = Staff.objects.filter(
                    status='Active',
                    staff_category__name='Technician').order_by('full_name')
 
    if request.method == 'POST':
        updated = _save_estimate(request, estimate=est)
        if updated:
            messages.success(
                request,
                f"Estimate {est.estimate_number} updated!")
            return redirect('jobcard_app:estimate_detail', pk=pk)
 
    parts      = est.items.filter(item_type='part')
    labour     = est.items.filter(item_type='labour')
    complaints = est.complaints.filter(complaint_type='customer')
    findings   = est.complaints.filter(complaint_type='technician')
 
    return render(request, 'jobcard_app/estimate_form.html', {
        'estimate':    est,
        'customers':   customers,
        'technicians': technicians,
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
    ).values(
        'id',
        'registration_number',
        'make',
        'model',
        'year'
    )

    result = []

    for v in qs:

        make = v['make'] or ''
        model = v['model'] or ''
        year = v['year']
        reg_no = v['registration_number'] or ''

        vehicle_model = f"{make} {model}".strip()

        if year:
            vehicle_model += f" ({year})"

        label = vehicle_model

        if reg_no:
            label += f" · {reg_no}"

        result.append({
            'id': v['id'],
            'label': label,
            'name': label,
            'make': make,
            'model': model,
            'year': year or '',
            'vehicle_model': vehicle_model,
            'registration_number': reg_no,
            'reg': reg_no,
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
    from .models import Quotation, QuotationItem, QuotationComplaint

    cid  = request.POST.get('customer')
    vid  = request.POST.get('vehicle')
    eid  = request.POST.get('loaded_estimate')
    jid  = request.POST.get('loaded_jobcard')
    aid  = request.POST.get('advisor')
    date = request.POST.get('date') or timezone.now().date()

    if not cid:
        messages.error(request, 'Customer is required.')
        return None

    customer  = get_object_or_404(LedgerCreation, pk=cid)
    vehicle   = WorkshopVehicle.objects.filter(pk=vid).first() if vid else None
    estimate  = Estimate.objects.filter(pk=eid).first()        if eid else None
    jobcard  = JobCard.objects.filter(pk=jid).first()         if jid else None
    advisor   = Staff.objects.filter(pk=aid).first()   if aid else None

    if quotation is None:
        quotation = Quotation(created_by=request.user.id)

    quotation.customer    = customer
    quotation.vehicle     = vehicle
    quotation.estimate    = estimate
    quotation.jobcard    = jobcard
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
    quotation.items.all().delete()
    quotation.complaints.all().delete()

    # ── Parts ─────────────────────────────────────────────────────────────────
    part_ids = request.POST.getlist('part_item_id[]')
    descriptions = request.POST.getlist('description[]')
    units = request.POST.getlist('item_unit[]')
    quantities = request.POST.getlist('quantity[]')
    unit_prices = request.POST.getlist('unit_price[]')
    warranties = request.POST.getlist('part_warranty[]')
    for i, desc in enumerate(descriptions):

        if not desc.strip():
            continue

        QuotationItem.objects.create(
            quotation=quotation,
            item_type='part',
            item_ref=part_ids[i] if i < len(part_ids) else '',
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

    for i, desc in enumerate(labour_descs):
        if not desc.strip():
            continue
        tech = Staff.objects.filter(
            pk=labour_techs[i] if i < len(labour_techs) else None
        ).first()
        QuotationItem.objects.create(
            quotation   = quotation,
            item_type   = 'labour',
            description = desc.strip(),
            technician  = tech,
            hours       = float(labour_hours[i]) if i < len(labour_hours) else 1,
            unit_price  = float(labour_rates[i]) if i < len(labour_rates) else 0,
            order       = i,
        )

    # ── Customer Complaints ───────────────────────────────────────────────────
    cmp_descs    = request.POST.getlist('customer_complaint[]')
    cmp_cats     = request.POST.getlist('customer_complaint_cat[]')
    cmp_types    = request.POST.getlist('customer_complaint_type[]')
    cmp_statuses = request.POST.getlist('customer_complaint_status[]')
    for i, c in enumerate(cmp_descs):
        if c.strip():
            cat_id = cmp_cats[i] if i < len(cmp_cats) else None
            cat_obj = ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None
            QuotationComplaint.objects.create(
                quotation        = quotation,
                complaint_type   = 'customer',
                description      = c.strip(),
                service_category = cat_obj,
                type             = cmp_types[i] if i < len(cmp_types) else 'Mechanical',
                status           = cmp_statuses[i] if i < len(cmp_statuses) else 'Open',
                order            = i,
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
        groups_id=2).order_by('ledger_name')
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
        ).prefetch_related('items', 'complaints').filter(pk=eid).first()

    # Pre-fill from job card
    prefill_job = None
    jcid = request.GET.get('from_jobcard')
    if jcid:
        prefill_job = JobCard.objects.select_related(
            'customer', 'workshop_vehicle'
        ).filter(pk=jcid).first()

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
    })


# ─────────────────────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────────────────────
@login_required
def quotation_detail(request, pk):
    quot = get_object_or_404(
        Quotation.objects.select_related(
            'customer', 'vehicle', 'estimate', 'jobcard', 'advisor'
        ).prefetch_related('items__technician', 'complaints'),
        pk=pk
    )
    return render(request, 'jobcard_app/quotation_detail.html', {
        'quotation':       quot,
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
    quot        = get_object_or_404(Quotation, pk=pk)
    customers   = LedgerCreation.objects.filter(
        groups_id=2).order_by('ledger_name')
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
# ─────────────────────────────────────────────────────────────
# VEHICLE LIST
# ─────────────────────────────────────────────────────────────
def wv_list(request):
    q           = request.GET.get('q', '').strip()
    customer_id = request.GET.get('customer', '')
    fuel_filter = request.GET.get('fuel', '')

    vehicles = WorkshopVehicle.objects.select_related(
        'customer').filter(is_active=True)

    if q:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=q) |
            Q(vehicle_number__icontains=q)      |
            Q(make__icontains=q)                |
            Q(model__icontains=q)               |
            Q(chassis_number__icontains=q)      |
            Q(engine_number__icontains=q)       |
            Q(customer__ledger_name__icontains=q)
        )
    if customer_id:
        vehicles = vehicles.filter(customer_id=customer_id)
    if fuel_filter:
        vehicles = vehicles.filter(fuel_type=fuel_filter)

    customers  = LedgerCreation.objects.filter(
        groups_id=2).order_by('ledger_name')
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
    customers = LedgerCreation.objects.filter(
        groups_id=2).order_by('ledger_name')

    preselected = None
    if customer_id:
        preselected = get_object_or_404(LedgerCreation, id=customer_id)

    if request.method == 'POST':
        # ── Validate required fields ──────────────────────────
        cid = request.POST.get('customer')
        reg = request.POST.get('registration_number', '').strip()
        make = request.POST.get('make', '').strip()
        model = request.POST.get('model', '').strip()

        errors = []
        if not cid:
            errors.append('Please select a customer.')
        if not reg:
            errors.append('Registration number is required.')
        if not make:
            errors.append('Make / Brand is required.')
        if not model:
            errors.append('Model is required.')
        if WorkshopVehicle.objects.filter(
                registration_number__iexact=reg, is_active=True).exists():
            errors.append(f"Vehicle with plate '{reg}' already exists.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'jobcard_app/wv_form.html', {
                'customers':   customers,
                'preselected': preselected,
                'fuel_choices': WorkshopVehicle.FUEL_CHOICES,
                'today':       timezone.now().date(),
                'post':        request.POST,
            })

        customer = get_object_or_404(LedgerCreation, id=cid)

        v = WorkshopVehicle(
            customer             = customer,
            registration_number  = reg,
            chassis_number       = request.POST.get('chassis_number')       or None,
            engine_number        = request.POST.get('engine_number')        or None,
            make                 = make,
            model                = model,
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
        return redirect('jobcard_app:wv_list', pk=v.pk)

    return render(request, 'jobcard_app/wv_form.html', {
        'customers':    customers,
        'preselected':  preselected,
        'fuel_choices': WorkshopVehicle.FUEL_CHOICES,
        'today':        timezone.now().date(),
    })



# ─────────────────────────────────────────────────────────────
# VEHICLE EDIT
# ─────────────────────────────────────────────────────────────
def wv_edit(request, pk):
    v         = get_object_or_404(WorkshopVehicle, pk=pk)
    customers = LedgerCreation.objects.filter(
        groups_id=2).order_by('ledger_name')

    if request.method == 'POST':
        make  = request.POST.get('make', '').strip()
        model = request.POST.get('model', '').strip()

        if not make or not model:
            messages.error(request, 'Make and Model are required.')
            return render(request, 'jobcard_app/wv_form.html', {
                'v':            v,
                'customers':    customers,
                'fuel_choices': WorkshopVehicle.FUEL_CHOICES,
                'today':        timezone.now().date(),
                'edit_mode':    True,
                'post':         request.POST,
            })

        v.chassis_number       = request.POST.get('chassis_number')       or None
        v.engine_number        = request.POST.get('engine_number')        or None
        v.make                 = make
        v.model                = model
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
        'v':            v,
        'customers':    customers,
        'fuel_choices': WorkshopVehicle.FUEL_CHOICES,
        'today':        timezone.now().date(),
        'edit_mode':    True,
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
        is_active=True,
        status='active'
    ).values(
        'id', 'vehicle_number', 'registration_number',
        'make', 'model', 'year', 'color',
        'odometer', 'fuel_type'
    )

    result = []
    for v in qs:
        label = f"{v['make']} {v['model']}"
        if v['year']:
            label += f" {v['year']}"
        label += f" · {v['registration_number']}"

        result.append({
            'id':          v['id'],
            'label':       label,
            'reg':         v['registration_number'],
            'make':        v['make'],
            'model':       v['model'],
            'year':        v['year'] or '',
            'color':       v['color'] or '',
            'odometer':    v['odometer'] or '',
            'fuel':        v['fuel_type'] or '',
            'veh_number':  v['vehicle_number'],
            'customer_phone': customer_phone,
        })

    return JsonResponse({'vehicles': result, 'customer_phone': customer_phone})


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
    from item_master.models import Item
    from django.utils import timezone

    cid = request.POST.get('customer')
    if not cid:
        messages.error(request, 'Customer is required.')
        return None

    customer    = get_object_or_404(LedgerCreation, pk=cid)
    vehicle     = WorkshopVehicle.objects.filter(
                      pk=request.POST.get('vehicle')).first()
    
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
    dn.vehicle          = vehicle
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

    # ── Completed Services ────────────────────────────────────
    dn.services.all().delete()
    svc_descs   = request.POST.getlist('svc_description[]')
    svc_qtys    = request.POST.getlist('svc_qty[]')
    svc_statuses = request.POST.getlist('svc_status[]')
    svc_remarks = request.POST.getlist('svc_remarks[]')
    for i, desc in enumerate(svc_descs):
        if desc.strip():
            DeliveryService.objects.create(
                delivery_note = dn,
                description   = desc.strip(),
                quantity      = float(svc_qtys[i]) if i < len(svc_qtys) else 1,
                status        = svc_statuses[i] if i < len(svc_statuses) else 'Completed',
                remarks       = svc_remarks[i] if i < len(svc_remarks) else '',
                order         = i,
            )

    if dn and dn.pk:
        for old_part in dn.parts.all():
            if old_part.item_id:
                try:
                    stock = Stock.objects.filter(
                        item_id=old_part.item_id
                    ).order_by('-id').first()
                    if stock:
                        stock.out_quantity = max(
                            0,
                            (stock.out_quantity or 0) - int(old_part.quantity)
                        )
                        stock.save()
                except Exception as e:
                    print(f'Stock restore error: {e}')

    dn.parts.all().delete()

    # ── Save new part rows ────────────────────────────────
    part_item_ids = request.POST.getlist('part_item_id[]')
    part_names    = request.POST.getlist('part_name[]')
    part_numbers  = request.POST.getlist('part_number[]')
    part_qtys     = request.POST.getlist('part_qty[]')
    part_units    = request.POST.getlist('part_unit[]')
    part_rates    = request.POST.getlist('part_rate[]')

    max_parts = max(len(part_item_ids), len(part_names), len(part_numbers))
    for i in range(max_parts):
        item_id  = part_item_ids[i] if i < len(part_item_ids) else None
        item_obj = Item.objects.filter(pk=item_id).first() if item_id else None
        name     = part_names[i] if i < len(part_names) else ''
        part_no  = part_numbers[i] if i < len(part_numbers) else ''

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
            item          = item_obj,
            name          = name.strip() or (item_obj.item_name if item_obj else 'Part'),
            item_code     = part_no.strip(),
            quantity      = qty,
            unit          = part_units[i] if i < len(part_units) else 'No',
            rate          = rate,
            order         = i,
        )

        # ── Deduct from stock ─────────────────────────────
        if item_obj:
            try:
                stock = Stock.objects.filter(
                    item_id=item_obj.id
                ).order_by('-id').first()

                if stock:
                    stock.out_quantity = (stock.out_quantity or 0) + int(qty)
                    stock.save()
                else:
                    Stock.objects.create(
                        item_id      = item_obj.id,
                        voucherDate  = timezone.now().date(),
                        in_quantity  = 0,
                        out_quantity = int(qty),
                        stock_value  = 0,
                        fyId         = 1,
                    )
            except Exception as e:
                print(f'Stock deduct error for item {item_obj.id}: {e}')

    # ── Save Labour Charges ────────────────────────────────
    dn.labours.all().delete()
    lab_descs  = request.POST.getlist('labour_desc[]')
    lab_hrs    = request.POST.getlist('labour_hrs[]')
    lab_rates  = request.POST.getlist('labour_rate[]')
    lab_techs  = request.POST.getlist('labour_technician[]')

    for i, desc in enumerate(lab_descs):
        if desc.strip():
            hrs  = float(lab_hrs[i])   if i < len(lab_hrs)   and lab_hrs[i]   else 1
            rate = float(lab_rates[i]) if i < len(lab_rates) and lab_rates[i] else 0
            tech_id = lab_techs[i] if i < len(lab_techs) and lab_techs[i] else None
            tech_obj = None
            if tech_id:
                tech_obj = Staff.objects.filter(id=tech_id).first()
            DeliveryLabour.objects.create(
                delivery_note = dn,
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

    qs = DeliveryNote.objects.select_related(
        'customer', 'vehicle', 'jobcard', 'quotation'
    ).filter(is_active=True)

    if q:
        qs = qs.filter(
            Q(delivery_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(jobcard__job_number__icontains=q) |
            Q(reg_number__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)

    all_dn = DeliveryNote.objects.filter(is_active=True)
    counts = {
        'total':     all_dn.count(),
        'draft':     all_dn.filter(status='draft').count(),
        'delivered': all_dn.filter(status='delivered').count(),
        'cancelled': all_dn.filter(status='cancelled').count(),
    }

    return render(request, 'jobcard_app/delivery_list.html', {
        'deliveries': qs,
        'q':          q,
        'status':     status,
        'counts':     counts,
    })


# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_create(request):
    customers   = LedgerCreation.objects.filter(
                      groups_id=2).order_by('ledger_name')
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
            'complaints', 'parts', 'labours'
        ).filter(pk=jcid).first()

    # Pre-fill from quotation
    prefill_quotation = None
    qid = request.GET.get('from_quotation')
    if qid:
        prefill_quotation = Quotation.objects.select_related(
            'customer', 'vehicle', 'advisor'
        ).prefetch_related(
            'items', 'complaints'
        ).filter(pk=qid).first()

    if request.method == 'POST':
        dn = _save_delivery(request)
        if dn:
            messages.success(
                request,
                f"Delivery Note {dn.delivery_number} saved!")
            return redirect('jobcard_app:delivery_list')

    from jobcard_app.utils import generate_voucher_number
    return render(request, 'jobcard_app/delivery_form.html', {
        'customers':         customers,
        'advisors':          advisors,
        'technicians':       technicians,
        'checklist_items':   _checklist_items(),
        'prefill_jc':        prefill_jc,
        'prefill_quotation': prefill_quotation,
        'next_dn_no':        generate_voucher_number('Delivery Note', DeliveryNote, 'delivery_number', default_prefix='DN-'),
        'today':             timezone.now().date(),
    })


# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_edit(request, pk):
    dn          = get_object_or_404(DeliveryNote, pk=pk)
    customers   = LedgerCreation.objects.filter(
                      groups_id=2).order_by('ledger_name')
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
                f"Delivery Note {dn.delivery_number} updated!")
            return redirect('jobcard_app:delivery_list', pk=pk)

    return render(request, 'jobcard_app/delivery_form.html', {
        'dn':              dn,
        'customers':       customers,
        'advisors':        advisors,
        'technicians':     technicians,
        'checklist_items': _checklist_items(),
        'services':        dn.services.all(),
        'parts':           dn.parts.all(),
        'labour':          dn.labours.all(),
        'edit_mode':       True,
        'today':           timezone.now().date(),
    })


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@login_required
def delivery_delete(request, pk):
    dn = get_object_or_404(DeliveryNote, pk=pk)
    if request.method == 'POST':
        num = dn.delivery_number
        dn.is_active = False
        dn.save()
        messages.success(request, f"Delivery Note {num} deleted.")
        return redirect('jobcard_app:delivery_list')
    return render(
        request,
        'jobcard_app/delivery_confirm_delete.html',
        {'dn': dn})


# ─────────────────────────────────────────────────────────────
# AJAX — search delivery notes (for invoice form)
# ─────────────────────────────────────────────────────────────
@login_required
def ajax_search_deliveries(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'deliveries': []})

    # ── Spare Parts ───────────────────────────────────────────────────────────────
    # New fields from item master dropdown
    part_item_ids = request.POST.getlist('part_item_id[]')
    part_names    = request.POST.getlist('part_name[]')
    part_codes    = request.POST.getlist('part_code[]')
    part_qtys     = request.POST.getlist('part_qty[]')
    part_units    = request.POST.getlist('part_unit[]')
    part_rates    = request.POST.getlist('part_rate[]')
    part_discs    = request.POST.getlist('part_disc[]')
    part_taxs     = request.POST.getlist('part_tax[]')

    # Build item master lookup for description/code resolution
    try:
        from item_master.models import Item as _Item
        _all_items = {str(i.id): i for i in _Item.objects.filter(isDeleted=False)}
    except Exception:
        _all_items = {}

    max_len = max(len(part_item_ids), len(part_names), len(part_codes)) if (part_item_ids or part_names or part_codes) else 0

    for i in range(max_len):
        item_id   = part_item_ids[i] if i < len(part_item_ids) else ''
        name_val  = part_names[i]    if i < len(part_names)    else ''
        code_val  = part_codes[i]    if i < len(part_codes)    else ''

        # Resolve description and code from Item Master if item_id given
        if item_id and item_id in _all_items:
            im_item   = _all_items[item_id]
            description = im_item.item_name
            code_val    = code_val or im_item.item_code or ''
        elif name_val.strip():
            description = name_val.strip()
        elif code_val.strip():
            description = code_val.strip()
        else:
            continue  # skip completely empty rows

        InvoicePart.objects.create(
            invoice      = invoice,
            item_ref     = item_id or '',
            item_code    = code_val,
            description  = description,
            quantity     = float(part_qtys[i])  if i < len(part_qtys)  else 1,
            unit         = part_units[i]         if i < len(part_units) else 'Pcs',
            unit_price   = float(part_rates[i])  if i < len(part_rates) else 0,
            discount_pct = float(part_discs[i])  if i < len(part_discs) else 0,
            tax_percent  = float(part_taxs[i])   if i < len(part_taxs)  else 8,
            order        = i,
        )

    qs = DeliveryNote.objects.select_related(
        'customer', 'vehicle'
    ).filter(is_active=True).filter(
        Q(delivery_number__icontains=q) |
        Q(customer__ledger_name__icontains=q) |
        Q(reg_number__icontains=q)
    )[:10]

    result = [{
        'id':              d.id,
        'delivery_number': d.delivery_number,
        'customer_id':     d.customer_id,
        'customer_name':   d.customer.ledger_name,
        'vehicle_id':      d.vehicle_id or '',
        'vehicle_name':    str(d.vehicle) if d.vehicle else '',
        'date':            d.date.strftime('%d %b %Y'),
        'grand_total':     d.get_grand_total(),
    } for d in qs]

    return JsonResponse({'deliveries': result})
@login_required
def ajax_get_jobcard_for_delivery(request):
    """
    Returns job cards and quotations for a customer+vehicle to load into delivery note.
    Returns: services (complaints), parts (with item_id), labour lines.
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
            'complaints', 'parts', 'labours'
        ).filter(
            customer_id=customer_id,
            is_active=True
        )

        if vehicle_id:
            qs = qs.filter(workshop_vehicle_id=vehicle_id)

        qs = qs.order_by('-date')[:15]

        result = []
        for jc in qs:

            # ── Complaints as services ────────────────────────
            services = []
            for c in jc.complaints.all():
                services.append({
                    'description': c.description or '',
                    'category':    c.category    or '',
                    'status':      'Completed',
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
                    'item_id':   str(matched_item.id) if matched_item else '',
                    'name':      name_str or (matched_item.item_name if matched_item else ''),
                    'item_code': matched_item.item_code if matched_item else code_str,
                    'unit':      _safe_unit(matched_item, 'No'),
                    'quantity':  float(p.quantity   or 1),
                    'rate':      float(p.unit_price or 0),
                    'amount':    float(p.total_price or 0),
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
                })

            result.append({
                'id':           jc.id,
                'job_number':   jc.job_number,
                'date':         jc.date.strftime('%d %b %Y'),
                'status':       jc.get_status_display(),
                'vehicle':      str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
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
            'items', 'complaints'
        ).filter(
            customer_id=customer_id
        )
        if vehicle_id:
            q_qs = q_qs.filter(vehicle_id=vehicle_id)

        q_qs = q_qs.order_by('-date')[:15]
        quotations_result = []

        for q in q_qs:
            q_services = []
            for c in q.complaints.all():
                q_services.append({
                    'description': c.description or '',
                    'category':    getattr(c, 'category', '') or '',
                    'status':      'Completed',
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
                    'item_id':   str(matched_item.id) if matched_item else (code_str if code_str.isdigit() else ''),
                    'name':      name_str or (matched_item.item_name if matched_item else ''),
                    'item_code': matched_item.item_code if matched_item else code_str,
                    'unit':      i.unit or _safe_unit(matched_item, 'No'),
                    'quantity':  float(i.quantity or 1),
                    'rate':      float(i.unit_price or 0),
                    'amount':    float(i.quantity or 1) * float(i.unit_price or 0),
                })

            q_labours = []
            for i in q.items.filter(item_type='labour'):
                q_labours.append({
                    'description': i.description or '',
                    'hours':       float(i.hours or 1),
                    'rate':        float(i.unit_price or 0),
                    'amount':      float(i.hours or 1) * float(i.unit_price or 0),
                })

            quotations_result.append({
                'id':               q.id,
                'quotation_number': q.quotation_number,
                'date':             q.date.strftime('%d %b %Y'),
                'status':           q.get_status_display(),
                'vehicle':          str(q.vehicle) if q.vehicle else '',
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
        'complaints', 'parts', 'labours'
    ).filter(is_active=True)

    if customer_id:
        jc_qs = jc_qs.filter(customer_id=customer_id)
    if vehicle_id:
        jc_qs = jc_qs.filter(workshop_vehicle_id=vehicle_id)
    if q:
        jc_qs = jc_qs.filter(job_number__icontains=q)

    jc_qs = jc_qs.order_by('-date')[:10]

    for jc in jc_qs:
        services = [{'description': c.description, 'category': getattr(c, 'category', ''), 'status': 'Completed'}
                    for c in jc.complaints.all() if c.description]
        parts    = [{'name': p.description, 'item_code': p.part_number or '',
                     'quantity': float(p.quantity or 1), 'rate': float(p.unit_price or 0),
                     'item_id': ''}
                    for p in jc.parts.all() if p.description]
        labours  = [{'description': l.description, 'hours': float(l.hours or 1),
                     'rate': float(l.rate or 0)}
                    for l in jc.labours.all() if l.description]

        result.append({
            'type':        'JC',
            'id':          jc.id,
            'number':      jc.job_number,
            'date':        jc.date.strftime('%d %b %Y'),
            'status':      jc.get_status_display(),
            'vehicle':     str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
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
        'items', 'complaints'
    )

    if customer_id:
        qt_qs = qt_qs.filter(customer_id=customer_id)
    if vehicle_id:
        qt_qs = qt_qs.filter(vehicle_id=vehicle_id)
    if q:
        qt_qs = qt_qs.filter(quotation_number__icontains=q)

    qt_qs = qt_qs.order_by('-date')[:10]

    for qt in qt_qs:
        services = [{'description': c.description, 'status': 'Completed'}
                    for c in qt.complaints.filter(complaint_type='customer')
                    if c.description]
        parts    = [{'name': i.description, 'item_code': i.item_ref or '',
                     'quantity': float(i.quantity or 1), 'rate': float(i.unit_price or 0),
                     'item_id': i.item_ref or ''}
                    for i in qt.items.filter(item_type='part') if i.description]
        labours  = [{'description': i.description, 'hours': float(i.hours or 1),
                     'rate': float(i.unit_price or 0)}
                    for i in qt.items.filter(item_type='labour') if i.description]

        result.append({
            'type':       'QT',
            'id':         qt.id,
            'number':     qt.quotation_number,
            'date':       qt.date.strftime('%d %b %Y'),
            'status':     qt.get_status_display(),
            'vehicle':    str(qt.vehicle) if qt.vehicle else '',
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

def _save_invoice(request, invoice=None):
    cid = request.POST.get('customer', '').strip()
    if not cid:
        messages.error(request, 'Customer is required.')
        return None

    customer = get_object_or_404(LedgerCreation, pk=cid)

    v_id    = request.POST.get('vehicle', '').strip()
    vehicle = WorkshopVehicle.objects.filter(pk=v_id).first() if v_id else None

    jc_id   = (request.POST.get('job_card', '').strip() or
               request.POST.get('loaded_job_card', '').strip())
    jobcard = JobCard.objects.filter(pk=jc_id).first() \
              if jc_id and jc_id.isdigit() else None

    adv_id  = request.POST.get('advisor', '').strip()
    advisor = Staff.objects.filter(pk=adv_id).first() if adv_id else None

    if invoice is None:
        invoice = Invoice(created_by=request.user.id)

    invoice.customer         = customer
    invoice.vehicle          = vehicle
    invoice.jobcard          = jobcard        # ← correct field name
    invoice.advisor          = advisor
    invoice.invoice_date     = request.POST.get('invoice_date') or timezone.now().date()
    invoice.due_date         = request.POST.get('due_date') or None
    invoice.status           = request.POST.get('status', 'draft')
    invoice.payment_mode     = request.POST.get('payment_mode', 'cash')
    invoice.customer_mobile  = request.POST.get('customer_mobile', '')
    invoice.customer_address = request.POST.get('customer_address', '')
    invoice.vehicle_model    = request.POST.get('vehicle_model', '')
    invoice.discount_pct     = request.POST.get('discount_pct') or 0
    invoice.amount_paid      = request.POST.get('amount_paid') or 0
    invoice.notes            = request.POST.get('notes', '')
    invoice.save()

    # ── Clear old lines ───────────────────────────────────
    invoice.parts.all().delete()
    invoice.labours.all().delete()
    invoice.other_charges.all().delete()

    # ── Spare Parts ───────────────────────────────────────
    part_item_ids = request.POST.getlist('part_item_id[]')
    part_names    = request.POST.getlist('part_name[]')
    part_codes    = request.POST.getlist('part_code[]')
    part_qtys     = request.POST.getlist('part_qty[]')
    part_units    = request.POST.getlist('part_unit[]')
    part_rates    = request.POST.getlist('part_rate[]')
    part_discs    = request.POST.getlist('part_disc[]')
    part_taxs     = request.POST.getlist('part_tax[]')

    row_count = max(len(part_item_ids), len(part_names), 0)

    for i in range(row_count):
        item_id  = part_item_ids[i].strip() if i < len(part_item_ids) else ''
        name_val = part_names[i].strip()    if i < len(part_names)    else ''
        code_val = part_codes[i].strip()    if i < len(part_codes)    else ''

        # skip completely empty rows
        if not item_id and not name_val:
            continue

        # resolve name from item master if hidden field was empty
        if item_id and not name_val:
            try:
                from item_master.models import Item
                item_obj = Item.objects.filter(pk=item_id).first()
                if item_obj:
                    name_val = item_obj.item_name
                    if not code_val:
                        code_val = item_obj.item_code or ''
            except Exception:
                pass

        if not name_val:
            continue

        def safe_float(lst, idx, default):
            try:
                return float(lst[idx]) if idx < len(lst) and lst[idx] else default
            except (ValueError, TypeError):
                return default

        qty  = safe_float(part_qtys,  i, 1)
        rate = safe_float(part_rates, i, 0)
        disc = safe_float(part_discs, i, 0)
        tax  = safe_float(part_taxs,  i, 8)
        unit = part_units[i] if i < len(part_units) and part_units[i] else 'Pcs'

        InvoicePart.objects.create(
            invoice      = invoice,
            item_ref     = item_id,
            item_code    = code_val,
            description  = name_val,
            quantity     = qty,
            unit         = unit,
            unit_price   = rate,
            discount_pct = disc,
            tax_percent  = tax,
            order        = i,
        )

    # ── Labour ────────────────────────────────────────────
    # InvoiceLabour fields: description, technician, hours, rate, tax_percent, order
    lab_descs = request.POST.getlist('lab_desc[]')
    lab_techs = request.POST.getlist('lab_tech[]')
    lab_hrs   = request.POST.getlist('lab_hrs[]')
    lab_rates = request.POST.getlist('lab_rate[]')
    lab_taxs  = request.POST.getlist('lab_tax[]')

    for i, desc in enumerate(lab_descs):
        if not desc.strip():
            continue

        tech_id = lab_techs[i].strip() if i < len(lab_techs) else ''
        tech    = Staff.objects.filter(pk=tech_id).first() if tech_id else None

        try:
            hrs  = float(lab_hrs[i])   if i < len(lab_hrs)   and lab_hrs[i]   else 1
        except (ValueError, TypeError):
            hrs  = 1
        try:
            rate = float(lab_rates[i]) if i < len(lab_rates) and lab_rates[i] else 0
        except (ValueError, TypeError):
            rate = 0
        try:
            tax  = float(lab_taxs[i])  if i < len(lab_taxs)  and lab_taxs[i]  else 8
        except (ValueError, TypeError):
            tax  = 8

        InvoiceLabour.objects.create(
            invoice     = invoice,
            description = desc.strip(),
            technician  = tech,
            hours       = hrs,
            rate        = rate,       # ← confirmed field name
            tax_percent = tax,
            order       = i,
        )

    # ── Other Charges ─────────────────────────────────────
    oth_descs = request.POST.getlist('oth_desc[]')
    oth_amts  = request.POST.getlist('oth_amt[]')
    oth_taxs  = request.POST.getlist('oth_tax[]')

    for i, desc in enumerate(oth_descs):
        if not desc.strip():
            continue
        try:
            amt = float(oth_amts[i]) if i < len(oth_amts) and oth_amts[i] else 0
        except (ValueError, TypeError):
            amt = 0
        try:
            tax = float(oth_taxs[i]) if i < len(oth_taxs) and oth_taxs[i] else 0
        except (ValueError, TypeError):
            tax = 0

        InvoiceOtherCharge.objects.create(
            invoice     = invoice,
            description = desc.strip(),
            amount      = amt,
            tax_percent = tax,
            order       = i,
        )

    # ── Auto update status ────────────────────────────────
    invoice.update_status()
    return invoice
# ─────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────
from django.db.models import Q

@login_required
def invoice_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    qs = Invoice.objects.select_related(
        'customer',
        'vehicle',
        'jobcard'
    ).filter(is_active=True)

    if q:
        qs = qs.filter(
            Q(invoice_number__icontains=q) |
            Q(customer__ledger_name__icontains=q) |
            Q(jobcard__job_number__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)

    if date_from:
        qs = qs.filter(invoice_date__gte=date_from)

    if date_to:
        qs = qs.filter(invoice_date__lte=date_to)

    # Dashboard Statistics
    all_invoices = Invoice.objects.filter(is_active=True)

    total_invoiced = 0
    total_paid = 0
    total_outstanding = 0

    for inv in all_invoices:
        grand = inv.get_grand_total()
        balance = inv.get_balance_due()

        total_invoiced += grand
        total_paid += float(inv.amount_paid)
        total_outstanding += balance

    stats = {
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'overdue_count': all_invoices.filter(status='overdue').count(),
    }

    counts = {
        'total': all_invoices.count(),
        'draft': all_invoices.filter(status='draft').count(),
        'sent': all_invoices.filter(status='sent').count(),
        'partial': all_invoices.filter(status='partial').count(),
        'paid': all_invoices.filter(status='paid').count(),
        'overdue': all_invoices.filter(status='overdue').count(),
        'cancelled': all_invoices.filter(status='cancelled').count(),
    }

    return render(request, 'jobcard_app/invoice_list.html', {
        'invoices': qs,
        'q': q,
        'status': status,
        'counts': counts,
        'stats': stats,
    })
 
# ─────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────
@login_required
def invoice_create(request):
    customers   = LedgerCreation.objects.filter(
                      groups_id=2).order_by('ledger_name')
    technicians = Staff.objects.filter(
                      status='Active',
                      staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')
  
 
    # Pre-fill from job card
    # Pre-fill from job card
    prefill_jc = None
    jcid = request.GET.get('from_jobcard')
    if jcid:
        prefill_jc = JobCard.objects.select_related(
            'customer', 'workshop_vehicle', 'advisor'
        ).prefetch_related(
            'parts', 'labours', 'complaints'
        ).filter(pk=jcid).first()
 
    if request.method == 'POST':
        inv = _save_invoice(request)
        if inv:
            messages.success(
                request,
                f"Invoice {inv.invoice_number} created!")
            return redirect('jobcard_app:invoice_list')
 
    from jobcard_app.utils import generate_voucher_number
    return render(request, 'jobcard_app/invoice_form.html', {
        'customers':   customers,
        'technicians': technicians,
        'advisors':    advisors,
        'prefill_jc':  prefill_jc,
        'next_inv_no': generate_voucher_number('Invoice', Invoice, 'invoice_number', default_prefix='INV-'),
        'today':       timezone.now().date(),
    })
 
 
# ─────────────────────────────────────────────────────────────
# DETAIL
# ─────────────────────────────────────────────────────────────
@login_required
def invoice_detail(request, pk):
    return redirect('jobcard_app:invoice_edit', pk=pk)
 
 
# ─────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────
@login_required
def invoice_edit(request, pk):
    inv         = get_object_or_404(Invoice, pk=pk)
    customers   = LedgerCreation.objects.filter(
                      groups_id=2).order_by('ledger_name')
    technicians = Staff.objects.filter(
                      status='Active',
                      staff_category__name='Technician').order_by('full_name')
    advisors    = Staff.objects.filter(status='Active').order_by('full_name')

 
    if request.method == 'POST':
        updated = _save_invoice(request, invoice=inv)
        if updated:
            messages.success(
                request,
                f"Invoice {inv.invoice_number} updated!")
            return redirect('jobcard_app:invoice_list')
 
    return render(request, 'jobcard_app/invoice_form.html', {
        'invoice':       inv,
        'customers':     customers,
        'technicians':   technicians,
        'advisors':      advisors,
        'parts':         inv.parts.all(),
        'labour':        inv.labours.all(),
        'other_charges': inv.other_charges.all(),
        'edit_mode':     True,
        'today':         timezone.now().date(),
    })
 
 
# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────
@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    invoice.delete()

    return redirect('jobcard_app:invoice_list')


# ─────────────────────────────────────────────────────────────
# AJAX — GET DOCUMENTS FOR INVOICE (Delivery Notes & Job Cards)
# ─────────────────────────────────────────────────────────────
@login_required
def ajax_get_docs_for_invoice(request):
    """
    Fetch active Delivery Notes and Job Cards for a given customer & vehicle
    to load data into the Invoice creation/editing form.
    """
    customer_id = request.GET.get('customer_id', '').strip()
    vehicle_id  = request.GET.get('vehicle_id', '').strip()

    if not customer_id:
        return JsonResponse({'delivery_notes': [], 'jobcards': []})

    delivery_notes_result = []
    jobcards_result = []

    try:
        from item_master.models import Item
        items_by_id = {str(i.id): i for i in Item.objects.filter(isDeleted=False)}
        items_by_code = {i.item_code.lower(): i for i in Item.objects.filter(isDeleted=False) if i.item_code}
        items_by_name = {i.item_name.lower(): i for i in Item.objects.filter(isDeleted=False) if i.item_name}

        # 1. Fetch Delivery Notes
        dn_qs = DeliveryNote.objects.select_related(
            'customer', 'vehicle', 'jobcard'
        ).prefetch_related('parts', 'labours', 'services').filter(
            customer_id=customer_id,
            is_active=True
        )

        if vehicle_id:
            dn_qs = dn_qs.filter(vehicle_id=vehicle_id)

        dn_qs = dn_qs.order_by('-date')[:15]

        for dn in dn_qs:
            parts = []
            for p in dn.parts.all():
                matched_item = None
                if p.item_id and str(p.item_id) in items_by_id:
                    matched_item = items_by_id[str(p.item_id)]
                elif p.item_code and p.item_code.lower() in items_by_code:
                    matched_item = items_by_code[p.item_code.lower()]
                elif p.name and p.name.lower() in items_by_name:
                    matched_item = items_by_name[p.name.lower()]

                parts.append({
                    'item_id':      str(matched_item.id) if matched_item else (str(p.item_id) if p.item_id else ''),
                    'part_code':    p.item_code or (matched_item.item_code if matched_item else ''),
                    'description':  p.name or (matched_item.item_name if matched_item else ''),
                    'quantity':     float(p.quantity or 1),
                    'unit':         p.unit or 'Pcs',
                    'rate':         float(p.rate or 0),
                    'discount_pct': 0,
                    'tax_percent':  8,
                    'amount':       float(p.rate or 0) * float(p.quantity or 1),
                })

            labours = []
            for l in dn.labours.all():
                labours.append({
                    'description':    l.description or '',
                    'technician_id':  str(l.technician_id) if l.technician_id else '',
                    'technician_name': l.technician.full_name if l.technician else '',
                    'hours':          float(l.hours or 1),
                    'rate':           float(l.rate or 0),
                    'tax_percent':    8,
                    'amount':         float(l.amount or 0),
                })

            delivery_notes_result.append({
                'id':              dn.id,
                'number':          dn.delivery_number,
                'date':            dn.date.strftime('%d %b %Y'),
                'status':          dn.get_status_display(),
                'vehicle_id':      dn.vehicle_id or '',
                'vehicle_name':    str(dn.vehicle) if dn.vehicle else '',
                'job_card_id':     dn.jobcard_id or '',
                'job_number':      dn.jobcard.job_number if dn.jobcard else '',
                'parts':           parts,
                'labours':         labours,
                'parts_count':     len(parts),
                'labours_count':   len(labours),
            })

        # 2. Fetch Job Cards
        jc_qs = JobCard.objects.select_related(
            'workshop_vehicle', 'advisor'
        ).prefetch_related('parts', 'labours', 'complaints').filter(
            customer_id=customer_id,
            is_active=True
        )

        if vehicle_id:
            jc_qs = jc_qs.filter(workshop_vehicle_id=vehicle_id)

        jc_qs = jc_qs.order_by('-date')[:15]

        for jc in jc_qs:
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
                    'item_id':      str(matched_item.id) if matched_item else '',
                    'part_code':    matched_item.item_code if matched_item else code_str,
                    'description':  name_str or (matched_item.item_name if matched_item else ''),
                    'quantity':     float(p.quantity or 1),
                    'unit':         'Pcs',
                    'rate':         float(p.unit_price or 0),
                    'discount_pct': 0,
                    'tax_percent': 8,
                    'amount':       float(p.total_price or 0),
                })

            labours = []
            for l in jc.labours.all():
                labours.append({
                    'description':    l.description or '',
                    'technician_id':  str(l.technician_id) if l.technician_id else '',
                    'technician_name': l.technician.full_name if l.technician else '',
                    'hours':          float(l.hours or 1),
                    'rate':           float(l.rate or 0),
                    'tax_percent':    float(getattr(l, 'tax_percent', 8) or 8),
                    'amount':         float(l.amount or (l.hours * l.rate if l.hours and l.rate else 0)),
                })

            jobcards_result.append({
                'id':            jc.id,
                'number':        jc.job_number,
                'date':          jc.date.strftime('%d %b %Y'),
                'status':        jc.get_status_display(),
                'vehicle_id':    jc.workshop_vehicle_id or '',
                'vehicle_name':  str(jc.workshop_vehicle) if jc.workshop_vehicle else '',
                'parts':         parts,
                'labours':       labours,
                'parts_count':   len(parts),
                'labours_count': len(labours),
            })

    except Exception as e:
        import traceback
        print(f"Error in ajax_get_docs_for_invoice: {e}")
        traceback.print_exc()

    return JsonResponse({
        'delivery_notes': delivery_notes_result,
        'jobcards':       jobcards_result,
    })
