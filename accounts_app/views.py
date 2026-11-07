import hmac
from decimal import InvalidOperation
import traceback
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from audit_app.common import log_activity
from fleet_app.common import *
from fleet_app.reports import *
from .models import *
from .forms import  *
from django.forms import modelformset_factory
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.contrib import messages
from django.forms import inlineformset_factory, formset_factory
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
import json
from item_master.models import *
from fleet_app.models import *
from django.db import connection
from django.db.models import Sum, Q, Count
from accounts_app.common import *
from django.views.decorators.http import require_http_methods
from asset_app.models import AssetMaster
from collections import defaultdict
from datetime import datetime
from django.utils import timezone
from django.utils.dateparse import parse_date

CLEAR_DATA_PASSWORD = "Pass@123"

#MENU ID 

#TRANSACTIONS

TIMESHEET_MENU_ID = 1
SIMPLE_QUOTATION_MENU_ID = 2
REPAIR_MENU_ID = 3 
DELIVERY_CONTRACT_MENU_ID = 4
OFFHIRE_MENU_ID = 5
INVOICE_MENU_ID = 6
FLEET_HIRE_MENU_ID = 7
REPLACEMENT_MENU_ID = 8
RETURN_SPAREPARTS_MENU_ID = 9
SERVICE_DEPARTMENT_MENU_ID = 10

OPENING_VOUCHER_MENU_ID = 11
RECEIPT_MENU_ID = 12
EXPENSE_MENU_ID = 13
PAYMENT_MENU_ID = 14 
JOURNAL_MENU_ID = 15
CONTRA_MENU_ID =16
CHEQUE_CLEARANCE_MENU_ID = 17
LOCAL_PAYMENT_MENU_ID = 18

RECEIPT_BILL_CLEARANCE_MENU_ID = 19
PAYMENT_BILL_CLEARANCE_MENU_ID = 20
DEBITNOTE_MENU_ID = 21
CREDITNOTE_MENU_ID = 22


#REPORTS PAGE

LEDGERREPORT_MENU_ID = 23
LEDGERPOSTING_MENU_ID = 24
TRIALBALANCE_MENU_ID = 25
PROFITLOSS_MENU_ID = 26
BALANCESHEET_MENU_ID = 27
CLIENTOUTSTANDING_MENU_ID = 28
SUPPLIEROUTSTANDING_MENU_ID = 29
BILLBYBILL_MENU_ID = 30
OPENINGBILLS_MENU_ID = 31
AGING_MENU_ID = 32

ASSETREPORT_MENU_ID = 33
ASSETTRACK_MENU_ID = 34
REPAIR_MENU_ID = 35
HIREREPORT_MENU_ID = 36
INVOICEREPORT_MENU_ID = 37
ASSETSTOCK_MENU_ID = 38
ASSETMOVEMENT_MENU_ID = 39
EQUIPMENT_MENU_ID = 40
SCRAP_MENU_ID = 41

PURCHASEREPORT_MENU_ID = 42
STOCKREPORT_MENU_ID = 43
CURRENTSTOCK_MENU_ID = 44


###### MENU ID CONFIGURATION END ##########














PURCHASE_VOUCHER_ID = 13
SALES_VOUCHER_ID = 14
PURCHASE_RETURN_VOUCHER_ID = 18
SALES_RETURN_VOUCHER_ID = 19

VOUCHER_MODEL_MAP = {
    'Payment Bill Clearance': PaymentBillMaster,
    'Receipt Bill Clearance': ReceiptBillMaster,
    'Payment': PaymentMaster,
    'Receipt': ReceiptMaster,
    'Contra': ContraMaster,
    'Journal': JournalMaster,
    'Credit Note': CreditNoteMaster,
    'Debit Note': DebitNoteMaster,
    'Expense Voucher': ExpenseMaster,

    #'Asset Purchase': AssetPurchase,
    #'Asset Opening': AssetOpeningMaster,


    'Invoice': Invoice,
    'Hire': FleetHire,
    #'Repair': RepairMaster,
     

    'Purchase': PurchaseMaster,
    'Sales': SalesMaster,
    'Purchase Return': PurchaseReturnMaster,
    'Sales Return': SalesReturnMaster,
    'Opening Stock': OpeningStockMaster,
    
}

VOUCHER_EDIT_URL_MAP = {
    'Payment Bill Clearance': 'accounts_app:view_paymentbill',
    'Receipt Bill Clearance': 'accounts_app:view_receiptbill',
    'Payment': 'accounts_app:payment_edit',
    'Receipt': 'accounts_app:edit_receipt',
    'Contra': 'accounts_app:contra_edit',
    'Journal': 'accounts_app:journal_edit',
    'Credit Note': 'accounts_app:edit_creditnote',
    'Debit Note': 'accounts_app:edit_debitnote',
    'Expense Voucher': 'accounts_app:edit_expense',

    'Asset Purchase': 'asset_app:asset_purchase_edit',
    'Asset Opening': 'asset_app:asset_opening_edit',

    'Invoice': 'fleet_app:edit_invoice',
    'Hire': 'fleet_app:fleet_hire_edit',
    'Repair': 'fleet_app:repair_edit',
     

    'Purchase': 'item_master:purchase_voucher_edit',
    'Sales': 'item_master:sales_voucher_edit',
    'Purchase Return': 'item_master:purchase_return_voucher_edit',
    'Sales Return': 'item_master:salesreturn_voucher_edit',
    'Opening Stock': 'item_master:opening_stock_edit',
    
}

# For 'master' source: remark comes straight off the master row (pk = VoucherNo).
# For 'detail' source: remark comes off the detail table, matched by its FK to the master pk.
#   -> You MUST verify 'fk' matches the actual FK field name on that detail model in your models.py
#      (e.g. if PaymentDetails has `payment = models.ForeignKey(PaymentMaster, ...)`, fk='payment_id').
REMARK_CONFIG = {
    'Payment Bill Clearance': {'source': 'master', 'field': 'Remark'},
    'Receipt Bill Clearance':  {'source': 'master', 'field': 'Remark'},
    'Payment':                {'source': 'detail', 'model': PaymentDetails,        'fk': 'Payment',           'field': 'Desc'},
    'Receipt':                {'source': 'detail', 'model': ReceiptDetails,        'fk': 'Receipt',           'field': 'Desc'},
    'Contra':                 None,
    'Journal':                {'source': 'detail', 'model': JournalDetail,         'fk': 'journal',           'field': 'narration'},
    'Credit Note':            {'source': 'master', 'field': 'remark'},
    'Debit Note':             {'source': 'master', 'field': 'remark'},
    'Expense Voucher':        {'source': 'master', 'field': 'narration'},

    #'Asset Purchase':         {'source': 'detail', 'model': AssetPurchaseDetails,  'fk': 'purchase',          'field': 'description'},
    #'Asset Opening':          {'source': 'detail', 'model': AssetOpeningDetail,    'fk': 'asset_opening',     'field': 'description'},

    #'Invoice':                {'source': 'detail', 'model': InvoiceDetails,        'fk': 'invoice',           'field': 'description'},
    'Hire':                   None,
    'Repair':                 {'source': 'master', 'field': 'remark'},

    'Purchase':               {'source': 'master', 'field': 'remarks'},
    'Sales':                  {'source': 'master', 'field': 'remarks'},
    'Purchase Return':        {'source': 'master', 'field': 'remarks'},
    'Sales Return':           {'source': 'master', 'field': 'remarks'},
    'Opening Stock':          {'source': 'master', 'field': 'remarks'},
}
# Create your views here.
@login_required(login_url='accounts_app:admin_login')
def home(request):
    return render(request, 'base.html')

@never_cache
def admin_login(request):
    if request.user.is_authenticated:
        return redirect('fleet_app:fleet_home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:  # ✅ allow all active CustomUsers
                login(request, user)
                
                # ✅ LOGIN LOG
                log_activity(
                    user=user,
                    screen_name="Authentication",
                    action_type="LOGIN",
                    remark=f"User {user.username} logged in"
                )
                
                
                return redirect('fleet_app:fleet_home')
            else:
                return HttpResponse('Your account is disabled. Contact admin.')
        else:
            return render(request, 'login.html', {'error': 'Incorrect username or password.'})

    return render(request, 'login.html')


@login_required(login_url='accounts_app:admin_login')
def logout_view(request):
    
    # ✅ LOGOUT LOG (before logout)
    log_activity(
        user=request.user,
        screen_name="Authentication",
        action_type="LOGOUT",
        remark=f"User {request.user.username} logged out"
    )

    logout(request)
    return redirect('accounts_app:admin_login')

@login_required(login_url='accounts_app:admin_login')
def nature_of_group_list(request):
    nature_of_groups = NatureOfGroup.objects.all()
    return render(request, 'nature_of_group_list.html', {'nature_of_groups': nature_of_groups})

@login_required(login_url='accounts_app:admin_login')
# Group View (Create, Update, Delete, List)
def main_group_view(request):
    form = MainGroupForm()
    if request.method == 'POST':
        if 'save' in request.POST:
            form = MainGroupForm(request.POST)
            if form.is_valid():
                main_group = form.save()
                # Create GroupUnder entry for MainGroup
                GroupUnder.objects.create(
                    under_name=main_group.main_group_name, 
                    main_group=main_group
                )
                return redirect('accounts_app:main_group_view')
        elif 'clear' in request.POST:
            return redirect('accounts_app:main_group_view')

    main_groups = MainGroup.objects.all()
    return render(request, 'main_group.html', {'form': form, 'main_groups': main_groups})


@login_required(login_url='accounts_app:admin_login')
def main_group_edit(request, pk):
    main_group = get_object_or_404(MainGroup, pk=pk)
    form = MainGroupForm(instance=main_group)

    if request.method == 'POST':
        form = MainGroupForm(request.POST, instance=main_group)
        if form.is_valid():
            form.save()

            # After saving the form, reorder all main groups to keep numbers sequential
            reorder_all_main_groups()

            return redirect('accounts_app:main_group_view')

    return render(request, 'main_group.html', {'form': form, 'main_groups': MainGroup.objects.all()})


@login_required(login_url='accounts_app:admin_login')
def main_group_delete(request, pk):
    # Get the group to be deleted
    main_group = get_object_or_404(MainGroup, pk=pk)
    main_group.delete()

    # After deletion, reorder all main groups to keep numbers sequential
    reorder_all_main_groups()

    return redirect('accounts_app:main_group_view')


def reorder_all_main_groups():
    """
    Reorder all main groups so that main group_no values are sequential without gaps.
    """
    main_groups = MainGroup.objects.all().order_by('main_group_no')
    for index, main_group in enumerate(main_groups, start=1):  # Start numbering from 1
        main_group.main_group_no = index
        main_group.save()



@login_required(login_url='accounts_app:admin_login')
# Group View (Create, Update, Delete, List)
def group_view(request):
    form = GroupForm()
    if request.method == 'POST':
        if 'save' in request.POST:
            form = GroupForm(request.POST)
            if form.is_valid():
                group = form.save()
                # Create GroupUnder entry for Group
                GroupUnder.objects.create(
                    under_name=group.group_name, 
                    group=group
                )
                # ✅ Create LOG
                user = request.user
                log_activity(
                    user=user,
                    screen_name="GROUP",
                    action_type="CREATE",
                    remark=f" created group {group.group_name}"
                )
                return redirect('accounts_app:group_view')
        elif 'clear' in request.POST:
            return redirect('accounts_app:group_view')

    groups = Group.objects.all()
    return render(request, 'group.html', {'form': form, 'groups': groups})


@login_required(login_url='accounts_app:admin_login')
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    form = GroupForm(instance=group)

    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()

            # After saving the form, reorder all groups to keep numbers sequential
            reorder_all_groups()

            return redirect('accounts_app:group_view')

    return render(request, 'group.html', {'form': form, 'groups': Group.objects.all()})


@login_required(login_url='accounts_app:admin_login')
def group_delete(request, pk):
    # Get the group to be deleted
    group = get_object_or_404(Group, pk=pk)
    group.delete()

    # After deletion, reorder all groups to keep numbers sequential
    reorder_all_groups()

    return redirect('accounts_app:group_view')


def reorder_all_groups():
    """
    Reorder all groups so that group_no values are sequential without gaps.
    """
    groups = Group.objects.all().order_by('group_no')
    for index, group in enumerate(groups, start=1):  # Start numbering from 1
        group.group_no = index
        group.save()


@login_required(login_url='accounts_app:admin_login')

# Subgroup View
def subgroup_view(request):
    form = SubgroupForm()
    if request.method == 'POST':
        if 'save' in request.POST:
            form = SubgroupForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('accounts_app:subgroup_view')
        elif 'clear' in request.POST:
            return redirect('accounts_app:subgroup_view')

    subgroups = Subgroup.objects.all()

    return render(request, 'subgroup.html', {'form': form, 'subgroups': subgroups})


@login_required(login_url='accounts_app:admin_login')

def subgroup_edit(request, pk):
    subgroup = get_object_or_404(Subgroup, pk=pk)
    form = SubgroupForm(instance=subgroup)

    if request.method == 'POST':
        form = SubgroupForm(request.POST, instance=subgroup)
        if form.is_valid():
            form.save()

            # After saving the form, reorder all subgroups to keep numbers sequential
            reorder_all_subgroups()

            return redirect('accounts_app:subgroup_view')

    return render(request, 'subgroup.html', {'form': form, 'subgroups': Subgroup.objects.all()})


@login_required(login_url='accounts_app:admin_login')
def subgroup_delete(request, pk):
    # Get the subgroup to be deleted
    subgroup = get_object_or_404(Subgroup, pk=pk)
    subgroup.delete()

    # After deletion, reorder all subgroups to keep numbers sequential
    reorder_all_subgroups()

    return redirect('accounts_app:subgroup_view')


def reorder_all_subgroups():
    """
    Reorder all subgroups so that sub_group_no values are sequential without gaps.
    """
    subgroups = Subgroup.objects.all().order_by('sub_group_no')
    for index, subgroup in enumerate(subgroups, start=1):  # Start numbering from 1
        subgroup.sub_group_no = index
        subgroup.save()



@login_required(login_url='accounts_app:admin_login')
def ledger_view(request):
    form = LedgerCreationForm()

    if request.method == 'POST':
        if 'save' in request.POST:
            form = LedgerCreationForm(request.POST)
            if form.is_valid():
                ledger = form.save()

                # ✅ Opening Balance Entry
                handle_opening_balance_ledger_posting(ledger, "create")

                # ✅ CREATE LOG
                log_activity(
                    user=request.user,
                    screen_name="Ledger Master",
                    action_type="CREATE",
                    remark=f"Ledger '{ledger.ledger_name}' created"
                )

                return redirect('accounts_app:ledger_view')

        elif 'clear' in request.POST:
            return redirect('accounts_app:ledger_view')

    selected_group = request.GET.get('group', '')
    ledgers = LedgerCreation.objects.all()
    if selected_group:
        ledgers = ledgers.filter(groups__id=selected_group)
    all_groups = Groups.objects.all().order_by('groupName')
    return render(request, 'ledger.html', {
        'form': form,
        'ledgers': ledgers,
        'all_groups': all_groups,
        'selected_group': selected_group,
    })


@login_required(login_url='accounts_app:admin_login')

def ledger_edit(request, pk):
    ledger = get_object_or_404(LedgerCreation, pk=pk)
    form = LedgerCreationForm(instance=ledger)

    if request.method == 'POST':
        form = LedgerCreationForm(request.POST, instance=ledger)
        if form.is_valid():
            updated_ledger = form.save()

            # ✅ Update Opening Balance Posting
            handle_opening_balance_ledger_posting(ledger, "update")

            # ✅ UPDATE LOG
            log_activity(
                user=request.user,
                screen_name="Ledger Master",
                action_type="UPDATE",
                remark=f"Ledger '{updated_ledger.ledger_name}' updated"
            )

            return redirect('accounts_app:ledger_view')

    return render(request, 'ledger.html', {
        'form': form,
        'ledgers': LedgerCreation.objects.all()
    })

@login_required(login_url='accounts_app:admin_login')
def ledger_delete(request, pk):
    ledger = get_object_or_404(LedgerCreation, pk=pk)

    # Delete opening balance posting first
    handle_opening_balance_ledger_posting(ledger, "delete")

    # Log before delete
    log_activity(
        user=request.user,
        screen_name="Ledger Master",
        action_type="DELETE",
        remark=f"Ledger '{ledger.ledger_name}' deleted"
    )

    ledger.delete()

    return redirect('accounts_app:ledger_view')




def local_payment_view(request, payment_id=None, pk=None):
    
    # Determine if we're editing or creating
    payment_instance = None
    existing_items = []
    existing_cheque = None
    
    if payment_id:
        # EDIT MODE - Get existing payment, items, and cheque
        payment_instance = get_object_or_404(LocalPayment, id=payment_id)
        existing_items = LocalPaymentItems.objects.filter(
            localpayment=payment_instance
        ).order_by('id')
        
        try:
            existing_cheque = LocalPaymentCheque.objects.get(localpayment=payment_instance)
        except LocalPaymentCheque.DoesNotExist:
            existing_cheque = None
        
        print(f"\n📝 Edit mode - Payment Voucher #{payment_instance.voucher_no}")
        print(f"Found {existing_items.count()} existing items")
        if existing_cheque:
            print(f"Found existing cheque: {existing_cheque.cheque_no}")
    
    if request.method == 'POST':
        
        try:  # ✅ WRAP IN TRY-CATCH
            # 🔐 PRIVILEGE CHECK
            action = "can_edit" if payment_id else "can_add"

            if not check_privilege(request.user, LOCAL_PAYMENT_MENU_ID, action):
                is_admin_ok, msg = check_admin_override(request)
                if not is_admin_ok:
                    return JsonResponse({
                        "admin_required": True,
                        "message": msg
                    }, status=403)

            # Pass instance for edit, None for create
            payment_form = LocalPaymentForm(request.POST, instance=payment_instance)
            items_formset = LocalPaymentItemFormSet(
                request.POST, 
                prefix='form',
                instance=payment_instance
            )
            cheque_form = None

            if request.POST.get('payment_mode') == 'cheque':
                cheque_form = LocalPaymentChequeForm(request.POST, instance=existing_cheque)

            print("=== FORM VALIDATION ===")
            print("Payment form valid?", payment_form.is_valid())
            print("Items formset valid?", items_formset.is_valid())
            if cheque_form:
                print("Cheque form valid?", cheque_form.is_valid())

            if payment_form.is_valid() and items_formset.is_valid() and \
               (cheque_form is None or cheque_form.is_valid()):
                try:
                    with transaction.atomic():
                        # Save main payment (without totals yet)
                        payment = payment_form.save(commit=False)

                        taxable_amount = Decimal('0')
                        vat_amount = Decimal('0')

                        # Loop through items to calculate VAT properly
                        for form in items_formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                                amount = Decimal(str(form.cleaned_data.get('amount', 0)))
                                vat_type = form.cleaned_data.get('vat_type')

                                if vat_type == 1:  # No VAT
                                    item_taxable = amount
                                    item_vat = Decimal('0')

                                elif vat_type == 2:  # Inclusive VAT (5%)
                                    item_taxable = amount / Decimal('1.05')
                                    item_vat = amount - item_taxable

                                elif vat_type == 3:  # Exclusive VAT (5%)
                                    item_taxable = amount
                                    item_vat = amount * Decimal('0.05')

                                else:
                                    item_taxable = amount
                                    item_vat = Decimal('0')

                                taxable_amount += item_taxable
                                vat_amount += item_vat

                        # Set totals on payment
                        payment.taxable_amount = taxable_amount
                        payment.VAT_amount = vat_amount
                        payment.net_amount = taxable_amount + vat_amount
                        payment.save()

                        print(f"✅ Saved payment: {payment.voucher_no} (ID: {payment.id})")

                        # Save items with recalculated vat_amount
                        items_formset.instance = payment
                        saved_items = items_formset.save(commit=False)
                        
                        for item in saved_items:
                            item.localpayment = payment
                            
                            amount = Decimal(str(item.amount))
                            if item.vat_type == 1:
                                item.vat_amount = Decimal('0')
                            elif item.vat_type == 2:
                                base = amount / Decimal('1.05')
                                item.vat_amount = amount - base
                            elif item.vat_type == 3:
                                item.vat_amount = amount * Decimal('0.05')
                            
                            item.save()
                        
                        # Handle deletions
                        for obj in items_formset.deleted_objects:
                            obj.delete()
                        
                        print(f"✅ Saved {len(saved_items)} payment items")
                        # 🔄 If edit mode, delete existing ledger postings
                        if payment_id:
                            LedgerPosting.objects.filter(
                                VoucherType=payment.voucherType,
                                VoucherNo=payment.id
                            ).delete()
                            print("🗑️ Deleted old ledger postings for Local Payment")

                        # ✅ Create ledger postings
                        create_ledger_postings_for_local_payment(payment)
                        print("✅ Ledger postings created for Local Payment")

                        # Save or update cheque details if needed
                        if cheque_form and payment.payment_mode == 'cheque':
                            cheque = cheque_form.save(commit=False)
                            cheque.localpayment = payment
                            cheque.save()
                            print(f"✅ Saved cheque: {cheque.cheque_no}")
                        elif payment_id and payment.payment_mode != 'cheque' and existing_cheque:
                            # Delete cheque if payment mode changed from cheque to something else
                            existing_cheque.delete()
                            print("🗑️ Deleted cheque (payment mode changed)")
                            
                    # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
                    log_activity(
                    user=request.user,
                    screen_name="Local Payment",
                    action_type="UPDATE" if payment_id else "CREATE",
                    remark=(
                        # The :.3f ensures only 3 decimal places are converted to the string
                        f"Local Payment {payment.voucher_no} updated "
                        f"with net amount {payment.net_amount:.3f}" 
                        if payment_id else
                        f"Local Payment {payment.voucher_no} created "
                        f"with net amount {payment.net_amount:.3f}"
                    )
                )    

                    # ✅ RETURN JSON RESPONSE
                    return JsonResponse({
                        "success": True,
                        "message": (
                            f"Local Payment #{payment.voucher_no} updated successfully."
                            if payment_id else
                            "Local Payment created successfully."
                        )
                    })

                except Exception as e:
                    print(f"❌ Error saving payment: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving payment: {str(e)}"
                    }, status=400)
            
            # Form validation failed
            errors = {}
            if payment_form.errors:
                print("❌ Payment form errors:", payment_form.errors)
                errors['payment_form'] = payment_form.errors
            if items_formset.errors:
                print("❌ Items form errors:", items_formset.errors)
                errors['items_formset'] = items_formset.errors
            if cheque_form and cheque_form.errors:
                print("❌ Cheque form errors:", cheque_form.errors)
                errors['cheque_form'] = cheque_form.errors
            
            return JsonResponse({
                "success": False,
                "message": "Please correct the errors",
                "errors": errors
            }, status=400)

        except Exception as e:  # ✅ CATCH UNEXPECTED ERRORS
            print("=== UNEXPECTED ERROR ===")
            print(str(e))
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)
    
    else:
        # GET request - initialize forms
        payment_form = LocalPaymentForm(instance=payment_instance)
        
        if payment_id:
            # Edit mode - load existing items
            items_formset = LocalPaymentItemFormSet(
                queryset=existing_items,
                prefix='form',
                instance=payment_instance
            )
        else:
            # Create mode - empty formset
            items_formset = LocalPaymentItemFormSet(
                queryset=LocalPaymentItems.objects.none(), 
                prefix='form'
            )
        
        cheque_form = LocalPaymentChequeForm(instance=existing_cheque)

    context = {
        'payment_form': payment_form,
        'items_formset': items_formset,
        'cheque_form': cheque_form,
        'payment_instance': payment_instance,
        'existing_items': existing_items,
        'existing_cheque': existing_cheque,
        'is_edit_mode': payment_id is not None,
    }
    return render(request, 'local_payment_form.html', context)
    
def local_payment_list(request):
    """Display a list of LocalPayment entries as vouchers."""
    local_payments = LocalPayment.objects.all()
    context = {
        'local_payments': local_payments,
    }
    return render(request, 'local_payment_list.html', context)

@require_http_methods(["POST"])
def delete_local_payment(request, id):
    """Delete a specific LocalPayment entry."""
    
    # 🔐 CHECK DELETE PRIVILEGE
    if not check_privilege(request.user, LOCAL_PAYMENT_MENU_ID, "can_delete"):
        is_admin_ok, msg = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg
            }, status=403)
    
    try:
        with transaction.atomic():
            payment = get_object_or_404(LocalPayment, id=id)
            voucher_no = payment.voucher_no
            net_amount = payment.net_amount

            payment.delete()  # ❗ real delete

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Local Payment Entry",
                action_type="DELETE",
                remark=f"Local Payment {voucher_no} deleted "
                       f"with net amount {net_amount}"
            ))

        
        return JsonResponse({
            'success': True, 
            'message': f'Payment {voucher_no} deleted successfully'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': f'Error deleting payment: {str(e)}'
        }, status=500)

def local_payment_detail(request, pk):
    """Display details of a specific LocalPayment, its items, and cheque details if available."""
    local_payment = get_object_or_404(LocalPayment, pk=pk)
    local_payment_items = LocalPaymentItems.objects.filter(localpayment=local_payment)
    local_payment_cheque = LocalPaymentCheque.objects.filter(localpayment=local_payment).first()  # Get first cheque if exists

    context = {
        'local_payment': local_payment,
        'local_payment_items': local_payment_items,
        'local_payment_cheque': local_payment_cheque,  # Include cheque details in context
    }
    return render(request, 'local_payment_detail.html', context)




from django.views.decorators.http import require_POST

