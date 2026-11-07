from accounts_app.models import PaymentBillMaster
from django.db.models import Sum
from accounts_app.models import LedgerCreation
from django.db.models import Q
from accounts_app.models import ReceiptBillDetails
from jobcard_app.models import Invoice
from accounts_app.models import BillWiseOpening
from decimal import Decimal
from accounts_app.models import ReceiptBillMaster
from .models import UserPrivilege, Menu
from django.contrib.auth import authenticate
from django.http import JsonResponse

from datetime import date


def check_privilege(user, menu_ids, privilege_fields):
    """
    Check if the logged-in user's role has the given privileges 
    for one or more menus.

    Example:
        check_privilege(user, [1, 2], ["can_read", "can_write"])
    """
    if not user.is_authenticated:
        return False

    # ✅ Superuser always has all privileges
    if getattr(user, "is_superuser", False):
        return True

    role = getattr(user, "user_role", None)
    if not role:
        return False

    # Ensure we always work with lists
    if isinstance(menu_ids, int):
        menu_ids = [menu_ids]
    if isinstance(privilege_fields, str):
        privilege_fields = [privilege_fields]

    # Fetch all privileges for this role and menus in one query
    privileges = UserPrivilege.objects.filter(user_role=role, menu_id__in=menu_ids)

    if not privileges.exists():
        return False

    # Check if ANY privilege matches
    for privilege in privileges:
        for field in privilege_fields:
            if getattr(privilege, field, False):
                return True  # ✅ user has at least one of the privileges

    return False  # ❌ none matched

# def check_admin_override(request):
#     """
#     Checks admin username & password sent in POST
#     """
#     admin_username = request.POST.get("admin_username")
#     admin_password = request.POST.get("admin_password")

#     if not admin_username or not admin_password:
#         return False, "Admin credentials required"

#     admin_user = authenticate(
#         request,
#         username=admin_username,
#         password=admin_password
#     )

#     if not admin_user:
#         return False, "Invalid admin credentials"

#     if not getattr(admin_user.user_role, "is_admin", False):
#         return False, "User is not an admin"

#     return True, admin_user




def check_admin_override(request):
    """
    Allows override by:
    - Django superuser
    - Custom admin role (user_role.is_admin)
    """

    admin_username = request.POST.get("admin_username")
    admin_password = request.POST.get("admin_password")

    if not admin_username or not admin_password:
        return False, "Admin credentials required"

    admin_user = authenticate(
        request,
        username=admin_username,
        password=admin_password
    )

    if not admin_user:
        return False, "Invalid admin credentials"

    # ✅ ALLOW DJANGO SUPERUSER
    if admin_user.is_superuser:
        return True, admin_user

    # ✅ ALLOW CUSTOM ADMIN ROLE
    if getattr(admin_user.user_role, "is_admin", False):
        return True, admin_user

    return False, "User is not authorized as admin"



CLEARANCE_TYPE_OPENING = 16

# BillWiseOpening's own voucherType — a bill can be either kind.
OPENING_BILL_VOUCHER_TYPES = [2]
CLEARANCE_TYPE_INVOICE = 2

def build_customer_outstanding_data(cid, from_date=None, to_date=None):
    """
    Builds one customer's outstanding data (bill_rows, totals, receipts).
    Shared by the report view and the per-client PDF so numbers always match.
    """
    cust = LedgerCreation.objects.get(pk=cid)

    data = {
        'customer': cust,
        'bill_rows': [],
        'total_debit': Decimal('0'),
        'total_credit': Decimal('0'),
        'total_outstanding': Decimal('0'),
        'final_cumulative': Decimal('0'),
        'total_invoice': Decimal('0'),
        'total_opening': Decimal('0'),
        'receipt_rows': [],
        'total_paid': Decimal('0'),
    }

    # ---------------------------------------------------
    # CREDIT LOOKUP
    # ---------------------------------------------------
    qs = ReceiptBillDetails.objects.filter(
        BillMaster__Customer_id=cid
    ).filter(
        Q(BillMaster__IsPDC=False) | Q(BillMaster__ChequeStatus='cleared')
    )

    if from_date:
        qs = qs.filter(BillMaster__Date__gte=from_date)
    if to_date:
        qs = qs.filter(BillMaster__Date__lte=to_date)

    totals = qs.values('VoucherNo', 'voucherType_id').annotate(credited=Sum('Amount'))
    credit_map = {
        (row['VoucherNo'], row['voucherType_id']): (row['credited'] or Decimal('0'))
        for row in totals
    }

    # ---------------------------------------------------
    # INVOICES
    # ---------------------------------------------------
    invoices = Invoice.objects.filter(
        payment_mode='Credit',
        customer_id=cid
    ).select_related('customer', 'voucherType')

    if from_date:
        invoices = invoices.filter(date__gte=from_date)
    if to_date:
        invoices = invoices.filter(date__lte=to_date)

    for invoice in invoices:
        debit_amt = invoice.grand_total
        credit_amt = credit_map.get((invoice.pk, CLEARANCE_TYPE_INVOICE), Decimal('0'))
        outstanding_amt = debit_amt - credit_amt

        data['bill_rows'].append({
            'source': invoice,
            'bill_type': 'invoice',
            'date': invoice.date,
            'number': invoice.voucher_no,
            'po_no': invoice.buyer_order_no,
            'debit_amt': debit_amt,
            'credit_amt': credit_amt,
            'outstanding_amt': outstanding_amt,
            'is_cleared': invoice.IsCleared,
        })
        data['total_invoice'] += debit_amt

    # ---------------------------------------------------
    # OPENING BILLS
    # ---------------------------------------------------
    opening_bills = BillWiseOpening.objects.filter(
        ledger_id=cid,
        voucherType_id__in=OPENING_BILL_VOUCHER_TYPES,
        IsCleared=False
    )

    if from_date:
        opening_bills = opening_bills.filter(InvDate__gte=from_date)
    if to_date:
        opening_bills = opening_bills.filter(InvDate__lte=to_date)

    for opening in opening_bills:
        debit_amt = opening.InvAmount
        credit_amt = opening.InvAmount - opening.InvBalance
        outstanding_amt = opening.InvBalance

        data['bill_rows'].append({
            'source': opening,
            'bill_type': 'opening',
            'date': opening.InvDate,
            'number': opening.InvNo,
            'po_no': opening.po_no,
            'debit_amt': debit_amt,
            'credit_amt': credit_amt,
            'outstanding_amt': outstanding_amt,
            'is_cleared': outstanding_amt <= Decimal('0.001'),
        })
        data['total_opening'] += debit_amt

    # ---------------------------------------------------
    # MERGE — sort + cumulative
    # ---------------------------------------------------
    data['bill_rows'].sort(key=lambda r: r['date'])

    today = to_date if to_date else date.today()

    # Convert string to date if needed
    if isinstance(today, str):
        from datetime import datetime
        today = datetime.strptime(today, "%Y-%m-%d").date()

    cumulative = Decimal('0')
    for row in data['bill_rows']:
        row['age'] = max((today - row['date']).days, 0) if row['date'] else 0
        cumulative += row['outstanding_amt']
        row['cumulative_amt'] = cumulative

        data['total_debit'] += row['debit_amt']
        data['total_credit'] += row['credit_amt']
        data['total_outstanding'] += row['outstanding_amt']

    data['final_cumulative'] = cumulative

    # ---------------------------------------------------
    # RECEIPTS
    # ---------------------------------------------------
    receipt_masters = ReceiptBillMaster.objects.filter(Customer_id=cid).order_by('Date')

    if from_date:
        receipt_masters = receipt_masters.filter(Date__gte=from_date)
    if to_date:
        receipt_masters = receipt_masters.filter(Date__lte=to_date)

    for master in receipt_masters:
        if master.IsPDC and master.ChequeStatus != 'cleared':
            continue
        data['receipt_rows'].append(master)
        data['total_paid'] += master.TotalAmount

    data['balance'] = data['total_outstanding']
    return data

