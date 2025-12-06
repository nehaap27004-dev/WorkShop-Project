from django.shortcuts import render, get_object_or_404, redirect
from item_master.forms import *
from item_master.models import *
import json
from django.db import IntegrityError, transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.forms import modelformset_factory
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Avg
from decimal import Decimal, InvalidOperation
from accounts_app.models import Group, LedgerCreation
from accounts_app.models import GroupUnder
from django.views.decorators.http import require_POST
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import datetime
from django.db.models import Sum, F
from accounts_app.common import check_privilege
from django.http import HttpResponseForbidden
from .common import create_ledger_postings_for_purchase, process_voucher, VoucherKind, create_ledger_postings_for_sale






# Create your views here.

@login_required(login_url='accounts_app:admin_login')
def item_category_create_update_list(request, category_id=None):
    # Handle create/update functionality
    if category_id:
        category = get_object_or_404(ItemCategory, id=category_id)
    else:
        category = None

    if request.method == 'POST':
        form = ItemCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('item_master:item_category_create_update_list')  # Redirect back to the same page after saving
    else:
        form = ItemCategoryForm(instance=category)

    # Handle listing functionality
    categories = ItemCategory.objects.all()

    return render(request, 'item_category_form.html', {
        'form': form,
        'categories': categories,
        'category': category
    })

@login_required(login_url='accounts_app:admin_login') 
def item_manufacturer_create_update_list(request, manufacturer_id=None):
    # Handle create/update functionality
    if manufacturer_id:
        manufacturer = get_object_or_404(ItemManufacturer, id=manufacturer_id)
    else:
        manufacturer = None

    if request.method == 'POST':
        form = ItemManufacturerForm(request.POST, instance=manufacturer)
        if form.is_valid():
            form.save()
            return redirect('item_master:item_manufacturer_create_update_list')  # Redirect back to the same page after saving
    else:
        form = ItemManufacturerForm(instance=manufacturer)

    # Handle listing functionality
    manufacturers = ItemManufacturer.objects.all()

    return render(request, 'item_manufacturer_form.html', {
        'form': form,
        'manufacturers': manufacturers,
        'manufacturer': manufacturer
    })    
    
    
def item_create_update(request, item_id=None):
    item = get_object_or_404(Item, id=item_id) if item_id else None
    
    # Initialize existing_alter_units to empty if item is None
    existing_alter_units = []
    if item:
        # Get the existing alter units for this item
        existing_alter_units = ItemAlterUnit.objects.filter(item=item)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            try:
                with transaction.atomic():
                    base_item = form.save(commit=False)

                    try:
                        base_item.purchase_rate = Decimal(base_item.purchase_rate or "0.00")
                        base_item.sales_rate = Decimal(base_item.sales_rate or "0.00")
                    except InvalidOperation:
                        base_item.purchase_rate = Decimal("0.00")
                        base_item.sales_rate = Decimal("0.00")

                    # Save the base item first to ensure it has an ID
                    base_item.save()

                    # Check if there are any alter units to delete
                    alter_unit_ids_to_keep = request.POST.getlist('alter_unit_ids[]')
                    
                    # Convert to integers (or empty list if no IDs)
                    alter_unit_ids_to_keep = [int(id) for id in alter_unit_ids_to_keep if id]
                    
                    # Delete alter units not in the list to keep
                    if item:  # Only if editing existing item
                        ItemAlterUnit.objects.filter(item=item).exclude(id__in=alter_unit_ids_to_keep).delete()
                    
                    # Extract alternate unit data
                    alter_unit_ids = request.POST.getlist('alter_unit_ids[]')
                    item_units = request.POST.getlist('item_units[]')
                    barcode_codes = request.POST.getlist('barcode_codes[]')
                    purchase_rates = request.POST.getlist('purchase_rates[]')
                    sales_rates = request.POST.getlist('sales_rates[]')
                    uc_factors = request.POST.getlist('uc_factors[]')
                    
                    # Handle checkbox misalignment: ensure each row gets a True/False even if checkbox is unchecked
                    raw_is_base_units = request.POST.getlist('is_base_units[]')
                    total_rows = len(item_units)
                    
                    # Initialize all to False
                    is_base_units = [False] * total_rows

                    # Set to True where checkboxes were submitted
                    for i, value in enumerate(raw_is_base_units):
                        if i < total_rows:
                            is_base_units[i] = True

                    # Process each row
                    for i, (unit_code, barcode, pur_rate, sale_rate, uc, is_base) in enumerate(zip(
                        item_units, barcode_codes, purchase_rates, sales_rates, uc_factors, is_base_units
                    )):
                        # Skip empty rows
                        if not (unit_code.strip() or barcode.strip() or pur_rate.strip() or sale_rate.strip() or uc.strip()):
                            continue
                        
                        try:
                            unit_instance = Unit.objects.get(unit_code=unit_code)
                            pur_rate = Decimal(pur_rate or "0.00")
                            sale_rate = Decimal(sale_rate or "0.00")
                            uc = Decimal(uc or "1.00")
                            is_base_bool = is_base

                        except (Unit.DoesNotExist, InvalidOperation):
                            continue

                        # Check if this is an existing alter unit (has an ID) or a new one
                        alter_unit_id = alter_unit_ids[i] if i < len(alter_unit_ids) else None
                        
                        if alter_unit_id and alter_unit_id.isdigit():
                            # Update existing alter unit
                            try:
                                alter_unit = ItemAlterUnit.objects.get(id=alter_unit_id, item=base_item)
                                alter_unit.unit = unit_instance
                                alter_unit.barcode_code = barcode
                                alter_unit.purchase_rate = pur_rate
                                alter_unit.sales_rate = sale_rate
                                alter_unit.uc_factor = uc
                                alter_unit.is_base_unit = is_base_bool
                                alter_unit.save()
                            except ItemAlterUnit.DoesNotExist:
                                # Create as new if not found
                                ItemAlterUnit.objects.create(
                                    item=base_item,
                                    unit=unit_instance,
                                    barcode_code=barcode,
                                    purchase_rate=pur_rate,
                                    sales_rate=sale_rate,
                                    uc_factor=uc,
                                    is_base_unit=is_base_bool,
                                )
                        else:
                            # Create new alter unit
                            ItemAlterUnit.objects.create(
                                item=base_item,
                                unit=unit_instance,
                                barcode_code=barcode,
                                purchase_rate=pur_rate,
                                sales_rate=sale_rate,
                                uc_factor=uc,
                                is_base_unit=is_base_bool,
                            )

                # If we reach here, the transaction was successful
                return redirect('item_master:item_create_update')  # Redirect to item list after successful operation

            except Exception as e:
                import traceback
                traceback.print_exc()  # print full error in console/log
                form.add_error(None, f"Unexpected error occurred: {str(e)}")
                
            # except IntegrityError:
            #     form.add_error(None, "Error: Barcode code already exists.")    

    else:
        form = ItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'existing_alter_units': existing_alter_units,
        'items': Item.objects.all(),
        'units': Unit.objects.all(),
    }

    return render(request, 'item_form.html', context)

def delete_item(request, item_id):
    """
    View function to handle item deletion
    """
    if request.method == 'POST':
        try:
            item = get_object_or_404(Item, id=item_id)
            item_name = item.item_name  # Save name for success message
            
            # Option 1: Permanently delete the item and all its alter units (CASCADE will handle related objects)
            item.delete()
            
            # Option 2: Alternatively, if you prefer soft delete:
            # item.isDeleted = True
            # item.save()
            
            messages.success(request, f'Item "{item_name}" has been successfully deleted.')
            return redirect('item_master:item_create_update')
        
        except Exception as e:
            messages.error(request, f'Error deleting item: {str(e)}')
            return redirect('item_master:item_create_update')
    
    # If not POST, redirect to item list (direct GET requests not allowed)
    return redirect('item_master:item_create_update')
    