@require_POST
def create_ledger(request):
    ledger_form = LedgerCreationForm(request.POST)
    
    if ledger_form.is_valid():
        try:
            ledger = ledger_form.save()
            return JsonResponse({
                'success': True,
                'ledger_id': ledger.id,
                'ledger_name': ledger.ledger_name
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    else:
        return JsonResponse({
            'success': False,
            'errors': [error for field_errors in ledger_form.errors.values() for error in field_errors]
        })


def fetch_outstanding_reports(request):
    ledger_id = request.GET.get('ledger_id')
    
    try:
        # Get the Vendor linked to the selected Ledger
        ledger = LedgerCreation.objects.get(id=ledger_id)
        vendor = Vendor.objects.get(vendor_name=ledger.ledger_name)  # Adjust based on your linking function
        
        # Fetch Outstanding Reports for the Vendor
        outstanding_reports = OutstandingReport.objects.filter(
            vendor=vendor, 
            transaction_type='Purchase'
        ).values('vendor__name', 'bill_no', 'credit_amount', 'balance_amount')
        
        return JsonResponse({'status': 'success', 'reports': list(outstanding_reports)})
    
    except (LedgerCreation.DoesNotExist, Vendor.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'Ledger or Vendor not found.'})




def payment_list(request):
    """Display a list of Payment entries as vouchers."""
    payments = Payment.objects.all()
    context = {
        'payments': payments,
    }
    return render(request, 'payment_list.html', context)



def group_management(request, group_id=None, delete_id=None):

    # DELETE
    if delete_id:
        group_to_delete = get_object_or_404(Groups, id=delete_id)

        if not group_to_delete.isDefault:
            log_activity(
                user=request.user,
                screen_name="Group Management",
                action_type="DELETE",
                remark=f"Group '{group_to_delete.groupName}' deleted"
            )
            group_to_delete.delete()

        return redirect('accounts_app:group_management')

    # EDIT
    if group_id:
        group_instance = get_object_or_404(Groups, id=group_id)
        if group_instance.isDefault:
            return redirect('accounts_app:group_management')
    else:
        group_instance = None

    form = GroupsForm(request.POST or None, instance=group_instance)

    if request.method == 'POST' and form.is_valid():

        if group_instance and group_instance.isDefault:
            return redirect('accounts_app:group_management')

        group = form.save()

        if group_instance is None:
            log_activity(
                user=request.user,
                screen_name="Group Management",
                action_type="CREATE",
                remark=f"Group '{group.groupName}' created"
            )
        else:
            log_activity(
                user=request.user,
                screen_name="Group Management",
                action_type="UPDATE",
                remark=f"Group '{group.groupName}' updated"
            )

        return redirect('accounts_app:group_management')

    groups = Groups.objects.all()

    return render(request, 'manage_groups.html', {
        'form': form,
        'groups': groups,
        'edit_mode': bool(group_instance),
        'editing_id': group_instance.id if group_instance else None,
    })
    
def manage_customers(request, pk=None):
    """Add, Edit, and List Customers in one page"""

    if pk:
        customer = get_object_or_404(LedgerCreation, pk=pk, groups_id=29, types='DR')
        form = CustomerForm(instance=customer)
        edit_mode = True
        title = "Edit Customer"
    else:
        customer = None
        form = CustomerForm()
        edit_mode = False
        title = "Add New Customer"

    if request.method == 'POST':

        # DELETE
        if 'delete_id' in request.POST:
            delete_id = request.POST.get('delete_id')
            del_customer = get_object_or_404(
                LedgerCreation,
                pk=delete_id,
                groups_id=29,
                types='DR'
            )

            log_activity(
                user=request.user,
                screen_name="Client Master",
                action_type="DELETE",
                remark=f"Client '{del_customer.ledger_name}' deleted"
            )

            del_customer.delete()
            messages.success(request, "Client deleted successfully!")
            return redirect('accounts_app:manage_customers')

        # CREATE / UPDATE
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            saved_customer = form.save()

            if edit_mode:
                log_activity(
                    user=request.user,
                    screen_name="Client Master",
                    action_type="UPDATE",
                    remark=f"Client '{saved_customer.ledger_name}' updated"
                )
                messages.success(request, "Client updated successfully!")
            else:
                log_activity(
                    user=request.user,
                    screen_name="Client Master",
                    action_type="CREATE",
                    remark=f"Client '{saved_customer.ledger_name}' created"
                )
                messages.success(request, "Client added successfully!")

            return redirect('accounts_app:manage_customers')

    customers = LedgerCreation.objects.filter(
        groups_id=29,
        types='DR'
    ).order_by('ledger_name')

    return render(request, 'create_customer.html', {
        'form': form,
        'edit_mode': edit_mode,
        'title': title,
        'customers': customers,
    })
    
def manage_vendors(request, pk=None):
    """Add, Edit, and List Vendors in one page"""

    if pk:
        vendor = get_object_or_404(LedgerCreation, pk=pk, groups_id=28, types='CR')
        form = VendorForm(instance=vendor)
        edit_mode = True
        title = "Edit Vendor"
    else:
        vendor = None
        form = VendorForm()
        edit_mode = False
        title = "Add New Vendor"

    if request.method == 'POST':

        # DELETE
        if 'delete_id' in request.POST:
            delete_id = request.POST.get('delete_id')
            del_vendor = get_object_or_404(
                LedgerCreation,
                pk=delete_id,
                groups_id=28,
                types='CR'
            )

            log_activity(
                user=request.user,
                screen_name="Supplier Master",
                action_type="DELETE",
                remark=f"Supplier '{del_vendor.ledger_name}' deleted"
            )

            del_vendor.delete()
            messages.success(request, "Supplier deleted successfully!")
            return redirect('accounts_app:manage_vendors')

        # CREATE / UPDATE
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            saved_vendor = form.save()

            if edit_mode:
                log_activity(
                    user=request.user,
                    screen_name="Supplier Master",
                    action_type="UPDATE",
                    remark=f"Supplier '{saved_vendor.ledger_name}' updated"
                )
                messages.success(request, "Supplier updated successfully!")
            else:
                log_activity(
                    user=request.user,
                    screen_name="Supplier Master",
                    action_type="CREATE",
                    remark=f"Supplier '{saved_vendor.ledger_name}' created"
                )
                messages.success(request, "Supplier added successfully!")

            return redirect('accounts_app:manage_vendors')

    vendors = LedgerCreation.objects.filter(
        groups_id=28,
        types='CR'
    ).order_by('ledger_name')

    return render(request, 'create_vendor.html', {
        'form': form,
        'edit_mode': edit_mode,
        'title': title,
        'vendors': vendors,
    })



@require_POST
def add_customer_ajax(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = CustomerForm(request.POST)
        if form.is_valid():
            try:
                customer = form.save()
                return JsonResponse({
                    'success': True,
                    'customer_id': customer.id,
                    'customer_name': customer.ledger_name,
                    'message': 'Customer created successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        else:
            # Return form errors
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
            return JsonResponse({
                'success': False,
                'error': 'Form validation failed',
                'errors': errors
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })
    
@require_POST
def add_vendor_ajax(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = VendorForm(request.POST)
        if form.is_valid():
            try:
                vendor = form.save()
                return JsonResponse({
                    'success': True,
                    'vendor_id': vendor.id,
                    'vendor_name': vendor.ledger_name,
                    'message': 'Vendor created successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        else:
            # Return form errors
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list
            return JsonResponse({
                'success': False,
                'error': 'Form validation failed',
                'errors': errors
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })    
    
    
def role_management(request, edit_id=None):
    roles = UserRole.objects.all().order_by('id')
    role = get_object_or_404(UserRole, pk=edit_id) if edit_id else None

    if request.method == 'POST':

        # DELETE
        if 'delete_id' in request.POST:
            delete_role = get_object_or_404(UserRole, pk=request.POST['delete_id'])

            log_activity(
                user=request.user,
                screen_name="User Role Management",
                action_type="DELETE",
                remark=f"User Role '{delete_role.name}' deleted"
            )

            delete_role.delete()
            return redirect('accounts_app:role_management')

        # CREATE / UPDATE
        form = UserRoleForm(request.POST, instance=role)
        if form.is_valid():
            saved_role = form.save()

            if role is None:
                log_activity(
                    user=request.user,
                    screen_name="User Role Management",
                    action_type="CREATE",
                    remark=f"User Role '{saved_role.name}' created"
                )
            else:
                log_activity(
                    user=request.user,
                    screen_name="User Role Management",
                    action_type="UPDATE",
                    remark=f"User Role '{saved_role.name}' updated"
                )

            return redirect('accounts_app:role_management')
    else:
        form = UserRoleForm(instance=role)

    return render(request, 'role_management.html', {
        'roles': roles,
        'form': form,
        'edit_role': role
    })
    
    
def user_management(request, edit_id=None):
    users = CustomUser.objects.all().order_by('id')
    user_instance = get_object_or_404(CustomUser, pk=edit_id) if edit_id else None

    if request.method == 'POST':

        # DELETE
        if 'delete_id' in request.POST:
            delete_user = get_object_or_404(CustomUser, pk=request.POST['delete_id'])

            log_activity(
                user=request.user,
                screen_name="User Management",
                action_type="DELETE",
                remark=f"User '{delete_user.username}' deleted"
            )

            delete_user.delete()
            return redirect('accounts_app:user_management')

        # CREATE / UPDATE
        form = CustomUserForm(request.POST, instance=user_instance)
        if form.is_valid():
            saved_user = form.save()

            if user_instance is None:
                log_activity(
                    user=request.user,
                    screen_name="User Management",
                    action_type="CREATE",
                    remark=f"User '{saved_user.username}' created"
                )
            else:
                log_activity(
                    user=request.user,
                    screen_name="User Management",
                    action_type="UPDATE",
                    remark=f"User '{saved_user.username}' updated"
                )

            return redirect('accounts_app:user_management')

    else:
        form = CustomUserForm(instance=user_instance)

    return render(request, 'user_management.html', {
        'users': users,
        'form': form,
        'edit_user': user_instance
    })
    
def menu_list_create(request):
    menus = Menu.objects.all().order_by('group', 'name')

    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            menu = form.save()
            messages.success(request, "Menu added successfully!")
            # ✅ Create LOG
            user = request.user
            log_activity(
                user=user,
                screen_name="MENU",
                action_type="CREATE",
                remark=f" created menu {menu.name}"
            )
            return redirect('accounts_app:menu_list_create')
    else:
        form = MenuForm()

    return render(request, 'menu_create.html', {
        'menus': menus,
        'form': form
    })


def menu_edit(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu updated successfully!")
            # ✅ Create LOG
            user = request.user
            log_activity(
                user=user,
                screen_name="MENU",
                action_type="UPDATE",
                remark=f" updated menu {menu.name}"
            )
            return redirect('accounts_app:menu_list_create')
    else:
        form = MenuForm(instance=menu)

    return render(request, 'menu_edit_form.html', {'form': form, 'menu': menu})


def menu_delete(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    menu.delete()
    messages.success(request, "Menu deleted successfully!")
    # ✅ Create LOG
    user = request.user
    log_activity(
        user=user,
        screen_name="MENU",
        action_type="DELETE",
        remark=f" deleted menu {menu.name}"
    )
    return redirect('accounts_app:menu_list_create')    

@transaction.atomic
def manage_privileges(request):
    roles = UserRole.objects.all()
    menus = list(Menu.objects.all())  # make it mutable for attaching attributes
    selected_role_id = request.GET.get('role')

    # Prepare privilege lookup
    privileges_lookup = {}
    if selected_role_id:
        existing_privileges = UserPrivilege.objects.filter(user_role_id=selected_role_id)
        privileges_lookup = {p.menu_id: p for p in existing_privileges}

        # Attach privilege object to each menu
        for menu in menus:
            menu.priv = privileges_lookup.get(menu.id)

    if request.method == "POST":
        selected_role_id = request.POST.get("role")
        if not selected_role_id:
            messages.error(request, "Please select a role.")
            return redirect('accounts_app:manage_privileges')

        role = UserRole.objects.get(id=selected_role_id)
        UserPrivilege.objects.filter(user_role=role).delete()

        for menu in menus:
            UserPrivilege.objects.create(
                user_role=role,
                menu=menu,
                can_add=request.POST.get(f"add_{menu.id}") == "on",
                can_edit=request.POST.get(f"edit_{menu.id}") == "on",
                can_delete=request.POST.get(f"delete_{menu.id}") == "on",
                can_read=request.POST.get(f"read_{menu.id}") == "on",
                can_cancel=request.POST.get(f"cancel_{menu.id}") == "on",
                can_email=request.POST.get(f"email_{menu.id}") == "on",
                can_print=request.POST.get(f"print_{menu.id}") == "on",
                can_export=request.POST.get(f"export_{menu.id}") == "on",
                can_sms=request.POST.get(f"sms_{menu.id}") == "on",
            )

        messages.success(request, f"Privileges updated for role '{role.name}'")
        return redirect(f"{request.path}?role={selected_role_id}")

    return render(request, "manage_privileges.html", {
        "roles": roles,
        "menus": menus,
        "selected_role_id": int(selected_role_id) if selected_role_id else None
    })

def truncate_table(tables):
    if isinstance(tables, str):
        tables = [tables]
    table_list = ", ".join(f'"{t}"' for t in dict.fromkeys(tables))  # also drops your duplicate entries
    with connection.cursor() as cursor:
        cursor.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;")

def _password_ok(request):
    entered = request.POST.get("password", "")
    return hmac.compare_digest(entered, CLEAR_DATA_PASSWORD)


TRANSACTION_TABLES = [
    "fleet_app_timesheet",
                "fleet_app_timesheetdetail",
                "fleet_app_simplequotation",
                "fleet_app_simplequotationdetails",
                "fleet_app_repairandmaintenance",
                "fleet_app_repairandmaintenanceitem",
                "fleet_app_fleetcontract",
                "fleet_app_fleethire",
                "fleet_app_fleethiredetails",
                "fleet_app_invoice",
                "fleet_app_invoicedetails",
                "accounts_app_ledgerposting",
                "accounts_app_paymentmaster",
                "accounts_app_paymentdetails",
                "accounts_app_receiptmaster",
                "accounts_app_receiptdetails",
                "accounts_app_paymentbillmaster",
                "accounts_app_paymentbilldetails",
                "accounts_app_receiptbillmaster",
                "accounts_app_receiptbilldetails",
                "accounts_app_localpayment",
                "accounts_app_localpaymentitems",
                "accounts_app_localpaymentcheque",
                "accounts_app_billwiseopening",
                "fleet_app_vehicleprofitloss",
                "audit_app_activitylog",
                "fleet_app_deliverycontract",
                "fleet_app_deliverycontractdetails",
                "fleet_app_offhire",
                "fleet_app_offhiredetails",
                "fleet_app_deliverycontract",
                "fleet_app_deliverycontractdetails",
                "fleet_app_repairmaster",
                "fleet_app_spareparts",
                "fleet_app_labourcharge",
                "fleet_app_pomaster",
                "fleet_app_podetails",
                "item_master_purchasemaster",
                "item_master_purchasedetail",
                "item_master_salesmaster",
                "item_master_salesdetail",
                "item_master_purchasereturnmaster",
                "item_master_purchasereturndetail",
                "item_master_salesreturnmaster",
                "item_master_salesreturndetail",
                "item_master_stock",
                "asset_app_assetmaster",
                "asset_app_assetpurchase",
                "asset_app_assetpurchasedetails",
                "accounts_app_journalmaster",
                "accounts_app_journaldetail",
                "accounts_app_contramaster",
                "accounts_app_debitnotemaster",
                "accounts_app_debitnotedetail",
                "accounts_app_creditnotemaster",
                "accounts_app_creditnotedetail",
                "asset_app_assetgrvmaster",
                "asset_app_assetgrvdetails",
                "asset_app_assetstock",
                "item_master_itemgrvmaster",
                "item_master_itemgrvdetail",
                "asset_app_assetopeningmaster",
                "asset_app_assetopeningdetail",
                "fleet_app_replacementmaster",
                "fleet_app_replacementdetail",
                "item_master_openingstockmaster",
                "item_master_openingstockdetail",
                
            ]




@login_required
def clear_transactions(request):
    if request.method == "GET":
        return render(request, "confirm_clear.html", {
            "title": "Clear All Transactions",
            "warning": "This will permanently delete ALL transactions and reset IDs. This cannot be undone.",
        })

    if request.method != "POST":
        messages.error(request, "Invalid request")
        return redirect("fleet_app:fleet_home")

    if not _password_ok(request):
        messages.error(request, "Incorrect password. Nothing was cleared.")
        return redirect("accounts_app:clear_data")

    try:
        with transaction.atomic():
            truncate_table(TRANSACTION_TABLES)
            LedgerCreation.objects.update(opening_balance=0)
            Vehicle.objects.update(status='1')

        log_activity(
            user=request.user,
            screen_name="CLEAR ALL TRANSACTIONS",
            action_type="DELETE",
            remark="cleared all transactions",
        )
        messages.success(request, "All transactions cleared and IDs reset.")
    except Exception as e:
        messages.error(request, f"Error clearing data: {e}")

    return redirect("fleet_app:fleet_home")


@login_required
def clear_billwise_opening(request):
    if request.method == "GET":
        return render(request, "confirm_clear.html", {
            "title": "Clear Billwise Opening",
            "warning": "This will permanently delete all BillWise Opening records and their opening Ledger Postings.",
        })

    if request.method != "POST":
        messages.error(request, "Invalid request")
        return redirect("fleet_app:fleet_home")

    if not _password_ok(request):
        messages.error(request, "Incorrect password. Nothing was cleared.")
        return redirect(request.path)  # back to this same confirm page

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Delete only Opening LedgerPosting entries
                cursor.execute("""
                    DELETE FROM accounts_app_ledgerposting
                    WHERE "IsOpening" = TRUE;
                """)
                ledger_deleted = cursor.rowcount

                # Delete BillWiseOpening records
                cursor.execute("""
                    DELETE FROM accounts_app_billwiseopening;
                """)
                opening_deleted = cursor.rowcount

        log_activity(
            user=request.user,
            screen_name="CLEAR BILLWISE OPENING",
            action_type="DELETE",
            remark=f"deleted {ledger_deleted} opening ledger posting(s) and {opening_deleted} billwise opening record(s)",
        )
        messages.success(
            request,
            f"Deleted {ledger_deleted} Ledger Posting(s) and {opening_deleted} BillWise Opening record(s)."
        )
    except Exception as e:
        messages.error(request, f"Error clearing data: {e}")

    return redirect("fleet_app:fleet_home")



def ledger_posting_report(request):
    ledgers = LedgerCreation.objects.all()
    vouchers = Vouchers.objects.all()

    # --- Filters ---
    ledger_id = request.GET.get('ledger')
    voucher_type_id = request.GET.get('voucher_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    postings = LedgerPosting.objects.filter(IsDeleted=False)

    if ledger_id and ledger_id != "":
        postings = postings.filter(ledger_id=ledger_id)

    if voucher_type_id and voucher_type_id != "":
        postings = postings.filter(VoucherType_id=voucher_type_id)

    if date_from:
        postings = postings.filter(date__gte=date_from)

    if date_to:
        postings = postings.filter(date__lte=date_to)

    # Totals
    total_debit = postings.aggregate(Sum('debit'))['debit__sum'] or 0
    total_credit = postings.aggregate(Sum('credit'))['credit__sum'] or 0
    balance = total_debit - total_credit

    context = {
        'postings': postings.order_by('-date'),
        'ledgers': ledgers,
        'vouchers': vouchers,
        'ledger_id': ledger_id,
        'voucher_type_id': voucher_type_id,
        'date_from': date_from,
        'date_to': date_to,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'balance': balance,
    }

    return render(request, 'ledger_posting_report.html', context)

def create_payment(request):
    form = PaymentForm(request.POST or None)
    bill_clearances = []

    # AJAX step 1: If LedgerDr is selected, fetch related bills
    ledger_id = request.GET.get("ledger_id")
    if ledger_id:
        bill_clearances = BillClearance.objects.filter(Ledger_id=ledger_id, Type__VoucherName="Payment")

    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.save()

        # Process bills — read from hidden fields or JS array
        for key, value in request.POST.items():
            if key.startswith("bill_"):  # e.g. bill_23 = 200
                bill_id = key.split("_")[1]
                amount = float(value)
                if amount > 0:
                    bill = BillClearance.objects.get(id=bill_id)
                    bill.Amount += amount
                    bill.Balance = bill.InvAmount - bill.Amount
                    if bill.Balance <= 0:
                        bill.Balance = 0
                    bill.save()

        messages.success(request, "Payment recorded successfully!")
        return redirect("accounts_app:create_payment")

    return render(request, "payment_form.html", {
        "form": form,
        "bill_clearances": bill_clearances,
    })
    
def update_invoice_cleared_status(invoice_id):
    """
    Update the IsCleared status for a specific invoice
    based on Receipt Bill + Credit Note clearance

    Returns:
        (invoice, was_updated, total_cleared, remaining)
    """

    try:

        from accounts_app.models import (
            ReceiptBillDetails,
            CreditNoteDetail
        )

        from fleet_app.models import Invoice

        invoice = Invoice.objects.get(pk=invoice_id)

        # ✅ Receipt Bill Total

        receipt_total = ReceiptBillDetails.objects.filter(
            VoucherNo=invoice_id,
            voucherType__id=2
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Credit Note Total

        credit_total = CreditNoteDetail.objects.filter(
            VoucherNo=invoice_id,
            voucherType__id=2
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Final Cleared Total

        total_cleared = (
            receipt_total +
            credit_total
        )

        print(f"\n📊 Invoice ID={invoice_id}")
        print(f"Voucher No: {invoice.voucher_no}")

        print(f"Receipt Total: {receipt_total}")
        print(f"Credit Note Total: {credit_total}")

        print(f"Grand Total: {invoice.grand_total}")
        print(f"Total Cleared: {total_cleared}")

        # ✅ Remaining Balance

        remaining = (
            invoice.grand_total -
            total_cleared
        )

        print(f"Remaining: {remaining}")

        # ✅ Cleared Status

        should_be_cleared = (
            remaining <= Decimal('0.01')
        )

        print(f"Should Be Cleared: {should_be_cleared}")
        print(f"Current IsCleared: {invoice.IsCleared}")

        # ✅ Update Status

        if invoice.IsCleared != should_be_cleared:

            invoice.IsCleared = should_be_cleared

            invoice.save()

            print(
                f"✅ IsCleared updated to: "
                f"{invoice.IsCleared}"
            )

            invoice.refresh_from_db()

            print(
                f"✅ Verified From DB: "
                f"{invoice.IsCleared}"
            )

            was_updated = True

        else:

            was_updated = False

        return (
            invoice,
            was_updated,
            total_cleared,
            remaining
        )

    except Exception as e:

        print(
            f"❌ Error in "
            f"update_invoice_cleared_status: {str(e)}"
        )

        import traceback

        traceback.print_exc()

        return (
            None,
            False,
            Decimal('0.000'),
            Decimal('0.000')
        )


def get_customer_invoices_and_openings(request):
    customer_id = request.GET.get('customer_id')
    credit_note_id = request.GET.get('credit_note_id')
    receipt_bill_id = request.GET.get('receipt_bill_id')  # NEW — self-exclusion in edit mode

    if not customer_id:
        return JsonResponse({'invoices': [], 'openings': []})

    # IDs already linked to the document currently being EDITED (credit note
    # or receipt bill). These rows must always be returned — even when their
    # remaining balance looks like zero — because it's this document's own
    # clearance that's making it look zero. This removes the need for the
    # fragile "row was filtered out, reconstruct it in JS" fallback.
    linked_invoice_ids = set()
    linked_opening_ids = set()

    if credit_note_id:
        for d in CreditNoteDetail.objects.filter(CreditMaster_id=credit_note_id):
            if d.voucherType_id == 2:
                linked_invoice_ids.add(d.VoucherNo)
            elif d.voucherType_id == 16:
                linked_opening_ids.add(d.VoucherNo)

    if receipt_bill_id:
        for d in ReceiptBillDetails.objects.filter(BillMaster_id=receipt_bill_id):
            if d.voucherType_id == 2:
                linked_invoice_ids.add(d.VoucherNo)
            elif d.voucherType_id == 16:
                linked_opening_ids.add(d.VoucherNo)

    invoice_data = []
    opening_data = []

    # =========================
    # INVOICES
    # =========================
    invoices = Invoice.objects.filter(
        customer_id=customer_id
    ).filter(
        Q(IsCleared=False) | Q(id__in=linked_invoice_ids)
    )

    for inv in invoices:
        receipt_qs = ReceiptBillDetails.objects.filter(VoucherNo=inv.id, voucherType__id=2)
        if receipt_bill_id:
            receipt_qs = receipt_qs.exclude(BillMaster_id=receipt_bill_id)
        receipt_total = receipt_qs.aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        credit_qs = CreditNoteDetail.objects.filter(VoucherNo=inv.id, voucherType__id=2)
        if credit_note_id:
            credit_qs = credit_qs.exclude(CreditMaster_id=credit_note_id)
        credit_total = credit_qs.aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        total_paid_excl_self = float(receipt_total) + float(credit_total)
        balance = float(inv.grand_total) - total_paid_excl_self

        # This bill's own previously-saved amount against this invoice —
        # used to prefill the input, NOT added to balance anymore since
        # balance above already excludes it.
        own_amount = 0.0
        if receipt_bill_id:
            own_amount = float(
                ReceiptBillDetails.objects.filter(
                    BillMaster_id=receipt_bill_id, VoucherNo=inv.id, voucherType__id=2
                ).aggregate(total=Sum('Amount'))['total'] or 0
            )

        if balance > 0 or inv.id in linked_invoice_ids:
            invoice_data.append({
                'type': 'invoice',
                'invoice_id': inv.id,
                'voucher_no': inv.voucher_no,
                'date': inv.date.strftime('%Y-%m-%d'),
                'customer': inv.customer.ledger_name,
                'grand_total': float(inv.grand_total),
                'amount_cleared': total_paid_excl_self,
                'receivable_balance': max(balance, 0),
                'existing_amount': own_amount,
            })

    # =========================
    # OPENINGS
    # =========================
    try:
        from accounts_app.models import LedgerCreation
        customer_ledger = LedgerCreation.objects.get(pk=customer_id)

        openings = BillWiseOpening.objects.filter(
            ledger=customer_ledger,
            voucherType__id=2
        ).filter(
            Q(IsCleared=False) | Q(id__in=linked_opening_ids)
        )

        for opening in openings:
            # This bill's own previously-saved amount against this opening.
            own_amount = 0.0
            if receipt_bill_id:
                own_amount = float(
                    ReceiptBillDetails.objects.filter(
                        BillMaster_id=receipt_bill_id, VoucherNo=opening.id, voucherType__id=16
                    ).aggregate(total=Sum('Amount'))['total'] or 0
                )

            # opening.InvBalance is the live, incrementally-adjusted balance
            # (via apply_opening_balance_delta) — it is ALREADY net of this
            # bill's own contribution, because that delta was applied the
            # last time this bill was saved. So the balance available for
            # THIS edit session is InvBalance + own_amount (add back only
            # what this bill itself previously claimed). Do NOT also apply
            # the JS-side "+ detail.amount" compensation any more — that
            # was double-counting this exact adjustment.
            #
            # We deliberately do NOT recompute this from InvAmount minus
            # all-time ReceiptBillDetails/CreditNoteDetail sums, because
            # InvBalance may carry a pre-import baked-in paid portion that
            # isn't reconstructable from those tables (see
            # apply_opening_balance_delta's docstring).
            balance = float(opening.InvBalance) + own_amount

            receipt_total_for_display = ReceiptBillDetails.objects.filter(
                VoucherNo=opening.id, voucherType__id=16
            ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')
            credit_total_for_display = CreditNoteDetail.objects.filter(
                VoucherNo=opening.id, voucherType__id=16
            ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')
            amount_cleared_display = (
                float(receipt_total_for_display) + float(credit_total_for_display) - own_amount
            )

            if balance > 0 or opening.id in linked_opening_ids:
                opening_data.append({
                    'type': 'opening',
                    'opening_id': opening.id,
                    'voucher_no': opening.InvNo,
                    'date': opening.InvDate.strftime('%Y-%m-%d'),
                    'customer': opening.ledger.ledger_name,
                    'grand_total': float(opening.InvBalance),
                    'amount_cleared': amount_cleared_display,
                    'receivable_balance': max(balance, 0),
                    'existing_amount': own_amount,
                })

    except Exception as e:
        import traceback
        traceback.print_exc()

    return JsonResponse({'invoices': invoice_data, 'openings': opening_data})



from django.db.models import F


def apply_opening_balance_delta(opening_id, delta):
    """
    Adjust BillWiseOpening.InvBalance by `delta` (the CHANGE in amount
    cleared against this bill on this save — not the total).

    delta > 0  → more was cleared than before → InvBalance decreases
    delta < 0  → some clearance was removed/reduced → InvBalance increases

    This never recomputes from InvAmount, so the pre-import-paid portion
    baked into the originally imported InvBalance is never lost — it's
    only ever adjusted incrementally from whatever it currently holds.
    """

    if delta == 0:
        return

    BillWiseOpening.objects.filter(pk=opening_id).update(
        InvBalance=F('InvBalance') - delta
    )

    opening = BillWiseOpening.objects.get(pk=opening_id)

    if opening.InvBalance < Decimal('0.000'):
        BillWiseOpening.objects.filter(pk=opening_id).update(
            InvBalance=Decimal('0.000')
        )
        opening.refresh_from_db()

    should_be_cleared = opening.InvBalance <= Decimal('0.01')

    if opening.IsCleared != should_be_cleared:
        BillWiseOpening.objects.filter(pk=opening_id).update(
            IsCleared=should_be_cleared
        )    
    
        
def update_billwise_opening_cleared_status(opening_id):
    """
    Update customer opening IsCleared status
    based on Receipt Bill + Credit Note clearances against it.
    InvBalance is never written — it's the frozen baseline,
    same as the payables side treats it for voucherType 17.
    """
    try:
        opening = BillWiseOpening.objects.get(pk=opening_id)

        receipt_total = ReceiptBillDetails.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=16
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        credit_total = CreditNoteDetail.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=16
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        total_cleared = receipt_total + credit_total
        remaining = opening.InvBalance - total_cleared

        should_be_cleared = remaining <= Decimal('0.01')

        if opening.IsCleared != should_be_cleared:
            BillWiseOpening.objects.filter(pk=opening_id).update(
                IsCleared=should_be_cleared
            )

        return opening, should_be_cleared, total_cleared, remaining

    except Exception as e:
        print(f"❌ Error in update_billwise_opening_cleared_status: {e}")
        import traceback
        traceback.print_exc()
        return None, False, Decimal('0.000'), Decimal('0.000')
        
                


def create_ReceiptBillClearance(request, pk=None):
    
    # Check if we're editing an existing receipt bill
    receipt_bill_instance = None
    if pk:
        receipt_bill_instance = get_object_or_404(ReceiptBillMaster, pk=pk)

    if request.method == 'POST':
        
        try:
            print("\n=== RECEIPT BILL SAVE DEBUG START ===")
            print("POST DATA:", request.POST)

            # 🔐 PRIVILEGE CHECK
            action = "can_edit" if pk else "can_add"

            if not check_privilege(request.user, RECEIPT_BILL_CLEARANCE_MENU_ID, action):
                is_admin_ok, msg = check_admin_override(request)
                if not is_admin_ok:
                    return JsonResponse({
                        "admin_required": True,
                        "message": msg
                    }, status=403)

            master_form = ReceiptBillMasterForm(request.POST, instance=receipt_bill_instance)
            formset = ReceiptBillDetailsFormSet(request.POST, prefix='form', instance=receipt_bill_instance)
            
            print("Master form valid:", master_form.is_valid())
            print("Formset valid:", formset.is_valid())

            if not master_form.is_valid():
                print("Master Form Errors:", master_form.errors)
            if not formset.is_valid():
                print("Formset Errors:", formset.errors)
                for i, form in enumerate(formset):
                    if form.errors:
                        print(f"Form {i} errors:", form.errors)

            if master_form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():
                        # ✅ Save master with commit=False first
                        master = master_form.save(commit=False)
                        
                        # Set user tracking if available
                        if request.user.is_authenticated:
                            master.created_by = request.user.id
                            master.updated_by = request.user.id
                        
                        # Calculate total from formset
                        total = Decimal('0.00')
                        for form in formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                amount = form.cleaned_data.get('Amount', Decimal('0.00'))
                                if amount and amount > 0:
                                    total += amount
                        
                        master.TotalAmount = total
                        
                        # ✅ Set Cleared field based on IsPDC
                        if master.IsPDC:
                            master.Cleared = "Not Cleared"
                        else:
                            master.Cleared = "Cleared"
                        
                        master.save()
                        print(f"✅ Master saved: ID={master.id}, TotalAmount={master.TotalAmount}, Cleared={master.Cleared}")

                        # 🔄 If editing, delete existing ledger postings for this receipt bill
                        if pk:
                            deleted_count = LedgerPosting.objects.filter(
                                VoucherType_id=5,  # Receipt Bill Clearance voucher type
                                VoucherNo=master.id
                            ).delete()[0]
                            print(f"🗑️ Deleted {deleted_count} existing ledger posting(s)")

                        # ✅ Only call LedgerPosting if NOT "Not Cleared"
                        if master.Cleared != "Not Cleared":
                            create_ledger_postings_for_receiptbillclr(master)
                            print("✅ Ledger posting created")
                        else:
                            print("⏸️ Ledger posting skipped - Receipt Bill is Not Cleared (PDC)")

                        # 🔄 If editing, snapshot OLD opening totals BEFORE
                        # deleting — needed to compute the delta afterwards.
                        old_invoice_ids = set()
                        old_opening_totals = {}

                        if pk:
                            old_entries = ReceiptBillDetails.objects.filter(
                                BillMaster=master
                            ).values('VoucherNo', 'voucherType_id')

                            for entry in old_entries:
                                if entry['voucherType_id'] == 2:  # Invoice
                                    old_invoice_ids.add(entry['VoucherNo'])

                            old_opening_qs = ReceiptBillDetails.objects.filter(
                                BillMaster=master,
                                voucherType_id=12
                            ).values('VoucherNo').annotate(total=Sum('Amount'))

                            old_opening_totals = {
                                row['VoucherNo']: (row['total'] or Decimal('0'))
                                for row in old_opening_qs
                            }

                            deleted_details_count = ReceiptBillDetails.objects.filter(BillMaster=master).delete()[0]
                            print(f"🗑️ Deleted {deleted_details_count} existing receipt bill detail(s)")

                        # Now save formset with the master instance
                        formset.instance = master
                        details = formset.save(commit=False)

                        invoices_to_check = set()
                        new_opening_totals = {}

                        if pk:
                            invoices_to_check.update(old_invoice_ids)

                        for detail in details:
                            if not detail.Amount or detail.Amount <= 0:
                                print(f"   ⏭️ Skipping detail with zero/empty amount for VoucherNo={detail.VoucherNo}")
                                continue

                            detail.BillMaster = master
                            voucher_type_id = detail.voucherType if isinstance(detail.voucherType, int) else detail.voucherType.id
                            detail.voucherType = Vouchers.objects.get(pk=voucher_type_id)

                            matching_form = next((f for f in formset.forms if f.cleaned_data.get('VoucherNo') == detail.VoucherNo), None)
                            if matching_form:
                                detail.CurrentAmount = matching_form.cleaned_data.get('CurrentAmount', Decimal('0.00'))
                            else:
                                detail.CurrentAmount = Decimal('0.00')

                            if request.user.is_authenticated:
                                detail.created_by = request.user.id
                                detail.updated_by = request.user.id

                            detail.save()
                            print(f"   ➕ Detail saved: VoucherType={detail.voucherType.id}, VoucherNo={detail.VoucherNo}, Amount={detail.Amount}")

                            if detail.voucherType.id == 2:  # Invoice
                                invoices_to_check.add(detail.VoucherNo)
                            elif detail.voucherType.id == 16:  # BillWiseOpening
                                new_opening_totals[detail.VoucherNo] = (
                                    new_opening_totals.get(detail.VoucherNo, Decimal('0')) + detail.Amount
                                )

                        # 🔍 Invoice status update — unchanged, full recompute
                        # is safe here since Invoice.grand_total has no
                        # "pre-import already-paid" concept to lose.
                        print("\n🔍 Starting invoice status update...")
                        for invoice_id in invoices_to_check:
                            try:
                                invoice = Invoice.objects.get(pk=invoice_id)

                                total_paid = sum(
                                    ReceiptBillDetails.objects.filter(
                                        VoucherNo=invoice_id,
                                        voucherType__id=2
                                    ).values_list('Amount', flat=True)
                                ) or Decimal('0.00')

                                remaining = invoice.grand_total - total_paid
                                should_be_cleared = abs(remaining) <= Decimal('0.01')

                                if invoice.IsCleared != should_be_cleared:
                                    Invoice.objects.filter(pk=invoice_id).update(IsCleared=should_be_cleared)

                            except Invoice.DoesNotExist:
                                print(f"  ⚠️ Invoice ID {invoice_id} not found")
                            except Exception as e:
                                print(f"  ❌ Error: {str(e)}")
                                import traceback
                                traceback.print_exc()

                        print("\n✅ Finished processing all invoices")

                        # 🔍 Opening balance update — DELTA-based, no recompute
                        print("\n🔍 Starting BillWiseOpening balance update...")

                        affected_opening_ids = set(old_opening_totals.keys()) | set(new_opening_totals.keys())

                        for opening_id in affected_opening_ids:
                            old_amt = old_opening_totals.get(opening_id, Decimal('0'))
                            new_amt = new_opening_totals.get(opening_id, Decimal('0'))
                            delta = new_amt - old_amt

                            print(f"Opening ID={opening_id}: old={old_amt}, new={new_amt}, delta={delta}")

                            apply_opening_balance_delta(opening_id, delta)

                        print("\n✅ Finished processing all openings\n")
                    
                    # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
                    log_activity(
                        user=request.user,
                        screen_name="Receipt Bill Clearance",
                        action_type="UPDATE" if pk else "CREATE",
                        remark=(
                            f"Receipt Bill Clearance #{master.id} updated "
                            f"with total {master.TotalAmount:.3f}"
                            if pk else
                            f"Receipt Bill Clearance #{master.id} created "
                            f"with total {master.TotalAmount:.3f}"
                        )
                    )
                    
                    # ✅ RETURN JSON RESPONSE
                    return JsonResponse({
                        "success": True,
                        "message": (
                            "Receipt bill updated successfully!"
                            if pk else
                            "Receipt bill saved successfully!"
                        ),
                        "pdf_url": reverse('accounts_app:receiptbill_pdf', args=[master.id]) 
                    })

                except Exception as e:
                    print("❌ Exception during save:", str(e))
                    import traceback
                    traceback.print_exc()
                    
                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving receipt bill: {str(e)}"
                    }, status=400)
            
            # Form validation failed
            return JsonResponse({
                "success": False,
                "message": "Please correct the errors",
                "errors": {
                    "master_form": master_form.errors,
                    "formset": formset.errors
                }
            }, status=400)

        except Exception as e:
            print("=== UNEXPECTED ERROR ===")
            print(str(e))
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)

    else:
        # GET request
        master_form = ReceiptBillMasterForm(instance=receipt_bill_instance)
        formset = ReceiptBillDetailsFormSet(prefix='form', instance=receipt_bill_instance)

    return render(request, 'create_ReceiptBillClearance.html', {
        'master_form': master_form,
        'formset': formset,
        'edit_mode': pk is not None,
        'receipt_bill_instance': receipt_bill_instance,
    })

def receiptbill_pdf(request, pk):
    receiptbill = get_object_or_404(ReceiptBillMaster, pk=pk)
    return create_receiptbill_pdf(receiptbill)

def view_receiptbill(request, pk):

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        RECEIPT_BILL_CLEARANCE_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    instance = get_object_or_404(ReceiptBillMaster, pk=pk)
    details = ReceiptBillDetails.objects.filter(BillMaster=instance).select_related('voucherType')
    return render(request, 'view_receiptbill.html', {
        'receipt_bill_instance': instance,
        'details': details,
    })
    
def list_receiptbill(request):
    """List all receipt bill clearances"""
    
    receipt_bills = ReceiptBillMaster.objects.all().order_by('-Date')
    return render(request, "ReceiptBillClr_list.html", {"receipt_bills": receipt_bills})

@require_http_methods(["POST"])
def receiptbill_delete(request, pk):

    if not check_privilege(request.user, RECEIPT_BILL_CLEARANCE_MENU_ID, "can_delete"):
        is_admin_ok, msg = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg
            }, status=403)

    try:
        with transaction.atomic():

            receipt_bill = get_object_or_404(ReceiptBillMaster, pk=pk)

            bill_no = receipt_bill.id
            total = receipt_bill.TotalAmount

            # 🔹 STEP 1: Capture affected invoices & opening AMOUNTS
            # (not just IDs) BEFORE delete — openings need the exact
            # amount this receipt cleared, to reverse it via delta.
            details = ReceiptBillDetails.objects.filter(BillMaster=receipt_bill)\
                .values('VoucherNo', 'voucherType_id', 'Amount')

            invoice_ids = set()
            opening_amounts = {}

            for d in details:
                if d['voucherType_id'] == 2:          # Invoice
                    invoice_ids.add(d['VoucherNo'])
                elif d['voucherType_id'] == 16:        # BillWiseOpening
                    opening_amounts[d['VoucherNo']] = (
                        opening_amounts.get(d['VoucherNo'], Decimal('0')) + (d['Amount'] or Decimal('0'))
                    )

            # 🔹 STEP 2: Delete Ledger Postings
            delete_ledger_postings_for_receiptbillclr(receipt_bill)

            # 🔹 STEP 3: Delete Receipt Details & Master
            ReceiptBillDetails.objects.filter(BillMaster=receipt_bill).delete()
            receipt_bill.delete()

            # 🔹 STEP 4: Recalculate Invoice IsCleared
            for invoice_id in invoice_ids:
                update_invoice_cleared_status(invoice_id)

            # 🔹 STEP 5: Reverse each opening's InvBalance by the amount
            # THIS receipt had cleared — negative delta increases
            # InvBalance back up, same mechanism used on save/edit.
            for opening_id, amount in opening_amounts.items():
                apply_opening_balance_delta(opening_id, -amount)

            # 🔹 LOG AFTER COMMIT
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Receipt Bill Clearance",
                action_type="DELETE",
                remark=f"Receipt Bill Clearance #{bill_no} deleted with total {total:.3f}"
            ))

        return JsonResponse({
            'success': True,
            'message': f'Receipt Bill #{bill_no} deleted successfully!'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error deleting receipt bill: {str(e)}'
        }, status=500)
        

#Payment Bill Clearance
def update_hire_cleared_status(hire_id):
    """
    Updates IsCleared for FleetHire
    based on Payment Bill + Debit Note
    """

    try:

        hire = FleetHire.objects.get(
            pk=hire_id
        )

        # ✅ Payment Total

        payment_total = PaymentBillDetails.objects.filter(
            VoucherNo=hire_id,
            voucherType__id=1
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Debit Note Total

        debit_total = DebitNoteDetail.objects.filter(
            VoucherNo=hire_id,
            voucherType__id=1
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Final Cleared

        total_cleared = (
            payment_total +
            debit_total
        )

        remaining = (
            hire.grand_total -
            total_cleared
        )

        print(f"\n📊 Hire ID={hire_id}")
        print(f"Voucher No: {hire.voucher_no}")

        print(f"Payment Total: {payment_total}")
        print(f"Debit Note Total: {debit_total}")

        print(f"Grand Total: {hire.grand_total}")
        print(f"Total Cleared: {total_cleared}")
        print(f"Remaining: {remaining}")

        should_be_cleared = (
            remaining <= Decimal('0.01')
        )

        print(f"Should Be Cleared: {should_be_cleared}")
        print(f"Current IsCleared: {hire.IsCleared}")

        if hire.IsCleared != should_be_cleared:

            hire.IsCleared = should_be_cleared

            hire.save(update_fields=['IsCleared'])

            print(
                f"✅ Updated IsCleared = "
                f"{hire.IsCleared}"
            )

            was_updated = True

        else:

            was_updated = False

        return (
            hire,
            was_updated,
            total_cleared,
            remaining
        )

    except Exception as e:

        print(
            f"❌ Error in "
            f"update_hire_cleared_status: {e}"
        )

        import traceback

        traceback.print_exc()

        return (
            None,
            False,
            Decimal('0.000'),
            Decimal('0.000')
        )

def update_billwise_opening_cleared_status_payment(opening_id):
    """
    Update supplier opening IsCleared
    based on Payment Bill + Debit Note
    """

    try:

        opening = BillWiseOpening.objects.get(
            pk=opening_id
        )

        # ✅ Payment Total

        payment_total = PaymentBillDetails.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=17
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Debit Note Total

        debit_total = DebitNoteDetail.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=17
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Final Cleared

        total_cleared = (
            payment_total +
            debit_total
        )

        remaining = (
            opening.InvBalance -
            total_cleared
        )

        print(f"\n📊 Opening ID={opening_id}")
        print(f"Opening No: {opening.InvNo}")

        print(f"Payment Total: {payment_total}")
        print(f"Debit Note Total: {debit_total}")

        print(f"Opening Balance: {opening.InvBalance}")
        print(f"Total Cleared: {total_cleared}")
        print(f"Remaining: {remaining}")

        should_be_cleared = (
            remaining <= Decimal('0.01')
        )

        print(f"Should Be Cleared: {should_be_cleared}")
        print(f"Current IsCleared: {opening.IsCleared}")

        if opening.IsCleared != should_be_cleared:

            BillWiseOpening.objects.filter(
                pk=opening_id
            ).update(
                IsCleared=should_be_cleared
            )

            opening.refresh_from_db()

            print(
                f"✅ Updated IsCleared = "
                f"{opening.IsCleared}"
            )

            was_updated = True

        else:

            was_updated = False

        return (
            opening,
            was_updated,
            total_cleared,
            remaining
        )

    except Exception as e:

        print(
            f"❌ Error in "
            f"update_billwise_opening_cleared_status_payment: "
            f"{e}"
        )

        import traceback

        traceback.print_exc()

        return (
            None,
            False,
            Decimal('0.000'),
            Decimal('0.000')
        )

def update_purchase_cleared_status(purchase_id):
    """
    Updates Purchase IsCleared
    based on Payment Bill + Debit Note
    """

    try:

        purchase = PurchaseMaster.objects.get(
            pk=purchase_id
        )

        # ✅ Payment Total

        payment_total = PaymentBillDetails.objects.filter(
            VoucherNo=purchase_id,
            voucherType__id=13
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Debit Note Total

        debit_total = DebitNoteDetail.objects.filter(
            VoucherNo=purchase_id,
            voucherType__id=13
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Final Cleared

        total_cleared = (
            payment_total +
            debit_total
        )

        remaining = (
            purchase.grand_total_amount -
            total_cleared
        )

        print(f"\n📊 Purchase ID={purchase_id}")
        print(f"Voucher No: {purchase.voucher_no}")

        print(f"Payment Total: {payment_total}")
        print(f"Debit Note Total: {debit_total}")

        print(f"Grand Total: {purchase.grand_total_amount}")
        print(f"Total Cleared: {total_cleared}")
        print(f"Remaining: {remaining}")

        should_be_cleared = (
            remaining <= Decimal('0.01')
        )

        print(f"Should Be Cleared: {should_be_cleared}")
        print(f"Current IsCleared: {purchase.IsCleared}")

        if purchase.IsCleared != should_be_cleared:

            purchase.IsCleared = should_be_cleared

            purchase.save(update_fields=['IsCleared'])

            print(
                f"✅ Updated IsCleared = "
                f"{purchase.IsCleared}"
            )

            was_updated = True

        else:

            was_updated = False

        return (
            purchase,
            was_updated,
            total_cleared,
            remaining
        )

    except Exception as e:

        print(
            f"❌ Error in "
            f"update_purchase_cleared_status: {e}"
        )

        import traceback

        traceback.print_exc()

        return (
            None,
            False,
            Decimal('0.000'),
            Decimal('0.000')
        )

def update_asset_purchase_cleared_status(asset_purchase_id):
    """
    Updates Asset Purchase IsCleared
    based on Payment Bill + Debit Note
    """

    try:

        asset_purchase = AssetPurchase.objects.get(
            pk=asset_purchase_id
        )

        # ✅ Payment Total

        payment_total = PaymentBillDetails.objects.filter(
            VoucherNo=asset_purchase_id,
            voucherType__id=17
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Debit Note Total

        debit_total = DebitNoteDetail.objects.filter(
            VoucherNo=asset_purchase_id,
            voucherType__id=17
        ).aggregate(
            total=Sum('Amount')
        )['total'] or Decimal('0.000')

        # ✅ Final Cleared

        total_cleared = (
            payment_total +
            debit_total
        )

        remaining = (
            asset_purchase.grand_total -
            total_cleared
        )

        print(f"\n📊 Asset Purchase ID={asset_purchase_id}")
        print(f"Voucher No: {asset_purchase.voucher_no}")

        print(f"Payment Total: {payment_total}")
        print(f"Debit Note Total: {debit_total}")

        print(f"Grand Total: {asset_purchase.grand_total}")
        print(f"Total Cleared: {total_cleared}")
        print(f"Remaining: {remaining}")

        should_be_cleared = (
            remaining <= Decimal('0.01')
        )

        print(f"Should Be Cleared: {should_be_cleared}")
        print(f"Current IsCleared: {asset_purchase.IsCleared}")

        if asset_purchase.IsCleared != should_be_cleared:

            asset_purchase.IsCleared = should_be_cleared

            asset_purchase.save(
                update_fields=['IsCleared']
            )

            print(
                f"✅ Updated IsCleared = "
                f"{asset_purchase.IsCleared}"
            )

            was_updated = True

        else:

            was_updated = False

        return (
            asset_purchase,
            was_updated,
            total_cleared,
            remaining
        )

    except Exception as e:

        print(
            f"❌ Error in "
            f"update_asset_purchase_cleared_status: {e}"
        )

        import traceback

        traceback.print_exc()

        return (
            None,
            False,
            Decimal('0.000'),
            Decimal('0.000')
        )

# ================================
# 🔹 CREATE PAYMENT BILL CLEARANCE
# ================================


def create_PaymentBillClearance(request):

    if request.method == 'POST':

        try:
            print("\n=== PAYMENT BILL SAVE DEBUG START ===")
            print("POST DATA:", request.POST)

            # 🔐 PRIVILEGE CHECK
            if not check_privilege(request.user, PAYMENT_BILL_CLEARANCE_MENU_ID, "can_add"):
                is_admin_ok, msg = check_admin_override(request)
                if not is_admin_ok:
                    return JsonResponse({
                        "admin_required": True,
                        "message": msg
                    }, status=403)

            master_form = PaymentBillMasterForm(request.POST)
            formset = PaymentBillDetailsFormSet(request.POST, prefix='form')

            print("Master form valid:", master_form.is_valid())
            print("Formset valid:", formset.is_valid())

            if not master_form.is_valid():
                print("Master Form Errors:", master_form.errors)
            if not formset.is_valid():
                print("Formset Errors:", formset.errors)
                for i, form in enumerate(formset):
                    if form.errors:
                        print(f"Form {i} errors:", form.errors)

            if master_form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():
                        master = master_form.save(commit=False)

                        if request.user.is_authenticated:
                            master.created_by = request.user.id
                            master.updated_by = request.user.id

                        total = Decimal('0.00')
                        for form in formset:
                            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                                amount = form.cleaned_data.get('Amount', Decimal('0.00'))
                                if amount and amount > 0:
                                    total += amount

                        master.TotalAmount = total

                        if master.IsPDC:
                            master.Cleared = "Not Cleared"
                        else:
                            master.Cleared = "Cleared"

                        master.save()
                        print(f"✅ Master saved: ID={master.id}, TotalAmount={master.TotalAmount}, Cleared={master.Cleared}")

                        if master.Cleared != "Not Cleared":
                            create_ledger_postings_for_paymentbillclr(master)
                            print("✅ Ledger posting created")
                        else:
                            print("⏸️ Ledger posting skipped - Payment Bill is Not Cleared (PDC)")

                        formset.instance = master
                        details = formset.save(commit=False)

                        hires_to_check = set()
                        openings_to_check = set()
                        purchases_to_check = set()
                        asset_purchases_to_check = set()

                        for detail in details:
                            if not detail.Amount or detail.Amount <= 0:
                                print(f"⏭️ Skipping detail with zero/empty amount for VoucherNo={detail.VoucherNo}")
                                continue

                            detail.BillMaster = master
                            voucher_type_id = detail.voucherType if isinstance(detail.voucherType, int) else detail.voucherType.id
                            detail.voucherType = Vouchers.objects.get(pk=voucher_type_id)

                            matching_form = next((f for f in formset.forms if f.cleaned_data.get('VoucherNo') == detail.VoucherNo), None)
                            if matching_form:
                                detail.CurrentAmount = matching_form.cleaned_data.get('CurrentAmount', Decimal('0.00'))
                            else:
                                detail.CurrentAmount = Decimal('0.00')

                            if request.user.is_authenticated:
                                detail.created_by = request.user.id
                                detail.updated_by = request.user.id

                            detail.save()
                            print(f"➕ Detail saved: voucherType={detail.voucherType.id}, VoucherNo={detail.VoucherNo}, Amount={detail.Amount}")

                            if detail.voucherType.id == 1:  # Hire
                                hires_to_check.add(detail.VoucherNo)
                            elif detail.voucherType.id == 17:  # BillWiseOpening
                                openings_to_check.add(detail.VoucherNo)
                            elif detail.voucherType.id == 13:  # Purchase
                                purchases_to_check.add(detail.VoucherNo)
                            elif detail.voucherType.id == 17:  # Asset Purchase
                                asset_purchases_to_check.add(detail.VoucherNo)

                        print("\n🔍 Starting hire status update...")
                        for hire_id in hires_to_check:
                            print(f"\n--- Processing Hire ID: {hire_id} ---")
                            try:
                                hire = FleetHire.objects.get(pk=hire_id)
                                print(f"✓ Hire found: {hire.voucher_no}")
                                print(f"  Before update - IsCleared: {hire.IsCleared}")

                                payment_details = PaymentBillDetails.objects.filter(
                                    VoucherNo=hire_id,
                                    voucherType__id=1
                                )
                                total_cleared = payment_details.aggregate(total=Sum('Amount'))['total'] or Decimal('0.00')
                                remaining = hire.grand_total - total_cleared
                                should_be_cleared = abs(remaining) <= Decimal('0.01')

                                if hire.IsCleared != should_be_cleared:
                                    print(f"🔄 Updating IsCleared from {hire.IsCleared} to {should_be_cleared}")
                                    FleetHire.objects.filter(pk=hire_id).update(IsCleared=should_be_cleared)
                                    hire.refresh_from_db()
                                    print(f"✅ After update - IsCleared: {hire.IsCleared}")
                                else:
                                    print("ℹ️ No update needed, already correct value")

                            except FleetHire.DoesNotExist:
                                print(f"⚠️ Hire ID {hire_id} not found")
                            except Exception as e:
                                print(f"❌ Error: {str(e)}")
                                import traceback
                                traceback.print_exc()

                        print("\n✅ Finished processing all hires")

                        print("\n🔍 Starting BillWiseOpening status update...")
                        for opening_id in openings_to_check:
                            print(f"\n--- Processing Opening ID: {opening_id} ---")
                            update_billwise_opening_cleared_status_payment(opening_id)
                        print("\n✅ Finished processing all openings\n")

                        print("\n🔍 Starting Purchase status update...")
                        for purchase_id in purchases_to_check:
                            print(f"\n--- Processing Purchase ID: {purchase_id} ---")
                            update_purchase_cleared_status(purchase_id)
                        print("\n✅ Finished processing all purchases\n")

                        print("\n🔍 Starting Asset Purchase status update...")
                        for asset_purchase_id in asset_purchases_to_check:
                            print(f"\n--- Processing Asset Purchase ID: {asset_purchase_id} ---")
                            update_asset_purchase_cleared_status(asset_purchase_id)
                        print("\n✅ Finished processing all asset purchases\n")

                    print("=== PAYMENT BILL SAVE DEBUG END ===\n")

                    log_activity(
                        user=request.user,
                        screen_name="Payment Bill Clearance",
                        action_type="CREATE",
                        remark=f"Payment Bill Clearance #{master.id} created with total {master.TotalAmount:.3f}"
                    )

                    return JsonResponse({
                        "success": True,
                        "message": "Payment bill saved successfully!",
                        "pdf_url": reverse('accounts_app:paymentbill_pdf', args=[master.id])
                    })

                except Exception as e:
                    print("❌ Exception during save:", str(e))
                    import traceback
                    traceback.print_exc()

                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving payment bill: {str(e)}"
                    }, status=400)

            return JsonResponse({
                "success": False,
                "message": "Please correct the errors",
                "errors": {
                    "master_form": master_form.errors,
                    "formset": formset.errors
                }
            }, status=400)

        except Exception as e:
            print("=== UNEXPECTED ERROR ===")
            print(str(e))
            import traceback
            traceback.print_exc()

            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)

    else:
        master_form = PaymentBillMasterForm()
        formset = PaymentBillDetailsFormSet(prefix='form')

    return render(request, 'create_PaymentBillClearance.html', {
        'master_form': master_form,
        'formset': formset,
    })

def view_PaymentBillClearance(request, pk):

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        PAYMENT_BILL_CLEARANCE_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    payment_bill_instance = get_object_or_404(PaymentBillMaster, pk=pk)

    details = payment_bill_instance.paymentbilldetails_set.all()

    return render(request, 'view_PaymentBillClearance.html', {
        'payment_bill_instance': payment_bill_instance,
        'details': details,
    })

def paymentbill_pdf(request, pk):
    paymentbill = get_object_or_404(PaymentBillMaster, pk=pk)
    return create_paymentbill_pdf(paymentbill)    


def get_supplier_hires_and_openings(request):
    """
    Get FleetHires, BillWiseOpenings, Purchases, and AssetPurchases for a supplier.
    In edit mode (debit_note_id provided):
      - Returns records already linked to this debit note even if IsCleared=True
      - Excludes this debit note's own amounts from total_paid so balance is correct
    """
    supplier_id = request.GET.get('supplier_id')
    debit_note_id = request.GET.get('debit_note_id')  # present only in edit mode

    data = {
        'hires': [],
        'openings': [],
        'purchases': [],
        'asset_purchases': []
    }

    if not supplier_id:
        return JsonResponse(data)

    # ─── Collect IDs already linked to this debit note (edit mode) ────────────
    linked_hire_ids = set()
    linked_opening_ids = set()
    linked_purchase_ids = set()
    linked_asset_ids = set()

    if debit_note_id:
        for d in DebitNoteDetail.objects.filter(
            DebitMaster_id=debit_note_id
        ).select_related('voucherType'):
            vt = d.voucherType.id
            if vt == 1:
                linked_hire_ids.add(d.VoucherNo)
            elif vt == 17:
                linked_opening_ids.add(d.VoucherNo)
            elif vt == 13:
                linked_purchase_ids.add(d.VoucherNo)
            elif vt == 17:
                linked_asset_ids.add(d.VoucherNo)

    # ─── Helper: total paid excluding THIS debit note ──────────────────────────
    def get_total_paid_hire(hire_id):
        payment = PaymentBillDetails.objects.filter(
            VoucherNo=hire_id,
            voucherType__id=1
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        debit_qs = DebitNoteDetail.objects.filter(
            VoucherNo=hire_id,
            voucherType__id=1
        )
        if debit_note_id:
            debit_qs = debit_qs.exclude(DebitMaster_id=debit_note_id)
        debit = debit_qs.aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        return payment + debit

    def get_total_paid_opening(opening_id):
        payment = PaymentBillDetails.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=17
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        debit_qs = DebitNoteDetail.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=17
        )
        if debit_note_id:
            debit_qs = debit_qs.exclude(DebitMaster_id=debit_note_id)
        debit = debit_qs.aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        return payment + debit

    def get_total_paid_purchase(purchase_id):
        payment = PaymentBillDetails.objects.filter(
            VoucherNo=purchase_id,
            voucherType__id=13
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        debit_qs = DebitNoteDetail.objects.filter(
            VoucherNo=purchase_id,
            voucherType__id=13
        )
        if debit_note_id:
            debit_qs = debit_qs.exclude(DebitMaster_id=debit_note_id)
        debit = debit_qs.aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        return payment + debit

    def get_total_paid_asset(asset_id):
        payment = PaymentBillDetails.objects.filter(
            VoucherNo=asset_id,
            voucherType__id=17
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        debit_qs = DebitNoteDetail.objects.filter(
            VoucherNo=asset_id,
            voucherType__id=17
        )
        if debit_note_id:
            debit_qs = debit_qs.exclude(DebitMaster_id=debit_note_id)
        debit = debit_qs.aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

        return payment + debit

    # ─── Hires (VoucherType 1) ─────────────────────────────────────────────────
    hire_qs = FleetHire.objects.filter(
        supplier_id=supplier_id
    ).filter(
        Q(IsCleared=False) | Q(id__in=linked_hire_ids)
    )

    for hire in hire_qs:
        total_paid = get_total_paid_hire(hire.id)
        balance = hire.grand_total - total_paid

        if balance > 0 or hire.id in linked_hire_ids:
            data['hires'].append({
                'type': 'hire',
                'hire_id': hire.id,
                'voucher_no': hire.voucher_no,
                'date': hire.date.strftime('%Y-%m-%d'),
                'supplier': hire.supplier.ledger_name,
                'grand_total': float(hire.grand_total),
                'amount_cleared': float(total_paid),
                'payable_balance': float(max(balance, Decimal('0.000'))),
            })

    # ─── BillWiseOpenings (VoucherType 16,17) ────────────────────────────────────
    try:
        print("=" * 80)
        print("Supplier ID:", supplier_id)

        print(
            "All openings for supplier:",
            list(
                BillWiseOpening.objects.filter(
                    ledger_id=supplier_id
                ).values(
                    "id",
                    "ledger_id",
                    "voucherType_id",
                    "InvNo",
                    "InvBalance",
                    "IsCleared"
                )
            )
        )

        opening_qs = BillWiseOpening.objects.filter(
            ledger_id=supplier_id,
            voucherType__id=17
        ).filter(
            Q(IsCleared=False) | Q(id__in=linked_opening_ids)
        )

        print(
            "Filtered openings:",
            list(
                opening_qs.values(
                    "id",
                    "InvNo",
                    "InvBalance",
                    "IsCleared"
                )
            )
        )

        for opening in opening_qs:
            print("Processing Opening:", opening.id)

            total_paid = get_total_paid_opening(opening.id)
            balance = opening.InvBalance - total_paid

            print(
                "InvBalance:", opening.InvBalance,
                "Total Paid:", total_paid,
                "Balance:", balance
            )

            if balance > 0 or opening.id in linked_opening_ids:
                data['openings'].append({
                    'type': 'opening',
                    'opening_id': opening.id,
                    'voucher_no': opening.InvNo,
                    'date': opening.InvDate.strftime('%Y-%m-%d'),
                    'supplier': opening.ledger.ledger_name,
                    'grand_total': float(opening.InvBalance),
                    'amount_cleared': float(total_paid),
                    'payable_balance': float(max(balance, Decimal('0.000'))),
                })

    except Exception:
        import traceback
        traceback.print_exc()

    # ─── Purchases (VoucherType 13) ────────────────────────────────────────────
    try:
        purchase_qs = PurchaseMaster.objects.filter(
            ledger_id=supplier_id
        ).filter(
            Q(IsCleared=False) | Q(id__in=linked_purchase_ids)
        )

        for purchase in purchase_qs:
            total_paid = get_total_paid_purchase(purchase.id)
            balance = purchase.grand_total_amount - total_paid

            if balance > 0 or purchase.id in linked_purchase_ids:
                data['purchases'].append({
                    'type': 'purchase',
                    'purchase_id': purchase.id,
                    'voucher_no': purchase.voucher_no,
                    'date': purchase.transaction_date.strftime('%Y-%m-%d'),
                    'supplier': purchase.ledger.ledger_name,
                    'grand_total': float(purchase.grand_total_amount),
                    'amount_cleared': float(total_paid),
                    'payable_balance': float(max(balance, Decimal('0.000'))),
                })
    except Exception as e:
        import traceback
        traceback.print_exc()

    # ─── Asset Purchases (VoucherType 17) ─────────────────────────────────────
    try:
        asset_qs = AssetPurchase.objects.filter(
            supplier_id=supplier_id
        ).filter(
            Q(IsCleared=False) | Q(id__in=linked_asset_ids)
        )

        for asset in asset_qs:
            total_paid = get_total_paid_asset(asset.id)
            balance = asset.grand_total - total_paid

            if balance > 0 or asset.id in linked_asset_ids:
                data['asset_purchases'].append({
                    'type': 'asset_purchase',
                    'asset_purchase_id': asset.id,
                    'voucher_no': asset.voucher_no,
                    'date': asset.date.strftime('%Y-%m-%d'),
                    'supplier': asset.supplier.ledger_name,
                    'grand_total': float(asset.grand_total),
                    'amount_cleared': float(total_paid),
                    'payable_balance': float(max(balance, Decimal('0.000'))),
                })
    except Exception as e:
        import traceback
        traceback.print_exc()

    return JsonResponse(data)

# ================================
# 🔹 LIST & DELETE PAYMENT BILL CLEARANCES
def list_paymentbill(request):
    """List all payment bill clearances"""
    
    payment_bills = PaymentBillMaster.objects.all().order_by('-Date')
    return render(request, "PaymentBillClr_list.html", {"payment_bills": payment_bills})

@require_http_methods(["POST"])
def paymentbill_delete(request, pk):

    if not check_privilege(request.user, PAYMENT_BILL_CLEARANCE_MENU_ID, "can_delete"):
        is_admin_ok, msg = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg
            }, status=403)

    try:
        with transaction.atomic():
            payment_bill = get_object_or_404(PaymentBillMaster, pk=pk)

            bill_no = payment_bill.id
            total = payment_bill.TotalAmount

            # 🔹 Capture affected IDs BEFORE deleting
            details = PaymentBillDetails.objects.filter(
                BillMaster=payment_bill
            ).values('VoucherNo', 'voucherType__id')

            hire_ids = set()
            opening_ids = set()
            purchase_ids = set()
            asset_purchase_ids = set()

            for d in details:
                if d['voucherType__id'] == 1:   # Hire
                    hire_ids.add(d['VoucherNo'])
                elif d['voucherType__id'] == 17:  # BillWiseOpening
                    opening_ids.add(d['VoucherNo'])
                elif d['voucherType__id'] == 13:  # Purchase
                    purchase_ids.add(d['VoucherNo'])
                elif d['voucherType__id'] == 17:  # Asset Purchase
                    asset_purchase_ids.add(d['VoucherNo'])

            # ✅ Delete ledger postings
            delete_ledger_postings_for_paymentbillclr(payment_bill)

            # ✅ Delete details
            PaymentBillDetails.objects.filter(BillMaster=payment_bill).delete()

            # ✅ Delete master
            payment_bill.delete()

            # Recalculate Hires
            for hire_id in hire_ids:
                update_hire_cleared_status(hire_id)

            # Recalculate Openings
            for opening_id in opening_ids:
                update_billwise_opening_cleared_status_payment(opening_id)

            # Recalculate Purchases
            for purchase_id in purchase_ids:
                update_purchase_cleared_status(purchase_id)

            # Recalculate Asset Purchases
            for asset_purchase_id in asset_purchase_ids:
                update_asset_purchase_cleared_status(asset_purchase_id)

            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Payment Bill Clearance",
                action_type="DELETE",
                remark=f"Payment Bill Clearance #{bill_no} deleted with total {total:.3f}"
            ))

        return JsonResponse({
            'success': True,
            'message': f'Payment Bill #{bill_no} deleted successfully!'
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error deleting payment bill: {str(e)}'
        }, status=500)    



def expense_list(request):
    """
    Renders the list of all expense vouchers.
    """
    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        EXPENSE_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    expenses = ExpenseMaster.objects.all().order_by('-Date', '-id')
    return render(request, 'expense_list.html', {'expenses': expenses})


def create_edit_expense(request, pk=None):
    if pk:
        expense_master = get_object_or_404(ExpenseMaster, pk=pk)
        title = "Edit Expense Voucher"
        is_edit_mode = True
    else:
        expense_master = ExpenseMaster()
        title = "Create Expense Voucher"
        is_edit_mode = False

    existing_details = []
    is_detailed_expense = True  # default for create mode
    if is_edit_mode:
        is_detailed_expense = expense_master.is_detailed_expense
        details_qs = expense_master.details.all()

        # Infer mode: detailed rows carry an invoice_no or a non-default VAT type
        is_detailed_expense = any(
            (d.invoice_no or '').strip() or d.vat_type != 1
            for d in details_qs
        )

        for detail in details_qs:
            existing_details.append({
                'id': detail.id,
                'ledger_id': detail.Ledger.id if detail.Ledger else '',
                'ledger_name': str(detail.Ledger) if detail.Ledger else '',
                'amount': str(detail.Amount),
                'paid_to': detail.PaidTo or '',
                'party_vat_no': detail.party_VAT_no or '',
                'desc': detail.Desc or '',
                'vehicle_id': detail.Vehicle.id if detail.Vehicle else '',
                'vehicle_name': str(detail.Vehicle) if detail.Vehicle else '',
                'invoice_date': detail.invoice_date.strftime('%Y-%m-%d') if detail.invoice_date else '',
                'invoice_no': detail.invoice_no or '',
                'vat_type': detail.vat_type,
                'vat_amount': str(detail.vat_amount),
            })

    existing_details_json = json.dumps(existing_details)

    if request.method == "POST":

        # 🔐 DETERMINE ACTION
        action = "can_edit" if pk else "can_add"

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            EXPENSE_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        post_data = request.POST.copy()

        # 🔢 CREATE MODE: ignore the voucher no shown on screen, take a fresh one
        if not pk:
            voucher_type_id = post_data.get('voucherType')
            if voucher_type_id:
                try:
                    vt = Vouchers.objects.get(pk=voucher_type_id)
                    post_data['voucher_no'] = vt.get_next_voucher_number()
                except Vouchers.DoesNotExist:
                    pass

        master_form = ExpenseMasterForm(post_data, request.FILES, instance=expense_master)
        formset = ExpenseDetailsFormSet(request.POST, instance=expense_master)

        if master_form.is_valid() and formset.is_valid():
            with transaction.atomic():
                master = master_form.save(commit=False)

                # 🔒 CREATE MODE: lock the voucher type row and take the final number
                if not pk and master.voucherType_id:
                    locked_vt = Vouchers.objects.select_for_update().get(pk=master.voucherType_id)
                    master.voucher_no = locked_vt.get_next_voucher_number()

                master.is_detailed_expense = request.POST.get('is_detailed') == '1'
                if not pk:
                    master.created_by = request.user.id if request.user.is_authenticated else None
                else:
                    master.updated_by = request.user.id if request.user.is_authenticated else None
                master.save()

                formset.instance = master
                instances = formset.save(commit=False)
                for instance in instances:
                    if not instance.pk:
                        instance.created_by = request.user.id if request.user.is_authenticated else None
                    else:
                        instance.updated_by = request.user.id if request.user.is_authenticated else None
                    instance.save()

                for obj in formset.deleted_objects:
                    obj.delete()

                delete_ledger_postings_for_expense(master)
                create_ledger_postings_for_expense(master)

            messages.success(request, f"Expense Voucher '{master.voucher_no}' saved successfully.")
            # ✅ Create LOG
            user = request.user
            action_type = "UPDATE" if is_edit_mode else "CREATE"
            log_activity(
                user=user,
                screen_name="EXPENSE VOUCHER",
                action_type=action_type,
                remark=f" {action_type.lower()}d expense voucher {master.voucher_no}"
            )
            return redirect(f"{reverse('accounts_app:expense_list')}?pdf={master.pk}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        master_form = ExpenseMasterForm(instance=expense_master)
        formset = ExpenseDetailsFormSet(instance=expense_master)

    context = {
        'master_form': master_form,
        'formset': formset,
        'title': title,
        'is_edit_mode': is_edit_mode,
        'existing_details_json': existing_details_json,
        'is_detailed_expense': is_detailed_expense,   # <-- now passed to template
    }
    return render(request, 'expense_form.html', context)


    
@require_POST
def delete_expense(request, pk):
    print("DELETE VIEW CALLED")

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        EXPENSE_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)
            
    expense_master = get_object_or_404(ExpenseMaster, pk=pk)

    voucher_no = expense_master.voucher_no

    delete_ledger_postings_for_expense(expense_master)

    expense_master.delete()

    messages.success(
        request,
        f"Expense Voucher '{voucher_no}' has been deleted successfully."
    )
    # ✅ Create LOG
    user = request.user
    action_type = "DELETE"
    log_activity(
        user=user,
        screen_name="EXPENSE VOUCHER",
        action_type=action_type,
        remark=f" {action_type.lower()}d expense voucher {voucher_no}"
    )

    return redirect("accounts_app:expense_list")

def expense_pdf(request, pk):
    expense = get_object_or_404(ExpenseMaster, pk=pk)
    return create_expense_pdf(expense)        

def get_expenses_for_payment(request):
    """Expense vouchers that still have at least one un-cleared detail."""
    qs = (ExpenseMaster.objects
          .filter(details__IsCleared=False)
          .distinct()
          .order_by('-Date', '-id'))

    data = [{
        'id': e.id,
        'voucher_no': e.voucher_no,
        'date': e.Date.strftime('%Y-%m-%d'),
        'ledger': str(e.ledger),
    } for e in qs]

    return JsonResponse({'success': True, 'expenses': data})


def get_expense_details_for_payment(request, expense_id):
    """Un-cleared detail lines of one expense voucher, ready to drop into a payment."""
    expense_master = get_object_or_404(ExpenseMaster, pk=expense_id)
    details = expense_master.details.filter(IsCleared=False)

    data = [{
        'expense_detail_id': d.id,
        'ledger_id': d.Ledger_id,
        'ledger_name': str(d.Ledger),
        'amount': str(d.Amount),
        'paid_to': d.PaidTo or '',
        'party_vat_no': d.party_VAT_no or '',
        'desc': d.Desc or '',
        'vehicle_id': d.Vehicle_id or '',
        'vehicle_name': str(d.Vehicle) if d.Vehicle else '',
        'invoice_date': str(d.invoice_date) if d.invoice_date else '',
        'invoice_no': d.invoice_no or '',
        'vat_type': d.vat_type,
        'vat_amount': str(d.vat_amount or 0),
    } for d in details]

    return JsonResponse({
        'success': True,
        'voucher_no': expense_master.voucher_no,
        'details': data,
    })    
    
 
def payment_create(request, pk=None):

    if pk:
        payment_instance = get_object_or_404(PaymentMaster, pk=pk)
        is_edit = True
    else:
        payment_instance = None
        is_edit = False

    if request.method == "POST":

        try:
            action = "can_edit" if is_edit else "can_add"

            if not check_privilege(request.user, PAYMENT_MENU_ID, action):
                is_admin_ok, msg = check_admin_override(request)
                if not is_admin_ok:
                    return JsonResponse({
                        "admin_required": True,
                        "message": msg
                    }, status=403)

            post_data = request.POST.copy()

            # 🔢 CREATE MODE: ignore the voucher no shown on screen, take a fresh one
            if not is_edit:
                voucher_type_id = post_data.get('voucherType')
                if voucher_type_id:
                    try:
                        vt = Vouchers.objects.get(pk=voucher_type_id)
                        post_data['voucher_no'] = vt.get_next_voucher_number()
                    except Vouchers.DoesNotExist:
                        pass

            form = PaymentMasterForm(post_data, instance=payment_instance)
            formset = PaymentDetailsFormSet(request.POST)

            if form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():

                        # --- CLEANUP OLD DATA (If Edit) ---
                        if is_edit:
                            old_detail_ids = list(payment_instance.details.values_list('id', flat=True))

                            # Expense details this payment was previously clearing.
                            # We'll revert them, then re-mark only what's actually
                            # submitted below — this keeps edits/removals correct.
                            old_expense_ids = list(
                                payment_instance.details
                                .exclude(expense__isnull=True)
                                .values_list('expense_id', flat=True)
                            )

                            LedgerPosting.objects.filter(
                                VoucherType_id=3
                            ).filter(
                                Q(VoucherNo=payment_instance.id) |
                                Q(VoucherNo__in=old_detail_ids)
                            ).delete()

                            payment_instance.details.all().delete()

                            if old_expense_ids:
                                ExpenseDetails.objects.filter(
                                    id__in=old_expense_ids
                                ).update(IsCleared=False)

                        # --- SAVE MASTER ---
                        master = form.save(commit=False)

                        # 🔒 CREATE MODE: lock the voucher type row and take the final number
                        if not is_edit and master.voucherType_id:
                            locked_vt = Vouchers.objects.select_for_update().get(pk=master.voucherType_id)
                            master.voucher_no = locked_vt.get_next_voucher_number()

                        if master.IsPDC:
                            master.Cleared = "Not Cleared"
                        else:
                            master.Cleared = "Cleared"

                        master.is_detailed = request.POST.get('is_detailed', '0') == '1'
                        master.save()

                        # --- SAVE DETAILS ---
                        new_details = []
                        used_expense_ids = []

                        for idx, detail_form in enumerate(formset):
                            if detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
                                ledger      = detail_form.cleaned_data.get('Ledger')
                                amount      = detail_form.cleaned_data.get('Amount')
                                vehicle     = detail_form.cleaned_data.get('Vehicle')
                                description = detail_form.cleaned_data.get('Desc', '')

                                invoice_date = detail_form.cleaned_data.get('invoice_date') or timezone.now().date()
                                invoice_no   = detail_form.cleaned_data.get('invoice_no') or ''
                                vat_type     = detail_form.cleaned_data.get('vat_type') or 1
                                vat_amount   = detail_form.cleaned_data.get('vat_amount') or 0
                                paid_to      = detail_form.cleaned_data.get('PaidTo', '')
                                party_VAT_no = detail_form.cleaned_data.get('party_VAT_no', '')
                                expense_detail = detail_form.cleaned_data.get('expense')  # NEW

                                detail = PaymentDetails()
                                detail.Ledger       = ledger
                                detail.Amount       = amount
                                detail.Vehicle      = vehicle
                                detail.Desc         = description
                                detail.invoice_date = invoice_date
                                detail.invoice_no   = invoice_no
                                detail.vat_type     = vat_type
                                detail.vat_amount   = vat_amount
                                detail.PaidTo       = paid_to
                                detail.party_VAT_no = party_VAT_no
                                detail.expense       = expense_detail   # NEW — link back to the expense line

                                if hasattr(detail, 'PaymentMaster'):
                                    detail.PaymentMaster = master
                                elif hasattr(detail, 'Payment'):
                                    detail.Payment = master
                                elif hasattr(detail, 'payment'):
                                    detail.payment = master
                                elif hasattr(detail, 'payment_master'):
                                    detail.payment_master = master
                                else:
                                    for field in detail._meta.fields:
                                        if field.related_model == PaymentMaster:
                                            setattr(detail, field.name, master)
                                            break

                                detail.save()
                                new_details.append(detail)

                                if expense_detail is not None:
                                    used_expense_ids.append(expense_detail.id)

                        if not new_details:
                            raise ValueError("No payment details were saved. Please add at least one detail.")

                        # --- UPDATE MASTER TOTAL ---
                        total_amount = sum(d.Amount for d in new_details if d.Amount)
                        master.TotalAmount = total_amount
                        master.save()

                        # --- LEDGER POSTING ---
                        if master.Cleared != "Not Cleared":
                            create_ledger_postings_for_payment(master)

                        # UPDATE VEHICLE PROFIT & LOSS
                        update_vehicle_profit_loss_for_payment(master)

                        # --- MARK LINKED EXPENSE DETAILS AS CLEARED (NEW) ---
                        if used_expense_ids:
                            ExpenseDetails.objects.filter(
                                id__in=used_expense_ids
                            ).update(IsCleared=True)

                    log_activity(
                        user=request.user,
                        screen_name="Payment ",
                        action_type="UPDATE" if is_edit else "CREATE",
                        remark=f"Payment Voucher {master.voucher_no} "
                               f"{'updated' if is_edit else 'created'} "
                               f"with total {master.TotalAmount}"
                    )

                    return JsonResponse({
                        "success": True,
                        "message": (
                            "Payment updated successfully!"
                            if is_edit else
                            f"Payment created successfully! Voucher No: {master.voucher_no}"
                        ),
                        "pdf_url": reverse('accounts_app:payment_pdf', args=[master.id])
                    })

                except Exception as e:
                    import traceback
                    print(f"❌ Error saving payment: {e}")
                    print(traceback.format_exc())

                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving payment: {str(e)}"
                    }, status=400)

            return JsonResponse({
                "success": False,
                "message": "Please correct the errors",
                "errors": {
                    "form": form.errors,
                    "formset": formset.errors
                }
            }, status=400)

        except Exception as e:
            print("=== UNEXPECTED ERROR ===")
            print(str(e))
            import traceback
            traceback.print_exc()

            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)

    else:
        form = PaymentMasterForm(instance=payment_instance)
        formset = PaymentDetailsFormSet()

    # ── Serialize existing details for edit mode ──────────────────────────────
    existing_details_data = []
    if is_edit and payment_instance:
        for detail in payment_instance.details.all():
            existing_details_data.append({
                'ledger_id':    detail.Ledger.id,
                'ledger_name':  str(detail.Ledger),
                'amount':       str(detail.Amount),
                'vehicle_id':   detail.Vehicle.id if detail.Vehicle else '',
                'vehicle_name': str(detail.Vehicle) if detail.Vehicle else '',
                'desc':         detail.Desc or '',
                'invoice_date': str(detail.invoice_date) if detail.invoice_date else '',
                'invoice_no':   detail.invoice_no or '',
                'vat_type':     detail.vat_type or 1,
                'vat_amount':   str(detail.vat_amount or 0),
                'paid_to':      detail.PaidTo or '',
                'party_vat_no': detail.party_VAT_no or '',   # fixed casing to match JS usage below
                'expense_id':   detail.expense_id or '',      # NEW
            })

    return render(request, "payment_create.html", {
        "form":                  form,
        "formset":               formset,
        "is_edit_mode":          is_edit,
        "existing_details_json": json.dumps(existing_details_data),
        "all_vehicles":          Vehicle.objects.all(),
        "is_detailed_payment":   payment_instance.is_detailed if payment_instance else False,
    })    

def list_payment(request):
    """List all payment master entries"""
    # 🔐 CHECK VIEW PRIVILEGE
    if not check_privilege(request.user, PAYMENT_MENU_ID, "can_read"):
        is_admin_ok, msg = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg
            }, status=403)
    
    payments = PaymentMaster.objects.all().order_by('-Date')
    return render(request, "payment_master_list.html", {"payments": payments})

@require_http_methods(["POST"])
def payment_master_delete(request, pk):
    """Delete payment master with P&L cleanup"""
    
    # 🔐 CHECK DELETE PRIVILEGE
    if not check_privilege(request.user, PAYMENT_MENU_ID, "can_delete"):
        is_admin_ok, msg = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg
            }, status=403)
    
    try:
        with transaction.atomic():
            payment = get_object_or_404(PaymentMaster, pk=pk)
            voucher_no = payment.voucher_no
            total = payment.TotalAmount

            detail_ids = list(payment.details.values_list('id', flat=True))

            # ✅ RESET ExpenseDetails.IsCleared for any linked expense rows
            expense_detail_ids = list(
                payment.details.exclude(expense_id__isnull=True)
                                .values_list('expense_id', flat=True)
            )
            if expense_detail_ids:
                ExpenseDetails.objects.filter(
                    id__in=expense_detail_ids
                ).update(IsCleared=False)

            # ✅ DELETE VEHICLE P&L
            delete_vehicle_profit_loss_for_payment(payment)

            # ✅ DELETE LEDGER POSTINGS
            LedgerPosting.objects.filter(
                VoucherType_id=3
            ).filter(
                Q(VoucherNo=payment.id) |
                Q(VoucherNo__in=detail_ids)
            ).delete()

            # ✅ DELETE PAYMENT
            payment.delete()

            # ✅ LOG ONLY AFTER COMMIT
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Payment Entry",
                action_type="DELETE",
                remark=f"Payment Voucher {voucher_no} deleted with total {total}"
            ))

        return JsonResponse({
            'success': True, 
            'message': f'Payment Voucher {voucher_no} deleted successfully!'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': f'Error deleting payment: {str(e)}'
        }, status=500)


