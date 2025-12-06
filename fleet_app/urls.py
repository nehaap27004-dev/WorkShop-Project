from django.urls import path
from fleet_app.views import *

app_name = 'fleet_app'

urlpatterns = [
    path('', fleet_home, name='fleet_home'),
    path('vehicles/', vehicle_list, name='vehicle_list'),
    
    path('manufacturers/', manufacturer_list, name='manufacturer_list'),
    path('manufacturers/new/', manufacturer_create, name='manufacturer_create'),
    path('manufacturers/<int:pk>/edit/', manufacturer_edit, name='manufacturer_edit'),
    path("manufacturer/<int:pk>/delete/", manufacturer_delete, name="manufacturer_delete"),
    
    path('vehicle-categories/', create_vehicle_category, name='create_vehicle_category'),
    path("vehicle-category/<int:pk>/edit/", vehicle_category_edit, name="vehicle_category_edit"),
    path("vehicle-category/<int:pk>/delete/", vehicle_category_delete, name="vehicle_category_delete"),
    
    path('vehicle-models/', create_vehicle_model, name='create_vehicle_model'),
    path('vehicle-models/update/<int:model_id>/', update_vehicle_model, name='update_vehicle_model'),
    path('vehicle-models-list/', vehicle_model_list, name='vehicle_model_list'),
    path("vehicle-model/<int:pk>/delete/", delete_vehicle_model, name="delete_vehicle_model"),
    path('get-models-by-manufacturer/', get_models_by_manufacturer, name='get_models_by_manufacturer'),
    
    
    path('drivers/', driver_list, name='driver_list'),  
    path('drivers/create/', create_driver, name='create_driver'), 
    path('driver/update/<int:driver_id>/', update_driver, name='update_driver'),
    
    path('vehicle/create/', create_or_update_vehicle, name='vehicle_create'),  
    path('vehicle/update/<int:pk>/', create_or_update_vehicle, name='vehicle_update'),
    path("vehicle/<int:pk>/delete/", delete_vehicle, name="delete_vehicle"),

    
    path('rentalcompanies/', rentalcompany_list, name='rentalcompany_list'),
    path('rentalcompany/new/', create_or_update_rentalcompany, name='rentalcompany_create'),
    path('rentalcompany/<int:pk>/edit/', create_or_update_rentalcompany, name='rentalcompany_update'),
    path("rentalcompany/<int:pk>/delete/", rentalcompany_delete, name="rentalcompany_delete"),
    
    #old
    path('rentalcompany/<int:company_id>/vehicles/', company_vehicles, name='company_vehicles'),
    
    path("company/<int:pk>/vehicles/", supplier_vehicles, name="supplier_vehicles"),

    path('rentalvehicles/', rentalcompanyvehicle_list, name='rentalcompanyvehicle_list'),
    path('rentalvehicles/create/', rentalcompanyvehicle_create_update, name='rentalcompanyvehicle_create'),
    path('rentalvehicles/update/<int:pk>/', rentalcompanyvehicle_create_update, name='rentalcompanyvehicle_update'),
    path('rentalcompanyvehicle/<int:pk>/delete/', rentalcompanyvehicle_delete, name='rentalcompanyvehicle_delete'),

    
    path('vendor/create/', vendor_create_update, name='vendor_create'),
    path('vendor/edit/<int:pk>/',vendor_create_update, name='vendor_update'),
    path('fleet/vendors/',vendor_list, name='vendor_list'),
    path('vendors/general/', general_vendor_list, name='general_vendor_list'),
    path('vendors/service/', service_vendor_list, name='service_vendor_list'),
    
    path('timesheet/', time_sheet_view, name='time_sheet'),
    path('timesheet/get_next_timesheet_no/', get_next_timesheet_no, name='get_next_timesheet_no'),
    path('timesheets/', timesheet_report, name='timesheet_report'),
    path('timesheet/edit/<int:timesheet_id>/', time_sheet_view, name='timesheet_edit'),
    path('timesheet/delete/<int:timesheet_id>/', timesheet_delete, name='timesheet_delete'),
    
    path('get_vehicle_reg_no/<int:vehicle_id>/', get_vehicle_reg_no, name='get_vehicle_reg_no'),
    
    path('vehicle-quotation/create/', create_fleet_quotation, name='create_vehicle_quotation'),
    path('quotations/', vehicle_quotation_list, name='vehicle_quotation_list'),
    path('quotations/<int:pk>/', vehicle_quotation_detail, name='vehicle_quotation_detail'),
    path('quotation/get_next_quotation_no/', get_next_quotation_no, name='get_next_quotation_no'),
    path('fleetquotations/', fleetquotation_list, name='fleetquotation_list'),
    path('fleetquotation/<int:pk>/edit/', fleetquotation_edit, name='fleetquotation_edit'),
    
    
    path('get_customer_address/<int:customer_id>/', get_customer_address, name='get_customer_address'),
    
    path('get-vehicle-rates/<int:vehicle_id>/', get_vehicle_rates, name='get_vehicle_rates'),
    
    path('repair-maintenance/', create_repair_and_maintenance, name='create_repair_and_maintenance'),
    path('maintenances/', maintenance_list, name='maintenance_list'),
    path('maintenance/<int:pk>/', maintenance_detail, name='maintenance_detail'),
    path('maintenances/get_next_voucher_no/', get_next_voucher_no, name='get_next_voucher_no'),
    
    path('vehicle-master-list/', vehicle_master_list, name='vehicle_master_list'),
    
    path('item/fleet-customers/', fleet_customer_management, name='fleet_customer_management'),
    path('item/fleet-customers/<int:customer_id>/', fleet_customer_management, name='fleet_customer_management'),
    path("fleetcustomer/<int:pk>/delete/", fleetcustomer_delete, name="fleetcustomer_delete"),
    
    
    path('staff-category/', staff_category_manage, name='staff_category_manage'),
    path('staff-category/<int:pk>/', staff_category_manage, name='staff_category_edit'),
    
    path('staff/', staff_manage, name='staff_manage'),
    path('staff/<int:pk>/', staff_manage, name='staff_edit'),
    
    path('add-vehicle-category/', add_vehicle_category_modal, name='add_vehicle_category'),
    
    path('ajax/add-vehicle-model/', add_vehicle_model, name='add_vehicle_model'),
    
    path('ajax/add-license-plate-code/', add_license_plate_code_modal, name='add_license_plate_code'),
    
    path('documents/', document_crud_view, name='document_crud'),
    path('documents/<int:pk>/', document_crud_view, name='document_update'),
    
    path('simple-quotation/create/', create_simple_quotation, name='create_quotation'),
    path('quotation/', simple_quotation_list, name='simple_quotation_list'),
    path('quotation/edit/<int:quotation_id>/', create_simple_quotation, name='edit_simple_quotation'),
    path('simple-quotation/delete/<int:quotation_id>/', simple_quotation_delete, name='simple_quotation_delete'),
    
    path('invoice/create/', create_invoice, name='create_invoice'),
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/edit/', invoice_edit, name='invoice_edit'),
    path('invoice/edit/<int:invoice_id>/', create_invoice, name='edit_invoice'),
    path("invoice/delete/<int:invoice_id>/", invoice_delete, name="invoice_delete"),
    
    path('company/', company_setup, name="company_setup"),
    path('company/documents/', document_list, name="document_list"),
    path('documents/delete/<int:doc_id>/', document_delete, name="document_delete"),
    
    path("fleet-hire/create/", fleet_hire_create, name="fleet_hire_create"),
    path("fleet-hire/", fleet_hire_list, name="fleet_hire_list"),
    path("fleet-hire/<int:pk>/", fleet_hire_detail, name="fleet_hire_detail"),
    path('fleet-hire/edit/<int:hire_id>/', fleet_hire_create, name='fleet_hire_edit'),
    
    path("hire/delete/<int:hire_id>/", fleet_hire_delete, name="fleet_hire_delete"),

    
    path('fleet/vouchers/', fleet_voucher_list, name='fleet_voucher_list'),
    path('fleet/vouchers/create/', fleet_voucher_create_update, name='fleet_voucher_create_update'),
    path('fleet/vouchers/<int:pk>/edit/', fleet_voucher_create_update, name='fleet_voucher_create_update'),
    
    path('get-voucher-number-fleet/', get_next_voucher_number_fleet, name='get_voucher_number_fleet'),

    path('fleet-contract/create/', create_fleet_contract, name='create_fleet_contract'),
    path('contract/edit/<int:pk>/', create_fleet_contract, name='edit_fleet_contract'),
    path('contracts/', fleet_contract_list, name='fleet_contract_list'),
    path("contract/delete/<int:pk>/", fleet_contract_delete, name="fleet_contract_delete"),



    
    


]