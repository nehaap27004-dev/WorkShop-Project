from fleet_app.reports import create_purchase_pdf
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
from .common import *
from fleet_app.common import *
from fleet_app.models import SpareParts
from accounts_app.views import update_purchase_cleared_status




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

def item_category_delete(request, category_id):
    category = get_object_or_404(ItemCategory, id=category_id)
    category.delete()
    return redirect('item_master:item_category_create_update_list')  


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

    
def item_manufacturer_delete(request, manufacturer_id):
    manufacturer = get_object_or_404(ItemManufacturer, id=manufacturer_id)
    manufacturer.delete()
    return redirect('item_master:item_manufacturer_create_update_list')    
    

#create , edit , list , delete item group    
@login_required(login_url='accounts_app:admin_login')
def manage_item_group(request, group_id=None):
    if group_id:
        group = get_object_or_404(ItemGroup, id=group_id)
    else:
        group = None

    if request.method == 'POST':
        form = ItemGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('item_master:manage_item_group')  # Redirect back to the same page after saving
    else:
        form = ItemGroupForm(instance=group)

    # Handle listing functionality
    groups = ItemGroup.objects.all()

    return render(request, 'item_group_form.html', {
        'form': form,
        'groups': groups,
        'group': group
    })    

def delete_item_group(request, group_id):
    group = get_object_or_404(ItemGroup, id=group_id)
    group.delete()
    return redirect('item_master:manage_item_group')    
    
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

                    # Item Name
                    if Item.objects.filter(item_name=base_item.item_name).exclude(pk=base_item.pk).exists():
                        form.add_error('item_name', 'Item Name already exists.')
                        raise ValueError("Item Name already exists.")

                    # Item Code
                    if Item.objects.filter(item_code=base_item.item_code).exclude(pk=base_item.pk).exists():
                        form.add_error('item_code', 'Item Code already exists.')
                        raise ValueError("Item Code already exists.")

                    # Barcode
                    if base_item.barcode_code:
                        if Item.objects.filter(barcode_code=base_item.barcode_code).exclude(pk=base_item.pk).exists():
                            form.add_error('barcode_code', 'Barcode already exists.')
                            raise ValueError("Barcode already exists.")    

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

            except ValueError:
                pass

            except IntegrityError as e:
                form.add_error(None, "Duplicate value found. Item Name, Item Code or Barcode must be unique.")

            except Exception as e:
                import traceback
                traceback.print_exc()
                form.add_error(None, str(e))  

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

def unit_delete(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id)
    unit.delete()
    return redirect('item_master:unit_manage')

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

def vat_delete(request, TAX_id):
    tax = get_object_or_404(TAX, id=TAX_id)
    tax.delete()
    return redirect('item_master:VAT_manage')   


@login_required(login_url='accounts_app:admin_login')
# ----------------- CREATE -----------------
@require_http_methods(["GET", "POST"])
def create_itemgrv_voucher(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Item GRV.")

    template_name = 'item_grv_form.html'

    if request.method == "GET":
        voucher_form = ItemGrvForm()
        voucher_form.fields['transaction_date']

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": ItemGrvItemForm(),
            "items": Item.objects.all(),
            "is_edit": False
        })

    # POST create
    voucher_form = ItemGrvForm(request.POST)
    items_raw = request.POST.get("items_data", "[]")

    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.ITEM_GRV,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )
                
                # create_ledger_postings_for_purchase(voucher)
                # # 🔥 UPDATE CLEARING STATUS
                # update_purchase_cleared_status(voucher.id)
                
                messages.success(request, f"✅ Item GRV {voucher.voucher_no} created successfully.")
                return redirect('item_master:itemgrv_voucher_list')
        except Exception as e:
            messages.error(request, f"Error creating voucher: {e}")
    else:
        # Show form validation errors
        messages.error(request, "⚠️ Please correct the errors below.")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": ItemGrvItemForm(),
        "items": Item.objects.all(),
        "is_edit": False
    })


# ----------------- EDIT -----------------
@require_http_methods(["GET", "POST"])
def edit_itemgrv_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Item GRV.")

    template_name = 'item_grv_form.html'
    voucher = get_object_or_404(ItemGrvMaster, pk=pk)

    if request.method == "GET":
        voucher_form = ItemGrvForm(instance=voucher)
        item_formset = ItemGrvItemFormSet(instance=voucher)

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": ItemGrvItemForm(),
            "item_formset": item_formset,
            "items": Item.objects.all(),
            "is_edit": True,
        })

    # POST update
    voucher_form = ItemGrvForm(request.POST, instance=voucher)
    item_formset = ItemGrvItemFormSet(request.POST, instance=voucher)

    try:
        with transaction.atomic():
            if voucher_form.is_valid() and item_formset.is_valid():

                # Save voucher
                voucher = voucher_form.save()

                # -------------------------------
                # 1. REVERSE OLD STOCK
                # -------------------------------
                old_details = ItemGrvDetail.objects.filter(item_grv=voucher)

                for d in old_details:
                    item = Item.objects.get(id=d.item_name_id)

                    base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)

                    upsert_stock(
                        item=item,
                        batch_id=d.Batch_id,
                        base_unit_id=item.item_unit_id,
                        base_qty_delta=base_qty,
                        rate=d.purchase_rate,
                        voucher_date=voucher.transaction_date,
                        voucher_type=voucher.voucherType,
                        voucher_id=voucher.id,
                        cost_center=voucher.cost_center,
                    )

                # -------------------------------
                # 2. DELETE OLD DETAILS
                # -------------------------------
                old_details.delete()

                # -------------------------------
                # 3. SAVE NEW DETAILS
                # -------------------------------
                item_formset.instance = voucher
                new_details = item_formset.save()

                # -------------------------------
                # 4. POST STOCK AGAIN
                # -------------------------------
                for d in new_details:
                    item = Item.objects.get(id=d.item_name_id)

                    base_qty = to_base_qty(item, d.unit_id, d.quantity)

                    upsert_stock(
                        item=item,
                        batch_id=d.Batch_id,
                        base_unit_id=item.item_unit_id,
                        base_qty_delta=base_qty,
                        rate=d.purchase_rate,
                        voucher_date=voucher.transaction_date,
                        voucher_type=voucher.voucherType,
                        voucher_id=voucher.id,
                        cost_center=voucher.cost_center,
                    )

                # # Ledger repost
                # create_ledger_postings_for_purchase(voucher)
                # # 🔥 UPDATE CLEARING STATUS AFTER EDIT
                # update_purchase_cleared_status(voucher.id)

                messages.success(request, f"✏️ Item GRV {voucher.voucher_no} updated successfully.")
                return redirect('item_master:itemgrv_voucher_list')

            else:
                messages.error(request, "⚠️ Please correct the errors below.")

    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": ItemGrvItemForm(),
        "item_formset": item_formset,
        "items": Item.objects.all(),
        "is_edit": True,
    })

@require_POST
def itemgrv_delete(request, pk):
    if not check_privilege(request.user, 3, "can_delete"):
        return HttpResponseForbidden("🚫 You do not have permission to delete Item GRV.")

    voucher = get_object_or_404(ItemGrvMaster, pk=pk)

    try:
        with transaction.atomic():

            # ---------------------------------
            # 1. REVERSE STOCK
            # ---------------------------------
            details = ItemGrvDetail.objects.filter(item_grv=voucher)

            for d in details:
                item = Item.objects.get(id=d.item_name_id)

                # Purchase = IN → reverse = OUT
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)

                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.purchase_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )

            # # ---------------------------------
            # # 2. DELETE LEDGER
            # # ---------------------------------
            # delete_ledger_postings(voucher.voucherType_id, voucher.id)

            # ---------------------------------
            # 3. DELETE DETAILS
            # ---------------------------------
            details.delete()

            # ---------------------------------
            # 4. DELETE VOUCHER
            # ---------------------------------
            voucher.delete()

            messages.success(request, "🗑️ Item GRV deleted successfully.")

    except Exception as e:
        messages.error(request, f"❌ Error deleting voucher: {str(e)}")

    return redirect('item_master:itemgrv_voucher_list')

@login_required(login_url='accounts_app:admin_login')
def itemgrv_list(request):
    # Check privilege for purchase listing
    if not check_privilege(request.user, 3, "can_read"):   # 3 is the ID of the "Purchase" menu

        return HttpResponseForbidden("🚫 You do not have permission to view Purchase.")
    # Query all PurchaseVoucher objects from the database
    vouchers = ItemGrvMaster.objects.all()

    # Pass the vouchers to the template context
    return render(request, 'itemgrv_list.html', {'vouchers': vouchers})    


# ─────────────────────────────────────────────────────────────────────────────
# AJAX HELPERS
# ─────────────────────────────────────────────────────────────────────────────
 
@login_required(login_url='accounts_app:admin_login')
def get_uninvoiced_grvs(request):
    """Returns all ItemGRV records that have not yet been invoiced."""
    grvs = (
        ItemGrvMaster.objects
        .filter(IsInvoiced=False, isDeleted=False)
        .order_by('-transaction_date')
        .values('id', 'voucher_no', 'transaction_date')
    )
    return JsonResponse({'grvs': list(grvs)})
 
 