def payment_pdf(request, pk):
    payment = get_object_or_404(PaymentMaster, pk=pk)
    return create_payment_pdf(payment)

    


def receipt_create(request, pk=None):

    receipt_instance = get_object_or_404(ReceiptMaster, pk=pk) if pk else None
    is_edit = bool(pk)

    if request.method == "POST":

        try:  # ✅ WRAP EVERYTHING IN TRY-CATCH
            # 🔐 PRIVILEGE CHECK
            action = "can_edit" if is_edit else "can_add"

            if not check_privilege(request.user, RECEIPT_MENU_ID, action):
                is_admin_ok, msg = check_admin_override(request)
                if not is_admin_ok:
                    return JsonResponse({
                        "admin_required": True,
                        "message": msg
                    }, status=403)

            form = ReceiptMasterForm(request.POST, instance=receipt_instance)
            formset = ReceiptDetailsFormSet(request.POST)

            print("=== FORM VALIDATION ===")  # Debug
            print("Form valid?", form.is_valid())
            print("Formset valid?", formset.is_valid())
            
            if not form.is_valid():
                print("Form errors:", form.errors)
            if not formset.is_valid():
                print("Formset errors:", formset.errors)

            if form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():

                        # 🧹 CLEAN OLD DATA (EDIT)
                        if is_edit:
                            LedgerPosting.objects.filter(
                                VoucherType_id=4,
                                VoucherNo=receipt_instance.id
                            ).delete()
                            receipt_instance.details.all().delete()

                        # 🟢 SAVE MASTER
                        master = form.save(commit=False)
                        master.Cleared = "Not Cleared" if master.IsPDC else "Cleared"
                        master.save()

                        # 🟢 SAVE DETAILS
                        details = []
                        for f in formset:
                            if f.cleaned_data and not f.cleaned_data.get("DELETE"):
                                d = ReceiptDetails(
                                    Receipt=master,  # ✅ FIX 1: Set Receipt directly in constructor
                                    Ledger=f.cleaned_data["Ledger"],
                                    Amount=f.cleaned_data["Amount"],
                                    Desc=f.cleaned_data.get("Desc", "")
                                )
                                d.save()  # ✅ FIX 2: Now save will work
                                details.append(d)

                        if not details:
                            raise ValueError("At least one receipt detail is required")

                        # 🟢 UPDATE TOTAL
                        master.TotalAmount = sum(d.Amount for d in details)
                        master.save()

                        # 🟢 LEDGER POSTING
                        if master.Cleared == "Cleared":
                            create_ledger_postings_for_receipt(master)
                    
                    # ✅ AUDIT LOG (ONLY AFTER SUCCESSFUL SAVE)
                    log_activity(
                        user=request.user,
                        screen_name="Receipt Entry",
                        action_type="UPDATE" if is_edit else "CREATE",
                        remark=f"Receipt Voucher {master.voucher_no} {'updated' if is_edit else 'created'} "
                            f"for amount {master.TotalAmount}"
                    )        

                    return JsonResponse({
                        "success": True,
                        "message": (
                            "Receipt updated successfully!"
                            if is_edit else
                            "Receipt created successfully!"
                        ),
                        "pdf_url": reverse('accounts_app:receipt_pdf', args=[master.id]) 
                    })

                except Exception as e:
                    print("=== TRANSACTION ERROR ===")
                    print(str(e))
                    import traceback
                    traceback.print_exc()
                    
                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving receipt: {str(e)}"
                    }, status=400)

            # Form validation failed
            return JsonResponse({
                "success": False,
                "message": "Please correct the errors",
                "errors": {
                    "form": form.errors,
                    "formset": formset.errors
                }
            }, status=400)

        except Exception as e:  # ✅ CATCH ANY UNEXPECTED ERRORS
            print("=== UNEXPECTED ERROR ===")
            print(str(e))
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)

    # GET
    form = ReceiptMasterForm(instance=receipt_instance)
    formset = ReceiptDetailsFormSet()

    existing_details = []
    if is_edit:
        for d in receipt_instance.details.all():
            existing_details.append({
                "ledger_id": d.Ledger.id,
                "ledger_name": str(d.Ledger),
                "amount": str(d.Amount),
                "desc": d.Desc or ""
            })

    return render(request, "receipt_create.html", {
        "form": form,
        "formset": formset,
        "is_edit_mode": is_edit,
        "existing_details_json": json.dumps(existing_details),
    })