def build_customer_pdc_list(customer_id, opening_balance):
    """
    PDC list for a single customer, grouped by receipt voucher_no
    (so a cheque split across multiple bills shows as one PDC row),
    ordered by maturity (ChequeDate), with a running balance that
    starts at the customer's current outstanding and reduces as
    each PDC matures.
    """
    lines = (
        ReceiptBillMaster.objects
        .filter(Customer_id=customer_id, IsPDC=True)
        .exclude(ChequeStatus__in=['cancelled', 'cleared'])  # drop cancelled cheques
        .order_by('ChequeDate', 'voucher_no')
    )

    grouped, order = {}, []
    for ln in lines:
        key = ln.voucher_no
        if key not in grouped:
            grouped[key] = {
                'voucher_no': ln.voucher_no,
                'cheque_no': ln.ChequeNo,
                'cheque_date': ln.ChequeDate,
                'date': ln.Date,
                'debit': Decimal('0'),
                'credit': Decimal('0'),
                'remarks': [],
            }
            order.append(key)
        grouped[key]['credit'] += ln.TotalAmount or 0
        if ln.Remark:
            grouped[key]['remarks'].append(ln.Remark)

    pdc_rows = [grouped[k] for k in order]
    pdc_rows.sort(key=lambda r: (r['cheque_date'] or r['date']))

    running = opening_balance
    for i, row in enumerate(pdc_rows, start=1):
        running -= row['credit']
        row['sl_no'] = i
        row['balance'] = running
        row['remark'] = '/'.join(row['remarks']) if row['remarks'] else '-'

    pdc_grand_credit = sum(r['credit'] for r in pdc_rows)
    return pdc_rows, pdc_grand_credit


def build_supplier_pdc_list(supplier_id, opening_balance):
    """
    PDC list for a single supplier (payable side), grouped by payment
    voucher_no, ordered by maturity (ChequeDate), with a running balance
    that starts at opening_balance (Cr, negative) and moves toward zero
    as each PDC matures — each PDC amount is a DEBIT against the
    supplier's payable ledger.
    """
    lines = (
        PaymentBillMaster.objects
        .filter(Supplier_id=supplier_id, IsPDC=True)
        .exclude(ChequeStatus__in=['cancelled', 'cleared'])
        .order_by('ChequeDate', 'voucher_no')
    )

    grouped, order = {}, []
    for ln in lines:
        key = ln.voucher_no
        if key not in grouped:
            grouped[key] = {
                'voucher_no': ln.voucher_no,
                'cheque_no': ln.ChequeNo,
                'cheque_date': ln.ChequeDate,
                'date': ln.Date,
                'debit': Decimal('0'),
                'credit': Decimal('0'),
                'remarks': [],
            }
            order.append(key)
        grouped[key]['debit'] += ln.TotalAmount or 0
        if ln.Remark:
            grouped[key]['remarks'].append(ln.Remark)

    pdc_rows = [grouped[k] for k in order]
    pdc_rows.sort(key=lambda r: (r['cheque_date'] or r['date']))

    running = opening_balance
    for i, row in enumerate(pdc_rows, start=1):
        running -= row['debit']
        row['sl_no'] = i
        row['balance'] = running
        row['remark'] = '/'.join(row['remarks']) if row['remarks'] else '-'

    pdc_grand_debit = sum(r['debit'] for r in pdc_rows)
    return pdc_rows, pdc_grand_debit