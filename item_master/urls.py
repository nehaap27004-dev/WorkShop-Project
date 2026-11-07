from django.urls import path
from item_master.views import *

app_name = 'item_master'

urlpatterns = [
    path('item/categories/', item_category_create_update_list, name='item_category_create_update_list'),
    path('item/categories/<int:category_id>/', item_category_create_update_list, name='item_category_create_update_list'),
    path('item/categories/<int:category_id>/delete/', item_category_delete, name='item_category_delete'),

    path('item/manufacturers/', item_manufacturer_create_update_list, name='item_manufacturer_create_update_list'),
    path('item/manufacturers/<int:manufacturer_id>/', item_manufacturer_create_update_list, name='item_manufacturer_create_update_list'),
    path('item/manufacturers/<int:manufacturer_id>/delete/', item_manufacturer_delete, name='item_manufacturer_delete'),


    path('item/groups/', manage_item_group, name='manage_item_group'),
    path('item/groups/<int:group_id>/', manage_item_group, name='manage_item_group'),
    path('item/groups/<int:group_id>/delete/', delete_item_group, name='delete_item_group'),


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
    path('units/<int:unit_id>/delete/', unit_delete, name='unit_delete'),

    path('VAT/', VAT_management, name='VAT_manage'),
    path('VAT/edit/<int:TAX_id>/', VAT_management, name='VAT_manage_edit'),
    path('VAT/<int:TAX_id>/delete/', vat_delete, name='vat_delete'),

    path('itemgrv/create/', create_itemgrv_voucher, name='create_itemgrv_voucher'),
    path('itemgrv/list/', itemgrv_list, name='itemgrv_voucher_list'),
    path("itemgrv/<int:pk>/edit/", edit_itemgrv_voucher, name="itemgrv_voucher_edit"),
    path('itemgrv-voucher/<int:pk>/delete/', itemgrv_delete, name='itemgrv_delete'),

    path('ajax/get-uninvoiced-grvs/', get_uninvoiced_grvs, name='get_uninvoiced_grvs'),
    path('ajax/get-grv-details-purchase/', get_grv_details_for_purchase, name='get_grv_details_for_purchase'),

    path('purchase/create/', create_purchase_voucher, name='create_purchase_voucher'),
    path('purchase/list/', purchase_voucher_list, name='purchase_voucher_list'),
    path('purchase-vouchers/<int:voucher_id>/', purchase_voucher_detail, name='purchase_voucher_detail'),
    path("purchase/<int:pk>/edit/", edit_purchase_voucher, name="purchase_voucher_edit"),
    path('purchase-voucher/<int:pk>/delete/', purchase_voucher_delete, name='purchase_voucher_delete'),
    path('purchase/<int:pk>/pdf/', purchase_voucher_pdf, name='purchase_voucher_pdf'),

    path('salesreturn/create/', create_salesreturn_voucher, name='create_salesreturn_voucher'),
    path('salesreturn/list/', salesreturn_voucher_list, name='salesreturn_voucher_list'),
    path("salesreturn/<int:pk>/edit/", edit_salesreturn_voucher, name="salesreturn_voucher_edit"),
    path('salesreturn-voucher/<int:pk>/delete/', salesreturn_voucher_delete, name='salesreturn_voucher_delete'),

    path('get-item-details/', get_item_details, name='get_item_details'),

    path('item/customers/', customer_management, name='customer_management'),
    path('item/customers/<int:customer_id>/', customer_management, name='customer_management'),

    path('sales-voucher/create/', sales_voucher_create, name='sales_voucher_create'),
    path("sales/<int:pk>/edit/", edit_sales_voucher, name="sales_voucher_edit"),
    path('sales-voucher/', sales_voucher_list, name='sales_voucher_list'),
    path('sales-voucher/<int:voucher_id>/', sales_voucher_detail, name='sales_voucher_detail'),
    path('sales-voucher/<int:pk>/delete/', sales_voucher_delete, name='sales_voucher_delete'),

    path("purchase-return/<int:pk>/edit/", edit_purchase_return_voucher, name="purchase_return_voucher_edit"),
    path('purchase-return/', purchase_return_voucher_list, name='purchase_return_voucher_list'),
    path('purchase-return/<int:pk>/delete/', purchase_return_voucher_delete, name='purchase_return_voucher_delete'),
    path('purchase-return/create/', purchase_return_create, name='purchase_return_voucher_create'),


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
     
    path('cost-center/create/', cost_center_create_update_list, name='cost_center_create'),
    path('cost-center/<int:pk>/edit/', cost_center_create_update_list, name='cost_center_edit'),
    path('cost-center/<int:pk>/delete/', cost_center_delete, name='cost_center_delete'),
    
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

    path("ajax/get-items-by-group/", get_items_by_group,name="get_items_by_group",),

    path('opening_stock/create/', create_opening_stock, name='create_openingstock_voucher'),
    path('opening_stock/list/', opening_stock_list, name='opening_stock_list'),
    path("opening_stock/<int:pk>/edit/", edit_opening_stock, name="opening_stock_edit"),
    path("opening_stock-voucher/<int:pk>/delete/", opening_stock_delete, name="opening_stock_delete"),

    path('reports/stock-report/', stock_report, name='stock_report'),

    path('reports/current-stock-report/', current_stock_report, name='current_stock_report'),

    path('reports/purchase/', purchase_report, name='purchase_report'),

    path('get-item-stock/', get_item_current_stock, name='get_item_stock'),
    
]