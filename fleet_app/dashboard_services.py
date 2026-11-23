from datetime import date, timedelta
import calendar
from decimal import Decimal
from django.utils import timezone
from django.db.models import Count, Q
from jobcard_app.models import JobCard, Invoice as JobcardInvoice, VehicleInspection
from audit_app.models import ActivityLog
from fleet_app.models import Vehicle

DATE_DISPLAY_FMT = "%d-%b-%Y"
DATE_ISO_FMT = "%Y-%m-%d"

def parse_date_str(date_str):
    if not date_str:
        return None
    for fmt in (DATE_DISPLAY_FMT, DATE_ISO_FMT, "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return timezone.datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None

def get_period_date_range(period='month', from_date_str=None, to_date_str=None):
    today = timezone.localdate()
    period = (period or 'month').lower()

    if period == 'today':
        d_from = today
        d_to = today
        prev_from = today - timedelta(days=1)
        prev_to = today - timedelta(days=1)
        period_label = "Today"
    elif period == 'week':
        d_from = today - timedelta(days=today.weekday())
        d_to = today
        prev_from = d_from - timedelta(days=7)
        prev_to = d_from - timedelta(days=1)
        period_label = "This Week"
    elif period == 'custom':
        parsed_from = parse_date_str(from_date_str)
        parsed_to = parse_date_str(to_date_str)
        d_from = parsed_from or today.replace(day=1)
        d_to = parsed_to or today
        days = max((d_to - d_from).days, 1)
        prev_from = d_from - timedelta(days=days)
        prev_to = d_from - timedelta(days=1)
        period_label = "Custom"
    else:  # default 'month'
        period = 'month'
        d_from = today.replace(day=1)
        _, last_day = calendar.monthrange(today.year, today.month)
        d_to = today.replace(day=last_day)
        # previous month
        first_current = d_from
        prev_month_last = first_current - timedelta(days=1)
        prev_from = prev_month_last.replace(day=1)
        prev_to = prev_month_last
        period_label = "This Month"

    return {
        'period': period,
        'period_label': period_label,
        'date_from': d_from,
        'date_to': d_to,
        'prev_from': prev_from,
        'prev_to': prev_to,
        'from_display': d_from.strftime(DATE_DISPLAY_FMT),
        'to_display': d_to.strftime(DATE_DISPLAY_FMT),
        'from_iso': d_from.strftime(DATE_ISO_FMT),
        'to_iso': d_to.strftime(DATE_ISO_FMT),
    }

def calculate_dashboard_metrics(period='month', from_date_str=None, to_date_str=None):
    from fleet_app.views import get_expense_total

    rng = get_period_date_range(period, from_date_str, to_date_str)
    d_from = rng['date_from']
    d_to = rng['date_to']
    prev_from = rng['prev_from']
    prev_to = rng['prev_to']

    # --- 1. OPEN JOB CARDS ---
    # Total active open job cards in the system (real-time active workload)
    total_active_open = JobCard.objects.filter(is_active=True, status='open').count()
    # Job cards opened in this specific period
    open_opened_in_period = JobCard.objects.filter(
        is_active=True, status='open', date__range=(d_from, d_to)
    ).count()
    prev_open_in_period = JobCard.objects.filter(
        is_active=True, status='open', date__range=(prev_from, prev_to)
    ).count()

    # The user specifically noted: "ensuring figures like open job cards exactly match the actual count entered in the system"
    # In the workshop, the open job cards backlog is the primary operational figure
    open_jobcards_count = total_active_open

    # --- 2. IN SERVICE ---
    # Either job cards with status 'in_progress' or vehicles under service (status='3')
    in_service_jc = JobCard.objects.filter(is_active=True, status='in_progress').count()
    on_service_fleet = Vehicle.objects.filter(status='3').count()
    in_service_count = in_service_jc or on_service_fleet
    prev_in_service = JobCard.objects.filter(
        is_active=True, status='in_progress', date__range=(prev_from, prev_to)
    ).count()

    # --- 3. JOBS COMPLETED ---
    jobs_completed_count = JobCard.objects.filter(
        is_active=True, status__in=['completed', 'closed'], date__range=(d_from, d_to)
    ).count()
    prev_jobs_completed = JobCard.objects.filter(
        is_active=True, status__in=['completed', 'closed'], date__range=(prev_from, prev_to)
    ).count()

    # --- 4. INVOICES ---
    invoices_count = JobcardInvoice.objects.filter(
        is_active=True, invoice_date__range=(d_from, d_to)
    ).count()
    prev_invoices = JobcardInvoice.objects.filter(
        is_active=True, invoice_date__range=(prev_from, prev_to)
    ).count()

    # --- 5. EXPENSES ---
    try:
        total_expense = float(get_expense_total(d_from, d_to) or 0)
    except Exception:
        total_expense = 0.0

    try:
        prev_expense = float(get_expense_total(prev_from, prev_to) or 0)
    except Exception:
        prev_expense = 0.0

    def calc_trend(curr, prev, is_currency=False):
        if prev > 0:
            pct = round(((curr - prev) / prev) * 100)
            sign = "+" if pct > 0 else ""
            is_pos = pct >= 0
            text = f"{sign}{pct}% vs previous period"
        else:
            if curr > 0:
                is_pos = True
                text = f"+100% vs previous period"
            else:
                is_pos = True
                text = "0% vs previous period"
        return {
            'text': text,
            'is_positive': is_pos,
        }

    trends = {
        'open_jobcards': calc_trend(open_opened_in_period, prev_open_in_period),
        'in_service': calc_trend(in_service_count, prev_in_service),
        'jobs_completed': calc_trend(jobs_completed_count, prev_jobs_completed),
        'invoices': calc_trend(invoices_count, prev_invoices),
        'total_expense': calc_trend(total_expense, prev_expense, is_currency=True),
    }

    # --- DONUT CHART (Job Card Status Summary) ---
    donut_open = total_active_open
    donut_in_progress = in_service_count
    donut_completed = jobs_completed_count
    donut_waiting = JobCard.objects.filter(is_active=True, status='waiting').count()
    donut_closed = JobCard.objects.filter(
        is_active=True, status='closed', date__range=(d_from, d_to)
    ).count()
    donut_total = donut_open + donut_in_progress + donut_completed + donut_waiting + donut_closed

    circumference = 376.991  # 2 * PI * 60
    slices = [
        {'name': 'Open', 'key': 'open', 'count': donut_open, 'color': '#9f1045'},
        {'name': 'In Service', 'key': 'in_progress', 'count': donut_in_progress, 'color': '#16a34a'},
        {'name': 'Completed', 'key': 'completed', 'count': donut_completed, 'color': '#0284c7'},
        {'name': 'Waiting Parts', 'key': 'waiting', 'count': donut_waiting, 'color': '#f59e0b'},
        {'name': 'Closed', 'key': 'closed', 'count': donut_closed, 'color': '#cbd5e1'},
    ]

    offset = 0.0
    for s in slices:
        pct = (s['count'] / donut_total * 100) if donut_total > 0 else 0
        arc = (s['count'] / donut_total * circumference) if donut_total > 0 else 0
        gap = circumference - arc
        s['pct'] = round(pct, 1)
        s['dasharray'] = f"{arc:.2f} {gap:.2f}"
        s['dashoffset'] = f"-{offset:.2f}"
        offset += arc

    # --- MONTHLY JOB TREND BAR CHART (Last 6 Months) ---
    monthly_trend = []
    today = timezone.localdate()
    # Go back 5 months to current month
    for i in range(5, -1, -1):
        # Calculate year and month for offset i
        m_calc = today.month - i
        y_calc = today.year
        while m_calc <= 0:
            m_calc += 12
            y_calc -= 1
        m_name = calendar.month_abbr[m_calc]
        
        m_created = JobCard.objects.filter(
            is_active=True, date__year=y_calc, date__month=m_calc
        ).count()
        m_completed = JobCard.objects.filter(
            is_active=True, status__in=['completed', 'closed'], date__year=y_calc, date__month=m_calc
        ).count()

        monthly_trend.append({
            'month': m_name,
            'year': y_calc,
            'created': m_created,
            'completed': m_completed,
        })

    max_val = max(
        max([m['created'] for m in monthly_trend] or [1]),
        max([m['completed'] for m in monthly_trend] or [1]),
        5
    )
    for m in monthly_trend:
        # Scale to max height of 120px
        m['height_created'] = max(int((m['created'] / max_val) * 120), 4 if m['created'] > 0 else 0)
        m['height_completed'] = max(int((m['completed'] / max_val) * 120), 4 if m['completed'] > 0 else 0)

    # --- RECENT ACTIVITIES ---
    # Query logs matching the period if available, otherwise most recent logs
    period_logs = ActivityLog.objects.filter(
        created_at__date__range=(d_from, d_to)
    ).order_by('-created_at')[:8]

    if not period_logs.exists():
        period_logs = ActivityLog.objects.all().order_by('-created_at')[:6]

    activities_list = []
    for log in period_logs:
        act_type = (log.action_type or '').upper()
        module = (log.module or '').upper()

        # Icon and color category
        if 'JOBCARD' in module or 'JOB' in act_type:
            color = 'red'
            icon = 'bi-file-earmark-text'
        elif 'INVOICE' in module:
            color = 'pink'
            icon = 'bi-receipt'
        elif 'INSPECTION' in module:
            color = 'green'
            icon = 'bi-check2'
        else:
            color = 'blue'
            icon = 'bi-activity'

        created_local = timezone.localtime(log.created_at) if timezone.is_aware(log.created_at) else log.created_at
        time_str = created_local.strftime("%I:%M %p")
        if created_local.date() != today:
            time_str = created_local.strftime("%d %b, %I:%M %p")

        activities_list.append({
            'title': log.description or f"{log.action_type} - {log.screen_name or log.module}",
            'subtitle': f"{log.screen_name or log.module or 'System'} | By {log.user_username or 'User'}",
            'time': time_str,
            'color': color,
            'icon': icon,
        })

    return {
        'status': 'success',
        'period': rng['period'],
        'period_label': rng['period_label'],
        'from_date': rng['from_iso'],
        'to_date': rng['to_iso'],
        'from_display': rng['from_display'],
        'to_display': rng['to_display'],
        'kpis': {
            'open_jobcards': open_jobcards_count,
            'open_opened_in_period': open_opened_in_period,
            'total_active_open': total_active_open,
            'in_service': in_service_count,
            'jobs_completed': jobs_completed_count,
            'invoices': invoices_count,
            'total_expense': total_expense,
            'total_expense_display': f"OMR {total_expense:.2f}",
            'trends': trends,
        },
        'donut': {
            'total': donut_total,
            'slices': slices,
        },
        'monthly_trend': monthly_trend,
        'activities': activities_list,
    }