def item_alter_units_view(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    alter_units = item.alter_units.all()  # related_name used in the FK

    return render(request, 'item_alter_units_view.html', {
        'item': item,
        'alter_units': alter_units,
    })

@csrf_exempt
def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        new_category = ItemCategory.objects.create(category_name=category_name)
        return JsonResponse({'category_name': new_category.category_name, 'category_id': new_category.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)




@login_required(login_url='accounts_app:admin_login')
# List Item
def item_list(request):
    items = Item.objects.all()
    return render(request, 'item_list.html', {'items': items})    

def item_search(request):
    query = request.GET.get('q')  # Get the search query from the request
    items = Item.objects.all()  # Start with all items

    if query:  # If there's a search query
        words = query.split()
        filters = Q()
        for word in words:
            filters |= (
                Q(item_code__icontains=word) |
                Q(item_name__icontains=word) |
                Q(barcode_code__icontains=word)
            )
        items = Item.objects.filter(filters)  # Filter based on query

    return render(request, 'item_search_results.html', {'items': items})


@login_required(login_url='accounts_app:admin_login')
def vendor_management(request, vendor_id=None):
    if vendor_id:
        vendor = get_object_or_404(Vendor, id=vendor_id)  # For updating an existing vendor
    else:
        vendor = None  # For creating a new vendor

    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)  # Create or Update Vendor form
        if form.is_valid():
            vendor = form.save()  # Save the vendor

            # Add the corresponding Ledger under "Sundry Creditor"
            sundry_creditors_group = GroupUnder.objects.filter(under_name="Sundry Creditors").first()
            if sundry_creditors_group:
                # Check if a ledger for this vendor already exists
                existing_ledger = LedgerCreation.objects.filter(ledger_name=vendor.vendor_name, group_under=sundry_creditors_group).first()
                if not existing_ledger:
                    LedgerCreation.objects.create(
                        ledger_name=vendor.vendor_name,
                        group_under=sundry_creditors_group,
                        opening_balance=0.00,  # Default opening balance
                        types='CR',  # Default type as Credit
                        remark=f"Ledger for Vendor {vendor.vendor_name}"
                    )
            else:
                # Log or handle the case where "Sundry Creditor" group doesn't exist
                print("Group 'Sundry Creditor' does not exist.")

            return redirect('item_master:vendor_management')  # Redirect to the same page after save
    else:
        form = VendorForm(instance=vendor)

    # Fetch all vendors to list them
    vendors = Vendor.objects.all()

    return render(request, 'vendor_management.html', {'form': form, 'vendors': vendors, 'vendor': vendor})


@login_required(login_url='accounts_app:admin_login')
def unit_management(request, unit_id=None):
    if unit_id:
        unit = get_object_or_404(Unit, id=unit_id)
        form = UnitForm(request.POST or None, instance=unit)
    else:
        form = UnitForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('item_master:unit_manage')

    units = Unit.objects.all()
    return render(request, 'unit_manage.html', {'form': form, 'units': units})

@login_required(login_url='accounts_app:admin_login')
def VAT_management(request, TAX_id=None):
    if TAX_id:
        tax_instance = get_object_or_404(TAX, id=TAX_id)
        form = TAXForm(request.POST or None, instance=tax_instance)
    else:
        form = TAXForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('item_master:VAT_manage')

    VATs = TAX.objects.all()
    return render(request, 'VAT_manage.html', {'form': form, 'VATs': VATs})



@login_required(login_url='accounts_app:admin_login')


# ----------------- CREATE -----------------
@require_http_methods(["GET", "POST"])
def create_purchase_voucher(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Purchase.")

    template_name = 'purchase_form1.html'

    if request.method == "GET":
        voucher_form = PurchaseVoucherForm()
        voucher_form.fields['transaction_date'].initial = datetime.date.today()
        voucher_form.fields['InvoiceDate'].initial = datetime.date.today()

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": PurchaseVoucherItemForm(),
            "items": Item.objects.all(),
            "is_edit": False
        })

    # POST create
    voucher_form = PurchaseVoucherForm(request.POST)
    items_raw = request.POST.get("items_data", "[]")

    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.PURCHASE,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )
                
                create_ledger_postings_for_purchase(voucher)
                
                messages.success(request, f"✅ Purchase voucher {voucher.voucher_no} created successfully.")
                return redirect('item_master:purchase_voucher_list')
        except Exception as e:
            messages.error(request, f"Error creating voucher: {e}")
    else:
        # Show form validation errors
        messages.error(request, "⚠️ Please correct the errors below.")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": PurchaseVoucherItemForm(),
        "items": Item.objects.all(),
        "is_edit": False
    })


# ----------------- EDIT -----------------
@require_http_methods(["GET", "POST"])
def edit_purchase_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Purchase.")

    template_name = 'purchase_form1.html'
    voucher = get_object_or_404(PurchaseMaster, pk=pk)

    if request.method == "GET":
        voucher_form = PurchaseVoucherForm(instance=voucher)
        item_formset = PurchaseVoucherItemFormSet(instance=voucher)

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": PurchaseVoucherItemForm(),
            "item_formset": item_formset,
            "items": Item.objects.all(),
            "is_edit": True,
        })

    # POST update
    voucher_form = PurchaseVoucherForm(request.POST, instance=voucher)
    item_formset = PurchaseVoucherItemFormSet(request.POST, instance=voucher)

    try:
        with transaction.atomic():
            if voucher_form.is_valid() and item_formset.is_valid():
                voucher = voucher_form.save()
                item_formset.save()
                messages.success(request, f"✏️ Purchase voucher {voucher.voucher_no} updated successfully.")
                return redirect('item_master:purchase_voucher_list')
            else:
                # Collect and display all form errors
                error_messages = []
                
                # Voucher form errors
                if voucher_form.errors:
                    for field, errors in voucher_form.errors.items():
                        for error in errors:
                            error_messages.append(f"{field}: {error}")
                
                # Item formset errors
                if item_formset.errors:
                    for i, form_errors in enumerate(item_formset.errors):
                        if form_errors:
                            for field, errors in form_errors.items():
                                for error in errors:
                                    error_messages.append(f"Item {i+1} - {field}: {error}")
                
                # Non-form errors
                if item_formset.non_form_errors():
                    for error in item_formset.non_form_errors():
                        error_messages.append(f"Formset error: {error}")
                
                if error_messages:
                    messages.error(request, "⚠️ Please correct the following errors: " + "; ".join(error_messages))
                else:
                    messages.error(request, "⚠️ Please correct the errors below.")

    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": PurchaseVoucherItemForm(),
        "item_formset": item_formset,
        "items": Item.objects.all(),
        "is_edit": True,
    })        


# ----------------- CREATE -----------------
@require_http_methods(["GET", "POST"])
def create_purchaseReturn_voucher(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Purchase.")

    template_name = 'purchaseReturn_form.html'

    if request.method == "GET":
        voucher_form = PurchaseReturnVoucherForm()
        voucher_form.fields['transaction_date'].initial = datetime.date.today()
        voucher_form.fields['InvoiceDate'].initial = datetime.date.today()

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": PurchaseReturnVoucherItemForm(),
            "items": Item.objects.all(),
            "is_edit": False
        })

    # POST create
    voucher_form = PurchaseReturnVoucherForm(request.POST)
    items_raw = request.POST.get("items_data", "[]")

    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.PURCHASE_RETURN,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )
                messages.success(request, f"✅ Purchase Return voucher {voucher.voucher_no} created successfully.")
                return redirect('item_master:purchase_voucher_list')
        except Exception as e:
            messages.error(request, f"Error creating voucher: {e}")
    else:
        # Show form validation errors
        messages.error(request, "⚠️ Please correct the errors below.")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": PurchaseReturnVoucherItemForm(),
        "items": Item.objects.all(),
        "is_edit": False
    })


# ----------------- EDIT -----------------
@require_http_methods(["GET", "POST"])
def edit_purchaseReturn_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Purchase.")

    template_name = 'purchaseReturn_form.html'
    voucher = get_object_or_404(PurchaseReturnMaster, pk=pk)

    if request.method == "GET":
        voucher_form = PurchaseReturnVoucherForm(instance=voucher)
        item_formset = PurchaseReturnVoucherItemFormSet(instance=voucher)

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": PurchaseReturnVoucherItemForm(),
            "item_formset": item_formset,
            "items": Item.objects.all(),
            "is_edit": True,
        })

    # POST update
    voucher_form = PurchaseReturnVoucherForm(request.POST, instance=voucher)
    item_formset = PurchaseReturnVoucherItemFormSet(request.POST, instance=voucher)

    try:
        with transaction.atomic():
            if voucher_form.is_valid() and item_formset.is_valid():
                voucher = voucher_form.save()
                item_formset.save()
                messages.success(request, f"✏️ Purchase Return voucher {voucher.voucher_no} updated successfully.")
                return redirect('item_master:purchase_voucher_list')
            else:
                # Collect and display all form errors
                error_messages = []
                
                # Voucher form errors
                if voucher_form.errors:
                    for field, errors in voucher_form.errors.items():
                        for error in errors:
                            error_messages.append(f"{field}: {error}")
                
                # Item formset errors
                if item_formset.errors:
                    for i, form_errors in enumerate(item_formset.errors):
                        if form_errors:
                            for field, errors in form_errors.items():
                                for error in errors:
                                    error_messages.append(f"Item {i+1} - {field}: {error}")
                
                # Non-form errors
                if item_formset.non_form_errors():
                    for error in item_formset.non_form_errors():
                        error_messages.append(f"Formset error: {error}")
                
                if error_messages:
                    messages.error(request, "⚠️ Please correct the following errors: " + "; ".join(error_messages))
                else:
                    messages.error(request, "⚠️ Please correct the errors below.")

    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": PurchaseReturnVoucherItemForm(),
        "item_formset": item_formset,
        "items": Item.objects.all(),
        "is_edit": True,
    })        


    