def receipt_pdf(request, pk):
    receipt = get_object_or_404(ReceiptMaster, pk=pk)
    return create_receipt_pdf(receipt)


def list_receipt(request):

    if not check_privilege(request.user, RECEIPT_MENU_ID, "can_read"):
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    receipts = ReceiptMaster.objects.all().order_by('-Date')
    return render(request, "receipt_list.html", {
        "receipts": receipts
    })

@require_http_methods(["POST"])  # ✅ ADD THIS
def receipt_delete(request, pk):

    if not check_privilege(request.user, RECEIPT_MENU_ID, "can_delete"):
        is_admin_ok, msg = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg
            }, status=403)

    try:
        with transaction.atomic():
            receipt = ReceiptMaster.objects.select_for_update().get(pk=pk)

            voucher_no = receipt.voucher_no
            total = receipt.TotalAmount

            # ✅ DELETE LEDGER POSTINGS FIRST
            delete_ledger_postings_for_receipt(receipt)

            # ✅ DELETE RECEIPT
            receipt.delete()

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name="Receipt Entry",
                action_type="DELETE",
                remark=f"Receipt Voucher {voucher_no} deleted with total {total}"
            ))
        
        
        

        return JsonResponse({
            "success": True,
            "message": f"Receipt {voucher_no} deleted successfully"
        })

    except ReceiptMaster.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Receipt not found"
        }, status=404)
    except Exception as e:  # ✅ CATCH OTHER ERRORS
        return JsonResponse({
            "success": False,
            "message": f"Error deleting receipt: {str(e)}"
        }, status=500)


        
