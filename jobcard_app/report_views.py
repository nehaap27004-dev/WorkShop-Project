from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import JobCardPart
from .models import JobCard
from datetime import date
from django.db.models import Sum
from item_master.models import PurchaseMaster, PurchaseDetail
from django.db.models import Q, Exists, OuterRef
from .models import DeliveryNote, Invoice
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import VehicleInspection
from fleet_app.models import Staff
from django.shortcuts import render
from django.db.models import Prefetch
from .models import WorkshopVehicle
from .models import (
    VehicleInspection,
    MechanicalInspection,
    InteriorInspection,
    AccessoriesInspection,
    ExteriorDamage,
    InspectionFinding,
)
from django.shortcuts import render
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from item_master.models import Item, Stock
from django.shortcuts import render
from django.db.models import Count
from django.utils.dateparse import parse_date
from .models import VehicleInspection
from .models import Invoice
from django.db.models import Count
from django.utils.dateparse import parse_date
from django.db.models.functions import Lower, Trim
from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.paginator import Paginator

from .models import (
    JobCard,
    WorkshopVehicle,
    JobCardComplaint,
    JobCardFinding,
)

def jobcard_status_report(request):

    jobcards = (
        JobCard.objects
        .filter(is_active=True)
        .select_related(
            'customer',
            'advisor',
            'workshop_vehicle'
        )
        .prefetch_related(
            'vehicles__vehicle',
            'complaints__technician',
            'findings__technician',
            'labours__technician',
            'parts'
        )
        .order_by('-date', '-id')
    )

    # Filters
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if status:
        jobcards = jobcards.filter(status=status)

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            jobcards = jobcards.filter(date__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            jobcards = jobcards.filter(date__lte=parsed_to)

    if search:
        jobcards = jobcards.filter(
            Q(voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(workshop_vehicle__vehicle_number__icontains=search) |
            Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    # Prepare report rows
    report_rows = []

    for job in jobcards:

        # Vehicle numbers
        vehicle_numbers = [
            entry.vehicle.vehicle_number
            for entry in job.vehicles.all()
        ]

        if not vehicle_numbers and job.workshop_vehicle:
            vehicle_numbers.append(
                job.workshop_vehicle.vehicle_number
            )

        # Collect assigned technicians
        technicians = set()

        for complaint in job.complaints.all():
            if complaint.technician:
                technicians.add(str(complaint.technician))

        for finding in job.findings.all():
            if finding.technician:
                technicians.add(str(finding.technician))

        for labour in job.labours.all():
            if labour.technician:
                technicians.add(str(labour.technician))

        report_rows.append({
            'job_number': job.voucher_number,
            'date': job.date,
            'vehicle_number': ', '.join(vehicle_numbers),
            'customer': job.customer.ledger_name,
            'technician': ', '.join(sorted(technicians)),
            'status': job.get_status_display(),
            'priority': job.get_priority_display(),
            'amount': job.grand_total,
        })

    context = {
        'report_rows': report_rows,
        'status_choices': JobCard.STATUS_CHOICES,
        'search': search,
        'selected_status': status,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(
        request,
        'jobcard_app/reports/jobcard_status_report.html',
        context
    )



def open_jobcard_report(request):

    # Show jobs that have not been closed or cancelled
    jobcards = (
        JobCard.objects
        .filter(
            is_active=True,
            status__in=['open', 'in_progress', 'waiting', 'completed']
        )
        .select_related(
            'customer',
            'advisor',
            'workshop_vehicle'
        )
        .prefetch_related(
            'vehicles__vehicle',
            'complaints__technician',
            'findings__technician',
            'labours__technician',
            'parts'
        )
        .order_by('-date', '-id')
    )

    # Read filters
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            jobcards = jobcards.filter(date__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            jobcards = jobcards.filter(date__lte=parsed_to)

    if search:
        jobcards = jobcards.filter(
            Q(voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(workshop_vehicle__vehicle_number__icontains=search) |
            Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    report_rows = []

    for job in jobcards:

        # Get vehicle numbers
        vehicle_numbers = [
            entry.vehicle.vehicle_number
            for entry in job.vehicles.all()
        ]

        if not vehicle_numbers and job.workshop_vehicle:
            vehicle_numbers.append(
                job.workshop_vehicle.vehicle_number
            )

        # Get assigned technicians
        technicians = set()

        for complaint in job.complaints.all():
            if complaint.technician:
                technicians.add(str(complaint.technician))

        for finding in job.findings.all():
            if finding.technician:
                technicians.add(str(finding.technician))

        for labour in job.labours.all():
            if labour.technician:
                technicians.add(str(labour.technician))

        report_rows.append({
            'job_number': job.voucher_number,
            'date': job.date,
            'vehicle_number': ', '.join(vehicle_numbers),
            'customer': job.customer.ledger_name,
            'technician': ', '.join(sorted(technicians)),
            'status': job.get_status_display(),
            'priority': job.get_priority_display(),
            'amount': job.grand_total,
        })

    context = {
        'report_rows': report_rows,
        'search': search,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(
        request,
        'jobcard_app/reports/open_jobcard_report.html',
        context
    )

def work_in_progress_report(request):

    # Only job cards currently under repair
    jobcards = (
        JobCard.objects
        .filter(
            is_active=True,
            status='in_progress'
        )
        .select_related(
            'customer',
            'advisor',
            'workshop_vehicle'
        )
        .prefetch_related(
            'vehicles__vehicle',
            'complaints__technician',
            'findings__technician',
            'labours__technician',
            'parts'
        )
        .order_by('-date', '-id')
    )

    # Filters
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            jobcards = jobcards.filter(date__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            jobcards = jobcards.filter(date__lte=parsed_to)

    if search:
        jobcards = jobcards.filter(
            Q(voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(workshop_vehicle__vehicle_number__icontains=search) |
            Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    report_rows = []

    for job in jobcards:

        # Vehicle numbers
        vehicle_numbers = [
            entry.vehicle.vehicle_number
            for entry in job.vehicles.all()
        ]

        if not vehicle_numbers and job.workshop_vehicle:
            vehicle_numbers.append(
                job.workshop_vehicle.vehicle_number
            )

        # Assigned technicians
        technicians = set()

        for complaint in job.complaints.all():
            if complaint.technician:
                technicians.add(str(complaint.technician))

        for finding in job.findings.all():
            if finding.technician:
                technicians.add(str(finding.technician))

        for labour in job.labours.all():
            if labour.technician:
                technicians.add(str(labour.technician))

        report_rows.append({
            'job_number': job.voucher_number,
            'date': job.date,
            'vehicle_number': ', '.join(vehicle_numbers),
            'customer': job.customer.ledger_name,
            'technician': ', '.join(sorted(technicians)),
            'priority': job.get_priority_display(),
            'amount': job.grand_total,
        })

    context = {
        'report_rows': report_rows,
        'search': search,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(
        request,
        'jobcard_app/reports/work_in_progress_report.html',
        context
    )
def delivered_not_invoiced_report(request):

    # Find active invoices linked directly to this Delivery Note
    # OR linked to its Job Card.
    invoice_exists = (
        Invoice.objects
        .filter(is_active=True)
        .exclude(status='cancelled')
        .filter(
            Q(delivery_note_id=OuterRef('pk')) |
            Q(jobcard_id=OuterRef('jobcard_id'))
        )
    )

    delivery_notes = (
        DeliveryNote.objects
        .filter(
            is_active=True,
            status='delivered',
            jobcard__isnull=False
        )
        .annotate(
            has_invoice=Exists(invoice_exists)
        )
        .filter(has_invoice=False)
        .select_related(
            'customer',
            'jobcard',
            'vehicle',
            'technician',
            'advisor'
        )
        .prefetch_related(
            'vehicles__vehicle',
            'parts',
            'labours',
            'services'
        )
        .order_by('-date', '-id')
    )

    # Filters
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            delivery_notes = delivery_notes.filter(
                date__gte=parsed_from
            )

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            delivery_notes = delivery_notes.filter(
                date__lte=parsed_to
            )

    if search:
        delivery_notes = delivery_notes.filter(
            Q(voucher_number__icontains=search) |
            Q(jobcard__voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(reg_number__icontains=search) |
            Q(vehicle__vehicle_number__icontains=search) |
            Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    report_rows = []

    for dn in delivery_notes:

        # Get attached vehicle numbers
        vehicle_numbers = [
            entry.vehicle.vehicle_number
            for entry in dn.vehicles.all()
            if entry.vehicle
        ]

        # Fallback to the main vehicle
        if not vehicle_numbers and dn.vehicle:
            vehicle_numbers.append(
                dn.vehicle.vehicle_number
            )

        # Fallback to registration number
        if not vehicle_numbers and dn.reg_number:
            vehicle_numbers.append(dn.reg_number)

        # Delivery Note technician
        technician_name = (
            str(dn.technician)
            if dn.technician else "-"
        )

        # Delivery Note amount
        amount = dn.get_grand_total()

        report_rows.append({
            'delivery_number': dn.voucher_number,
            'job_number': dn.jobcard.voucher_number,
            'delivery_date': dn.date,
            'vehicle_number': ', '.join(vehicle_numbers),
            'customer': dn.customer.ledger_name,
            'technician': technician_name,
            'amount': amount,
        })

    total_amount = sum(
        (row['amount'] for row in report_rows),
        0
    )

    context = {
        'report_rows': report_rows,
        'search': search,
        'from_date': from_date,
        'to_date': to_date,
        'total_amount': total_amount,
    }

    return render(
        request,
        'jobcard_app/reports/delivered_not_invoiced_report.html',
        context
    )
def invoiced_payment_pending_report(request):

    today = timezone.localdate()

    # Include invoices linked directly to a Job Card,
    # or linked through a Delivery Note that belongs to a Job Card.
    invoices = (
        Invoice.objects
        .filter(
            is_active=True
        )
        .filter(
            Q(jobcard__isnull=False) |
            Q(delivery_note__jobcard__isnull=False)
        )
        .exclude(status__in=['draft', 'cancelled'])
        .select_related(
            'customer',
            'jobcard',
            'jobcard__workshop_vehicle',
            'delivery_note',
            'delivery_note__jobcard',
            'delivery_note__vehicle',
            'vehicle',
        )
        .prefetch_related(
            'items',
            'jobcard__vehicles__vehicle',
            'delivery_note__vehicles__vehicle',
        )
        .order_by('-invoice_date', '-id')
    )

    # Filters
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            invoices = invoices.filter(
                invoice_date__gte=parsed_from
            )

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            invoices = invoices.filter(
                invoice_date__lte=parsed_to
            )

    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(jobcard__voucher_number__icontains=search) |
            Q(delivery_note__jobcard__voucher_number__icontains=search) |
            Q(vehicle__vehicle_number__icontains=search) |
            Q(jobcard__workshop_vehicle__vehicle_number__icontains=search) |
            Q(jobcard__vehicles__vehicle__vehicle_number__icontains=search) |
            Q(delivery_note__vehicle__vehicle_number__icontains=search) |
            Q(delivery_note__vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    report_rows = []
    total_outstanding = Decimal('0.000')

    for invoice in invoices:

        # Calculate invoice total and outstanding balance
        invoice_total = Decimal(
            str(invoice.get_grand_total() or 0)
        ).quantize(
            Decimal('0.001'),
            rounding=ROUND_HALF_UP
        )

        amount_paid = Decimal(
            str(invoice.amount_paid or 0)
        ).quantize(
            Decimal('0.001'),
            rounding=ROUND_HALF_UP
        )

        balance_due = (
            invoice_total - amount_paid
        ).quantize(
            Decimal('0.001'),
            rounding=ROUND_HALF_UP
        )

        # Skip fully paid invoices
        if balance_due <= 0:
            continue

        # Resolve linked Job Card
        job = invoice.jobcard

        if not job and invoice.delivery_note:
            job = invoice.delivery_note.jobcard

        # Collect vehicle numbers
        vehicle_numbers = set()

        if invoice.vehicle:
            vehicle_numbers.add(
                invoice.vehicle.vehicle_number
            )

        if invoice.delivery_note:
            dn = invoice.delivery_note

            if dn.vehicle:
                vehicle_numbers.add(dn.vehicle.vehicle_number)

            for entry in dn.vehicles.all():
                if entry.vehicle:
                    vehicle_numbers.add(
                        entry.vehicle.vehicle_number
                    )

        if job:
            if job.workshop_vehicle:
                vehicle_numbers.add(
                    job.workshop_vehicle.vehicle_number
                )

            for entry in job.vehicles.all():
                if entry.vehicle:
                    vehicle_numbers.add(
                        entry.vehicle.vehicle_number
                    )

        # Determine payment status using actual outstanding balance
        if invoice.due_date and invoice.due_date < today:
            payment_status = 'Overdue'
            days_overdue = (today - invoice.due_date).days

        elif amount_paid > 0:
            payment_status = 'Partially Paid'
            days_overdue = 0

        else:
            payment_status = 'Unpaid'
            days_overdue = 0

        report_rows.append({
            'invoice_number': (
                invoice.display_number
            ),
            'job_number': (
                job.voucher_number if job else '-'
            ),
            'invoice_date': invoice.invoice_date,
            'due_date': invoice.due_date,
            'vehicle_number': ', '.join(
                sorted(vehicle_numbers)
            ),
            'customer': invoice.customer.ledger_name,
            'payment_mode': invoice.get_payment_mode_display(),
            'invoice_total': invoice_total,
            'amount_paid': amount_paid,
            'balance_due': balance_due,
            'payment_status': payment_status,
            'days_overdue': days_overdue,
        })

        total_outstanding += balance_due

    context = {
        'report_rows': report_rows,
        'search': search,
        'from_date': from_date,
        'to_date': to_date,
        'total_outstanding': total_outstanding,
    }

    return render(
        request,
        'jobcard_app/reports/invoiced_payment_pending_report.html',
        context
    )

@login_required
def technician_pending_jobs_report(request):
    from django.db.models import Q
    from django.utils.dateparse import parse_date
    from .models import JobCardComplaint, JobCardFinding
    from fleet_app.models import Staff

    search = request.GET.get('search', '').strip()
    technician_id = request.GET.get('technician', '').strip()
    task_status = request.GET.get('task_status', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    # Only active Job Cards that are still being worked on
    active_job_statuses = ['open', 'in_progress', 'waiting']

    complaint_qs = JobCardComplaint.objects.filter(
        jobcard__is_active=True,
        jobcard__status__in=active_job_statuses,
        technician__isnull=False,
        status__in=['Open', 'In Progress']
    ).select_related(
        'jobcard',
        'jobcard__customer',
        'jobcard__workshop_vehicle',
        'technician'
    ).prefetch_related('jobcard__vehicles__vehicle')

    finding_qs = JobCardFinding.objects.filter(
        jobcard__is_active=True,
        jobcard__status__in=active_job_statuses,
        technician__isnull=False,
        status__in=['Pending', 'Confirmed']
    ).select_related(
        'jobcard',
        'jobcard__customer',
        'jobcard__workshop_vehicle',
        'technician'
    ).prefetch_related('jobcard__vehicles__vehicle')

    # Keep the technician dropdown populated from all assigned technicians
    assigned_ids = set(
        complaint_qs.values_list('technician_id', flat=True)
    ) | set(
        finding_qs.values_list('technician_id', flat=True)
    )
    assigned_ids.discard(None)

    technicians = Staff.objects.filter(
        pk__in=assigned_ids
    ).order_by('full_name')

    # Search filter
    if search:
        complaint_qs = complaint_qs.filter(
            Q(jobcard__voucher_number__icontains=search) |
            Q(jobcard__customer__ledger_name__icontains=search) |
            Q(jobcard__workshop_vehicle__vehicle_number__icontains=search) |
            Q(jobcard__vehicles__vehicle__vehicle_number__icontains=search) |
            Q(technician__full_name__icontains=search) |
            Q(description__icontains=search)
        ).distinct()

        finding_qs = finding_qs.filter(
            Q(jobcard__voucher_number__icontains=search) |
            Q(jobcard__customer__ledger_name__icontains=search) |
            Q(jobcard__workshop_vehicle__vehicle_number__icontains=search) |
            Q(jobcard__vehicles__vehicle__vehicle_number__icontains=search) |
            Q(technician__full_name__icontains=search) |
            Q(description__icontains=search)
        ).distinct()

    # Technician filter
    if technician_id:
        complaint_qs = complaint_qs.filter(
            technician_id=technician_id
        )
        finding_qs = finding_qs.filter(
            technician_id=technician_id
        )

    # Job Card date filters
    parsed_from_date = parse_date(from_date) if from_date else None
    parsed_to_date = parse_date(to_date) if to_date else None

    if parsed_from_date:
        complaint_qs = complaint_qs.filter(
            jobcard__date__gte=parsed_from_date
        )
        finding_qs = finding_qs.filter(
            jobcard__date__gte=parsed_from_date
        )

    if parsed_to_date:
        complaint_qs = complaint_qs.filter(
            jobcard__date__lte=parsed_to_date
        )
        finding_qs = finding_qs.filter(
            jobcard__date__lte=parsed_to_date
        )

    # Task status filter
    if task_status:
        complaint_qs = complaint_qs.filter(status=task_status)
        finding_qs = finding_qs.filter(status=task_status)

    report_rows = []

    def get_job_vehicle_names(job):
        names = []

        if job.workshop_vehicle:
            names.append(job.workshop_vehicle.vehicle_number)

        for job_vehicle in job.vehicles.all():
            if job_vehicle.vehicle:
                names.append(job_vehicle.vehicle.vehicle_number)

        # Remove duplicate vehicle numbers while preserving order
        names = list(dict.fromkeys(
            name for name in names if name
        ))

        return ', '.join(names) if names else '-'

    # Complaint tasks
    for item in complaint_qs:
        job = item.jobcard

        report_rows.append({
            'job_id': job.id,
            'job_number': job.voucher_number or '-',
            'job_date': job.date,
            'customer': job.customer.ledger_name,
            'vehicle': get_job_vehicle_names(job),
            'technician': item.technician.full_name,
            'task_type': 'Complaint',
            'description': item.description,
            'task_status': item.get_status_display(),
            'job_status': job.get_status_display(),
            'expected_delivery': job.delivery_date,
        })

    # Finding tasks
    for item in finding_qs:
        job = item.jobcard

        report_rows.append({
            'job_id': job.id,
            'job_number': job.voucher_number or '-',
            'job_date': job.date,
            'customer': job.customer.ledger_name,
            'vehicle': get_job_vehicle_names(job),
            'technician': item.technician.full_name,
            'task_type': 'Finding',
            'description': item.description,
            'task_status': item.get_status_display(),
            'job_status': job.get_status_display(),
            'expected_delivery': job.delivery_date,
        })

    # Newest Job Cards first
    report_rows.sort(
        key=lambda row: (row['job_date'], row['job_number']),
        reverse=True
    )

    total_pending_tasks = len(report_rows)
    total_pending_jobs = len({
        row['job_id'] for row in report_rows
    })
    total_technicians = len({
        row['technician'] for row in report_rows
    })

    return render(
        request,
        'jobcard_app/reports/technician_pending_jobs_report.html',
        {
            'report_rows': report_rows,
            'technicians': technicians,
            'search': search,
            'technician_id': technician_id,
            'task_status': task_status,
            'from_date': from_date,
            'to_date': to_date,
            'total_pending_tasks': total_pending_tasks,
            'total_pending_jobs': total_pending_jobs,
            'total_technicians': total_technicians,
        }
    )

def get_all_categorized_reports():
    """
    Returns organized inventory of all reports across the system,
    structured into categorized subgroups with pre-resolved URLs.
    """
    from django.urls import reverse

    categories = [
        {
            'id': 'operations',
            'title': 'Workshop Operations',
            'icon': 'bi-gear-wide-connected',
            'accent': '#76213b',
            'badge_class': 'badge-maroon',
            'description': 'Job cards, active workflow, preventive service, inspections and workshop staff output.',
            'subgroups': [
                {
                    'id': 'jobcard_workflow',
                    'title': 'Job Cards & Workflow',
                    'icon': 'bi-card-checklist',
                    'reports': [
                        {
                            'id': 'jc_status',
                            'name': 'Job Card Status',
                            'description': 'Real-time status overview across all active and historical jobs.',
                            'url_name': 'jobcard_app:jobcard_status_report',
                            'icon': 'bi-bar-chart-line',
                            'color': '#e11d48',
                            'badge': 'Live',
                            'badge_type': 'primary',
                            'is_pinned': True,
                        },
                        {
                            'id': 'jc_open',
                            'name': 'Open Job Cards',
                            'description': 'Job cards currently opened and awaiting execution or closure.',
                            'url_name': 'jobcard_app:open_jobcard_report',
                            'icon': 'bi-folder2-open',
                            'color': '#f59e0b',
                            'badge': 'Active',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                        {
                            'id': 'jc_wip',
                            'name': 'Work In Progress (WIP)',
                            'description': 'Active workshop floor repairs and ongoing service operations.',
                            'url_name': 'jobcard_app:work_in_progress_report',
                            'icon': 'bi-gear',
                            'color': '#0284c7',
                            'badge': 'Floor',
                            'badge_type': 'info',
                            'is_pinned': True,
                        },
                        {
                            'id': 'jc_aging',
                            'name': 'Job Card Aging Report',
                            'description': 'Aging buckets for open job cards to identify bottlenecks.',
                            'url_name': 'jobcard_app:jobcard_aging_report',
                            'icon': 'bi-hourglass-split',
                            'color': '#ef4444',
                            'badge': 'Aging',
                            'badge_type': 'danger',
                            'is_pinned': False,
                        },
                        {
                            'id': 'jc_completed_not_delivered',
                            'name': 'Completed – Not Delivered',
                            'description': 'Completed jobs ready for collection awaiting gate delivery.',
                            'url_name': 'jobcard_app:completed_not_delivered_report',
                            'icon': 'bi-check2-circle',
                            'color': '#10b981',
                            'badge': 'Ready',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                        {
                            'id': 'jc_delivered_not_invoiced',
                            'name': 'Delivered – Not Invoiced',
                            'description': 'Delivered vehicles with pending invoice and billing generation.',
                            'url_name': 'jobcard_app:delivered_not_invoiced_report',
                            'icon': 'bi-truck',
                            'color': '#d97706',
                            'badge': 'Billing Due',
                            'badge_type': 'warning',
                            'is_pinned': True,
                        },
                        {
                            'id': 'jc_invoiced_payment_pending',
                            'name': 'Invoiced – Payment Pending',
                            'description': 'Billed invoices awaiting full payment collection or settlement.',
                            'url_name': 'jobcard_app:invoiced_payment_pending_report',
                            'icon': 'bi-wallet2',
                            'color': '#8b5cf6',
                            'badge': 'Unpaid',
                            'badge_type': 'danger',
                            'is_pinned': False,
                        },
                    ]
                },
                {
                    'id': 'service_repairs',
                    'title': 'Service & Repairs',
                    'icon': 'bi-tools',
                    'reports': [
                        {
                            'id': 'sr_register',
                            'name': 'Service Register',
                            'description': 'Master register of all maintenance schedules, services and repairs.',
                            'url_name': 'jobcard_app:service_register_report',
                            'icon': 'bi-journal-text',
                            'color': '#2563eb',
                            'badge': 'Register',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'sr_due',
                            'name': 'Service Due Report',
                            'description': 'Vehicles due for periodic maintenance based on time & odometer.',
                            'url_name': 'jobcard_app:service_due_report',
                            'icon': 'bi-calendar-check',
                            'color': '#ea580c',
                            'badge': 'Alerts',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                        {
                            'id': 'sr_repair_register',
                            'name': 'Repair Register',
                            'description': 'Corrective repairs, mechanical works and system overhaul logs.',
                            'url_name': 'jobcard_app:repair_register_report',
                            'icon': 'bi-wrench-adjustable',
                            'color': '#059669',
                            'badge': 'Repairs',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'sr_rework',
                            'name': 'Rework & Recall Analysis',
                            'description': 'Repeat complaints, rework instances, warranty claims and root cause.',
                            'url_name': 'jobcard_app:rework_report',
                            'icon': 'bi-arrow-repeat',
                            'color': '#dc2626',
                            'badge': 'QA',
                            'badge_type': 'danger',
                            'is_pinned': False,
                        },
                    ]
                },
                {
                    'id': 'vehicle_inspections',
                    'title': 'Vehicle Inspections',
                    'icon': 'bi-clipboard-check',
                    'reports': [
                        {
                            'id': 'insp_register',
                            'name': 'Inspection Register',
                            'description': 'Complete log of vehicle check-in inspections and checklists.',
                            'url_name': 'jobcard_app:inspection_register_report',
                            'icon': 'bi-clipboard-check',
                            'color': '#0284c7',
                            'badge': 'Check-in',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'insp_summary',
                            'name': 'Inspection Status Summary',
                            'description': 'Pass, warning and failure statistical breakdown across vehicle systems.',
                            'url_name': 'jobcard_app:inspection_status_summary_report',
                            'icon': 'bi-pie-chart',
                            'color': '#7c3aed',
                            'badge': 'Summary',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'insp_failed',
                            'name': 'Failed Inspection Items',
                            'description': 'Damaged components, safety issues and missing accessories identified.',
                            'url_name': 'jobcard_app:failed_inspection_items_report',
                            'icon': 'bi-exclamation-triangle',
                            'color': '#e11d48',
                            'badge': 'Defects',
                            'badge_type': 'danger',
                            'is_pinned': False,
                        },
                        {
                            'id': 'insp_vehicle_history',
                            'name': 'Vehicle Inspection History',
                            'description': 'Recurring conditions, wear trends and previous check-in histories.',
                            'url_name': 'jobcard_app:vehicle_inspection_history_report',
                            'icon': 'bi-clock-history',
                            'color': '#64748b',
                            'badge': 'History',
                            'badge_type': 'secondary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'insp_custom_list',
                            'name': 'Inspection Records Master',
                            'description': 'Direct access to all vehicle inspection records and forms.',
                            'url_name': 'jobcard_app:inspection_list',
                            'icon': 'bi-card-checklist',
                            'color': '#0d9488',
                            'badge': 'Master',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                    ]
                },
                {
                    'id': 'productivity_workforce',
                    'title': 'Productivity & Staff',
                    'icon': 'bi-speedometer2',
                    'reports': [
                        {
                            'id': 'jc_daily_activity',
                            'name': 'Daily Workshop Activity',
                            'description': 'Daily intake, throughput, deliveries and technician assignments.',
                            'url_name': 'jobcard_app:daily_workshop_activity_report',
                            'icon': 'bi-calendar-day',
                            'color': '#0891b2',
                            'badge': 'Daily',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'jc_monthly_performance',
                            'name': 'Monthly Performance',
                            'description': 'Monthly job volume trends, revenue and completion metrics.',
                            'url_name': 'jobcard_app:monthly_performance_report',
                            'icon': 'bi-calendar3',
                            'color': '#4f46e5',
                            'badge': 'Monthly',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'jc_turnaround',
                            'name': 'Job Turnaround Time (TAT)',
                            'description': 'Time from gate entry to vehicle delivery analysis.',
                            'url_name': 'jobcard_app:job_turnaround_report',
                            'icon': 'bi-stopwatch',
                            'color': '#d97706',
                            'badge': 'Speed',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                        {
                            'id': 'jc_efficiency',
                            'name': 'Workshop Efficiency',
                            'description': 'Target hours vs actual hours, capacity utilization and rating.',
                            'url_name': 'jobcard_app:workshop_efficiency_report',
                            'icon': 'bi-speedometer2',
                            'color': '#16a34a',
                            'badge': 'KPI',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                        {
                            'id': 'tech_perf',
                            'name': 'Technician Performance',
                            'description': 'Jobs assigned, completed, efficiency ratios and throughput.',
                            'url_name': 'jobcard_app:technician_performance_report',
                            'icon': 'bi-person-check',
                            'color': '#9333ea',
                            'badge': 'Performance',
                            'badge_type': 'primary',
                            'is_pinned': True,
                        },
                        {
                            'id': 'tech_pending',
                            'name': 'Technician Pending Jobs',
                            'description': 'Current open task backlogs and workload distribution per staff.',
                            'url_name': 'jobcard_app:technician_pending_jobs_report',
                            'icon': 'bi-person-lines-fill',
                            'color': '#ea580c',
                            'badge': 'Backlog',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                        {
                            'id': 'tech_rev',
                            'name': 'Technician-wise Revenue',
                            'description': 'Labour revenue generated per technician and service category.',
                            'url_name': 'jobcard_app:technician_revenue_report',
                            'icon': 'bi-currency-exchange',
                            'color': '#059669',
                            'badge': 'Labour Rev',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                    ]
                },
            ]
        },
        {
            'id': 'inventory',
            'title': 'Inventory & Stock',
            'icon': 'bi-box-seam',
            'accent': '#059669',
            'badge_class': 'badge-green',
            'description': 'Parts consumption, warehouse stock levels, low inventory alerts and purchase margins.',
            'subgroups': [
                {
                    'id': 'stock_control',
                    'title': 'Stock Control & Usage',
                    'icon': 'bi-boxes',
                    'reports': [
                        {
                            'id': 'parts_stock',
                            'name': 'Stock Inventory Report',
                            'description': 'Live quantities on hand, warehouse valuation and ledger balances.',
                            'url_name': 'jobcard_app:parts_stock_report',
                            'icon': 'bi-boxes',
                            'color': '#0284c7',
                            'badge': 'Live Stock',
                            'badge_type': 'success',
                            'is_pinned': True,
                        },
                        {
                            'id': 'parts_consumption',
                            'name': 'Parts Consumption Report',
                            'description': 'Quantity and value of spare parts fitted across all job cards.',
                            'url_name': 'jobcard_app:parts_consumption_report',
                            'icon': 'bi-gear',
                            'color': '#6366f1',
                            'badge': 'Consumption',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'parts_low_stock',
                            'name': 'Low Stock Alert',
                            'description': 'Critical items below reorder threshold needing urgent purchase.',
                            'url_name': 'jobcard_app:low_stock_report',
                            'icon': 'bi-shield-exclamation',
                            'color': '#dc2626',
                            'badge': 'Critical',
                            'badge_type': 'danger',
                            'is_pinned': True,
                        },
                    ]
                },
                {
                    'id': 'procurement_margins',
                    'title': 'Procurement & Margins',
                    'icon': 'bi-cart-check',
                    'reports': [
                        {
                            'id': 'parts_purchase',
                            'name': 'Parts Purchase Report',
                            'description': 'Vendor procurement logs, purchase receipts and supplier rates.',
                            'url_name': 'jobcard_app:parts_purchase_report',
                            'icon': 'bi-cart-check',
                            'color': '#2563eb',
                            'badge': 'Procurement',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'parts_profitability',
                            'name': 'Parts Profitability',
                            'description': 'Cost price vs billed price margin and gross profit analysis.',
                            'url_name': 'jobcard_app:parts_profitability_report',
                            'icon': 'bi-cash-coin',
                            'color': '#16a34a',
                            'badge': 'Profit Margin',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                    ]
                },
            ]
        },
        {
            'id': 'billing',
            'title': 'Billing & Deliveries',
            'icon': 'bi-receipt',
            'accent': '#c2185b',
            'badge_class': 'badge-pink',
            'description': 'Customer invoices, summary registers, VAT/tax breakdowns and delivery handovers.',
            'subgroups': [
                {
                    'id': 'invoicing_taxes',
                    'title': 'Invoices & Taxes',
                    'icon': 'bi-receipt-cutoff',
                    'reports': [
                        {
                            'id': 'inv_register',
                            'name': 'Invoice Register',
                            'description': 'Comprehensive ledger of all customer invoices, credit notes and dates.',
                            'url_name': 'jobcard_app:invoice_register_report',
                            'icon': 'bi-receipt',
                            'color': '#4f46e5',
                            'badge': 'Invoices',
                            'badge_type': 'primary',
                            'is_pinned': True,
                        },
                        {
                            'id': 'inv_summary',
                            'name': 'Invoice Summary',
                            'description': 'Aggregated billing totals, payment collection statuses and metrics.',
                            'url_name': 'jobcard_app:invoice_summary_report',
                            'icon': 'bi-graph-up',
                            'color': '#0284c7',
                            'badge': 'Aggregates',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'inv_tax',
                            'name': 'Invoice Tax Report',
                            'description': 'Taxable amounts, tax rates, input/output VAT breakdown.',
                            'url_name': 'jobcard_app:invoice_tax_report',
                            'icon': 'bi-percent',
                            'color': '#d97706',
                            'badge': 'VAT / Tax',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                    ]
                },
                {
                    'id': 'deliveries',
                    'title': 'Gate Delivery Tracking',
                    'icon': 'bi-box-arrow-up-right',
                    'reports': [
                        {
                            'id': 'del_register',
                            'name': 'Delivery Register',
                            'description': 'Vehicle handovers, delivery notes, recipient signatures and gate pass.',
                            'url_name': 'jobcard_app:delivery_register_report',
                            'icon': 'bi-box-arrow-up-right',
                            'color': '#059669',
                            'badge': 'Delivery Note',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                    ]
                },
            ]
        },
        {
            'id': 'customers',
            'title': 'Customers & Vehicles',
            'icon': 'bi-car-front',
            'accent': '#d97706',
            'badge_class': 'badge-orange',
            'description': 'Customer revenue, lifetime visit records, fleet registers and repair cost breakdowns.',
            'subgroups': [
                {
                    'id': 'crm_analytics',
                    'title': 'Customer Intelligence',
                    'icon': 'bi-person-badge',
                    'reports': [
                        {
                            'id': 'cust_history',
                            'name': 'Customer History',
                            'description': 'Full chronological job card and billing archive for selected clients.',
                            'url_name': 'jobcard_app:customer_history_report',
                            'icon': 'bi-person-badge',
                            'color': '#2563eb',
                            'badge': 'CRM',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'cust_revenue',
                            'name': 'Customer-wise Revenue',
                            'description': 'Total revenue, collected payments and outstanding sums per customer.',
                            'url_name': 'jobcard_app:customer_revenue_report',
                            'icon': 'bi-cash-coin',
                            'color': '#16a34a',
                            'badge': 'Revenue',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                        {
                            'id': 'cust_repeat',
                            'name': 'Repeat Customer Analysis',
                            'description': 'Retention rate, multi-visit customers, visit frequency and intervals.',
                            'url_name': 'jobcard_app:repeat_customer_report',
                            'icon': 'bi-arrow-repeat',
                            'color': '#9333ea',
                            'badge': 'Retention',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                    ]
                },
                {
                    'id': 'fleet_analytics',
                    'title': 'Vehicle Analytics & Fleet',
                    'icon': 'bi-car-front-fill',
                    'reports': [
                        {
                            'id': 'veh_register',
                            'name': 'Vehicle Register',
                            'description': 'All registered workshop vehicles with owner, specs and service counts.',
                            'url_name': 'jobcard_app:vehicle_register_report',
                            'icon': 'bi-car-front',
                            'color': '#0284c7',
                            'badge': 'Fleet Master',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'veh_history',
                            'name': 'Vehicle History',
                            'description': 'Lifecycle maintenance timeline and job history per vehicle.',
                            'url_name': 'jobcard_app:vehicle_history_report',
                            'icon': 'bi-clock-history',
                            'color': '#64748b',
                            'badge': 'Timeline',
                            'badge_type': 'secondary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'veh_cost',
                            'name': 'Vehicle Repair Cost Analysis',
                            'description': 'Cumulative parts and labour expenditure grouped by vehicle.',
                            'url_name': 'jobcard_app:vehicle_repair_cost_report',
                            'icon': 'bi-calculator',
                            'color': '#ea580c',
                            'badge': 'Cost Matrix',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                        {
                            'id': 'veh_make_model',
                            'name': 'Make & Model Breakdown',
                            'description': 'Job frequency and total repair expenses grouped by brand & model.',
                            'url_name': 'jobcard_app:vehicle_make_model_report',
                            'icon': 'bi-bar-chart-steps',
                            'color': '#0891b2',
                            'badge': 'Make/Model',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                    ]
                },
            ]
        },
        {
            'id': 'financial',
            'title': 'Financial & Accounts',
            'icon': 'bi-wallet2',
            'accent': '#1e293b',
            'badge_class': 'badge-dark',
            'description': 'Receivables, payables, aging, trial balance, P&L, balance sheet and workshop financials.',
            'subgroups': [
                {
                    'id': 'receivables_payables',
                    'title': 'Receivables, Payables & Ageing',
                    'icon': 'bi-cash-stack',
                    'reports': [
                        {
                            'id': 'fin_cust_out',
                            'name': 'Customer Outstanding',
                            'description': 'Debtor ledger balances, overdue receivables and pending collections.',
                            'url_name': 'accounts_app:new_client_outstanding_report',
                            'icon': 'bi-person',
                            'color': '#dc2626',
                            'badge': 'Receivables',
                            'badge_type': 'danger',
                            'is_pinned': True,
                        },
                        {
                            'id': 'fin_supp_out',
                            'name': 'Vendor Outstanding',
                            'description': 'Creditor payables due to parts suppliers, vendors and contractors.',
                            'url_name': 'accounts_app:new_supplier_outstanding_report',
                            'icon': 'bi-truck',
                            'color': '#d97706',
                            'badge': 'Payables',
                            'badge_type': 'warning',
                            'is_pinned': True,
                        },
                        {
                            'id': 'fin_bill_by_bill',
                            'name': 'Bill-by-Bill Report',
                            'description': 'Detailed bill-level matching, invoice adjustments and remaining balances.',
                            'url_name': 'accounts_app:bill_by_bill_report',
                            'icon': 'bi-receipt-cutoff',
                            'color': '#2563eb',
                            'badge': 'Bills',
                            'badge_type': 'primary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_aging',
                            'name': 'Financial Aging Report',
                            'description': 'Aging buckets (0-30, 31-60, 61-90, 90+ days) for client dues.',
                            'url_name': 'accounts_app:aging_report',
                            'icon': 'bi-calendar3-range',
                            'color': '#ef4444',
                            'badge': 'Aging',
                            'badge_type': 'danger',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_client_pdc',
                            'name': 'Client PDC Register',
                            'description': 'Customer post-dated cheques in hand and maturity calendar.',
                            'url_name': 'accounts_app:client_pdc_report',
                            'icon': 'bi-card-checklist',
                            'color': '#0284c7',
                            'badge': 'PDC In',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_supp_pdc',
                            'name': 'Supplier PDC Register',
                            'description': 'Issued supplier cheques, scheduled disbursements and clearances.',
                            'url_name': 'accounts_app:supplier_pdc_report',
                            'icon': 'bi-credit-card-2-front',
                            'color': '#64748b',
                            'badge': 'PDC Out',
                            'badge_type': 'secondary',
                            'is_pinned': False,
                        },
                    ]
                },
                {
                    'id': 'statements_analysis',
                    'title': 'Ledgers & Financial Statements',
                    'icon': 'bi-file-earmark-bar-graph',
                    'reports': [
                        {
                            'id': 'fin_ledger_report',
                            'name': 'General Ledger Report',
                            'description': 'Detailed activity statement for any individual ledger account.',
                            'url_name': 'accounts_app:ledger_report_page',
                            'icon': 'bi-book',
                            'color': '#4f46e5',
                            'badge': 'Ledger',
                            'badge_type': 'primary',
                            'is_pinned': True,
                        },
                        {
                            'id': 'fin_ledger_posting',
                            'name': 'Ledger Posting Journal',
                            'description': 'Chronological audit trail of all posted debit and credit vouchers.',
                            'url_name': 'accounts_app:ledger_posting_list',
                            'icon': 'bi-journal-text',
                            'color': '#64748b',
                            'badge': 'Audit Trail',
                            'badge_type': 'secondary',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_trial_balance',
                            'name': 'Trial Balance',
                            'description': 'Comprehensive debit and credit balances verifying ledger equality.',
                            'url_name': 'fleet_app:trial_balance_report',
                            'icon': 'bi-calculator',
                            'color': '#0284c7',
                            'badge': 'Trial Balance',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_balance_sheet',
                            'name': 'Balance Sheet',
                            'description': 'Statement of financial position (Assets, Liabilities & Equity).',
                            'url_name': 'fleet_app:balance_sheet',
                            'icon': 'bi-file-earmark-bar-graph',
                            'color': '#2563eb',
                            'badge': 'Balance Sheet',
                            'badge_type': 'primary',
                            'is_pinned': True,
                        },
                        {
                            'id': 'fin_profit_loss',
                            'name': 'Profit & Loss Statement',
                            'description': 'Statement of operations, workshop revenues, expenses and net profit.',
                            'url_name': 'fleet_app:profit_loss',
                            'icon': 'bi-graph-up-arrow',
                            'color': '#16a34a',
                            'badge': 'Income Statement',
                            'badge_type': 'success',
                            'is_pinned': True,
                        },
                        {
                            'id': 'fin_workshop_expenses',
                            'name': 'Workshop Expense Report',
                            'description': 'Overhead expenditure, tooling, facility and operating costs.',
                            'url_name': 'jobcard_app:expense_report',
                            'icon': 'bi-cash-stack',
                            'color': '#ea580c',
                            'badge': 'Expenses',
                            'badge_type': 'warning',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_workshop_revenue',
                            'name': 'Workshop Revenue Analysis',
                            'description': 'Revenue streams breakdown (labour, parts, sublet services).',
                            'url_name': 'jobcard_app:workshop_revenue_report',
                            'icon': 'bi-graph-up',
                            'color': '#10b981',
                            'badge': 'Revenue Stream',
                            'badge_type': 'success',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_vehicle_pl',
                            'name': 'Vehicle Profit & Loss',
                            'description': 'Profitability breakdown per vehicle asset and commercial fleet unit.',
                            'url_name': 'fleet_app:vehicle_pl_report',
                            'icon': 'bi-truck-flatbed',
                            'color': '#0891b2',
                            'badge': 'Vehicle P&L',
                            'badge_type': 'info',
                            'is_pinned': False,
                        },
                        {
                            'id': 'fin_asset_report',
                            'name': 'Fixed Asset Master Report',
                            'description': 'Machinery, workshop tools, depreciation and asset values.',
                            'url_name': 'fleet_app:asset_report',
                            'icon': 'bi-building',
                            'color': '#64748b',
                            'badge': 'Fixed Assets',
                            'badge_type': 'secondary',
                            'is_pinned': False,
                        },
                    ]
                },
            ]
        },
    ]

    total_reports = 0
    total_subgroups = 0

    for cat in categories:
        cat_report_count = 0
        for sub in cat['subgroups']:
            total_subgroups += 1
            for rep in sub['reports']:
                total_reports += 1
                cat_report_count += 1
                try:
                    rep['url'] = reverse(rep['url_name'])
                except Exception:
                    rep['url'] = '#'
                rep['category_id'] = cat['id']
                rep['category_title'] = cat['title']
                rep['subgroup_title'] = sub['title']
        cat['report_count'] = cat_report_count

    return {
        'categories': categories,
        'total_reports': total_reports,
        'total_categories': len(categories),
        'total_subgroups': total_subgroups,
    }


@login_required
def jobcard_reports_dashboard(request):
    reports_data = get_all_categorized_reports()
    raw_category = request.GET.get('category', '').strip()

    category_alias_map = {
        'jobcards': 'operations',
        'service-repairs': 'operations',
        'technicians': 'operations',
        'operations': 'operations',
        'inventory': 'inventory',
        'billing-delivery': 'billing',
        'billing': 'billing',
        'customers-vehicles': 'customers',
        'customers': 'customers',
        'financial': 'financial',
        'finance': 'financial',
    }

    if raw_category in category_alias_map:
        selected_category = category_alias_map[raw_category]
    else:
        # Default to the first category (e.g. Workshop Operations) so user is not overwhelmed
        selected_category = reports_data['categories'][0]['id']

    current_category = next(
        (cat for cat in reports_data['categories'] if cat['id'] == selected_category),
        reports_data['categories'][0]
    )

    search_query = request.GET.get('search', '').strip()

    context = {
        **reports_data,
        'selected_category': selected_category,
        'current_category': current_category,
        'search_query': search_query,
        'page_title': f"{current_category['title']} Reports",
    }
    return render(
        request,
        'jobcard_app/reports/jobcard_reports_dashboard.html',
        context
    )

@login_required
def completed_not_delivered_report(request):
    from django.db.models import Exists, OuterRef, Q
    from django.utils.dateparse import parse_date
    from decimal import Decimal
    from .models import JobCard, DeliveryNote

    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    # Find delivered delivery notes linked to each Job Card
    delivered_notes = DeliveryNote.objects.filter(
        jobcard_id=OuterRef('pk'),
        is_active=True,
        status='delivered'
    )

    # Completed Job Cards without a delivered Delivery Note
    jobs = JobCard.objects.filter(
        is_active=True,
        status='completed'
    ).annotate(
        has_delivered_note=Exists(delivered_notes)
    ).filter(
        has_delivered_note=False
    ).select_related(
        'customer',
        'workshop_vehicle',
        'advisor'
    ).prefetch_related(
        'vehicles__vehicle',
        'complaints__technician',
        'findings__technician',
        'labours__technician'
    ).order_by('-date', '-id')

    # Search
    if search:
        jobs = jobs.filter(
            Q(voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(workshop_vehicle__vehicle_number__icontains=search) |
            Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    # Date filters
    start_date = parse_date(from_date) if from_date else None
    end_date = parse_date(to_date) if to_date else None

    if start_date:
        jobs = jobs.filter(date__gte=start_date)

    if end_date:
        jobs = jobs.filter(date__lte=end_date)

    report_rows = []
    total_amount = Decimal('0.000')

    for job in jobs:
        # Collect vehicle numbers
        vehicle_names = []

        if job.workshop_vehicle:
            vehicle_names.append(
                job.workshop_vehicle.vehicle_number
            )

        for job_vehicle in job.vehicles.all():
            if job_vehicle.vehicle:
                vehicle_names.append(
                    job_vehicle.vehicle.vehicle_number
                )

        vehicle_names = list(dict.fromkeys(vehicle_names))
        vehicle_number = ', '.join(vehicle_names) if vehicle_names else '-'

        # Collect assigned technicians
        technician_names = set()

        for complaint in job.complaints.all():
            if complaint.technician:
                technician_names.add(
                    complaint.technician.full_name
                )

        for finding in job.findings.all():
            if finding.technician:
                technician_names.add(
                    finding.technician.full_name
                )

        for labour in job.labours.all():
            if labour.technician:
                technician_names.add(
                    labour.technician.full_name
                )

        technicians = ', '.join(sorted(technician_names)) if technician_names else '-'

        amount = Decimal(str(job.grand_total or 0))
        total_amount += amount

        report_rows.append({
            'job': job,
            'jobcard': job,
            'job_number': job.voucher_number or '-',
            'job_date': job.date,
            'customer': job.customer.ledger_name,
            'vehicle': vehicle_number,
            'technicians': technicians,
            'techs': technicians,
            'priority': job.get_priority_display(),
            'expected_delivery': job.delivery_date,
            'amount': amount,
            'job_amount': amount,
        })

    return render(
        request,
        'jobcard_app/reports/completed_not_delivered_report.html',
        {
            'report_rows': report_rows,
            'jobs': report_rows,
            'total_jobs': len(report_rows),
            'total_amount': total_amount,
            'search': search,
            'from_date': from_date,
            'to_date': to_date,
        }
    )
@login_required
def jobcard_aging_report(request):
    from django.db.models import Q
    from django.utils import timezone
    from django.utils.dateparse import parse_date
    from .models import JobCard

    today = timezone.localdate()

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '').strip()
    aging_category = request.GET.get('aging_category', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    # Only pending Job Cards
    jobs = JobCard.objects.filter(
        is_active=True,
        status__in=['open', 'in_progress', 'waiting']
    ).select_related(
        'customer',
        'advisor',
        'workshop_vehicle'
    ).prefetch_related(
        'vehicles__vehicle',
        'complaints__technician',
        'findings__technician',
        'labours__technician'
    ).order_by('date', 'id')

    # Search
    if search:
        jobs = jobs.filter(
            Q(voucher_number__icontains=search) |
            Q(customer__ledger_name__icontains=search) |
            Q(workshop_vehicle__vehicle_number__icontains=search) |
            Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    # Status filter
    if status in ['open', 'in_progress', 'waiting']:
        jobs = jobs.filter(status=status)

    # Date filters
    start_date = parse_date(from_date) if from_date else None
    end_date = parse_date(to_date) if to_date else None

    if start_date:
        jobs = jobs.filter(date__gte=start_date)

    if end_date:
        jobs = jobs.filter(date__lte=end_date)

    report_rows = []

    aging_counts = {
        'today': 0,
        'one_to_three': 0,
        'four_to_seven': 0,
        'eight_to_fifteen': 0,
        'above_fifteen': 0,
    }

    for job in jobs:

        # Calculate pending days
        days_pending = (
            (today - job.date).days
            if job.date else 0
        )

        days_pending = max(days_pending, 0)

        # Determine aging category
        if days_pending == 0:
            category = 'today'
            category_label = 'Today'
        elif days_pending <= 3:
            category = 'one_to_three'
            category_label = '1–3 Days'
        elif days_pending <= 7:
            category = 'four_to_seven'
            category_label = '4–7 Days'
        elif days_pending <= 15:
            category = 'eight_to_fifteen'
            category_label = '8–15 Days'
        else:
            category = 'above_fifteen'
            category_label = 'Above 15 Days'

        # Aging category filter
        if aging_category and category != aging_category:
            continue

        aging_counts[category] += 1

        if aging_category and category != aging_category:
            continue

        # Vehicle details
        vehicle_names = []

        if job.workshop_vehicle:
            vehicle_names.append(
                job.workshop_vehicle.vehicle_number
            )

        for job_vehicle in job.vehicles.all():
            if job_vehicle.vehicle:
                vehicle_names.append(
                    job_vehicle.vehicle.vehicle_number
                )

        vehicle_number = ', '.join(
            dict.fromkeys(vehicle_names)
        ) or '-'

        # Technician details
        technician_names = set()

        for complaint in job.complaints.all():
            if complaint.technician:
                technician_names.add(
                    complaint.technician.full_name
                )

        for finding in job.findings.all():
            if finding.technician:
                technician_names.add(
                    finding.technician.full_name
                )

        for labour in job.labours.all():
            if labour.technician:
                technician_names.add(
                    labour.technician.full_name
                )

        technicians = ', '.join(
            sorted(technician_names)
        ) or '-'

        report_rows.append({
            'job': job,
            'job_number': job.voucher_number or '-',
            'job_date': job.date,
            'customer': (
                job.customer.ledger_name
                if job.customer else '-'
            ),
            'vehicle': vehicle_number,
            'technicians': technicians,
            'status': job.get_status_display(),
            'priority': job.get_priority_display(),
            'expected_delivery': job.delivery_date,
            'days_pending': days_pending,
            'aging_category': category,
            'aging_label': category_label,
        })

    total_jobs = len(report_rows)

    oldest_pending_days = max(
        (row['days_pending'] for row in report_rows),
        default=0
    )

    context = {
        'report_rows': report_rows,
        'total_jobs': total_jobs,
        'aging_counts': aging_counts,
        'oldest_pending_days': oldest_pending_days,
        'search': search,
        'status': status,
        'aging_category': aging_category,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(
        request,
        'jobcard_app/reports/jobcard_aging.html',
        context
    )


@login_required(login_url='accounts_app:admin_login')
def inspection_reports_dashboard(request):
    return render(
        request,
        'accounts_app/reports/report_category_dashboard.html',
        {
            'dashboard_title': 'Inspection Reports',
            'dashboard_description': 'View and analyze vehicle inspection activities.',
            'reports': [
                {
                    'name': 'Inspection Register',
                    'description': 'View and filter all vehicle inspections.',
                    'icon': 'bi-clipboard-check',
                    'url_name': 'jobcard_app:inspection_register_report',
                },
                {
                    'name': 'Failed Inspection Items',
                    'description': 'Identify poor conditions, damaged components and missing vehicle accessories.',
                    'icon': 'bi-exclamation-triangle',
                    'url_name': 'jobcard_app:failed_inspection_items_report',
                },
                {
                    'name': 'Vehicle Inspection History',
                    'description': 'Review previous inspections, recurring problems and vehicle condition history.',
                    'icon': 'bi-clock-history',
                    'url_name': 'jobcard_app:vehicle_inspection_history_report',
                },
                {
                    'name': 'Inspection Status Summary',
                    'description': 'View inspection pass, attention and failure statistics with inspector-wise analysis.',
                    'icon': 'bi-bar-chart',
                    'url_name': 'jobcard_app:inspection_status_summary_report',
                },
                {
                    'name': 'Inspection History',
                    'description': 'View previous inspection records.',
                    'url_name': 'jobcard_app:inspection_list',
                    'icon': 'bi-clock-history',
                },
                {
                    'name': 'Technician Inspection',
                    'description': 'Technician-wise inspection report.',
                    'url_name': None,
                    'icon': 'bi-person-badge',
                },
            ]
        }
    )








def inspection_register_report(request):

    inspections = VehicleInspection.objects.select_related(
        'vehicle',
        'customer',
        'jobcard',
        'inspector',
        'voucherType'
    ).prefetch_related(
        'exterior_damages',
        'findings'
    ).all()

    # -------------------------
    # FILTER VALUES
    # -------------------------
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    selected_status = request.GET.get('status', '')
    selected_inspector = request.GET.get('inspector', '')

    # -------------------------
    # SEARCH
    # -------------------------
    if search:
        inspections = inspections.filter(
            Q(voucher_number__icontains=search) |
            Q(driver_name__icontains=search) |
            Q(vehicle__registration_number__icontains=search) |
            Q(vehicle__vehicle_number__icontains=search) |
            Q(customer__ledger_name__icontains=search)
        )

    # -------------------------
    # DATE FILTERS
    # -------------------------
    if from_date:
        inspections = inspections.filter(
            inspection_date__gte=from_date
        )

    if to_date:
        inspections = inspections.filter(
            inspection_date__lte=to_date
        )

    # -------------------------
    # STATUS FILTER
    # -------------------------
    if selected_status:
        inspections = inspections.filter(
            overall_status=selected_status
        )

    # -------------------------
    # INSPECTOR FILTER
    # -------------------------
    if selected_inspector:
        inspections = inspections.filter(
            inspector_id=selected_inspector
        )

    # -------------------------
    # INSPECTORS
    # -------------------------
    inspectors = Staff.objects.filter(
        status='Active'
    ).order_by('full_name')

    # -------------------------
    # STATUS CHOICES
    # -------------------------
    status_choices = VehicleInspection.STATUS_CHOICES

    # -------------------------
    # CONTEXT
    # -------------------------
    context = {
        'inspections': inspections,

        'search': search,
        'from_date': from_date,
        'to_date': to_date,

        'selected_status': selected_status,
        'selected_inspector': selected_inspector,

        'status_choices': status_choices,
        'inspectors': inspectors,

        'total_inspections': inspections.count(),
    }

    return render(
        request,
        'jobcard_app/reports/inspection_register_report.html',
        context
    )

from django.shortcuts import render
from django.db.models import Q

from .models import (
    VehicleInspection,
    MechanicalInspection,
    InteriorInspection,
    AccessoriesInspection,
    ExteriorDamage,
)


def failed_inspection_items_report(request):

    inspections = VehicleInspection.objects.select_related(
        'vehicle',
        'customer',
        'jobcard',
        'inspector',
    ).prefetch_related(
        'exterior_damages',
        'findings',
    ).order_by('-inspection_date', '-created_on')

    # FILTERS
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    selected_category = request.GET.get('category', '')
    selected_condition = request.GET.get('condition', '')

    # DATE FILTER
    if from_date:
        inspections = inspections.filter(
            inspection_date__gte=from_date
        )

    if to_date:
        inspections = inspections.filter(
            inspection_date__lte=to_date
        )

    # SEARCH
    if search:
        inspections = inspections.filter(
            Q(voucher_number__icontains=search) |
            Q(driver_name__icontains=search) |
            Q(vehicle__registration_number__icontains=search) |
            Q(vehicle__vehicle_number__icontains=search)
        )

    # CONDITION LABELS
    condition_labels = {
        'poor': 'Poor',
        'fair': 'Fair',
        'missing': 'Missing',
        'damaged': 'Damaged',
    }

    # CATEGORY LABELS
    category_labels = {
        'mechanical': 'Mechanical',
        'interior': 'Interior',
        'accessories': 'Accessories',
        'exterior': 'Exterior Damage',
    }

    report_rows = []

    # --------------------------------------------------
    # MECHANICAL INSPECTION
    # --------------------------------------------------
    mechanical_fields = [
        'oil_leak',
        'coolant_leak',
        'abnormal_noise',
        'brake_pad',
        'brake_disc',
        'shock_absorbers',
        'bushes',
        'battery',
        'starter',
        'lights',
        'tyre_fl',
        'tyre_fr',
        'tyre_rl',
        'tyre_rr',
        'tyre_spare',
        'brake_fluid',
        'steering_fluid',
        'washer_fluid',
        'exhaust_system',
    ]

    # --------------------------------------------------
    # INTERIOR INSPECTION
    # --------------------------------------------------
    interior_fields = [
        'dashboard',
        'seats',
        'steering_wheel',
        'ac_system',
        'audio_system',
        'windows',
        'seat_belts',
        'floor_carpet',
        'headliner',
        'door_panels',
    ]

    # --------------------------------------------------
    # ACCESSORIES INSPECTION
    # --------------------------------------------------
    accessory_fields = [
        'spare_wheel',
        'tool_kit',
        'service_book',
        'remote_key',
        'safety_triangle',
        'floor_mat',
        'jack',
        'fire_extinguisher',
        'first_aid_kit',
    ]

    for inspection in inspections:

        vehicle = inspection.vehicle

        vehicle_name = (
            vehicle.registration_number
            or vehicle.vehicle_number
            or '-'
        )

        customer_name = str(inspection.customer)

        inspection_number = (
            inspection.voucher_number or '-'
        )

        # ==============================================
        # MECHANICAL
        # ==============================================
        mechanical = getattr(
            inspection, 'mechanical', None
        )

        if mechanical:

            for field_name in mechanical_fields:

                value = getattr(mechanical, field_name, None)

                if value in ('poor', 'fair'):

                    field_obj = mechanical._meta.get_field(field_name)

                    item_name = field_obj.verbose_name

                    condition = dict(
                        mechanical.CONDITION_CHOICES
                    ).get(value, value)

                    report_rows.append({
                        'inspection': inspection,
                        'inspection_number': inspection_number,
                        'inspection_date': inspection.inspection_date,
                        'vehicle': vehicle_name,
                        'customer': customer_name,
                        'category': 'mechanical',
                        'category_label': 'Mechanical',
                        'item': str(item_name).title(),
                        'condition': value,
                        'condition_label': condition,
                        'notes': '',
                    })

        # ==============================================
        # INTERIOR
        # ==============================================
        interior = getattr(
            inspection, 'interior', None
        )

        if interior:

            for field_name in interior_fields:

                value = getattr(interior, field_name, None)

                if value in ('poor', 'fair'):

                    field_obj = interior._meta.get_field(field_name)

                    item_name = field_obj.verbose_name

                    condition = dict(
                        interior.CONDITION_CHOICES
                    ).get(value, value)

                    report_rows.append({
                        'inspection': inspection,
                        'inspection_number': inspection_number,
                        'inspection_date': inspection.inspection_date,
                        'vehicle': vehicle_name,
                        'customer': customer_name,
                        'category': 'interior',
                        'category_label': 'Interior',
                        'item': str(item_name).title(),
                        'condition': value,
                        'condition_label': condition,
                        'notes': '',
                    })

        # ==============================================
        # ACCESSORIES
        # ==============================================
        accessories = getattr(
            inspection, 'accessories', None
        )

        if accessories:

            for field_name in accessory_fields:

                value = getattr(accessories, field_name, None)

                if value in ('missing', 'damaged'):

                    field_obj = accessories._meta.get_field(field_name)

                    item_name = field_obj.verbose_name

                    condition = dict(
                        accessories.STATUS_CHOICES
                    ).get(value, value)

                    report_rows.append({
                        'inspection': inspection,
                        'inspection_number': inspection_number,
                        'inspection_date': inspection.inspection_date,
                        'vehicle': vehicle_name,
                        'customer': customer_name,
                        'category': 'accessories',
                        'category_label': 'Accessories',
                        'item': str(item_name).title(),
                        'condition': value,
                        'condition_label': condition,
                        'notes': '',
                    })

        # ==============================================
        # EXTERIOR DAMAGE
        # ==============================================
        damages = inspection.exterior_damages.all()

        for damage in damages:

            damage_type = damage.get_damage_type_display()
            zone = damage.get_zone_display()

            report_rows.append({
                'inspection': inspection,
                'inspection_number': inspection_number,
                'inspection_date': inspection.inspection_date,
                'vehicle': vehicle_name,
                'customer': customer_name,
                'category': 'exterior',
                'category_label': 'Exterior Damage',
                'item': zone,
                'condition': damage.damage_type,
                'condition_label': damage_type,
                'notes': damage.notes or '',
            })

    # --------------------------------------------------
    # FILTER REPORT ROWS
    # --------------------------------------------------

    if selected_category:
        report_rows = [
            row for row in report_rows
            if row['category'] == selected_category
        ]

    if selected_condition:
        report_rows = [
            row for row in report_rows
            if row['condition'] == selected_condition
        ]

    # --------------------------------------------------
    # CATEGORY FILTER OPTIONS
    # --------------------------------------------------

    category_choices = [
        ('mechanical', 'Mechanical'),
        ('interior', 'Interior'),
        ('accessories', 'Accessories'),
        ('exterior', 'Exterior Damage'),
    ]

    # --------------------------------------------------
    # CONDITION FILTER OPTIONS
    # --------------------------------------------------

    condition_choices = [
        ('poor', 'Poor'),
        ('fair', 'Fair'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged'),
        ('dent', 'Dent'),
        ('scratch', 'Scratch'),
        ('paint', 'Paint Damage'),
        ('crack', 'Crack'),
    ]

    # --------------------------------------------------
    # SUMMARY COUNTS
    # --------------------------------------------------

    total_issues = len(report_rows)

    poor_count = sum(
        1 for row in report_rows
        if row['condition'] == 'poor'
    )

    fair_count = sum(
        1 for row in report_rows
        if row['condition'] == 'fair'
    )

    missing_count = sum(
        1 for row in report_rows
        if row['condition'] == 'missing'
    )

    damaged_count = sum(
        1 for row in report_rows
        if row['condition'] in (
            'damaged', 'dent', 'scratch',
            'paint', 'crack', 'missing'
        )
    )

    context = {
        'report_rows': report_rows,

        'search': search,
        'from_date': from_date,
        'to_date': to_date,

        'selected_category': selected_category,
        'selected_condition': selected_condition,

        'category_choices': category_choices,
        'condition_choices': condition_choices,

        'total_issues': total_issues,
        'poor_count': poor_count,
        'fair_count': fair_count,
        'missing_count': missing_count,
        'damaged_count': damaged_count,
    }

    return render(
        request,
        'jobcard_app/reports/failed_inspection_items_report.html',
        context
    )


def vehicle_inspection_history_report(request):

    vehicle_id = request.GET.get('vehicle')

    vehicles = WorkshopVehicle.objects.all().order_by('registration_number')

    inspections = VehicleInspection.objects.none()

    history_data = []
    selected_vehicle = None

    if vehicle_id:
        selected_vehicle = WorkshopVehicle.objects.filter(
            id=vehicle_id
        ).first()

        if selected_vehicle:
            inspections = VehicleInspection.objects.filter(
                vehicle=selected_vehicle
            ).select_related(
                'vehicle',
                'customer',
                'inspector',
                'jobcard'
            ).prefetch_related(
                'exterior_damages',
                'findings'
            ).order_by(
                '-inspection_date',
                '-created_on'
            )

            for inspection in inspections:

                issues = []

                # -------------------------
                # MECHANICAL ISSUES
                # -------------------------
                mechanical = getattr(inspection, 'mechanical', None)

                if mechanical:
                    mechanical_fields = [
                        'oil_leak', 'coolant_leak', 'abnormal_noise',
                        'brake_pad', 'brake_disc', 'shock_absorbers',
                        'bushes', 'battery', 'starter', 'lights',
                        'tyre_fl', 'tyre_fr', 'tyre_rl', 'tyre_rr',
                        'tyre_spare', 'brake_fluid', 'steering_fluid',
                        'washer_fluid', 'exhaust_system'
                    ]

                    for field in mechanical_fields:
                        value = getattr(mechanical, field, None)

                        if value in ['poor', 'fair']:
                            field_obj = mechanical._meta.get_field(field)

                            issues.append({
                                'category': 'Mechanical',
                                'item': field_obj.verbose_name.title(),
                                'condition': value.title(),
                            })

                # -------------------------
                # INTERIOR ISSUES
                # -------------------------
                interior = getattr(inspection, 'interior', None)

                if interior:
                    interior_fields = [
                        'dashboard', 'seats', 'steering_wheel',
                        'ac_system', 'audio_system', 'windows',
                        'seat_belts', 'floor_carpet', 'headliner',
                        'door_panels'
                    ]

                    for field in interior_fields:
                        value = getattr(interior, field, None)

                        if value in ['poor', 'fair']:
                            field_obj = interior._meta.get_field(field)

                            issues.append({
                                'category': 'Interior',
                                'item': field_obj.verbose_name.title(),
                                'condition': value.title(),
                            })

                # -------------------------
                # ACCESSORIES
                # -------------------------
                accessories = getattr(inspection, 'accessories', None)

                if accessories:
                    accessory_fields = [
                        'spare_wheel', 'tool_kit', 'service_book',
                        'remote_key', 'safety_triangle', 'floor_mat',
                        'jack', 'fire_extinguisher', 'first_aid_kit'
                    ]

                    for field in accessory_fields:
                        value = getattr(accessories, field, None)

                        if value in ['missing', 'damaged']:
                            field_obj = accessories._meta.get_field(field)

                            issues.append({
                                'category': 'Accessories',
                                'item': field_obj.verbose_name.title(),
                                'condition': value.title(),
                            })

                # -------------------------
                # EXTERIOR DAMAGE
                # -------------------------
                for damage in inspection.exterior_damages.all():

                    issues.append({
                        'category': 'Exterior',
                        'item': getattr(damage, 'zone', 'Exterior'),
                        'condition': getattr(damage, 'damage_type', 'Damage'),
                        'notes': getattr(damage, 'notes', ''),
                    })

                # -------------------------
                # INSPECTION FINDINGS
                # -------------------------
                for finding in inspection.findings.all():

                    issues.append({
                        'category': 'Finding',
                        'item': getattr(finding, 'finding_type', 'Finding'),
                        'condition': 'Recorded',
                        'notes': getattr(finding, 'description', ''),
                    })

                history_data.append({
                    'inspection': inspection,
                    'issues': issues,
                    'issue_count': len(issues),
                })

    context = {
        'vehicles': vehicles,
        'selected_vehicle': selected_vehicle,
        'history_data': history_data,
        'total_inspections': len(history_data),
        'total_issues': sum(
            item['issue_count'] for item in history_data
        ),
    }

    return render(
        request,
        'jobcard_app/reports/vehicle_inspection_history_report.html',
        context
    )

def inspection_status_summary_report(request):

    inspections = VehicleInspection.objects.select_related(
        'vehicle',
        'customer',
        'inspector',
        'jobcard'
    ).order_by('-inspection_date', '-created_on')

    # ---------------- FILTERS ----------------
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    inspector_id = request.GET.get('inspector', '')

    if from_date:
        parsed_from_date = parse_date(from_date)
        if parsed_from_date:
            inspections = inspections.filter(
                inspection_date__gte=parsed_from_date
            )

    if to_date:
        parsed_to_date = parse_date(to_date)
        if parsed_to_date:
            inspections = inspections.filter(
                inspection_date__lte=parsed_to_date
            )

    if inspector_id:
        inspections = inspections.filter(inspector_id=inspector_id)

    # ---------------- STATUS COUNTS ----------------
    total_inspections = inspections.count()

    # Normalize status using LOWER + TRIM in the database.
    from django.db.models.functions import Lower, Trim

    normalized_inspections = inspections.annotate(
        normalized_status=Lower(Trim('overall_status'))
    )

    passed_count = normalized_inspections.filter(
        normalized_status='pass'
    ).count()

    attention_count = normalized_inspections.filter(
        normalized_status='attention'
    ).count()

    failed_count = normalized_inspections.filter(
        normalized_status='fail'
    ).count()

    # ---------------- PERCENTAGES ----------------
    def percentage(count):
        if total_inspections > 0:
            return round((count / total_inspections) * 100, 1)
        return 0

    pass_percentage = percentage(passed_count)
    attention_percentage = percentage(attention_count)
    fail_percentage = percentage(failed_count)

    # ---------------- INSPECTOR SUMMARY ----------------
    inspector_summary = inspections.values(
        'inspector_id',
        'inspector__full_name'
    ).annotate(
        total=Count('id')
    ).order_by('-total')

    # ---------------- INSPECTOR FILTER DROPDOWN ----------------
    inspectors = VehicleInspection.objects.values(
        'inspector_id',
        'inspector__full_name'
    ).distinct().order_by('inspector__full_name')

    # ---------------- STATUS RECORDS ----------------
    pass_inspections = normalized_inspections.filter(
        normalized_status='pass'
    )

    attention_inspections = normalized_inspections.filter(
        normalized_status='attention'
    )

    failed_inspections = normalized_inspections.filter(
        normalized_status='fail'
    )

    # ---------------- CONTEXT ----------------
    context = {
        'inspections': inspections,

        'total_inspections': total_inspections,

        'passed_count': passed_count,
        'attention_count': attention_count,
        'failed_count': failed_count,

        'pass_percentage': pass_percentage,
        'attention_percentage': attention_percentage,
        'fail_percentage': fail_percentage,

        'inspector_summary': inspector_summary,
        'inspectors': inspectors,

        'pass_inspections': pass_inspections,
        'attention_inspections': attention_inspections,
        'failed_inspections': failed_inspections,

        'from_date': from_date,
        'to_date': to_date,
        'selected_inspector': inspector_id,
    }

    return render(
        request,
        'jobcard_app/reports/inspection_status_summary_report.html',
        context
    )

def get_jobcard_report_queryset():
    return (
        JobCard.objects
        .filter(is_active=True)
        .select_related(
            'customer',
            'workshop_vehicle',
            'workshop_vehicle__manufacturer',
            'workshop_vehicle__vehicle_model',
            'advisor',
        )
        .prefetch_related(
            'parts',
            'labours__technician',
            'complaints',
            'findings',
        )
        .order_by('-date', '-id')
    )


def get_jobcard_parts_total(jobcard):
    return sum(
        (Decimal(str(part.total_price or 0))
         for part in jobcard.parts.all()),
        Decimal('0')
    )


def get_jobcard_labour_total(jobcard):
    return sum(
        (Decimal(str(labour.amount or 0))
         for labour in jobcard.labours.all()),
        Decimal('0')
    )


def get_jobcard_total(jobcard):
    return (
        get_jobcard_parts_total(jobcard)
        + get_jobcard_labour_total(jobcard)
    )


def get_vehicle_display(vehicle):
    if not vehicle:
        return '-'

    return vehicle.registration_number or vehicle.vehicle_number


def get_vehicle_model_display(vehicle):
    if not vehicle:
        return '-'

    manufacturer = (
        vehicle.manufacturer.manufacturer_name
        if vehicle.manufacturer else ''
    )

    model = (
        vehicle.vehicle_model.model_name
        if vehicle.vehicle_model else ''
    )

    return f"{manufacturer} {model}".strip() or '-'
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import JobCard, WorkshopVehicle


# =========================================================
# COMMON REPORT QUERYSET
# =========================================================

def service_report_jobcards():
    return (
        JobCard.objects.filter(is_active=True)
        .select_related(
            'customer',
            'workshop_vehicle',
            'workshop_vehicle__manufacturer',
            'workshop_vehicle__vehicle_model',
            'advisor',
        )
        .prefetch_related(
            'complaints',
            'findings',
            'parts',
            'labours__technician',
        )
        .order_by('-date', '-id')
    )


def service_report_filter(request, queryset):
    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '')

    if search:
        queryset = queryset.filter(
            Q(voucher_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
            | Q(workshop_vehicle__registration_number__icontains=search)
            | Q(workshop_vehicle__vehicle_number__icontains=search)
        )

    if date_from:
        parsed = parse_date(date_from)
        if parsed:
            queryset = queryset.filter(date__gte=parsed)

    if date_to:
        parsed = parse_date(date_to)
        if parsed:
            queryset = queryset.filter(date__lte=parsed)

    if status:
        queryset = queryset.filter(status=status)

    return queryset


def report_vehicle_number(vehicle):
    if not vehicle:
        return '-'

    return vehicle.registration_number or vehicle.vehicle_number or '-'


def report_vehicle_model(vehicle):
    if not vehicle:
        return '-'

    manufacturer = (
        vehicle.manufacturer.manufacturer_name
        if vehicle.manufacturer else ''
    )

    model = (
        vehicle.vehicle_model.model_name
        if vehicle.vehicle_model else ''
    )

    return f"{manufacturer} {model}".strip() or '-'


# =========================================================
# 1. SERVICE REGISTER
# =========================================================

@login_required
def service_register_report(request):

    queryset = service_report_jobcards()
    queryset = service_report_filter(request, queryset)

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'jobcards': page_obj.object_list,
        'total_count': queryset.count(),
        'search': request.GET.get('search', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'status': request.GET.get('status', ''),
        'report_title': 'Service Register',
    }

    return render(
        request,
        'jobcard_app/reports/service_register.html',
        context
    )


# =========================================================
# 2. SERVICE DUE REPORT
# =========================================================

@login_required
def service_due_report(request):

    vehicles = (
        WorkshopVehicle.objects
        .filter(is_active=True)
        .select_related(
            'customer',
            'manufacturer',
            'vehicle_model',
        )
        .order_by('next_service_date')
    )

    search = request.GET.get('search', '').strip()
    service_status = request.GET.get('service_status', '')

    if search:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search)
            | Q(vehicle_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
        )

    # Service status filtering
    vehicle_list = []

    for vehicle in vehicles:
        vehicle.service_status_report = vehicle.get_service_status()

        if service_status:
            if vehicle.service_status_report != service_status:
                continue

        vehicle_list.append(vehicle)

    context = {
        'vehicles': vehicle_list,
        'search': search,
        'service_status': service_status,
        'total_vehicles': len(vehicle_list),
        'overdue_count': sum(
            1 for v in vehicle_list
            if v.service_status_report == 'overdue'
        ),
        'due_soon_count': sum(
            1 for v in vehicle_list
            if v.service_status_report == 'due_soon'
        ),
        'unknown_count': sum(
            1 for v in vehicle_list
            if v.service_status_report == 'unknown'
        ),
        'report_title': 'Service Due Report',
    }

    return render(
        request,
        'jobcard_app/reports/service_due.html',
        context
    )


# =========================================================
# 3. REPAIR REGISTER
# =========================================================

@login_required
def repair_register_report(request):

    queryset = service_report_jobcards()

    # Repair-related job cards
    queryset = queryset.filter(
        Q(complaints__isnull=False)
        | Q(findings__isnull=False)
    ).distinct()

    queryset = service_report_filter(request, queryset)

    paginator = Paginator(queryset, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'jobcards': page_obj.object_list,
        'total_count': queryset.count(),
        'search': request.GET.get('search', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'status': request.GET.get('status', ''),
        'report_title': 'Repair Register',
    }

    return render(
        request,
        'jobcard_app/reports/repair_register.html',
        context
    )


# =========================================================
# 4. REWORK REPORT
# =========================================================

@login_required
def rework_report(request):

    queryset = service_report_jobcards()

    queryset = service_report_filter(request, queryset)

    jobcards = list(queryset)

    rework_records = []

    for jobcard in jobcards:

        vehicle = jobcard.workshop_vehicle

        if not vehicle:
            continue

        previous_jobcards = (
            JobCard.objects
            .filter(
                is_active=True,
                workshop_vehicle=vehicle,
                date__lt=jobcard.date,
            )
            .exclude(status='cancelled')
            .order_by('-date', '-id')
        )

        previous_jobcard = previous_jobcards.first()

        if previous_jobcard:
            rework_records.append({
                'jobcard': jobcard,
                'previous_jobcard': previous_jobcard,
                'vehicle': vehicle,
            })

    paginator = Paginator(rework_records, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'rework_records': page_obj.object_list,
        'total_count': len(rework_records),
        'search': request.GET.get('search', ''),
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'status': request.GET.get('status', ''),
        'report_title': 'Rework Report',
    }

    return render(
        request,
        'jobcard_app/reports/rework_report.html',
        context
    )

def service_repair_reports_dashboard(request):
    return render(
        request,
        'jobcard_app/reports/service_repair_reports_dashboard.html'
    )

def technician_reports_dashboard(request):
    return render(
        request,
        'jobcard_app/reports/technician_reports_dashboard.html'
    )

def technician_performance_report(request):

    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '').strip()

    technicians = Staff.objects.filter(
        labour_entries__isnull=False
    ).distinct()

    if search:
        technicians = technicians.filter(
            Q(full_name__icontains=search) |
            Q(staff_id__icontains=search)
        )

    technicians = technicians.order_by('full_name')

    report_data = []

    for technician in technicians:

        labour_entries = JobCardLabour.objects.filter(
            technician=technician,
            jobcard__is_active=True
        )

        if date_from:
            labour_entries = labour_entries.filter(
                jobcard__date__gte=date_from
            )

        if date_to:
            labour_entries = labour_entries.filter(
                jobcard__date__lte=date_to
            )

        if status:
            labour_entries = labour_entries.filter(
                jobcard__status=status
            )

        jobcards = JobCard.objects.filter(
            labours__technician=technician,
            is_active=True
        ).distinct()

        if date_from:
            jobcards = jobcards.filter(date__gte=date_from)

        if date_to:
            jobcards = jobcards.filter(date__lte=date_to)

        if status:
            jobcards = jobcards.filter(status=status)

        total_jobs = jobcards.count()

        completed_jobs = jobcards.filter(
            status__in=['completed', 'closed']
        ).count()

        in_progress_jobs = jobcards.filter(
            status='in_progress'
        ).count()

        pending_jobs = jobcards.filter(
            status__in=['open', 'waiting']
        ).count()

        completion_rate = (
            (completed_jobs / total_jobs) * 100
            if total_jobs else 0
        )

        report_data.append({
            'technician': technician,
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'pending_jobs': pending_jobs,
            'in_progress_jobs': in_progress_jobs,
            'completion_rate': completion_rate,
        })

    # Summary
    total_technicians = len(report_data)

    total_jobs = sum(item['total_jobs'] for item in report_data)

    total_completed = sum(
        item['completed_jobs'] for item in report_data
    )

    total_pending = sum(
        item['pending_jobs'] for item in report_data
    )

    # Pagination
    paginator = Paginator(report_data, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'report_data': page_obj,
        'page_obj': page_obj,

        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'status': status,

        'total_technicians': total_technicians,
        'total_jobs': total_jobs,
        'total_completed': total_completed,
        'total_pending': total_pending,
    }

    return render(
        request,
        'jobcard_app/reports/technician_performance_report.html',
        context
    )

def technician_revenue_report(request):

    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    status = request.GET.get('status', '').strip()

    technicians = Staff.objects.filter(
        labour_entries__isnull=False
    ).distinct()

    if search:
        technicians = technicians.filter(
            Q(full_name__icontains=search) |
            Q(staff_id__icontains=search)
        )

    report_data = []

    for technician in technicians.order_by('full_name'):

        labour_entries = JobCardLabour.objects.filter(
            technician=technician,
            jobcard__is_active=True
        )

        if date_from:
            labour_entries = labour_entries.filter(
                jobcard__date__gte=date_from
            )

        if date_to:
            labour_entries = labour_entries.filter(
                jobcard__date__lte=date_to
            )

        if status:
            labour_entries = labour_entries.filter(
                jobcard__status=status
            )

        total_jobs = labour_entries.values(
            'jobcard_id'
        ).distinct().count()

        completed_jobs = labour_entries.filter(
            jobcard__status__in=['completed', 'closed']
        ).values('jobcard_id').distinct().count()

        total_hours = labour_entries.aggregate(
            total=Coalesce(
                Sum('hours'),
                Decimal('0.00')
            )
        )['total']

        total_revenue = labour_entries.aggregate(
            total=Coalesce(
                Sum('amount'),
                Decimal('0.000')
            )
        )['total']

        average_revenue = (
            total_revenue / total_jobs
            if total_jobs > 0
            else Decimal('0.000')
        )

        report_data.append({
            'technician': technician,
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'total_hours': total_hours,
            'total_revenue': total_revenue,
            'average_revenue': average_revenue,
        })

    # Summary totals
    total_technicians = len(report_data)

    total_jobs = sum(
        item['total_jobs'] for item in report_data
    )

    total_hours = sum(
        (item['total_hours'] for item in report_data),
        Decimal('0.00')
    )

    total_revenue = sum(
        (item['total_revenue'] for item in report_data),
        Decimal('0.000')
    )

    # Pagination
    paginator = Paginator(report_data, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'report_data': page_obj,
        'page_obj': page_obj,

        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'status': status,

        'total_technicians': total_technicians,
        'total_jobs': total_jobs,
        'total_hours': total_hours,
        'total_revenue': total_revenue,
    }

    return render(
        request,
        'jobcard_app/reports/technician_revenue_report.html',
        context
    )

def spare_parts_reports_dashboard(request):
    return render(
        request,
        'jobcard_app/reports/spare_parts_reports_dashboard.html'
    )

def parts_stock_report(request):

    items = Item.objects.filter(isDeleted=False).select_related(
        'item_category',
        'item_unit'
    ).order_by('item_name')

    stock_data = []

    for item in items:
        stock_qty = Stock.objects.filter(
            item=item
        ).aggregate(
            total_in=Sum('in_quantity'),
            total_out=Sum('out_quantity')
        )

        quantity = (stock_qty['total_in'] or 0) - (stock_qty['total_out'] or 0)

        stock_data.append({
            'item': item,
            'quantity': quantity,
            'stock_value': quantity * item.purchase_rate,
        })

    return render(
        request,
        'jobcard_app/reports/parts_stock_report.html',
        {
            'stock_data': stock_data,
        }
    )

def low_stock_report(request):

    items = Item.objects.filter(
        isDeleted=False
    ).select_related(
        'item_category',
        'item_unit'
    ).order_by('item_name')

    low_stock_data = []

    for item in items:

        stock = Stock.objects.filter(
            item=item
        ).aggregate(
            total_in=Sum('in_quantity'),
            total_out=Sum('out_quantity')
        )

        current_stock = (stock['total_in'] or 0) - (stock['total_out'] or 0)

        minimum_stock = item.min_stock or 0
        reorder_level = item.Reorder or 0

        if current_stock <= minimum_stock:

            low_stock_data.append({
                'item': item,
                'current_stock': current_stock,
                'minimum_stock': minimum_stock,
                'reorder_level': reorder_level,
                'status': 'Out of Stock' if current_stock <= 0 else 'Low Stock',
            })

    return render(
        request,
        'jobcard_app/reports/low_stock_report.html',
        {
            'low_stock_data': low_stock_data,
        }
    )

def parts_purchase_report(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    purchases = PurchaseMaster.objects.filter(
        isDeleted=False
    ).select_related(
        'ledger'
    ).prefetch_related(
        'items__item_name'
    ).order_by('-transaction_date')

    if from_date:
        purchases = purchases.filter(transaction_date__gte=from_date)

    if to_date:
        purchases = purchases.filter(transaction_date__lte=to_date)

    purchase_rows = []
    total_quantity = 0
    total_amount = 0

    for purchase in purchases:

        for detail in purchase.items.all():

            quantity = detail.quantity or 0
            amount = detail.item_total_amount or 0

            purchase_rows.append({
                'purchase': purchase,
                'detail': detail,
                'quantity': quantity,
                'amount': amount,
            })

            total_quantity += quantity
            total_amount += amount

    return render(
        request,
        'jobcard_app/reports/parts_purchase_report.html',
        {
            'purchase_rows': purchase_rows,
            'from_date': from_date,
            'to_date': to_date,
            'total_quantity': total_quantity,
            'total_amount': total_amount,
        }
    )

def parts_consumption_report(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    parts = JobCardPart.objects.select_related(
        'jobcard',
        'jobcard__customer',
        'vehicle'
    ).order_by('-jobcard__date', '-id')

    if from_date:
        parts = parts.filter(jobcard__date__gte=from_date)

    if to_date:
        parts = parts.filter(jobcard__date__lte=to_date)

    total_quantity = sum(
        (part.quantity or 0) for part in parts
    )

    total_amount = sum(
        (part.total_price or 0) for part in parts
    )

    return render(
        request,
        'jobcard_app/reports/parts_consumption_report.html',
        {
            'parts': parts,
            'from_date': from_date,
            'to_date': to_date,
            'total_quantity': total_quantity,
            'total_amount': total_amount,
        }
    )


from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from item_master.models import Item
from .models import Invoice, InvoiceItem


def parts_profitability_report(request):
    today = timezone.localdate()

    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    items = InvoiceItem.objects.filter(
        item_type='part',
        invoice__is_active=True
    ).select_related('invoice', 'item').order_by('description')

    if start_date:
        items = items.filter(invoice__invoice_date__gte=start_date)

    if end_date:
        items = items.filter(invoice__invoice_date__lte=end_date)

    report_rows = []

    total_sales = Decimal('0.00')
    total_cost = Decimal('0.00')
    total_profit = Decimal('0.00')
    total_quantity = Decimal('0.00')

    for line in items:
        item_obj = line.item

        # Use purchase rate from Item Master
        purchase_rate = (
            Decimal(str(item_obj.purchase_rate or 0))
            if item_obj else Decimal('0.00')
        )

        quantity = Decimal(str(line.quantity or 0))
        selling_rate = Decimal(str(line.unit_price or 0))

        discount_pct = Decimal(str(line.discount_pct or 0))

        # Sales amount after line discount, excluding tax
        sales_amount = (
            quantity * selling_rate *
            (Decimal('1') - discount_pct / Decimal('100'))
        )

        cost_amount = quantity * purchase_rate
        profit = sales_amount - cost_amount

        profit_percentage = (
            (profit / cost_amount) * Decimal('100')
            if cost_amount > 0 else Decimal('0.00')
        )

        report_rows.append({
            'item_code': line.item_code or (
                item_obj.item_code if item_obj else ''
            ),
            'item_name': line.description,
            'quantity': quantity,
            'purchase_rate': purchase_rate,
            'sales_rate': selling_rate,
            'sales_amount': sales_amount,
            'cost_amount': cost_amount,
            'profit': profit,
            'profit_percentage': profit_percentage,
        })

        total_quantity += quantity
        total_sales += sales_amount
        total_cost += cost_amount
        total_profit += profit

    overall_profit_percentage = (
        (total_profit / total_cost) * Decimal('100')
        if total_cost > 0 else Decimal('0.00')
    )

    context = {
        'report_rows': report_rows,
        'start_date': start_date,
        'end_date': end_date,
        'total_quantity': total_quantity,
        'total_sales': total_sales,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'overall_profit_percentage': overall_profit_percentage,
    }

    return render(
        request,
        'jobcard_app/reports/parts_profitability_report.html',
        context
    )
# =========================================================
# CUSTOMER & VEHICLE REPORTS
# Paste at the BOTTOM of jobcard_app/report_views.py
# =========================================================
from collections import defaultdict
from django.db.models import Max, Min

ZERO = Decimal('0.000')


# ---------------- helpers ----------------

def _apply_date_range(qs, field, from_date, to_date):
    start = parse_date(from_date) if from_date else None
    end = parse_date(to_date) if to_date else None
    if start:
        qs = qs.filter(**{field + '__gte': start})
    if end:
        qs = qs.filter(**{field + '__lte': end})
    return qs


def _money(value):
    return Decimal(str(value or 0))


def _valid_jobs():
    """Active, non-cancelled job cards."""
    return JobCard.objects.filter(is_active=True).exclude(status='cancelled')


def _valid_invoices(from_date='', to_date=''):
    qs = (
        Invoice.objects
        .filter(is_active=True)
        .exclude(status__in=['draft', 'cancelled'])
        .select_related('customer', 'jobcard', 'delivery_note')
        .prefetch_related('items')
        .order_by('-invoice_date', '-id')
    )
    return _apply_date_range(qs, 'invoice_date', from_date, to_date)


def _job_vehicle_label(job):
    names = []
    if job.workshop_vehicle:
        names.append(report_vehicle_number(job.workshop_vehicle))
    for jv in job.vehicles.all():
        if jv.vehicle:
            names.append(jv.vehicle.vehicle_number)
    return ', '.join(dict.fromkeys(n for n in names if n)) or '-'


def _vehicle_cost_map(from_date='', to_date=''):
    """vehicle_id -> {jobs, parts, labour, total, last_date}"""
    jobs = _apply_date_range(
        _valid_jobs().filter(workshop_vehicle__isnull=False),
        'date', from_date, to_date
    ).prefetch_related('parts', 'labours')

    data = defaultdict(lambda: {
        'jobs': 0, 'parts': ZERO, 'labour': ZERO, 'last_date': None
    })
    for job in jobs:
        d = data[job.workshop_vehicle_id]
        d['jobs'] += 1
        d['parts'] += get_jobcard_parts_total(job)
        d['labour'] += get_jobcard_labour_total(job)
        if not d['last_date'] or job.date > d['last_date']:
            d['last_date'] = job.date
    for d in data.values():
        d['total'] = d['parts'] + d['labour']
    return data


def _customer_model():
    return JobCard._meta.get_field('customer').related_model


# =========================================================
# 1. CUSTOMER HISTORY
# =========================================================

@login_required
def customer_history_report(request):
    customers = _customer_model().objects.filter(
        pk__in=JobCard.objects.values('customer_id')
    ).order_by('ledger_name')

    customer_id = request.GET.get('customer', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    selected_customer = None
    job_rows, invoice_rows = [], []
    total_jobs_amount = total_billed = total_paid = ZERO

    if customer_id.isdigit():
        selected_customer = customers.filter(pk=customer_id).first()

    if selected_customer:
        jobs = _apply_date_range(
            JobCard.objects.filter(is_active=True, customer=selected_customer)
            .select_related('workshop_vehicle')
            .prefetch_related('vehicles__vehicle')
            .order_by('-date', '-id'),
            'date', from_date, to_date
        )
        for job in jobs:
            amount = _money(job.grand_total)
            if job.status != 'cancelled':
                total_jobs_amount += amount
            job_rows.append({
                'job_number': job.voucher_number or '-',
                'date': job.date,
                'vehicle': _job_vehicle_label(job),
                'status': job.get_status_display(),
                'amount': amount,
            })

        for inv in _valid_invoices(from_date, to_date).filter(
            customer=selected_customer
        ):
            total = _money(inv.get_grand_total())
            paid = _money(inv.amount_paid)
            total_billed += total
            total_paid += paid
            invoice_rows.append({
                'invoice_number': inv.display_number,
                'date': inv.invoice_date,
                'job_number': inv.jobcard.voucher_number if inv.jobcard else '-',
                'total': total,
                'paid': paid,
                'balance': total - paid,
            })

    return render(request, 'jobcard_app/reports/customer_history_report.html', {
        'customers': customers,
        'selected_customer': selected_customer,
        'from_date': from_date,
        'to_date': to_date,
        'job_rows': job_rows,
        'invoice_rows': invoice_rows,
        'total_visits': len([r for r in job_rows if r['status'] != 'Cancelled']),
        'total_billed': total_billed,
        'total_paid': total_paid,
        'total_balance': total_billed - total_paid,
    })


# =========================================================
# 2. CUSTOMER-WISE REVENUE
# =========================================================

@login_required
def customer_revenue_report(request):
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    invoices = _valid_invoices(from_date, to_date)
    if search:
        invoices = invoices.filter(customer__ledger_name__icontains=search)

    data = defaultdict(lambda: {
        'name': '', 'invoices': 0, 'billed': ZERO, 'paid': ZERO
    })
    for inv in invoices:
        d = data[inv.customer_id]
        d['name'] = inv.customer.ledger_name
        d['invoices'] += 1
        d['billed'] += _money(inv.get_grand_total())
        d['paid'] += _money(inv.amount_paid)

    job_counts = dict(
        _apply_date_range(_valid_jobs(), 'date', from_date, to_date)
        .order_by().values_list('customer_id')
        .annotate(c=Count('id'))
    )

    grand_billed = sum((d['billed'] for d in data.values()), ZERO)
    grand_paid = sum((d['paid'] for d in data.values()), ZERO)

    report_rows = []
    for cid, d in data.items():
        report_rows.append({
            'customer': d['name'],
            'jobs': job_counts.get(cid, 0),
            'invoices': d['invoices'],
            'billed': d['billed'],
            'paid': d['paid'],
            'balance': d['billed'] - d['paid'],
            'share': (d['billed'] / grand_billed * 100) if grand_billed else 0,
        })
    report_rows.sort(key=lambda r: r['billed'], reverse=True)

    return render(request, 'jobcard_app/reports/customer_revenue_report.html', {
        'report_rows': report_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'total_customers': len(report_rows),
        'grand_billed': grand_billed,
        'grand_paid': grand_paid,
        'grand_balance': grand_billed - grand_paid,
    })


# =========================================================
# 3. REPEAT CUSTOMER ANALYSIS
# =========================================================

@login_required
def repeat_customer_report(request):
    today = timezone.localdate()
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    min_visits = request.GET.get('min_visits', '2').strip()
    min_visits = int(min_visits) if min_visits.isdigit() and int(min_visits) > 0 else 2

    jobs = _apply_date_range(_valid_jobs(), 'date', from_date, to_date)
    if search:
        jobs = jobs.filter(customer__ledger_name__icontains=search)

    total_customers = jobs.order_by().values('customer_id').distinct().count()

    stats = (
        jobs.order_by()
        .values('customer_id', 'customer__ledger_name')
        .annotate(visits=Count('id'), first_visit=Min('date'), last_visit=Max('date'))
        .filter(visits__gte=min_visits)
        .order_by('-visits', 'customer__ledger_name')
    )

    revenue = defaultdict(lambda: ZERO)
    for inv in _valid_invoices(from_date, to_date):
        revenue[inv.customer_id] += _money(inv.get_grand_total())

    report_rows = []
    for s in stats:
        visits = s['visits']
        gap = (
            round((s['last_visit'] - s['first_visit']).days / (visits - 1), 1)
            if visits > 1 else 0
        )
        report_rows.append({
            'customer': s['customer__ledger_name'],
            'visits': visits,
            'first_visit': s['first_visit'],
            'last_visit': s['last_visit'],
            'avg_gap': gap,
            'days_since': (today - s['last_visit']).days,
            'revenue': revenue.get(s['customer_id'], ZERO),
        })

    return render(request, 'jobcard_app/reports/repeat_customer_report.html', {
        'report_rows': report_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'min_visits': min_visits,
        'total_customers': total_customers,
        'repeat_customers': len(report_rows),
        'repeat_percentage': round(len(report_rows) / total_customers * 100, 1)
        if total_customers else 0,
    })


# =========================================================
# 4. VEHICLE REGISTER
# =========================================================

@login_required
def vehicle_register_report(request):
    search = request.GET.get('search', '').strip()
    service_status = request.GET.get('service_status', '').strip()

    vehicles = (
        WorkshopVehicle.objects.filter(is_active=True)
        .select_related('customer', 'manufacturer', 'vehicle_model')
        .order_by('registration_number')
    )
    if search:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search)
            | Q(vehicle_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
        )

    job_stats = {
        r['workshop_vehicle_id']: r
        for r in _valid_jobs().order_by()
        .values('workshop_vehicle_id')
        .annotate(jobs=Count('id'), last_visit=Max('date'))
    }

    report_rows = []
    for v in vehicles:
        status = v.get_service_status()
        if service_status and status != service_status:
            continue
        stat = job_stats.get(v.pk, {})
        report_rows.append({
            'vehicle': report_vehicle_number(v),
            'make_model': report_vehicle_model(v),
            'customer': v.customer.ledger_name if v.customer else '-',
            'jobs': stat.get('jobs', 0),
            'last_visit': stat.get('last_visit'),
            'next_service': v.next_service_date,
            'service_status': status,
        })

    return render(request, 'jobcard_app/reports/vehicle_register_report.html', {
        'report_rows': report_rows,
        'search': search,
        'service_status': service_status,
        'total_vehicles': len(report_rows),
    })


# =========================================================
# 5. VEHICLE HISTORY
# =========================================================

@login_required
def vehicle_history_report(request):
    vehicles = WorkshopVehicle.objects.all().order_by('registration_number')
    vehicle_id = request.GET.get('vehicle', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    selected_vehicle = None
    report_rows = []
    total_parts = total_labour = total_amount = ZERO

    if vehicle_id.isdigit():
        selected_vehicle = vehicles.filter(pk=vehicle_id).first()

    if selected_vehicle:
        jobs = _apply_date_range(
            JobCard.objects.filter(is_active=True)
            .filter(
                Q(workshop_vehicle=selected_vehicle)
                | Q(vehicles__vehicle=selected_vehicle)
            )
            .distinct()
            .select_related('customer')
            .prefetch_related('complaints', 'parts', 'labours'),
            'date', from_date, to_date
        ).order_by('-date', '-id')

        for job in jobs:
            parts = get_jobcard_parts_total(job)
            labour = get_jobcard_labour_total(job)
            amount = _money(job.grand_total)
            if job.status != 'cancelled':
                total_parts += parts
                total_labour += labour
                total_amount += amount
            report_rows.append({
                'job_number': job.voucher_number or '-',
                'date': job.date,
                'customer': job.customer.ledger_name,
                'complaints': ', '.join(
                    c.description for c in job.complaints.all() if c.description
                ) or '-',
                'status': job.get_status_display(),
                'parts': parts,
                'labour': labour,
                'amount': amount,
            })

    return render(request, 'jobcard_app/reports/vehicle_history_report.html', {
        'vehicles': vehicles,
        'selected_vehicle': selected_vehicle,
        'from_date': from_date, 'to_date': to_date,
        'report_rows': report_rows,
        'total_visits': len(report_rows),
        'total_parts': total_parts,
        'total_labour': total_labour,
        'total_amount': total_amount,
        'last_visit': report_rows[0]['date'] if report_rows else None,
    })


# =========================================================
# 6. VEHICLE REPAIR COST ANALYSIS
# =========================================================

@login_required
def vehicle_repair_cost_report(request):
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    cost_map = _vehicle_cost_map(from_date, to_date)

    vehicles = WorkshopVehicle.objects.filter(
        pk__in=cost_map.keys()
    ).select_related('customer', 'manufacturer', 'vehicle_model')
    if search:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=search)
            | Q(vehicle_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
        )

    report_rows = []
    for v in vehicles:
        d = cost_map[v.pk]
        report_rows.append({
            'vehicle': report_vehicle_number(v),
            'make_model': report_vehicle_model(v),
            'customer': v.customer.ledger_name if v.customer else '-',
            'jobs': d['jobs'],
            'parts': d['parts'],
            'labour': d['labour'],
            'total': d['total'],
            'average': d['total'] / d['jobs'] if d['jobs'] else ZERO,
            'last_date': d['last_date'],
        })
    report_rows.sort(key=lambda r: r['total'], reverse=True)

    return render(request, 'jobcard_app/reports/vehicle_repair_cost_report.html', {
        'report_rows': report_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'total_vehicles': len(report_rows),
        'total_jobs': sum(r['jobs'] for r in report_rows),
        'total_parts': sum((r['parts'] for r in report_rows), ZERO),
        'total_labour': sum((r['labour'] for r in report_rows), ZERO),
        'total_cost': sum((r['total'] for r in report_rows), ZERO),
    })


# =========================================================
# 7. VEHICLE MAKE / MODEL ANALYSIS
# =========================================================

@login_required
def vehicle_make_model_report(request):
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    search = request.GET.get('search', '').strip()

    cost_map = _vehicle_cost_map(from_date, to_date)

    vehicles = WorkshopVehicle.objects.filter(
        is_active=True
    ).select_related('manufacturer', 'vehicle_model')

    groups = defaultdict(lambda: {
        'vehicles': 0, 'serviced': 0, 'jobs': 0, 'parts': ZERO, 'labour': ZERO
    })
    for v in vehicles:
        make = v.manufacturer.manufacturer_name if v.manufacturer else 'Unknown'
        model = v.vehicle_model.model_name if v.vehicle_model else 'Unknown'
        if search and search.lower() not in f'{make} {model}'.lower():
            continue
        g = groups[(make, model)]
        g['vehicles'] += 1
        d = cost_map.get(v.pk)
        if d:
            g['serviced'] += 1
            g['jobs'] += d['jobs']
            g['parts'] += d['parts']
            g['labour'] += d['labour']

    report_rows = []
    for (make, model), g in groups.items():
        total = g['parts'] + g['labour']
        report_rows.append({
            'make': make, 'model': model,
            'vehicles': g['vehicles'], 'serviced': g['serviced'],
            'jobs': g['jobs'], 'parts': g['parts'], 'labour': g['labour'],
            'total': total,
            'avg_per_job': total / g['jobs'] if g['jobs'] else ZERO,
            'avg_per_vehicle': total / g['serviced'] if g['serviced'] else ZERO,
        })
    report_rows.sort(key=lambda r: (r['jobs'], r['total']), reverse=True)

    return render(request, 'jobcard_app/reports/vehicle_make_model_report.html', {
        'report_rows': report_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'total_models': len(report_rows),
        'total_vehicles': sum(r['vehicles'] for r in report_rows),
        'total_jobs': sum(r['jobs'] for r in report_rows),
        'total_cost': sum((r['total'] for r in report_rows), ZERO),
    })


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def customer_vehicle_reports_dashboard(request):
    return render(
        request,
        'accounts_app/reports/report_category_dashboard.html',
        {
            'dashboard_title': 'Customer & Vehicle Reports',
            'dashboard_description': 'Analyse customers, vehicles, repair costs and visit patterns.',
            'reports': [
                {'name': 'Customer History',
                 'description': 'Job cards and invoices for a selected customer.',
                 'icon': 'bi-person-lines-fill',
                 'url_name': 'jobcard_app:customer_history_report'},
                {'name': 'Customer-wise Revenue',
                 'description': 'Billed, collected and outstanding amounts per customer.',
                 'icon': 'bi-cash-coin',
                 'url_name': 'jobcard_app:customer_revenue_report'},
                {'name': 'Repeat Customer Analysis',
                 'description': 'Customers with multiple visits, visit gaps and revenue.',
                 'icon': 'bi-arrow-repeat',
                 'url_name': 'jobcard_app:repeat_customer_report'},
                {'name': 'Vehicle Register',
                 'description': 'All workshop vehicles with owner, visits and service status.',
                 'icon': 'bi-car-front',
                 'url_name': 'jobcard_app:vehicle_register_report'},
                {'name': 'Vehicle History',
                 'description': 'Complete job card history of a selected vehicle.',
                 'icon': 'bi-clock-history',
                 'url_name': 'jobcard_app:vehicle_history_report'},
                {'name': 'Vehicle Repair Cost Analysis',
                 'description': 'Parts and labour cost per vehicle.',
                 'icon': 'bi-wrench-adjustable',
                 'url_name': 'jobcard_app:vehicle_repair_cost_report'},
                {'name': 'Vehicle Make/Model Analysis',
                 'description': 'Jobs and repair cost grouped by make and model.',
                 'icon': 'bi-bar-chart',
                 'url_name': 'jobcard_app:vehicle_make_model_report'},
            ]
        }
    )


def _status_options(model):
    values = model.objects.order_by().values_list('status', flat=True).distinct()
    return sorted(
        [(v, str(v).replace('_', ' ').title()) for v in values if v],
        key=lambda x: x[1]
    )


def _status_label(obj):
    fn = getattr(obj, 'get_status_display', None)
    return fn() if fn else (obj.status or '-')


def _invoice_queryset():
    """All active invoices (including draft / cancelled)."""
    return (
        Invoice.objects.filter(is_active=True)
        .select_related(
            'customer', 'vehicle',
            'jobcard', 'jobcard__workshop_vehicle',
            'delivery_note', 'delivery_note__vehicle',
        )
        .prefetch_related('items')
        .order_by('-invoice_date', '-id')
    )


def _invoice_vehicle(inv):
    vehicle = inv.vehicle
    if not vehicle and inv.jobcard:
        vehicle = inv.jobcard.workshop_vehicle
    if not vehicle and inv.delivery_note:
        vehicle = inv.delivery_note.vehicle
    return report_vehicle_number(vehicle)


def _invoice_job_number(inv):
    job = inv.jobcard or (inv.delivery_note.jobcard if inv.delivery_note else None)
    return job.voucher_number if job else '-'


PAYMENT_LABELS = {
    'paid': 'Paid', 'partial': 'Partially Paid',
    'unpaid': 'Unpaid', 'overdue': 'Overdue',
}


def _payment_state(inv, total, paid, today):
    if total - paid <= 0:
        return 'paid'
    if inv.due_date and inv.due_date < today:
        return 'overdue'
    if paid > 0:
        return 'partial'
    return 'unpaid'


def _tax_rate_field():
    """Find the tax-percentage field on InvoiceItem (name differs per project)."""
    names = {f.name for f in InvoiceItem._meta.get_fields()}
    for candidate in (
        'tax_pct', 'tax_percent', 'tax_percentage', 'tax_rate',
        'vat_pct', 'vat_percent', 'vat_percentage', 'vat_rate',
        'gst_pct', 'gst_percent', 'gst_rate', 'tax', 'vat',
    ):
        if candidate in names:
            return candidate
    return None


def _invoice_amounts(inv, rate_field):
    """Returns subtotal (taxable), tax, total and a {rate: [taxable, tax]} map."""
    subtotal = ZERO
    tax = ZERO
    by_rate = defaultdict(lambda: [ZERO, ZERO])

    for item in inv.items.all():
        taxable = (
            _money(item.quantity) * _money(item.unit_price)
            * (Decimal('1') - _money(item.discount_pct) / Decimal('100'))
        )
        subtotal += taxable
        if rate_field:
            try:
                rate = _money(getattr(item, rate_field, 0))
            except Exception:
                rate = ZERO
            item_tax = taxable * rate / Decimal('100')
            tax += item_tax
            key = rate.quantize(Decimal('0.01'))
            by_rate[key][0] += taxable
            by_rate[key][1] += item_tax

    total = _money(inv.get_grand_total())

    if not rate_field:
        # No tax field found: treat the difference as tax
        tax = max(total - subtotal, ZERO)
        by_rate[None][0] += subtotal
        by_rate[None][1] += tax

    return {'subtotal': subtotal, 'tax': tax, 'total': total, 'by_rate': by_rate}


# =========================================================
# 1. DELIVERY REGISTER
# =========================================================

@login_required
def delivery_register_report(request):
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    selected_status = request.GET.get('status', '').strip()
    invoiced = request.GET.get('invoiced', '').strip()

    invoice_exists = (
        Invoice.objects.filter(is_active=True)
        .exclude(status='cancelled')
        .filter(
            Q(delivery_note_id=OuterRef('pk'))
            | Q(jobcard_id=OuterRef('jobcard_id'))
        )
    )

    notes = (
        DeliveryNote.objects.filter(is_active=True)
        .annotate(has_invoice=Exists(invoice_exists))
        .select_related('customer', 'jobcard', 'vehicle', 'technician')
        .prefetch_related('vehicles__vehicle')
        .order_by('-date', '-id')
    )
    notes = _apply_date_range(notes, 'date', from_date, to_date)

    if selected_status:
        notes = notes.filter(status=selected_status)
    if invoiced == 'yes':
        notes = notes.filter(has_invoice=True)
    elif invoiced == 'no':
        notes = notes.filter(has_invoice=False)

    if search:
        notes = notes.filter(
            Q(voucher_number__icontains=search)
            | Q(jobcard__voucher_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
            | Q(reg_number__icontains=search)
            | Q(vehicle__vehicle_number__icontains=search)
            | Q(vehicles__vehicle__vehicle_number__icontains=search)
        ).distinct()

    report_rows = []
    total_amount = ZERO
    for dn in notes:
        numbers = [e.vehicle.vehicle_number for e in dn.vehicles.all() if e.vehicle]
        if not numbers and dn.vehicle:
            numbers.append(dn.vehicle.vehicle_number)
        if not numbers and dn.reg_number:
            numbers.append(dn.reg_number)

        amount = _money(dn.get_grand_total())
        total_amount += amount
        report_rows.append({
            'delivery_number': dn.voucher_number or '-',
            'date': dn.date,
            'job_number': dn.jobcard.voucher_number if dn.jobcard else '-',
            'customer': dn.customer.ledger_name,
            'vehicle': ', '.join(dict.fromkeys(numbers)) or '-',
            'technician': str(dn.technician) if dn.technician else '-',
            'status': _status_label(dn),
            'invoiced': 'Yes' if dn.has_invoice else 'No',
            'amount': amount,
        })

    return render(request, 'jobcard_app/reports/delivery_register_report.html', {
        'report_rows': report_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'selected_status': selected_status, 'invoiced': invoiced,
        'status_options': _status_options(DeliveryNote),
        'total_deliveries': len(report_rows),
        'not_invoiced': sum(1 for r in report_rows if r['invoiced'] == 'No'),
        'total_amount': total_amount,
    })


# =========================================================
# 2. INVOICE REGISTER
# =========================================================

@login_required
def invoice_register_report(request):
    today = timezone.localdate()
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    selected_status = request.GET.get('status', '').strip()
    selected_payment = request.GET.get('payment', '').strip()

    invoices = _apply_date_range(_invoice_queryset(), 'invoice_date', from_date, to_date)
    if selected_status:
        invoices = invoices.filter(status=selected_status)

    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search)
            | Q(voucher_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
            | Q(jobcard__voucher_number__icontains=search)
            | Q(delivery_note__voucher_number__icontains=search)
            | Q(vehicle__vehicle_number__icontains=search)
            | Q(jobcard__workshop_vehicle__vehicle_number__icontains=search)
        ).distinct()

    report_rows = []
    total_invoiced = total_paid = ZERO

    for inv in invoices:
        total = _money(inv.get_grand_total())
        paid = _money(inv.amount_paid)
        cancelled = inv.status in ('cancelled', 'draft')
        state = 'cancelled' if inv.status == 'cancelled' else (
            'draft' if inv.status == 'draft' else _payment_state(inv, total, paid, today)
        )

        if selected_payment and state != selected_payment:
            continue

        if not cancelled:
            total_invoiced += total
            total_paid += paid

        report_rows.append({
            'invoice_number': inv.display_number,
            'date': inv.invoice_date,
            'due_date': inv.due_date,
            'job_number': _invoice_job_number(inv),
            'customer': inv.customer.ledger_name,
            'vehicle': _invoice_vehicle(inv),
            'payment_mode': inv.get_payment_mode_display(),
            'status': _status_label(inv),
            'payment_status': PAYMENT_LABELS.get(state, state.title()),
            'total': total,
            'paid': paid,
            'balance': ZERO if cancelled else total - paid,
        })

    return render(request, 'jobcard_app/reports/invoice_register_report.html', {
        'report_rows': report_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'selected_status': selected_status, 'selected_payment': selected_payment,
        'status_options': _status_options(Invoice),
        'total_invoices': len(report_rows),
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'total_balance': total_invoiced - total_paid,
    })


# =========================================================
# 3. INVOICE SUMMARY
# =========================================================

@login_required
def invoice_summary_report(request):
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    rate_field = _tax_rate_field()

    # Valid invoices (draft / cancelled excluded)
    valid = list(_valid_invoices(from_date, to_date).select_related('customer'))

    monthly = defaultdict(lambda: {
        'count': 0, 'subtotal': ZERO, 'tax': ZERO, 'total': ZERO, 'paid': ZERO
    })
    by_mode = defaultdict(lambda: {'count': 0, 'total': ZERO, 'paid': ZERO})

    grand_total = grand_paid = ZERO
    for inv in valid:
        a = _invoice_amounts(inv, rate_field)
        paid = _money(inv.amount_paid)

        key = (inv.invoice_date.year, inv.invoice_date.month)
        m = monthly[key]
        m['count'] += 1
        m['subtotal'] += a['subtotal']
        m['tax'] += a['tax']
        m['total'] += a['total']
        m['paid'] += paid

        mode = inv.get_payment_mode_display() or '-'
        by_mode[mode]['count'] += 1
        by_mode[mode]['total'] += a['total']
        by_mode[mode]['paid'] += paid

        grand_total += a['total']
        grand_paid += paid

    monthly_rows = []
    for (year, month), m in sorted(monthly.items(), reverse=True):
        monthly_rows.append({
            'period': date(year, month, 1),
            **m,
            'balance': m['total'] - m['paid'],
        })

    mode_rows = [
        {'mode': mode, **d, 'balance': d['total'] - d['paid']}
        for mode, d in sorted(by_mode.items(), key=lambda x: x[1]['total'], reverse=True)
    ]

    # Status breakdown uses ALL active invoices so drafts / cancelled show up
    status_data = defaultdict(lambda: {'count': 0, 'total': ZERO})
    for inv in _apply_date_range(
        _invoice_queryset(), 'invoice_date', from_date, to_date
    ):
        s = status_data[_status_label(inv)]
        s['count'] += 1
        s['total'] += _money(inv.get_grand_total())
    status_rows = [
        {'status': k, **v}
        for k, v in sorted(status_data.items(), key=lambda x: x[1]['total'], reverse=True)
    ]

    count = len(valid)
    return render(request, 'jobcard_app/reports/invoice_summary_report.html', {
        'monthly_rows': monthly_rows,
        'mode_rows': mode_rows,
        'status_rows': status_rows,
        'from_date': from_date, 'to_date': to_date,
        'total_invoices': count,
        'grand_total': grand_total,
        'grand_paid': grand_paid,
        'grand_balance': grand_total - grand_paid,
        'average_invoice': grand_total / count if count else ZERO,
    })


# =========================================================
# 4. INVOICE TAX REPORT
# =========================================================

@login_required
def invoice_tax_report(request):
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    rate_field = _tax_rate_field()

    invoices = _valid_invoices(from_date, to_date)
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search)
            | Q(voucher_number__icontains=search)
            | Q(customer__ledger_name__icontains=search)
        )

    report_rows = []
    rate_totals = defaultdict(lambda: [ZERO, ZERO])
    total_taxable = total_tax = total_amount = ZERO

    for inv in invoices:
        a = _invoice_amounts(inv, rate_field)
        total_taxable += a['subtotal']
        total_tax += a['tax']
        total_amount += a['total']

        for rate, (taxable, tax) in a['by_rate'].items():
            rate_totals[rate][0] += taxable
            rate_totals[rate][1] += tax

        rates = sorted(r for r in a['by_rate'] if r is not None)
        report_rows.append({
            'invoice_number': inv.display_number,
            'date': inv.invoice_date,
            'customer': inv.customer.ledger_name,
            'rate_label': ', '.join(f'{r}%' for r in rates) or '-',
            'taxable': a['subtotal'],
            'tax': a['tax'],
            'total': a['total'],
        })

    rate_rows = [
        {
            'rate_label': f'{rate}%' if rate is not None else 'Derived (total - taxable)',
            'taxable': vals[0],
            'tax': vals[1],
            'total': vals[0] + vals[1],
        }
        for rate, vals in sorted(
            rate_totals.items(), key=lambda x: (x[0] is None, x[0] or 0)
        )
    ]

    return render(request, 'jobcard_app/reports/invoice_tax_report.html', {
        'report_rows': report_rows,
        'rate_rows': rate_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'total_invoices': len(report_rows),
        'total_taxable': total_taxable,
        'total_tax': total_tax,
        'total_amount': total_amount,
        'tax_field_found': bool(rate_field),
    })



def _taxable(item):
    """Line value after discount, excluding tax."""
    return (
        _money(item.quantity) * _money(item.unit_price)
        * (Decimal('1') - _money(item.discount_pct) / Decimal('100'))
    )


# =========================================================
# 1. EXPENSE REPORT  (purchase vouchers)
# =========================================================

@login_required
def expense_report(request):
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    purchases = (
        PurchaseMaster.objects.filter(isDeleted=False)
        .select_related('ledger')
        .prefetch_related('items')
        .order_by('-transaction_date', '-id')
    )
    purchases = _apply_date_range(purchases, 'transaction_date', from_date, to_date)
    if search:
        purchases = purchases.filter(ledger__ledger_name__icontains=search)

    suppliers = defaultdict(lambda: {'count': 0, 'amount': ZERO})
    monthly = defaultdict(lambda: {'count': 0, 'amount': ZERO})
    purchase_rows = []
    total_amount = ZERO

    for p in purchases:
        details = list(p.items.all())
        amount = sum((_money(d.item_total_amount) for d in details), ZERO)
        qty = sum((_money(d.quantity) for d in details), ZERO)
        total_amount += amount

        supplier = p.ledger.ledger_name if p.ledger else 'Unknown'
        suppliers[supplier]['count'] += 1
        suppliers[supplier]['amount'] += amount

        key = (p.transaction_date.year, p.transaction_date.month)
        monthly[key]['count'] += 1
        monthly[key]['amount'] += amount

        purchase_rows.append({
            'voucher': (
                getattr(p, 'voucher_number', None)
                or getattr(p, 'invoice_number', None)
                or f'#{p.pk}'
            ),
            'date': p.transaction_date,
            'supplier': supplier,
            'lines': len(details),
            'quantity': qty,
            'amount': amount,
        })

    supplier_rows = [
        {'supplier': k, **v,
         'share': (v['amount'] / total_amount * 100) if total_amount else 0}
        for k, v in sorted(suppliers.items(), key=lambda x: x[1]['amount'], reverse=True)
    ]
    monthly_rows = [
        {'period': date(y, m, 1), **v}
        for (y, m), v in sorted(monthly.items(), reverse=True)
    ]

    return render(request, 'jobcard_app/reports/expense_report.html', {
        'purchase_rows': purchase_rows,
        'supplier_rows': supplier_rows,
        'monthly_rows': monthly_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'total_purchases': len(purchase_rows),
        'total_suppliers': len(supplier_rows),
        'total_amount': total_amount,
        'average_purchase': total_amount / len(purchase_rows) if purchase_rows else ZERO,
    })


# =========================================================
# 2. WORKSHOP REVENUE ANALYSIS
# =========================================================

@login_required
def workshop_revenue_report(request):
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    invoices = _valid_invoices(from_date, to_date).prefetch_related('items__item')

    categories = defaultdict(lambda: {'lines': 0, 'revenue': ZERO, 'cost': ZERO})
    monthly = defaultdict(lambda: {
        'invoices': 0, 'parts': ZERO, 'other': ZERO, 'taxable': ZERO,
        'total': ZERO, 'paid': ZERO, 'parts_cost': ZERO,
    })

    for inv in invoices:
        m = monthly[(inv.invoice_date.year, inv.invoice_date.month)]
        m['invoices'] += 1
        m['total'] += _money(inv.get_grand_total())
        m['paid'] += _money(inv.amount_paid)

        for item in inv.items.all():
            value = _taxable(item)
            label = str(item.item_type or 'other').replace('_', ' ').title()
            c = categories[label]
            c['lines'] += 1
            c['revenue'] += value
            m['taxable'] += value

            if item.item_type == 'part':
                cost = _money(item.quantity) * _money(
                    item.item.purchase_rate if item.item else 0
                )
                c['cost'] += cost
                m['parts'] += value
                m['parts_cost'] += cost
            else:
                m['other'] += value

    total_taxable = sum((c['revenue'] for c in categories.values()), ZERO)
    total_invoiced = sum((m['total'] for m in monthly.values()), ZERO)
    total_paid = sum((m['paid'] for m in monthly.values()), ZERO)
    parts_profit = sum(
        (m['parts'] - m['parts_cost'] for m in monthly.values()), ZERO
    )
    invoice_count = sum(m['invoices'] for m in monthly.values())

    category_rows = []
    for label, c in sorted(categories.items(), key=lambda x: x[1]['revenue'], reverse=True):
        is_part = label.lower() == 'part'
        category_rows.append({
            'category': label,
            'lines': c['lines'],
            'revenue': c['revenue'],
            'share': (c['revenue'] / total_taxable * 100) if total_taxable else 0,
            'cost': c['cost'] if is_part else None,
            'profit': (c['revenue'] - c['cost']) if is_part else None,
        })

    monthly_rows = [
        {'period': date(y, mo, 1), **m,
         'parts_profit': m['parts'] - m['parts_cost'],
         'balance': m['total'] - m['paid']}
        for (y, mo), m in sorted(monthly.items(), reverse=True)
    ]

    return render(request, 'jobcard_app/reports/workshop_revenue_report.html', {
        'category_rows': category_rows,
        'monthly_rows': monthly_rows,
        'from_date': from_date, 'to_date': to_date,
        'invoice_count': invoice_count,
        'total_taxable': total_taxable,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'parts_profit': parts_profit,
        'average_invoice': total_invoiced / invoice_count if invoice_count else ZERO,
    })
# =========================================================
# OPERATIONS & PERFORMANCE REPORTS
# Paste at the BOTTOM of jobcard_app/report_views.py
# (below the Customer & Vehicle block - reuses ZERO, _money,
#  _apply_date_range, _valid_jobs, _valid_invoices, report_vehicle_number)
# =========================================================
import datetime as _dt
from django.db.models import Avg
from django.db.models.functions import ExtractMonth


# ---------------- helpers ----------------

def _status_label(obj):
    fn = getattr(obj, 'get_status_display', None)
    return fn() if fn else (obj.status or '-')


def _as_date(value):
    return value.date() if isinstance(value, _dt.datetime) else value


def _tat_bucket(days):
    if days == 0:
        return 'Same Day'
    if days <= 3:
        return '1-3 Days'
    if days <= 7:
        return '4-7 Days'
    if days <= 15:
        return '8-15 Days'
    return 'Above 15 Days'


TAT_BUCKETS = ['Same Day', '1-3 Days', '4-7 Days', '8-15 Days', 'Above 15 Days']


def _turnaround_rows(from_date='', to_date='', search='', filter_field='date'):
    """One row per job card: job opened -> first delivered Delivery Note."""
    notes = (
        DeliveryNote.objects
        .filter(is_active=True, status='delivered', jobcard__isnull=False)
        .select_related('jobcard', 'jobcard__customer', 'jobcard__workshop_vehicle')
        .order_by('date', 'id')
    )
    notes = _apply_date_range(notes, filter_field, from_date, to_date)
    if search:
        notes = notes.filter(
            Q(voucher_number__icontains=search)
            | Q(jobcard__voucher_number__icontains=search)
            | Q(jobcard__customer__ledger_name__icontains=search)
            | Q(jobcard__workshop_vehicle__vehicle_number__icontains=search)
            | Q(jobcard__workshop_vehicle__registration_number__icontains=search)
        )

    seen, rows = set(), []
    for dn in notes:
        job = dn.jobcard
        if job.pk in seen:
            continue
        seen.add(job.pk)

        opened = _as_date(job.date)
        delivered = _as_date(dn.date)
        expected = _as_date(job.delivery_date) if job.delivery_date else None
        if not opened or not delivered:
            continue

        tat = max((delivered - opened).days, 0)
        rows.append({
            'job_number': job.voucher_number or '-',
            'delivery_number': dn.voucher_number or '-',
            'customer': job.customer.ledger_name,
            'vehicle': report_vehicle_number(job.workshop_vehicle),
            'opened': opened,
            'expected': expected,
            'delivered': delivered,
            'tat': tat,
            'bucket': _tat_bucket(tat),
            'delay': max((delivered - expected).days, 0) if expected else None,
            'on_time': None if expected is None else delivered <= expected,
            'on_time_label': '-' if expected is None else (
                'On Time' if delivered <= expected else 'Delayed'
            ),
        })

    rows.sort(key=lambda r: r['delivered'], reverse=True)
    return rows


def _tat_stats(rows):
    if not rows:
        return {'count': 0, 'avg': 0, 'min': 0, 'max': 0, 'on_time_pct': 0}
    days = [r['tat'] for r in rows]
    with_expected = [r for r in rows if r['on_time'] is not None]
    on_time = sum(1 for r in with_expected if r['on_time'])
    return {
        'count': len(rows),
        'avg': round(sum(days) / len(days), 1),
        'min': min(days),
        'max': max(days),
        'on_time_pct': round(on_time / len(with_expected) * 100, 1) if with_expected else 0,
    }


# =========================================================
# 1. DAILY WORKSHOP ACTIVITY
# =========================================================

@login_required
def daily_workshop_activity_report(request):
    day = parse_date(request.GET.get('date', '').strip()) or timezone.localdate()

    jobs = (
        JobCard.objects.filter(is_active=True, date=day)
        .select_related('customer', 'workshop_vehicle').order_by('-id')
    )
    deliveries = (
        DeliveryNote.objects.filter(is_active=True, date=day)
        .select_related('customer', 'jobcard', 'vehicle').order_by('-id')
    )
    invoices = (
        Invoice.objects.filter(is_active=True, invoice_date=day)
        .exclude(status__in=['draft', 'cancelled'])
        .select_related('customer', 'jobcard', 'delivery_note')
        .prefetch_related('items').order_by('-id')
    )
    inspections = (
        VehicleInspection.objects.filter(inspection_date=day)
        .select_related('vehicle', 'customer', 'inspector').order_by('-id')
    )

    job_rows = [{
        'job_number': j.voucher_number or '-',
        'customer': j.customer.ledger_name,
        'vehicle': report_vehicle_number(j.workshop_vehicle),
        'status': j.get_status_display(),
        'priority': j.get_priority_display(),
        'amount': _money(j.grand_total),
    } for j in jobs]

    delivery_rows = [{
        'delivery_number': d.voucher_number or '-',
        'job_number': d.jobcard.voucher_number if d.jobcard else '-',
        'customer': d.customer.ledger_name,
        'vehicle': report_vehicle_number(d.vehicle) if d.vehicle else (d.reg_number or '-'),
        'status': _status_label(d),
        'amount': _money(d.get_grand_total()),
    } for d in deliveries]

    invoice_rows, invoiced_total = [], ZERO
    for inv in invoices:
        total = _money(inv.get_grand_total())
        invoiced_total += total
        invoice_rows.append({
            'invoice_number': inv.display_number,
            'job_number': inv.jobcard.voucher_number if inv.jobcard else '-',
            'customer': inv.customer.ledger_name,
            'total': total,
            'paid': _money(inv.amount_paid),
        })

    inspection_rows = [{
        'inspection_number': i.voucher_number or '-',
        'vehicle': report_vehicle_number(i.vehicle),
        'customer': str(i.customer),
        'inspector': str(i.inspector) if i.inspector else '-',
        'status': (i.overall_status or '-').title(),
    } for i in inspections]

    pending_now = _valid_jobs().filter(
        status__in=['open', 'in_progress', 'waiting']
    ).count()

    return render(request, 'jobcard_app/reports/daily_workshop_activity_report.html', {
        'selected_date': day,
        'job_rows': job_rows,
        'delivery_rows': delivery_rows,
        'invoice_rows': invoice_rows,
        'inspection_rows': inspection_rows,
        'jobs_count': len(job_rows),
        'deliveries_count': len(delivery_rows),
        'invoices_count': len(invoice_rows),
        'inspections_count': len(inspection_rows),
        'invoiced_total': invoiced_total,
        'pending_now': pending_now,
    })


# =========================================================
# 2. MONTHLY PERFORMANCE
# =========================================================

@login_required
def monthly_performance_report(request):
    today = timezone.localdate()
    year_param = request.GET.get('year', '').strip()
    year = int(year_param) if year_param.isdigit() else today.year
    years = sorted(
        {d.year for d in JobCard.objects.dates('date', 'year')} | {today.year, year},
        reverse=True
    )

    jobs = {
        r['m']: r['c'] for r in
        _valid_jobs().filter(date__year=year)
        .annotate(m=ExtractMonth('date')).values('m')
        .annotate(c=Count('id')).order_by()
    }
    inspections = {
        r['m']: r['c'] for r in
        VehicleInspection.objects.filter(inspection_date__year=year)
        .annotate(m=ExtractMonth('inspection_date')).values('m')
        .annotate(c=Count('id')).order_by()
    }

    tat_by_month = defaultdict(list)
    for r in _turnaround_rows(f'{year}-01-01', f'{year}-12-31'):
        tat_by_month[r['delivered'].month].append(r)

    inv_by_month = defaultdict(lambda: {'count': 0, 'revenue': ZERO, 'paid': ZERO})
    for inv in _valid_invoices(f'{year}-01-01', f'{year}-12-31'):
        m = inv.invoice_date.month
        inv_by_month[m]['count'] += 1
        inv_by_month[m]['revenue'] += _money(inv.get_grand_total())
        inv_by_month[m]['paid'] += _money(inv.amount_paid)

    report_rows, prev_revenue = [], None
    for m in range(1, 13):
        stats = _tat_stats(tat_by_month.get(m, []))
        inv = inv_by_month.get(m, {'count': 0, 'revenue': ZERO, 'paid': ZERO})
        change = None
        if prev_revenue:
            change = round(float((inv['revenue'] - prev_revenue) / prev_revenue * 100), 1)
        report_rows.append({
            'period': date(year, m, 1),
            'jobs': jobs.get(m, 0),
            'inspections': inspections.get(m, 0),
            'deliveries': stats['count'],
            'avg_tat': stats['avg'],
            'on_time_pct': stats['on_time_pct'],
            'invoices': inv['count'],
            'revenue': inv['revenue'],
            'paid': inv['paid'],
            'balance': inv['revenue'] - inv['paid'],
            'revenue_change': change,
        })
        prev_revenue = inv['revenue']

    all_tat = [r for rows in tat_by_month.values() for r in rows]
    year_stats = _tat_stats(all_tat)

    return render(request, 'jobcard_app/reports/monthly_performance_report.html', {
        'report_rows': report_rows,
        'year': year, 'years': years,
        'total_jobs': sum(r['jobs'] for r in report_rows),
        'total_deliveries': year_stats['count'],
        'total_revenue': sum((r['revenue'] for r in report_rows), ZERO),
        'total_paid': sum((r['paid'] for r in report_rows), ZERO),
        'avg_tat': year_stats['avg'],
        'on_time_pct': year_stats['on_time_pct'],
    })


# =========================================================
# 3. JOB TURNAROUND TIME
# =========================================================

@login_required
def job_turnaround_report(request):
    search = request.GET.get('search', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    delivery_status = request.GET.get('delivery_status', '').strip()

    rows = _turnaround_rows(from_date, to_date, search)
    if delivery_status == 'on_time':
        rows = [r for r in rows if r['on_time'] is True]
    elif delivery_status == 'delayed':
        rows = [r for r in rows if r['on_time'] is False]

    stats = _tat_stats(rows)
    counts = defaultdict(int)
    for r in rows:
        counts[r['bucket']] += 1
    bucket_rows = [{
        'bucket': b, 'count': counts[b],
        'share': round(counts[b] / len(rows) * 100, 1) if rows else 0,
    } for b in TAT_BUCKETS]

    return render(request, 'jobcard_app/reports/job_turnaround_report.html', {
        'report_rows': rows,
        'bucket_rows': bucket_rows,
        'search': search, 'from_date': from_date, 'to_date': to_date,
        'delivery_status': delivery_status,
        'total_jobs': stats['count'],
        'avg_tat': stats['avg'],
        'fastest': stats['min'],
        'slowest': stats['max'],
        'on_time_pct': stats['on_time_pct'],
    })


# =========================================================
# 4. WORKSHOP EFFICIENCY
# =========================================================

@login_required
def workshop_efficiency_report(request):
    from .models import JobCardLabour

    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    jobs = _apply_date_range(_valid_jobs(), 'date', from_date, to_date)
    total_jobs = jobs.count()
    completed_jobs = jobs.filter(status__in=['completed', 'closed']).count()

    # Turnaround & on-time delivery (by job date, to match the jobs above)
    tat_rows = _turnaround_rows(from_date, to_date, filter_field='jobcard__date')
    tat = _tat_stats(tat_rows)

    # Technician efficiency
    labour = _apply_date_range(
        JobCardLabour.objects.filter(
            jobcard__is_active=True, technician__isnull=False
        ).exclude(jobcard__status='cancelled'),
        'jobcard__date', from_date, to_date
    )
    stats = (
        labour.order_by()
        .values('technician_id', 'technician__full_name')
        .annotate(
            jobs=Count('jobcard_id', distinct=True),
            done=Count(
                'jobcard_id', distinct=True,
                filter=Q(jobcard__status__in=['completed', 'closed'])
            ),
            hours=Sum('hours'),
            revenue=Sum('amount'),
        )
    )

    technician_rows = []
    for s in stats:
        hours = _money(s['hours'])
        revenue = _money(s['revenue'])
        technician_rows.append({
            'technician': s['technician__full_name'],
            'jobs': s['jobs'],
            'completed': s['done'],
            'completion_pct': round(s['done'] / s['jobs'] * 100, 1) if s['jobs'] else 0,
            'hours': hours,
            'revenue': revenue,
            'revenue_per_hour': revenue / hours if hours else ZERO,
            'hours_per_job': hours / s['jobs'] if s['jobs'] else ZERO,
        })
    technician_rows.sort(key=lambda r: r['revenue'], reverse=True)

    total_hours = sum((r['hours'] for r in technician_rows), ZERO)
    total_labour = sum((r['revenue'] for r in technician_rows), ZERO)

    # Status distribution (all active job cards in range)
    labels = dict(JobCard.STATUS_CHOICES)
    dist = (
        _apply_date_range(JobCard.objects.filter(is_active=True), 'date', from_date, to_date)
        .order_by().values('status').annotate(c=Count('id')).order_by('-c')
    )
    dist_total = sum(d['c'] for d in dist)
    status_rows = [{
        'status': labels.get(d['status'], d['status']),
        'count': d['c'],
        'share': round(d['c'] / dist_total * 100, 1) if dist_total else 0,
    } for d in dist]

    pending_now = _valid_jobs().filter(status__in=['open', 'in_progress', 'waiting']).count()

    return render(request, 'jobcard_app/reports/workshop_efficiency_report.html', {
        'technician_rows': technician_rows,
        'status_rows': status_rows,
        'from_date': from_date, 'to_date': to_date,
        'total_jobs': total_jobs,
        'completion_rate': round(completed_jobs / total_jobs * 100, 1) if total_jobs else 0,
        'on_time_pct': tat['on_time_pct'],
        'avg_tat': tat['avg'],
        'pending_now': pending_now,
        'total_hours': total_hours,
        'revenue_per_hour': total_labour / total_hours if total_hours else ZERO,
        'jobs_per_technician': round(total_jobs / len(technician_rows), 1) if technician_rows else 0,
    })