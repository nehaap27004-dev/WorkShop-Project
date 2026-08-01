from django.shortcuts import render
from audit_app.models import ActivityLog
# Create your views here.
from django.core.paginator import Paginator


def activity_log_list(request):
    # Fetch all logs (ordering is handled by Meta in models.py)
    log_queryset = ActivityLog.objects.all()
    
    # Pagination: Show 20 logs per page
    paginator = Paginator(log_queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'activity_log_list.html', context)