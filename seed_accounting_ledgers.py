"""
Seed script: creates the essential accounting ledgers and voucher types
required by the purchase/sales voucher system.

Run with:  python seed_accounting_ledgers.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts.settings')
django.setup()

from accounts_app.models import LedgerCreation, Groups
from item_master.models import Vouchers, CostCenter


# ── 1. Ensure required Groups exist ──────────────────────────────────────────
REQUIRED_GROUPS = [
    {"id": 6,  "groupName": "Purchase Account"},
    {"id": 7,  "groupName": "Direct Expenses"},
    {"id": 8,  "groupName": "Indirect Expenses"},
    {"id": 9,  "groupName": "Sales Account"},
    {"id": 10, "groupName": "Direct Income"},
]

for gdata in REQUIRED_GROUPS:
    obj, created = Groups.objects.get_or_create(
        id=gdata["id"],
        defaults={"groupName": gdata["groupName"]}
    )
    status = "[CREATED]" if created else "[EXISTS] "
    print(f"  {status} Group: {obj.groupName} (id={obj.id})")


# ── 2. Ensure essential LedgerCreation records exist ─────────────────────────
purchase_group  = Groups.objects.get(id=6)   # Purchase Account
expenses_group  = Groups.objects.get(id=7)   # Direct Expenses
sales_group     = Groups.objects.get(id=9)   # Sales Account
income_group    = Groups.objects.get(id=10)  # Direct Income

REQUIRED_LEDGERS = [
    {
        "ledger_name": "Purchase Account",
        "groups":      purchase_group,
        "isDefault":   True,
    },
    {
        "ledger_name": "Input Tax",
        "groups":      expenses_group,
        "isDefault":   True,
    },
    {
        "ledger_name": "Discount Received",
        "groups":      income_group,
        "isDefault":   True,
    },
    {
        "ledger_name": "Sales Account",
        "groups":      sales_group,
        "isDefault":   True,
    },
    {
        "ledger_name": "Output Tax",
        "groups":      income_group,
        "isDefault":   True,
    },
    {
        "ledger_name": "Discount Allowed",
        "groups":      expenses_group,
        "isDefault":   True,
    },
]

for ldata in REQUIRED_LEDGERS:
    obj, created = LedgerCreation.objects.get_or_create(
        ledger_name=ldata["ledger_name"],
        defaults={
            "groups":    ldata["groups"],
            "isDefault": ldata["isDefault"],
        }
    )
    status = "[CREATED]" if created else "[EXISTS] "
    print(f"  {status} Ledger: {obj.ledger_name} (id={obj.id})")


# ── 3. Ensure required Voucher Types exist ────────────────────────────────────
REQUIRED_VOUCHERS = [
    {"VoucherType": "Purchase",         "VoucherName": "Purchase",         "Prefix": "PUR", "MinLength": 5, "StartingNo": 1},
    {"VoucherType": "Sales",            "VoucherName": "Sales",            "Prefix": "SAL", "MinLength": 5, "StartingNo": 1},
    {"VoucherType": "Purchase Return",  "VoucherName": "Purchase Return",  "Prefix": "PRN", "MinLength": 5, "StartingNo": 1},
    {"VoucherType": "Sales Return",     "VoucherName": "Sales Return",     "Prefix": "SRN", "MinLength": 5, "StartingNo": 1},
]

for vdata in REQUIRED_VOUCHERS:
    obj, created = Vouchers.objects.get_or_create(
        VoucherType=vdata["VoucherType"],
        defaults={
            "VoucherName": vdata["VoucherName"],
            "Prefix":      vdata["Prefix"],
            "MinLength":   vdata["MinLength"],
            "StartingNo":  vdata["StartingNo"],
            "isDefault":   True,
        }
    )
    status = "[CREATED]" if created else "[EXISTS] "
    print(f"  {status} Voucher Type: {obj.VoucherType} (id={obj.id})")

print()
print("=== All Ledgers now ===")
for l in LedgerCreation.objects.all().order_by('id'):
    print(f"  id={l.id:<4}  name={l.ledger_name!r}  group={l.groups}")
print()
print("=== All Voucher Types now ===")
for v in Vouchers.objects.all().order_by('id'):
    print(f"  id={v.id:<4}  type={v.VoucherType!r}")