@login_required(login_url='accounts_app:admin_login')
def get_grv_details_for_purchase(request):
    """Returns GRV master + line items to pre-fill the purchase form."""
    grv_id = request.GET.get('grv_id', '').strip()
    if not grv_id:
        return JsonResponse({'status': 'error', 'message': 'grv_id is required'}, status=400)
 
    grv = get_object_or_404(ItemGrvMaster, pk=grv_id, IsInvoiced=False, isDeleted=False)
 
    master = {
        'ledger_id':        grv.ledger_id,
        'ledger_name':      str(grv.ledger) if grv.ledger else '',
        'cost_center_id':   grv.cost_center_id,
        'transaction_date': str(grv.transaction_date),
        'lrNo':             grv.lrNo or '',
        'transportCompany': grv.transportCompany or '',
        'Freight':          str(grv.Freight),
        'remarks':          grv.remarks or '',
    }
 
    details = []
    for d in grv.items.select_related('item_name', 'unit', 'Batch').all():
        # Use the GRV Cost field as the suggested purchase_rate
        purchase_rate = float(d.Cost or 0)
        quantity      = float(d.quantity or 0)
        tax_pct       = float(d.tax or 0)

        net_amount    = quantity * purchase_rate
        tax_amount    = round(net_amount * tax_pct / 100, 3)
        total_amount  = round(net_amount + tax_amount, 3)

        details.append({
            'item_name_id':   d.item_name_id,
            'item_name_text': d.item_name.item_name if d.item_name else '',

            'item_code':      d.item_code or '',
            'barcode_code':   d.barcode_code or '',

            'quantity':       quantity,

            'unit_id':        d.unit_id or '',
            'unit_text':      str(d.unit) if d.unit else '',

            'tax':            tax_pct,

            'free_quantity':  d.free_quantity or 0,

            'batch_id':       d.Batch_id or '',
            'batch_text':     str(d.Batch) if d.Batch else '',

            'mfd':            str(d.MFD) if d.MFD else '',
            'exp':            str(d.EXP) if d.EXP else '',

            'serial_no':      d.SerialNo or '',
            'cess':           float(d.Cess or 0),

            'cost':           float(d.Cost or 0),

            # calculated for purchase only
            'purchase_rate':    purchase_rate,
            'item_net_amount':  round(net_amount, 3),
            'item_tax_amount':  tax_amount,
            'item_total_amount': total_amount,

            # purchase-only defaults
            'sales_rate':      0,
            'profit':          0,
        })
 
    return JsonResponse({'status': 'success', 'master': master, 'details': details})
    




# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE CREATE
# ─────────────────────────────────────────────────────────────────────────────
 
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def create_purchase_voucher(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Purchase.")
 
    template_name = 'purchase_form1.html'
 
    if request.method == "GET":
        voucher_form = PurchaseVoucherForm()
        voucher_form.fields['transaction_date']
        voucher_form.fields['InvoiceDate']
 
        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form":    PurchaseVoucherItemForm(),
            "items":        Item.objects.all(),
            "item_groups":  ItemGroup.objects.all(),
            "is_edit":      False,
            "linked_grv":   None,
        })
 
    # ── POST ──────────────────────────────────────────────────────────────
    voucher_form = PurchaseVoucherForm(request.POST)
    items_raw    = request.POST.get("items_data", "[]")
    grv_id       = request.POST.get("item_grv_id", "").strip()
 
    if voucher_form.is_valid():
        try:
            with transaction.atomic():
 
                if grv_id:
                    # ── GRV-LINKED PATH ───────────────────────────────────
                    # Stock already posted at GRV stage – do NOT call upsert_stock.
                    grv = get_object_or_404(
                        ItemGrvMaster, pk=grv_id, IsInvoiced=False, isDeleted=False
                    )
 
                    voucher = voucher_form.save(commit=False)
                    voucher.item_grv = grv
                    voucher.save()
 
                    items_data = json.loads(items_raw)
                    for d in items_data:
                        PurchaseDetail.objects.create(
                            purchase          = voucher,
                            item_group_id     = d.get('item_group_id') or None, 
                            item_name_id      = d.get('item_name_id') or None,
                            item_code         = d.get('item_code', ''),
                            barcode_code      = d.get('barcode_code', ''),
                            quantity          = d.get('quantity') or 0,
                            purchase_rate     = d.get('purchase_rate') or 0,
                            item_net_amount   = d.get('item_net_amount') or 0,
                            tax               = d.get('tax') or 0,
                            item_tax_amount   = d.get('item_tax_amount') or 0,
                            unit_id           = d.get('unit_id') or None,
                            free_quantity     = d.get('free_quantity') or 0,
                            MFD               = d.get('mfd') or None,
                            EXP               = d.get('exp') or None,
                            sales_rate        = d.get('sales_rate') or 0,
                            profit            = d.get('profit') or 0,
                            item_total_amount = d.get('item_total_amount') or 0,
                            Batch_id          = d.get('batch_id') or None,
                            Cost              = d.get('cost') or 0,
                            SerialNo          = d.get('serial_no', ''),
                            Cess              = d.get('cess') or 0,
                        )
 
                    create_ledger_postings_for_purchase(voucher)
                    update_purchase_cleared_status(voucher.id)
 
                    # Mark GRV as fully invoiced
                    grv.IsInvoiced = True
                    grv.save(update_fields=['IsInvoiced'])
 
                else:
                    # ── DIRECT PURCHASE (original flow) ───────────────────
                    voucher, _ = process_voucher(
                        kind=VoucherKind.PURCHASE,
                        voucher_form=voucher_form,
                        items_raw_json=items_raw,
                    )
                    create_ledger_postings_for_purchase(voucher)
                    update_purchase_cleared_status(voucher.id)
 
                messages.success(
                    request,
                    f"✅ Purchase voucher {voucher.voucher_no} created successfully."
                )
                return redirect('item_master:purchase_voucher_list')
 
        except Exception as e:
            messages.error(request, f"Error creating voucher: {e}")
    else:
        messages.error(request, "⚠️ Please correct the errors below.")
 
    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form":    PurchaseVoucherItemForm(),
        "items":        Item.objects.all(),
        "item_groups":  ItemGroup.objects.all(),
        "is_edit":      False,
        "linked_grv":   None,
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE EDIT
# ─────────────────────────────────────────────────────────────────────────────
 
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def edit_purchase_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Purchase.")
 
    template_name = 'purchase_form1.html'
    voucher       = get_object_or_404(PurchaseMaster, pk=pk)
    is_grv_linked = voucher.item_grv_id is not None   # capture before any changes
 
    if request.method == "GET":
        voucher_form  = PurchaseVoucherForm(instance=voucher)
        item_formset  = PurchaseVoucherItemFormSet(instance=voucher)
 
        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form":    PurchaseVoucherItemForm(),
            "item_formset": item_formset,
            "items":        Item.objects.all(),
            "item_groups":  ItemGroup.objects.all(),
            "units":        PurchaseVoucherItemForm().fields['unit'].queryset, 
            "is_edit":      True,
            "linked_grv":   voucher.item_grv,
        })
 
    # ── POST ──────────────────────────────────────────────────────────────
    voucher_form = PurchaseVoucherForm(request.POST, instance=voucher)
    item_formset = PurchaseVoucherItemFormSet(request.POST, instance=voucher)
 
    try:
        with transaction.atomic():
            if voucher_form.is_valid() and item_formset.is_valid():
 
                voucher = voucher_form.save()
 
                if not is_grv_linked:
                    # ── DIRECT PURCHASE: reverse old stock, let formset handle
                    #    create/update/delete itself, then re-post new stock ───

                    # Snapshot BEFORE any DB writes — used only to reverse old stock.
                    old_details = list(PurchaseDetail.objects.filter(purchase=voucher))

                    for d in old_details:
                        item     = Item.objects.get(id=d.item_name_id)
                        base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)
                        upsert_stock(
                            item           = item,
                            batch_id       = d.Batch_id,
                            base_unit_id   = item.item_unit_id,
                            base_qty_delta = base_qty,
                            rate           = d.purchase_rate,
                            voucher_date   = voucher.transaction_date,
                            voucher_type   = voucher.voucherType,
                            voucher_id     = voucher.id,
                            cost_center    = voucher.cost_center,
                        )

                    # Do NOT delete old_details manually — let the formset's own
                    # save() apply inserts, updates, and DELETE-checked removals.
                    item_formset.instance = voucher
                    item_formset.save()

                    # Re-read what's actually in the DB now, and re-post stock
                    # against that (reflects adds/edits/deletes correctly).
                    new_details = list(PurchaseDetail.objects.filter(purchase=voucher))

                    for d in new_details:
                        item     = Item.objects.get(id=d.item_name_id)
                        base_qty = to_base_qty(item, d.unit_id, d.quantity)
                        upsert_stock(
                            item           = item,
                            batch_id       = d.Batch_id,
                            base_unit_id   = item.item_unit_id,
                            base_qty_delta = base_qty,
                            rate           = d.purchase_rate,
                            voucher_date   = voucher.transaction_date,
                            voucher_type   = voucher.voucherType,
                            voucher_id     = voucher.id,
                            cost_center    = voucher.cost_center,
                        )
 
                else:
                    # ── GRV-LINKED: save formset only, no stock changes ───
                    item_formset.instance = voucher
                    item_formset.save()
 
                # Ledger repost (both cases)
                create_ledger_postings_for_purchase(voucher)
                update_purchase_cleared_status(voucher.id)
 
                messages.success(
                    request,
                    f"✏️ Purchase voucher {voucher.voucher_no} updated successfully."
                )
                return redirect('item_master:purchase_voucher_list')
 
            else:
                messages.error(request, "⚠️ Please correct the errors below.")
 
    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")
 
    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form":    PurchaseVoucherItemForm(),
        "item_formset": item_formset,
        "items":        Item.objects.all(),
        "item_groups":  ItemGroup.objects.all(), 
        "units":        PurchaseVoucherItemForm().fields['unit'].queryset,
        "is_edit":      True,
        "linked_grv":   voucher.item_grv,
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE DELETE
# ─────────────────────────────────────────────────────────────────────────────
 
