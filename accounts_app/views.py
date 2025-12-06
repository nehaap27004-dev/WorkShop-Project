from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404

from fleet_app.common import create_bounce_charge_ledger_posting, create_bounce_charge_ledger_posting_paymentbill, create_bounce_charge_ledger_posting_receipt, create_bounce_charge_ledger_posting_receiptbill, create_ledger_postings_for_payment, create_ledger_postings_for_paymentbillclr, create_ledger_postings_for_receipt, create_ledger_postings_for_receiptbillclr
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
                return redirect('fleet_app:fleet_home')
            else:
                return HttpResponse('Your account is disabled. Contact admin.')
        else:
            return render(request, 'login.html', {'error': 'Incorrect username or password.'})

    return render(request, 'login.html')


@login_required(login_url='accounts_app:admin_login')
def logout_view(request):
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
                form.save()
                return redirect('accounts_app:ledger_view')
        elif 'clear' in request.POST:
            return redirect('accounts_app:ledger_view')

    ledgers = LedgerCreation.objects.all()

    return render(request, 'ledger.html', {'form': form, 'ledgers': ledgers})


@login_required(login_url='accounts_app:admin_login')

def ledger_edit(request, pk):
    ledger = get_object_or_404(LedgerCreation, pk=pk)
    form = LedgerCreationForm(instance=ledger)

    if request.method == 'POST':
        form = LedgerCreationForm(request.POST, instance=ledger)
        if form.is_valid():
            form.save()

            

            return redirect('accounts_app:ledger_view')

    return render(request, 'ledger.html', {'form': form, 'ledgers': LedgerCreation.objects.all()})


@login_required(login_url='accounts_app:admin_login')
def ledger_delete(request, pk):
    # Get the ledger to be deleted
    ledger = get_object_or_404(LedgerCreation, pk=pk)
    ledger.delete()

    

    return redirect('accounts_app:ledger_view')


from decimal import Decimal
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, render

def local_payment_view(request):
    if request.method == 'POST':
        payment_form = LocalPaymentForm(request.POST)
        items_formset = LocalPaymentItemFormSet(request.POST, prefix='form')
        cheque_form = None

        if request.POST.get('payment_mode') == 'cheque':
            cheque_form = LocalPaymentChequeForm(request.POST)

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

                    # Save items with recalculated vat_amount
                    for form in items_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                            item = form.save(commit=False)
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

                    # Save cheque details if needed
                    if cheque_form and payment.payment_mode == 'cheque':
                        cheque = cheque_form.save(commit=False)
                        cheque.localpayment = payment
                        cheque.save()

                messages.success(request, 'Local Payment created successfully.')
                return redirect('accounts_app:local_payment_list')

            except Exception as e:
                messages.error(request, f'Error saving payment: {str(e)}')
        else:
            if payment_form.errors:
                messages.error(request, f'Payment form errors: {payment_form.errors}')
            if items_formset.errors:
                messages.error(request, f'Items form errors: {items_formset.errors}')
            if cheque_form and cheque_form.errors:
                messages.error(request, f'Cheque form errors: {cheque_form.errors}')
    else:
        payment_form = LocalPaymentForm()
        items_formset = LocalPaymentItemFormSet(queryset=LocalPaymentItems.objects.none(), prefix='form')
        cheque_form = LocalPaymentChequeForm()

    context = {
        'payment_form': payment_form,
        'items_formset': items_formset,
        'cheque_form': cheque_form,
    }
    return render(request, 'local_payment_form.html', context)

