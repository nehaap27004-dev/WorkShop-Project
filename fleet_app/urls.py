from django.urls import path
from fleet_app.views import *
from . import views          # ← ADD THIS LINE AT THE TOP
from django.views.generic import RedirectView
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
    path('timesheets/', timesheet_report, name='timesheet_report'),
    path('timesheet/edit/<int:timesheet_id>/', time_sheet_view, name='timesheet_edit'),
    path('timesheet/delete/<int:timesheet_id>/', timesheet_delete, name='timesheet_delete'),
    path('timesheet/pdf/<int:timesheet_id>/', timesheet_pdf_view, name='timesheet_pdf'),
    path('timesheet/pdf/<int:pk>/no-header/', timesheet_pdf_without_header, name='timesheet_pdf_no_header'),
    
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
    
    
    # AFTER

    path('item/fleet-customers/', RedirectView.as_view(url='/customers-manage/', permanent=False), name='fleet_customer_management'),
    path('item/fleet-customers/<int:customer_id>/', RedirectView.as_view(url='/customers-manage/', permanent=False), name='fleet_customer_management_edit'),
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
    path('simple-quotation/pdf/<int:quotation_id>/', simple_quotation_pdf, name='simple_quotation_pdf'),
    path('simplequotation/pdf/<int:pk>/no-header/', simplequotation_pdf_without_header, name='simplequotation_pdf_no_header'),
    
    path('invoice/create/', create_invoice, name='create_invoice'),
    path('invoices/', invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/edit/', invoice_edit, name='invoice_edit'),
    path('invoice/edit/<int:invoice_id>/', create_invoice, name='edit_invoice'),
    path("invoice/delete/<int:invoice_id>/", invoice_delete, name="invoice_delete"),
    path('invoice/pdf/<int:invoice_id>/', invoice_pdf, name='invoice_pdf'),
    path('invoice/pdf/<int:pk>/no-header/', invoice_pdf_without_header, name='invoice_pdf_no_header'),
    path('get-vehicle-rates/', get_vehicle_rates, name='get_vehicle_rates'),

    path('delivery-contract/create/', create_delivery_contract, name='delivery_contract_create'),
    path('delivery-contract/edit/<int:contract_id>/', create_delivery_contract, name='delivery_contract_edit'),
    path('delivery-contract/list/', delivery_contract_list, name='delivery_contract_list'),
    path('delivery-contract/delete/<int:contract_id>/', delete_delivery_contract, name='delivery_contract_delete'),
    path('get-delivery-contract-details/', get_delivery_contract_details, name='get_delivery_contract_details'),
    path('delivery-contract/pdf/<int:contract_id>/', delivery_contract_pdf, name='delivery_contract_pdf'), 
    path('get-customer-contracts/', get_customer_contracts, name='get_customer_contracts'),
    path('delivery-contract/pdf/<int:pk>/no-header/', delivery_contract_pdf_without_header, name='delivery_contract_pdf_no_header'),

    path('company/', company_setup, name="company_setup"),
    path('company/documents/', document_list, name="document_list"),

    path('documents/delete/<int:doc_id>/', document_delete, name="document_delete"),
    
    path("fleet-hire/create/", fleet_hire_create, name="fleet_hire_create"),
    path("fleet-hire/", fleet_hire_list, name="fleet_hire_list"),
    path("fleet-hire/<int:pk>/", fleet_hire_detail, name="fleet_hire_detail"),
    path('fleet-hire/edit/<int:hire_id>/', fleet_hire_create, name='fleet_hire_edit'),
    path('fleet-hire/delete/<int:hire_id>/', fleet_hire_delete, name='fleet_hire_delete'),

    
    path('fleet/vouchers/', fleet_voucher_list, name='fleet_voucher_list'),
    path('fleet/vouchers/create/', fleet_voucher_create_update, name='fleet_voucher_create_update'),
    path('fleet/vouchers/<int:pk>/edit/', fleet_voucher_create_update, name='fleet_voucher_create_update'),
    
    path('get-voucher-number-fleet/', get_next_voucher_number_fleet, name='get_voucher_number_fleet'),

    path('fleet-contract/create/', create_fleet_contract, name='create_fleet_contract'),
    path('contract/edit/<int:pk>/', create_fleet_contract, name='edit_fleet_contract'),
    path('contracts/', fleet_contract_list, name='fleet_contract_list'),
    path("contract/delete/<int:pk>/", fleet_contract_delete, name="fleet_contract_delete"),

    path('ajax/add-manufacturer/', add_manufacturer_ajax, name='add_manufacturer_ajax'),
    path('ajax/add-vehicle-category/', add_vehicle_category_ajax, name='add_vehicle_category_ajax'),

    path('notifications/', get_notifications, name='get_notifications'),
    
     #EMI URLs
    path('emi/', emi_list, name='emi_list'),
    path('emi/create/', manage_emi, name='create_emi'),
    path('emi/<int:emi_id>/edit/', manage_emi, name='edit_emi'),
    path('emi/<int:emi_id>/detail/', emi_detail, name='emi_detail'),
    path('emi/<int:emi_id>/delete/', delete_emi, name='delete_emi'),
    path('emi/notifications/', emi_notifications, name='emi_notifications'),
    path('emi/installment/<int:installment_id>/paid/', mark_installment_paid, name='mark_installment_paid'),
    path('emi/installment/<int:installment_id>/unpaid/', mark_installment_unpaid, name='mark_installment_unpaid'),
    
    # Vehicle Profit & Loss Report URLs
    path('reports/vehicle-pl/', vehicle_profit_loss_report, name='vehicle_pl_report'),
    path('reports/vehicle-pl/<int:vehicle_id>/', vehicle_profit_loss_detail, name='vehicle_pl_detail'),

    path('offhire/create/', create_offhire, name='create_offhire'),
    path('offhire/edit/<int:offhire_id>/', create_offhire, name='edit_offhire'),
    path('offhire/list/', offhire_list, name='offhire_list'),
    path('offhire/delete/<int:offhire_id>/', delete_offhire, name='delete_offhire'),
    
    # AJAX endpoints for OffHire
    path('get-customer-delivery-contracts-offhire/', get_customer_delivery_contracts_offhire, name='get_customer_delivery_contracts_offhire'),
    path('get-delivery-contract-details-offhire/', get_delivery_contract_details_offhire, name='get_delivery_contract_details_offhire'),

    path('reports/asset_report/', asset_report, name='asset_report'),

    path('trial-balance/', trial_balance_report, name='trial_balance_report'),
    path('trial-balance/postings/', trial_balance_postings_ajax, name='trial_balance_postings_ajax'),

    path("ajax/get-ledgers/", get_ledgers_by_group, name="get_ledgers_by_group"),

    path('reports/balance-sheet/', balance_sheet, name='balance_sheet'),

    path('reports/profit-loss/', profit_and_loss, name='profit_loss'),

    # Purchase Orders
    path('purchase-orders/', po_list,   name='po_list'),
    path('purchase-orders/create/', po_create, name='po_create'),
    path('purchase-orders/<int:pk>/edit/', po_edit,   name='po_edit'),
    path('purchase-orders/<int:pk>/delete/', po_delete, name='po_delete'),
    path('purchase-orders/<int:pk>/pdf/', po_pdf,    name='po_pdf'),

]