@require_POST
def purchase_voucher_delete(request, pk):
    if not check_privilege(request.user, 3, "can_delete"):
        return HttpResponseForbidden("🚫 You do not have permission to delete Purchase.")
 
    voucher       = get_object_or_404(PurchaseMaster, pk=pk)
    is_grv_linked = voucher.item_grv_id is not None
 
    try:
        with transaction.atomic():
            details = PurchaseDetail.objects.filter(purchase=voucher)
 
            if not is_grv_linked:
                # ── DIRECT PURCHASE: reverse stock ───────────────────────
                for d in details:
                    item     = Item.objects.get(id=d.item_name_id)
                    base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)
                    upsert_stock(
                        item           = item,
                        batch_id       = d.Batch_id,
                        base_unit_id   = item.item_unit_id,
                        base_qty_delta = base_qty,
                        rate           = d.purchase_rate,
                        voucher_date   = voucher.transaction_date,
                        voucher_type   = voucher.voucherType,
                        voucher_id     = voucher.id,
                        cost_center    = voucher.cost_center,
                    )
            else:
                # ── GRV-LINKED: re-open GRV for future invoicing ─────────
                grv = voucher.item_grv
                grv.IsInvoiced = False
                grv.save(update_fields=['IsInvoiced'])
 
            # Delete ledger postings (both cases)
            delete_ledger_postings(voucher.voucherType_id, voucher.id)
 
            details.delete()
            voucher.delete()
 
            messages.success(request, "🗑️ Purchase voucher deleted successfully.")
 
    except Exception as e:
        messages.error(request, f"❌ Error deleting voucher: {str(e)}")
 
    return redirect('item_master:purchase_voucher_list')
 

def purchase_voucher_pdf(request, pk):
    purchase = get_object_or_404(PurchaseMaster, pk=pk)
    return create_purchase_pdf(purchase)
    
# ─────────────────────────────────────────────────────────────────────────────
# PURCHASE LIST  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
 
@login_required(login_url='accounts_app:admin_login')
def purchase_voucher_list(request):
    if not check_privilege(request.user, 3, "can_read"):
        return HttpResponseForbidden("🚫 You do not have permission to view Purchase.")
 
    vouchers = PurchaseMaster.objects.all()
    return render(request, 'purchase_voucher_list.html', {'vouchers': vouchers})




# @login_required(login_url='accounts_app:admin_login')
# # ----------------- CREATE -----------------
# @require_http_methods(["GET", "POST"])
# def create_purchase_voucher(request):
#     if not check_privilege(request.user, 3, "can_add"):
#         return HttpResponseForbidden("🚫 You do not have permission to Create Purchase.")

#     template_name = 'purchase_form1.html'

#     if request.method == "GET":
#         voucher_form = PurchaseVoucherForm()
#         voucher_form.fields['transaction_date'].initial = datetime.date.today()
#         voucher_form.fields['InvoiceDate'].initial = datetime.date.today()

#         return render(request, template_name, {
#             "voucher_form": voucher_form,
#             "item_form": PurchaseVoucherItemForm(),
#             "items": Item.objects.all(),
#             "is_edit": False
#         })

#     # POST create
#     voucher_form = PurchaseVoucherForm(request.POST)
#     items_raw = request.POST.get("items_data", "[]")

#     if voucher_form.is_valid():
#         try:
#             with transaction.atomic():
#                 voucher, _ = process_voucher(
#                     kind=VoucherKind.PURCHASE,
#                     voucher_form=voucher_form,
#                     items_raw_json=items_raw,
#                 )
                
#                 create_ledger_postings_for_purchase(voucher)
#                 # 🔥 UPDATE CLEARING STATUS
#                 update_purchase_cleared_status(voucher.id)
                
#                 messages.success(request, f"✅ Purchase voucher {voucher.voucher_no} created successfully.")
#                 return redirect('item_master:purchase_voucher_list')
#         except Exception as e:
#             messages.error(request, f"Error creating voucher: {e}")
#     else:
#         # Show form validation errors
#         messages.error(request, "⚠️ Please correct the errors below.")

#     return render(request, template_name, {
#         "voucher_form": voucher_form,
#         "item_form": PurchaseVoucherItemForm(),
#         "items": Item.objects.all(),
#         "is_edit": False
#     })


# # ----------------- EDIT -----------------
# @require_http_methods(["GET", "POST"])
# def edit_purchase_voucher(request, pk):
#     if not check_privilege(request.user, 3, "can_edit"):
#         return HttpResponseForbidden("🚫 You do not have permission to Edit Purchase.")

#     template_name = 'purchase_form1.html'
#     voucher = get_object_or_404(PurchaseMaster, pk=pk)

#     if request.method == "GET":
#         voucher_form = PurchaseVoucherForm(instance=voucher)
#         item_formset = PurchaseVoucherItemFormSet(instance=voucher)

#         return render(request, template_name, {
#             "voucher_form": voucher_form,
#             "item_form": PurchaseVoucherItemForm(),
#             "item_formset": item_formset,
#             "items": Item.objects.all(),
#             "is_edit": True,
#         })

#     # POST update
#     voucher_form = PurchaseVoucherForm(request.POST, instance=voucher)
#     item_formset = PurchaseVoucherItemFormSet(request.POST, instance=voucher)

#     try:
#         with transaction.atomic():
#             if voucher_form.is_valid() and item_formset.is_valid():

#                 # Save voucher
#                 voucher = voucher_form.save()

#                 # -------------------------------
#                 # 1. REVERSE OLD STOCK
#                 # -------------------------------
#                 old_details = PurchaseDetail.objects.filter(purchase=voucher)

#                 for d in old_details:
#                     item = Item.objects.get(id=d.item_name_id)

#                     base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)

#                     upsert_stock(
#                         item=item,
#                         batch_id=d.Batch_id,
#                         base_unit_id=item.item_unit_id,
#                         base_qty_delta=base_qty,
#                         rate=d.purchase_rate,
#                         voucher_date=voucher.transaction_date,
#                         voucher_type=voucher.voucherType,
#                         voucher_id=voucher.id,
#                         cost_center=voucher.cost_center,
#                     )

#                 # -------------------------------
#                 # 2. DELETE OLD DETAILS
#                 # -------------------------------
#                 old_details.delete()

#                 # -------------------------------
#                 # 3. SAVE NEW DETAILS
#                 # -------------------------------
#                 item_formset.instance = voucher
#                 new_details = item_formset.save()

#                 # -------------------------------
#                 # 4. POST STOCK AGAIN
#                 # -------------------------------
#                 for d in new_details:
#                     item = Item.objects.get(id=d.item_name_id)

#                     base_qty = to_base_qty(item, d.unit_id, d.quantity)

#                     upsert_stock(
#                         item=item,
#                         batch_id=d.Batch_id,
#                         base_unit_id=item.item_unit_id,
#                         base_qty_delta=base_qty,
#                         rate=d.purchase_rate,
#                         voucher_date=voucher.transaction_date,
#                         voucher_type=voucher.voucherType,
#                         voucher_id=voucher.id,
#                         cost_center=voucher.cost_center,
#                     )

#                 # Ledger repost
#                 create_ledger_postings_for_purchase(voucher)
#                 # 🔥 UPDATE CLEARING STATUS AFTER EDIT
#                 update_purchase_cleared_status(voucher.id)

#                 messages.success(request, f"✏️ Purchase voucher {voucher.voucher_no} updated successfully.")
#                 return redirect('item_master:purchase_voucher_list')

#             else:
#                 messages.error(request, "⚠️ Please correct the errors below.")

#     except Exception as e:
#         messages.error(request, f"❌ Error updating voucher: {str(e)}")

#     return render(request, template_name, {
#         "voucher_form": voucher_form,
#         "item_form": PurchaseVoucherItemForm(),
#         "item_formset": item_formset,
#         "items": Item.objects.all(),
#         "is_edit": True,
#     })

# @require_POST
# def purchase_voucher_delete(request, pk):
#     if not check_privilege(request.user, 3, "can_delete"):
#         return HttpResponseForbidden("🚫 You do not have permission to delete Purchase.")

#     voucher = get_object_or_404(PurchaseMaster, pk=pk)

#     try:
#         with transaction.atomic():

#             # ---------------------------------
#             # 1. REVERSE STOCK
#             # ---------------------------------
#             details = PurchaseDetail.objects.filter(purchase=voucher)

#             for d in details:
#                 item = Item.objects.get(id=d.item_name_id)

#                 # Purchase = IN → reverse = OUT
#                 base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)

#                 upsert_stock(
#                     item=item,
#                     batch_id=d.Batch_id,
#                     base_unit_id=item.item_unit_id,
#                     base_qty_delta=base_qty,
#                     rate=d.purchase_rate,
#                     voucher_date=voucher.transaction_date,
#                     voucher_type=voucher.voucherType,
#                     voucher_id=voucher.id,
#                     cost_center=voucher.cost_center,
#                 )

#             # ---------------------------------
#             # 2. DELETE LEDGER
#             # ---------------------------------
#             delete_ledger_postings(voucher.voucherType_id, voucher.id)

