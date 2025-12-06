from django.urls import path
from settings.views import *

app_name = "settings"

urlpatterns = [
    path('settings/', settings_view, name='settings_view'),
    
    path('currency/', currency_list_create, name='currency_list_create'),
    path('currency/<int:pk>/', currency_list_create, name='currency_edit'),
    path('currency/delete/<int:pk>/', currency_delete, name='currency_delete'),
    
]