def get_item_details(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        item_id = request.GET.get('item_id')
            # Use select_related to fetch related VAT and item_unit in single query
        item = Item.objects.select_related('TAX', 'item_unit').get(id=item_id)
            
            # Prepare the response data
        data = {
                'status': 'success',
                'item_code': item.item_code,
                'barcode_code': item.barcode_code if item.barcode_code else '',
                'TAX_id': item.TAX.id if item.TAX else None,
                'TAX_percent': float(item.TAX.TAX_percent) if item.TAX else 0,  # Assuming VAT model has percentage field
                'item_unit_id': item.item_unit.id if item.item_unit else None,
                'purchase_rate': float(item.purchase_rate) if item.purchase_rate else 0,
                'sales_rate': float(item.sales_rate) if item.sales_rate else 0,
        }
        return JsonResponse(data)

def search_items(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_term = request.GET.get('term', '')
        if search_term:
            items = Item.objects.filter(
                Q(item_name__icontains=search_term) |
                Q(item_code__icontains=search_term)
            ).select_related('VAT', 'item_unit')[:10]  # Limit to 10 results

            data = [{
                'id': item.id,
                'item_name': item.item_name,
                'item_code': item.item_code,
                'barcode_code': item.barcode_code or ''
            } for item in items]
            return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


@login_required(login_url='accounts_app:admin_login')
def purchase_voucher_list(request):
    # Check privilege for purchase listing
    if not check_privilege(request.user, 3, "can_read"):   # 3 is the ID of the "Purchase" menu

        return HttpResponseForbidden("🚫 You do not have permission to view Purchase.")
    # Query all PurchaseVoucher objects from the database
    vouchers = PurchaseMaster.objects.all()

    # Pass the vouchers to the template context
    return render(request, 'purchase_voucher_list.html', {'vouchers': vouchers})


@login_required(login_url='accounts_app:admin_login')
def purchase_voucher_detail(request, voucher_id):
    # Retrieve the PurchaseVoucher object and related PurchaseVoucherItem objects
    voucher = get_object_or_404(PurchaseMaster, id=voucher_id)
    items = PurchaseDetail.objects.filter(purchase__id=voucher.id)
    # Pass the voucher and its items to the template context
    return render(request, 'purchase_voucher_detail.html', {
        'voucher': voucher,
        'items': items
    })    
    
    
@require_POST
def purchase_voucher_delete(request, pk):
    # Check privilege for purchase delete
    if not check_privilege(request.user, 3, "can_delete"):   # 3 is the ID of the "Purchase" menu

        return HttpResponseForbidden("🚫 You do not have permission to delete Purchase.")
    voucher = get_object_or_404(PurchaseMaster, pk=pk)
    voucher.delete()
    return redirect('item_master:purchase_voucher_list')


# @login_required(login_url='accounts_app:admin_login')
# def purchaseReturn_voucher_list(request):
#     # Check privilege for purchase listing
#     if not check_privilege(request.user, 3, "can_read"):   # 3 is the ID of the "Purchase" menu

#         return HttpResponseForbidden("🚫 You do not have permission to view Purchase.")
#     # Query all PurchaseVoucher objects from the database
#     vouchers = PurchaseReturnMaster.objects.all()

#     # Pass the vouchers to the template context
#     return render(request, 'purchaseReturn_voucher_list.html', {'vouchers': vouchers})


# @login_required(login_url='accounts_app:admin_login')
# def purchaseReturn_voucher_detail(request, voucher_id):
#     # Retrieve the PurchaseVoucher object and related PurchaseVoucherItem objects
#     voucher = get_object_or_404(PurchaseReturnMaster, id=voucher_id)
#     items = PurchaseReturnDetail.objects.filter(purchase__id=voucher.id)
#     # Pass the voucher and its items to the template context
#     return render(request, 'purchaseReturn_voucher_detail.html', {
#         'voucher': voucher,
#         'items': items
#     })    
    
    
# @require_POST
# def purchaseReturn_voucher_delete(request, pk):
#     # Check privilege for purchase delete
#     if not check_privilege(request.user, 3, "can_delete"):   # 3 is the ID of the "Purchase" menu

#         return HttpResponseForbidden("🚫 You do not have permission to delete Purchase.")
#     voucher = get_object_or_404(PurchaseReturnMaster, pk=pk)
#     voucher.delete()
#     return redirect('item_master:purchaseReturn_voucher_list')


    


    


@login_required(login_url='accounts_app:admin_login')        
def customer_management(request, customer_id=None):
    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id)  # For updating an existing customer
    else:
        customer = None  # For creating a new customer

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)  # Create or Update Customer form
        if form.is_valid():
            customer = form.save()  # Save the customer

            # Add the corresponding Ledger under "Sundry Debtor"
            sundry_debtors_group = GroupUnder.objects.filter(under_name="Sundry Debtors").first()
            if sundry_debtors_group:
                # Check if a ledger for this customer already exists
                existing_ledger = LedgerCreation.objects.filter(ledger_name=customer.customer_name, group_under=sundry_debtors_group).first()
                if not existing_ledger:
                    LedgerCreation.objects.create(
                        ledger_name=customer.customer_name,
                        group_under=sundry_debtors_group,
                        opening_balance=0.00,  # Default opening balance
                        types='DR',  # Default type as Debit
                        remark=f"Ledger for Customer {customer.customer_name}"
                    )
            else:
                # Log or handle the case where "Sundry Debtor" group doesn't exist
                print("Group 'Sundry Debtors' does not exist.")

            return redirect('item_master:customer_management')  # Redirect to the same page after save
    else:
        form = CustomerForm(instance=customer)

    # Fetch all customers to list them
    customers = Customer.objects.all()

    return render(request, 'customer_management.html', {'form': form, 'customers': customers, 'customer': customer})



@login_required(login_url='accounts_app:admin_login')
def sales_voucher_create(request):
    item_form = SalesVoucherItemForm()

    # Row validation via AJAX
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = SalesVoucherItemForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            item_data = {
                'item_name': cd['item_name'].id,
                'item_name_text': str(cd['item_name']),
                'item_code': cd['item_code'],
                'barcode_code': cd['barcode_code'],
                'quantity': float(cd['quantity']),
                'sales_rate': float(cd['sales_rate']),
                'item_net_amount': float(cd['item_net_amount']),
                'tax': float(cd['tax']),
                'item_tax_amount': float(cd['item_tax_amount']),
                'unit': cd['unit'].id if cd.get('unit') else None,
                'unit_text': str(cd['unit']) if cd.get('unit') else '',
                'item_total_amount': float(cd['item_total_amount']),
                'batch': cd['Batch'].id if cd.get('Batch') else None,
                'batch_text': str(cd['Batch']) if cd.get('Batch') else '',
                'mfd': cd['MFD'].isoformat() if cd.get('MFD') else '',
                'exp': cd['EXP'].isoformat() if cd.get('EXP') else ''
            }
            return JsonResponse({'status': 'success', 'item': item_data})
        return JsonResponse({'status': 'error', 'errors': form.errors})

    if request.method == 'POST':
        voucher_form = SalesVoucherForm(request.POST)
        items_raw = request.POST.get('items_data', '[]')
        try:
            voucher, _ = process_voucher(
                kind=VoucherKind.SALES,
                voucher_form=voucher_form,
                items_raw_json=items_raw,
            )
            
            #  Create LedgerPostings after SaleMaster saved
            create_ledger_postings_for_sale(voucher)
            
            messages.success(request, f"Sales voucher {voucher.voucher_no} created successfully.")
            return redirect('item_master:sales_voucher_list')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('item_master:sales_voucher_create')

    # GET
    voucher_form = SalesVoucherForm()
    vat_choices = [{'id': vat.id, 'TAX_percent': float(vat.TAX_percent)} for vat in TAX.objects.all()]
    customer_form = CustomerForm()
    return render(request, 'sales_voucher_create.html', {
        'voucher_form': voucher_form,
        'item_form': item_form,
        'VAT_CHOICES': json.dumps(vat_choices),
        'customer_form': customer_form,
    })
    