#             # ---------------------------------
#             # 3. DELETE DETAILS
#             # ---------------------------------
#             details.delete()

#             # ---------------------------------
#             # 4. DELETE VOUCHER
#             # ---------------------------------
#             voucher.delete()

#             messages.success(request, "🗑️ Purchase voucher deleted successfully.")

#     except Exception as e:
#         messages.error(request, f"❌ Error deleting voucher: {str(e)}")

#     return redirect('item_master:purchase_voucher_list')

# @login_required(login_url='accounts_app:admin_login')
# def purchase_voucher_list(request):
#     # Check privilege for purchase listing
#     if not check_privilege(request.user, 3, "can_read"):   # 3 is the ID of the "Purchase" menu

#         return HttpResponseForbidden("🚫 You do not have permission to view Purchase.")
#     # Query all PurchaseVoucher objects from the database
#     vouchers = PurchaseMaster.objects.all()

#     # Pass the vouchers to the template context
#     return render(request, 'purchase_voucher_list.html', {'vouchers': vouchers})



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
def purchase_voucher_detail(request, voucher_id):
    # Retrieve the PurchaseVoucher object and related PurchaseVoucherItem objects
    voucher = get_object_or_404(PurchaseMaster, id=voucher_id)
    items = PurchaseDetail.objects.filter(purchase__id=voucher.id)
    # Pass the voucher and its items to the template context
    return render(request, 'purchase_voucher_detail.html', {
        'voucher': voucher,
        'items': items
    })    
    
    

# ----------------- CREATE -----------------
@require_http_methods(["GET", "POST"])
def create_salesreturn_voucher(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Sales Return.")

    template_name = 'salesReturn_voucher_create.html'

    if request.method == "GET":
        voucher_form = SalesReturnVoucherForm()
        voucher_form.fields['transaction_date']
        voucher_form.fields['InvoiceDate']

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": SalesReturnVoucherItemForm(),
            "items": Item.objects.all(),
            "is_edit": False
        })

    # POST create
    voucher_form = SalesReturnVoucherForm(request.POST)
    items_raw = request.POST.get("items_data", "[]")

    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.SALES_RETURN,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )
                
                create_ledger_postings_for_salesreturn(voucher)
                
                messages.success(request, f"✅ Sales Return voucher {voucher.voucher_no} created successfully.")
                return redirect('item_master:salesreturn_voucher_list')
        except Exception as e:
            messages.error(request, f"Error creating voucher: {e}")
    else:
        # Show form validation errors
        messages.error(request, "⚠️ Please correct the errors below.")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": SalesReturnVoucherItemForm(),
        "items": Item.objects.all(),
        "is_edit": False
    })


# ----------------- EDIT -----------------
@require_http_methods(["GET", "POST"])
def edit_salesreturn_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Sales Return.")

    template_name = 'salesReturn_voucher_create.html'
    voucher = get_object_or_404(SalesReturnMaster, pk=pk)

    if request.method == "GET":
        voucher_form = SalesReturnVoucherForm(instance=voucher)
        item_formset = SalesReturnVoucherItemFormSet(instance=voucher)

        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form": SalesReturnVoucherItemForm(),
            "item_formset": item_formset,
            "items": Item.objects.all(),
            "is_edit": True,
        })

    # POST update
    voucher_form = SalesReturnVoucherForm(request.POST, instance=voucher)
    item_formset = SalesReturnVoucherItemFormSet(request.POST, instance=voucher)

    try:
        with transaction.atomic():
            if voucher_form.is_valid() and item_formset.is_valid():

                # Save voucher
                voucher = voucher_form.save()

                # -------------------------------
                # 1. REVERSE OLD STOCK
                # -------------------------------
                old_details = SalesReturnDetail.objects.filter(salesreturn=voucher)

                for d in old_details:
                    item = Item.objects.get(id=d.item_name_id)

                    base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)

                    upsert_stock(
                        item=item,
                        batch_id=d.Batch_id,
                        base_unit_id=item.item_unit_id,
                        base_qty_delta=base_qty,
                        rate=d.purchase_rate,
                        voucher_date=voucher.transaction_date,
                        voucher_type=voucher.voucherType,
                        voucher_id=voucher.id,
                        cost_center=voucher.cost_center,
                    )

                # -------------------------------
                # 2. DELETE OLD DETAILS
                # -------------------------------
                old_details.delete()

                # -------------------------------
                # 3. SAVE NEW DETAILS
                # -------------------------------
                item_formset.instance = voucher
                new_details = item_formset.save()

                # -------------------------------
                # 4. POST STOCK AGAIN
                # -------------------------------
                for d in new_details:
                    item = Item.objects.get(id=d.item_name_id)

                    base_qty = to_base_qty(item, d.unit_id, d.quantity)

                    upsert_stock(
                        item=item,
                        batch_id=d.Batch_id,
                        base_unit_id=item.item_unit_id,
                        base_qty_delta=base_qty,
                        rate=d.purchase_rate,
                        voucher_date=voucher.transaction_date,
                        voucher_type=voucher.voucherType,
                        voucher_id=voucher.id,
                        cost_center=voucher.cost_center,
                    )

                # Ledger repost
                create_ledger_postings_for_salesreturn(voucher)

                messages.success(request, f"✏️ Sales Return voucher {voucher.voucher_no} updated successfully.")
                return redirect('item_master:salesreturn_voucher_list')

            else:
                messages.error(request, "⚠️ Please correct the errors below.")

    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")

    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form": SalesReturnVoucherItemForm(),
        "item_formset": item_formset,
        "items": Item.objects.all(),
        "is_edit": True,
    })


@login_required(login_url='accounts_app:admin_login')
def salesreturn_voucher_list(request):
    # Check privilege for purchase listing
    if not check_privilege(request.user, 3, "can_read"):   # 3 is the ID of the "Purchase" menu

        return HttpResponseForbidden("🚫 You do not have permission to view Sales Return.")
    # Query all PurchaseVoucher objects from the database
    vouchers = SalesReturnMaster.objects.all()

    # Pass the vouchers to the template context
    return render(request, 'sales_return_list.html', {'vouchers': vouchers})
    
    
@require_POST
def salesreturn_voucher_delete(request, pk):
    if not check_privilege(request.user, 3, "can_delete"):
        return HttpResponseForbidden("🚫 You do not have permission to delete Sales Return.")

    voucher = get_object_or_404(SalesReturnMaster, pk=pk)

    try:
        with transaction.atomic():

            # ---------------------------------
            # 1. REVERSE STOCK
            # ---------------------------------
            details = SalesReturnDetail.objects.filter(salesreturn=voucher)

            for d in details:
                item = Item.objects.get(id=d.item_name_id)

                # Purchase = IN → reverse = OUT
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)

                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.purchase_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )

            # ---------------------------------
            # 2. DELETE LEDGER
            # ---------------------------------
            delete_ledger_postings(voucher.voucherType_id, voucher.id)

            # ---------------------------------
            # 3. DELETE DETAILS
            # ---------------------------------
            details.delete()

            # ---------------------------------
            # 4. DELETE VOUCHER
            # ---------------------------------
            voucher.delete()

            messages.success(request, "🗑️ Sales Return voucher deleted successfully.")

    except Exception as e:
        messages.error(request, f"❌ Error deleting voucher: {str(e)}")

    return redirect('item_master:sales_return_list')

    


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