def ledger_posting_list(request):
    # Get all postings
    postings = list(
        LedgerPosting.objects.all()
        .select_related('ledger', 'VoucherType')
        .order_by('-date', '-id')
    )

    # Resolve real voucher_no strings the same way the ledger report does
    number_lookup = resolve_voucher_numbers(postings)
    for p in postings:
        type_name = p.VoucherType.VoucherName if p.VoucherType_id else ''
        p.display_no = number_lookup.get((type_name, p.VoucherNo), p.VoucherNo)

    # Get filter options
    voucher_types = Vouchers.objects.all()
    ledgers = LedgerCreation.objects.all()

    context = {
        'postings': postings,
        'voucher_types': voucher_types,
        'ledgers': ledgers,
    }

    return render(request, 'ledger_posting_list.html', context)
    
def cheque_clearance(request):
    """
    Display cheque clearance form
    """

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        CHEQUE_CLEARANCE_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)
            
    return render(request, "cheque_clearance.html")



def get_cheque_clearance_bills(request):
    """
    API endpoint to fetch bills based on filter type and date
    Returns JSON data for the table
    """
    try:
        filter_type = request.GET.get('type', 'payable')
        date_filter = request.GET.get('date', '').strip()
        party_filter = request.GET.get('party', '').strip()   # ✅ NEW

        print(f"Filter Type: {filter_type}")
        print(f"Date Filter: '{date_filter}'")
        print(f"Party Filter: '{party_filter}'")

        bills = []

        if filter_type == 'payable':
            query = PaymentMaster.objects.filter(Cleared__in=["Not Cleared", "Bounced"])

            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                except ValueError as e:
                    print(f"Invalid date format: {e}")

            for payment in query.select_related('Ledger'):
                bills.append({
                    'id': payment.id,
                    'voucher_no': payment.voucher_no,
                    'date': payment.Date.strftime('%d/%b/%Y'),
                    'net_total': float(payment.TotalAmount),
                    'ledger_name': payment.Ledger.ledger_name if payment.Ledger else '',
                    'check_date': payment.ChequeDate.strftime('%d/%b/%Y') if payment.ChequeDate else '',
                    'cheque_no': payment.ChequeNo or '',
                    'cleared': payment.Cleared or '',
                })

        elif filter_type == 'receivable':
            query = ReceiptMaster.objects.filter(Cleared__in=["Not Cleared", "Bounced"])

            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                except ValueError as e:
                    print(f"Invalid date format: {e}")

            for receipt in query.select_related('Ledger'):
                bills.append({
                    'id': receipt.id,
                    'voucher_no': receipt.voucher_no,
                    'date': receipt.Date.strftime('%d/%b/%Y'),
                    'net_total': float(receipt.TotalAmount),
                    'ledger_name': receipt.Ledger.ledger_name if receipt.Ledger else '',
                    'check_date': receipt.ChequeDate.strftime('%d/%b/%Y') if receipt.ChequeDate else '',
                    'cheque_no': receipt.ChequeNo or '',
                    'cleared': receipt.Cleared or '',
                })

        elif filter_type == 'payment-bill':
            query = PaymentBillMaster.objects.filter(
                IsPDC=True,
                Cleared__in=["Not Cleared", "Bounced"]
            )

            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                except ValueError as e:
                    print(f"Invalid date format: {e}")

            if party_filter:  # ✅ NEW — search by Supplier ledger name
                query = query.filter(Supplier__ledger_name__icontains=party_filter)

            for payment_bill in query.select_related('Ledger', 'Supplier'):
                bills.append({
                    'id': payment_bill.id,
                    'voucher_no': payment_bill.TrnNo or payment_bill.id,
                    'date': payment_bill.Date.strftime('%d/%b/%Y'),
                    'net_total': float(payment_bill.TotalAmount),
                    'party_name': payment_bill.Supplier.ledger_name if payment_bill.Supplier else '',  # ✅ NEW
                    'ledger_name': payment_bill.Ledger.ledger_name if payment_bill.Ledger else '',
                    'check_date': payment_bill.ChequeDate.strftime('%d/%b/%Y') if payment_bill.ChequeDate else '',
                    'cheque_no': payment_bill.ChequeNo or '',
                    'cleared': payment_bill.Cleared or '',
                })

        elif filter_type == 'receipt-bill':
            query = ReceiptBillMaster.objects.filter(
                IsPDC=True,
                Cleared__in=["Not Cleared", "Bounced"]
            )

            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                except ValueError as e:
                    print(f"Invalid date format: {e}")

            if party_filter:  # ✅ NEW — search by Customer ledger name
                query = query.filter(Customer__ledger_name__icontains=party_filter)

            for receipt_bill in query.select_related('Ledger', 'Customer'):
                bills.append({
                    'id': receipt_bill.id,
                    'voucher_no': receipt_bill.TrnNo or receipt_bill.id,
                    'date': receipt_bill.Date.strftime('%d/%b/%Y'),
                    'net_total': float(receipt_bill.TotalAmount),
                    'party_name': receipt_bill.Customer.ledger_name if receipt_bill.Customer else '',  # ✅ NEW
                    'ledger_name': receipt_bill.Ledger.ledger_name if receipt_bill.Ledger else '',
                    'check_date': receipt_bill.ChequeDate.strftime('%d/%b/%Y') if receipt_bill.ChequeDate else '',
                    'cheque_no': receipt_bill.ChequeNo or '',
                    'cleared': receipt_bill.Cleared or '',
                })

        print(f"Returning {len(bills)} bills")
        return JsonResponse({'bills': bills})

    except Exception as e:
        print(f"❌ Error in get_cheque_clearance_bills: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e),
            'bills': []
        }, status=500)
    
@require_POST
def update_cheque_status(request):
    try:
        data = json.loads(request.body)
        bill_id = data.get('bill_id')
        status = data.get('status')
        bill_type = data.get('type')
        bounce_charge = Decimal(str(data.get('bounce_charge', 0)))

        # ✅ posting_date only matters for Cleared
        posting_date_str = data.get('posting_date')
        if posting_date_str:
            posting_date = datetime.strptime(posting_date_str, '%Y-%m-%d').date()
        else:
            posting_date = timezone.localdate()

        with transaction.atomic():

            if bill_type == 'payable':
                obj = PaymentMaster.objects.select_for_update().get(id=bill_id)
                voucher_no = obj.voucher_no
                old_status = obj.Cleared

                obj.Cleared = status
                if status == "Bounced":
                    obj.BounceCharge = bounce_charge
                obj.save()

                if old_status == "Not Cleared" and status == "Cleared":
                    create_ledger_postings_for_payment(obj, posting_date=posting_date)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting(obj)  # unchanged — today's date

                screen_name = "Cheque Clearance - Payment"

            elif bill_type == 'receivable':
                obj = ReceiptMaster.objects.select_for_update().get(id=bill_id)
                voucher_no = obj.voucher_no
                old_status = obj.Cleared

                obj.Cleared = status
                if status == "Bounced":
                    obj.BounceCharge = bounce_charge
                obj.save()

                if old_status == "Not Cleared" and status == "Cleared":
                    create_ledger_postings_for_receipt(obj, posting_date=posting_date)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting_receipt(obj)  # unchanged

                screen_name = "Cheque Clearance - Receipt"

            elif bill_type == 'payment-bill':
                obj = PaymentBillMaster.objects.select_for_update().get(id=bill_id)
                voucher_no = str(obj.TrnNo or obj.id)
                old_status = obj.Cleared

                obj.Cleared = status

                if status == "Cleared":
                    obj.ChequeStatus = "cleared"
                elif status == "Bounced":
                    obj.ChequeStatus = "bounced"
                    obj.BounceCharge = bounce_charge

                obj.save()

                if old_status == "Not Cleared" and status == "Cleared":
                    create_ledger_postings_for_paymentbillclr(obj, posting_date=posting_date)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting_paymentbill(obj)  # unchanged

                screen_name = "Cheque Clearance - Payment Bill"

            elif bill_type == 'receipt-bill':
                obj = ReceiptBillMaster.objects.select_for_update().get(id=bill_id)
                voucher_no = str(obj.TrnNo or obj.id)
                old_status = obj.Cleared

                obj.Cleared = status

                if status == "Cleared":
                    obj.ChequeStatus = "cleared"
                elif status == "Bounced":
                    obj.ChequeStatus = "bounced"
                    obj.BounceCharge = bounce_charge

                obj.save()

                if old_status == "Not Cleared" and status == "Cleared":
                    create_ledger_postings_for_receiptbillclr(obj, posting_date=posting_date)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting_receiptbill(obj)  # unchanged

                screen_name = "Cheque Clearance - Receipt Bill"

            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid bill type'
                }, status=400)

            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name=screen_name,
                action_type="UPDATE",
                remark=(
                    f"Voucher {voucher_no} cheque status changed "
                    f"from '{old_status}' to '{status}'"
                    + (f" (posting date: {posting_date})" if status == "Cleared" else "")
                    + (
                        f" with bounce charge ₹{bounce_charge}"
                        if status == "Bounced" and bounce_charge > 0
                        else ""
                    )
                )
            ))

        return JsonResponse({
            'success': True,
            'message': f"Voucher {voucher_no} marked as {status}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

# def client_outstanding_report(request):

#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     customer_id = request.GET.get('customer')

#     # Base query
#     credit_invoices = Invoice.objects.filter(
#         payment_mode='Credit',
#         customer__isnull=False
#     )

#     # Apply filters
#     if from_date:
#         credit_invoices = credit_invoices.filter(date__gte=from_date)

#     if to_date:
#         credit_invoices = credit_invoices.filter(date__lte=to_date)

#     if customer_id:
#         credit_invoices = credit_invoices.filter(customer_id=customer_id)

#     credit_invoices = credit_invoices.select_related(
#         'customer', 'voucherType'
#     ).order_by('customer__ledger_name', 'date')

#     customer_map = {}

#     for invoice in credit_invoices:
#         cust = invoice.customer
#         cid = cust.pk

#         if cid not in customer_map:
#             customer_map[cid] = {
#                 'customer': cust,
#                 'invoice_rows': [],
#                 'receipt_rows': [],
#                 'total_invoice': Decimal('0'),
#                 'total_paid': Decimal('0'),
#             }

#         customer_map[cid]['invoice_rows'].append(invoice)
#         customer_map[cid]['total_invoice'] += invoice.grand_total

#     # Receipts
#     for cid, data in customer_map.items():

#         receipt_masters = ReceiptBillMaster.objects.filter(
#             Customer_id=cid
#         ).order_by('Date')

#         if from_date:
#             receipt_masters = receipt_masters.filter(Date__gte=from_date)

#         if to_date:
#             receipt_masters = receipt_masters.filter(Date__lte=to_date)

#         for master in receipt_masters:

#             if master.IsPDC and master.ChequeStatus != 'cleared':
#                 continue

#             data['receipt_rows'].append(master)
#             data['total_paid'] += master.TotalAmount

#     report = []

#     for data in customer_map.values():
#         data['balance'] = data['total_invoice'] - data['total_paid']
#         report.append(data)

#     report.sort(key=lambda x: str(x['customer']))

#     grand_invoice = sum(r['total_invoice'] for r in report)
#     grand_paid = sum(r['total_paid'] for r in report)
#     grand_balance = sum(r['balance'] for r in report)

#     customers = LedgerCreation.objects.filter(
#         groups__groupName='Sundry Debtors'
#     ).order_by('ledger_name')

#     return render(request, 'client_outstanding_report.html', {
#         'report': report,
#         'grand_invoice': grand_invoice,
#         'grand_paid': grand_paid,
#         'grand_balance': grand_balance,
#         'customers': customers,
#         'from_date': from_date,
#         'to_date': to_date,
#         'selected_customer': customer_id,
#     })

# Fixed voucherType IDs used specifically on ReceiptBillDetails
# to mark what kind of record a clearance line belongs to.
# These are NOT the same as BillWiseOpening.voucherType_id.


CLEARANCE_TYPE_OPENING = 16

# BillWiseOpening's own voucherType — a bill can be either kind.
OPENING_BILL_VOUCHER_TYPES = [2]
CLEARANCE_TYPE_INVOICE = 2

# def client_outstanding_report(request):

#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')
#     customer_id = request.GET.get('customer')

#     credit_invoices = Invoice.objects.filter(payment_mode='Credit', customer__isnull=False)
#     if from_date:
#         credit_invoices = credit_invoices.filter(date__gte=from_date)
#     if to_date:
#         credit_invoices = credit_invoices.filter(date__lte=to_date)
#     if customer_id:
#         credit_invoices = credit_invoices.filter(customer_id=customer_id)

#     invoice_customer_ids = set(
#         credit_invoices.values_list('customer_id', flat=True)
#     )

#     opening_customers_qs = BillWiseOpening.objects.filter(
#         voucherType_id__in=OPENING_BILL_VOUCHER_TYPES,
#         IsCleared=False
#     )
#     if customer_id:
#         opening_customers_qs = opening_customers_qs.filter(ledger_id=customer_id)
#     if from_date:
#         opening_customers_qs = opening_customers_qs.filter(InvDate__gte=from_date)
#     if to_date:
#         opening_customers_qs = opening_customers_qs.filter(InvDate__lte=to_date)

#     opening_customer_ids = set(opening_customers_qs.values_list('ledger_id', flat=True))

#     all_customer_ids = invoice_customer_ids | opening_customer_ids

#     report = []
#     for cid in all_customer_ids:
#         data = build_customer_outstanding_data(cid, from_date, to_date)
#         report.append(data)

#     report.sort(key=lambda x: str(x['customer']))

#     grand_invoice = sum(r['total_invoice'] for r in report)
#     grand_opening = sum(r['total_opening'] for r in report)
#     grand_paid = sum(r['total_paid'] for r in report)
#     grand_balance = sum(r['total_outstanding'] for r in report)

#     customers = LedgerCreation.objects.filter(
#         groups__groupName='Sundry Debtors'
#     ).order_by('ledger_name')

#     pdc_list, pdc_grand_credit = [], 0
#     if customer_id and report:
#         pdc_list, pdc_grand_credit = build_customer_pdc_list(
#             customer_id, report[0]['total_outstanding']
#         )

#     return render(
#         request,
#         'client_outstanding_report.html',
#         {
#             'report': report,
#             'grand_invoice': grand_invoice,
#             'grand_opening': grand_opening,
#             'grand_paid': grand_paid,
#             'grand_balance': grand_balance,
#             'customers': customers,
#             'from_date': from_date,
#             'to_date': to_date,
#             'selected_customer': customer_id,
#             'pdc_list': pdc_list,
#             'pdc_grand_credit': pdc_grand_credit,
#         }
#     )
    
# def client_outstanding_pdf(request, customer_id):
#     from_date = request.GET.get('from_date')
#     to_date = request.GET.get('to_date')

#     # Guard against literal "None" string from template rendering
#     if from_date in (None, '', 'None'):
#         from_date = None
#     if to_date in (None, '', 'None'):
#         to_date = None

#     return create_client_outstanding_pdf(customer_id, from_date, to_date)
    

def get_supplier_dict(supp):
    return {
        'supplier': supp,
        'hire_rows': [],
        'purchase_rows': [],
        'asset_rows': [],
        'payment_rows': [],
        'asset_billwise_opening_rows': [],
        'total_hire': Decimal('0'),
        'total_purchase': Decimal('0'),
        'total_asset': Decimal('0'),
        'total_asset_billwise_opening': Decimal('0'),
        'total_paid': Decimal('0'),
    }

def supplier_outstanding_report(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    supplier_id = request.GET.get('supplier')

    credit_hires = FleetHire.objects.filter(
        payment_mode='Credit',
        supplier__isnull=False
    )

    # Apply filters
    if supplier_id:
        credit_hires = credit_hires.filter(supplier_id=supplier_id)

    if from_date:
        credit_hires = credit_hires.filter(date__gte=from_date)

    if to_date:
        credit_hires = credit_hires.filter(date__lte=to_date)

    credit_hires = credit_hires.select_related(
        'supplier','voucherType'
    ).order_by('supplier__ledger_name','date')

    credit_purchases = PurchaseMaster.objects.filter(
        payment_mode='Credit',
        ledger__isnull=False
    )

    if supplier_id:
        credit_purchases = credit_purchases.filter(ledger_id=supplier_id)

    if from_date:
        credit_purchases = credit_purchases.filter(date__gte=from_date)

    if to_date:
        credit_purchases = credit_purchases.filter(date__lte=to_date)

    credit_purchases = credit_purchases.select_related(
        'ledger'
    ).order_by('ledger__ledger_name', 'transaction_date')

    credit_asset_purchases = AssetPurchase.objects.filter(
        payment_mode='Credit',
        supplier__isnull=False
    )

    if supplier_id:
        credit_asset_purchases = credit_asset_purchases.filter(supplier_id=supplier_id)

    if from_date:
        credit_asset_purchases = credit_asset_purchases.filter(date__gte=from_date)

    if to_date:
        credit_asset_purchases = credit_asset_purchases.filter(date__lte=to_date)

    credit_asset_purchases = credit_asset_purchases.select_related(
        'supplier'
    ).order_by('supplier__ledger_name', 'date')

    asset_billwise_openings = BillWiseOpening.objects.filter(
    voucherType_id=17
    )

    if supplier_id:
        asset_billwise_openings = asset_billwise_openings.filter(ledger_id=supplier_id)

    if from_date:
        asset_billwise_openings = asset_billwise_openings.filter(InvDate__gte=from_date)

    if to_date:
        asset_billwise_openings = asset_billwise_openings.filter(InvDate__lte=to_date)

    asset_billwise_openings = asset_billwise_openings.select_related(
        'ledger'
    ).order_by('ledger__ledger_name', 'InvDate')

    supplier_map = {}

    for hire in credit_hires:
        supp = hire.supplier
        sid = supp.pk

        if sid not in supplier_map:
            supplier_map[sid] = get_supplier_dict(supp)

        supplier_map[sid]['hire_rows'].append(hire)
        supplier_map[sid]['total_hire'] += hire.grand_total

    for purchase in credit_purchases:
        supp = purchase.ledger
        sid = supp.pk

        if sid not in supplier_map:
            supplier_map[sid] = get_supplier_dict(supp)

        supplier_map[sid]['purchase_rows'].append(purchase)
        supplier_map[sid]['total_purchase'] += purchase.grand_total_amount  

    for asset in credit_asset_purchases:
        supp = asset.supplier
        sid = supp.pk

        if sid not in supplier_map:
            supplier_map[sid] = get_supplier_dict(supp)

        supplier_map[sid]['asset_rows'].append(asset)
        supplier_map[sid]['total_asset'] += asset.grand_total      


    for opening in asset_billwise_openings:
        supp = opening.ledger
        sid = supp.pk

        if sid not in supplier_map:
            supplier_map[sid] = get_supplier_dict(supp)

        supplier_map[sid]['asset_billwise_opening_rows'].append(opening)
        supplier_map[sid]['total_asset_billwise_opening'] += opening.InvBalance


    for sid, data in supplier_map.items():

        payment_masters = PaymentBillMaster.objects.filter(
            Supplier_id=sid
        ).order_by('Date')

        if from_date:
            payment_masters = payment_masters.filter(Date__gte=from_date)

        if to_date:
            payment_masters = payment_masters.filter(Date__lte=to_date)

        for master in payment_masters:

            if master.IsPDC and master.ChequeStatus != 'cleared':
                continue

            data['payment_rows'].append(master)
            data['total_paid'] += master.TotalAmount


    report = []

    for data in supplier_map.values():
        data['total_amount'] = (
            data.get('total_hire', 0) +
            data.get('total_purchase', 0) +
            data.get('total_asset', 0) +
            data.get('total_asset_billwise_opening', 0)
        )

        data['balance'] = data['total_amount'] - data['total_paid']
        report.append(data)

    report.sort(key=lambda x: str(x['supplier']))

    grand_hire = sum(r['total_hire'] for r in report)
    grand_purchase = sum(r['total_purchase'] for r in report)
    grand_asset = sum(r['total_asset'] for r in report)
    grand_asset_billwise_opening = sum(r['total_asset_billwise_opening'] for r in report)
    grand_total = sum(r['total_amount'] for r in report)
    grand_paid = sum(r['total_paid'] for r in report)
    grand_balance = sum(r['balance'] for r in report)

    suppliers = LedgerCreation.objects.all().order_by('ledger_name')

    return render(request,'supplier_outstanding_report.html',{
    'report': report,
    'grand_hire': grand_hire,
    'grand_purchase': grand_purchase,
    'grand_asset': grand_asset,
    'grand_asset_billwise_opening': grand_asset_billwise_opening,
    'grand_total': grand_total,
    'grand_paid': grand_paid,
    'grand_balance': grand_balance,
    'suppliers': suppliers,
    'from_date': from_date,
    'to_date': to_date,
    'selected_supplier': supplier_id,
})

    
#JOURNAL VOUCHER   

def journal_list(request):
    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        JOURNAL_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)
    
    journals = JournalMaster.objects.select_related(
        'voucherType', 'cost_center', 'staff'
    ).order_by('-created_at')
    return render(request, 'journal_list.html', {'journals': journals})


def journal_create_edit(request, pk=None):
    instance = get_object_or_404(JournalMaster, pk=pk) if pk else None
    form = JournalMasterForm(instance=instance)
    ledgers = LedgerCreation.objects.all().order_by('ledger_name')

    existing_details = []
    if instance:
        for d in instance.details.all():
            existing_details.append({
                'id': d.id,
                'debit_id': d.debit_id or '',
                'debit_name': str(d.debit) if d.debit else '—',
                'credit_id': d.credit_id or '',
                'credit_name': str(d.credit) if d.credit else '—',
                'amount': str(d.amount),
                'narration': d.narration or '',
            })

    if request.method == 'POST':

        # 🔐 DETERMINE ACTION
        action = "can_edit" if pk else "can_add"

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            JOURNAL_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        form = JournalMasterForm(request.POST, instance=instance)

        debit_ids   = request.POST.getlist('detail_debit[]')
        credit_ids  = request.POST.getlist('detail_credit[]')
        amounts     = request.POST.getlist('detail_amount[]')
        narrations  = request.POST.getlist('detail_narration[]')
        detail_ids  = request.POST.getlist('detail_id[]')

        valid_rows = [a for a in amounts if a.strip()]

        if form.is_valid():
            if not valid_rows:
                messages.error(request, 'At least one detail line is required.')
            else:
                try:
                    with transaction.atomic():
                        master = form.save()

                        if instance:
                            kept_ids = [int(x) for x in detail_ids if x.strip()]
                            master.details.exclude(pk__in=kept_ids).delete()

                        for i, amount in enumerate(amounts):
                            if not amount.strip():
                                continue

                            debit_id   = debit_ids[i]  if i < len(debit_ids)   else ''
                            credit_id  = credit_ids[i] if i < len(credit_ids)  else ''
                            narration  = narrations[i] if i < len(narrations)  else ''
                            row_id     = detail_ids[i] if i < len(detail_ids)  else ''

                            if row_id.strip():
                                detail = get_object_or_404(JournalDetail, pk=int(row_id))
                            else:
                                detail = JournalDetail(journal=master)

                            detail.debit_id  = int(debit_id)  if debit_id.strip()  else None
                            detail.credit_id = int(credit_id) if credit_id.strip() else None
                            detail.amount    = amount
                            detail.narration = narration
                            detail.save()

                        # ✅ DELETE OLD LEDGER POSTINGS (IMPORTANT FOR EDIT)
                        delete_ledger_postings_for_journal(master)

                        # ✅ CREATE NEW LEDGER POSTINGS
                        create_ledger_postings_for_journal(master)    
                            

                    log_activity(
                        user=request.user,
                        screen_name="Journal Voucher",
                        action_type="UPDATE" if instance else "CREATE",
                        remark=f"Journal Voucher #{master.voucher_no} "
                               f"{'updated' if instance else 'created'} successfully"
                    )

                    messages.success(request, 'Journal saved successfully.')
                    return redirect(f"{reverse('accounts_app:journal_list')}?pdf={master.pk}")

                except Exception as e:
                    messages.error(request, f'Error saving journal: {e}')

    context = {
        'form':             form,
        'ledgers':          ledgers,
        'existing_details': json.dumps(existing_details),
        'is_edit':          instance is not None,
        'instance':         instance,
    }
    return render(request, 'journal_form.html', context)


def journal_delete(request, pk):
    journal = get_object_or_404(JournalMaster, pk=pk)
    if request.method == 'POST':

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            JOURNAL_MENU_ID,
            "can_delete"
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        # 🔹 DELETE LEDGER POSTINGS FIRST
        delete_ledger_postings_for_journal(journal)
        journal.delete()

        log_activity(
            user=request.user,
            screen_name="Journal Voucher",
            action_type="DELETE",
            remark=f"Journal Voucher #{journal.voucher_no} deleted successfully"
        )
        messages.success(request, 'Journal deleted successfully.')
    return redirect('accounts_app:journal_list')


def journal_pdf(request, pk):
    journal = get_object_or_404(JournalMaster, pk=pk)
    return create_journal_pdf(journal)    


# ===================================CONTRA============================================
import csv
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

def contra_list(request):
    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        CONTRA_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)
    contras = ContraMaster.objects.select_related(
        'voucherType', 'cost_center', 'transfer_from', 'transfer_to'
    ).order_by('-created_at')
    return render(request, 'contra_list.html', {'contras': contras})


def contra_create_edit(request, pk=None):
    instance = get_object_or_404(ContraMaster, pk=pk) if pk else None
    form = ContraMasterForm(request.POST or None, instance=instance)

    if request.method == 'POST':

        # 🔐 DETERMINE ACTION
        action = "can_edit" if pk else "can_add"

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            CONTRA_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        if form.is_valid():
            try:
                with transaction.atomic():
                    contra = form.save()  # ✅ assign

                    # 🔹 DELETE OLD (safe for both create/edit)
                    delete_ledger_postings_for_contra(contra)

                    # 🔹 CREATE NEW
                    create_ledger_postings_for_contra(contra)

                    log_activity(
                        user=request.user,
                        screen_name="Contra Voucher",
                        action_type="UPDATE" if instance else "CREATE",
                        remark=f"Contra Voucher #{contra.voucher_no} "
                               f"{'updated' if instance else 'created'} successfully"
                    )

                messages.success(request, 'Contra voucher saved successfully.')
                return redirect('accounts_app:contra_list')

            except Exception as e:
                messages.error(request, f'Error saving contra: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'form': form,
        'is_edit': instance is not None,
        'instance': instance,
    }
    return render(request, 'contra_form.html', context)

def contra_delete(request, pk):
    contra = get_object_or_404(ContraMaster, pk=pk)
    if request.method == 'POST':
        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            CONTRA_MENU_ID,
            "can_delete"
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        # 🔹 DELETE LEDGER POSTINGS
        delete_ledger_postings_for_contra(contra)
        contra.delete()

        log_activity(
            user=request.user,
            screen_name="Contra Voucher",
            action_type="DELETE",
            remark=f"Contra Voucher #{contra.voucher_no} deleted successfully"
        )
        messages.success(request, 'Contra voucher deleted successfully.')
    return redirect('accounts_app:contra_list')


# ── PDF Export ──────────────────────────────────────────────────────────────

def contra_pdf(request, pk):
    contra = get_object_or_404(
        ContraMaster.objects.select_related(
            'voucherType', 'cost_center', 'transfer_from', 'transfer_to'
        ),
        pk=pk
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm,   bottomMargin=2 * cm,
    )
    styles   = getSampleStyleSheet()
    elements = []

    # ── Title block ────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'title', parent=styles['Heading1'],
        alignment=TA_CENTER, fontSize=16, spaceAfter=4
    )
    sub_style = ParagraphStyle(
        'sub', parent=styles['Normal'],
        alignment=TA_CENTER, fontSize=10, textColor=colors.grey
    )

    elements.append(Paragraph("CONTRA VOUCHER", title_style))
    elements.append(Paragraph(
        f"Voucher No: <b>{contra.voucher_no}</b>", sub_style
    ))
    elements.append(Spacer(1, 0.4 * cm))

    # ── Divider ────────────────────────────────────────────────────
    divider = Table([['']], colWidths=[17 * cm])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#2c3e50')),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 0.4 * cm))

    # ── Header info table ──────────────────────────────────────────
    header_data = [
        ['Voucher Type',  str(contra.voucherType),
         'Date',          contra.date.strftime('%d-%m-%Y')],
        ['Cost Center',   str(contra.cost_center), '', ''],
    ]
    label_style = ParagraphStyle(
        'lbl', parent=styles['Normal'],
        fontSize=9, textColor=colors.grey
    )
    value_style = ParagraphStyle(
        'val', parent=styles['Normal'],
        fontSize=10, fontName='Helvetica-Bold'
    )

    formatted_header = []
    for row in header_data:
        formatted_header.append([
            Paragraph(row[0], label_style),
            Paragraph(row[1], value_style),
            Paragraph(row[2], label_style),
            Paragraph(row[3], value_style),
        ])

    header_tbl = Table(formatted_header, colWidths=[4 * cm, 5.5 * cm, 4 * cm, 3.5 * cm])
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1),
         [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID',        (0, 0), (-1, -1), 0.4, colors.HexColor('#dee2e6')),
        ('TOPPADDING',  (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(header_tbl)
    elements.append(Spacer(1, 0.6 * cm))

    # ── Transfer Details ───────────────────────────────────────────
    elements.append(Paragraph(
        "Transfer Details",
        ParagraphStyle('sec', parent=styles['Heading3'],
                       fontSize=11, textColor=colors.HexColor('#2c3e50'), spaceAfter=6)
    ))

    transfer_data = [
        ['', 'Ledger', 'Amount (OMR)'],
        ['Transfer From', str(contra.transfer_from), ''],
        ['Transfer To',   str(contra.transfer_to),   f"{contra.amount:,.3f}"],
    ]

    amt_style = ParagraphStyle(
        'amt', parent=styles['Normal'],
        alignment=TA_RIGHT, fontSize=10, fontName='Helvetica-Bold'
    )

    transfer_tbl = Table(
        transfer_data,
        colWidths=[4 * cm, 9.5 * cm, 3.5 * cm]
    )
    transfer_tbl.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 10),
        ('ALIGN',         (2, 0), (2, 0), 'RIGHT'),
        # Data rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#eaf4fb'), colors.white]),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 10),
        ('FONTNAME',      (0, 1), (0, -1), 'Helvetica-Bold'),
        ('ALIGN',         (2, 1), (2, -1), 'RIGHT'),
        ('GRID',          (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
    ]))
    elements.append(transfer_tbl)
    elements.append(Spacer(1, 0.6 * cm))

    # ── Amount summary box ─────────────────────────────────────────
    summary_data = [['Total Amount', f"OMR {contra.amount:,.3f}"]]
    summary_tbl = Table(summary_data, colWidths=[13.5 * cm, 3.5 * cm])
    summary_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, 0), (-1, -1), colors.white),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 11),
        ('ALIGN',         (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING',   (0, 0), (0, -1), 8),
        ('RIGHTPADDING',  (1, 0), (1, -1), 8),
    ]))
    elements.append(summary_tbl)

    # ── Footer ─────────────────────────────────────────────────────
    elements.append(Spacer(1, 1.5 * cm))
    footer_data = [['Prepared By', 'Authorized By', 'Received By']]
    footer_tbl  = Table(footer_data, colWidths=[5.6 * cm, 5.7 * cm, 5.7 * cm])
    footer_tbl.setStyle(TableStyle([
        ('LINEABOVE',     (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('TEXTCOLOR',     (0, 0), (-1, -1), colors.grey),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
    ]))
    elements.append(footer_tbl)

    doc.build(elements)
    buffer.seek(0)
    filename = f"Contra_{contra.voucher_no}.pdf"
    response  = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response


# ── CSV Export ──────────────────────────────────────────────────────────────

def contra_csv(request, pk):
    contra = get_object_or_404(
        ContraMaster.objects.select_related(
            'voucherType', 'cost_center', 'transfer_from', 'transfer_to'
        ),
        pk=pk
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="Contra_{contra.voucher_no}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['CONTRA VOUCHER'])
    writer.writerow([])
    writer.writerow(['Voucher No',    contra.voucher_no])
    writer.writerow(['Voucher Type',  str(contra.voucherType)])
    writer.writerow(['Date',          contra.date.strftime('%d-%m-%Y')])
    writer.writerow(['Cost Center',   str(contra.cost_center)])
    writer.writerow([])
    writer.writerow(['Transfer Details'])
    writer.writerow(['', 'Transfer From', str(contra.transfer_from)])
    writer.writerow(['', 'Transfer To',   str(contra.transfer_to)])
    writer.writerow(['', 'Amount',        f"{contra.amount:.3f}"])
    

    return response

def create_edit_debitnote(request, pk=None):

    instance = get_object_or_404(DebitNoteMaster, pk=pk) if pk else None

    if request.method == 'POST':

        # 🔐 DETERMINE ACTION
        action = "can_edit" if pk else "can_add"

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            DEBITNOTE_MENU_ID,
            action
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        master_form = DebitNoteMasterForm(
            request.POST,
            instance=instance
        )

        formset = DebitNoteDetailFormSet(
            request.POST,
            prefix='form',
            instance=instance
        )

        if master_form.is_valid() and formset.is_valid():

            with transaction.atomic():

                master = master_form.save(commit=False)

                if request.user.is_authenticated:
                    master.created_by = request.user.id
                    master.updated_by = request.user.id

                total = Decimal('0.00')

                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):

                        amount = form.cleaned_data.get('Amount') or Decimal('0.00')

                        total += amount

                master.total_amount = total

                master.save()

                # DELETE OLD LEDGER POSTINGS
                if pk:
                    LedgerPosting.objects.filter(
                        VoucherType=master.voucherType,
                        VoucherNo=master.id
                    ).delete()

                # DELETE OLD DETAILS
                if pk:
                    DebitNoteDetail.objects.filter(
                        DebitMaster=master
                    ).delete()

                formset.instance = master

                details = formset.save(commit=False)

                for detail in details:

                    if detail.Amount <= 0:
                        continue

                    detail.DebitMaster = master

                    if request.user.is_authenticated:
                        detail.created_by = request.user.id
                        detail.updated_by = request.user.id

                    detail.save()

                # CREATE LEDGER POSTINGS
                create_ledger_postings_for_debitnote(master)

                hire_ids = DebitNoteDetail.objects.filter(
                    DebitMaster=master,
                    voucherType__id=1
                ).values_list('VoucherNo', flat=True)

                opening_ids = DebitNoteDetail.objects.filter(
                    DebitMaster=master,
                    voucherType__id=17
                ).values_list('VoucherNo', flat=True)

                purchase_ids = DebitNoteDetail.objects.filter(
                    DebitMaster=master,
                    voucherType__id=13
                ).values_list('VoucherNo', flat=True)

                asset_purchase_ids = DebitNoteDetail.objects.filter(
                    DebitMaster=master,
                    voucherType__id=17
                ).values_list('VoucherNo', flat=True)

                for hire_id in hire_ids:
                    update_hire_cleared_status(hire_id)

                for opening_id in opening_ids:
                    update_billwise_opening_cleared_status_payment(opening_id)

                for purchase_id in purchase_ids:
                    update_purchase_cleared_status(purchase_id)

                for asset_purchase_id in asset_purchase_ids:
                    update_asset_purchase_cleared_status(asset_purchase_id)

                log_activity(
                    user=request.user,
                    screen_name="Debit Note",
                    action_type="UPDATE" if instance else "CREATE",
                    remark=f"Debit Note #{master.voucher_no} "
                           f"{'updated' if instance else 'created'} successfully"
                )    


                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Debit Note Saved Successfully'
                    })

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Debit Note Saved Successfully'})
                return redirect('accounts_app:list_debitnote')

    else:

        master_form = DebitNoteMasterForm(instance=instance)

        formset = DebitNoteDetailFormSet(
            prefix='form',
            instance=instance
        )

    return render(request, 'create_debitnote.html', {
        'master_form': master_form,
        'formset': formset,
        'edit_mode': pk is not None,
        'instance': instance,
    })

