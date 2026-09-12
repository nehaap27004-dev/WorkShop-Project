from django.urls import path
from . import views

app_name = 'jobcard_app'

urlpatterns = [
     # Service Category
     path('service-category/',
          views.service_category_list,
          name='service_category_list'),

     path('service-category/create/',
          views.service_category_create,
          name='service_category_create'),

     path('service-category/<int:pk>/edit/',
          views.service_category_edit,
          name='service_category_edit'),

     path('service-category/<int:pk>/delete/',
          views.service_category_delete,
          name='service_category_delete'),

     # Service Type
     path('service-type/',
          views.service_type_list,
          name='service_type_list'),

     path('service-type/create/',
          views.service_type_create,
          name='service_type_create'),

     path('service-type/<int:pk>/edit/',
          views.service_type_edit,
          name='service_type_edit'),

     path('service-type/<int:pk>/delete/',
          views.service_type_delete,
          name='service_type_delete'),

     # AJAX
     path('ajax/get-service-categories/',
          views.get_service_categories,
          name='jc_get_service_categories'),

     path('ajax/get-service-types/',
          views.get_service_types,
          name='jc_get_service_types'),

     path('ajax/get-categories/',
          
          views.ajax_get_categories,
          name='ajax_get_categories'),

    # ── Job Card ──────────────────────────────────────────────
    path('', views.jobcard_list, name='jobcard_list'),
    path('create/', views.jobcard_create, name='jobcard_create'),
    path('edit/<int:pk>/', views.jobcard_edit, name='jobcard_edit'),
    path('delete/<int:pk>/', views.jobcard_delete, name='jobcard_delete'),
    path('ajax/jc-get-vehicles/', views.jc_get_vehicles, name='jc_get_vehicles'),
    path('ajax/jc-get-items/', views.jc_get_items, name='jc_get_items'),
    path('ajax/jc-search-jobcards/', views.jc_search_jobcards, name='jc_search_jobcards'),
    path('ajax/get-inspections/',views.ajax_get_inspections,name='ajax_get_inspections'),
    path('ajax/get-next-jobcard-number/', views.get_next_jobcard_number, name='get_next_jobcard_number'),


     # ── Quotations ────────────────────────────────────────────
    path('quotation/',
         views.quotation_list,
         name='quotation_list'),

    path('quotation/create/',
         views.quotation_create,
         name='quotation_create'),

    path('quotation/<int:pk>/',
         views.quotation_detail,
         name='quotation_detail'),

    path('quotation/<int:pk>/edit/',
         views.quotation_edit,
         name='quotation_edit'),

    path('quotation/<int:pk>/delete/',
         views.quotation_delete,
         name='quotation_delete'),
    path('quotation/<int:pk>/delete/',
          views.quotation_delete,
          name='quotation_delete'),

    path('quotation/<int:pk>/status-update/',
          views.quotation_status_update,
          name='quotation_status_update'),
    path('ajax/get-next-quotation-number/', views.get_next_quotation_number, name='get_next_quotation_number'),
    
   

  


    path('vehicles/',views.wv_list,name='wv_list'),
 
    path('vehicles/create/',
         views.wv_create,
         name='wv_create'),
 
    # Pre-fill customer from customer list "Add Vehicle" button
    path('vehicles/create/customer/<int:customer_id>/',
         views.wv_create,
         name='wv_create_for_customer'),
 
    
 
    path('vehicles/<int:pk>/edit/',
         views.wv_edit,
         name='wv_edit'),
 
    path('vehicles/<int:pk>/delete/',
         views.wv_delete,
         name='wv_delete'),
 
    # AJAX endpoints
 
    path('ajax/vehicle-search/',views.ajax_wv_search,name='ajax_wv_search'),
 
    path('inspection/',views.inspection_list,name='inspection_list'),
 
    path('inspection/create/',views.inspection_create,name='inspection_create'),
 
    path('inspection/create/vehicle/<int:vehicle_id>/', views.inspection_create,name='inspection_create_for_vehicle'),
 


    path('inspection/<int:pk>/edit/', views.inspection_edit,name='inspection_edit'),
 
    path('inspection/<int:pk>/delete/',views.inspection_delete,name='inspection_delete'),
 
    # AJAX
    path('ajax/inspection-vehicles/',views.insp_get_vehicles,name='insp_get_vehicles'),

   
    path('estimate/',
         views.estimate_list,
         name='estimate_list'),

    path('estimate/create/',
         views.estimate_create,
         name='estimate_create'),

    path('estimate/<int:pk>/',
         views.estimate_detail,
         name='estimate_detail'),

    path('estimate/<int:pk>/edit/',
         views.estimate_edit,
         name='estimate_edit'),

    path('estimate/<int:pk>/delete/',
         views.estimate_delete,
         name='estimate_delete'),
    path('ajax/get-next-estimate-number/', views.get_next_estimate_number, name='get_next_estimate_number'),
    # ── Estimate AJAX ─────────────────────────────────────────
    path('ajax/search-jobcards/',
         views.jc_search_jobcards,
         name='jc_search_jobcards'),

    path('ajax/get-vehicles/',
         views.jc_get_vehicles,
         name='jc_get_vehicles'),

    path('ajax/get-items/',
         views.jc_get_items,
         name='jc_get_items'),
    path(
    "ajax/get-estimate-data/",
    views.jc_get_estimate_data,
    name="jc_get_estimate_data"),
    path(
    "ajax/get-customer-estimates/",
    views.ajax_get_customer_estimates,
    name="ajax_get_customer_estimates"),
    path('ajax/get-all-items/',
     views.ajax_get_all_items,
     name='ajax_get_all_items'),
    
    path('ajax/get-jobcard-complaints/',
     views.ajax_get_jobcard_complaints,
     name='ajax_get_jobcard_complaints'),
    # ── Delivery Notes ────────────────────────────────────────
     path('delivery/',
          views.delivery_list,
          name='delivery_list'),

    path('delivery/create/',
         views.delivery_create,
         name='delivery_create'),

    path('delivery/<int:pk>/',
         views.delivery_detail,
         name='delivery_detail'),

    path('delivery/<int:pk>/edit/',
         views.delivery_edit,
         name='delivery_edit'),
    path('delivery/get-next-number/', views.get_next_delivery_number, name='get_next_delivery_number'),
    path('delivery/<int:pk>/delete/',
         views.delivery_delete,
         name='delivery_delete'),
    path('ajax/get-jobcard-for-delivery/',
          views.ajax_get_jobcard_for_delivery,
          name='ajax_get_jobcard_for_delivery'), 
    path('ajax/get-docs-for-delivery/',
          views.ajax_get_docs_for_delivery,
          name='ajax_get_docs_for_delivery'),
    # ── AJAX ─────────────────────────────────────────────────
    path('ajax/search-deliveries/',
         views.ajax_search_deliveries,
         name='ajax_search_deliveries'),
    # ── Invoices ─────────────────────────────────────────────
    path('invoice/',
         views.invoice_list,
         name='invoice_list'),

    path('invoice/create/',
         views.invoice_create,
         name='invoice_create'),
    path('ajax/get-next-invoice-number/', views.get_next_invoice_number, name='get_next_invoice_number'),
    path('invoice/<int:pk>/',
         views.invoice_detail,
         name='invoice_detail'),

    path('invoice/<int:pk>/edit/',
         views.invoice_edit,
         name='invoice_edit'),

    path('invoice/<int:pk>/delete/',
         views.invoice_delete,
         name='invoice_delete'),

    path(
          'ajax/get-docs-for-invoice/',
          views.ajax_get_docs_for_invoice,
          name='ajax_get_docs_for_invoice'
          ),

   

    # ── AJAX ─────────────────────────────────────────────────
    path('ajax/search-deliveries/',
         views.ajax_search_deliveries,
         name='ajax_search_deliveries'),

    path('ajax/vehicles-by-customer/', views.ajax_wv_by_customer, name='ajax_wv_by_customer'),
    path('ajax/relational-mapping/', views.ajax_get_relational_mapping, name='ajax_get_relational_mapping'),

    # ── Skill Tag Master ──────────────────────────────────────
    path('skill-tags/', views.skill_tag_list, name='skill_tag_list'),
    path('skill-tags/create/', views.skill_tag_save, name='skill_tag_create'),
    path('skill-tags/<int:pk>/edit/', views.skill_tag_save, name='skill_tag_edit'),
    path('skill-tags/<int:pk>/toggle/', views.skill_tag_toggle, name='skill_tag_toggle'),
    path('skill-tags/<int:pk>/delete/', views.skill_tag_delete, name='skill_tag_delete'),
]