# ─────────────────────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def sales_voucher_create(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Sales.")
 
    template_name = 'sales_voucher_create.html'
 
    # ── AJAX row-validation (Add Item button hits this) ──────────────────────
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = SalesVoucherItemForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            item_data = {
                'item_name':       cd['item_name'].id,
                'item_name_text':  str(cd['item_name']),
                'item_code':       cd.get('item_code', ''),
                'barcode_code':    cd.get('barcode_code', ''),
                'quantity':        float(cd['quantity']),
                'sales_rate':      float(cd['sales_rate']),
                'item_net_amount': float(cd['item_net_amount']),
                'tax':             float(cd['tax']),
                'item_tax_amount': float(cd['item_tax_amount']),
                'unit':       cd['unit'].id    if cd.get('unit')  else None,
                'unit_text':  str(cd['unit'])  if cd.get('unit')  else '',
                'item_total_amount': float(cd['item_total_amount']),
                'batch':      cd['Batch'].id   if cd.get('Batch') else None,
                'batch_text': str(cd['Batch']) if cd.get('Batch') else '',
                'mfd': cd['MFD'].isoformat()   if cd.get('MFD')   else '',
                'exp': cd['EXP'].isoformat()   if cd.get('EXP')   else '',
            }
            return JsonResponse({'status': 'success', 'item': item_data})
        return JsonResponse({'status': 'error', 'errors': form.errors})
 
    # ── GET ──────────────────────────────────────────────────────────────────
    if request.method == 'GET':
        voucher_form = SalesVoucherForm()
        voucher_form.fields['transaction_date']
        voucher_form.fields['InvoiceDate']
        return render(request, template_name, {
            'voucher_form': voucher_form,
            'item_form':    SalesVoucherItemForm(),
            'is_edit':      False,
        })
 
    # ── POST create ──────────────────────────────────────────────────────────
    voucher_form = SalesVoucherForm(request.POST)
    items_raw    = request.POST.get('items_data', '[]')
 
    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.SALES,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )

                create_ledger_postings_for_sale(voucher)


                messages.success(request, f"✅ Sales voucher {voucher.voucher_no} created successfully.")
                return redirect('item_master:sales_voucher_list')
        except Exception as e:
            messages.error(request, f"❌ Error creating voucher: {e}")
    else:
        messages.error(request, "⚠️ Please correct the errors below.")
 
    return render(request, template_name, {
        'voucher_form': voucher_form,
        'item_form':    SalesVoucherItemForm(),
        'is_edit':      False,
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def edit_sales_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Sales.")
 
    template_name = 'sales_voucher_create.html'
    voucher = get_object_or_404(SalesMaster, pk=pk)
 
    # ── GET ──────────────────────────────────────────────────────────────────
    if request.method == 'GET':
        voucher_form = SalesVoucherForm(instance=voucher)
 
        # Serialize existing line items → JS will pre-populate the items array
        existing_items = []
        for d in SalesDetail.objects.filter(sales_voucher=voucher):
            existing_items.append({
                'item_name':       d.item_name_id,
                'item_name_text':  str(d.item_name),
                'item_code':       d.item_code       or '',
                'barcode_code':    d.barcode_code     or '',
                'quantity':        float(d.quantity),
                'sales_rate':      float(d.sales_rate),
                'item_net_amount': float(d.item_net_amount),
                'tax':             float(d.tax),
                'item_tax_amount': float(d.item_tax_amount),
                'unit':       d.unit_id,
                'unit_text':  str(d.unit)  if d.unit  else '',
                'item_total_amount': float(d.item_total_amount),
                'batch':      d.Batch_id,
                'batch_text': str(d.Batch) if d.Batch else '',
                'mfd': d.MFD.isoformat()   if d.MFD   else '',
                'exp': d.EXP.isoformat()   if d.EXP   else '',
            })
 
        return render(request, template_name, {
            'voucher_form':        voucher_form,
            'item_form':           SalesVoucherItemForm(),
            'is_edit':             True,
            'existing_items_json': json.dumps(existing_items),
        })
 
    # ── POST update ──────────────────────────────────────────────────────────
    voucher_form = SalesVoucherForm(request.POST, instance=voucher)
    items_raw    = request.POST.get('items_data', '[]')
 
    try:
        with transaction.atomic():
            if not voucher_form.is_valid():
                messages.error(request, "⚠️ Please correct the errors below.")
                raise ValueError("Form invalid")
 
            # ── 1. Save voucher header (preserve voucher_no) ─────────────────
            old_voucher_no = voucher.voucher_no
            voucher = voucher_form.save(commit=False)
            voucher.voucher_no = old_voucher_no
            voucher.save()
 
            # ── 2. Reverse old stock ─────────────────────────────────────────
            old_details = SalesDetail.objects.filter(sales_voucher=voucher)
            for d in old_details:
                item = Item.objects.get(id=d.item_name_id)
                # Sales reduces stock, so reversing a sale adds stock back (+1)
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(1)
                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.sales_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )
 
            # ── 3. Delete old detail rows ────────────────────────────────────
            old_details.delete()
 
            # ── 4. Create new detail rows from JSON ──────────────────────────
            items_list  = json.loads(items_raw)
            new_details = []
            for item_data in items_list:
                detail = SalesDetail(
                    sales_voucher    = voucher,
                    item_name_id     = item_data['item_name'],
                    item_code        = item_data.get('item_code',    ''),
                    barcode_code     = item_data.get('barcode_code', ''),
                    quantity         = Decimal(str(item_data['quantity'])),
                    sales_rate       = Decimal(str(item_data['sales_rate'])),
                    item_net_amount  = Decimal(str(item_data['item_net_amount'])),
                    tax              = Decimal(str(item_data['tax'])),
                    item_tax_amount  = Decimal(str(item_data['item_tax_amount'])),
                    unit_id          = item_data.get('unit')  or None,
                    item_total_amount= Decimal(str(item_data['item_total_amount'])),
                    Batch_id         = item_data.get('batch') or None,
                    MFD              = item_data.get('mfd')   or None,
                    EXP              = item_data.get('exp')   or None,
                )
                detail.save()
                new_details.append(detail)
 
            # ── 5. Post new stock ────────────────────────────────────────────
            for d in new_details:
                item = Item.objects.get(id=d.item_name_id)
                # Sales reduces stock (-1)
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)
                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.sales_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )
 
            # ── 6. Delete old ledger + Repost ────────────────────────────────
            delete_ledger_postings(voucher.voucherType_id, voucher.id)
            create_ledger_postings_for_sale(voucher)
 
            messages.success(request, f"✏️ Sales voucher {voucher.voucher_no} updated successfully.")
            return redirect('item_master:sales_voucher_list')
 
    except ValueError:
        pass  # form-invalid path; error message already set above
    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")
 
    return render(request, template_name, {
        'voucher_form':        voucher_form,
        'item_form':           SalesVoucherItemForm(),
        'is_edit':             True,
        'existing_items_json': '[]',
    })


@require_POST
def sales_voucher_delete(request, pk):

    # Permission check
    if not check_privilege(request.user, 3, "can_delete"):
        return HttpResponseForbidden("🚫 You do not have permission to delete Sales.")

    voucher = get_object_or_404(SalesMaster, pk=pk)

    try:
        with transaction.atomic():

            # ---------------------------------
            # 1. REVERSE STOCK
            # ---------------------------------
            details = SalesDetail.objects.filter(sales_voucher=voucher)

            for d in details:
                item = Item.objects.get(id=d.item_name_id)

                # Sales = OUT → reverse = IN
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(1)

                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.sales_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )

            # ---------------------------------
            # 2. DELETE LEDGER
            # ---------------------------------
            delete_ledger_postings(voucher.voucherType_id, voucher.id)

            # ---------------------------------
            # 3. DELETE DETAILS
            # ---------------------------------
            details.delete()

            # ---------------------------------
            # 4. DELETE VOUCHER
            # ---------------------------------
            voucher.delete()

            messages.success(request, "🗑️ Sales voucher deleted successfully.")

    except Exception as e:
        messages.error(request, f"❌ Error deleting voucher: {str(e)}")

    return redirect('item_master:sales_voucher_list')   

    
@login_required(login_url='accounts_app:admin_login')
def sales_voucher_list(request):
    # Check privilege for Sales listing
    if not check_privilege(request.user, 1, "can_read"):   # 1 is the ID of the "Sales" menu

        return HttpResponseForbidden("🚫 You do not have permission to view Sales.")

    vouchers = SalesMaster.objects.all()
    return render(request, 'sales_voucher_list.html', {'vouchers': vouchers})



# ─────────────────────────────────────────────────────────────────────────────
# CREATE Purchase Return
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def purchase_return_create(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Purchase Return.")
 
    template_name = 'purchaseReturn_form.html'
 
    # ── AJAX row-validation (Add Item button hits this) ──────────────────────
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = PurchaseReturnVoucherItemForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            item_data = {
                'item_name':       cd['item_name'].id,
                'item_name_text':  str(cd['item_name']),
                'item_code':       cd.get('item_code', ''),
                'barcode_code':    cd.get('barcode_code', ''),
                'quantity':        float(cd['quantity']),
                'sales_rate':      float(cd['sales_rate']),
                'item_net_amount': float(cd['item_net_amount']),
                'tax':             float(cd['tax']),
                'item_tax_amount': float(cd['item_tax_amount']),
                'unit':       cd['unit'].id    if cd.get('unit')  else None,
                'unit_text':  str(cd['unit'])  if cd.get('unit')  else '',
                'item_total_amount': float(cd['item_total_amount']),
                'batch':      cd['Batch'].id   if cd.get('Batch') else None,
                'batch_text': str(cd['Batch']) if cd.get('Batch') else '',
                'mfd': cd['MFD'].isoformat()   if cd.get('MFD')   else '',
                'exp': cd['EXP'].isoformat()   if cd.get('EXP')   else '',
            }
            return JsonResponse({'status': 'success', 'item': item_data})
        return JsonResponse({'status': 'error', 'errors': form.errors})
 
    # ── GET ──────────────────────────────────────────────────────────────────
    if request.method == 'GET':
        voucher_form = PurchaseReturnVoucherForm()
        voucher_form.fields['transaction_date']
        voucher_form.fields['InvoiceDate']
        return render(request, template_name, {
            'voucher_form': voucher_form,
            'item_form':    PurchaseReturnVoucherItemForm(),
            'is_edit':      False,
        })
 
    # ── POST create ──────────────────────────────────────────────────────────
    voucher_form = PurchaseReturnVoucherForm(request.POST)
    items_raw    = request.POST.get('items_data', '[]')
 
    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.PURCHASE_RETURN,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )

                create_ledger_postings_for_purchasereturn(voucher)

                messages.success(request, f"✅ Purchase Return {voucher.voucher_no} created successfully.")
                return redirect('item_master:purchase_return_voucher_list')
        except Exception as e:
            messages.error(request, f"❌ Error creating voucher: {e}")
    else:
        messages.error(request, "⚠️ Please correct the errors below.")
 
    return render(request, template_name, {
        'voucher_form': voucher_form,
        'item_form':    PurchaseReturnVoucherItemForm(),
        'is_edit':      False,
    })
 
 
