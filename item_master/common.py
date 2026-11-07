from __future__ import annotations
from accounts_app.models import *
from django.db import models
from item_master.models import *
from fleet_app.models import Vouchers
import datetime, json
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Iterable, Tuple
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.http import JsonResponse



def get_all_subgroup_ids(*group_ids):

    #Recursively get all subgroup IDs for the given group IDs.
    #Includes the given IDs themselves.


    ids = list(group_ids)
    for group_id in group_ids:
        children = Groups.objects.filter(groupId=group_id)
        for child in children:
            ids += get_all_subgroup_ids(child.id)
    return list(set(ids))  # remove duplicates


def get_ledgers_by_group_ids(*group_ids):

    #Get all LedgerCreation objects for the given group IDs and their subgroups.
    
    all_group_ids = get_all_subgroup_ids(*group_ids)
    return LedgerCreation.objects.filter(groups__id__in=all_group_ids)



def filter_voucher_types(form, allowed_ids):
    #   
    form.fields['voucherType'].queryset = Vouchers.objects.filter(id__in=allowed_ids)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    




# 1) Voucher “kind” and flow direction
class VoucherKind:
    PURCHASE = "Purchase"
    SALES = "Sales"
    PURCHASE_RETURN = "Purchase Return"
    SALES_RETURN = "Sales Return"
    OPENING_BALANCE = "Opening Balance"
    ITEM_GRV = "Item GRV"
    OPENING_STOCK = "Opening Stock"  # Added

# Flow: whether stock increases or decreases in base unit
FLOW_IN = +1
FLOW_OUT = -1

FLOW_BY_KIND = {
    VoucherKind.PURCHASE: FLOW_IN,
    VoucherKind.SALES: FLOW_OUT,
    VoucherKind.PURCHASE_RETURN: FLOW_OUT,   # returning to supplier reduces our stock
    VoucherKind.SALES_RETURN: FLOW_IN,       # customer returns increases our stock
    VoucherKind.OPENING_BALANCE: FLOW_IN,
    VoucherKind.ITEM_GRV: FLOW_IN,
    VoucherKind.OPENING_STOCK: FLOW_IN,      # Added (Opening stock increases stock levels)
}

# 2) Input row DTO (strict: use Decimal, not float)
@dataclass
class LineRow:
    item_id: int
    unit_id: Optional[int]     # selected unit in UI (may be base or alt)
    batch_id: Optional[int]
    quantity: Decimal
    rate: Decimal
    mfd: Optional[datetime.date] = None
    exp: Optional[datetime.date] = None
    item_group_id: Optional[int] = None
    item_code: str = ""
    barcode_code: str = ""
    item_net_amount: Decimal = Decimal(0)
    tax: Decimal = Decimal(0)
    item_tax_amount: Decimal = Decimal(0)
    item_total_amount: Decimal = Decimal(0)
    free_quantity: Decimal = Decimal(0)
    cost: Decimal = Decimal(0)  # for purchase/opening stock
    serial_no: str = ""         # Added for opening stock

# 3) Parsing helper (takes your JSON `items_data`)
def parse_items_data(raw: str) -> list[LineRow]:
    try:
        data = json.loads(raw or "[]")
    except Exception:
        raise ValidationError("Invalid items payload.")

    rows: list[LineRow] = []
    for d in data:
        rows.append(LineRow(
            item_id=int(d.get("item_name") or d.get("item_name_id")),
            unit_id=(int(d["unit"]) if d.get("unit") else (int(d["unit_id"]) if d.get("unit_id") else None)),
            batch_id=(int(d["batch"]) if d.get("batch") else (int(d["batch_id"]) if d.get("batch_id") else None)),
            quantity=Decimal(str(d.get("quantity", "0"))),
            rate=Decimal(str(d.get("purchase_rate") or "0")),
            mfd=(_to_date(d.get("mfd") or d.get("MFD"))),
            exp=(_to_date(d.get("exp") or d.get("EXP"))),
            item_group_id=int(d["item_group_id"]) if d.get("item_group_id") else None,
            item_code=d.get("item_code") or "",
            barcode_code=d.get("barcode_code") or "",
            item_net_amount=Decimal(str(d.get("item_net_amount", "0"))),
            tax=Decimal(str(d.get("tax", "0"))),
            item_tax_amount=Decimal(str(d.get("item_tax_amount", "0"))),
            item_total_amount=Decimal(str(d.get("item_total_amount", "0"))),
            free_quantity=Decimal(str(d.get("free_quantity", "0"))),
            cost=Decimal(str(d.get("cost") or d.get("Cost") or "0")),  # Map from either key case
            serial_no=d.get("serial_no") or d.get("SerialNo") or "",  # Added mapping
        ))
    if not rows:
        raise ValidationError("Please add at least one item.")
    return rows

