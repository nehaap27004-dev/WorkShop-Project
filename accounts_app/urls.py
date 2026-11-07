from django.urls import path

from .views import *

app_name = 'accounts_app'

urlpatterns = [
    path('home/', home, name='home'),
    
    path('admin_login/', admin_login, name='admin_login'),
    path('logout/', logout_view, name='logout_view'),
    
    path('nature-of-groups/', nature_of_group_list, name='nature_of_group_list'),
    
    path('maingroup/', main_group_view, name='main_group_view'),
    path('maingroup/edit/<int:pk>/', main_group_edit, name='main_group_edit'),
    path('maingroup/delete/<int:pk>/', main_group_delete, name='main_group_delete'),
        
    path('group/', group_view, name='group_view'),
    path('group/edit/<int:pk>/', group_edit, name='group_edit'),
    path('group/delete/<int:pk>/', group_delete, name='group_delete'),
    
    path('subgroup/', subgroup_view, name='subgroup_view'),
    path('subgroup/edit/<int:pk>/', subgroup_edit, name='subgroup_edit'),
    path('subgroup/delete/<int:pk>/', subgroup_delete, name='subgroup_delete'),
    
    path('ledger/', ledger_view, name='ledger_view'),
    path('ledger/edit/<int:pk>/', ledger_edit, name='ledger_edit'),
    path('ledger/delete/<int:pk>/', ledger_delete, name='ledger_delete'),  
    
    path('local-payment/', local_payment_view, name='create_local_payment'),  # For creating
    path('local-payment/<int:pk>/', local_payment_view, name='update_local_payment'),  # For updating   
    path('local_payment_list/', local_payment_list, name='local_payment_list'),  # URL for the voucher list
    path('local_payment_details/<int:pk>/', local_payment_detail, name='local_payment_detail'),  # URL for voucher details
    path('local-payment/edit/<int:payment_id>/', local_payment_view, name='local_payment_edit'),
    path('delete-local-payment/<int:id>/', delete_local_payment, name='delete_local_payment'),
    
    path('create-ledger/', create_ledger, name='create_ledger'),
    
    path('groups/', group_management, name='group_management'),
    path('groups/<int:group_id>/', group_management, name='group_management'),
    path('groups/delete/<int:delete_id>/', group_management, name='group_management_delete'),
    
    path('customers-manage/', manage_customers, name='manage_customers'),
    path('customers/<int:pk>/', manage_customers, name='edit_customer'),
    
    path('vendors-manage/', manage_vendors, name='manage_vendors'),
    path('vendors/<int:pk>/', manage_vendors, name='edit_vendor'),
    
    path('add-customer-ajax/', add_customer_ajax, name='add_customer_ajax'),
    path('add-vendor-ajax/', add_vendor_ajax, name='add_vendor_ajax'),
    
    path('roles/', role_management, name='role_management'),
    path('roles/edit/<int:edit_id>/', role_management, name='role_edit_inline'),
    
    path('users/', user_management, name='user_management'),
    path('users/edit/<int:edit_id>/', user_management, name='user_edit_inline'),
    
    path('menus/', menu_list_create, name='menu_list_create'),
    path('menus/edit/<int:pk>/', menu_edit, name='menu_edit'),
    path('menus/delete/<int:pk>/', menu_delete, name='menu_delete'),
    
    path('privileges/', manage_privileges, name='manage_privileges'),
    
    path("clear-data/", clear_transactions, name="clear_data"),

    path('ledger-posting-report/', ledger_posting_report, name='ledger_posting_report'),
    
    path('payment/create/', create_payment, name='create_payment'),
    
    path('create-receiptbill/', create_ReceiptBillClearance, name='create_receiptbill'),
    path('receiptbill/view/<int:pk>/', view_receiptbill, name='view_receiptbill'),
    path('receiptbill/list/', list_receiptbill, name='list_receiptbill'),
    path('receiptbill/delete/<int:pk>/', receiptbill_delete, name='receiptbill_delete'),
    path('ajax/get-customer-invoices-openings/', get_customer_invoices_and_openings, name='get_customer_invoices_and_openings'),
    path('receiptbill/<int:pk>/pdf/', receiptbill_pdf, name='receiptbill_pdf'),
    path('receiptbill/view/<int:pk>/', view_receiptbill, name='view_receiptbill'),
    
    path('create-paymentbill/', create_PaymentBillClearance, name='create_paymentbill'),
    path('paymentbill/<int:pk>/view/', view_PaymentBillClearance, name='view_paymentbill'),
    path('paymentbill/list/', list_paymentbill, name='list_paymentbill'),
    path('paymentbill/delete/<int:pk>/', paymentbill_delete, name='paymentbill_delete'),
    path('get-supplier-hires-and-openings/', get_supplier_hires_and_openings, name='get_supplier_hires_and_openings'),
    path('paymentbill/<int:pk>/pdf/', paymentbill_pdf, name='paymentbill_pdf'),

    path('expense_list/', expense_list, name='expense_list'),
    path('expense/create/', create_edit_expense, name='create_expense'),
    path('expense/<int:pk>/edit/', create_edit_expense, name='edit_expense'),
    path('expense/delete/<int:pk>/',delete_expense, name='delete_expense'),
    path('expense/<int:pk>/pdf/', expense_pdf, name='expense_pdf'),

    path('get-expenses-for-payment/', get_expenses_for_payment, name='get_expenses_for_payment'),
    path('get-expense-details/<int:expense_id>/', get_expense_details_for_payment, name='get_expense_details_for_payment'),
    
    path("payment-create/", payment_create, name="payment_create"),
    path('payments-master/', list_payment, name='list_payment'),
    path('payment_master_delete/<int:pk>/', payment_master_delete, name='payment_master_delete'),
    path('payment/edit/<int:pk>/', payment_create, name='payment_edit'),
    path('payment/<int:pk>/pdf/', payment_pdf, name='payment_pdf'),
    
    path("receipt/create/", receipt_create, name="receipt_create"),
    path("receipt/list/", list_receipt, name="list_receipt"),
    path("receipt/delete/<int:pk>/", receipt_delete, name="receipt_delete"),
    path('receipt/edit/<int:pk>/', receipt_create, name='edit_receipt'),
    path('receipt/<int:pk>/pdf/', receipt_pdf, name='receipt_pdf'),
    
    path('ledger-postings/', ledger_posting_list, name='ledger_posting_list'),

    path('cheque-clearance/', cheque_clearance, name='cheque_clearance'),
    path('cheque-clearance/bills/', get_cheque_clearance_bills, name='get_cheque_clearance_bills'),
    path('cheque-clearance/update/', update_cheque_status, name='update_cheque_status'),

    # path('receipt-bill-outstanding-report/', client_outstanding_report, name='client_outstanding_report'),
    # path('reports/client-outstanding/<int:customer_id>/pdf/', client_outstanding_pdf, name='client_outstanding_pdf'),
    path('supplier-outstanding-report/', supplier_outstanding_report, name='supplier_outstanding_report'),

    path('journal/',                   journal_list,         name='journal_list'),
    path('journal/create/',            journal_create_edit,  name='journal_create'),
    path('journal/<int:pk>/edit/',     journal_create_edit,  name='journal_edit'),
    path('journal/<int:pk>/delete/',   journal_delete,       name='journal_delete'),
    path('journal/<int:pk>/pdf/',     journal_pdf,          name='journal_pdf'),

    path('contra/',                  contra_list,         name='contra_list'),
    path('contra/create/',           contra_create_edit,  name='contra_create'),
    path('contra/<int:pk>/edit/',    contra_create_edit,  name='contra_edit'),
    path('contra/<int:pk>/delete/',  contra_delete,       name='contra_delete'),
    path('contra/<int:pk>/pdf/',     contra_pdf,          name='contra_pdf'),
    path('contra/<int:pk>/csv/',     contra_csv,          name='contra_csv'),

    path('debitnote/create/', create_edit_debitnote, name='create_debitnote'),
    path('debitnote/view/<int:pk>/', view_debitnote, name='view_debitnote'),
    path('debitnote/delete/<int:pk>/', delete_debitnote, name='delete_debitnote'),
    path('debitnote/list/', list_debitnote, name='list_debitnote'),
    path('debitnote/<int:pk>/pdf/', debitnote_pdf, name='debitnote_pdf'),
    

    
    path('creditnote/create/', create_edit_creditnote, name='create_creditnote'),
    path('creditnote/edit/<int:pk>/', create_edit_creditnote, name='edit_creditnote'),
    path('creditnote/delete/<int:pk>/', delete_creditnote, name='delete_creditnote'),
    path('creditnote/list/', list_creditnote, name='list_creditnote'),
    path('creditnote/view/<int:pk>/', view_creditnote, name='view_creditnote'),
    path('creditnote/<int:pk>/pdf/', creditnote_pdf, name='creditnote_pdf'),
    

    path('bill-by-bill-report/', bill_by_bill_report, name='bill_by_bill_report'),

    path('billwise-opening-list/',billwise_opening_list, name='billwise_opening_list'),
    path('billwise-opening/delete/<int:pk>/',delete_billwise_opening,name='delete_billwise_opening'),
    path('billwise-opening/clear/',clear_billwise_opening,name='clear_billwise_opening'),
    path('billwise-opening/detail/<int:id>/', billwise_opening_detail, name='billwise_opening_detail'),
    path('billwise-opening/edit/<int:id>/', billwise_opening_edit, name='billwise_opening_edit'),
    path('billwise-opening/create/', billwise_opening_create, name='billwise_opening_create'),
    

    path('aging-report/', aging_report, name='aging_report'),

    path('ledger-report/', ledger_report_page, name='ledger_report_page'),
    path('ledger-report/data/', ledger_report_data, name='ledger_report_data'),

    path('openingvoucher/', list_openingvoucher, name='list_openingvoucher'),
    path('openingvoucher/create/', create_openingvoucher, name='create_openingvoucher'),
    path('openingvoucher/edit/<int:pk>/', edit_openingvoucher, name='edit_openingvoucher'),
    path('openingvoucher/delete/<int:pk>/', delete_openingvoucher, name='delete_openingvoucher'),

    path('new/reports/client-outstanding/<int:ledger_id>/pdf/',new_client_outstanding_pdf,name='new_client_outstanding_pdf'),
    path('new/reports/client-outstanding/', new_client_outstanding_report,name='new_client_outstanding_report'),
    path('reports/supplier-outstanding/',new_supplier_outstanding_report,name='new_supplier_outstanding_report'),
    path('reports/supplier-outstanding/<int:ledger_id>/pdf/',new_supplier_outstanding_pdf,name='new_supplier_outstanding_pdf'),

    path('reports/client-pdc/', client_pdc_report, name='client_pdc_report'),
    path('reports/supplier-pdc/', supplier_pdc_report, name='supplier_pdc_report'),
    
]