# ─────────────────────────────────────────────────────────────────────────────
# EDIT
# ─────────────────────────────────────────────────────────────────────────────
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def edit_purchase_return_voucher(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Purchase Return.")
 
    template_name = 'purchaseReturn_form.html'
    voucher = get_object_or_404(PurchaseReturnMaster, pk=pk)
 
    # ── GET ──────────────────────────────────────────────────────────────────
    if request.method == 'GET':
        voucher_form = PurchaseReturnVoucherForm(instance=voucher)
 
        # Serialize existing line items → JS will pre-populate the items array
        existing_items = []
        for d in PurchaseReturnDetail.objects.filter(purchase_return=voucher):
            existing_items.append({
                'item_name':       d.item_name_id,
                'item_name_text':  str(d.item_name),
                'item_code':       d.item_code       or '',
                'barcode_code':    d.barcode_code     or '',
                'quantity':        float(d.quantity),
                'sales_rate':      float(d.sales_rate),
                'item_net_amount': float(d.item_net_amount),
                'tax':             float(d.tax),
                'item_tax_amount': float(d.item_tax_amount),
                'unit':       d.unit_id,
                'unit_text':  str(d.unit)  if d.unit  else '',
                'item_total_amount': float(d.item_total_amount),
                'batch':      d.Batch_id,
                'batch_text': str(d.Batch) if d.Batch else '',
                'mfd': d.MFD.isoformat()   if d.MFD   else '',
                'exp': d.EXP.isoformat()   if d.EXP   else '',
            })
 
        return render(request, template_name, {
            'voucher_form':        voucher_form,
            'item_form':           PurchaseReturnVoucherItemForm(),
            "item_groups":   ItemGroup.objects.all(),
            'is_edit':             True,
            'existing_items_json': json.dumps(existing_items),
        })
 
    # ── POST update ──────────────────────────────────────────────────────────
    voucher_form = PurchaseReturnVoucherForm(request.POST, instance=voucher)
    items_raw    = request.POST.get('items_data', '[]')
 
    try:
        with transaction.atomic():
            if not voucher_form.is_valid():
                messages.error(request, "⚠️ Please correct the errors below.")
                raise ValueError("Form invalid")
 
            # ── 1. Save voucher header (preserve voucher_no) ─────────────────
            old_voucher_no = voucher.voucher_no
            voucher = voucher_form.save(commit=False)
            voucher.voucher_no = old_voucher_no
            voucher.save()
 
            # ── 2. Reverse old stock ─────────────────────────────────────────
            old_details = PurchaseReturnDetail.objects.filter(purchase_return_voucher=voucher)
            for d in old_details:
                item = Item.objects.get(id=d.item_name_id)
                # Purchase Return reduces stock, so reversing a purchase return adds stock back (+1)
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(1)
                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.sales_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )
 
            # ── 3. Delete old detail rows ────────────────────────────────────
            old_details.delete()
 
            # ── 4. Create new detail rows from JSON ──────────────────────────
            items_list  = json.loads(items_raw)
            new_details = []
            for item_data in items_list:
                detail = PurchaseReturnDetail(
                    purchase_return_voucher    = voucher,
                    item_name_id     = item_data['item_name'],
                    item_code        = item_data.get('item_code',    ''),
                    barcode_code     = item_data.get('barcode_code', ''),
                    quantity         = Decimal(str(item_data['quantity'])),
                    sales_rate       = Decimal(str(item_data['sales_rate'])),
                    item_net_amount  = Decimal(str(item_data['item_net_amount'])),
                    tax              = Decimal(str(item_data['tax'])),
                    item_tax_amount  = Decimal(str(item_data['item_tax_amount'])),
                    unit_id          = item_data.get('unit')  or None,
                    item_total_amount= Decimal(str(item_data['item_total_amount'])),
                    Batch_id         = item_data.get('batch') or None,
                    MFD              = item_data.get('mfd')   or None,
                    EXP              = item_data.get('exp')   or None,
                )
                detail.save()
                new_details.append(detail)
 
            # ── 5. Post new stock ────────────────────────────────────────────
            for d in new_details:
                item = Item.objects.get(id=d.item_name_id)
                # Sales reduces stock (-1)
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)
                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.sales_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )
 
            # ── 6. Delete old ledger + Repost ────────────────────────────────
            delete_ledger_postings(voucher.voucherType_id, voucher.id)
            create_ledger_postings_for_purchasereturn(voucher)
 
            messages.success(request, f"✏️ Purchase Return {voucher.voucher_no} updated successfully.")
            return redirect('item_master:purchase_return_list')
 
    except ValueError:
        pass  # form-invalid path; error message already set above
    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")
 
    return render(request, template_name, {
        'voucher_form':        voucher_form,
        'item_form':           PurchaseReturnVoucherItemForm(),
        "item_groups":   ItemGroup.objects.all(),
        'is_edit':             True,
        'existing_items_json': '[]',
    })


@require_POST
def purchase_return_voucher_delete(request, pk):

    # Permission check
    if not check_privilege(request.user, 3, "can_delete"):
        return HttpResponseForbidden("🚫 You do not have permission to delete Purchase Return.")

    voucher = get_object_or_404(PurchaseReturnMaster, pk=pk)

    try:
        with transaction.atomic():

            # ---------------------------------
            # 1. REVERSE STOCK
            # ---------------------------------
            details = PurchaseReturnDetail.objects.filter(purchase_return_voucher=voucher)

            for d in details:
                item = Item.objects.get(id=d.item_name_id)

                # Purchase Return = OUT → reverse = IN
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(1)

                upsert_stock(
                    item=item,
                    batch_id=d.Batch_id,
                    base_unit_id=item.item_unit_id,
                    base_qty_delta=base_qty,
                    rate=d.sales_rate,
                    voucher_date=voucher.transaction_date,
                    voucher_type=voucher.voucherType,
                    voucher_id=voucher.id,
                    cost_center=voucher.cost_center,
                )

            # ---------------------------------
            # 2. DELETE LEDGER
            # ---------------------------------
            delete_ledger_postings(voucher.voucherType_id, voucher.id)

            # ---------------------------------
            # 3. DELETE DETAILS
            # ---------------------------------
            details.delete()

            # ---------------------------------
            # 4. DELETE VOUCHER
            # ---------------------------------
            voucher.delete()

            messages.success(request, "🗑️ Purchase Return voucher deleted successfully.")

    except Exception as e:
        messages.error(request, f"❌ Error deleting voucher: {str(e)}")

    return redirect('item_master:purchase_return_list')   

    
@login_required(login_url='accounts_app:admin_login')
def purchase_return_voucher_list(request):
    # Check privilege for Sales listing
    if not check_privilege(request.user, 1, "can_read"):   # 1 is the ID of the "Sales" menu

        return HttpResponseForbidden("🚫 You do not have permission to view Sales.")

    vouchers = PurchaseReturnMaster.objects.all()
    return render(request, 'purchase_return_list.html', {'vouchers': vouchers})


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
    
    
    


# def stock_list(request):
#     base_unit_stocks = []

#     # Get query parameters
#     item_name = request.GET.get('item_name')
#     item_code = request.GET.get('item_code')
#     cost_center = request.GET.get('cost_center')
#     batch = request.GET.get('batch')

#     # Initial queryset
#     all_stocks = Stock.objects.select_related('item', 'unit', 'costCenter', 'batch').all()

#     # Apply filters
#     if item_name:
#         all_stocks = all_stocks.filter(item__item_name__icontains=item_name)

#     if item_code:
#         all_stocks = all_stocks.filter(item__item_code__icontains=item_code)

#     if cost_center:
#         all_stocks = all_stocks.filter(costCenter__name__icontains=cost_center)

#     if batch:
#         all_stocks = all_stocks.filter(batch__BatchNo__icontains=batch)

#     # Filter for base unit and calculate stock value
#     for stock in all_stocks:
#         stock.stock_value = stock.in_quantity * stock.rate
        
        
#         # Skip if both in and out quantities are 0
#         if stock.in_quantity == 0 and stock.out_quantity == 0:
#             continue    

#         is_base = (
#             ItemAlterUnit.objects.filter(item=stock.item, unit=stock.unit, is_base_unit=True).exists()
#             or stock.unit == stock.item.item_unit
#         )

#         if is_base:
#             has_alter_units = ItemAlterUnit.objects.filter(item=stock.item, is_base_unit=False).exists()
#             stock.has_alter_units = has_alter_units
#             base_unit_stocks.append(stock)

#     context = {
#         'stock_entries': base_unit_stocks,
#     }

#     return render(request, 'stock_list.html', context)



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

    for stock in all_stocks:

        # Skip empty rows
        if stock.in_quantity == 0 and stock.out_quantity == 0:
            continue

        # ✅ Only calculate net qty for display
        stock.net_qty = stock.in_quantity - stock.out_quantity

        # -------------------------------
        # Base unit filter
        # -------------------------------
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
        
#cost center create, edit and list
def cost_center_create_update_list(request, pk=None):
    if pk:
        cost_center = get_object_or_404(CostCenter, pk=pk)
        form = CostCenterForm(request.POST or None, instance=cost_center)
    else:
        form = CostCenterForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect('item_master:cost_center_create')

    cost_centers = CostCenter.objects.all().order_by('name')
    return render(request, 'cost_center_form.html', {'form': form, 'cost_centers': cost_centers, 'pk': pk})

def cost_center_delete(request, pk):
    cost_center = get_object_or_404(CostCenter, pk=pk)
    cost_center.delete()
    return redirect('item_master:cost_center_create')    

      
    

    
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


def get_items_by_group(request):
    group_id = request.GET.get("group_id")

    items = Item.objects.filter(
        item_group_id=group_id
    ).values("id", "item_name")

    return JsonResponse({
        "items": list(items)
    })

