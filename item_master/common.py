from __future__ import annotations
from accounts_app.models import *
from django.db import models
from item_master.models import PurchaseMaster, SalesMaster, PurchaseReturnMaster, SalesReturnMaster, Item, Stock, ItemAlterUnit, PurchaseDetail, SalesDetail, PurchaseReturnDetail, SalesReturnDetail
from fleet_app.models import Vouchers
import datetime, json
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Iterable, Tuple
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError



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

# Flow: whether stock increases or decreases in base unit
FLOW_IN = +1
FLOW_OUT = -1

FLOW_BY_KIND = {
    VoucherKind.PURCHASE: FLOW_IN,
    VoucherKind.SALES: FLOW_OUT,
    VoucherKind.PURCHASE_RETURN: FLOW_OUT,   # returning to supplier reduces our stock
    VoucherKind.SALES_RETURN: FLOW_IN,       # customer returns increases our stock
    VoucherKind.OPENING_BALANCE: FLOW_IN,
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
    item_code: str = ""
    barcode_code: str = ""
    item_net_amount: Decimal = Decimal(0)
    tax: Decimal = Decimal(0)
    item_tax_amount: Decimal = Decimal(0)
    item_total_amount: Decimal = Decimal(0)
    free_quantity: Decimal = Decimal(0)
    cost: Decimal = Decimal(0)  # for purchase

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
            rate=Decimal(str(d.get("sales_rate") or d.get("purchase_rate") or "0")),
            mfd=(_to_date(d.get("mfd") or d.get("MFD"))),
            exp=(_to_date(d.get("exp") or d.get("EXP"))),
            item_code=d.get("item_code") or "",
            barcode_code=d.get("barcode_code") or "",
            item_net_amount=Decimal(str(d.get("item_net_amount", "0"))),
            tax=Decimal(str(d.get("tax", "0"))),
            item_tax_amount=Decimal(str(d.get("item_tax_amount", "0"))),
            item_total_amount=Decimal(str(d.get("item_total_amount", "0"))),
            free_quantity=Decimal(str(d.get("free_quantity", "0"))),
            cost=Decimal(str(d.get("cost", "0"))),
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
        entry.rate = rate  # last rate wins; adjust if you want weighted avg
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

    elif kind == VoucherKind.PURCHASE_RETURN:
        return PurchaseReturnDetail.objects.create(
            purchase=voucher,   # ✅ matches your model (FK to PurchaseReturnMaster)
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

    elif kind == VoucherKind.SALES_RETURN:
        return SalesReturnDetail.objects.create(
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

    else:
        raise ValidationError(f"Unsupported voucher kind {kind}")

# def create_detail_for_kind(kind: str, voucher, row: LineRow, item: Item):
#     if kind in (VoucherKind.PURCHASE, VoucherKind.PURCHASE_RETURN, VoucherKind.OPENING_BALANCE):
#         # Purchase-like details
#         return PurchaseDetail.objects.create(
#             purchase=voucher,
#             item_name_id=row.item_id,
#             item_code=row.item_code,
#             barcode_code=row.barcode_code,
#             quantity=row.quantity,
#             purchase_rate=row.rate,
#             item_net_amount=row.item_net_amount,
#             tax=row.tax,
#             item_tax_amount=row.item_tax_amount,
#             unit_id=row.unit_id or None,
#             free_quantity=row.free_quantity,
#             MFD=row.mfd,
#             EXP=row.exp,
#             sales_rate=None,   # set if you need
#             profit=None,       # set if you need
#             item_total_amount=row.item_total_amount,
#             Batch_id=row.batch_id or None,
#             Cost=row.cost,
#         )
#     elif kind in (VoucherKind.SALES, VoucherKind.SALES_RETURN):
#         return SalesDetail.objects.create(
#             sales_voucher=voucher,
#             item_name_id=row.item_id,
#             item_code=row.item_code,
#             barcode_code=row.barcode_code,
#             quantity=row.quantity,
#             sales_rate=row.rate,
#             item_net_amount=row.item_net_amount,
#             tax=row.tax,
#             item_tax_amount=row.item_tax_amount,
#             unit_id=row.unit_id or None,
#             item_total_amount=row.item_total_amount,
#             Batch_id=row.batch_id or None,
#             MFD=row.mfd,
#             EXP=row.exp
#         )
#     else:
#         raise ValidationError(f"Unsupported voucher kind {kind}")

# 7) Ledger / Outstanding posting (optional hooks)
# def post_daybook_if_needed(kind: str, voucher):
#     # Purchase often credits cash/bank; Sales debits. Adapt to your schema.
#     if kind == VoucherKind.SALES:
#         DayBookReport.objects.create(
#             date=voucher.transaction_date,
#             ledger=voucher.ledger,
#             voucher_type='Sales',
#             debit_amount=voucher.grand_total_amount,
#             credit_amount=Decimal(0),
#             invoice_no=voucher.voucher_no
#         )
#     elif kind == VoucherKind.PURCHASE:
#         DayBookReport.objects.create(
#             date=voucher.transaction_date,
#             ledger=voucher.ledger,
#             voucher_type='Purchase',
#             debit_amount=Decimal(0),
#             credit_amount=voucher.grand_total_amount,
#             invoice_no=voucher.voucher_no
#         )
#     elif kind == VoucherKind.PURCHASE_RETURN:
#         DayBookReport.objects.create(
#             date=voucher.transaction_date,
#             ledger=voucher.ledger,
#             voucher_type='Purchase Return',
#             debit_amount=Decimal(0),
#             credit_amount=voucher.grand_total_amount,
#             invoice_no=voucher.voucher_no
#         )
#     elif kind == VoucherKind.SALES_RETURN:
#         DayBookReport.objects.create(
#             date=voucher.transaction_date,
#             ledger=voucher.ledger,
#             voucher_type='Sales Return',
#             debit_amount=Decimal(0),
#             credit_amount=voucher.grand_total_amount,
#             invoice_no=voucher.voucher_no
#         )        
#     # Add entries for returns if you maintain them

# def post_outstanding_if_needed(kind: str, voucher):
#     if voucher.payment_mode != "Credit":
#         return
#     if kind == VoucherKind.PURCHASE:
#         OutstandingReport.objects.create(
#             ledger=voucher.ledger,
#             bill_no=voucher.auto_no,
#             invoice_no=voucher.voucher_no,
#             transaction_type='Purchase',
#             debit_amount=Decimal(0),
#             credit_amount=voucher.grand_total_amount,
#             balance_amount=voucher.grand_total_amount
#         )
#     elif kind == VoucherKind.SALES:
#         OutstandingReport.objects.create(
#             ledger=voucher.ledger,
#             bill_no=voucher.auto_no or "",
#             invoice_no=voucher.voucher_no,
#             transaction_type='Sales',
#             debit_amount=voucher.grand_total_amount,
#             credit_amount=Decimal(0),
#             balance_amount=voucher.grand_total_amount
#         )
#     elif kind == VoucherKind.PURCHASE_RETURN:
#         OutstandingReport.objects.create(
#             ledger=voucher.ledger,
#             bill_no=voucher.auto_no,
#             invoice_no=voucher.voucher_no,
#             transaction_type='Purchase Return',
#             debit_amount=Decimal(0),
#             credit_amount=voucher.grand_total_amount,
#             balance_amount=voucher.grand_total_amount
#         )
#     elif kind == VoucherKind.SALES_RETURN:
#         OutstandingReport.objects.create(
#             ledger=voucher.ledger,
#             bill_no=voucher.auto_no or "",
#             invoice_no=voucher.voucher_no,
#             transaction_type='Sales Return',
#             debit_amount=voucher.grand_total_amount,
#             credit_amount=Decimal(0),
#             balance_amount=voucher.grand_total_amount
#         )    
            
    # Mirror logic for returns if you track them in AR/AP

# 8) The one high-level function your views call
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
            upsert_stock(
                item=item,
                batch_id=row.batch_id,
                base_unit_id=item.item_unit_id,
                base_qty_delta=base_qty,
                rate=row.rate,
                voucher_date=voucher.transaction_date,
                voucher_type=voucher.voucherType,
                voucher_id=voucher.id,
                cost_center=voucher.cost_center,
            )

            if create_detail:
                create_detail_for_kind(kind, voucher, row, item)

        # post_daybook_if_needed(kind, voucher)
        # post_outstanding_if_needed(kind, voucher)

    return voucher, rows


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
        voucher_no = sale.id
        cost_center = sale.cost_center
        fy = None  # future FK (optional)

        # ---------------------- DEBIT ENTRY ----------------------
        LedgerPosting.objects.create(
            date=transaction_date,
            VoucherType=voucher_type,
            VoucherNo=voucher_no,
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
                VoucherNo=voucher_no,
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
            VoucherNo=voucher_no,
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
                VoucherNo=voucher_no,
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
                VoucherNo=voucher_no,
                ledger=LedgerCreation.objects.get(id=13), # Freight Ledger
                debit=None,
                credit=sale.Freight,
                CostCenter=cost_center,
                FY=fy,
                IsDeleted=False
        )    
            
    except Exception as e:
        print(f"Error creating LedgerPosting for sale {sale.id}: {e}")
        
        
#LedgerPosting for Purchase
import traceback

def create_ledger_postings_for_purchase(purchase):
    try:
        print("DEBUG: Entered ledger posting function")

        print("DEBUG: Fetching Purchase voucher type...")
        voucher_type = Vouchers.objects.get(id=13)
        print("DEBUG: Voucher type found:", voucher_type)

        print("DEBUG: Creating Supplier Credit entry...")
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

        print("DEBUG: Checking discount...")
        if purchase.discount > 0:
            print("DEBUG: Fetching Discount Ledger (id=20)...")
            discount_ledger = LedgerCreation.objects.get(id=20)

            LedgerPosting.objects.create(
                date=purchase.transaction_date,
                VoucherType=voucher_type,
                VoucherNo=purchase.id,
                ledger=discount_ledger,
                debit=None,
                credit=purchase.discount,
                CostCenter=purchase.cost_center,
                FY=None,
                IsDeleted=False
            )

        print("DEBUG: Fetching Purchase Ledger (id=6)...")
        purchase_ledger = LedgerCreation.objects.get(id=6)

        LedgerPosting.objects.create(
            date=purchase.transaction_date,
            VoucherType=voucher_type,
            VoucherNo=purchase.id,
            ledger=purchase_ledger,
            debit=purchase.total_net_value,
            credit=None,
            CostCenter=purchase.cost_center,
            FY=None,
            IsDeleted=False
        )

        print("DEBUG: Checking Tax...")
        if purchase.total_tax_amount > 0:
            print("DEBUG: Fetching Tax Ledger (id=3)...")
            tax_ledger = LedgerCreation.objects.get(id=3)

            LedgerPosting.objects.create(
                date=purchase.transaction_date,
                VoucherType=voucher_type,
                VoucherNo=purchase.id,
                ledger=tax_ledger,
                debit=purchase.total_tax_amount,
                credit=None,
                CostCenter=purchase.cost_center,
                FY=None,
                IsDeleted=False
            )

        print("DEBUG: Ledger posting completed successfully")

    except Exception as e:
        print("ERROR OCCURRED:")
        traceback.print_exc()
        raise e