@login_required(login_url='accounts_app:admin_login')
def salesReturn_voucher_create(request):
    item_form = SalesReturnVoucherItemForm()

    # Row validation via AJAX
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = SalesReturnVoucherItemForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            item_data = {
                'item_name': cd['item_name'].id,
                'item_name_text': str(cd['item_name']),
                'item_code': cd['item_code'],
                'barcode_code': cd['barcode_code'],
                'quantity': float(cd['quantity']),
                'sales_rate': float(cd['sales_rate']),
                'item_net_amount': float(cd['item_net_amount']),
                'tax': float(cd['tax']),
                'item_tax_amount': float(cd['item_tax_amount']),
                'unit': cd['unit'].id if cd.get('unit') else None,
                'unit_text': str(cd['unit']) if cd.get('unit') else '',
                'item_total_amount': float(cd['item_total_amount']),
                'batch': cd['Batch'].id if cd.get('Batch') else None,
                'batch_text': str(cd['Batch']) if cd.get('Batch') else '',
                'mfd': cd['MFD'].isoformat() if cd.get('MFD') else '',
                'exp': cd['EXP'].isoformat() if cd.get('EXP') else ''
            }
            return JsonResponse({'status': 'success', 'item': item_data})
        return JsonResponse({'status': 'error', 'errors': form.errors})

    if request.method == 'POST':
        voucher_form = SalesReturnVoucherForm(request.POST)
        items_raw = request.POST.get('items_data', '[]')
        try:
            voucher, _ = process_voucher(
                kind=VoucherKind.SALES_RETURN,
                voucher_form=voucher_form,
                items_raw_json=items_raw,
            )
            messages.success(request, f"Sales Return voucher {voucher.voucher_no} created successfully.")
            return redirect('item_master:sales_voucher_list')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('item_master:sales_voucher_create')

    # GET
    voucher_form = SalesReturnVoucherForm()
    vat_choices = [{'id': vat.id, 'TAX_percent': float(vat.TAX_percent)} for vat in TAX.objects.all()]
    customer_form = CustomerForm()
    return render(request, 'salesReturn_voucher_create.html', {
        'voucher_form': voucher_form,
        'item_form': item_form,
        'VAT_CHOICES': json.dumps(vat_choices),
        'customer_form': customer_form,
    })
    
# def sales_voucher_create(request):
#     item_form = SalesVoucherItemForm()

#     if request.method == 'POST':
#         if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#             form = SalesVoucherItemForm(request.POST)
#             if form.is_valid():
#                 item_data = {
#                     'item_name': form.cleaned_data['item_name'].id,
#                     'item_name_text': str(form.cleaned_data['item_name']),
#                     'item_code': form.cleaned_data['item_code'],
#                     'barcode_code': form.cleaned_data['barcode_code'],
#                     'quantity': float(form.cleaned_data['quantity']),
#                     'sales_rate': float(form.cleaned_data['sales_rate']),
#                     'item_net_amount': float(form.cleaned_data['item_net_amount']),
#                     'tax': float(form.cleaned_data['tax']),
#                     'item_tax_amount': float(form.cleaned_data['item_tax_amount']),
#                     'unit': form.cleaned_data['unit'].id if form.cleaned_data['unit'] else None,
#                     'unit_text': str(form.cleaned_data['unit']) if form.cleaned_data['unit'] else '',
#                     'item_total_amount': float(form.cleaned_data['item_total_amount']),
#                     'batch': form.cleaned_data['Batch'].id if form.cleaned_data.get('Batch') else None,
#                     'batch_text': str(form.cleaned_data['Batch']) if form.cleaned_data.get('Batch') else '',
#                     'mfd': form.cleaned_data['MFD'].isoformat() if form.cleaned_data.get('MFD') else '',
#                     'exp': form.cleaned_data['EXP'].isoformat() if form.cleaned_data.get('EXP') else ''
#                 }
#                 return JsonResponse({'status': 'success', 'item': item_data})
#             return JsonResponse({'status': 'error', 'errors': form.errors})

#         voucher_form = SalesVoucherForm(request.POST)
        
#         items_data = json.loads(request.POST.get('items_data', '[]'))

#         if voucher_form.is_valid() and items_data:
#             try:
#                 with transaction.atomic():
#                     # 🔸 Generate voucher_no before saving
#                     voucher = voucher_form.save(commit=False)
                    
#                     voucher.save()

#                     for item_data in items_data:
#                         item_id = item_data['item_name']
#                         unit_id = item_data['unit']
#                         batch_id = item_data.get('batch')
#                         quantity = Decimal(item_data['quantity'])
#                         rate = Decimal(item_data['sales_rate'])

#                         item = get_object_or_404(Item, id=item_id)
#                         uc_factor = Decimal(1)

#                         # Convert to base unit if needed
#                         uc_factor = Decimal('1')
#                         if unit_id and str(unit_id) != str(item.item_unit_id):
#                             try:
#                                 alt_unit = ItemAlterUnit.objects.get(item=item, unit_id=unit_id)
#                                 uc_factor = alt_unit.uc_factor
#                             except ItemAlterUnit.DoesNotExist:
#                                 raise ValueError(f"Invalid unit for item {item.item_name}")

#                         base_quantity = quantity * uc_factor
#                         stock_value = rate * base_quantity

#                         # Fetch or create stock entry in base unit
#                         stock_entry, created = Stock.objects.get_or_create(
#                             item_id=item_id,
#                             batch_id=batch_id,
#                             unit_id=item.item_unit_id,  # Always in base unit
#                             defaults={
#                                 'voucherDate': voucher.transaction_date,
#                                 'voucherType': voucher.voucherType,
#                                 'voucherNo': voucher.id,
#                                 'costCenter': voucher.cost_center,
#                                 'rate': rate,
#                                 'in_quantity': 0,
#                                 'out_quantity': base_quantity,
#                                 'stock_value': -stock_value,
#                             }
#                         )

#                         if not created:
#                             # Adjust in_quantity and out_quantity
#                             if stock_entry.in_quantity >= base_quantity:
#                                 stock_entry.in_quantity -= base_quantity
#                             else:
#                                 shortfall = base_quantity - stock_entry.in_quantity
#                                 stock_entry.in_quantity = 0
#                                 stock_entry.out_quantity += shortfall

#                             stock_entry.stock_value -= stock_value
#                             stock_entry.save()

#                     # Update stock entry for unit
#                     if unit_id:
#                         stock_entry, created = Stock.objects.get_or_create(
#                             item_id=item_id,
#                             batch_id=batch_id,
#                             unit_id=unit_id,
#                             defaults={
#                                 'voucherDate': voucher.transaction_date,
#                                 'voucherType': voucher.voucherType,
#                                 'voucherNo': voucher.id,
#                                 'costCenter': voucher.cost_center,
#                                 'rate': rate,
#                                 'in_quantity': 0,
#                                 'out_quantity': quantity,
#                                 'stock_value': -stock_value,
#                             }
#                         )


#                         # Create sale item
#                         SalesDetail.objects.create(
#                             sales_voucher=voucher,
#                             item_name_id=item_id,
#                             item_code=item_data['item_code'],
#                             barcode_code=item_data['barcode_code'],
#                             quantity=quantity,
#                             sales_rate=rate,
#                             item_net_amount=Decimal(item_data['item_net_amount']),
#                             tax=Decimal(item_data['tax']),
#                             item_tax_amount=Decimal(item_data['item_tax_amount']),
#                             unit_id=unit_id if unit_id else None,
#                             item_total_amount=Decimal(item_data['item_total_amount']),
#                             Batch_id=batch_id if batch_id else None,
#                             MFD=item_data.get('mfd') or None,
#                             EXP=item_data.get('exp') or None
#                         )

#                     DayBookReport.objects.create(
#                         date=voucher.transaction_date,
#                         ledger=voucher.ledger,
#                         voucher_type='Sales ',
#                         debit_amount=voucher.grand_total_amount,
#                         credit_amount=0,
#                         invoice_no=voucher.voucher_no
#                     )

#                     if voucher.payment_mode == 'Credit':
#                         try:
#                             OutstandingReport.objects.create(
#                                 ledger=voucher.ledger,
#                                 bill_no=voucher.auto_no or "",  # Ensure no crash if auto_no is None
#                                 invoice_no=voucher.voucher_no,
#                                 transaction_type='Sales ',
#                                 debit_amount=voucher.grand_total_amount,
#                                 credit_amount=0,
#                                 balance_amount=voucher.grand_total_amount
#                             )
#                         except Exception as e:
#                             print(f"Outstanding creation failed: {e}")