def debitnote_pdf(request, pk):
    debitnote = get_object_or_404(DebitNoteMaster, pk=pk)
    return create_debitnote_pdf(debitnote)    

def view_debitnote(request, pk):

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        DEBITNOTE_MENU_ID,
        "can_read"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    instance = get_object_or_404(DebitNoteMaster, pk=pk)
    details = DebitNoteDetail.objects.filter(DebitMaster=instance)
    return render(request, 'view_debitnote.html', {
        'debitnote_instance': instance,
        'details': details,
    })    

def delete_debitnote(request, pk):

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        DEBITNOTE_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    instance = get_object_or_404(DebitNoteMaster, pk=pk)

    with transaction.atomic():

        # Force evaluation NOW, before anything is deleted
        hire_ids = list(DebitNoteDetail.objects.filter(
            DebitMaster=instance,
            voucherType__id=1
        ).values_list('VoucherNo', flat=True))

        opening_ids = list(DebitNoteDetail.objects.filter(
            DebitMaster=instance,
            voucherType__id=17
        ).values_list('VoucherNo', flat=True))

        purchase_ids = list(DebitNoteDetail.objects.filter(
            DebitMaster=instance,
            voucherType__id=13
        ).values_list('VoucherNo', flat=True))

        asset_purchase_ids = list(DebitNoteDetail.objects.filter(
            DebitMaster=instance,
            voucherType__id=17
        ).values_list('VoucherNo', flat=True))

        # DELETE OLD DETAILS
        DebitNoteDetail.objects.filter(
            DebitMaster=instance,
        ).delete()

        delete_ledger_postings_for_debitnote(instance)

        instance.delete()

        log_activity(
            user=request.user,
            screen_name="Debit Note",
            action_type="DELETE",
            remark=f"Debit Note #{instance.voucher_no} deleted successfully"
        )

    # status updates run against real, pre-captured IDs, outside the atomic block
    for hire_id in hire_ids:
        update_hire_cleared_status(hire_id)

    for opening_id in opening_ids:
        update_billwise_opening_cleared_status_payment(opening_id)

    for purchase_id in purchase_ids:
        update_purchase_cleared_status(purchase_id)

    for asset_purchase_id in asset_purchase_ids:
        update_asset_purchase_cleared_status(asset_purchase_id)

    messages.success(request, 'Debit Note Deleted')

    return redirect('accounts_app:list_debitnote')

def list_debitnote(request):

    debitnotes = DebitNoteMaster.objects.all()
    
    return render(request, 'list_debitnote.html', {
        'debitnotes': debitnotes
    })


# ================================
# 🔹 CREATE / EDIT CREDITNOTE
# ================================

def create_edit_creditnote(request, pk=None):

    creditnote_instance = None

    if pk:
        creditnote_instance = get_object_or_404(
            CreditNoteMaster,
            pk=pk
        )

    if request.method == 'POST':

        try:

            print("\n=== CREDIT NOTE SAVE DEBUG START ===")
            print("POST DATA:", request.POST)

            master_form = CreditNoteMasterForm(
                request.POST,
                instance=creditnote_instance
            )

            formset = CreditNoteDetailFormSet(
                request.POST,
                prefix='form',
                instance=creditnote_instance
            )

            print("Master form valid:", master_form.is_valid())
            print("Formset valid:", formset.is_valid())

            if not master_form.is_valid():
                print("Master Form Errors:", master_form.errors)

            if not formset.is_valid():
                print("Formset Errors:", formset.errors)

                for i, form in enumerate(formset):
                    if form.errors:
                        print(f"Form {i} errors:", form.errors)

            if master_form.is_valid() and formset.is_valid():

                try:

                    with transaction.atomic():

                        master = master_form.save(commit=False)

                        if request.user.is_authenticated:
                            master.created_by = request.user.id
                            master.updated_by = request.user.id

                        total = Decimal('0.000')

                        for form in formset:

                            if (
                                form.cleaned_data and
                                not form.cleaned_data.get('DELETE', False)
                            ):

                                amount = form.cleaned_data.get(
                                    'Amount',
                                    Decimal('0.000')
                                )

                                if amount and amount > 0:
                                    total += amount

                        master.total_amount = total

                        master.save()

                        print(
                            f"✅ Master saved: "
                            f"ID={master.id}, "
                            f"Total={master.total_amount}"
                        )

                        # ✅ DELETE OLD LEDGER POSTINGS
                        if pk:

                            delete_ledger_postings_for_creditnote(master)

                        # ✅ CREATE LEDGER POSTINGS
                        create_ledger_postings_for_creditnote(master)

                        print("✅ Ledger posting created")

                        # ✅ DELETE OLD DETAILS
                        # Snapshot OLD opening totals BEFORE deleting — needed
                        # to compute the delta afterwards (same as Receipt Bill).
                        old_invoice_ids = set()
                        old_opening_totals = {}

                        if pk:

                            old_entries = CreditNoteDetail.objects.filter(
                                CreditMaster=master
                            ).values(
                                'VoucherNo',
                                'voucherType__id'
                            )

                            for entry in old_entries:

                                if entry['voucherType__id'] == 2:

                                    old_invoice_ids.add(entry['VoucherNo'])

                            old_opening_qs = CreditNoteDetail.objects.filter(
                                CreditMaster=master,
                                voucherType__id=16  # BillWiseOpening
                            ).values('VoucherNo').annotate(total=Sum('Amount'))

                            old_opening_totals = {
                                row['VoucherNo']: (row['total'] or Decimal('0'))
                                for row in old_opening_qs
                            }

                            CreditNoteDetail.objects.filter(
                                CreditMaster=master
                            ).delete()

                            print("🗑️ Deleted old credit note details")

                        # ✅ SAVE DETAILS
                        formset.instance = master

                        details = formset.save(commit=False)

                        invoices_to_check = set()
                        new_opening_totals = {}

                        if pk:

                            invoices_to_check.update(old_invoice_ids)

                        for detail in details:

                            if not detail.Amount or detail.Amount <= 0:

                                print(
                                    f"⏭️ Skipping zero amount "
                                    f"VoucherNo={detail.VoucherNo}"
                                )

                                continue

                            detail.CreditMaster = master

                            voucher_type_id = (
                                detail.voucherType
                                if isinstance(detail.voucherType, int)
                                else detail.voucherType.id
                            )

                            detail.voucherType = Vouchers.objects.get(
                                pk=voucher_type_id
                            )

                            matching_form = next(
                                (
                                    f for f in formset.forms
                                    if f.cleaned_data.get('VoucherNo')
                                    == detail.VoucherNo
                                ),
                                None
                            )

                            if matching_form:

                                detail.CurrentAmount = (
                                    matching_form.cleaned_data.get(
                                        'CurrentAmount',
                                        Decimal('0.000')
                                    )
                                )

                            else:

                                detail.CurrentAmount = Decimal('0.000')

                            if request.user.is_authenticated:

                                detail.created_by = request.user.id
                                detail.updated_by = request.user.id

                            detail.save()

                            print(
                                f"➕ Detail saved: "
                                f"voucherType={detail.voucherType.id}, "
                                f"VoucherNo={detail.VoucherNo}, "
                                f"Amount={detail.Amount}"
                            )

                            # ✅ TRACK FOR RECALCULATION

                            if detail.voucherType.id == 2:

                                invoices_to_check.add(detail.VoucherNo)

                            elif detail.voucherType.id == 16:

                                new_opening_totals[detail.VoucherNo] = (
                                    new_opening_totals.get(detail.VoucherNo, Decimal('0'))
                                    + detail.Amount
                                )

                        # ✅ UPDATE INVOICE STATUS
                        for invoice_id in invoices_to_check:

                            update_invoice_cleared_status(
                                invoice_id
                            )

                        # ✅ UPDATE OPENING BALANCE — DELTA-based, same as
                        # Receipt Bill Clearance, so the credited amount is
                        # taken off the opening's balance and the Receipt Bill
                        # screen shows the reduced pending amount.
                        affected_opening_ids = (
                            set(old_opening_totals.keys()) |
                            set(new_opening_totals.keys())
                        )

                        for opening_id in affected_opening_ids:

                            old_amt = old_opening_totals.get(opening_id, Decimal('0'))
                            new_amt = new_opening_totals.get(opening_id, Decimal('0'))
                            delta = new_amt - old_amt

                            print(
                                f"Opening ID={opening_id}: old={old_amt}, "
                                f"new={new_amt}, delta={delta}"
                            )

                            apply_opening_balance_delta(opening_id, delta)

                    print("=== CREDIT NOTE SAVE DEBUG END ===\n")

                    log_activity(
                        user=request.user,
                        screen_name="Credit Note",
                        action_type="UPDATE" if pk else "CREATE",
                        remark=f"Credit Note #{master.voucher_no} "
                            f"{'updated' if pk else 'created'} successfully"
                    )    

                    return JsonResponse({
                        "success": True,
                        "message": (
                            "Credit Note updated successfully!"
                            if pk else
                            "Credit Note saved successfully!"
                        ),
                        "pdf_url": reverse('accounts_app:creditnote_pdf', args=[master.id]) 
                    })

                except Exception as e:

                    print("❌ Exception during save:", str(e))

                    import traceback
                    traceback.print_exc()

                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving credit note: {str(e)}"
                    }, status=400)

            return JsonResponse({
                "success": False,
                "message": "Please correct the errors",
                "errors": {
                    "master_form": master_form.errors,
                    "formset": formset.errors
                }
            }, status=400)

        except Exception as e:

            print("=== UNEXPECTED ERROR ===")
            print(str(e))

            import traceback
            traceback.print_exc()

            return JsonResponse({
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }, status=500)

    else:

        master_form = CreditNoteMasterForm(
            instance=creditnote_instance
        )

        formset = CreditNoteDetailFormSet(
            prefix='form',
            instance=creditnote_instance
        )

    return render(request, 'create_creditnote.html', {
        'master_form': master_form,
        'formset': formset,
        'edit_mode': pk is not None,
        'creditnote_instance': creditnote_instance,
    })
    
def creditnote_pdf(request, pk):
    creditnote = get_object_or_404(CreditNoteMaster, pk=pk)
    return create_creditnote_pdf(creditnote)


def view_creditnote(request, pk):
    instance = get_object_or_404(CreditNoteMaster, pk=pk)
    details = CreditNoteDetail.objects.filter(CreditMaster=instance).select_related('voucherType')
    return render(request, 'view_creditnote.html', {
        'creditnote_instance': instance,
        'details': details,
    })


def delete_creditnote(request, pk):
    if request.method == 'POST':
        try:
            creditnote_master = CreditNoteMaster.objects.get(id=pk)
            voucher_no = creditnote_master.voucher_no  # capture before delete

            with transaction.atomic():

                # ==========================================
                # ✅ STEP 1 : GET ALL DETAIL RECORDS FIRST
                # ==========================================
                details = list(CreditNoteDetail.objects.filter(
                    CreditMaster=creditnote_master
                ))

                print("🗑️ Deleting Credit Note - Total details:", len(details))

                # ==========================================
                # ✅ STEP 2 : COLLECT ALL VOUCHER IDs
                #    (openings: total credited amount per opening, so it
                #     can be given back to the opening's balance)
                # ==========================================
                invoices_to_check = set()
                opening_totals = {}

                for detail in details:

                    if detail.voucherType.id == 2:

                        invoices_to_check.add(detail.VoucherNo)

                    elif detail.voucherType.id == 16:

                        opening_totals[detail.VoucherNo] = (
                            opening_totals.get(detail.VoucherNo, Decimal('0'))
                            + (detail.Amount or Decimal('0'))
                        )

                print("⏭️ Vouchers to update:", {
                    "invoices": len(invoices_to_check),
                    "openings": len(opening_totals),
                })

                # ==========================================
                # ✅ STEP 3 : Delete Detail Records FIRST
                # ==========================================
                CreditNoteDetail.objects.filter(
                    CreditMaster=creditnote_master
                ).delete()

                print("🗑️ Deleted CreditNoteDetail records")

                # ==========================================
                # ✅ STEP 4 : Delete Master Record
                #    (ledger postings: keep whatever your model / signals
                #     already do here — unchanged from before)
                # ==========================================
                creditnote_master.delete()

                print("🗑️ Deleted CreditNoteMaster record")

                # ==========================================
                # ✅ STEP 5 : RE-OPEN ALL AFFECTED VOUCHERS
                # ==========================================

                # Open Invoice
                for invoice_id in invoices_to_check:

                    update_invoice_cleared_status(
                        invoice_id
                    )

                # Open Opening Balance — give the credited amount back
                # (negative delta = reverse of what the save applied)
                for opening_id, amount in opening_totals.items():

                    print(f"Opening ID={opening_id}: reversing {amount}")

                    apply_opening_balance_delta(opening_id, -amount)

                print("✅ All related vouchers updated")

                

            log_activity(
                user=request.user,
                screen_name="Credit Note",
                action_type="DELETE",
                remark=f"Credit Note #{voucher_no} deleted successfully"
            )

            return JsonResponse({
                "success": True,
                "message": "Credit Note deleted successfully!"
            })

        except CreditNoteMaster.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Credit Note not found."
            }, status=404)

        except Exception as e:
            print("❌ Deletion Error:", str(e))
            traceback.print_exc()
            return JsonResponse({
                "success": False,
                "message": f"Failed to delete: {str(e)}"
            }, status=400)

    return JsonResponse({
        "success": False,
        "message": "Invalid request method."
    }, status=405)

def list_creditnote(request):
    creditnotes = CreditNoteMaster.objects.all()
    return render(request, 'list_creditnote.html', {
        'creditnotes': creditnotes,
    })

def bill_by_bill_report(request):
    from accounts_app.models import LedgerCreation

    bill_type   = request.GET.get('bill_type', 'receipt')   # 'receipt' or 'payment'
    party_id    = request.GET.get('party_id', '').strip()
    from_date   = request.GET.get('from_date', '').strip()
    to_date     = request.GET.get('to_date', '').strip()

    receipt_masters = []
    payment_masters = []
    customers       = []
    suppliers       = []
    totals          = {'total_amount': 0, 'count': 0}

    if bill_type == 'receipt':
        qs = ReceiptBillMaster.objects.select_related(
            'Customer', 'Ledger'
        ).prefetch_related(
            'receiptbilldetails_set__voucherType'
        ).order_by('-Date')

        if party_id:
            qs = qs.filter(Customer_id=party_id)
        if from_date:
            qs = qs.filter(Date__gte=from_date)
        if to_date:
            qs = qs.filter(Date__lte=to_date)

        receipt_masters = list(qs)

        ids = [r.id for r in receipt_masters]
        agg = ReceiptBillMaster.objects.filter(id__in=ids).aggregate(
            total_amount=Sum('TotalAmount'),
            count=Count('id'),
        )
        totals = {
            'total_amount': agg['total_amount'] or 0,
            'count':        agg['count'] or 0,
        }
        customers = LedgerCreation.objects.filter(
            receipt_party__isnull=False
        ).distinct().order_by('ledger_name')

    else:  # payment
        qs = PaymentBillMaster.objects.select_related(
            'Supplier', 'Ledger'
        ).prefetch_related(
            'paymentbilldetails_set__voucherType'
        ).order_by('-Date')

        if party_id:
            qs = qs.filter(Supplier_id=party_id)
        if from_date:
            qs = qs.filter(Date__gte=from_date)
        if to_date:
            qs = qs.filter(Date__lte=to_date)

        payment_masters = list(qs)

        ids = [p.id for p in payment_masters]
        agg = PaymentBillMaster.objects.filter(id__in=ids).aggregate(
            total_amount=Sum('TotalAmount'),
            count=Count('id'),
        )
        totals = {
            'total_amount': agg['total_amount'] or 0,
            'count':        agg['count'] or 0,
        }
        suppliers = LedgerCreation.objects.filter(
            Payment_party__isnull=False
        ).distinct().order_by('ledger_name')

    context = {
        'bill_type':        bill_type,
        'receipt_masters':  receipt_masters,
        'payment_masters':  payment_masters,
        'customers':        customers,
        'suppliers':        suppliers,
        'totals':           totals,
        'filters': {
            'party_id':  party_id,
            'from_date': from_date,
            'to_date':   to_date,
        },
    }
    return render(request, 'bill_by_bill_report.html', context)    