def _to_date(s: Optional[str]) -> Optional[datetime.date]:
    if not s: return None
    try:
        return datetime.date.fromisoformat(s)
    except Exception:
        return None

# 4) Unit conversion utilities
def uc_factor_for(item: Item, selected_unit_id: Optional[int]) -> Decimal:
    """Return factor to convert selected unit -> base unit."""
    if not selected_unit_id or str(selected_unit_id) == str(item.item_unit_id):
        return Decimal(1)
    alt = ItemAlterUnit.objects.filter(item=item, unit_id=selected_unit_id).first()
    if not alt:
        raise ValidationError(f"Invalid unit for item {item.item_name}")
    return alt.uc_factor

def to_base_qty(item: Item, unit_id: Optional[int], qty: Decimal) -> Decimal:
    return qty * uc_factor_for(item, unit_id)

# 5) Stock upsert (single source of truth)
def upsert_stock(
    *,
    item: Item,
    batch_id: Optional[int],
    base_unit_id: int,
    base_qty_delta: Decimal,        # signed by flow
    rate: Decimal,
    voucher_date: datetime.date,
    voucher_type: str,
    voucher_id: int,
    cost_center,
) -> Stock:
    stock_value_delta = rate * base_qty_delta
    entry, created = Stock.objects.get_or_create(
        item_id=item.id,
        batch_id=batch_id,
        unit_id=base_unit_id,       # always store in base unit
        defaults={
            "voucherDate": voucher_date,
            "voucherType": voucher_type,
            "voucherNo": voucher_id,
            "costCenter": cost_center,
            "rate": rate,
            "in_quantity": (base_qty_delta if base_qty_delta > 0 else 0),
            "out_quantity": (abs(base_qty_delta) if base_qty_delta < 0 else 0),
            "stock_value": stock_value_delta,
        }
    )
    if not created:
        # Move quantities against existing
        if base_qty_delta >= 0:
            # Incoming: first net against any negative out, then add to in
            if entry.out_quantity > 0:
                nettable = min(entry.out_quantity, base_qty_delta)
                entry.out_quantity -= nettable
                base_qty_delta -= nettable
            entry.in_quantity += base_qty_delta
        else:
            # Outgoing: consume from in_quantity, then add to out shortfall
            wanted = abs(base_qty_delta)
            if entry.in_quantity >= wanted:
                entry.in_quantity -= wanted
            else:
                short = wanted - entry.in_quantity
                entry.in_quantity = 0
                entry.out_quantity += short
        entry.stock_value += stock_value_delta

        total_qty = entry.in_quantity - entry.out_quantity

        if total_qty > 0:
            entry.rate = entry.stock_value / total_qty
        else:
            entry.rate = 0
            
        entry.voucherDate = voucher_date
        entry.voucherType = voucher_type
        entry.voucherNo = voucher_id
        entry.costCenter = cost_center
        entry.save()
    return entry