# ─────────────────────────────────────────────────────────────────────────────
# OPENING STOCK  CREATE
# ─────────────────────────────────────────────────────────────────────────────
 
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def create_opening_stock(request):
    if not check_privilege(request.user, 3, "can_add"):
        return HttpResponseForbidden("🚫 You do not have permission to Create Opening Stock.")
 
    template_name = 'opening_stock_form.html'
 
    if request.method == "GET":
        voucher_form = OpeningStockForm()
        voucher_form.fields['transaction_date']
 
        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form":    OpeningStockItemForm(),
            "items":        Item.objects.all(),
            "is_edit":      False,
        })
 
    # POST
    voucher_form = OpeningStockForm(request.POST)
    items_raw    = request.POST.get("items_data", "[]")
 
    if voucher_form.is_valid():
        try:
            with transaction.atomic():
                voucher, _ = process_voucher(
                    kind=VoucherKind.OPENING_STOCK,
                    voucher_form=voucher_form,
                    items_raw_json=items_raw,
                )
                    
                create_ledger_postings_for_opening_stock(voucher)
                
 
                messages.success(
                    request,
                    f"✅ Opening Stock voucher {voucher.voucher_no} created successfully."
                )
                return redirect('item_master:opening_stock_list')
 
        except Exception as e:
            messages.error(request, f"Error creating voucher: {e}")
    else:
        messages.error(request, "⚠️ Please correct the errors below.")
 
    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form":    OpeningStockItemForm(),
        "items":        Item.objects.all(),
        "is_edit":      False,
    })
 
 
@login_required(login_url='accounts_app:admin_login')
@require_http_methods(["GET", "POST"])
def edit_opening_stock(request, pk):
    if not check_privilege(request.user, 3, "can_edit"):
        return HttpResponseForbidden("🚫 You do not have permission to Edit Opening Stock.")
 
    template_name = 'opening_stock_form.html'
    voucher       = get_object_or_404(OpeningStockMaster, pk=pk)
 
    if request.method == "GET":
        voucher_form  = OpeningStockForm(instance=voucher)
        item_formset  = OpeningStockItemFormSet(instance=voucher)
 
        return render(request, template_name, {
            "voucher_form": voucher_form,
            "item_form":    OpeningStockItemForm(),
            "item_formset": item_formset,
            "items":        Item.objects.all(),
            "is_edit":      True,
        })
 
    # POST
    voucher_form = OpeningStockForm(request.POST, instance=voucher)
    item_formset = OpeningStockItemFormSet(request.POST, instance=voucher)
 
    try:
        with transaction.atomic():
            if voucher_form.is_valid() and item_formset.is_valid():
                voucher = voucher_form.save()
                item_formset.instance = voucher
                item_formset.save()
 
                delete_ledger_postings_for_opening_stock(voucher)
                create_ledger_postings_for_opening_stock(voucher)
 
                messages.success(
                    request,
                    f"✏️ Opening Stock voucher {voucher.voucher_no} updated successfully."
                )
                return redirect('item_master:opening_stock_list')
            else:
                messages.error(request, "⚠️ Please correct the errors below.")
    except Exception as e:
        messages.error(request, f"❌ Error updating voucher: {str(e)}")
 
    return render(request, template_name, {
        "voucher_form": voucher_form,
        "item_form":    OpeningStockItemForm(),
        "item_groups":   ItemGroup.objects.all(),
        "item_formset": item_formset,
        "items":        Item.objects.all(),
        "is_edit":      True,
    })
 
 
@require_POST
def opening_stock_delete(request, pk):
    if not check_privilege(request.user, 3, "can_delete"):
        return HttpResponseForbidden("🚫 You do not have permission to delete Opening Stock.")
 
    voucher = get_object_or_404(OpeningStockMaster, pk=pk)
 
    try:
        with transaction.atomic():
            details = OpeningStockDetail.objects.filter(opening_stock=voucher)
 
            for d in details:
                # 1. Skip if the foreign key ID itself is blank/null
                if not d.item_name_id:
                    continue
                
                # 2. Try fetching the item safely; skip if it doesn't exist in the database
                try:
                    item = d.item_name
                except Item.DoesNotExist:
                    continue
                
                # 3. Calculate and reverse stock quantities
                base_qty = to_base_qty(item, d.unit_id, d.quantity) * Decimal(-1)
                upsert_stock(
                    item           = item,
                    batch_id       = None,  
                    base_unit_id   = item.item_unit_id,
                    base_qty_delta = base_qty,
                    rate           = d.purchase_rate,
                    voucher_date   = voucher.transaction_date,
                    voucher_type   = voucher.voucherType,
                    voucher_id     = voucher.id,
                    cost_center    = voucher.cost_center,
                )
 
            # Revert accounting postings and delete records
            delete_ledger_postings_for_opening_stock(voucher)
            details.delete()
            voucher.delete()
 
            messages.success(request, "🗑️ Opening stock voucher deleted successfully.")
    except Exception as e:
        messages.error(request, f"❌ Error deleting voucher: {str(e)}")
 
    return redirect('item_master:opening_stock_list')
 
 
@login_required(login_url='accounts_app:admin_login')
def opening_stock_list(request):
    if not check_privilege(request.user, 3, "can_read"):
        return HttpResponseForbidden("🚫 You do not have permission to view Opening Stock.")
 
    vouchers = OpeningStockMaster.objects.all()
    return render(request, 'opening_stock_list.html', {'vouchers': vouchers})


def stock_report(request):
    items = Item.objects.all().order_by('item_name')
    voucher_types = Vouchers.objects.all().order_by('VoucherName')

    item_id = request.GET.get('item')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    voucher_type_id = request.GET.get('voucher_type')

    report_rows = []

    if item_id:
        # ---- Opening Stock -> Stock In ----
        os_qs = OpeningStockDetail.objects.filter(
            item_name_id=item_id, opening_stock__IsCleared=False
        ).select_related('opening_stock', 'opening_stock__voucherType')

        if from_date:
            os_qs = os_qs.filter(opening_stock__transaction_date__gte=from_date)
        if to_date:
            os_qs = os_qs.filter(opening_stock__transaction_date__lte=to_date)
        if voucher_type_id:
            os_qs = os_qs.filter(opening_stock__voucherType_id=voucher_type_id)

        for d in os_qs:
            report_rows.append({
                'date': d.opening_stock.transaction_date,
                'voucher_no': d.opening_stock.voucher_no,
                'voucher_type': d.opening_stock.voucherType.VoucherName,
                'ledger': '-',
                'stock_in': d.quantity or 0,
                'stock_out': 0,
            })

        # ---- Purchase -> Stock In ----
        pu_qs = PurchaseDetail.objects.filter(
            item_name_id=item_id, purchase__isDeleted=False
        ).exclude(
            item_name__item_class='Service Item'
        ).select_related('purchase', 'purchase__voucherType', 'purchase__ledger')

        if from_date:
            pu_qs = pu_qs.filter(purchase__transaction_date__gte=from_date)
        if to_date:
            pu_qs = pu_qs.filter(purchase__transaction_date__lte=to_date)
        if voucher_type_id:
            pu_qs = pu_qs.filter(purchase__voucherType_id=voucher_type_id)

        for d in pu_qs:
            report_rows.append({
                'date': d.purchase.transaction_date,
                'voucher_no': d.purchase.voucher_no,
                'voucher_type': d.purchase.voucherType.VoucherName,
                'ledger': d.purchase.ledger.ledger_name if d.purchase.ledger else '-',
                'stock_in': d.quantity or 0,
                'stock_out': 0,
            })

        # ---- Return Spare Parts -> Stock In ----
        rsp_qs = ReturnSparePartsDetails.objects.filter(
            sparepart_id=item_id,
        ).exclude(
            condition='Missing'
        ).select_related('return_spareparts', 'return_spareparts__voucherType', 'return_spareparts__ledger')

        if from_date:
            rsp_qs = rsp_qs.filter(return_spareparts__date__gte=from_date)
        if to_date:
            rsp_qs = rsp_qs.filter(return_spareparts__date__lte=to_date)
        if voucher_type_id:
            rsp_qs = rsp_qs.filter(return_spareparts__voucherType_id=voucher_type_id)

        for d in rsp_qs:
            report_rows.append({
                'date': d.return_spareparts.date,
                'voucher_no': d.return_spareparts.voucher_no,
                'voucher_type': d.return_spareparts.voucherType.VoucherName,
                'ledger': d.return_spareparts.ledger.ledger_name if d.return_spareparts.ledger else '-',
                'stock_in': d.quantity or 0,
                'stock_out': 0,
            })    

        # ---- Repair (SpareParts) -> Stock Out ----
        sp_qs = SpareParts.objects.filter(
            sparepart_id=item_id
        ).select_related('repair', 'repair__voucherType', 'repair__supplier', 'repair__client')

        if from_date:
            sp_qs = sp_qs.filter(repair__date__gte=from_date)
        if to_date:
            sp_qs = sp_qs.filter(repair__date__lte=to_date)
        if voucher_type_id:
            sp_qs = sp_qs.filter(repair__voucherType_id=voucher_type_id)

        for d in sp_qs:
            ledger = d.repair.supplier or d.repair.client
            report_rows.append({
                'date': d.repair.date,
                'voucher_no': d.repair.voucher_no,
                'voucher_type': d.repair.voucherType.VoucherName,
                'ledger': ledger.ledger_name if ledger else '-',
                'stock_in': 0,
                'stock_out': d.quantity or 0,
            })

                # ---- Delivery Contract Spare Parts -> Stock Out ----
        dcsp_qs = DeliveryContractSpareParts.objects.filter(
            sparepart_id=item_id
        ).select_related('delivery_contract', 'delivery_contract__voucherType', 'delivery_contract__customer')

        if from_date:
            dcsp_qs = dcsp_qs.filter(delivery_contract__date__gte=from_date)
        if to_date:
            dcsp_qs = dcsp_qs.filter(delivery_contract__date__lte=to_date)
        if voucher_type_id:
            dcsp_qs = dcsp_qs.filter(delivery_contract__voucherType_id=voucher_type_id)

        for d in dcsp_qs:
            report_rows.append({
                'date': d.delivery_contract.date,
                'voucher_no': d.delivery_contract.voucher_no,
                'voucher_type': d.delivery_contract.voucherType.VoucherName,
                'ledger': d.delivery_contract.customer.ledger_name if d.delivery_contract.customer else '-',
                'stock_in': 0,
                'stock_out': d.quantity or 0,
            })

        # Sort date-wise, top to bottom
        report_rows.sort(key=lambda r: (r['date'], r['voucher_no']))

    total_in = sum(r['stock_in'] for r in report_rows)
    total_out = sum(r['stock_out'] for r in report_rows)
    balance = total_in - total_out    

    context = {
        'items': items,
        'voucher_types': voucher_types,
        'report_rows': report_rows,
        'selected_item': item_id,
        'from_date': from_date or '',
        'to_date': to_date or '',
        'selected_voucher_type': voucher_type_id or '',
        'total_in': total_in,
        'total_out': total_out,
        'balance': balance,
    }
    return render(request, 'stock_report.html', context)    


