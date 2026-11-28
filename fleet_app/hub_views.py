from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction
from django.urls import reverse


# ── 1. WORKSHOP HUB ────────────────────────────────────────────────────────
@login_required
def hub_workshop(request):
    """
    Workshop Operations: Job Cards, Inspections, Estimates, Quotations, Delivery Notes, Invoices.
    Matches exact UI from screenshot: 6 clean cards in 3 columns.
    """
    items = [
        {
            'name': 'Job Cards',
            'description': 'Create and manage job cards',
            'url': reverse('jobcard_app:jobcard_list'),
            'icon': 'bi-card-checklist',
        },
        {
            'name': 'Inspections',
            'description': 'Vehicle inspection and reports',
            'url': reverse('jobcard_app:inspection_list'),
            'icon': 'bi-clipboard-check',
        },
        {
            'name': 'Estimates',
            'description': 'Create service estimates',
            'url': reverse('jobcard_app:estimate_list'),
            'icon': 'bi-file-earmark-text',
        },
        {
            'name': 'Quotations',
            'description': 'Create and manage quotations',
            'url': reverse('jobcard_app:quotation_list'),
            'icon': 'bi-chat-square-quote',
        },
        {
            'name': 'Delivery Notes',
            'description': 'Create delivery notes',
            'url': reverse('jobcard_app:delivery_list'),
            'icon': 'bi-truck',
        },
        {
            'name': 'Invoices',
            'description': 'Create and manage invoices',
            'url': reverse('jobcard_app:invoice_list'),
            'icon': 'bi-receipt',
        },
    ]

    context = {
        'hub_id': 'workshop',
        'hub_title': 'Workshop',
        'hub_heading': 'Workshop Operations & Job Cards',
        'hub_subtitle': 'Manage job cards, inspections, estimates, quotations, delivery notes and invoices.',
        'hub_icon': 'bi-tools',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── 2. PURCHASE & SALES HUB ────────────────────────────────────────────────
@login_required
def hub_purchase_sales(request):
    """
    Purchase & Sales: Purchase Orders, Purchase Vouchers, Purchase Return,
    Sales Returns, Issue Voucher, Create GRV.
    """
    items = [
        {
            'name': 'Purchase Orders',
            'description': 'Create and manage purchase orders',
            'url': reverse('fleet_app:po_list'),
            'icon': 'bi-bag-check',
        },
        {
            'name': 'Purchase Vouchers',
            'description': 'Create and manage purchase vouchers',
            'url': reverse('item_master:purchase_voucher_list'),
            'icon': 'bi-receipt-cutoff',
        },
        {
            'name': 'Purchase Return',
            'description': 'Supplier returns and debit notes',
            'url': reverse('item_master:purchase_return_voucher_list'),
            'icon': 'bi-arrow-counterclockwise',
        },
        {
            'name': 'Sales Returns',
            'description': 'Customer returns and credit notes',
            'url': reverse('item_master:salesreturn_voucher_list'),
            'icon': 'bi-arrow-return-left',
        },
        {
            'name': 'Issue Voucher',
            'description': 'Spare parts issue vouchers',
            'url': reverse('item_master:sales_voucher_list'),
            'icon': 'bi-cart-check',
        },
        {
            'name': 'Create GRV',
            'description': 'Goods receipt vouchers and inspection',
            'url': reverse('item_master:create_itemgrv_voucher'),
            'icon': 'bi-box-arrow-in-down',
        },
    ]

    context = {
        'hub_id': 'purchase_sales',
        'hub_title': 'Purchase & Sales',
        'hub_heading': 'Purchase & Sales Management',
        'hub_subtitle': 'Manage purchase orders, purchase vouchers, returns, issue vouchers and goods receipt vouchers.',
        'hub_icon': 'bi-cart3',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── 3. VEHICLE & SERVICE MASTER HUB ────────────────────────────────────────
@login_required
def hub_vehicle_service(request):
    """
    Vehicle & Service Master: Vehicle Registration, Models, Types, Manufacturers,
    Service Category, Service Type.
    """
    items = [
        {
            'name': 'Vehicle Registration',
            'description': 'Register and manage vehicles',
            'url': reverse('jobcard_app:wv_list'),
            'icon': 'bi-car-front',
        },
        {
            'name': 'Models',
            'description': 'Manage vehicle models',
            'url': reverse('fleet_app:vehicle_model_list'),
            'icon': 'bi-grid-3x3-gap',
        },
        {
            'name': 'Types',
            'description': 'Vehicle categories and types',
            'url': reverse('fleet_app:create_vehicle_category'),
            'icon': 'bi-tags',
        },
        {
            'name': 'Manufacturers',
            'description': 'Manage vehicle manufacturers',
            'url': reverse('fleet_app:manufacturer_list'),
            'icon': 'bi-buildings',
        },
        {
            'name': 'Service Category',
            'description': 'Manage service categories',
            'url': reverse('jobcard_app:service_category_list'),
            'icon': 'bi-layers',
        },
        {
            'name': 'Service Type',
            'description': 'Manage service types and labour',
            'url': reverse('jobcard_app:service_type_list'),
            'icon': 'bi-wrench-adjustable',
        },
    ]

    context = {
        'hub_id': 'vehicle_service',
        'hub_title': 'Vehicle & Service Master',
        'hub_heading': 'Vehicle & Service Masters',
        'hub_subtitle': 'Manage vehicle registration, models, types, manufacturers, and service masters.',
        'hub_icon': 'bi-car-front-fill',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── 4. INVENTORY MANAGEMENT HUB ────────────────────────────────────────────
@login_required
def hub_inventory(request):
    """
    Inventory Management: Item Master, Item Category, Units, VAT, Batches,
    Cost Centers, Stock Summary.
    """
    items = [
        {
            'name': 'Item Master',
            'description': 'Catalog and spare parts master',
            'url': reverse('item_master:item_list'),
            'icon': 'bi-box-seam',
        },
        {
            'name': 'Item Category',
            'description': 'Classify parts and items',
            'url': reverse('item_master:item_category_create_update_list'),
            'icon': 'bi-diagram-3',
        },
        {
            'name': 'Units',
            'description': 'Units of measurement',
            'url': reverse('item_master:unit_manage'),
            'icon': 'bi-rulers',
        },
        {
            'name': 'VAT',
            'description': 'Manage VAT and tax rates',
            'url': reverse('item_master:VAT_manage'),
            'icon': 'bi-percent',
        },
        {
            'name': 'Batches',
            'description': 'Batch numbers and expiry tracking',
            'url': reverse('item_master:batch_list'),
            'icon': 'bi-stack',
        },
        {
            'name': 'Cost Centers',
            'description': 'Departmental cost centers',
            'url': reverse('item_master:cost_center_create'),
            'icon': 'bi-pie-chart',
        },
        {
            'name': 'Stock Summary',
            'description': 'Real-time inventory and stock levels',
            'url': reverse('item_master:stock_list'),
            'icon': 'bi-bar-chart-steps',
        },
    ]

    context = {
        'hub_id': 'inventory',
        'hub_title': 'Inventory Management',
        'hub_heading': 'Inventory & Stock Management',
        'hub_subtitle': 'Manage item master, categories, units, VAT, batches, cost centers and stock summary.',
        'hub_icon': 'bi-box-seam-fill',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── 5. CUSTOMERS & STAFF HUB ───────────────────────────────────────────────
@login_required
def hub_people_parties(request):
    """
    Customers & Staff: Suppliers, Customers, Staff Directories, Staff Categories, Skill Tags.
    """
    items = [
        {
            'name': 'Suppliers',
            'description': 'Manage parts vendors and suppliers',
            'url': reverse('accounts_app:manage_vendors'),
            'icon': 'bi-shop',
        },
        {
            'name': 'Customers',
            'description': 'Manage customer profiles and accounts',
            'url': reverse('accounts_app:manage_customers'),
            'icon': 'bi-people',
        },
        {
            'name': 'Staff Directories',
            'description': 'Technicians and workshop personnel',
            'url': reverse('fleet_app:staff_manage'),
            'icon': 'bi-person-badge',
        },
        {
            'name': 'Staff Categories',
            'description': 'Staff designations and roles',
            'url': reverse('fleet_app:staff_category_manage'),
            'icon': 'bi-diagram-2',
        },
        {
            'name': 'Skill Tags',
            'description': 'Technician specialties and skills',
            'url': reverse('jobcard_app:skill_tag_list'),
            'icon': 'bi-patch-check',
        },
    ]

    context = {
        'hub_id': 'people_parties',
        'hub_title': 'Customers & Staff',
        'hub_heading': 'Customers & Staff Management',
        'hub_subtitle': 'Manage suppliers, customers, staff directories, staff categories and skill tags.',
        'hub_icon': 'bi-people-fill',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── 6. ACCOUNTS HUB ────────────────────────────────────────────────────────
@login_required
def hub_accounts(request):
    """
    Accounts: Receipts, Payments, Cheque Clearance, Receipt Bill Clearance,
    Payment Bill Clearance, Journals, Contra, Expense Vouchers, Debit/Credit Notes, Opening Vouchers.
    """
    items = [
        {
            'name': 'Receipts',
            'description': 'Customer payment receipts',
            'url': reverse('accounts_app:list_receipt'),
            'icon': 'bi-arrow-down-left-circle',
        },
        {
            'name': 'Payments',
            'description': 'Supplier and expense payments',
            'url': reverse('accounts_app:list_payment'),
            'icon': 'bi-arrow-up-right-circle',
        },
        {
            'name': 'Cheque Clearance',
            'description': 'PDC and cheque status tracking',
            'url': reverse('accounts_app:cheque_clearance'),
            'icon': 'bi-check2-circle',
        },
        {
            'name': 'Receipt Bill Clearance',
            'description': 'Match receipts to sales invoices',
            'url': reverse('accounts_app:list_receiptbill'),
            'icon': 'bi-file-earmark-check',
        },
        {
            'name': 'Payment Bill Clearance',
            'description': 'Match payments to purchase bills',
            'url': reverse('accounts_app:list_paymentbill'),
            'icon': 'bi-file-earmark-diff',
        },
        {
            'name': 'Journals',
            'description': 'Double-entry journal vouchers',
            'url': reverse('accounts_app:journal_list'),
            'icon': 'bi-journal-text',
        },
        {
            'name': 'Contra',
            'description': 'Cash and bank transfer vouchers',
            'url': reverse('accounts_app:contra_list'),
            'icon': 'bi-arrow-left-right',
        },
        {
            'name': 'Expense Vouchers',
            'description': 'Workshop operational expenses',
            'url': reverse('accounts_app:expense_list'),
            'icon': 'bi-cash-stack',
        },
        {
            'name': 'Debit/Credit Notes',
            'description': 'Debit notes and credit notes',
            'url': reverse('accounts_app:list_debitnote'),
            'icon': 'bi-file-earmark-plus',
        },
        {
            'name': 'Opening Vouchers',
            'description': 'Financial opening balance vouchers',
            'url': reverse('accounts_app:list_openingvoucher'),
            'icon': 'bi-calendar-check',
        },
    ]

    context = {
        'hub_id': 'accounts',
        'hub_title': 'Accounts',
        'hub_heading': 'Accounts & Financial Management',
        'hub_subtitle': 'Manage receipts, payments, cheque clearance, clearances, journals, contra and ledgers.',
        'hub_icon': 'bi-wallet2',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── 7. ADMIN MASTER HUB ────────────────────────────────────────────────────
@login_required
def hub_admin_master(request):
    """
    Admin Master: Company Setup, Roles, Users, Menus, Menu Privileges, Document Centers, Groups, Ledgers.
    """
    items = [
        {
            'name': 'Company Setup',
            'description': 'Company profile and TRN details',
            'url': reverse('fleet_app:company_setup'),
            'icon': 'bi-building-gear',
        },
        {
            'name': 'Roles',
            'description': 'User roles and access permissions',
            'url': reverse('accounts_app:role_management'),
            'icon': 'bi-person-gear',
        },
        {
            'name': 'Users',
            'description': 'System user logins and accounts',
            'url': reverse('accounts_app:user_management'),
            'icon': 'bi-person-check',
        },
        {
            'name': 'Menus',
            'description': 'Configure system and user menus',
            'url': reverse('accounts_app:menu_list_create'),
            'icon': 'bi-list-ul',
        },
        {
            'name': 'Menu Privileges',
            'description': 'Menu visibility and access rights',
            'url': reverse('accounts_app:manage_privileges'),
            'icon': 'bi-shield-lock',
        },
        {
            'name': 'Document Centers',
            'description': 'Company documents and licenses',
            'url': reverse('fleet_app:document_list'),
            'icon': 'bi-folder2-open',
        },
        {
            'name': 'Groups',
            'description': 'Main groups and sub groups',
            'url': reverse('accounts_app:group_management'),
            'icon': 'bi-diagram-3-fill',
        },
        {
            'name': 'Ledgers',
            'description': 'Chart of accounts and general ledgers',
            'url': reverse('accounts_app:ledger_view'),
            'icon': 'bi-journal-bookmark',
        },
    ]

    context = {
        'hub_id': 'admin_master',
        'hub_title': 'Admin Master',
        'hub_heading': 'Admin Master & System Control',
        'hub_subtitle': 'Manage company setup, roles, users, menu privileges, document centers, groups, and ledgers.',
        'hub_icon': 'bi-shield-check',
        'items': items,
    }
    return render(request, 'hub_dashboard.html', context)


# ── LEGACY REDIRECT ALIASES ────────────────────────────────────────────────
@login_required
def hub_manage(request):
    return redirect('fleet_app:hub_workshop')

@login_required
def hub_master(request):
    return redirect('fleet_app:hub_vehicle_service')

@login_required
def hub_transactions(request):
    return redirect('fleet_app:hub_purchase_sales')


@login_required
@require_POST
def clear_transactions(request):
    """
    Deletes all transactional records across workshop, accounting, inventory,
    fleet operations, and activity logs while preserving all master/setup data.
    """
    from jobcard_app.models import (
        InvoiceItem, InvoiceVehicle, Invoice as JCInvoice,
        DeliveryService, DeliveryPart, DeliveryLabour, DeliveryNoteVehicle, DeliveryNote,
        QuotationItem, QuotationComplaint, QuotationVehicle, Quotation,
        EstimateItem, EstimateComplaint, EstimateVehicle, Estimate,
        ExteriorDamage, InteriorInspection, MechanicalInspection, AccessoriesInspection,
        InspectionFinding, VehicleInspection,
        CustomInspectionAnswer, CustomInspection,
        JobCardPart, JobCardLabour, JobCardFinding, JobCardComplaint, JobCardVehicle, JobCard,
    )
    from accounts_app.models import (
        LedgerPosting, BillClearance, BillWiseOpening,
        ReceiptDetails, ReceiptMaster, ReceiptBillDetails, ReceiptBillMaster,
        ReceiptItems, ReceiptCheque, Receipt,
        PaymentDetails, PaymentMaster, PaymentBillDetails, PaymentBillMaster,
        LocalPaymentItems, LocalPaymentCheque, LocalPayment, Payment,
        ExpenseDetails, ExpenseMaster,
        JournalDetail, JournalMaster, Journal,
        ContraMaster, Contra,
        DebitNoteDetail, DebitNoteMaster,
        CreditNoteDetail, CreditNoteMaster,
        OpeningVoucherDetails, OpeningVoucherMaster,
    )
    from item_master.models import (
        Stock, StockTransferItem, StockTransfer, OpeningStockDetail, OpeningStockMaster,
        ItemGrvDetail, ItemGrvMaster,
        PurchaseDetail, PurchaseMaster,
        PurchaseReturnDetail, PurchaseReturnMaster,
        SalesDetail, SalesMaster,
        SalesReturnDetail, SalesReturnMaster,
        Batch, OutstandingReport, BillByBill, DayBookReport,
    )
    from fleet_app.models import (
        OffHireDetails, OffHire,
        DeliveryContractSpareParts, DeliveryContractDetails, DeliveryContract,
        FleetHireDetails, FleetHire, FleetContract,
        FleetQuotationItem, FleetQuotation,
        SimpleQuotationDetails, SimpleQuotation,
        InvoiceDetails, Invoice as FleetInvoice,
        TimeSheetDetail, TimeSheet,
        RepairAndMaintenanceItem, RepairAndMaintenance,
        SpareParts, LabourCharge, RepairMaster,
        ReplacementDetail, ReplacementMaster,
        ReturnSparePartsDetails, ReturnSparePartsMaster,
        EMIInstallment, VehicleEMI, VehicleProfitLoss,
        PODetails, POMaster,
    )
    from audit_app.models import ActivityLog

    models_to_clear = [
        # 1. Workshop / Job Card Operations (child -> parent)
        InvoiceItem, InvoiceVehicle, JCInvoice,
        DeliveryService, DeliveryPart, DeliveryLabour, DeliveryNoteVehicle, DeliveryNote,
        QuotationItem, QuotationComplaint, QuotationVehicle, Quotation,
        EstimateItem, EstimateComplaint, EstimateVehicle, Estimate,
        ExteriorDamage, InteriorInspection, MechanicalInspection, AccessoriesInspection,
        InspectionFinding, VehicleInspection,
        CustomInspectionAnswer, CustomInspection,
        JobCardPart, JobCardLabour, JobCardFinding, JobCardComplaint, JobCardVehicle, JobCard,
        # 2. Accounting & Vouchers
        LedgerPosting, BillClearance, BillWiseOpening,
        ReceiptDetails, ReceiptMaster, ReceiptBillDetails, ReceiptBillMaster,
        ReceiptItems, ReceiptCheque, Receipt,
        PaymentDetails, PaymentMaster, PaymentBillDetails, PaymentBillMaster,
        LocalPaymentItems, LocalPaymentCheque, LocalPayment, Payment,
        ExpenseDetails, ExpenseMaster,
        JournalDetail, JournalMaster, Journal,
        ContraMaster, Contra,
        DebitNoteDetail, DebitNoteMaster,
        CreditNoteDetail, CreditNoteMaster,
        OpeningVoucherDetails, OpeningVoucherMaster,
        # 3. Inventory & Stock
        Stock, StockTransferItem, StockTransfer, OpeningStockDetail, OpeningStockMaster,
        ItemGrvDetail, ItemGrvMaster,
        PurchaseDetail, PurchaseMaster,
        PurchaseReturnDetail, PurchaseReturnMaster,
        SalesDetail, SalesMaster,
        SalesReturnDetail, SalesReturnMaster,
        Batch, OutstandingReport, BillByBill, DayBookReport,
        # 4. Fleet Operations & Contracts
        OffHireDetails, OffHire,
        DeliveryContractSpareParts, DeliveryContractDetails, DeliveryContract,
        FleetHireDetails, FleetHire, FleetContract,
        FleetQuotationItem, FleetQuotation,
        SimpleQuotationDetails, SimpleQuotation,
        InvoiceDetails, FleetInvoice,
        TimeSheetDetail, TimeSheet,
        RepairAndMaintenanceItem, RepairAndMaintenance,
        SpareParts, LabourCharge, RepairMaster,
        ReplacementDetail, ReplacementMaster,
        ReturnSparePartsDetails, ReturnSparePartsMaster,
        EMIInstallment, VehicleEMI, VehicleProfitLoss,
        PODetails, POMaster,
        # 5. Activity Logs
        ActivityLog,
    ]

    total_deleted = 0
    with transaction.atomic():
        for model in models_to_clear:
            deleted_count, _ = model.objects.all().delete()
            total_deleted += deleted_count

    messages.success(
        request,
        f'All transactional data cleared successfully ({total_deleted} records removed). Master and setup data preserved.'
    )
    return redirect('fleet_app:hub_admin_master')
