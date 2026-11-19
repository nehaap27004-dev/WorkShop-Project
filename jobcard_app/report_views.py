from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.utils.dateparse import parse_date

from .models import JobCard

from django.db.models import Q, Exists, OuterRef
from .models import DeliveryNote, Invoice
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone


from .models import Invoice

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

@login_required
def jobcard_reports_dashboard(request):
    return render(
        request,
        'jobcard_app/reports/jobcard_reports_dashboard.html'
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