def current_stock_report(request):
    item_group_id = request.GET.get('item_group')
    search = request.GET.get('search', '').strip()
    stock_status = request.GET.get('stock_status')  # '', 'in_stock', 'out_of_stock', 'negative'

    item_groups = ItemGroup.objects.all()

    # ---- Aggregate Stock In: Opening Stock ----
    opening_qs = OpeningStockDetail.objects.filter(
        opening_stock__IsCleared=False
    ).values('item_name').annotate(total=Sum('quantity'))
    opening_map = {row['item_name']: row['total'] or 0 for row in opening_qs}

        # ---- Aggregate Stock In: Purchase ----
    purchase_qs = PurchaseDetail.objects.filter(
        purchase__isDeleted=False
    ).exclude(
        item_name__item_class='Service Item'
    ).values('item_name').annotate(total=Sum('quantity'))
    purchase_map = {row['item_name']: row['total'] or 0 for row in purchase_qs}

    # ---- Aggregate Stock In: Return Spare Parts (excludes Missing condition) ----
    return_sp_qs = ReturnSparePartsDetails.objects.exclude(
        condition='Missing'
    ).values('sparepart').annotate(total=Sum('quantity'))
    return_sp_map = {row['sparepart']: row['total'] or 0 for row in return_sp_qs}

    # ---- Aggregate Stock Out: Repair / SpareParts ----
    repair_qs = SpareParts.objects.values('sparepart').annotate(total=Sum('quantity'))
    repair_map = {row['sparepart']: row['total'] or 0 for row in repair_qs}

    # ---- Aggregate Stock Out: Delivery Contract Spare Parts ----
    delivery_contract_sp_qs = DeliveryContractSpareParts.objects.values('sparepart').annotate(total=Sum('quantity'))
    delivery_contract_sp_map = {row['sparepart']: row['total'] or 0 for row in delivery_contract_sp_qs}

    # ---- Base item list ----
    items_qs = Item.objects.all().select_related('item_group') if hasattr(Item, 'item_group') else Item.objects.all()

    if item_group_id:
        items_qs = items_qs.filter(item_group_id=item_group_id)
    if search:
        items_qs = items_qs.filter(item_name__icontains=search)

    items_qs = items_qs.order_by('item_name')

    report_rows = []
    total_in_sum = 0
    total_out_sum = 0

    for item in items_qs:
        stock_in = opening_map.get(item.id, 0) + purchase_map.get(item.id, 0) + return_sp_map.get(item.id, 0)
        stock_out = repair_map.get(item.id, 0) + delivery_contract_sp_map.get(item.id, 0)
        current_stock = stock_in - stock_out

        if stock_status == 'in_stock' and current_stock <= 0:
            continue
        if stock_status == 'out_of_stock' and current_stock != 0:
            continue
        if stock_status == 'negative' and current_stock >= 0:
            continue

        total_in_sum += stock_in
        total_out_sum += stock_out

        report_rows.append({
            'item_id': item.id,
            'item_name': item.item_name,
            'item_group': getattr(item.item_group, 'group_code', '-') if hasattr(item, 'item_group') and item.item_group else '-',
            'stock_in': stock_in,
            'stock_out': stock_out,
            'current_stock': current_stock,
        })

    context = {
        'item_groups': item_groups,
        'report_rows': report_rows,
        'selected_item_group': item_group_id or '',
        'search': search,
        'stock_status': stock_status or '',
        'total_in_sum': total_in_sum,
        'total_out_sum': total_out_sum,
        'total_current_stock': total_in_sum - total_out_sum,
    }
    return render(request, 'current_stock_report.html', context)    


def purchase_report(request):
    """
    Purchase Report — lists purchase vouchers (header) with their
    line items (detail), filterable by date range, ledger, item group,
    item, and payment mode.
    """
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    ledger_id = request.GET.get('ledger')
    item_group_id = request.GET.get('item_group')
    item_id = request.GET.get('item')
    payment_mode = request.GET.get('payment_mode')
    voucher_no = request.GET.get('voucher_no')

    purchases = (
        PurchaseMaster.objects
        .filter(isDeleted=False)
        .select_related('ledger', 'voucherType')
        .prefetch_related('items', 'items__item_group', 'items__item_name', 'items__unit')
        .order_by('-transaction_date', '-auto_no')
    )

    if from_date:
        purchases = purchases.filter(transaction_date__gte=from_date)
    if to_date:
        purchases = purchases.filter(transaction_date__lte=to_date)
    if ledger_id:
        purchases = purchases.filter(ledger_id=ledger_id)
    if payment_mode:
        purchases = purchases.filter(payment_mode=payment_mode)
    if voucher_no:
        purchases = purchases.filter(voucher_no__icontains=voucher_no)
    if item_group_id:
        purchases = purchases.filter(items__item_group_id=item_group_id).distinct()
    if item_id:
        purchases = purchases.filter(items__item_name_id=item_id).distinct()

    # Build report rows: one row per (purchase, item) pair, but keep
    # header fields attached so the template can rowspan / group them.
    report_data = []
    grand_total_net = 0
    grand_total_tax = 0
    grand_total_amount = 0
    grand_total_discount = 0

    for purchase in purchases:
        items = list(purchase.items.all())
        grand_total_net += purchase.total_net_value or 0
        grand_total_tax += purchase.total_tax_amount or 0
        grand_total_amount += purchase.grand_total_amount or 0
        grand_total_discount += purchase.discount or 0

        if item_group_id:
            items = [i for i in items if str(i.item_group_id) == str(item_group_id)]
        if item_id:
            items = [i for i in items if str(i.item_name_id) == str(item_id)]

        report_data.append({
            'purchase': purchase,
            'items': items,
            'item_count': len(items),
        })

    context = {
        'report_data': report_data,
        'grand_total_net': grand_total_net,
        'grand_total_tax': grand_total_tax,
        'grand_total_amount': grand_total_amount,
        'grand_total_discount': grand_total_discount,
        'ledgers': LedgerCreation.objects.all().order_by('LedgerName') if hasattr(LedgerCreation, 'LedgerName') else LedgerCreation.objects.all(),
        'item_groups': _get_item_groups(),
        'items_list': Item.objects.filter(
            id__in=PurchaseDetail.objects.filter(purchase__isDeleted=False).values('item_name_id')
        ),
        'payment_modes': PurchaseMaster.PAYMENT_MODE_CHOICES,
        'filters': {
            'from_date': from_date or '',
            'to_date': to_date or '',
            'ledger': ledger_id or '',
            'item_group': item_group_id or '',
            'item': item_id or '',
            'payment_mode': payment_mode or '',
            'voucher_no': voucher_no or '',
        },
    }
    return render(request, 'purchase_report.html', context)

def _get_item_groups():
   
    return ItemGroup.objects.all().order_by('name') if hasattr(ItemGroup, 'name') else ItemGroup.objects.all()    


#API used in Repair form and Purchase to show Current Stock of Item
def get_item_current_stock(request):
    item_id = request.GET.get('item_id')
    if not item_id:
        return JsonResponse({'success': False, 'error': 'item_id required'})

    try:
        item = Item.objects.get(id=item_id)
    except Item.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Item not found'})

    opening_qty = OpeningStockDetail.objects.filter(
        opening_stock__IsCleared=False,
        item_name=item
    ).aggregate(total=Sum('quantity'))['total'] or 0

    purchase_qty = PurchaseDetail.objects.filter(
        purchase__isDeleted=False,
        item_name=item
    ).exclude(
        item_name__item_class='Service Item'
    ).aggregate(total=Sum('quantity'))['total'] or 0

    repair_qty = SpareParts.objects.filter(
        sparepart=item
    ).aggregate(total=Sum('quantity'))['total'] or 0

    stock_in = opening_qty + purchase_qty
    stock_out = repair_qty
    current_stock = stock_in - stock_out

    return JsonResponse({
        'success': True,
        'current_stock': float(current_stock),
        'stock_in': float(stock_in),
        'stock_out': float(stock_out),
    })    