#                     messages.success(request, f"Sales voucher {voucher.voucher_no} created successfully.")
#                     return redirect('item_master:sales_voucher_list')

#             except Exception as e:
#                 print(e)
#                 if 'voucher' in locals() and voucher.pk:
#                     voucher.delete()
#                 messages.error(request, f"An error occurred: {str(e)}")
#                 return redirect('item_master:sales_voucher_create')

#     else:
#         voucher_form = SalesVoucherForm()
        
        

#     vat_choices = [{'id': vat.id, 'TAX_percent': float(vat.TAX_percent)} for vat in TAX.objects.all()]
#     customer_form = CustomerForm()

#     return render(request, 'sales_voucher_create.html', {
#         'voucher_form': voucher_form,
#         'item_form': item_form,
#         'VAT_CHOICES': json.dumps(vat_choices),
#         'customer_form': customer_form,
#     })


    
@login_required(login_url='accounts_app:admin_login')
def sales_voucher_list(request):
    # Check privilege for Sales listing
    if not check_privilege(request.user, 1, "can_read"):   # 1 is the ID of the "Sales" menu

        return HttpResponseForbidden("🚫 You do not have permission to view Sales.")

    vouchers = SalesMaster.objects.all()
    return render(request, 'sales_voucher_list.html', {'vouchers': vouchers})


@login_required(login_url='accounts_app:admin_login')
def sales_voucher_detail(request, voucher_id):
    # Retrieve the SalesVoucher object and related SalesVoucherItem objects
    voucher = get_object_or_404(SalesMaster, id=voucher_id)
    items = SalesDetail.objects.filter(sales_voucher__id=voucher.id)

    # Pass the voucher and its items to the template context
    return render(request, 'sales_voucher_detail.html', {
        'voucher': voucher,
        'items': items
    })
    
# @login_required(login_url='accounts_app:admin_login')
# def salesReturn_voucher_list(request):
#     # Check privilege for Sales listing
#     if not check_privilege(request.user, 1, "can_read"):   # 1 is the ID of the "Sales" menu

#         return HttpResponseForbidden("🚫 You do not have permission to view Sales.")

#     vouchers = SalesReturnMaster.objects.all()
#     return render(request, 'salesReturn_voucher_list.html', {'vouchers': vouchers})


# @login_required(login_url='accounts_app:admin_login')
# def salesReturn_voucher_detail(request, voucher_id):
#     # Retrieve the SalesVoucher object and related SalesVoucherItem objects
#     voucher = get_object_or_404(SalesReturnMaster, id=voucher_id)
#     items = SalesReturnDetail.objects.filter(sales_voucher__id=voucher.id)

#     # Pass the voucher and its items to the template context
#     return render(request, 'salesReturn_voucher_detail.html', {
#         'voucher': voucher,
#         'items': items
#     })
    
    


def stock_list(request):
    base_unit_stocks = []

    # Get query parameters
    item_name = request.GET.get('item_name')
    item_code = request.GET.get('item_code')
    cost_center = request.GET.get('cost_center')
    batch = request.GET.get('batch')

    # Initial queryset
    all_stocks = Stock.objects.select_related('item', 'unit', 'costCenter', 'batch').all()

    # Apply filters
    if item_name:
        all_stocks = all_stocks.filter(item__item_name__icontains=item_name)

    if item_code:
        all_stocks = all_stocks.filter(item__item_code__icontains=item_code)

    if cost_center:
        all_stocks = all_stocks.filter(costCenter__name__icontains=cost_center)

    if batch:
        all_stocks = all_stocks.filter(batch__BatchNo__icontains=batch)

    # Filter for base unit and calculate stock value
    for stock in all_stocks:
        stock.stock_value = stock.in_quantity * stock.rate
        
        
        # Skip if both in and out quantities are 0
        if stock.in_quantity == 0 and stock.out_quantity == 0:
            continue    

        is_base = (
            ItemAlterUnit.objects.filter(item=stock.item, unit=stock.unit, is_base_unit=True).exists()
            or stock.unit == stock.item.item_unit
        )

        if is_base:
            has_alter_units = ItemAlterUnit.objects.filter(item=stock.item, is_base_unit=False).exists()
            stock.has_alter_units = has_alter_units
            base_unit_stocks.append(stock)

    context = {
        'stock_entries': base_unit_stocks,
    }

    return render(request, 'stock_list.html', context)

def get_alter_units_stock(request, item_id):
    alter_units = ItemAlterUnit.objects.select_related('unit').filter(item_id=item_id, is_base_unit=False)

    units = []
    for unit in alter_units:
        units.append({
            'unit_name': unit.unit.unit_name,
            'uc_factor': float(unit.uc_factor),
            'sales_rate': float(unit.sales_rate),  # Use alter unit's own rate
        })

    return JsonResponse({'units': units})

def outstanding_report_view(request):
    # Fetch all outstanding reports grouped by ledger (formerly vendor)
    outstanding_data = (
        OutstandingReport.objects
        .values('ledger__ledger_name')  # Group by ledger name
        .annotate(
            total_debit=Sum('debit_amount', default=0),  # Handle null values if any
            total_credit=Sum('credit_amount', default=0),  # Handle null values if any
            balance=Sum(F('debit_amount') - F('credit_amount'), default=0)  # Handle null values
        )
        .order_by('ledger__ledger_name')  # Optional: Order by ledger name
    )

    # Fetch individual transactions per ledger for detailed listing
    detailed_data = (
        OutstandingReport.objects
        .select_related('ledger')
        .order_by('ledger__ledger_name')
    )

    context = {
        'outstanding_data': outstanding_data,
        'detailed_data': detailed_data,
    }
    return render(request, 'outstanding_report.html', context)

def settle_bill(request):
    if request.method == 'POST':
        ledger_id = request.POST.get('ledger_id')  # Get selected ledger
        settle_data = request.POST.getlist('settle_amount')  # Get settle amounts
        outstanding_ids = request.POST.getlist('outstanding_id')  # Get outstanding record IDs

        for index, outstanding_id in enumerate(outstanding_ids):
            outstanding = get_object_or_404(OutstandingReport, id=outstanding_id)
            try:
                # Handle empty or invalid settle amounts
                settle_amount = float(settle_data[index]) if settle_data[index].strip() else 0.0
            except ValueError:
                return HttpResponseBadRequest(f"Invalid settle amount provided for index {index}: {settle_data[index]}")

            # Save settled amount
            BillByBill.objects.create(outstanding=outstanding, settle_amount=settle_amount)
            
            settle_amount = Decimal(settle_amount)  # Convert settle_amount to Decimal if it's a float
            # Update balance amount in OutstandingReport
            outstanding.balance_amount += settle_amount
            outstanding.settled_amount += settle_amount
            outstanding.save()

        return redirect('item_master:outstanding_report')

    ledgers = LedgerCreation.objects.filter(id__in=OutstandingReport.objects.values('ledger')).distinct()
    return render(request, 'settle_bill.html', {'ledgers': ledgers})

def get_outstanding_records(request):
    ledger_id = request.GET.get('ledger_id')
    outstanding_records = OutstandingReport.objects.filter(ledger_id=ledger_id)
    data = [
        {
            'id': record.id,
            'bill_no': record.bill_no,
            'invoice_no': record.invoice_no,
            'transaction_type': record.transaction_type,
            'balance_amount': str(record.balance_amount),
        }
        for record in outstanding_records
    ]
    return JsonResponse(data, safe=False)

def daybook_report_list(request):
    """
    View to list all DayBookReport entries.
    """
    daybook_records = DayBookReport.objects.all().order_by('-date')  # Order by most recent date
    return render(request, 'daybook.html', {'daybook_records': daybook_records})


# views.py


def get_outstanding_reports(request):
    ledger_id = request.GET.get('ledger_id')
    if ledger_id:
        # Fetch only reports where balance_amount is greater than zero
        reports = OutstandingReport.objects.filter(
            ledger_id=ledger_id,
            balance_amount__gt=0,  
            transaction_type__in=['Purchase']
        )
        
        data = list(reports.values('id', 'bill_no', 'invoice_no', 'transaction_type', 
                                 'debit_amount', 'credit_amount', 'balance_amount', 
                                 'settled_amount'))
        return JsonResponse({'reports': data})
    return JsonResponse({'reports': []})