def local_payment_list(request):
    """Display a list of LocalPayment entries as vouchers."""
    local_payments = LocalPayment.objects.all()
    context = {
        'local_payments': local_payments,
    }
    return render(request, 'local_payment_list.html', context)

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
    if delete_id:
        group_to_delete = get_object_or_404(Groups, id=delete_id)
        if not group_to_delete.isDefault:
            group_to_delete.delete()
        return redirect('accounts_app:group_management')

    if group_id:
        group_instance = get_object_or_404(Groups, id=group_id)
        if group_instance.isDefault:
            return redirect('accounts_app:group_management')
    else:
        group_instance = None

    form = GroupsForm(request.POST or None, instance=group_instance)
    if request.method == 'POST' and form.is_valid():
        group = form.save(commit=False)
        if group_instance and group_instance.isDefault:
            return redirect('accounts_app:group_management')
        group.save()
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
        # Delete operation
        if 'delete_id' in request.POST:
            delete_id = request.POST.get('delete_id')
            del_customer = get_object_or_404(LedgerCreation, pk=delete_id, groups_id=29, types='DR')
            del_customer.delete()
            messages.success(request, "Customer deleted successfully!")
            return redirect('accounts_app:manage_customers')

        # Add/Edit operation
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            if edit_mode:
                messages.success(request, "Customer updated successfully!")
            else:
                messages.success(request, "Customer added successfully!")
            return redirect('accounts_app:manage_customers')

    customers = LedgerCreation.objects.filter(groups_id=29, types='DR').order_by('ledger_name')
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
        # Delete operation
        if 'delete_id' in request.POST:
            delete_id = request.POST.get('delete_id')
            del_vendor = get_object_or_404(LedgerCreation, pk=delete_id, groups_id=28, types='CR')
            del_vendor.delete()
            messages.success(request, "Vendor deleted successfully!")
            return redirect('accounts_app:manage_vendors')

        # Add/Edit operation
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            if edit_mode:
                messages.success(request, "Vendor updated successfully!")
            else:
                messages.success(request, "Vendor added successfully!")
            return redirect('accounts_app:manage_vendors')

    vendors = LedgerCreation.objects.filter(groups_id=28, types='CR').order_by('ledger_name')
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
    if edit_id:
        role = get_object_or_404(UserRole, pk=edit_id)
    else:
        role = None

    if request.method == 'POST':
        if 'delete_id' in request.POST:  # Delete action
            delete_role = get_object_or_404(UserRole, pk=request.POST['delete_id'])
            delete_role.delete()
            return redirect('accounts_app:role_management')

        form = UserRoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
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
    if edit_id:
        user_instance = get_object_or_404(CustomUser, pk=edit_id)
    else:
        user_instance = None

    if request.method == 'POST':
        if 'delete_id' in request.POST:
            delete_user = get_object_or_404(CustomUser, pk=request.POST['delete_id'])
            delete_user.delete()
            return redirect('accounts_app:user_management')

        form = CustomUserForm(request.POST, instance=user_instance)
        if form.is_valid():
            form.save()
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

# def clear_transactions(request):
#     if request.method in ["POST", "GET"]:
#         # Delete details first (to avoid FK issues), then masters
#         PurchaseDetail.objects.all().delete()
#         PurchaseMaster.objects.all().delete()
#         SalesDetail.objects.all().delete()
#         SalesMaster.objects.all().delete()
#         PurchaseReturnDetail.objects.all().delete()
#         PurchaseReturnMaster.objects.all().delete()
#         SalesReturnDetail.objects.all().delete()
#         SalesReturnMaster.objects.all().delete()
#         PaymentCheque.objects.all().delete()
#         PaymentItems.objects.all().delete()
#         Payment.objects.all().delete()
#         LocalPaymentCheque.objects.all().delete()
#         LocalPaymentItems.objects.all().delete()
#         LocalPayment.objects.all().delete()
#         ReceiptCheque.objects.all().delete()
#         ReceiptItems.objects.all().delete()
#         Receipt.objects.all().delete()


#         messages.success(request, "All purchase and sale data cleared successfully.")
#         return redirect("accounts_app:home")  # change to your desired page
    