# 6) Details writer (dispatch by voucher kind)
def create_detail_for_kind(kind: str, voucher, row: LineRow, item: Item):
    if kind == VoucherKind.PURCHASE:
        return PurchaseDetail.objects.create(
            purchase=voucher,
            item_group_id=row.item_group_id or None, 
            item_name_id=row.item_id,
            item_code=row.item_code,
            barcode_code=row.barcode_code,
            quantity=row.quantity,
            purchase_rate=row.rate,
            item_net_amount=row.item_net_amount,
            tax=row.tax,
            item_tax_amount=row.item_tax_amount,
            unit_id=row.unit_id or None,
            free_quantity=getattr(row, "free_quantity", 0),
            MFD=row.mfd,
            EXP=row.exp,
            sales_rate=None,
            profit=None,
            item_total_amount=row.item_total_amount,
            Batch_id=row.batch_id or None,
            Cost=getattr(row, "cost", None),
        )

    elif kind == VoucherKind.OPENING_STOCK:
        # Calculate base units and rates specifically for OpeningStockDetail
        factor = uc_factor_for(item, row.unit_id)
        qty_in_base = row.quantity * factor
        rate_in_base = row.rate / factor if factor > 0 else row.rate

        return OpeningStockDetail.objects.create(
            opening_stock=voucher,
            item_code=row.item_code,
            item_name_id=row.item_id,
            barcode_code=row.barcode_code,
            quantity=row.quantity,
            purchase_rate=row.rate,
            item_net_amount=row.item_net_amount,
            tax=row.tax,
            item_tax_amount=row.item_tax_amount,
            unit_id=row.unit_id or None,
            item_total_amount=row.item_total_amount,
            QtyInBaseUnit=qty_in_base,
            RateInBaseUnit=rate_in_base,
            BaseUnit_id=item.item_unit_id,
            SerialNo=row.serial_no,
            Cost=row.cost,
        )

    elif kind == VoucherKind.SALES_RETURN:
        return SalesReturnDetail.objects.create(
            sales_return=voucher,   # ✅ matches your model (FK to PurchaseReturnMaster)
            item_name_id=row.item_id,
            item_code=row.item_code,
            barcode_code=row.barcode_code,
            quantity=row.quantity,
            purchase_rate=row.rate,
            item_net_amount=row.item_net_amount,
            tax=row.tax,
            item_tax_amount=row.item_tax_amount,
            unit_id=row.unit_id or None,
            free_quantity=getattr(row, "free_quantity", 0),
            MFD=row.mfd,
            EXP=row.exp,
            sales_rate=None,
            profit=None,
            item_total_amount=row.item_total_amount,
            Batch_id=row.batch_id or None,
            Cost=getattr(row, "cost", None),
        )

    elif kind == VoucherKind.ITEM_GRV:
        return ItemGrvDetail.objects.create(
            item_grv=voucher,
            item_name_id=row.item_id,
            item_code=row.item_code,
            barcode_code=row.barcode_code,
            quantity=row.quantity,
            tax=row.tax,
            unit_id=row.unit_id or None,
            free_quantity=getattr(row, "free_quantity", 0),
            MFD=row.mfd,
            EXP=row.exp,
            Batch_id=row.batch_id or None,
            Cost=getattr(row, "cost", None),
        )    

    elif kind == VoucherKind.SALES:
        return SalesDetail.objects.create(
            sales_voucher=voucher,  # ✅ matches your model
            item_name_id=row.item_id,
            item_code=row.item_code,
            barcode_code=row.barcode_code,
            quantity=row.quantity,
            sales_rate=row.rate,
            item_net_amount=row.item_net_amount,
            tax=row.tax,
            item_tax_amount=row.item_tax_amount,
            unit_id=row.unit_id or None,
            MFD=row.mfd,
            EXP=row.exp,
            item_total_amount=row.item_total_amount,
            Batch_id=row.batch_id or None,
        )

    elif kind == VoucherKind.PURCHASE_RETURN:
        return PurchaseReturnDetail.objects.create(
            purchase_return=voucher,  # ✅ matches your model
            item_name_id=row.item_id,
            item_code=row.item_code,
            barcode_code=row.barcode_code,
            quantity=row.quantity,
            sales_rate=row.rate,
            item_net_amount=row.item_net_amount,
            tax=row.tax,
            item_tax_amount=row.item_tax_amount,
            unit_id=row.unit_id or None,
            MFD=row.mfd,
            EXP=row.exp,
            item_total_amount=row.item_total_amount,
            Batch_id=row.batch_id or None,
        )

    else:
        raise ValidationError(f"Unsupported voucher kind {kind}")

def get_current_avg_rate(item, batch_id, cost_center):
    stock = Stock.objects.filter(
        item=item,
        batch_id=batch_id,
        costCenter=cost_center
    ).first()

    return stock.rate if stock else 0        