def get_outstanding_reports_receipt(request):
    ledger_id = request.GET.get('ledger_id')
    if ledger_id:
        # Fetch only reports where balance_amount is greater than zero
        reports = OutstandingReport.objects.filter(
            ledger_id=ledger_id,
            balance_amount__gt=0,  
            transaction_type__in=['Sales']
        )
        
        data = list(reports.values('id', 'bill_no', 'invoice_no', 'transaction_type', 
                                 'debit_amount', 'credit_amount', 'balance_amount', 
                                 'settled_amount'))
        return JsonResponse({'reports': data})
    return JsonResponse({'reports': []})

@require_POST
def create_bill_by_bill(request):
    try:
        with transaction.atomic():  # Use transaction to ensure data consistency
            data = json.loads(request.POST.get('settle_amounts', '[]'))
            for item in data:
                # Get the outstanding report
                outstanding_report = OutstandingReport.objects.get(id=item['report_id'])
                settle_amount = Decimal(item['settle_amount'])
                
                # Validate settle amount
                remaining_balance = outstanding_report.balance_amount 
                if settle_amount > remaining_balance:
                    raise ValueError(f"Settle amount {settle_amount} exceeds remaining balance {remaining_balance}")
                
                # Create BillByBill entry
                BillByBill.objects.create(
                    outstanding=outstanding_report,
                    settle_amount=settle_amount
                )
                
                # Update OutstandingReport's settled amount
                outstanding_report.settled_amount += settle_amount
                outstanding_report.balance_amount -= settle_amount
                outstanding_report.save()
                
        return JsonResponse({
            'status': 'success',
            'message': 'Settlement recorded successfully'
        })
    except ValueError as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error processing settlement: {str(e)}'
        }, status=500)
        

def create_cost_center(request):
    if request.method == "POST":
        form = CostCenterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('item_master:cost_center_list')  # Redirect to list page after successful creation
    else:
        form = CostCenterForm()

    return render(request, 'cost_center_form.html', {'form': form})

def cost_center_list(request):
    cost_centers = CostCenter.objects.all()
    return render(request, 'cost_center_list.html', {'cost_centers': cost_centers})        

def create_opeingstock_voucher(request):
    # Create item_form at the beginning so it's available in all paths
    item_form = OpeningStockItemForm()
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX request for adding items
            form = OpeningStockItemForm(request.POST)
            if form.is_valid():
                item_data = {
                    'item_name': form.cleaned_data['item_name'].id,
                    'item_name_text': str(form.cleaned_data['item_name']),
                    'item_code': form.cleaned_data['item_code'],
                    'barcode_code': form.cleaned_data['barcode_code'],
                    'quantity': float(form.cleaned_data['quantity']),
                    'purchase_rate': float(form.cleaned_data['purchase_rate']),
                    'item_net_amount': float(form.cleaned_data['item_net_amount']),
                    'tax': float(form.cleaned_data['tax']),
                    'item_tax_amount': float(form.cleaned_data['item_tax_amount']),
                    'unit': form.cleaned_data['unit'].id if form.cleaned_data['unit'] else None,
                    'unit_text': str(form.cleaned_data['unit']) if form.cleaned_data['unit'] else '',
                    'free_quantity': float(form.cleaned_data['free_quantity'] or 0),
                    'manufacture_date': form.cleaned_data['manufacture_date'].strftime('%Y-%m-%d') if form.cleaned_data['manufacture_date'] else None,
                    'expire_date': form.cleaned_data['expire_date'].strftime('%Y-%m-%d') if form.cleaned_data['expire_date'] else None,
                    'sales_rate': float(form.cleaned_data['sales_rate']),
                    'profit': float(form.cleaned_data['profit']),
                    'item_total_amount': float(form.cleaned_data['item_total_amount'])
                }
                return JsonResponse({'status': 'success', 'item': item_data})
            return JsonResponse({'status': 'error', 'errors': form.errors})
        
        # Handle final form submission
        voucher_form = OpeningStockForm(request.POST)
        items_data = json.loads(request.POST.get('items_data', '[]'))
        
        if voucher_form.is_valid() and items_data:
            try:
                # Save the voucher first
                voucher = voucher_form.save()
                
                # Save all items and update stock
                for item_data in items_data:
                    # Create the purchase voucher item
                    purchase_item = OpeningStockDetail.objects.create(
                        opening_stock=voucher,
                        item_name_id=item_data['item_name'],
                        item_code=item_data['item_code'],
                        barcode_code=item_data['barcode_code'],
                        quantity=item_data['quantity'],
                        purchase_rate=item_data['purchase_rate'],
                        item_net_amount=item_data['item_net_amount'],
                        tax=item_data['tax'],
                        item_tax_amount=item_data['item_tax_amount'],
                        unit_id=item_data['unit'] if item_data['unit'] else None,
                        free_quantity=item_data.get('free_quantity', 0),
                        manufacture_date=item_data.get('manufacture_date'),
                        expire_date=item_data.get('expire_date'),
                        sales_rate=item_data['sales_rate'],
                        profit=item_data['profit'],
                        item_total_amount=item_data['item_total_amount']
                    )
                    
                    # Update stock for each item
                    try:
                        # Fetch all item variants of the same item_code
                        item_variants = Item.objects.filter(item_code=purchase_item.item_code)

                        # Identify the base unit item
                        base_item = item_variants.get(is_base_unit=True)

                        # Find the purchased item instance
                        purchased_item = item_variants.get(id=purchase_item.item_name.id)

                        # Initialize base unit stock quantity
                        if purchased_item.is_base_unit:
                            base_quantity = Decimal(purchase_item.quantity)
                        else:
                            base_quantity = Decimal(purchase_item.quantity) * Decimal(purchased_item.uc_factor)

                        # Now update stock for all units based on base_quantity
                        for variant in item_variants:
                            if variant.is_base_unit:
                                variant_quantity = base_quantity
                            else:
                                variant_quantity = base_quantity / Decimal(variant.uc_factor)

                            # Update or create the stock entry
                            stock, created = Stock.objects.get_or_create(
                                item_code=variant.item_code,
                                unit=variant.item_unit,
                                defaults={
                                    'item_name': variant,
                                    'quantity': 0,
                                    'purchase_rate': purchase_item.purchase_rate,
                                    'stock_value': 0,
                                    'cost_center': voucher.cost_center,
                                }
                            )

                            # ✅ Add to existing stock
                            stock.quantity += variant_quantity
                            stock.stock_value += variant_quantity * Decimal(purchase_item.purchase_rate)
                            stock.purchase_rate = purchase_item.purchase_rate  # Optional: update latest rate
                            stock.save()

                    except Item.DoesNotExist:
                        pass
                        
                # Update DayBookReport
                DayBookReport.objects.create(
                    date=voucher.transaction_date,
                    ledger=voucher.ledger,
                    voucher_type='Opening Stock',
                    debit_amount=0,
                    credit_amount=voucher.grand_total_amount,
                    invoice_no=voucher.voucher_no
                )        
                
               
                
                
                return redirect('item_master:purchase_voucher_list')  # Redirect to your list view
                
            except Exception as e:
                # If there's an error, rollback the voucher creation
                if 'voucher' in locals():
                    voucher.delete()
                raise e
    else:
        voucher_form = OpeningStockForm()
    
    vat_choices = [{'id': vat.id, 'VAT_percent': float(vat.VAT_percent)} 
                   for vat in TAX.objects.all()]    
    
    return render(request, 'opening_stock_create.html', {
        'voucher_form': voucher_form,
        'item_form': item_form,
        'VAT_CHOICES': json.dumps(vat_choices),
    })
    
@login_required(login_url='accounts_app:admin_login')
def opening_stock_list(request):
    # Query all PurchaseVoucher objects from the database
    vouchers = OpeningStockMaster.objects.all()

    # Pass the vouchers to the template context
    return render(request, 'opening_stock_list.html', {'vouchers': vouchers})


@login_required(login_url='accounts_app:admin_login')
def opening_stock_detail(request, voucher_id):
    # Retrieve the PurchaseVoucher object and related PurchaseVoucherItem objects
    voucher = get_object_or_404(OpeningStockMaster, id=voucher_id)
    items = OpeningStockDetail.objects.filter(opening_stock__id=voucher.id)
    # Pass the voucher and its items to the template context
    return render(request, 'opening_stock_detail.html', {
        'voucher': voucher,
        'items': items
    })    
    

    