#     messages.error(request, "Invalid request")
#     return redirect("accounts_app:home")
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
                
                
            ]

            for table in tables:
                truncate_table(table)

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
        from fleet_app.models import Invoice
        from accounts_app.models import ReceiptBillDetails
        from fleet_app.models import Vouchers
        
        invoice = Invoice.objects.get(pk=invoice_id)
        
        # Get total amount cleared from all receipt bill details
        total_cleared = ReceiptBillDetails.objects.filter(
            VoucherNo=invoice_id,
            VoucherType__id=2  # Invoice voucher type
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
    
            
def create_ReceiptBillClearance(request, pk=None):
    # Check if we're editing an existing receipt bill
    receipt_bill_instance = None
    if pk:
        receipt_bill_instance = get_object_or_404(ReceiptBillMaster, pk=pk)

    if request.method == 'POST':
        print("\n=== RECEIPT BILL SAVE DEBUG START ===")
        print("POST DATA:", request.POST)

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
                        # Get all old invoice IDs before deletion for clearing status check
                        old_invoice_ids = set(
                            ReceiptBillDetails.objects.filter(BillMaster=master).values_list('VoucherNo', flat=True)
                        )

                        deleted_details_count = ReceiptBillDetails.objects.filter(BillMaster=master).delete()[0]
                        print(f"🗑️ Deleted {deleted_details_count} existing receipt bill detail(s)")

                    # Now save formset with the master instance
                    formset.instance = master
                    details = formset.save(commit=False)

                    # Track invoices for clearing status update
                    invoices_to_check = set()

                    # If editing, add old invoice IDs to check for updated clearing status
                    if pk:
                        invoices_to_check.update(old_invoice_ids)
                    
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
                        print(f"   ➕ Detail saved: VoucherNo={detail.VoucherNo}, Amount={detail.Amount}")
                        
                        # Track this invoice for clearing check
                        invoices_to_check.add(detail.VoucherNo)
                    
                    # Check and update IsCleared status for each invoice
                    print("\n🔍 Starting invoice status update...")
                    for invoice_id in invoices_to_check:
                        print(f"\n--- Processing Invoice ID: {invoice_id} ---")
                        
                        try:
                            invoice = Invoice.objects.get(pk=invoice_id)
                            print(f"✓ Invoice found: {invoice.voucher_no}")
                            print(f"  Before update - IsCleared: {invoice.IsCleared}")
                            
                            # Calculate total cleared
                            receipt_details = ReceiptBillDetails.objects.filter(VoucherNo=invoice_id)
                            print(f"  Found {receipt_details.count()} receipt detail(s)")
                            
                            total_result = receipt_details.aggregate(total=Sum('Amount'))
                            total_cleared = total_result['total'] or Decimal('0.00')
                            
                            print(f"  Grand Total: {invoice.grand_total}")
                            print(f"  Total Cleared: {total_cleared}")
                            
                            remaining = invoice.grand_total - total_cleared
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
                    
                    print("\n✅ Finished processing all invoices\n")

                print("=== RECEIPT BILL SAVE DEBUG END ===\n")
                if pk:
                    messages.success(request, 'Receipt bill updated successfully!')
                else:
                    messages.success(request, 'Receipt bill saved successfully!')
                return redirect('accounts_app:list_receiptbill')

            except Exception as e:
                print("❌ Exception during save:", str(e))
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error saving receipt: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')

        return render(request, 'create_ReceiptBillClearance.html', {
            'master_form': master_form,
            'formset': formset,
            'edit_mode': pk is not None,
            'receipt_bill_instance': receipt_bill_instance,
        })

    else:
        master_form = ReceiptBillMasterForm(instance=receipt_bill_instance)
        formset = ReceiptBillDetailsFormSet(prefix='form', instance=receipt_bill_instance)

    return render(request, 'create_ReceiptBillClearance.html', {
        'master_form': master_form,
        'formset': formset,
        'edit_mode': pk is not None,
        'receipt_bill_instance': receipt_bill_instance,
    })


def list_receiptbill(request):
    """List all receipt bill clearances"""
    receipt_bills = ReceiptBillMaster.objects.all().order_by('-Date')
    return render(request, "ReceiptBillClr_list.html", {"receipt_bills": receipt_bills})

def receiptbill_delete(request, pk):
    """Delete a receipt bill clearance"""
    receipt_bill = get_object_or_404(ReceiptBillMaster, pk=pk)
    receipt_bill.delete()
    messages.success(request, 'Receipt bill deleted successfully!')
    return redirect('accounts_app:list_receiptbill')

    # --- AJAX View to fetch uncleared invoices ---
def get_customer_invoices(request):
    customer_id = request.GET.get('customer_id')
    data = []

    if customer_id:
        invoices = Invoice.objects.filter(customer_id=customer_id, IsCleared=False)
        for inv in invoices:
            # Calculate amount already cleared
            total_paid = sum(
                ReceiptBillDetails.objects.filter(VoucherNo=inv.id).values_list('Amount', flat=True)
            ) or 0

            balance = float(inv.grand_total) - float(total_paid)

            data.append({
                'invoice_id': inv.id,
                'voucher_no': inv.voucher_no,
                'date': inv.date.strftime('%Y-%m-%d'),
                'customer': inv.customer.ledger_name,  # ✅ Correct field
                'grand_total': float(inv.grand_total),
                'amount_cleared': float(total_paid),
                'receivable_balance': balance,
            })

    return JsonResponse({'invoices': data})



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
            VoucherType__id=1  # VoucherType for Hire
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
def create_PaymentBillClearance(request, pk=None):
    # Check if we're editing an existing payment bill
    payment_bill_instance = None
    if pk:
        payment_bill_instance = get_object_or_404(PaymentBillMaster, pk=pk)

    if request.method == 'POST':
        print("\n=== PAYMENT BILL SAVE DEBUG START ===")
        print("POST DATA:", request.POST)

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
                            VoucherType_id=6,
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
                        PaymentBillDetails.objects.filter(BillMaster=master).delete()
                        print(f"🗑️ Deleted old payment bill details")

                    # Save details
                    formset.instance = master
                    details = formset.save(commit=False)
                    hires_to_check = set()

                    for detail in details:
                        if not detail.Amount or detail.Amount <= 0:
                            print(f"⏭️ Skipping detail with zero/empty amount for VoucherNo={detail.VoucherNo}")
                            continue

                        detail.BillMaster = master
                        voucher_type_id = detail.voucherType if isinstance(detail.voucherType, int) else detail.voucherType.id
                        detail.VoucherType = Vouchers.objects.get(pk=voucher_type_id)

                        if request.user.is_authenticated:
                            detail.created_by = request.user.id
                            detail.updated_by = request.user.id

                        detail.save()
                        print(f"➕ Detail saved: VoucherNo={detail.VoucherNo}, Amount={detail.Amount}")
                        hires_to_check.add(detail.VoucherNo)

                    # 🔍 Update each hire's cleared status
                    print("\n🔍 Starting hire status update...")
                    for hire_id in hires_to_check:
                        print(f"\n--- Processing Hire ID: {hire_id} ---")
                        try:
                            hire = FleetHire.objects.get(pk=hire_id)
                            print(f"✓ Hire found: {hire.voucher_no}")
                            print(f"  Before update - IsCleared: {hire.IsCleared}")

                            payment_details = PaymentBillDetails.objects.filter(VoucherNo=hire_id)
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

                    print("\n✅ Finished processing all hires\n")

                print("=== PAYMENT BILL SAVE DEBUG END ===\n")
                if pk:
                    messages.success(request, 'Payment bill updated successfully!')
                else:
                    messages.success(request, 'Payment bill saved successfully!')
                return redirect('accounts_app:list_paymentbill')

            except Exception as e:
                print("❌ Exception during save:", str(e))
                import traceback
                traceback.print_exc()
                messages.error(request, f'Error saving payment: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')

        return render(request, 'create_PaymentBillClearance.html', {
            'master_form': master_form,
            'formset': formset,
            'edit_mode': pk is not None,
            'payment_bill_instance': payment_bill_instance,
        })

    else:
        master_form = PaymentBillMasterForm(instance=payment_bill_instance)
        formset = PaymentBillDetailsFormSet(prefix='form', instance=payment_bill_instance)

    return render(request, 'create_PaymentBillClearance.html', {
        'master_form': master_form,
        'formset': formset,
        'edit_mode': pk is not None,
        'payment_bill_instance': payment_bill_instance,
    })
    
# ================================
# 🔹 LIST & DELETE PAYMENT BILL CLEARANCES
def list_paymentbill(request):
    """List all payment bill clearances"""
    payment_bills = PaymentBillMaster.objects.all().order_by('-Date')
    return render(request, "PaymentBillClr_list.html", {"payment_bills": payment_bills})

def paymentbill_delete(request, pk):
    """Delete a payment bill clearance"""
    payment_bill = get_object_or_404(PaymentBillMaster, pk=pk)
    payment_bill.delete()
    messages.success(request, 'Payment bill deleted successfully!')
    return redirect('accounts_app:list_paymentbill')

# ================================
# 🔹 AJAX - FETCH UNCLEARED HIRES
# ================================
def get_supplier_hires(request):
    supplier_id = request.GET.get('supplier_id')
    data = []

    if supplier_id:
        hires = FleetHire.objects.filter(supplier_id=supplier_id, IsCleared=False)
        for hire in hires:
            total_paid = sum(
                PaymentBillDetails.objects.filter(VoucherNo=hire.id).values_list('Amount', flat=True)
            ) or 0

            balance = float(hire.grand_total) - float(total_paid)

            data.append({
                'hire_id': hire.id,
                'voucher_no': hire.voucher_no,
                'date': hire.date.strftime('%Y-%m-%d'),
                'supplier': hire.supplier.ledger_name,
                'grand_total': float(hire.grand_total),
                'amount_cleared': float(total_paid),
                'payable_balance': balance,
            })

    return JsonResponse({'hires': data})

def payment_create(request):
    if request.method == "POST":
        # Debug
        print("\n=== ALL POST DATA ===")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        print("===================\n")
        
        form = PaymentMasterForm(request.POST)
        formset = PaymentDetailsFormSet(request.POST)
        
        print("Form valid:", form.is_valid())
        print("Formset valid:", formset.is_valid())
        print("Formset total forms:", formset.total_form_count())
        
        if not form.is_valid():
            print("Form errors:", form.errors)
        
        if not formset.is_valid():
            print("Formset errors:", formset.errors)
            print("Formset non_form_errors:", formset.non_form_errors())
        else:
            print("\n=== FORMSET CLEANED DATA ===")
            for i, form_instance in enumerate(formset):
                if form_instance.cleaned_data:
                    print(f"Form {i}: {form_instance.cleaned_data}")
            print("============================\n")

        if form.is_valid() and formset.is_valid():
            master = form.save(commit=False)  # ✅ Don't save yet
            
            # ✅ Set Cleared field based on IsPDC
            if master.IsPDC:
                master.Cleared = "Not Cleared"
            else:
                master.Cleared = "Cleared"
            
            master.save()  # ✅ Now save
            
            formset.instance = master
            details = formset.save()
            
            print(f"✅ Saved {len(details)} payment details")
            
            # ✅ Only call LedgerPosting if Cleared is NOT "Not Cleared"
            if master.Cleared != "Not Cleared":
                create_ledger_postings_for_payment(master)
                print("✅ Ledger posting created")
            else:
                print("⏸️ Ledger posting skipped - Payment is Not Cleared (PDC)")
            
            messages.success(request, f"Payment voucher created successfully with {len(details)} details!")
            return redirect("accounts_app:payment_create")
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = PaymentMasterForm()
        formset = PaymentDetailsFormSet()

    return render(request, "payment_create.html", {
        "form": form,
        "formset": formset,
    })    
    
    
    
    
def receipt_create(request):
    if request.method == "POST":
        # Debug
        print("\n=== ALL POST DATA ===")
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        print("===================\n")
        
        form = ReceiptMasterForm(request.POST)
        formset = ReceiptDetailsFormSet(request.POST)
        
        print("Form valid:", form.is_valid())
        print("Formset valid:", formset.is_valid())
        
        if not form.is_valid():
            print("Form errors:", form.errors)
        
        if not formset.is_valid():
            print("Formset errors:", formset.errors)
            print("Formset non_form_errors:", formset.non_form_errors())
        else:
            print("Formset is valid!")

        if form.is_valid() and formset.is_valid():
            master = form.save(commit=False)  # ✅ Don't save yet
            
            # ✅ Set Cleared field based on IsPDC
            if master.IsPDC:
                master.Cleared = "Not Cleared"
            else:
                master.Cleared = "Cleared"
            
            master.save()  # ✅ Now save
            
            formset.instance = master
            details = formset.save()
            
            print(f"✅ Saved {len(details)} receipt details")
            
            # ✅ Only call LedgerPosting if NOT "Not Cleared"
            if master.Cleared != "Not Cleared":
                create_ledger_postings_for_receipt(master)
                print("✅ Ledger posting created")
            else:
                print("⏸️ Ledger posting skipped - Receipt is Not Cleared (PDC)")
            
            messages.success(request, f"Receipt voucher created successfully with {len(details)} details!")
            return redirect("accounts_app:receipt_create")
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ReceiptMasterForm()
        formset = ReceiptDetailsFormSet()

    return render(request, "receipt_create.html", {
        "form": form,
        "formset": formset,
    })

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
    return render(request, "receipt_list.html", {"receipts": receipts})

def receipt_delete(request, pk):
    receipt = get_object_or_404(ReceiptMaster, pk=pk)
    receipt.delete()
    return redirect('receipt_list')

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
            # ✅ Get Payment Bill vouchers with "Not Cleared" status
            query = PaymentBillMaster.objects.filter(Cleared__in=["Not Cleared", "Bounced"])
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                    print(f"Filtering by date: {filter_date}")
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            print(f"Query count: {query.count()}")
            
            for payment_bill in query.select_related('Ledger'):
                bills.append({
                    'id': payment_bill.id,
                    'voucher_no': payment_bill.voucher_no,
                    'date': payment_bill.Date.strftime('%d/%b/%Y'),
                    'net_total': float(payment_bill.TotalAmount),
                    'ledger_name': payment_bill.Ledger.ledger_name if payment_bill.Ledger else '',
                    'check_date': payment_bill.ChequeDate.strftime('%d/%b/%Y') if payment_bill.ChequeDate else '',
                    'cheque_no': payment_bill.ChequeNo or '',
                    'cleared': payment_bill.Cleared or '',
                })
        
        elif filter_type == 'receipt-bill':
            query = ReceiptBillMaster.objects.filter(Cleared__in=["Not Cleared", "Bounced"])
            
            if date_filter:
                try:
                    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                    query = query.filter(Date=filter_date)
                    print(f"Filtering by date: {filter_date}")
                except ValueError as e:
                    print(f"Invalid date format: {e}")
            
            print(f"Query count: {query.count()}")
            
            for receipt_bill in query.select_related('Ledger'):
                bills.append({
                    'id': receipt_bill.id,
                    'voucher_no': receipt_bill.voucher_no,
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
    """
    try:
        data = json.loads(request.body)
        bill_id = data.get('bill_id')
        status = data.get('status')  # "Cleared", "Bounced", "Not Cleared"
        bill_type = data.get('type', 'payable')
        bounce_charge = data.get('bounce_charge', 0)
        
        print(f"Updating bill {bill_id} to status: {status}, bounce_charge: {bounce_charge}")
        
        if bill_type == 'payable':
            payment = PaymentMaster.objects.get(id=bill_id)
            old_status = payment.Cleared
            payment.Cleared = status
            
            if status == "Bounced":
                payment.BounceCharge = Decimal(str(bounce_charge))
            
            payment.save()
            
            if old_status == "Not Cleared" and status == "Cleared":
                create_ledger_postings_for_payment(payment)
                message = f"Payment {payment.voucher_no} marked as {status} and ledger posted"
                
            elif status == "Bounced" and Decimal(str(bounce_charge)) > 0:
                create_bounce_charge_ledger_posting(payment)
                message = f"Payment {payment.voucher_no} marked as {status} with bounce charge ₹{bounce_charge}"
                
            else:
                message = f"Payment {payment.voucher_no} marked as {status}"
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        
        elif bill_type == 'receivable':
            receipt = ReceiptMaster.objects.get(id=bill_id)
            old_status = receipt.Cleared
            receipt.Cleared = status
            
            if status == "Bounced":
                receipt.BounceCharge = Decimal(str(bounce_charge))
            
            receipt.save()
            
            if old_status == "Not Cleared" and status == "Cleared":
                create_ledger_postings_for_receipt(receipt)
                message = f"Receipt {receipt.voucher_no} marked as {status} and ledger posted"
                
            elif status == "Bounced" and Decimal(str(bounce_charge)) > 0:
                create_bounce_charge_ledger_posting_receipt(receipt)
                message = f"Receipt {receipt.voucher_no} marked as {status} with bounce charge ₹{bounce_charge}"
                
            else:
                message = f"Receipt {receipt.voucher_no} marked as {status}"
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        
        elif bill_type == 'payment-bill':
            # ✅ Handle Payment Bill
            payment_bill = PaymentBillMaster.objects.get(id=bill_id)
            old_status = payment_bill.Cleared
            payment_bill.Cleared = status
            
            if status == "Bounced":
                payment_bill.BounceCharge = Decimal(str(bounce_charge))
            
            payment_bill.save()
            
            if old_status == "Not Cleared" and status == "Cleared":
                create_ledger_postings_for_paymentbillclr(payment_bill)
                message = f"Payment Bill {payment_bill.voucher_no} marked as {status} and ledger posted"
                
            elif status == "Bounced" and Decimal(str(bounce_charge)) > 0:
                create_bounce_charge_ledger_posting_paymentbill(payment_bill)
                message = f"Payment Bill {payment_bill.voucher_no} marked as {status} with bounce charge ₹{bounce_charge}"
                
            else:
                message = f"Payment Bill {payment_bill.voucher_no} marked as {status}"
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        
        elif bill_type == 'receipt-bill':
            receipt_bill = ReceiptBillMaster.objects.get(id=bill_id)
            old_status = receipt_bill.Cleared
            receipt_bill.Cleared = status
            
            if status == "Bounced":
                receipt_bill.BounceCharge = Decimal(str(bounce_charge))
            
            receipt_bill.save()
            
            if old_status == "Not Cleared" and status == "Cleared":
                create_ledger_postings_for_receiptbillclr(receipt_bill)
                message = f"Receipt Bill {receipt_bill.voucher_no} marked as {status} and ledger posted"
                
            elif status == "Bounced" and Decimal(str(bounce_charge)) > 0:
                create_bounce_charge_ledger_posting_receiptbill(receipt_bill)
                message = f"Receipt Bill {receipt_bill.voucher_no} marked as {status} with bounce charge ₹{bounce_charge}"
                
            else:
                message = f"Receipt Bill {receipt_bill.voucher_no} marked as {status}"
            
            return JsonResponse({
                'success': True,
                'message': message
            })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid bill type'
        })
        
    except Exception as e:
        print(f"❌ Error in update_cheque_status: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)