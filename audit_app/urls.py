from django.urls import path
from audit_app.views import *

app_name = 'audit_app'

urlpatterns = [
    path('activity-log/', activity_log_list, name='activity_log_list'),
]