def billwise_opening_list(request):
    openings = BillWiseOpening.objects.select_related(
        'ledger', 'voucherType'
    ).order_by('-InvDate')

    ledgers = LedgerCreation.objects.all().order_by('ledger_name')  # adjust field name if different
    voucher_types = Vouchers.objects.all().order_by('id')  # adjust field name if different

    return render(
        request,
        'billwise_opening_list.html',
        {
            'openings': openings,
            'ledgers': ledgers,
            'voucher_types': voucher_types,
        }
    )

@require_POST
def billwise_opening_create(request):
    try:
        ledger_id = request.POST.get('ledger')
        voucherType_id = request.POST.get('voucherType')
        InvNo = request.POST.get('InvNo', '').strip()
        InvDate = parse_date(request.POST.get('InvDate', ''))
        po_no = request.POST.get('po_no', '').strip()
        InvAmount = request.POST.get('InvAmount')
        InvBalance = request.POST.get('InvBalance')
        dr_cr = request.POST.get('dr_cr')
        IsCleared = request.POST.get('IsCleared') == 'true'

        if not all([ledger_id, voucherType_id, InvNo, InvDate, InvAmount, InvBalance, dr_cr]):
            return JsonResponse({'success': False, 'message': 'Please fill all required fields.'})

        try:
            InvAmount = Decimal(InvAmount)
            InvBalance = Decimal(InvBalance)
        except InvalidOperation:
            return JsonResponse({'success': False, 'message': 'Amount / Balance must be valid numbers.'})

        opening = BillWiseOpening.objects.create(
            ledger_id=ledger_id,
            voucherType_id=voucherType_id,
            InvNo=InvNo,
            InvDate=InvDate,
            po_no=po_no,
            InvAmount=InvAmount,
            InvBalance=InvBalance,
            dr_cr=dr_cr,
            IsCleared=IsCleared,
        )

        log_activity(
            user=request.user,
            screen_name="Bill Wise Opening",
            action_type="CREATE",
            remark=f"Bill Wise Opening #{opening.InvNo} created successfully"
        )

        return JsonResponse({
            'success': True,
            'message': 'Bill Wise Opening created successfully.',
            'data': {
                'id': opening.id,
                'voucherType': str(opening.voucherType),
                'InvNo': opening.InvNo,
                'InvDate': opening.InvDate.strftime('%d-%m-%Y'),
                'ledger': str(opening.ledger),
                'po_no': opening.po_no or '',
                'InvAmount': str(opening.InvAmount),
                'InvBalance': str(opening.InvBalance),
                'dr_cr': opening.get_dr_cr_display(),
                'IsCleared': opening.IsCleared,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error creating record: {str(e)}'})    


def billwise_opening_detail(request, id):
    """AJAX GET — returns the record's current values as JSON for the edit modal."""
    opening = get_object_or_404(BillWiseOpening, id=id)
    return JsonResponse({
        'success': True,
        'data': {
            'id': opening.id,
            'ledger_id': opening.ledger_id,
            'voucherType_id': opening.voucherType_id,
            'InvNo': opening.InvNo,
            'InvDate': opening.InvDate.strftime('%Y-%m-%d'),
            'po_no': opening.po_no or '',
            'InvAmount': str(opening.InvAmount),
            'InvBalance': str(opening.InvBalance),
            'dr_cr': opening.dr_cr,
            'IsCleared': opening.IsCleared,
        }
    })


@require_POST
@transaction.atomic
def billwise_opening_edit(request, id):
    """AJAX POST — updates the record and keeps LedgerPosting in sync."""
    opening = get_object_or_404(BillWiseOpening, id=id)

    try:
        ledger_id = request.POST.get('ledger')
        voucherType_id = request.POST.get('voucherType')
        InvNo = request.POST.get('InvNo', '').strip()
        InvDate = parse_date(request.POST.get('InvDate', ''))
        po_no = request.POST.get('po_no', '').strip()
        InvAmount = request.POST.get('InvAmount')
        InvBalance = request.POST.get('InvBalance')
        dr_cr = request.POST.get('dr_cr')
        IsCleared = request.POST.get('IsCleared') == 'true'

        if not all([ledger_id, voucherType_id, InvNo, InvDate, InvAmount, InvBalance, dr_cr]):
            return JsonResponse({'success': False, 'message': 'Please fill all required fields.'})

        try:
            InvAmount = Decimal(InvAmount)
            InvBalance = Decimal(InvBalance)
        except InvalidOperation:
            return JsonResponse({'success': False, 'message': 'Amount / Balance must be valid numbers.'})

        # --- Capture old VoucherType so we can find the old posting even if it changed ---
        old_voucherType_id = opening.voucherType_id

        opening.ledger_id = ledger_id
        opening.voucherType_id = voucherType_id
        opening.InvNo = InvNo
        opening.InvDate = InvDate
        opening.po_no = po_no
        opening.InvAmount = InvAmount
        opening.InvBalance = InvBalance
        opening.dr_cr = dr_cr
        opening.IsCleared = IsCleared
        opening.save()

        # --- Sync LedgerPosting ---
        # Opening postings are linked by (VoucherType, VoucherNo=opening.id, IsOpening=True).
        # Look under BOTH old and new voucherType, in case voucherType was changed.
        postings = LedgerPosting.objects.filter(
            VoucherType_id__in={old_voucherType_id, opening.voucherType_id},
            VoucherNo=opening.id,
            IsOpening=True
        ).order_by('id')

        if postings.exists():
            # Keep the earliest row, delete any accidental duplicates
            posting = postings.first()
            duplicate_ids = list(postings.exclude(id=posting.id).values_list('id', flat=True))
            if duplicate_ids:
                LedgerPosting.objects.filter(id__in=duplicate_ids).delete()
        else:
            posting = LedgerPosting(
                VoucherType_id=opening.voucherType_id,
                VoucherNo=opening.id,
                IsOpening=True
            )

        posting.date = opening.InvDate
        posting.VoucherType_id = opening.voucherType_id
        posting.ledger_id = opening.ledger_id
        posting.debit = opening.InvBalance if opening.dr_cr == 'DR' else None
        posting.credit = opening.InvBalance if opening.dr_cr == 'CR' else None
        posting.save()

        log_activity(
            user=request.user,
            screen_name="Bill Wise Opening",
            action_type="UPDATE",
            remark=f"Bill Wise Opening #{opening.InvNo} updated successfully"
        )

        return JsonResponse({
            'success': True,
            'message': 'Bill Wise Opening updated successfully.',
            'data': {
                'id': opening.id,
                'voucherType': str(opening.voucherType),
                'InvNo': opening.InvNo,
                'InvDate': opening.InvDate.strftime('%d-%m-%Y'),
                'ledger': str(opening.ledger),
                'po_no': opening.po_no or '',
                'InvAmount': str(opening.InvAmount),
                'InvBalance': str(opening.InvBalance),
                'dr_cr': opening.get_dr_cr_display(),
                'IsCleared': opening.IsCleared,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating record: {str(e)}'})


@require_POST
def delete_billwise_opening(request, pk):

    try:
        with transaction.atomic():

            opening = get_object_or_404(
                BillWiseOpening,
                pk=pk
            )

            # Delete related LedgerPosting
            LedgerPosting.objects.filter(
                VoucherNo=opening.id,
                VoucherType_id=opening.voucherType_id,
                IsOpening=True
            ).delete()

            # Delete BillWiseOpening
            opening.delete()

            log_activity(
                user=request.user,
                screen_name="Bill Wise Opening",
                action_type="DELETE",
                remark=f"Bill Wise Opening #{opening.InvNo} deleted successfully"
            )

        return JsonResponse({
            'success': True,
            'message': 'Bill Wise Opening deleted successfully.'
        })

    except Exception as e:

        import traceback
        print("BILLWISE DELETE ERROR:", e)
        print(traceback.format_exc())

        return JsonResponse({
            'success': False,
            'message': f'Error deleting record: {str(e)}'
        }, status=400)


# def clear_billwise_opening(request):
#     if request.method not in ["POST", "GET"]:
#         messages.error(request, "Invalid request")
#         return redirect("fleet_app:fleet_home")

#     try:
#         with connection.cursor() as cursor:
#             # Delete only Opening LedgerPosting entries
#             cursor.execute("""
#                 DELETE FROM accounts_app_ledgerposting
#                 WHERE "IsOpening" = TRUE;
#             """)
#             ledger_deleted = cursor.rowcount

#             # Delete BillWiseOpening records
#             cursor.execute("""
#                 DELETE FROM accounts_app_billwiseopening;
#             """)
#             opening_deleted = cursor.rowcount

#             log_activity(
#                 user=request.user,
#                 screen_name="Bill Wise Opening",
#                 action_type="DELETE",
#                 remark=f"Cleared {ledger_deleted} Ledger Posting(s) and {opening_deleted} BillWise Opening record(s)."
#             )

#         messages.success(
#             request,
#             f"Deleted {ledger_deleted} Ledger Posting(s) and {opening_deleted} BillWise Opening record(s)."
#         )

#     except Exception as e:
#         messages.error(request, f"Error clearing data: {e}")

#     return redirect("fleet_app:fleet_home")



# =========================================================
# CLEARANCE-TYPE MARKERS
# (the voucherType_id written on ReceiptBillDetails /
# PaymentBillDetails to say WHAT KIND of bill a line clears —
# not the bill's own voucherType)
# =========================================================
CLEARANCE_TYPE_INVOICE = 2
CLEARANCE_TYPE_OPENING = 16          # BillWiseOpening, either side, either sub-type
CLEARANCE_TYPE_HIRE = 1
CLEARANCE_TYPE_PURCHASE = 13
CLEARANCE_TYPE_ASSET_PURCHASE = 17

# BillWiseOpening's OWN voucherType (client side: old invoices)
CLIENT_OPENING_BILL_VOUCHER_TYPES = [2]

# BillWiseOpening's OWN voucherType (supplier side: old asset purchases)
SUPPLIER_ASSET_OPENING_VOUCHER_TYPE = 17

OUTSTANDING_THRESHOLD = Decimal('0.001')


# =========================================================
# BUCKET HELPERS
# =========================================================
def _bucket_labels(bucket_size, start=0, num_buckets=10):
    edges = [start + i * bucket_size for i in range(num_buckets + 1)]
    labels = ['Current']
    for i in range(num_buckets):
        lo = edges[i] if i == 0 else edges[i] + 1
        hi = edges[i + 1]
        labels.append(f'{lo}-{hi}')
    labels.append(f'Above {edges[num_buckets]}')
    return labels


def _bucket_label(age, bucket_size, start=0, num_buckets=10):
    edges = [start + i * bucket_size for i in range(num_buckets + 1)]

    if age <= 0:
        return 'Current'

    for i in range(num_buckets):
        if age <= edges[i + 1]:
            lo = edges[i] if i == 0 else edges[i] + 1
            hi = edges[i + 1]
            return f'{lo}-{hi}'

    return f'Above {edges[num_buckets]}'

# =========================================================
# CLIENT AGING
# =========================================================
def _build_client_aging(customer_id, as_of_date, bucket_size, bucket_labels, start=0, num_buckets=10):

    customers, _ = build_client_outstanding_data(
        customer_id=customer_id,
        to_date=as_of_date,
    )

    party_map = {}

    for cust in customers:
        ledger = cust['ledger']
        entry = {
            'party': ledger,
            'buckets': {label: Decimal('0') for label in bucket_labels},
            'total': Decimal('0'),
        }

        for bill in cust['bills']:
            outstanding = bill['outstanding']
            if outstanding <= OUTSTANDING_THRESHOLD:
                continue

            label = _bucket_label(bill['age_days'], bucket_size, start, num_buckets)
            entry['buckets'][label] += outstanding
            entry['total'] += outstanding

        party_map[ledger.pk] = entry

    return _finalize(party_map, bucket_labels)

# =========================================================
# SUPPLIER AGING
# =========================================================
def _build_supplier_aging(supplier_id, as_of_date, bucket_size, bucket_labels, start=0, num_buckets=10):

    suppliers, _ = build_supplier_outstanding_data(
        supplier_id=supplier_id,
        to_date=as_of_date,
    )

    party_map = {}

    for supp in suppliers:
        ledger = supp['ledger']
        entry = {
            'party': ledger,
            'buckets': {label: Decimal('0') for label in bucket_labels},
            'total': Decimal('0'),
        }

        for bill in supp['bills']:
            outstanding = bill['outstanding']
            if outstanding <= OUTSTANDING_THRESHOLD:
                continue

            label = _bucket_label(bill['age_days'], bucket_size, start, num_buckets)
            entry['buckets'][label] += outstanding
            entry['total'] += outstanding

        party_map[ledger.pk] = entry

    return _finalize(party_map, bucket_labels)

# =========================================================
# SHARED FINALIZER — dict buckets -> ordered lists + grand totals
# =========================================================
def _finalize(party_map, bucket_labels):

    report = sorted(party_map.values(), key=lambda x: str(x['party']))

    for entry in report:
        entry['bucket_values'] = [entry['buckets'][label] for label in bucket_labels]

    grand_totals = {label: Decimal('0') for label in bucket_labels}
    grand_total_amount = Decimal('0')

    for entry in report:
        for label in bucket_labels:
            grand_totals[label] += entry['buckets'][label]
        grand_total_amount += entry['total']

    grand_totals_list = [grand_totals[label] for label in bucket_labels]

    return report, grand_totals_list, grand_total_amount


# =========================================================
# MAIN VIEW
# =========================================================
def aging_report(request):

    entity = request.GET.get('entity', 'client')
    if entity not in ('client', 'supplier'):
        entity = 'client'

    entity_id = request.GET.get('entity_id')

    bucket_size_raw = request.GET.get('bucket_size')
    try:
        bucket_size = int(bucket_size_raw) if bucket_size_raw else 30
        if bucket_size <= 0:
            bucket_size = 30
    except ValueError:
        bucket_size = 30

    bucket_start_raw = request.GET.get('bucket_start')
    try:
        bucket_start = int(bucket_start_raw) if bucket_start_raw else 0
        if bucket_start < 0:
            bucket_start = 0
    except ValueError:
        bucket_start = 0

    num_buckets_raw = request.GET.get('num_buckets')
    try:
        num_buckets = int(num_buckets_raw) if num_buckets_raw else 10
        if num_buckets <= 0:
            num_buckets = 10
    except ValueError:
        num_buckets = 10

    as_of_raw = request.GET.get('as_of_date')
    if as_of_raw:
        try:
            as_of_date = datetime.strptime(as_of_raw, '%Y-%m-%d').date()
        except ValueError:
            as_of_date = date.today()
    else:
        as_of_date = date.today()

    bucket_labels = _bucket_labels(bucket_size, bucket_start, num_buckets)

    if entity == 'supplier':
        report, grand_totals_list, grand_total_amount = _build_supplier_aging(
            entity_id, as_of_date, bucket_size, bucket_labels, bucket_start, num_buckets
        )
        parties = LedgerCreation.objects.all().order_by('ledger_name')
    else:
        report, grand_totals_list, grand_total_amount = _build_client_aging(
            entity_id, as_of_date, bucket_size, bucket_labels, bucket_start, num_buckets
        )
        parties = LedgerCreation.objects.filter(
            groups__groupName='Sundry Debtors'
        ).order_by('ledger_name')

    return render(
        request,
        'aging_report.html',
        {
            'entity': entity,
            'entity_id': entity_id,
            'as_of_date': as_of_date.strftime('%Y-%m-%d'),
            'bucket_size': bucket_size,
            'bucket_start': bucket_start,
            'num_buckets': num_buckets,
            'bucket_labels': bucket_labels,
            'report': report,
            'grand_totals_list': grand_totals_list,
            'grand_total_amount': grand_total_amount,
            'parties': parties,
        }
    )
    
def ledger_report_page(request):
    """Renders the page shell: ledger dropdown + date pickers + empty table."""
    ledgers = LedgerCreation.objects.all().order_by('ledger_name')
    return render(request, 'ledger_report.html', {'ledgers': ledgers})


@require_GET
def ledger_report_data(request):
    """AJAX endpoint — returns the ledger report as JSON for the given filters."""
    ledger_id = request.GET.get('ledger_id')
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')

    if not (ledger_id and from_date_str and to_date_str):
        return JsonResponse({'error': 'ledger_id, from_date and to_date are required'}, status=400)

    try:
        from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Dates must be in YYYY-MM-DD format'}, status=400)

    ledger = LedgerCreation.objects.filter(pk=ledger_id).first()
    if not ledger:
        return JsonResponse({'error': 'Ledger not found'}, status=404)

    rows = get_ledger_report(ledger_id, from_date, to_date)

    def fmt(amount):
        return f"{amount:.3f}" if amount is not None else ""

    def fmt_balance(balance):
        return f"{abs(balance):.3f} {'Dr' if balance >= 0 else 'Cr'}"

    total_debit = sum((r['debit'] or Decimal('0')) for r in rows[1:])
    total_credit = sum((r['credit'] or Decimal('0')) for r in rows[1:])
    closing_balance = rows[-1]['balance'] if rows else Decimal('0')

    # ---------------------------------------------------
    # PDC LIST — try customer (receivable) side first,
    # fall back to supplier (payable) side.
    # ---------------------------------------------------
    pdc_list, pdc_grand_credit = build_customer_pdc_list(ledger_id, closing_balance)
    pdc_side = 'receipt'
    if not pdc_list:
        pdc_list, pdc_grand_credit = build_supplier_pdc_list(ledger_id, abs(closing_balance))
        pdc_side = 'payment'

    data = {
        'ledger_name': ledger.ledger_name,
        'rows': [
            {
                'date': r['date'].strftime('%d-%b-%Y'),
                'particulars': r['particulars'],
                'voucher_type': r['voucher_type'],
                'voucher_no': r['voucher_no'],
                'remark': r.get('remark', ''),  
                'edit_url': r.get('edit_url'),
                'debit': fmt(r['debit']),
                'credit': fmt(r['credit']),
                'balance': fmt_balance(r['balance']),
            }
            for r in rows
        ],
        'total_debit': fmt(total_debit),
        'total_credit': fmt(total_credit),
        'closing_balance': fmt_balance(closing_balance),
        'pdc_side': pdc_side if pdc_list else None,
                'pdc_list': [
                    {
                        'sl_no': p['sl_no'],
                        'date': p['date'].strftime('%d/%m/%Y') if p['date'] else '',
                        'voucher_no': p['voucher_no'],
                        'cheque_no': p['cheque_no'] or '-',
                        'cheque_date': p['cheque_date'].strftime('%d/%m/%Y') if p['cheque_date'] else '-',
                        'debit': fmt(p['debit']),
                        'credit': fmt(p['credit']),
                        'balance': fmt(abs(p['balance'])) + (' Dr' if p['balance'] >= 0 else ' Cr'),
                        'remark': p['remark'],
                    }
                    for p in pdc_list
                ],
        'pdc_grand_credit': fmt(pdc_grand_credit),
    }
    return JsonResponse(data)


# def resolve_voucher_numbers(period_postings):
#     """Batch-resolve VoucherNo (PK) -> real voucher_no string, one query per voucher type."""
#     by_type = defaultdict(set)
#     for p in period_postings:
#         by_type[p.VoucherType.VoucherName].add(p.VoucherNo)

#     number_lookup = {}  # (VoucherName, pk) -> voucher_no string, only if non-empty
#     for type_name, pks in by_type.items():
#         model = VOUCHER_MODEL_MAP.get(type_name)
#         if not model:
#             continue
#         for obj_id, voucher_no in model.objects.filter(pk__in=pks).values_list('id', 'voucher_no'):
#             if voucher_no:  # skip None / '' — let the caller fall back to PK
#                 number_lookup[(type_name, obj_id)] = voucher_no
#     return number_lookup



def resolve_voucher_numbers(period_postings):
    """Batch-resolve VoucherNo (PK) -> real voucher_no string, one query per voucher type."""
    regular_postings = [p for p in period_postings if not p.IsOpening]
    opening_postings = [p for p in period_postings if p.IsOpening]

    by_type = defaultdict(set)
    for p in regular_postings:
        by_type[p.VoucherType.VoucherName].add(p.VoucherNo)

    number_lookup = {}  # (VoucherName, pk) -> voucher_no string, only if non-empty
    for type_name, pks in by_type.items():
        model = VOUCHER_MODEL_MAP.get(type_name)
        if not model:
            continue
        # Use the correct voucher number field for each model
        field_names = {field.name for field in model._meta.get_fields()}

        if 'voucher_no' in field_names:
            number_field = 'voucher_no'
        elif 'voucher_number' in field_names:
            number_field = 'voucher_number'
        else:
            continue

        for obj_id, voucher_no in model.objects.filter(
            pk__in=pks
        ).values_list('id', number_field):
            if voucher_no:
                number_lookup[(type_name, obj_id)] = voucher_no

    # Opening entries: VoucherNo is a BillWiseOpening id, display its InvNo instead
    opening_ids = {p.VoucherNo for p in opening_postings}
    if opening_ids:
        for obj_id, inv_no in BillWiseOpening.objects.filter(pk__in=opening_ids).values_list('id', 'InvNo'):
            if inv_no:
                for p in opening_postings:
                    if p.VoucherNo == obj_id:
                        type_name = p.VoucherType.VoucherName if p.VoucherType_id else ''
                        number_lookup[(type_name, obj_id)] = inv_no

    return number_lookup


# natureOfGroup codes on Groups model
NATURE_EXPENSE = 1
NATURE_INCOME = 2
NATURE_LIABILITY = 3
NATURE_ASSET = 4

# Natures with a normal CREDIT balance: Opening + Credit - Debit
CREDIT_NATURE_CODES = {NATURE_INCOME, NATURE_LIABILITY}
# Everything else (Expense, Asset, or unrecognized/null) => normal DEBIT balance


def get_balance_by_nature(nature_code, opening, total_debit, total_credit):
    """
    Compute a ledger's running/closing balance per its accounting nature.

    Asset / Expense (or unknown nature) -> Opening + Debit - Credit   (normal Dr)
    Liability / Income                  -> Opening + Credit - Debit   (normal Cr)

    Sign convention matches the existing fmt_balance():
        positive => Dr, negative => Cr
    So for credit-nature ledgers we compute (Credit - Debit) off an
    opening balance that itself must be read as debit-positive first
    (LedgerPosting aggregates always give opening as debit - credit,
    regardless of the ledger's nature), then negate the whole result
    to express it in the same debit-positive sign convention.
    """
    if nature_code in CREDIT_NATURE_CODES:
        credit_positive_opening = -opening
        result_credit_positive = credit_positive_opening + total_credit - total_debit
        return -result_credit_positive
    # Normal Dr balance
    return opening + total_debit - total_credit    

def build_remark_lookup(period_postings):
    """
    Returns { (voucher_type_name, voucher_no): remark_string }
    One query per voucher type present in the period, not per row.
    """
    remark_lookup = {}

    grouped = defaultdict(set)
    for p in period_postings:
        grouped[p.VoucherType.VoucherName].add(p.VoucherNo)

    for type_name, voucher_nos in grouped.items():
        config = REMARK_CONFIG.get(type_name)
        if not config:
            continue  # Contra, Hire, or unmapped types -> stays blank

        field = config['field']

        if config['source'] == 'master':
            model = VOUCHER_MODEL_MAP.get(type_name)
            if not model:
                continue
            qs = model.objects.filter(pk__in=voucher_nos).values_list('pk', field)
            for pk, val in qs:
                remark_lookup[(type_name, pk)] = val or ''

        elif config['source'] == 'detail':
            detail_model = config['model']
            fk_field = config['fk']
            qs = (
                detail_model.objects
                .filter(**{f'{fk_field}__in': voucher_nos})
                .order_by('pk')
                .values_list(fk_field, field)
            )
            for master_pk, val in qs:
                key = (type_name, master_pk)
                # take the first non-empty remark found for that voucher
                if val and not remark_lookup.get(key):
                    remark_lookup[key] = val

        # backfill blanks so .get() always resolves cleanly downstream
        for vn in voucher_nos:
            remark_lookup.setdefault((type_name, vn), '')

    return remark_lookup    

def get_ledger_report(ledger_id, from_date, to_date):
    base_qs = LedgerPosting.objects.filter(ledger_id=ledger_id, IsDeleted=False)

    opening_agg = base_qs.filter(date__lt=from_date).aggregate(
        d=Sum('debit'), c=Sum('credit')
    )
    opening_balance = (opening_agg['d'] or Decimal('0')) - (opening_agg['c'] or Decimal('0'))

    period_postings = list(
        base_qs.filter(date__gte=from_date, date__lte=to_date)
        .select_related('VoucherType')
        .order_by('date', 'id')
    )

    voucher_keys = {(p.VoucherType_id, p.VoucherNo) for p in period_postings}
    voucher_type_ids = {k[0] for k in voucher_keys}
    voucher_nos = {k[1] for k in voucher_keys}
    number_lookup = resolve_voucher_numbers(period_postings)
    remark_lookup = build_remark_lookup(period_postings)

    contra_map = defaultdict(list)
    if voucher_keys:
        contra_postings = (
            LedgerPosting.objects
            .filter(IsDeleted=False, VoucherType_id__in=voucher_type_ids, VoucherNo__in=voucher_nos)
            .exclude(ledger_id=ledger_id)
            .select_related('ledger')
        )
        for c in contra_postings:
            key = (c.VoucherType_id, c.VoucherNo)
            if key in voucher_keys:
                contra_map[key].append(c.ledger.ledger_name)

    rows = [{
        'date': from_date,
        'particulars': 'Opening Balance',
        'voucher_type': '',
        'voucher_no': '',
        'remark': '',  
        'debit': opening_balance if opening_balance > 0 else None,
        'credit': -opening_balance if opening_balance < 0 else None,
        'balance': opening_balance,
    }]

    running = opening_balance
    for p in period_postings:
        names = contra_map.get((p.VoucherType_id, p.VoucherNo)) or ['Sundries']
        particulars = ('To ' if p.debit else 'By ') + ', '.join(names)
        running += (p.debit or Decimal('0')) - (p.credit or Decimal('0'))

        type_name = p.VoucherType.VoucherName
        display_no = number_lookup.get((type_name, p.VoucherNo), p.VoucherNo)
        remark = remark_lookup.get((type_name, p.VoucherNo), '')

        edit_url = None
        url_name = VOUCHER_EDIT_URL_MAP.get(type_name)
        if url_name:
            try:
                edit_url = reverse(url_name, args=[p.VoucherNo])
            except Exception:
                edit_url = None

        rows.append({
            'date': p.date,
            'particulars': particulars,
            'voucher_type': type_name,
            'voucher_no': display_no,
            'remark': remark,  
            'edit_url': edit_url,
            'debit': p.debit,
            'credit': p.credit,
            'balance': running,
        })

    return rows


@login_required
def create_openingvoucher(request):
    if request.method == 'POST':
        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            OPENING_VOUCHER_MENU_ID,
            "can_add"
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)
        master_form = OpeningVoucherMasterForm(request.POST)
        formset = OpeningVoucherDetailsFormSet(request.POST)

        if master_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    master = master_form.save()

                    formset.instance = master
                    formset.save()

                    create_ledger_postings_for_openingvoucher(master)

                    log_activity(
                        user=request.user,
                        screen_name="Opening Voucher",
                        action_type="CREATE",
                        remark=f"Opening Voucher #{master.voucher_no} created successfully"
                    )

                messages.success(request, 'Opening Voucher created successfully.')
                return redirect('accounts_app:list_openingvoucher')
            except Exception as e:
                messages.error(request, f'Error creating voucher: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        master_form = OpeningVoucherMasterForm()
        formset = OpeningVoucherDetailsFormSet()

    context = {
        'master_form': master_form,
        'formset': formset,
        'is_edit': False,
    }
    return render(request, 'openingvoucher_form.html', context)


@login_required
def edit_openingvoucher(request, pk):
    master = get_object_or_404(OpeningVoucherMaster, pk=pk)

    if request.method == 'POST':

        # 🔐 CHECK PRIVILEGE
        has_permission = check_privilege(
            request.user,
            OPENING_VOUCHER_MENU_ID,
            "can_edit"
        )

        if not has_permission:
            is_admin_ok, msg_or_admin = check_admin_override(request)
            if not is_admin_ok:
                return JsonResponse({
                    "admin_required": True,
                    "message": msg_or_admin
                }, status=403)

        master_form = OpeningVoucherMasterForm(request.POST, instance=master)
        formset = OpeningVoucherDetailsFormSet(request.POST, instance=master)

        if master_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():

                    master_form.save()
                    delete_ledger_postings_for_openingvoucher(master)
                    formset.save()
                    create_ledger_postings_for_openingvoucher(master)

                    log_activity(
                        user=request.user,
                        screen_name="Opening Voucher",
                        action_type="UPDATE",
                        remark=f"Opening Voucher #{master.voucher_no} updated successfully"
                    )

                messages.success(request, 'Opening Voucher updated successfully.')
                return redirect('accounts_app:list_openingvoucher')
            except Exception as e:
                messages.error(request, f'Error updating voucher: {e}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        master_form = OpeningVoucherMasterForm(instance=master)
        formset = OpeningVoucherDetailsFormSet(instance=master)

    context = {
        'master_form': master_form,
        'formset': formset,
        'is_edit': True,
        'voucher': master,
    }
    return render(request, 'openingvoucher_form.html', context)

@login_required
@require_POST
def delete_openingvoucher(request, pk):

    # 🔐 CHECK PRIVILEGE
    has_permission = check_privilege(
        request.user,
        OPENING_VOUCHER_MENU_ID,
        "can_delete"
    )

    if not has_permission:
        is_admin_ok, msg_or_admin = check_admin_override(request)
        if not is_admin_ok:
            return JsonResponse({
                "admin_required": True,
                "message": msg_or_admin
            }, status=403)

    master = get_object_or_404(OpeningVoucherMaster, pk=pk)
    voucher_no = master.voucher_no
    try:
        with transaction.atomic():
            delete_ledger_postings_for_openingvoucher(master)
            master.delete()
            
            log_activity(
                user=request.user,
                screen_name="Opening Voucher",
                action_type="DELETE",
                remark=f"Opening Voucher #{voucher_no} deleted successfully"
            )
            
        return JsonResponse({'status': 'success', 'message': f'Opening Voucher "{voucher_no}" deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def list_openingvoucher(request):
    vouchers = OpeningVoucherMaster.objects.select_related(
        'voucherType', 'cost_conter', 'sales_person'
    ).order_by('-date', '-id')

    context = {'vouchers': vouchers}
    return render(request, 'openingvoucher_list.html', context)



SUNDRY_DEBTOR_GROUP_ID = 29
ZERO = Decimal('0.000')
OPENING_VOUCHER_TYPE_ID = 16   # voucherType used for openings in ReceiptBillDetails
EXCLUDED_CHEQUE_STATUSES = ()
VOUCHER_DETAIL_MAP = {
    'Opening': {
        'app': 'accounts_app',
        'model': 'BillWiseOpening',
        'invoice_field': 'InvNo',
        'po_field': 'po_no',
    },
    'Invoice': {
        'app': 'fleet_app',
        'model': 'Invoice',
        'invoice_field': 'voucher_no',
        'po_field': 'buyer_order_no',
    },
    # Add every other VoucherType that can post to a Sundry Debtor ledger here,
    # e.g. 'Credit Note': {...}, 'Receipt': {...}
}
 
from django.apps import apps 
# def _get_voucher_detail(voucher_type_name, voucher_no):
#     """Resolve Invoice No / PO No for one LedgerPosting row. Falls back to a
#     generic INV-<id> label if no mapping is configured for that voucher type."""
#     config = VOUCHER_DETAIL_MAP.get(voucher_type_name)
#     fallback_no = f"{voucher_no}"
#     if not config:
#         return fallback_no, '-'
#     try:
#         model = apps.get_model(config['app'], config['model'])
#     except LookupError:
#         return fallback_no, '-'
 
#     obj = model.objects.filter(pk=voucher_no).first()
#     if not obj:
#         return fallback_no, '-'
 
#     invoice_no = getattr(obj, config['invoice_field'], None) or fallback_no
#     po_no = getattr(obj, config['po_field'], None) or '-'
#     return invoice_no, po_no
 
def _bill_key(voucher_type_id, voucher_no, is_opening=False):
    """Openings are matched by ('OPENING', no) because LedgerPosting stores
    them as Invoice + IsOpening, while ReceiptBillDetails uses voucherType 16."""
    try:
        voucher_no = int(voucher_no)
    except (TypeError, ValueError):
        pass
    if is_opening:
        return ('OPENING', voucher_no)
    return (voucher_type_id, voucher_no)


def _get_billwise_cleared(customer_id, to_date=None):
    qs = ReceiptBillDetails.objects.filter(BillMaster__Customer_id=customer_id)
    if EXCLUDED_CHEQUE_STATUSES:
        qs = qs.exclude(BillMaster__ChequeStatus__in=EXCLUDED_CHEQUE_STATUSES)
    if to_date:
        qs = qs.filter(BillMaster__Date__lte=to_date)

    cleared = defaultdict(lambda: ZERO)
    for row in qs.values('voucherType_id', 'VoucherNo').annotate(total=Sum('Amount')):
        key = _bill_key(
            row['voucherType_id'],
            row['VoucherNo'],
            is_opening=(row['voucherType_id'] == OPENING_VOUCHER_TYPE_ID),
        )
        cleared[key] += row['total'] or ZERO
    return cleared 

def _get_voucher_detail(voucher_type_name, voucher_no, is_opening=False):
    """Resolve Invoice No / PO No for one LedgerPosting row. Falls back to a
    generic INV-<id> label if no mapping is configured for that voucher type."""
    config = VOUCHER_DETAIL_MAP.get('Opening') if is_opening else VOUCHER_DETAIL_MAP.get(voucher_type_name)
    fallback_no = f"{voucher_no}"
    if not config:
        return fallback_no, '-'
    try:
        model = apps.get_model(config['app'], config['model'])
    except LookupError:
        return fallback_no, '-'

    obj = model.objects.filter(pk=voucher_no).first()
    if not obj:
        return fallback_no, '-'

    invoice_no = getattr(obj, config['invoice_field'], None) or fallback_no
    po_no = getattr(obj, config['po_field'], None) or '-'
    return invoice_no, po_no


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, '%Y-%m-%d').date()
 
 

def build_client_outstanding_data(customer_id=None, from_date=None, to_date=None):
    """
    Returns (customers, grand_totals).

    For every Sundry Debtor ledger:
      1. Bill-wise: amounts cleared via Receipt Bill Clearance are applied to
         the exact bill they were cleared against.
      2. On-account: any remaining credit (plain receipts, credit notes, etc.)
         is applied FIFO to the still-unpaid bills.
      3. Fully settled bills are dropped.

    Allocation always runs on full history up to to_date; from_date only
    limits which bills are displayed.
    """
    from_date = _parse_date(from_date)
    to_date = _parse_date(to_date)
    as_of = to_date or date.today()

    ledgers = LedgerCreation.objects.filter(groups_id=SUNDRY_DEBTOR_GROUP_ID).order_by('ledger_name')
    if customer_id:
        ledgers = ledgers.filter(pk=customer_id)

    customers = []
    grand_totals = {
        'invoice_amount': ZERO,
        'opening_amount': ZERO,
        'received_amount': ZERO,
        'balance_due': ZERO,
    }

    for ledger in ledgers:
        postings = LedgerPosting.objects.filter(ledger=ledger).select_related('VoucherType')
        if to_date:
            postings = postings.filter(date__lte=to_date)
        postings = postings.order_by('date', 'id')

        bills = []
        total_credit = ZERO
        for p in postings:
            if p.debit:
                bills.append(p)
            if p.credit:
                total_credit += p.credit

        cleared_map = _get_billwise_cleared(ledger.id, to_date)
        billwise_total = sum(cleared_map.values(), ZERO)

        # Credit not linked to any specific bill -> FIFO
        on_account = max(total_credit - billwise_total, ZERO)

        display_rows = []
        cumulative = ZERO
        inv_amt = ZERO
        opening_amt = ZERO
        total_debit_amt = ZERO
        total_credit_amt = ZERO

        for p in bills:
            debit = p.debit or ZERO

            # 1) bill-wise clearance (pop so a bill is only matched once)
            key = _bill_key(p.VoucherType_id, p.VoucherNo, p.IsOpening)
            billwise = min(cleared_map.pop(key, ZERO), debit)

            # 2) on-account credit, FIFO
            fifo = min(on_account, debit - billwise)
            on_account -= fifo

            applied = billwise + fifo
            outstanding = debit - applied

            if outstanding <= ZERO:
                continue  # fully settled
            if from_date and p.date < from_date:
                continue  # outside display range

            invoice_no, po_no = _get_voucher_detail(p.VoucherType.VoucherName, p.VoucherNo, p.IsOpening)
            cumulative += outstanding

            if p.IsOpening:
                opening_amt += outstanding
            else:
                inv_amt += outstanding

            total_debit_amt += debit
            total_credit_amt += applied

            display_rows.append({
                'type': 'OPENING' if p.IsOpening else p.VoucherType.VoucherName.upper(),
                'voucher_invoice_no': invoice_no,
                'po_no': po_no,
                'date': p.date,
                'age_days': (as_of - p.date).days,
                'debit': debit,
                'credit': applied,
                'outstanding': outstanding,
                'cumulative': cumulative,
            })

        if not display_rows:
            continue

        balance_due = inv_amt + opening_amt
        pdc_list, pdc_grand_credit = build_customer_pdc_list(ledger.id, balance_due)

        customers.append({
            'ledger': ledger,
            'bills': display_rows,
            'total_inv_amt': inv_amt,
            'total_opening_amt': opening_amt,
            'total_received_amt': total_credit_amt,   # credit applied to displayed bills
            'total_balance_amt': balance_due,
            'total_debit_amt': total_debit_amt,
            'total_credit_amt': total_credit_amt,
            'pdc_list': pdc_list,
            'pdc_grand_credit': pdc_grand_credit,
            'has_pdc': bool(pdc_list),
        })

        grand_totals['invoice_amount'] += inv_amt
        grand_totals['opening_amount'] += opening_amt
        grand_totals['received_amount'] += total_credit_amt
        grand_totals['balance_due'] += balance_due

    return customers, grand_totals

# def build_client_outstanding_data(customer_id=None, from_date=None, to_date=None):
#     """
#     Returns (customers, grand_totals).
 
#     For every Sundry Debtor ledger:
#       - pulls all LedgerPosting rows (optionally date-bounded)
#       - allocates total credits (receipts/credit notes) against debit bills
#         in date order (FIFO) — same philosophy as the existing aging report
#       - drops bills that are fully settled (outstanding <= 0)
#       - returns the remaining bills with a running cumulative balance
#     """
#     from_date = _parse_date(from_date)
#     to_date = _parse_date(to_date)
#     as_of = to_date or date.today()
 
#     ledgers = LedgerCreation.objects.filter(groups_id=SUNDRY_DEBTOR_GROUP_ID).order_by('ledger_name')
#     if customer_id:
#         ledgers = ledgers.filter(pk=customer_id)
 
#     customers = []
#     grand_totals = {
#         'invoice_amount': ZERO,
#         'opening_amount': ZERO,
#         'received_amount': ZERO,
#         'balance_due': ZERO,
#     }
 
#     for ledger in ledgers:
#         postings = LedgerPosting.objects.filter(ledger=ledger).select_related('VoucherType')
#         if from_date:
#             postings = postings.filter(date__gte=from_date)
#         if to_date:
#             postings = postings.filter(date__lte=to_date)
#         postings = postings.order_by('date', 'id')
 
#         bills = []
#         total_credit = ZERO
#         for p in postings:
#             if p.debit:
#                 bills.append(p)
#             if p.credit:
#                 total_credit += p.credit
 
#         remaining_credit = total_credit
#         display_rows = []
#         cumulative = ZERO
#         inv_amt = ZERO
#         opening_amt = ZERO
#         total_debit_amt = ZERO      #sum of debit for displayed bills only
#         total_credit_amt = ZERO
 
#         for p in bills:
#             debit = p.debit or ZERO
#             applied = min(remaining_credit, debit)
#             remaining_credit -= applied
#             outstanding = debit - applied
 
#             if outstanding <= ZERO:
#                 continue  # fully settled — don't show
 
#             invoice_no, po_no = _get_voucher_detail(p.VoucherType.VoucherName, p.VoucherNo, p.IsOpening)
#             cumulative += outstanding
 
#             if p.IsOpening:
#                 opening_amt += outstanding
#             else:
#                 inv_amt += outstanding

#             total_debit_amt += debit      
#             total_credit_amt += applied     
 
#             display_rows.append({
#                 'type': 'OPENING' if p.IsOpening else p.VoucherType.VoucherName.upper(),
#                 'voucher_invoice_no': invoice_no,
#                 'po_no': po_no,
#                 'date': p.date,
#                 'age_days': (as_of - p.date).days,
#                 'debit': debit,
#                 'credit': applied,
#                 'outstanding': outstanding,
#                 'cumulative': cumulative,
#             })
 
#         if not display_rows:
#             continue  # customer fully settled in this range — skip from list
 
#         balance_due = inv_amt + opening_amt
 
#         # build_customer_pdc_list(customer_id, opening_balance) -> (pdc_rows, pdc_grand_credit)
#         pdc_list, pdc_grand_credit = build_customer_pdc_list(ledger.id, balance_due)
 
#         customers.append({
#             'ledger': ledger,
#             'bills': display_rows,
#             'total_inv_amt': inv_amt,
#             'total_opening_amt': opening_amt,
#             'total_received_amt': total_credit,
#             'total_balance_amt': balance_due,
#             'total_debit_amt': total_debit_amt,     #use this for the "Total Debit" footer
#             'total_credit_amt': total_credit_amt, 
#             'pdc_list': pdc_list,
#             'pdc_grand_credit': pdc_grand_credit,
#             'has_pdc': bool(pdc_list),
#         })
 
#         grand_totals['invoice_amount'] += inv_amt
#         grand_totals['opening_amount'] += opening_amt
#         grand_totals['received_amount'] += total_credit
#         grand_totals['balance_due'] += balance_due
 
#     return customers, grand_totals

 
 
def new_client_outstanding_report(request):
    customer_id = request.GET.get('customer') or None
    from_date = request.GET.get('from_date') or None
    to_date = request.GET.get('to_date') or None
 
    customers, totals = build_client_outstanding_data(
        customer_id=customer_id, from_date=from_date, to_date=to_date
    )
 
    all_customers = LedgerCreation.objects.filter(
        groups_id=SUNDRY_DEBTOR_GROUP_ID
    ).order_by('ledger_name')
 
    context = {
        'customers': customers,
        'totals': totals,
        'all_customers': all_customers,
        'selected_customer': customer_id,
        'from_date': from_date or '',
        'to_date': to_date or '',
    }
    return render(request, 'new_client_outstanding_report.html', context)
 
def new_client_outstanding_pdf(request, ledger_id):
    """Per-customer PDF, reusing the existing PDF generator."""
    from_date = request.GET.get('from_date') or None
    to_date = request.GET.get('to_date') or None
 
    return create_client_outstanding_pdf(ledger_id, from_date, to_date)


#SUPPLIER OUTSTANDING     

SUNDRY_CREDITOR_GROUP_ID = 28
ZERO = Decimal('0.000')
 
# ---------------------------------------------------------------------------
# VoucherNo on LedgerPosting stores the PK of the actual voucher row. Fill in
# the real model/app/field names for whatever voucher types post to a Sundry
# Creditor ledger (purchase bills, opening balances, debit notes, etc.).
# ---------------------------------------------------------------------------
SUPPLIER_VOUCHER_DETAIL_MAP = {
    'Opening Voucher': {
        'app': 'accounts_app',
        'model': 'BillWiseOpening',
        'invoice_field': 'InvNo',
        'po_field': 'po_no',
    },
    'Purchase': {
        'app': 'item_master',
        'model': 'PurchaseMaster',
        'invoice_field': 'voucher_no',
        'po_field': None,  # no PO field for this voucher type
    },
    'Asset Purchase': {
        'app': 'asset_app',
        'model': 'AssetPurchase',
        'invoice_field': 'voucher_no',
        'po_field': None,  # no PO field for this voucher type
    },
}
 
 
 
def _get_supplier_voucher_detail(voucher_type_name, voucher_no, is_opening=False):
    config = SUPPLIER_VOUCHER_DETAIL_MAP.get('Opening Voucher') if is_opening else SUPPLIER_VOUCHER_DETAIL_MAP.get(voucher_type_name)
    fallback_no = f"{voucher_no}"
    if not config:
        return fallback_no, '-'
    try:
        model = apps.get_model(config['app'], config['model'])
    except LookupError:
        return fallback_no, '-'

    obj = model.objects.filter(pk=voucher_no).first()
    if not obj:
        return fallback_no, '-'

    invoice_no = getattr(obj, config['invoice_field'], None) or fallback_no
    po_no = '-'
    if config.get('po_field'):
        po_no = getattr(obj, config['po_field'], None) or '-'
    return invoice_no, po_no 
 
def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value
    return datetime.strptime(value, '%Y-%m-%d').date()
 
 
def build_supplier_outstanding_data(supplier_id=None, from_date=None, to_date=None):
    """
    Returns (suppliers, grand_totals).
 
    For every Sundry Creditor ledger:
      - pulls all LedgerPosting rows (optionally date-bounded)
      - allocates total debits (payments made) against credit-side bills
        in date order (FIFO)
      - drops bills that are fully settled (outstanding <= 0)
      - returns the remaining bills with a running cumulative balance
    """
    from_date = _parse_date(from_date)
    to_date = _parse_date(to_date)
    as_of = to_date or date.today()
 
    ledgers = LedgerCreation.objects.filter(groups_id=SUNDRY_CREDITOR_GROUP_ID).order_by('ledger_name')
    if supplier_id:
        ledgers = ledgers.filter(pk=supplier_id)
 
    suppliers = []
    grand_totals = {
        'purchase_amount': ZERO,
        'opening_amount': ZERO,
        'paid_amount': ZERO,
        'balance_due': ZERO,
    }
 
    for ledger in ledgers:
        postings = LedgerPosting.objects.filter(ledger=ledger).select_related('VoucherType')
        if from_date:
            postings = postings.filter(date__gte=from_date)
        if to_date:
            postings = postings.filter(date__lte=to_date)
        postings = postings.order_by('date', 'id')
 
        bills = []       # credit-side rows (what we owe), in date order
        total_debit = ZERO
 
        for p in postings:
            if p.credit:
                bills.append(p)
            if p.debit:
                total_debit += p.debit
 
        remaining_debit = total_debit
        display_rows = []
        cumulative = ZERO
        purchase_amt = ZERO
        opening_amt = ZERO
 
        for p in bills:
            credit = p.credit or ZERO
            applied = min(remaining_debit, credit)
            remaining_debit -= applied
            outstanding = credit - applied
 
            if outstanding <= ZERO:
                continue  # fully paid — don't show
 
            invoice_no, po_no = _get_supplier_voucher_detail(p.VoucherType.VoucherName, p.VoucherNo, p.IsOpening)
            cumulative += outstanding
 
            if p.IsOpening:
                opening_amt += outstanding
            else:
                purchase_amt += outstanding
 
            display_rows.append({
                'type': 'OPENING' if p.IsOpening else p.VoucherType.VoucherName.upper(),
                'voucher_invoice_no': invoice_no,
                'po_no': po_no,
                'date': p.date,
                'age_days': (as_of - p.date).days,
                'debit': applied,
                'credit': credit,
                'outstanding': outstanding,
                'cumulative': cumulative,
            })
 
        if not display_rows:
            continue  # supplier fully settled in this range — skip from list
 
        balance_due = purchase_amt + opening_amt
 
        pdc_list, pdc_grand_credit = build_supplier_pdc_list(ledger.id, balance_due)
 
        suppliers.append({
            'ledger': ledger,
            'bills': display_rows,
            'total_purchase_amt': purchase_amt,
            'total_opening_amt': opening_amt,
            'total_paid_amt': total_debit,
            'total_balance_amt': balance_due,
            'pdc_list': pdc_list,
            'pdc_grand_credit': pdc_grand_credit,
            'has_pdc': bool(pdc_list),
        })
 
        grand_totals['purchase_amount'] += purchase_amt
        grand_totals['opening_amount'] += opening_amt
        grand_totals['paid_amount'] += total_debit
        grand_totals['balance_due'] += balance_due
 
    return suppliers, grand_totals
 
 
def new_supplier_outstanding_report(request):
    supplier_id = request.GET.get('supplier') or None
    from_date = request.GET.get('from_date') or None
    to_date = request.GET.get('to_date') or None
 
    suppliers, totals = build_supplier_outstanding_data(
        supplier_id=supplier_id, from_date=from_date, to_date=to_date
    )
 
    all_suppliers = LedgerCreation.objects.filter(
        groups_id=SUNDRY_CREDITOR_GROUP_ID
    ).order_by('ledger_name')
 
    context = {
        'suppliers': suppliers,
        'totals': totals,
        'all_suppliers': all_suppliers,
        'selected_supplier': supplier_id,
        'from_date': from_date or '',
        'to_date': to_date or '',
    }
    return render(request, 'new_supplier_outstanding_report.html', context)
 
 
def new_supplier_outstanding_pdf(request, ledger_id):
    """Per-supplier PDF, reusing the existing PDF generator."""
    from_date = request.GET.get('from_date') or None
    to_date = request.GET.get('to_date') or None
 
    return create_supplier_outstanding_pdf(ledger_id, from_date, to_date)



# ---------------------------------------------------------------------------
# CLIENT PDC
# ---------------------------------------------------------------------------
def _maturity_status(cheque_date, today):
    """Badge text/class for how far the cheque is from maturity."""
    if not cheque_date:
        return '-', 'secondary'
    days = (cheque_date - today).days
    if days < 0:
        return f'Matured {abs(days)}d ago', 'danger'
    if days == 0:
        return 'Due today', 'warning'
    if days <= 7:
        return f'Due in {days}d', 'warning'
    return f'Due in {days}d', 'info'
 
 
def client_pdc_report(request):
    # Privilege check — same inline pattern as other report views:
    # if not (check_privilege(request, 'client_pdc_report', 'can_read')
    #         or check_admin_override(request)):
    #     return redirect('no_permission')
 
    customer_id = request.GET.get('customer') or None
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    today = date.today()
 
    ledgers = (
        LedgerCreation.objects
        .filter(groups_id=SUNDRY_DEBTOR_GROUP_ID)
        .order_by('ledger_name')
    )
    if customer_id:
        ledgers = ledgers.filter(pk=customer_id)
 
    # Outstanding per client, exactly as the Client Outstanding Report computes it
    outstanding_customers, _ = build_client_outstanding_data(customer_id=customer_id)
    outstanding_map = {c['ledger'].id: c['total_balance_amt'] for c in outstanding_customers}
 
    groups = []
    grand_total = ZERO
    total_count = 0
    matured_amount = ZERO
    due_week_amount = ZERO
 
    for ledger in ledgers:
        outstanding = outstanding_map.get(ledger.id, ZERO)
        rows, _ = build_customer_pdc_list(ledger.id, outstanding)
        if not rows:
            continue
 
        # Cheque-date filter on the helper's output. Running balance stays
        # correct because earlier PDCs were already deducted before filtering.
        if date_from or date_to:
            rows = [
                r for r in rows
                if (not date_from or (r['cheque_date'] and r['cheque_date'] >= date_from))
                and (not date_to or (r['cheque_date'] and r['cheque_date'] <= date_to))
            ]
            for i, r in enumerate(rows, start=1):
                r['sl_no'] = i
            if not rows:
                continue
 
        total = sum((r['credit'] for r in rows), ZERO)
 
        for r in rows:
            r['status_text'], r['status_class'] = _maturity_status(r['cheque_date'], today)
            if r['cheque_date']:
                days = (r['cheque_date'] - today).days
                if days <= 0:
                    matured_amount += r['credit']
                elif days <= 7:
                    due_week_amount += r['credit']
 
        groups.append({
            'ledger': ledger,
            'outstanding': outstanding,
            'rows': rows,
            'total': total,
            'balance_after': rows[-1]['balance'],
        })
        grand_total += total
        total_count += len(rows)
 
    context = {
        'groups': groups,
        'grand_total': grand_total,
        'total_count': total_count,
        'customer_count': len(groups),
        'matured_amount': matured_amount,
        'due_week_amount': due_week_amount,
        'all_customers': (
            LedgerCreation.objects
            .filter(groups_id=SUNDRY_DEBTOR_GROUP_ID)
            .order_by('ledger_name')
        ),
        'selected_customer': customer_id,
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'today': today,
    }
    return render(request, 'client_pdc_report.html', context)

    
# --------------------------------------------------------------------------- 
#SUPPLIER PDC


def supplier_pdc_report(request):
    # Privilege check — same inline pattern as other report views:
    # if not (check_privilege(request, 'supplier_pdc_report', 'can_read')
    #         or check_admin_override(request)):
    #     return redirect('no_permission')
 
    supplier_id = request.GET.get('supplier') or None
    date_from = _parse_date(request.GET.get('date_from'))
    date_to = _parse_date(request.GET.get('date_to'))
    today = date.today()
 
    ledgers = (
        LedgerCreation.objects
        .filter(groups_id=SUNDRY_CREDITOR_GROUP_ID)
        .order_by('ledger_name')
    )
    if supplier_id:
        ledgers = ledgers.filter(pk=supplier_id)
 
    # Payable per supplier, exactly as the Supplier Outstanding Report computes it
    outstanding_suppliers, _ = build_supplier_outstanding_data(supplier_id=supplier_id)
    outstanding_map = {s['ledger'].id: s['total_balance_amt'] for s in outstanding_suppliers}
 
    groups = []
    grand_total = ZERO
    total_count = 0
    matured_amount = ZERO
    due_week_amount = ZERO
 
    for ledger in ledgers:
        outstanding = outstanding_map.get(ledger.id, ZERO)
        rows, _ = build_supplier_pdc_list(ledger.id, outstanding)
        if not rows:
            continue
 
        # Cheque-date filter on the helper's output. Running balance stays
        # correct because earlier PDCs were already deducted before filtering.
        if date_from or date_to:
            rows = [
                r for r in rows
                if (not date_from or (r['cheque_date'] and r['cheque_date'] >= date_from))
                and (not date_to or (r['cheque_date'] and r['cheque_date'] <= date_to))
            ]
            for i, r in enumerate(rows, start=1):
                r['sl_no'] = i
            if not rows:
                continue
 
        total = sum((r['debit'] for r in rows), ZERO)
 
        for r in rows:
            r['status_text'], r['status_class'] = _maturity_status(r['cheque_date'], today)
            if r['cheque_date']:
                days = (r['cheque_date'] - today).days
                if days <= 0:
                    matured_amount += r['debit']
                elif days <= 7:
                    due_week_amount += r['debit']
 
        groups.append({
            'ledger': ledger,
            'outstanding': outstanding,
            'rows': rows,
            'total': total,
            'balance_after': rows[-1]['balance'],
        })
        grand_total += total
        total_count += len(rows)
 
    context = {
        'groups': groups,
        'grand_total': grand_total,
        'total_count': total_count,
        'supplier_count': len(groups),
        'matured_amount': matured_amount,
        'due_week_amount': due_week_amount,
        'all_suppliers': (
            LedgerCreation.objects
            .filter(groups_id=SUNDRY_CREDITOR_GROUP_ID)
            .order_by('ledger_name')
        ),
        'selected_supplier': supplier_id,
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
        'today': today,
    }
    return render(request, 'supplier_pdc_report.html', context)
 