def get_item_alter_units(request, item_id):
    alter_units = ItemAlterUnit.objects.filter(item_id=item_id)
    data = []
    for unit in alter_units:
        data.append({
            'unit_id': unit.unit.id,
            'unit_code': unit.unit.unit_code,
            'unit_name': unit.unit.unit_name,
            'barcode_code': unit.barcode_code,
            'purchase_rate': str(unit.purchase_rate),
            'sales_rate': str(unit.sales_rate),
            'uc_factor': str(unit.uc_factor),
        })
    return JsonResponse({'units': data})


#Unit modal
def create_unit_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        unit_code = data.get('unit_code')
        unit_name = data.get('unit_name')

        if not unit_code or not unit_name:
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        if Unit.objects.filter(unit_code=unit_code).exists():
            return JsonResponse({'success': False, 'error': 'Unit code already exists.'})

        unit = Unit.objects.create(unit_code=unit_code, unit_name=unit_name)
        return JsonResponse({
            'success': True,
            'unit_id': unit.id,
            'unit_name': unit.unit_name
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def create_cost_center_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        code = data.get('code')
        description = data.get('description')

        if not name or not code:
            return JsonResponse({'success': False, 'error': 'Name and Code are required.'})

        if CostCenter.objects.filter(name=name).exists() or CostCenter.objects.filter(code=code).exists():
            return JsonResponse({'success': False, 'error': 'Name or Code already exists.'})

        cost_center = CostCenter.objects.create(name=name, code=code, description=description)
        return JsonResponse({'success': True, 'id': cost_center.id, 'name': cost_center.name})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


def create_vat_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        percent = data.get('vat_percent')
        name = data.get('vat_name')

        if not percent:
            return JsonResponse({'success': False, 'error': 'VAT percentage is required.'})

        try:
            percent_val = float(percent)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid VAT percentage.'})

        vat = TAX.objects.create(TAX_percent=percent_val, TAX_name=name or "")
        label = f"{vat.TAX_percent}%"
        return JsonResponse({'success': True, 'id': vat.id, 'text': label})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def create_category_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required.'})

        category = ItemCategory.objects.create(category_name=name)
        return JsonResponse({'success': True, 'id': category.id, 'name': category.category_name})
    
def create_manufacturer_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        name = data.get('name')
        if not name:
            return JsonResponse({'success': False, 'error': 'Name is required.'})

        manufacturer = ItemManufacturer.objects.create(manufacturer_name=name)
        return JsonResponse({'success': True, 'id': manufacturer.id, 'name': manufacturer.manufacturer_name})    
    
def batch_create_update(request, pk=None):
    batch = get_object_or_404(Batch, pk=pk) if pk else None

    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            return redirect('item_master:batch_list')  # Create batch_list view if needed
    else:
        form = BatchForm(instance=batch)

    return render(request, 'batch_form.html', {
        'form': form, 
        'batch': batch,
        'error_message': form.errors.get('__all__')  # Pass any form errors to template
    })
    
def batch_list(request):
    batches = Batch.objects.select_related('Item').all()
    return render(request, 'batch_list.html', {'batches': batches})

def create_batch_modal(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        batch_no = data.get('batch_no')
        item_id = data.get('item_id')
        mfd = data.get('mfd') or None
        exp = data.get('exp') or None
        is_active = data.get('is_active', False)

        if not batch_no or not item_id:
            return JsonResponse({'success': False, 'error': 'Batch number and Item are required.'})

        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected item does not exist.'})

        # Check if batch with same number exists for this item
        if Batch.objects.filter(BatchNo=batch_no, Item=item).exists():
            return JsonResponse({
                'success': False, 
                'error': f'A batch with number "{batch_no}" already exists for this item.'
            })

        try:
            batch = Batch.objects.create(
                BatchNo=batch_no,
                Item=item,
                Mfd=mfd,
                Exp=exp,
                IsActive=is_active
            )
            return JsonResponse({'success': True, 'id': batch.id, 'name': batch.BatchNo})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

def voucher_create_update(request, pk=None):
    if pk:
        voucher = get_object_or_404(Vouchers, pk=pk)
    else:
        voucher = None

    if request.method == 'POST':
        form = VouchersForm(request.POST, instance=voucher)
        if form.is_valid():
            form.save()
            return redirect('item_master:voucher_list')  # Make sure you define this view too
    else:
        form = VouchersForm(instance=voucher)

    return render(request, 'voucher_form.html', {'form': form, 'voucher': voucher})

def voucher_list(request):
    vouchers = Vouchers.objects.all()
    return render(request, 'voucher_list.html', {'vouchers': vouchers})


# Create a view to fetch batches for a specific item
def get_item_batches(request):
    item_id = request.GET.get('item_id')
    if not item_id:
        return JsonResponse({'batches': []})
    
    # Get all batches related to the selected item
    batches = Batch.objects.filter(Item_id=item_id)
    
    # Format the data to return
    batch_data = []
    for batch in batches:
        batch_data.append({
            'id': batch.id,
            'batch_no': batch.BatchNo,
            'mfd': batch.Mfd.strftime('%Y-%m-%d') if batch.Mfd else '',
            'exp': batch.Exp.strftime('%Y-%m-%d') if batch.Exp else ''
        })
    
    return JsonResponse({'batches': batch_data})

# Item form barcode field hide 
def get_item_barcode_status(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
        return JsonResponse({'IsItemBarcode': item.IsItemBarcode})
    except Item.DoesNotExist:
        return JsonResponse({'IsItemBarcode': True})  # default hide
 
 
# PurchaseDetail form batch, mfd, exp field hide     
def get_item_batch_status(request, item_id):
    try:
        item = Item.objects.get(id=item_id)
        return JsonResponse({'IsBatch': item.IsBatch})
    except Item.DoesNotExist:
        return JsonResponse({'IsBatch': False})  # Default: hide fields    
    
    
def get_next_voucher_number(request):
    """AJAX view to get next voucher number"""
    print(f"AJAX Request received: {request.GET}")  # Debug print
    
    if request.method == 'GET' and 'voucher_type_id' in request.GET:
        try:
            voucher_type_id = request.GET['voucher_type_id']
            print(f"Looking for voucher type ID: {voucher_type_id}")  # Debug print
            
            voucher_type = Vouchers.objects.get(pk=voucher_type_id)
            print(f"Found voucher type: {voucher_type}")  # Debug print
            
            next_number = voucher_type.get_next_voucher_number()
            print(f"Generated voucher number: {next_number}")  # Debug print
            
            return JsonResponse({
                'voucher_number': next_number,
                'success': True
            })
        except Vouchers.DoesNotExist:
            print(f"Voucher type not found for ID: {voucher_type_id}")  # Debug print
            return JsonResponse({'error': 'Voucher type not found'}, status=404)
        except Exception as e:
            print(f"Error generating voucher number: {str(e)}")  # Debug print
            return JsonResponse({'error': str(e)}, status=500)
    
    print("Invalid request parameters")  # Debug print
    return JsonResponse({'error': 'Invalid request'}, status=400)



@require_http_methods(["GET", "POST"])
def create_stock_transfer(request):
    if request.method == "GET":
        transfer_form = StockTransferForm()
        item_form = StockTransferItemForm()
        
        # Add this line to get all items for the dropdown
        items = Item.objects.filter(isDeleted=False).order_by('item_name')
        
        # Also get batches if needed
        batches = Batch.objects.all().order_by('BatchNo')
        
        return render(request, "stock_transfer.html", {
            "transfer_form": transfer_form,
            "item_form": item_form,
            "items": items,  # Pass items to template
            "batches": batches,  # Pass batches to template
        })

    elif request.method == "POST":
        transfer_form = StockTransferForm(request.POST)
        items_data_str = request.POST.get("items_data", "[]")
        
        # Debug logging
        print(f"Items data received: {items_data_str}")
        
        try:
            items_data = json.loads(items_data_str)
        except json.JSONDecodeError as e:
            messages.error(request, f"Invalid JSON data: {e}")
            return redirect("item_master:stock_transfer")
        
        print(f"Parsed items data: {items_data}")
        print(f"Form valid: {transfer_form.is_valid()}")
        print(f"Items count: {len(items_data)}")
        
        if not transfer_form.is_valid():
            messages.error(request, f"Form errors: {transfer_form.errors}")
            return redirect("item_master:stock_transfer")
            
        if not items_data:
            messages.error(request, "No items provided for transfer.")
            return redirect("item_master:stock_transfer")

        if transfer_form.is_valid() and items_data:
            try:
                with transaction.atomic():
                    transfer = transfer_form.save()

                    for item_data in items_data:
                        print(f"Processing item: {item_data}")
                        
                        item = get_object_or_404(Item, id=item_data['item'])
                        unit_id = item_data['unit']
                        quantity = Decimal(str(item_data['quantity']))
                        batch_id = item_data.get('batch') if item_data.get('batch') else None
                        rate = Decimal(str(item_data['rate']))
                        
                        print(f"Item: {item.item_name}, Unit: {unit_id}, Quantity: {quantity}, Batch: {batch_id}, Rate: {rate}")

                        uc_factor = Decimal(1)
                        if str(unit_id) != str(item.item_unit_id):
                            alt_unit = ItemAlterUnit.objects.filter(item=item, unit_id=unit_id).first()
                            if not alt_unit:
                                raise ValueError(f"Unit mismatch for item {item.item_name}")
                            uc_factor = alt_unit.uc_factor

                        base_quantity = quantity * uc_factor
                        stock_value = rate * base_quantity

                        # Check if source stock exists
                        source_stock = Stock.objects.filter(
                            item=item, unit_id=item.item_unit_id, costCenter=transfer.source_cost_center
                        ).first()
                        if not source_stock or source_stock.in_quantity < base_quantity:
                            raise ValueError(f"Insufficient stock for item {item.item_name} in source cost center.")

                        # Reduce from source
                        source_stock.in_quantity -= base_quantity
                        source_stock.out_quantity += base_quantity
                        source_stock.stock_value -= stock_value
                        source_stock.save()

                        # Get or create voucher type
                        voucher_type, _ = Vouchers.objects.get_or_create(
                            VoucherName='Stock Transfer',
                            defaults={
                                'VoucherName': 'Stock Transfer',
                                'VoucherType': 'Stock Transfer'
                            }
                        )
                        
                        # Add to destination
                        destination_stock, created = Stock.objects.get_or_create(
                            item=item, unit_id=item.item_unit_id,
                            costCenter=transfer.destination_cost_center,
                            defaults={
                                'voucherDate': transfer.transfer_date,
                                'voucherType': voucher_type,
                                'voucherNo': transfer.voucher_no,
                                'rate': rate,
                                'in_quantity': base_quantity,
                                'out_quantity': 0,
                                'stock_value': stock_value
                            }
                        )

                        if not created:
                            destination_stock.in_quantity += base_quantity
                            destination_stock.stock_value += stock_value
                            destination_stock.save()

                        # Save the transfer item
                        StockTransferItem.objects.create(
                            stock_transfer=transfer,
                            item=item,
                            unit_id=unit_id,
                            batch_id=batch_id,
                            quantity=quantity,
                            rate=rate,
                        )

                    messages.success(request, f"Stock Transfer {transfer.voucher_no} created.")
                    return redirect("item_master:stock_transfer")

            except Exception as e:
                print(f"Exception during stock transfer: {e}")
                messages.error(request, f"Error: {e}")
                return redirect("item_master:stock_transfer")
        else:
            error_msg = "Form validation failed"
            if not transfer_form.is_valid():
                error_msg += f" - Form errors: {transfer_form.errors}"
            if not items_data:
                error_msg += " - No items provided"
            messages.error(request, error_msg)
            return redirect("item_master:stock_transfer")
        
        
def get_item_units_rate(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    base_unit = {'id': item.item_unit.id, 'name': item.item_unit.unit_name}
    alt_units = list(ItemAlterUnit.objects.filter(item=item).values('unit_id', 'unit__unit_name'))
    units = [base_unit] + [{'id': u['unit_id'], 'name': u['unit__unit_name']} for u in alt_units]

    return JsonResponse({
        'units': units,
        'rate': float(item.purchase_rate or 0)
    })

def get_item_batches_stocktransfer(request, item_id):
    """Get batches for a specific item"""
    try:
        item = get_object_or_404(Item, pk=item_id)
        batches = Batch.objects.filter(Item=item).values('id', 'BatchNo', 'Exp')
        
        # Format the response
        batch_list = []
        for batch in batches:
            batch_display = batch['BatchNo'] or f"Batch {batch['id']}"
            if batch['Exp']:
                batch_display += f" (Exp: {batch['Exp'].strftime('%Y-%m-%d')})"
            
            batch_list.append({
                'id': batch['id'],
                'BatchNo': batch_display
            })
        
        return JsonResponse({'batches': batch_list})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)  
    
def get_items_by_costcenter(request, cost_center_id):
    # Get items with positive stock in this cost center
    item_ids = (
        Stock.objects
        .filter(costCenter_id=cost_center_id, in_quantity__gt=0)
        .values_list('item_id', flat=True)
        .distinct()
    )
    items = Item.objects.filter(id__in=item_ids, isDeleted=False)
    # Prepare list for response
    response = [
        {"id": item.id, "item_name": item.item_name, "item_code": item.item_code}
        for item in items
    ]
    return JsonResponse(response, safe=False)    
# def get_items_for_cost_center(request, cost_center_id):
#     items = Stock.objects.filter(costCenter_id=cost_center_id).select_related('item').values('item_id', 'item__name').distinct()
#     return JsonResponse(list(items), safe=False)    
    
    
def sales_return_list(request):
    sales_return_type = get_object_or_404(Vouchers, VoucherType="Sales Return")
    sales_returns = PurchaseMaster.objects.filter(voucherType=sales_return_type, isDeleted=False).order_by('-transaction_date')
    return render(request, 'sales_return_list.html', {'sales_returns': sales_returns})


def sales_return_detail(request, pk):
    purchase = get_object_or_404(PurchaseMaster, pk=pk, voucherType__VoucherType="Sales Return", isDeleted=False)
    items = PurchaseDetail.objects.filter(purchase=purchase)
    return render(request, 'sales_return_detail.html', {'purchase': purchase, 'items': items})


def purchase_return_list(request):
    purchase_return_type = get_object_or_404(Vouchers, VoucherType="Purchase Return")
    purchase_returns = SalesMaster.objects.filter(voucherType=purchase_return_type, isDeleted=False).order_by('-transaction_date')
    return render(request, 'purchase_return_list.html', {'purchase_returns': purchase_returns})


def purchase_return_detail(request, pk):
    sale = get_object_or_404(SalesMaster, pk=pk, voucherType__VoucherType="Purchase Return", isDeleted=False)
    items = SalesDetail.objects.filter(sales_voucher=sale)
    return render(request, 'purchase_return_detail.html', {'sale': sale, 'items': items})


def get_stock_quantity(request):
    item_id = request.GET.get('item_id')
    unit_id = request.GET.get('unit_id')  # This is now just for reference
    batch_id = request.GET.get('batch_id')
    cost_center_id = request.GET.get('cost_center_id')

    if item_id and cost_center_id:
        # ✅ Get the base unit for this item
        try:
            item = Item.objects.get(id=item_id)
            base_unit_id = item.item_unit_id  # Adjust field name if different
        except Item.DoesNotExist:
            return JsonResponse({'stock_quantity': None}, status=400)

        filters = {
            'item_id': item_id,
            'unit_id': base_unit_id,  # ✅ Always use base unit for stock query
            'costCenter_id': cost_center_id
        }
        if batch_id:
            filters['batch_id'] = batch_id

        stock_entries = Stock.objects.filter(**filters)
        total_qty = sum(entry.in_quantity - entry.out_quantity for entry in stock_entries)

        return JsonResponse({'stock_quantity': float(total_qty)})
    
    return JsonResponse({'stock_quantity': None}, status=400)

def get_item_stock(request, cost_center_id, item_id):
    # Optional: can also filter by batch and unit if needed
    stock = (
        Stock.objects
        .filter(costCenter_id=cost_center_id, item_id=item_id)
        .aggregate(total_qty=models.Sum('in_quantity'))
    )
    qty = stock['total_qty'] or 0
    return JsonResponse({'quantity': qty})


def filter_ledgers_view_purchase(request):
    is_customer = request.GET.get("customer") == "1"

    if is_customer:
        queryset = get_ledgers_by_group_ids(29)   # Customer group
    else:
        queryset = get_ledgers_by_group_ids(8, 28)  # Cash & Sundry Creditors

    data = [
        {"id": ledger.id, "name": str(ledger.ledger_name)}  # adjust field name if needed
        for ledger in queryset
    ]
    return JsonResponse(data, safe=False)

def filter_ledgers_sales_view(request):
    is_vendor = request.GET.get("vendor") == "1"

    if is_vendor:
        queryset = get_ledgers_by_group_ids(28)   # Vendor group
    else:
        queryset = get_ledgers_by_group_ids(8, 29)  # Cash + Sundry Debtors

    data = [
        {"id": ledger.id, "name": str(ledger.ledger_name)}
        for ledger in queryset
    ]
    return JsonResponse(data, safe=False)