def process_voucher(
    *,
    kind: str,
    voucher_form,
    items_raw_json: str,
    create_detail=True,
) -> Tuple[object, list[LineRow]]:
    """
    Saves voucher (from form), creates details, updates Stock in base units,
    and posts accounting hooks. Returns (voucher, parsed_rows).
    """
    if not voucher_form.is_valid():
        raise ValidationError(voucher_form.errors.as_json())

    rows = parse_items_data(items_raw_json)
    with transaction.atomic():
        voucher = voucher_form.save(commit=False)
        voucher.save()

        flow = FLOW_BY_KIND[kind]
        for row in rows:
            item = get_object_or_404(Item, id=row.item_id)
            base_qty = to_base_qty(item, row.unit_id, row.quantity) * Decimal(flow)

            # Update stock (always in base unit)
            if kind == VoucherKind.SALES:
                rate = get_current_avg_rate(item, row.batch_id, voucher.cost_center)
            elif kind == VoucherKind.ITEM_GRV:
                rate = Decimal(0)
            else:
                rate = row.rate
            upsert_stock(
                item=item,
                batch_id=row.batch_id,
                base_unit_id=item.item_unit_id,
                base_qty_delta=base_qty,
                rate=rate,
                voucher_date=voucher.transaction_date,
                voucher_type=voucher.voucherType,
                voucher_id=voucher.id,
                cost_center=voucher.cost_center,
            )

            if create_detail:
                create_detail_for_kind(kind, voucher, row, item)

    return voucher, rows

def reverse_stock_for_voucher(voucher, kind):
    flow = FLOW_BY_KIND[kind] * -1  # reverse flow

    if kind == VoucherKind.PURCHASE:
        details = PurchaseDetail.objects.filter(purchase=voucher)
    elif kind == VoucherKind.OPENING_STOCK:
        details = OpeningStockDetail.objects.filter(opening_stock=voucher)
    elif kind == VoucherKind.SALES:
        details = SalesDetail.objects.filter(sales_voucher=voucher)
    elif kind == VoucherKind.PURCHASE_RETURN:
        details = PurchaseReturnDetail.objects.filter(purchase=voucher)
    elif kind == VoucherKind.SALES_RETURN:
        details = SalesReturnDetail.objects.filter(sales_voucher=voucher)
    elif kind == VoucherKind.ITEM_GRV:
        details = ItemGrvDetail.objects.filter(item_grv=voucher)    
    else:
        return

    for d in details:
        item = Item.objects.get(id=d.item_name_id)
        base_qty = to_base_qty(item, d.unit_id, d.quantity) * flow

        if kind == VoucherKind.ITEM_GRV:
            rate = Decimal(0)
        else:
            rate = d.purchase_rate if hasattr(d, 'purchase_rate') else d.sales_rate

        # Support clean execution even if models exclude Batch_id
        batch_id = getattr(d, 'Batch_id', None)

        upsert_stock(
            item=item,
            batch_id=batch_id,
            base_unit_id=item.item_unit_id,
            base_qty_delta=base_qty,
            rate=rate,
            voucher_date=voucher.transaction_date,
            voucher_type=voucher.voucherType,
            voucher_id=voucher.id,
            cost_center=voucher.cost_center,
        )





#LedgerPosting for Sales
def create_ledger_postings_for_sale(sale):
    """
    Creates LedgerPosting entries for a given SalesMaster instance.
    Handles debit entry for customer/Cash ledger,
    and credit entries for sales, tax, and discount allowed.
    """
    try:
        # --- Common Data ---
        transaction_date = sale.transaction_date
        voucher_type = Vouchers.objects.get(id=14)  # Sales VoucherType
        voucher_no = sale.voucher_no
        cost_center = sale.cost_center
        fy = None  # future FK (optional)

        # ---------------------- DEBIT ENTRY ----------------------
        LedgerPosting.objects.create(
            date=transaction_date,
            VoucherType=voucher_type,
            VoucherNo=sale.id,
            ledger=sale.ledger,  # selected Cash/Customer ledger from sale
            debit=sale.grand_total_amount,
            credit=None,
            CostCenter=cost_center,
            FY=fy,
            IsDeleted=False
        )
        # Discount Allowed Ledger (id=19)
        if sale.discount > 0:
            LedgerPosting.objects.create(
                date=transaction_date,
                VoucherType=voucher_type,
                VoucherNo=sale.id,
                ledger=LedgerCreation.objects.get(id=19), # Discount Allowed Ledger
                debit=sale.discount,
                credit=None,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
            )

        # ---------------------- CREDIT ENTRY 1 ----------------------
        # Sales Ledger (id=7)
        LedgerPosting.objects.create(
            date=transaction_date,
            VoucherType=voucher_type,
            VoucherNo=sale.id,
            ledger=LedgerCreation.objects.get(id=7), # Sales Account Ledger
            debit=None,
            credit=sale.total_net_value,
            CostCenter=cost_center,
            FY=fy,
            IsDeleted=False
        )

        # ---------------------- CREDIT ENTRY 2 ----------------------
        # Tax Ledger (id=2)
        if sale.total_tax_amount > 0:
            LedgerPosting.objects.create(
                date=transaction_date,
                VoucherType=voucher_type,
                VoucherNo=sale.id,
                ledger=LedgerCreation.objects.get(id=2), # Vat Payable Ledger
                debit=None,
                credit=sale.total_tax_amount,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
            )
        
        if sale.Freight > 0:
            LedgerPosting.objects.create(
                date=transaction_date,
                VoucherType=voucher_type,
                VoucherNo=sale.id,
                ledger=LedgerCreation.objects.get(id=13), # Freight Ledger
                debit=None,
                credit=sale.Freight,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
        )    
            
    except Exception as e:
        print(f"Error creating LedgerPosting for sale {sale.id}: {e}")


