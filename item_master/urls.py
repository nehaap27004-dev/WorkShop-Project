from django.urls import path

from .views import *

app_name = 'item_master'

urlpatterns = [
    path('item/categories/', item_category_create_update_list, name='item_category_create_update_list'),
    path('item/categories/<int:category_id>/', item_category_create_update_list, name='item_category_create_update_list'),

    path('item/manufacturers/', item_manufacturer_create_update_list, name='item_manufacturer_create_update_list'),
    path('item/manufacturers/<int:manufacturer_id>/', item_manufacturer_create_update_list, name='item_manufacturer_create_update_list'),

    path('items/', item_list, name='item_list'),
    path('items/<int:item_id>/', item_create_update, name='item_create_update'),
    path('items/create/', item_create_update, name='item_create_update'), 
    path('items/search/', item_search, name='item_search'),
    path('delete/<int:item_id>/', delete_item, name='delete_item'), 

    path('item/<int:item_id>/units/', item_alter_units_view, name='item_alter_units_view'),


    path('add-category/', add_category, name='add_category'),

    
    path('item/vendors/', vendor_management, name='vendor_management'),
    path('item/vendors/<int:vendor_id>/', vendor_management, name='vendor_management'),

    path('units/', unit_management, name='unit_manage'),
    path('units/edit/<int:unit_id>/', unit_management, name='unit_manage_edit'),

    path('VAT/', VAT_management, name='VAT_manage'),
    path('VAT/edit/<int:TAX_id>/', VAT_management, name='VAT_manage_edit'),

    path('purchase/create/', create_purchase_voucher, name='create_purchase_voucher'),
    path('purchase/list/', purchase_voucher_list, name='purchase_voucher_list'),
    path('purchase-vouchers/<int:voucher_id>/', purchase_voucher_detail, name='purchase_voucher_detail'),
    path("purchase/<int:pk>/edit/", edit_purchase_voucher, name="purchase_voucher_edit"),
    # path("purchase/edit/<int:pk>/", create_purchase_voucher, name="purchase_voucher_edit"),
    path('purchase-voucher/<int:pk>/delete/', purchase_voucher_delete, name='purchase_voucher_delete'),


    path('get-item-details/', get_item_details, name='get_item_details'),
    
    
    path('purchaseReturn/create/', create_purchaseReturn_voucher, name='create_purchaseReturn_voucher'),
    path("purchaseReturn/<int:pk>/edit/", edit_purchaseReturn_voucher, name="purchaseReturn_voucher_edit"),
    # path('purchaseReturn/list/', purchaseReturn_voucher_list, name='purchaseReturn_voucher_list'),
    # path('purchaseReturn-vouchers/<int:voucher_id>/', purchaseReturn_voucher_detail, name='purchaseReturn_voucher_detail'),
    # path('purchaseReturn-voucher/<int:pk>/delete/', purchaseReturn_voucher_delete, name='purchaseReturn_voucher_delete'),


    

    path('item/customers/', customer_management, name='customer_management'),
    path('item/customers/<int:customer_id>/', customer_management, name='customer_management'),

    path('sales-voucher/create/', sales_voucher_create, name='sales_voucher_create'),
    path('sales-voucher/', sales_voucher_list, name='sales_voucher_list'),
    path('sales-voucher/<int:voucher_id>/', sales_voucher_detail, name='sales_voucher_detail'),
    
    path('salesReturn-voucher/create/', salesReturn_voucher_create, name='salesReturn_voucher_create'),
    # path('salesReturn-voucher/', salesReturn_voucher_list, name='salesReturn_voucher_list'),
    # path('salesReturn-voucher/<int:voucher_id>/', salesReturn_voucher_detail, name='salesReturn_voucher_detail'),


    


    path('item/stock_list/', stock_list, name='stock_list'),
    path('get_alter_units_stock/<int:item_id>/', get_alter_units_stock, name='get_alter_units_stock'),

    path('search-items/', search_items, name='search_items'),

    path('outstanding-report/', outstanding_report_view, name='outstanding_report'),
    
    path('settle-bill/', settle_bill, name='settle_bill'),
    path('get_outstanding_records/', get_outstanding_records, name='get_outstanding_records'),
    
    path('daybook/', daybook_report_list, name='daybook_report_list'),
    
    path('get-outstanding-reports/', get_outstanding_reports, name='get_outstanding_reports'),
    path('get-outstanding-reports-receipt/', get_outstanding_reports_receipt, name='get_outstanding_reports_receipt'),
    path('create-bill-by-bill/', create_bill_by_bill, name='create_bill_by_bill'),
     
    path('cost-center/create/', create_cost_center, name='create_cost_center'),
    path('cost-center/', cost_center_list, name='cost_center_list'), 
    
    path('opening-stock/create/', create_opeingstock_voucher, name='create_opeingstock_voucher'),
    path('opening-stock/list/', opening_stock_list, name='opening_stock_list'),
    path('opening-stock-list/<int:voucher_id>/', opening_stock_detail, name='opening_stock_detail'),
    
    
    
    
     path('api/item-alter-units/<int:item_id>/', get_item_alter_units, name='get_item_alter_units'),
     
     path('create-unit-modal/', create_unit_modal, name='create_unit_modal'),
     
     path('create-cost-center-modal/', create_cost_center_modal, name='create_cost_center_modal'),
     
     path('create-vat-modal/', create_vat_modal, name='create_vat_modal'),
     
     path('create-category-modal/', create_category_modal, name='create_category_modal'),
     
     path('create-manufacturer-modal/', create_manufacturer_modal, name='create_manufacturer_modal'),

    path('batch/', batch_create_update, name='batch_create'),
    path('batch/<int:pk>/', batch_create_update, name='batch_update'),
    path('batches/', batch_list, name='batch_list'),
    path('create-batch-modal/', create_batch_modal, name='create_batch_modal'),

    
    path('vouchers/', voucher_list, name='voucher_list'),
    path('vouchers/create/', voucher_create_update, name='voucher_create_update'),
    path('vouchers/<int:pk>/edit/', voucher_create_update, name='voucher_create_update'),
    
    path('get-item-batches/', get_item_batches, name='get_item_batches'),
    
    path('api/item-barcode-status/<int:item_id>/', get_item_barcode_status, name='item_barcode_status'),
    
    path('get-item-batch-status/<int:item_id>/', get_item_batch_status, name='get_item_batch_status'),
    
    path('get-voucher-number/', get_next_voucher_number, name='get_voucher_number'),
    
    path('stock-transfer/', create_stock_transfer, name='stock_transfer'),
    path('api/get-item-units-rate/<int:item_id>/', get_item_units_rate, name='get_item_units_rate'),
    path('api/get-item-batches/<int:item_id>/', get_item_batches_stocktransfer, name='get_item_batches'),
    # path('get-items/<int:cost_center_id>/', get_items_for_cost_center, name='get_items_for_cost_center'),
    path('get-items/<int:cost_center_id>/', get_items_by_costcenter, name='get_items_by_costcenter'),
    
    path('sales-returns/', sales_return_list, name='sales_return_list'),
    path('sales-return/<int:pk>/', sales_return_detail, name='sales_return_detail'),
    
    path('ajax/get-stock-quantity/', get_stock_quantity, name='get_stock_quantity'),
    
    path('get-item-stock/<int:cost_center_id>/<int:item_id>/', get_item_stock, name='get_item_stock'),
    
    path("filter-ledgers-purchase/", filter_ledgers_view_purchase, name="filter_ledgers_purchase"),
    path("filter-ledgers-sales/", filter_ledgers_sales_view, name="filter_ledgers_sales"),

    

]