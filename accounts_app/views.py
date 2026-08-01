from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from audit_app.common import log_activity
from fleet_app.common import *
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
from django.views.decorators.http import require_POST
import json
from item_master.models import *
from fleet_app.models import *
from django.db import connection
from django.db.models import Sum, Q
from accounts_app.common import check_privilege, check_admin_override
from django.views.decorators.http import require_http_methods

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

    ledgers = LedgerCreation.objects.all()
    return render(request, 'ledger.html', {
        'form': form,
        'ledgers': ledgers
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
    ledger.delete()
    # ❌ Remove Opening Balance Entry
    handle_opening_balance_ledger_posting(ledger, "delete")

    # ✅ DELETE LOG (before delete)
    log_activity(
        user=request.user,
        screen_name="Ledger Master",
        action_type="DELETE",
        remark=f"Ledger '{ledger.ledger_name}' deleted"
    )
    return redirect('accounts_app:ledger_view')




LOCAL_PAYMENT_MENU_ID = 9

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




def contra_create(request):
    """
    View to handle the creation of a new Contra entry.
    """
    if request.method == "POST":
        form = ContraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contra entry created successfully!")
            return redirect("accounts_app:contra_list")  # Replace with your desired redirect URL name
        else:
            messages.error(request, "Failed to create Contra entry. Please check the form for errors.")
    else:
        form = ContraForm()

    return render(request, "contra_create.html", {"form": form})


def list_contra(request):
    """
    View to display a list of all Contra entries.
    """
    contras = Contra.objects.all().order_by('-date')  # Orders by date in descending order
    return render(request, "contra_list.html", {"contras": contras})


def journal_list(request):
    journals = Journal.objects.all()
    return render(request, 'journal_list.html', {'journals': journals})

def journal_create(request):
    if request.method == 'POST':
        form = JournalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('accounts_app:journal_list')
    else:
        form = JournalForm()
    return render(request, 'journal_form.html', {'form': form})

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
        customer = get_object_or_404(LedgerCreation, pk=pk, groups_id=2, types='DR')
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
                groups_id=2,
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
        groups_id=2,
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
            form.save()
            messages.success(request, "Menu added successfully!")
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
            return redirect('accounts_app:menu_list_create')
    else:
        form = MenuForm(instance=menu)

    return render(request, 'menu_edit_form.html', {'form': form, 'menu': menu})


def menu_delete(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    menu.delete()
    messages.success(request, "Menu deleted successfully!")
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

def truncate_table(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')

def clear_transactions(request):
    if request.method in ["POST", "GET"]:
        try:
            tables = [
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
                
                
                
            ]

            for table in tables:
                truncate_table(table)

            # 🔹 Reset Ledger Opening Balance    
            LedgerCreation.objects.update(opening_balance=0)    

            # 🔹 Reset ALL Vehicle Status to 'Free'
            Vehicle.objects.update(status='1')

            messages.success(request, "All Transactions cleared and IDs reset.")
        except Exception as e:
            messages.error(request, f"Error clearing data: {e}")

        return redirect("fleet_app:fleet_home")

    messages.error(request, "Invalid request")
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
    Update the IsCleared status for a specific invoice based on payments received
    Returns: (invoice, was_updated, total_cleared, remaining)
    """
    try:
        from accounts_app.models import ReceiptBillDetails
        from fleet_app.models import Vouchers, Invoice
        
        invoice = Invoice.objects.get(pk=invoice_id)
        
        # Get total amount cleared from all receipt bill details
        total_cleared = ReceiptBillDetails.objects.filter(
            VoucherNo=invoice_id,
            voucherType__id=2  # Invoice voucher type
        ).aggregate(total=Sum('Amount'))['total']
        
        if total_cleared is None:
            total_cleared = Decimal('0.00')
        
        # Calculate remaining
        remaining = invoice.grand_total - total_cleared
        
        # Debug logging
        print(f"   📊 Invoice ID={invoice_id}, Voucher={invoice.voucher_no}")
        print(f"      Grand Total: {invoice.grand_total}")
        print(f"      Total Cleared: {total_cleared}")
        print(f"      Remaining: {remaining}")
        
        # Determine if cleared - invoice is cleared when remaining is 0 or negative
        should_be_cleared = remaining <= Decimal('0.01')
        
        print(f"      Should be cleared: {should_be_cleared}")
        print(f"      Current IsCleared: {invoice.IsCleared}")
        
        # Always update the status
        if invoice.IsCleared != should_be_cleared:
            invoice.IsCleared = should_be_cleared
            invoice.save()
            print(f"      ✅ IsCleared saved as: {invoice.IsCleared}")
            
            # Verify it was saved
            invoice.refresh_from_db()
            print(f"      ✅ Verified from DB: {invoice.IsCleared}")
            was_updated = True
        else:
            was_updated = False
        
        return invoice, was_updated, total_cleared, remaining
        
    except Exception as e:
        print(f"   ❌ Error in update_invoice_cleared_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, False, Decimal('0.00'), Decimal('0.00')
    
            
RECEIPT_BILL_CLEARANCE_MENU_ID = 11

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

                        # 🔄 If editing, delete existing receipt bill details
                        if pk:
                            # Get all old invoice/opening IDs before deletion for clearing status check
                            old_entries = ReceiptBillDetails.objects.filter(BillMaster=master).values('VoucherNo', 'voucherType__id')
                            old_invoice_ids = set()
                            old_opening_ids = set()
                            
                            for entry in old_entries:
                                if entry['voucherType__id'] == 2:  # Invoice
                                    old_invoice_ids.add(entry['VoucherNo'])
                                elif entry['voucherType__id'] == 12:  # BillWiseOpening
                                    old_opening_ids.add(entry['VoucherNo'])

                            deleted_details_count = ReceiptBillDetails.objects.filter(BillMaster=master).delete()[0]
                            print(f"🗑️ Deleted {deleted_details_count} existing receipt bill detail(s)")

                        # Now save formset with the master instance
                        formset.instance = master
                        details = formset.save(commit=False)

                        # Track invoices and openings for clearing status update
                        invoices_to_check = set()
                        openings_to_check = set()

                        # If editing, add old IDs to check for updated clearing status
                        if pk:
                            invoices_to_check.update(old_invoice_ids)
                            openings_to_check.update(old_opening_ids)
                        
                        for detail in details:
                            # Skip if amount is zero or None
                            if not detail.Amount or detail.Amount <= 0:
                                print(f"   ⏭️ Skipping detail with zero/empty amount for VoucherNo={detail.VoucherNo}")
                                continue
                            
                            detail.BillMaster = master
                            # Set VoucherType from the form data
                            voucher_type_id = detail.voucherType if isinstance(detail.voucherType, int) else detail.voucherType.id
                            detail.voucherType = Vouchers.objects.get(pk=voucher_type_id)
                            
                            # Save current amount
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
                            
                            # Track this entry for clearing check
                            if detail.voucherType.id == 2:  # Invoice
                                invoices_to_check.add(detail.VoucherNo)
                            elif detail.voucherType.id == 12:  # BillWiseOpening
                                openings_to_check.add(detail.VoucherNo)
                        
                        # Check and update IsCleared status for each invoice
                        print("\n🔍 Starting invoice status update...")
                        for invoice_id in invoices_to_check:
                            print(f"\n--- Processing Invoice ID: {invoice_id} ---")
                            
                            try:
                                invoice = Invoice.objects.get(pk=invoice_id)
                                print(f"✓ Invoice found: {invoice.voucher_no}")
                                print(f"  Before update - IsCleared: {invoice.IsCleared}")
                                
                                # Calculate total cleared
                                total_paid = sum(
                                    ReceiptBillDetails.objects.filter(
                                        VoucherNo=invoice_id,
                                        voucherType__id=2  # Invoice voucher type
                                    ).values_list('Amount', flat=True)
                                ) or Decimal('0.00')
                                
                                print(f"  Grand Total: {invoice.grand_total}")
                                print(f"  Total Cleared: {total_paid}")
                                
                                remaining = invoice.grand_total - total_paid
                                print(f"  Remaining: {remaining}")
                                
                                should_be_cleared = abs(remaining) <= Decimal('0.01')
                                print(f"  Should be cleared: {should_be_cleared}")
                                
                                if invoice.IsCleared != should_be_cleared:
                                    print(f"  🔄 Updating IsCleared from {invoice.IsCleared} to {should_be_cleared}")
                                    
                                    # Use update() to bypass the save() method entirely
                                    Invoice.objects.filter(pk=invoice_id).update(IsCleared=should_be_cleared)
                                    print(f"  💾 Direct update() executed")
                                    
                                    # Verify
                                    invoice.refresh_from_db()
                                    print(f"  ✅ After update - IsCleared: {invoice.IsCleared}")
                                    
                                    if invoice.IsCleared == should_be_cleared:
                                        print(f"  ✅✅ SUCCESS! Invoice {invoice.voucher_no} updated correctly")
                                    else:
                                        print(f"  ❌❌ FAILED! Database value didn't change!")
                                else:
                                    print(f"  ℹ️ No update needed, already at correct value")
                            
                            except Invoice.DoesNotExist:
                                print(f"  ⚠️ Invoice ID {invoice_id} not found")
                            except Exception as e:
                                print(f"  ❌ Error: {str(e)}")
                                import traceback
                                traceback.print_exc()
                        
                        print("\n✅ Finished processing all invoices")
                        
                        # Check and update IsCleared status for each BillWiseOpening
                        print("\n🔍 Starting BillWiseOpening status update...")
                        for opening_id in openings_to_check:
                            print(f"\n--- Processing Opening ID: {opening_id} ---")
                            update_billwise_opening_cleared_status(opening_id)
                        
                        print("\n✅ Finished processing all openings\n")

                    print("=== RECEIPT BILL SAVE DEBUG END ===\n")
                    
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
                        )
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
    
def update_billwise_opening_cleared_status(opening_id):
    """
    Update the IsCleared status for a specific BillWiseOpening based on payments received
    Returns: (opening, was_updated, total_cleared, remaining)
    """
    try:
        opening = BillWiseOpening.objects.get(pk=opening_id)
        
        # Get total amount cleared from all receipt bill details
        # ✅ FIXED: Use voucherType__id=12 for BillWiseOpening (Opening)
        total_cleared = ReceiptBillDetails.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=12  # BillWiseOpening voucher type (Opening)
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.00')
        
        # Calculate remaining (use InvBalance instead of Amount)
        remaining = opening.InvBalance - total_cleared
        
        # Debug logging
        print(f"   📊 Opening ID={opening_id}, InvNo={opening.InvNo}")
        print(f"      Invoice Balance: {opening.InvBalance}")
        print(f"      Total Cleared: {total_cleared}")
        print(f"      Remaining: {remaining}")
        
        # Determine if cleared - opening is cleared when remaining is 0 or negative
        should_be_cleared = remaining <= Decimal('0.01')
        
        print(f"      Should be cleared: {should_be_cleared}")
        print(f"      Current IsCleared: {opening.IsCleared}")
        
        # Update the status
        if opening.IsCleared != should_be_cleared:
            print(f"      🔄 Updating IsCleared from {opening.IsCleared} to {should_be_cleared}")
            
            # Use update() to bypass the save() method entirely
            BillWiseOpening.objects.filter(pk=opening_id).update(IsCleared=should_be_cleared)
            print(f"      💾 Direct update() executed")
            
            # Verify
            opening.refresh_from_db()
            print(f"      ✅ After update - IsCleared: {opening.IsCleared}")
            
            if opening.IsCleared == should_be_cleared:
                print(f"      ✅✅ SUCCESS! Opening {opening.InvNo} updated correctly")
            else:
                print(f"      ❌❌ FAILED! Database value didn't change!")
            was_updated = True
        else:
            print(f"      ℹ️ No update needed, already at correct value")
            was_updated = False
        
        return opening, was_updated, total_cleared, remaining
        
    except Exception as e:
        print(f"   ❌ Error in update_billwise_opening_cleared_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, False, Decimal('0.00'), Decimal('0.00')
    
    
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

            # 🔹 STEP 1: Capture affected invoices & openings BEFORE delete
            details = ReceiptBillDetails.objects.filter(BillMaster=receipt_bill)\
                .values('VoucherNo', 'voucherType__id')

            invoice_ids = set()
            opening_ids = set()

            for d in details:
                if d['voucherType__id'] == 2:        # Invoice
                    invoice_ids.add(d['VoucherNo'])
                elif d['voucherType__id'] == 12:     # BillWiseOpening
                    opening_ids.add(d['VoucherNo'])

            # 🔹 STEP 2: Delete Ledger Postings
            delete_ledger_postings_for_receiptbillclr(receipt_bill)

            # 🔹 STEP 3: Delete Receipt Details & Master
            ReceiptBillDetails.objects.filter(BillMaster=receipt_bill).delete()
            receipt_bill.delete()

            # 🔹 STEP 4: Recalculate Invoice IsCleared
            for invoice_id in invoice_ids:
                update_invoice_cleared_status(invoice_id)

            # 🔹 STEP 5: Recalculate BillWiseOpening IsCleared
            for opening_id in opening_ids:
                update_billwise_opening_cleared_status(opening_id)

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
def get_customer_invoices_and_openings(request):
    """
    Get both pending invoices and bill-wise openings for a customer
    """
    customer_id = request.GET.get('customer_id')
    
    print(f"\n=== GET CUSTOMER INVOICES AND OPENINGS ===")
    print(f"Customer ID: {customer_id}")
    
    if not customer_id:
        print("No customer_id provided")
        return JsonResponse({'invoices': [], 'openings': []})
    
    invoice_data = []
    opening_data = []
    
    # ✅ Get Not Cleared Invoices
    invoices = Invoice.objects.filter(customer_id=customer_id, IsCleared=False)
    print(f"Found {invoices.count()} not cleared invoices")
    
    for inv in invoices:
        # Calculate amount already cleared
        total_paid = sum(
            ReceiptBillDetails.objects.filter(
                VoucherNo=inv.id,
                voucherType__id=2  # Invoice voucher type
            ).values_list('Amount', flat=True)
        ) or 0

        balance = float(inv.grand_total) - float(total_paid)

        if balance > 0:  # Only include if there's still something to receive
            invoice_data.append({
                'type': 'invoice',
                'invoice_id': inv.id,
                'voucher_no': inv.voucher_no,
                'date': inv.date.strftime('%Y-%m-%d'),
                'customer': inv.customer.ledger_name,
                'grand_total': float(inv.grand_total),
                'amount_cleared': float(total_paid),
                'receivable_balance': balance,
            })
    
    # ✅ Get Not Cleared BillWiseOpenings
    # Filter by ledger (customer ledger) and VoucherType = 2 (Invoice)
    try:
        from accounts_app.models import LedgerCreation
        customer_ledger = LedgerCreation.objects.get(pk=customer_id)
        
        openings = BillWiseOpening.objects.filter(
            ledger=customer_ledger,
            IsCleared=False,
            voucherType__id=2  # Invoice voucher type
        )
        
        print(f"Found {openings.count()} not cleared bill-wise openings")
        
        for opening in openings:
            # Calculate amount already cleared
            total_paid = sum(
                ReceiptBillDetails.objects.filter(
                    VoucherNo=opening.id,
                    voucherType__id=12 # BillWiseOpening voucher type
                ).values_list('Amount', flat=True)
            ) or 0
            
            balance = float(opening.InvBalance) - float(total_paid)
            
            if balance > 0:  # Only include if there's still something to receive
                opening_data.append({
                    'type': 'opening',
                    'opening_id': opening.id,
                    'voucher_no': opening.InvNo,
                    'date': opening.InvDate.strftime('%Y-%m-%d'),
                    'customer': opening.ledger.ledger_name,
                    'grand_total': float(opening.InvBalance),  # ✅ Changed from InvAmount to InvBalance
                    'amount_cleared': float(total_paid),
                    'receivable_balance': balance,
                })
    except Exception as e:
        print(f"Error fetching openings: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"Returning {len(invoice_data)} invoices and {len(opening_data)} openings")
    print(f"Invoice data: {invoice_data}")
    print(f"Opening data: {opening_data}")
    print("=== END GET CUSTOMER INVOICES AND OPENINGS ===\n")
    
    return JsonResponse({
        'invoices': invoice_data,
        'openings': opening_data
    })


#Payment Bill Clearance
def update_hire_cleared_status(hire_id):
    """
    Updates IsCleared for a FleetHire based on payment bills made.
    Returns: (hire, was_updated, total_cleared, remaining)
    """
    try:
        hire = FleetHire.objects.get(pk=hire_id)

        total_cleared = PaymentBillDetails.objects.filter(
            VoucherNo=hire_id,
            voucherType__id=1  # VoucherType for Hire
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.00')

        remaining = hire.grand_total - total_cleared

        print(f"📊 Hire ID={hire_id}, Voucher={hire.voucher_no}")
        print(f"   Grand Total: {hire.grand_total}")
        print(f"   Total Cleared: {total_cleared}")
        print(f"   Remaining: {remaining}")

        should_be_cleared = remaining <= Decimal('0.01')

        if hire.IsCleared != should_be_cleared:
            hire.IsCleared = should_be_cleared
            hire.save(update_fields=['IsCleared'])
            print(f"✅ Updated IsCleared = {hire.IsCleared}")
            was_updated = True
        else:
            was_updated = False

        return hire, was_updated, total_cleared, remaining

    except Exception as e:
        print(f"❌ Error in update_hire_cleared_status: {e}")
        import traceback
        traceback.print_exc()
        return None, False, Decimal('0.00'), Decimal('0.00')


# ================================
# 🔹 CREATE PAYMENT BILL CLEARANCE
# ================================
# 1. UPDATE create_PaymentBillClearance VIEW

def update_billwise_opening_cleared_status_payment(opening_id):
    """
    Update the IsCleared status for a specific BillWiseOpening based on payments made
    Returns: (opening, was_updated, total_cleared, remaining)
    """
    try:
        opening = BillWiseOpening.objects.get(pk=opening_id)
        
        # Get total amount cleared from all payment bill details
        # ✅ VoucherType__id=12 for BillWiseOpening (Opening) - same for both receipts and payments
        total_cleared = PaymentBillDetails.objects.filter(
            VoucherNo=opening_id,
            voucherType__id=12  # BillWiseOpening voucher type (Opening)
        ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.00')
        
        # Calculate remaining (use InvBalance instead of Amount)
        remaining = opening.InvBalance - total_cleared
        
        # Debug logging
        print(f"   📊 Opening ID={opening_id}, InvNo={opening.InvNo}")
        print(f"      Invoice Balance: {opening.InvBalance}")
        print(f"      Total Cleared: {total_cleared}")
        print(f"      Remaining: {remaining}")
        
        # Determine if cleared - opening is cleared when remaining is 0 or negative
        should_be_cleared = remaining <= Decimal('0.01')
        
        print(f"      Should be cleared: {should_be_cleared}")
        print(f"      Current IsCleared: {opening.IsCleared}")
        
        # Update the status
        if opening.IsCleared != should_be_cleared:
            print(f"      🔄 Updating IsCleared from {opening.IsCleared} to {should_be_cleared}")
            
            # Use update() to bypass the save() method entirely
            BillWiseOpening.objects.filter(pk=opening_id).update(IsCleared=should_be_cleared)
            print(f"      💾 Direct update() executed")
            
            # Verify
            opening.refresh_from_db()
            print(f"      ✅ After update - IsCleared: {opening.IsCleared}")
            
            if opening.IsCleared == should_be_cleared:
                print(f"      ✅✅ SUCCESS! Opening {opening.InvNo} updated correctly")
            else:
                print(f"      ❌❌ FAILED! Database value didn't change!")
            was_updated = True
        else:
            print(f"      ℹ️ No update needed, already at correct value")
            was_updated = False
        
        return opening, was_updated, total_cleared, remaining
        
    except Exception as e:
        print(f"   ❌ Error in update_billwise_opening_cleared_status_payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, False, Decimal('0.00'), Decimal('0.00')

# ================================
# 🔹 CREATE PAYMENT BILL CLEARANCE
# ================================
PAYMENT_BILL_CLEARANCE_MENU_ID = 12

def create_PaymentBillClearance(request, pk=None):
    
    # Check if we're editing an existing payment bill
    payment_bill_instance = None
    if pk:
        payment_bill_instance = get_object_or_404(PaymentBillMaster, pk=pk)

    if request.method == 'POST':
        
        try:  # ✅ WRAP IN TRY-CATCH
            print("\n=== PAYMENT BILL SAVE DEBUG START ===")
            print("POST DATA:", request.POST)

            # 🔐 PRIVILEGE CHECK
            action = "can_edit" if pk else "can_add"

            if not check_privilege(request.user, PAYMENT_BILL_CLEARANCE_MENU_ID, action):
                is_admin_ok, msg = check_admin_override(request)
                if not is_admin_ok:
                    return JsonResponse({
                        "admin_required": True,
                        "message": msg
                    }, status=403)

            master_form = PaymentBillMasterForm(request.POST, instance=payment_bill_instance)
            formset = PaymentBillDetailsFormSet(request.POST, prefix='form', instance=payment_bill_instance)

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
                        
                        # ✅ Set Cleared field based on IsPDC
                        if master.IsPDC:
                            master.Cleared = "Not Cleared"
                        else:
                            master.Cleared = "Cleared"
                        
                        master.save()
                        print(f"✅ Master saved: ID={master.id}, TotalAmount={master.TotalAmount}, Cleared={master.Cleared}")

                        # Delete old ledger postings when editing
                        if pk:
                            deleted_count = LedgerPosting.objects.filter(
                                voucherType_id=6,
                                VoucherNo=master.id
                            ).delete()[0]
                            print(f"🗑️ Deleted {deleted_count} old ledger posting(s)")

                        # ✅ Only call LedgerPosting if NOT "Not Cleared"
                        if master.Cleared != "Not Cleared":
                            create_ledger_postings_for_paymentbillclr(master)
                            print("✅ Ledger posting created")
                        else:
                            print("⏸️ Ledger posting skipped - Payment Bill is Not Cleared (PDC)")

                        # Delete old details when editing
                        if pk:
                            # Get all old hire/opening IDs before deletion for clearing status check
                            old_entries = PaymentBillDetails.objects.filter(BillMaster=master).values('VoucherNo', 'voucherType__id')
                            old_hire_ids = set()
                            old_opening_ids = set()
                            
                            for entry in old_entries:
                                if entry['voucherType__id'] == 1:  # Hire
                                    old_hire_ids.add(entry['VoucherNo'])
                                elif entry['voucherType__id'] == 12:  # BillWiseOpening
                                    old_opening_ids.add(entry['VoucherNo'])

                            PaymentBillDetails.objects.filter(BillMaster=master).delete()
                            print(f"🗑️ Deleted old payment bill details")

                        # Save details
                        formset.instance = master
                        details = formset.save(commit=False)
                        
                        hires_to_check = set()
                        openings_to_check = set()

                        # If editing, add old IDs to check for updated clearing status
                        if pk:
                            hires_to_check.update(old_hire_ids)
                            openings_to_check.update(old_opening_ids)

                        for detail in details:
                            if not detail.Amount or detail.Amount <= 0:
                                print(f"⏭️ Skipping detail with zero/empty amount for VoucherNo={detail.VoucherNo}")
                                continue

                            detail.BillMaster = master
                            voucher_type_id = detail.voucherType if isinstance(detail.voucherType, int) else detail.voucherType.id
                            detail.voucherType = Vouchers.objects.get(pk=voucher_type_id)

                            # Save current amount
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
                            
                            # Track this entry for clearing check
                            if detail.voucherType.id == 1:  # Hire
                                hires_to_check.add(detail.VoucherNo)
                            elif detail.voucherType.id == 12:  # BillWiseOpening
                                openings_to_check.add(detail.VoucherNo)

                        # 🔍 Update each hire's cleared status
                        print("\n🔍 Starting hire status update...")
                        for hire_id in hires_to_check:
                            print(f"\n--- Processing Hire ID: {hire_id} ---")
                            try:
                                hire = FleetHire.objects.get(pk=hire_id)
                                print(f"✓ Hire found: {hire.voucher_no}")
                                print(f"  Before update - IsCleared: {hire.IsCleared}")

                                payment_details = PaymentBillDetails.objects.filter(
                                    VoucherNo=hire_id,
                                    voucherType__id=1  # Hire voucher type
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
                                    print(f"ℹ️ No update needed, already correct value")

                            except FleetHire.DoesNotExist:
                                print(f"⚠️ Hire ID {hire_id} not found")
                            except Exception as e:
                                print(f"❌ Error: {str(e)}")
                                import traceback
                                traceback.print_exc()

                        print("\n✅ Finished processing all hires")

                        # Check and update IsCleared status for each BillWiseOpening
                        print("\n🔍 Starting BillWiseOpening status update...")
                        for opening_id in openings_to_check:
                            print(f"\n--- Processing Opening ID: {opening_id} ---")
                            update_billwise_opening_cleared_status_payment(opening_id)
                        
                        print("\n✅ Finished processing all openings\n")

                    print("=== PAYMENT BILL SAVE DEBUG END ===\n")
                    
                    # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
                    log_activity(
                        user=request.user,
                        screen_name="Payment Bill Clearance",
                        action_type="UPDATE" if pk else "CREATE",
                        remark=(
                            f"Payment Bill Clearance #{master.id} updated "
                            f"with total {master.TotalAmount:.3f}"
                            if pk else
                            f"Payment Bill Clearance #{master.id} created "
                            f"with total {master.TotalAmount:.3f}"
                        )
                    )

                    
                    # ✅ RETURN JSON RESPONSE
                    return JsonResponse({
                        "success": True,
                        "message": (
                            "Payment bill updated successfully!"
                            if pk else
                            "Payment bill saved successfully!"
                        )
                    })

                except Exception as e:
                    print("❌ Exception during save:", str(e))
                    import traceback
                    traceback.print_exc()
                    
                    return JsonResponse({
                        "success": False,
                        "message": f"Error saving payment bill: {str(e)}"
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
        # GET request
        master_form = PaymentBillMasterForm(instance=payment_bill_instance)
        formset = PaymentBillDetailsFormSet(prefix='form', instance=payment_bill_instance)

    return render(request, 'create_PaymentBillClearance.html', {
        'master_form': master_form,
        'formset': formset,
        'edit_mode': pk is not None,
        'payment_bill_instance': payment_bill_instance,
    })


def get_supplier_hires_and_openings(request):
    """
    Get both FleetHires and BillWiseOpenings for a supplier
    Similar to get_customer_invoices_and_openings but for payments
    """
    supplier_id = request.GET.get('supplier_id')
    data = {'hires': [], 'openings': []}

    if supplier_id:
        # Get Hires (VoucherType 1)
        hires = FleetHire.objects.filter(supplier_id=supplier_id, IsCleared=False)
        for hire in hires:
            total_paid = PaymentBillDetails.objects.filter(
                VoucherNo=hire.id,
                voucherType__id=1  # Hire voucher type
            ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.00')

            balance = hire.grand_total - total_paid

            data['hires'].append({
                'type': 'hire',
                'hire_id': hire.id,
                'voucher_no': hire.voucher_no,
                'date': hire.date.strftime('%Y-%m-%d'),
                'supplier': hire.supplier.ledger_name,
                'grand_total': float(hire.grand_total),
                'amount_cleared': float(total_paid),
                'payable_balance': float(balance),
            })

        # Get BillWiseOpenings (VoucherType 1 for supplier/payments)
        openings = BillWiseOpening.objects.filter(
            ledger_id=supplier_id, 
            IsCleared=False,
            voucherType__id=1  # VoucherType 1 for payment openings
        )
        
        for opening in openings:
            total_paid = PaymentBillDetails.objects.filter(
                VoucherNo=opening.id,
                voucherType__id=12  # BillWiseOpening voucher type
            ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.00')

            balance = opening.InvBalance - total_paid

            data['openings'].append({
                'type': 'opening',
                'opening_id': opening.id,
                'voucher_no': opening.InvNo,
                'date': opening.InvDate.strftime('%Y-%m-%d'),
                'supplier': opening.ledger.ledger_name,
                'grand_total': float(opening.InvBalance),
                'amount_cleared': float(total_paid),
                'payable_balance': float(balance),
            })

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

            for d in details:
                if d['voucherType__id'] == 1:   # Hire
                    hire_ids.add(d['VoucherNo'])
                elif d['voucherType__id'] == 12:  # BillWiseOpening
                    opening_ids.add(d['VoucherNo'])

            # ✅ Delete ledger postings
            delete_ledger_postings_for_paymentbillclr(payment_bill)

            # ✅ Delete details
            PaymentBillDetails.objects.filter(BillMaster=payment_bill).delete()

            # ✅ Delete master
            payment_bill.delete()

            # 🔥 Recalculate Hires
            for hire_id in hire_ids:
                update_hire_cleared_status(hire_id)

            # 🔥 Recalculate Openings
            for opening_id in opening_ids:
                update_billwise_opening_cleared_status_payment(opening_id)

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


# def payment_create(request, pk=None):
   
#     # 1. Fetch existing instance if pk is provided (Edit Mode)

#     if pk:
#         payment_instance = get_object_or_404(PaymentMaster, pk=pk)
#         is_edit = True
#     else:
#         payment_instance = None
#         is_edit = False

#     if request.method == "POST":
#         # Pass the instance to the form if editing
#         form = PaymentMasterForm(request.POST, instance=payment_instance)
        
#         # Note: We do NOT pass 'instance' to formset here because your JS generates 
#         # fresh rows without IDs. We will handle the relationships manually.
#         formset = PaymentDetailsFormSet(request.POST)

#         if form.is_valid() and formset.is_valid():
#             try:
#                 with transaction.atomic():
#                     # --- STEP 1: CLEANUP OLD DATA (If Edit) ---
#                     if is_edit:
#                         # A. Find IDs of existing details to clean up LedgerPosting
#                         old_detail_ids = list(payment_instance.details.values_list('id', flat=True))
                        
#                         # B. Delete existing Ledger Postings (Master + Details)
#                         # Assumes VoucherType ID 3 is for Payment
#                         LedgerPosting.objects.filter(
#                             VoucherType_id=3
#                         ).filter(
#                             Q(VoucherNo=payment_instance.id) |  # The Master Entry
#                             Q(VoucherNo__in=old_detail_ids)     # The Detail Entries
#                         ).delete()

#                         # C. Delete old Payment Details (We recreate them from the formset)
#                         payment_instance.details.all().delete()

#                     # --- STEP 2: SAVE MASTER FIRST ---
#                     master = form.save(commit=False)
                    
#                     # Set Cleared field based on IsPDC
#                     if master.IsPDC:
#                         master.Cleared = "Not Cleared"
#                     else:
#                         master.Cleared = "Cleared"
                    
#                     # IMPORTANT: Save master BEFORE creating details
#                     master.save()
#                     print(f"✅ Master saved with ID: {master.id}")

#                     # --- STEP 3: SAVE DETAILS ---
#                     new_details = []
#                     for idx, detail_form in enumerate(formset):
#                         if detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
#                             # Get the cleaned data
#                             ledger = detail_form.cleaned_data.get('Ledger')
#                             amount = detail_form.cleaned_data.get('Amount')
#                             description = detail_form.cleaned_data.get('Description', '')
                            
#                             print(f"Processing detail {idx}: Ledger={ledger}, Amount={amount}")
                            
#                             # Create detail instance manually to ensure proper linking
#                             detail = PaymentDetails()
#                             detail.Ledger = ledger
#                             detail.Amount = amount
#                             detail.Description = description
                            
#                             # Link to master - TRY BOTH POSSIBLE FIELD NAMES
#                             # Check your PaymentDetails model to see which field name is correct
#                             if hasattr(detail, 'PaymentMaster'):
#                                 detail.PaymentMaster = master
#                             elif hasattr(detail, 'Payment'):
#                                 detail.Payment = master
#                             elif hasattr(detail, 'payment'):
#                                 detail.payment = master
#                             elif hasattr(detail, 'payment_master'):
#                                 detail.payment_master = master
#                             else:
#                                 # Find the actual field name
#                                 for field in detail._meta.fields:
#                                     if field.related_model == PaymentMaster:
#                                         setattr(detail, field.name, master)
#                                         print(f"Found FK field: {field.name}")
#                                         break
                            
#                             detail.save()
#                             new_details.append(detail)
#                             print(f"✅ Detail {idx} saved with ID: {detail.id}")

#                     if not new_details:
#                         raise ValueError("No payment details were saved. Please add at least one detail.")

#                     # --- STEP 4: UPDATE MASTER TOTAL ---
#                     total_amount = sum(d.Amount for d in new_details if d.Amount)
#                     master.TotalAmount = total_amount
#                     master.save()
#                     print(f"✅ Master total updated: {total_amount}")

#                     # --- STEP 5: LEDGER POSTING ---
#                     # Only create if Cleared
#                     if master.Cleared != "Not Cleared":
#                         create_ledger_postings_for_payment(master)
#                         print("✅ Ledger posting created/updated")
#                     else:
#                         print("⏸️ Ledger posting skipped - Payment is Not Cleared (PDC)")

#                     action = "updated" if is_edit else "created"
#                     messages.success(request, f"Payment voucher {action} successfully!")
#                     return redirect("accounts_app:list_payment")

#             except Exception as e:
#                 import traceback
#                 print(f"❌ Error saving payment: {e}")
#                 print(traceback.format_exc())
#                 messages.error(request, f"Error saving payment: {e}")
#         else:
#             print("❌ Form validation failed")
#             print("Form errors:", form.errors)
#             print("Formset errors:", formset.errors)
#             messages.error(request, "Please correct the errors below.")

#     else:
#         # GET Request
#         form = PaymentMasterForm(instance=payment_instance)
#         formset = PaymentDetailsFormSet() # Empty formset, we populate via JS
    
#     # Prepare existing details for JavaScript if editing
#     existing_details_data = []
#     if is_edit and payment_instance:
#         for detail in payment_instance.details.all():
#             existing_details_data.append({
#                 'ledger_id': detail.Ledger.id,
#                 'ledger_name': str(detail.Ledger),
#                 'amount': str(detail.Amount),
#                 'desc': detail.Desc or ""
#             })

#     return render(request, "payment_create.html", {
#         "form": form,
#         "formset": formset,
#         "is_edit_mode": is_edit,
#         "existing_details_json": json.dumps(existing_details_data),
#     })    
    

PAYMENT_MENU_ID = 8

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

            form = PaymentMasterForm(request.POST, instance=payment_instance)
            formset = PaymentDetailsFormSet(request.POST)

            if form.is_valid() and formset.is_valid():
                try:
                    with transaction.atomic():
                        # --- CLEANUP OLD DATA (If Edit) ---
                        if is_edit:
                            old_detail_ids = list(payment_instance.details.values_list('id', flat=True))
                            
                            LedgerPosting.objects.filter(
                                VoucherType_id=3
                            ).filter(
                                Q(VoucherNo=payment_instance.id) |
                                Q(VoucherNo__in=old_detail_ids)
                            ).delete()

                            payment_instance.details.all().delete()

                        # --- SAVE MASTER ---
                        master = form.save(commit=False)
                        
                        if master.IsPDC:
                            master.Cleared = "Not Cleared"
                        else:
                            master.Cleared = "Cleared"
                        
                        master.save()

                        # --- SAVE DETAILS ---
                        new_details = []
                        for idx, detail_form in enumerate(formset):
                            if detail_form.cleaned_data and not detail_form.cleaned_data.get('DELETE', False):
                                ledger = detail_form.cleaned_data.get('Ledger')
                                amount = detail_form.cleaned_data.get('Amount')
                                vehicle = detail_form.cleaned_data.get('Vehicle')
                                description = detail_form.cleaned_data.get('Description', '')
                                
                                detail = PaymentDetails()
                                detail.Ledger = ledger
                                detail.Amount = amount
                                detail.Vehicle = vehicle
                                detail.Desc = description
                                
                                # Find FK field
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

                        if not new_details:
                            raise ValueError("No payment details were saved. Please add at least one detail.")

                        # --- UPDATE MASTER TOTAL ---
                        total_amount = sum(d.Amount for d in new_details if d.Amount)
                        master.TotalAmount = total_amount
                        master.save()

                        # --- LEDGER POSTING ---
                        if master.Cleared != "Not Cleared":
                            create_ledger_postings_for_payment(master)
                        
                        # ✅ UPDATE VEHICLE PROFIT & LOSS
                        update_vehicle_profit_loss_for_payment(master)
                        
                    # ✅ AUDIT LOG — ONLY AFTER SUCCESSFUL COMMIT
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
                            "Payment created successfully!"
                        )
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
    
    existing_details_data = []
    if is_edit and payment_instance:
        for detail in payment_instance.details.all():
            existing_details_data.append({
                'ledger_id': detail.Ledger.id,
                'ledger_name': str(detail.Ledger),
                'amount': str(detail.Amount),
                'vehicle_id': detail.Vehicle.id if detail.Vehicle else '',
                'vehicle_name': str(detail.Vehicle) if detail.Vehicle else '',
                'desc': detail.Desc or ""
            })

    return render(request, "payment_create.html", {
        "form": form,
        "formset": formset,
        "is_edit_mode": is_edit,
        "existing_details_json": json.dumps(existing_details_data),
        "all_vehicles": Vehicle.objects.all(),
    })


    
# def receipt_create(request, pk=None):
#     """
#     Create or Edit Receipt
#     """
    
#     if pk:
#         receipt_instance = get_object_or_404(ReceiptMaster, pk=pk)
#         is_edit = True
#     else:
#         receipt_instance = None
#         is_edit = False

#     if request.method == "POST":
#         form = ReceiptMasterForm(request.POST, instance=receipt_instance)
#         formset = ReceiptDetailsFormSet(request.POST)

#         if form.is_valid() and formset.is_valid():
#             try:
#                 with transaction.atomic():

#                     # 🔴 STEP 1: CLEAN OLD DATA (EDIT MODE)
#                     if is_edit:
#                         # Delete ALL ledger postings of this receipt
#                         LedgerPosting.objects.filter(
#                             VoucherType_id=4,   # Receipt
#                             VoucherNo=receipt_instance.id
#                         ).delete()

#                         # Delete old receipt details
#                         receipt_instance.details.all().delete()

#                     # 🟢 STEP 2: SAVE MASTER
#                     master = form.save(commit=False)

#                     if master.IsPDC:
#                         master.Cleared = "Not Cleared"
#                     else:
#                         master.Cleared = "Cleared"

#                     master.save()

#                     # 🟢 STEP 3: SAVE DETAILS
#                     new_details = []
#                     for detail_form in formset:
#                         if detail_form.cleaned_data and not detail_form.cleaned_data.get("DELETE"):
#                             detail = ReceiptDetails(
#                                 Ledger=detail_form.cleaned_data["Ledger"],
#                                 Amount=detail_form.cleaned_data["Amount"],
#                                 Desc=detail_form.cleaned_data.get("Desc", "")
#                             )

#                             # Link to master
#                             for field in detail._meta.fields:
#                                 if field.related_model == ReceiptMaster:
#                                     setattr(detail, field.name, master)
#                                     break

#                             detail.save()
#                             new_details.append(detail)

#                     if not new_details:
#                         raise ValueError("At least one receipt detail is required.")

#                     # 🟢 STEP 4: UPDATE TOTAL
#                     master.TotalAmount = sum(
#                         d.Amount for d in new_details if d.Amount
#                     )
#                     master.save()

#                     # 🟢 STEP 5: LEDGER POSTING
#                     if master.Cleared == "Cleared":
#                         create_ledger_postings_for_receipt(master)

#                     action = "updated" if is_edit else "created"
#                     messages.success(request, f"Receipt voucher {action} successfully!")
#                     return redirect("accounts_app:list_receipt")

#             except Exception as e:
#                 messages.error(request, f"Error saving receipt: {e}")

#         else:
#             messages.error(request, "Please correct the errors below.")

#     else:
#         form = ReceiptMasterForm(instance=receipt_instance)
#         formset = ReceiptDetailsFormSet()

#     # Existing details for JS (Edit mode)
#     existing_details_data = []
#     if is_edit:
#         for detail in receipt_instance.details.all():
#             existing_details_data.append({
#                 "ledger_id": detail.Ledger.id,
#                 "ledger_name": str(detail.Ledger),
#                 "amount": str(detail.Amount),
#                 "desc": detail.Desc or ""
#             })

#     return render(request, "receipt_create.html", {
#         "form": form,
#         "formset": formset,
#         "is_edit_mode": is_edit,
#         "existing_details_json": json.dumps(existing_details_data),
#     })

RECEIPT_MENU_ID = 7

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
                        )
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

def list_payment(request):
    """List all payment master entries"""
    
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
        
def ledger_posting_list(request):
    # Get all postings
    postings = LedgerPosting.objects.all().select_related('ledger', 'VoucherType').order_by('-date', '-id')
    
    # Get filter options
    voucher_types = Vouchers.objects.all()
    ledgers = LedgerCreation.objects.all()
    
    context = {
        'postings': postings,
        'voucher_types': voucher_types,
        'ledgers': ledgers,
    }
    
    return render(request, 'ledger_posting_list.html', context)

def list_receipt(request):
   

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

    
def cheque_clearance(request):
    """
    Display cheque clearance form
    """
    return render(request, "cheque_clearance.html")



def get_cheque_clearance_bills(request):
    """
    API endpoint to fetch bills based on filter type and date
    Returns JSON data for the table
    """
    try:
        filter_type = request.GET.get('type', 'payable')
        date_filter = request.GET.get('date', '').strip()
        
        print(f"Filter Type: {filter_type}")
        print(f"Date Filter: '{date_filter}'")
        
        bills = []
        
        if filter_type == 'payable':
            query = PaymentMaster.objects.filter(Cleared__in=["Not Cleared", "Bounced"])
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                    print(f"Filtering by date: {filter_date}")
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            print(f"Query count: {query.count()}")
            
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
                    print(f"Filtering by date: {filter_date}")
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            print(f"Query count: {query.count()}")
            
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
            # ✅ Get Payment Bill vouchers with IsPDC=True and "Not Cleared" status
            query = PaymentBillMaster.objects.filter(
                IsPDC=True,  # ✅ Only PDC cheques
                Cleared__in=["Not Cleared", "Bounced"]
            )
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                    print(f"Filtering by date: {filter_date}")
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            print(f"Query count: {query.count()}")
            
            for payment_bill in query.select_related('Ledger', 'Supplier'):
                bills.append({
                    'id': payment_bill.id,
                    'voucher_no': payment_bill.TrnNo or payment_bill.id,  # Use TrnNo or ID
                    'date': payment_bill.Date.strftime('%d/%b/%Y'),
                    'net_total': float(payment_bill.TotalAmount),
                    'ledger_name': payment_bill.Ledger.ledger_name if payment_bill.Ledger else '',
                    'check_date': payment_bill.ChequeDate.strftime('%d/%b/%Y') if payment_bill.ChequeDate else '',
                    'cheque_no': payment_bill.ChequeNo or '',
                    'cleared': payment_bill.Cleared or '',
                })
        
        elif filter_type == 'receipt-bill':
            # ✅ Get Receipt Bill vouchers with IsPDC=True and "Not Cleared" status
            query = ReceiptBillMaster.objects.filter(
                IsPDC=True,  # ✅ Only PDC cheques
                Cleared__in=["Not Cleared", "Bounced"]
            )
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                    print(f"Filtering by date: {filter_date}")
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            print(f"Query count: {query.count()}")
            
            for receipt_bill in query.select_related('Ledger', 'Customer'):
                bills.append({
                    'id': receipt_bill.id,
                    'voucher_no': receipt_bill.TrnNo or receipt_bill.id,  # Use TrnNo or ID
                    'date': receipt_bill.Date.strftime('%d/%b/%Y'),
                    'net_total': float(receipt_bill.TotalAmount),
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
    """
    Update the cleared status of a payment/receipt/payment-bill/receipt-bill
    WITH PROPER AUDIT LOGGING
    """
    try:
        data = json.loads(request.body)
        bill_id = data.get('bill_id')
        status = data.get('status')  # Cleared / Bounced / Not Cleared
        bill_type = data.get('type')
        bounce_charge = Decimal(str(data.get('bounce_charge', 0)))

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
                    create_ledger_postings_for_payment(obj)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting(obj)

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
                    create_ledger_postings_for_receipt(obj)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting_receipt(obj)

                screen_name = "Cheque Clearance - Receipt"

            elif bill_type == 'payment-bill':
                obj = PaymentBillMaster.objects.select_for_update().get(id=bill_id)
                voucher_no = str(obj.TrnNo or obj.id)  # ✅ Use TrnNo or ID
                old_status = obj.Cleared

                obj.Cleared = status

                if status == "Cleared":
                    obj.ChequeStatus = "cleared"

                elif status == "Bounced":
                    obj.ChequeStatus = "bounced"
                    obj.BounceCharge = bounce_charge

                obj.save()

                if old_status == "Not Cleared" and status == "Cleared":
                    create_ledger_postings_for_paymentbillclr(obj)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting_paymentbill(obj)

                screen_name = "Cheque Clearance - Payment Bill"

            elif bill_type == 'receipt-bill':
                obj = ReceiptBillMaster.objects.select_for_update().get(id=bill_id)
                voucher_no = str(obj.TrnNo or obj.id)  # ✅ Use TrnNo or ID
                old_status = obj.Cleared

                obj.Cleared = status

                if status == "Cleared":
                    obj.ChequeStatus = "cleared"

                elif status == "Bounced":
                    obj.ChequeStatus = "bounced"
                    obj.BounceCharge = bounce_charge

                obj.save()

                if old_status == "Not Cleared" and status == "Cleared":
                    create_ledger_postings_for_receiptbillclr(obj)

                elif status == "Bounced" and bounce_charge > 0:
                    create_bounce_charge_ledger_posting_receiptbill(obj)

                screen_name = "Cheque Clearance - Receipt Bill"

            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid bill type'
                }, status=400)

            # ✅ LOG ONLY AFTER COMMIT SUCCESS
            transaction.on_commit(lambda: log_activity(
                user=request.user,
                screen_name=screen_name,
                action_type="UPDATE",
                remark=(
                    f"Voucher {voucher_no} cheque status changed "
                    f"from '{old_status}' to '{status}'"
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


def client_outstanding_report(request):

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    customer_id = request.GET.get('customer')

    # Base query
    credit_invoices = Invoice.objects.filter(
        payment_mode='Credit',
        customer__isnull=False
    )

    # Apply filters
    if from_date:
        credit_invoices = credit_invoices.filter(date__gte=from_date)

    if to_date:
        credit_invoices = credit_invoices.filter(date__lte=to_date)

    if customer_id:
        credit_invoices = credit_invoices.filter(customer_id=customer_id)

    credit_invoices = credit_invoices.select_related(
        'customer', 'voucherType'
    ).order_by('customer__ledger_name', 'date')

    customer_map = {}

    for invoice in credit_invoices:
        cust = invoice.customer
        cid = cust.pk

        if cid not in customer_map:
            customer_map[cid] = {
                'customer': cust,
                'invoice_rows': [],
                'receipt_rows': [],
                'total_invoice': Decimal('0'),
                'total_paid': Decimal('0'),
            }

        customer_map[cid]['invoice_rows'].append(invoice)
        customer_map[cid]['total_invoice'] += invoice.grand_total

    # Receipts
    for cid, data in customer_map.items():

        receipt_masters = ReceiptBillMaster.objects.filter(
            Customer_id=cid
        ).order_by('Date')

        if from_date:
            receipt_masters = receipt_masters.filter(Date__gte=from_date)

        if to_date:
            receipt_masters = receipt_masters.filter(Date__lte=to_date)

        for master in receipt_masters:

            if master.IsPDC and master.ChequeStatus != 'cleared':
                continue

            data['receipt_rows'].append(master)
            data['total_paid'] += master.TotalAmount

    report = []

    for data in customer_map.values():
        data['balance'] = data['total_invoice'] - data['total_paid']
        report.append(data)

    report.sort(key=lambda x: str(x['customer']))

    grand_invoice = sum(r['total_invoice'] for r in report)
    grand_paid = sum(r['total_paid'] for r in report)
    grand_balance = sum(r['balance'] for r in report)

    customers = LedgerCreation.objects.filter(
        groups__groupName='Sundry Debtors'
    ).order_by('ledger_name')

    return render(request, 'client_outstanding_report.html', {
        'report': report,
        'grand_invoice': grand_invoice,
        'grand_paid': grand_paid,
        'grand_balance': grand_balance,
        'customers': customers,
        'from_date': from_date,
        'to_date': to_date,
        'selected_customer': customer_id,
    })

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

    supplier_map = {}

    for hire in credit_hires:
        supp = hire.supplier
        sid = supp.pk

        if sid not in supplier_map:
            supplier_map[sid] = {
                'supplier': supp,
                'hire_rows': [],
                'payment_rows': [],
                'total_hire': Decimal('0'),
                'total_paid': Decimal('0'),
            }

        supplier_map[sid]['hire_rows'].append(hire)
        supplier_map[sid]['total_hire'] += hire.grand_total


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
        data['balance'] = data['total_hire'] - data['total_paid']
        report.append(data)

    report.sort(key=lambda x: str(x['supplier']))

    grand_hire = sum(r['total_hire'] for r in report)
    grand_paid = sum(r['total_paid'] for r in report)
    grand_balance = sum(r['balance'] for r in report)

    suppliers = LedgerCreation.objects.all().order_by('ledger_name')

    return render(request,'supplier_outstanding_report.html',{
        'report': report,
        'grand_hire': grand_hire,
        'grand_paid': grand_paid,
        'grand_balance': grand_balance,
        'suppliers': suppliers,
        'from_date': from_date,
        'to_date': to_date,
        'selected_supplier': supplier_id,
    })