def create_ledger_postings_for_purchasereturn(purchase_return):
    """
    Creates LedgerPosting entries for a given PurchaseReturnMaster instance.
    Handles debit entry for customer/Cash ledger,
    and credit entries for purchase return, tax, and discount allowed.
    """
    try:
        # --- Common Data ---
        transaction_date = purchase_return.transaction_date
        voucher_type = Vouchers.objects.get(id=18)  # Purchase Return VoucherType
        voucher_no = purchase_return.voucher_no
        cost_center = purchase_return.cost_center
        fy = None  # future FK (optional)

        # ---------------------- DEBIT ENTRY ----------------------
        LedgerPosting.objects.create(
            date=transaction_date,
            VoucherType=voucher_type,
            VoucherNo=purchase_return.id,
            ledger=purchase_return.ledger,  # selected Cash/Customer ledger from sale
            debit=purchase_return.grand_total_amount,
            credit=None,
            CostCenter=cost_center,
            FY=fy,
            IsDeleted=False
        )
        # Discount Allowed Ledger (id=19)
        if purchase_return.discount > 0:
            LedgerPosting.objects.create(
                date=transaction_date,
                VoucherType=voucher_type,
                VoucherNo=purchase_return.id,
                ledger=LedgerCreation.objects.get(id=19), # Discount Allowed Ledger
                debit=purchase_return.discount,
                credit=None,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
            )

        # ---------------------- CREDIT ENTRY 1 ----------------------
        # Purchase Return Ledger (id=7)
        LedgerPosting.objects.create(
            date=transaction_date,
            VoucherType=voucher_type,
            VoucherNo=purchase_return.id,
            ledger=LedgerCreation.objects.get(id=7), # Purchase Return Account Ledger
            debit=None,
            credit=purchase_return.total_net_value,
            CostCenter=cost_center,
            FY=fy,
            IsDeleted=False
        )

        # ---------------------- CREDIT ENTRY 2 ----------------------
        # Tax Ledger (id=2)
        if purchase_return.total_tax_amount > 0:
            LedgerPosting.objects.create(
                date=transaction_date,
                VoucherType=voucher_type,
                VoucherNo=purchase_return.id,
                ledger=LedgerCreation.objects.get(id=2), # Vat Payable Ledger
                debit=None,
                credit=purchase_return.total_tax_amount,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
            )
        
        if purchase_return.Freight > 0:
            LedgerPosting.objects.create(
                date=transaction_date,
                VoucherType=voucher_type,
                VoucherNo=purchase_return.id,
                ledger=LedgerCreation.objects.get(id=13), # Freight Ledger
                debit=None,
                credit=purchase_return.Freight,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
        )    
            
    except Exception as e:
        print(f"Error creating LedgerPosting for purchase return {purchase_return.id}: {e}")

        
        
