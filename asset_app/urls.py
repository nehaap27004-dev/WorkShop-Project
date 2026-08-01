from django.urls import path
from asset_app.views import *

urlpatterns = [

    path('asset-master/', asset_master_view, name='asset_master'),
    path('asset-master/<int:pk>/', asset_master_view, name='asset_edit'),
    path('asset-master/delete/<int:pk>/', asset_delete, name='asset_delete'),

]