#LedgerPosting for Purchase
def create_ledger_postings_for_purchase(purchase):
    """
    Creates LedgerPosting entries for a given PurchaseMaster instance.
    Deletes old postings first (for edit case).
    """
    voucher_type = Vouchers.objects.get(id=13)

    # ----------------------------------
    # DELETE OLD LEDGER POSTINGS
    # ----------------------------------
    LedgerPosting.objects.filter(
        VoucherType=voucher_type,
        VoucherNo=purchase.id
    ).delete()

    # ----------------------------------
    # CREDIT ENTRY
    # ----------------------------------
    LedgerPosting.objects.create(
        date=purchase.transaction_date,
        VoucherType=voucher_type,
        VoucherNo=purchase.id,
        ledger=purchase.ledger,
        debit=None,
        credit=purchase.grand_total_amount,
        CostCenter=purchase.cost_center,
        FY=None,
        IsDeleted=False
    )

    # Credit Discount Received
    if purchase.discount > 0:
        LedgerPosting.objects.create(
            date=purchase.transaction_date,
            VoucherType=voucher_type,
            VoucherNo=purchase.id,
            ledger=LedgerCreation.objects.get(id=20),
            debit=None,
            credit=purchase.discount,
            CostCenter=purchase.cost_center,
            FY=None,
            IsDeleted=False
        )

    # ----------------------------------
    # DEBIT ENTRY
    # ----------------------------------
    LedgerPosting.objects.create(
        date=purchase.transaction_date,
        VoucherType=voucher_type,
        VoucherNo=purchase.id,
        ledger=LedgerCreation.objects.get(id=6),
        debit=purchase.total_net_value,
        credit=None,
        CostCenter=purchase.cost_center,
        FY=None,
        IsDeleted=False
    )

    # Debit Tax Refundable
    if purchase.total_tax_amount > 0:
        LedgerPosting.objects.create(
            date=purchase.transaction_date,
            VoucherType=voucher_type,
            VoucherNo=purchase.id,
            ledger=LedgerCreation.objects.get(id=3),
            debit=purchase.total_tax_amount,
            credit=None,
            CostCenter=purchase.cost_center,
            FY=None,
            IsDeleted=False
        )


def create_ledger_postings_for_salesreturn(sales_return):
    """
    Creates LedgerPosting entries for a given SalesReturnMaster instance.
    Deletes old postings first (for edit case).
    """
    voucher_type = Vouchers.objects.get(id=19)

    # ----------------------------------
    # DELETE OLD LEDGER POSTINGS
    # ----------------------------------
    LedgerPosting.objects.filter(
        VoucherType=voucher_type,
        VoucherNo=sales_return.id
    ).delete()

    # ----------------------------------
    # CREDIT ENTRY
    # ----------------------------------
    LedgerPosting.objects.create(
        date=sales_return.transaction_date,
        VoucherType=voucher_type,
        VoucherNo=sales_return.id,
        ledger=sales_return.ledger,
        debit=None,
        credit=sales_return.grand_total_amount,
        CostCenter=sales_return.cost_center,
        FY=None,
        IsDeleted=False
    )

    # Credit Discount Received
    if sales_return.discount > 0:
        LedgerPosting.objects.create(
            date=sales_return.transaction_date,
            VoucherType=voucher_type,
            VoucherNo=sales_return.id,
            ledger=LedgerCreation.objects.get(id=20),
            debit=None,
            credit=sales_return.discount,
            CostCenter=sales_return.cost_center,
            FY=None,
            IsDeleted=False
        )

    # ----------------------------------
    # DEBIT ENTRY
    # ----------------------------------
    LedgerPosting.objects.create(
        date=sales_return.transaction_date,
        VoucherType=voucher_type,
        VoucherNo=sales_return.id,
        ledger=LedgerCreation.objects.get(id=6),
        debit=sales_return.total_net_value,
        credit=None,
        CostCenter=sales_return.cost_center,
        FY=None,
        IsDeleted=False
    )

    # Debit Tax Refundable
    if sales_return.total_tax_amount > 0:
        LedgerPosting.objects.create(
            date=sales_return.transaction_date,
            VoucherType=voucher_type,
            VoucherNo=sales_return.id,
            ledger=LedgerCreation.objects.get(id=3),
            debit=sales_return.total_tax_amount,
            credit=None,
            CostCenter=sales_return.cost_center,
            FY=None,
            IsDeleted=False
        )


def delete_ledger_postings(voucher_type_id, voucher_id):
    qs = LedgerPosting.objects.filter(
        VoucherType_id=voucher_type_id,
        VoucherNo=voucher_id
    )
    print(f"Deleting {qs.count()} postings for type={voucher_type_id!r} no={voucher_id!r}")
    qs.delete()  


def get_item_avg_cost(request):
    item_id = request.GET.get('item_id')

    if not item_id:
        return JsonResponse({'success': False, 'rate': 0})

    stock = Stock.objects.filter(item_id=item_id).order_by('-id').first()

    return JsonResponse({
        'success': True,
        'rate': float(stock.rate) if stock else 0
    })    