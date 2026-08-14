"""
Script to create missing voucher types required by the accounting modules.
Run with: python manage.py shell < create_voucher_types.py
Or: python create_voucher_types.py (as a standalone Django script)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts.settings')
django.setup()

from fleet_app.models import Vouchers
from django.db import connection

vouchers_to_create = [
    (7,  'Receipt',         'Receipt',          'REC-', 5, 1),
    (8,  'Payment',         'Payment',          'PAY-', 5, 1),
    (9,  'Contra',          'Contra',           'CON-', 5, 1),
    (10, 'Journal',         'Journal',          'JNL-', 5, 1),
    (11, 'Local Payment',   'Local Payment',    'LP-',  5, 1),
    (12, 'Opening Stock',   'Opening Stock',    'OS-',  5, 1),
    (13, 'Purchase',        'Purchase',         'PUR-', 5, 1),
    (14, 'Sales',           'Sales',            'SAL-', 5, 1),
    (15, 'Stock Transfer',  'Stock Transfer',   'STK-', 5, 1),
    (16, 'Debit Note',      'Debit Note',       'DBN-', 5, 1),
    (17, 'Purchase Return', 'Purchase Return',  'PRR-', 5, 1),
    (18, 'Sales Return',    'Sales Return',     'SRR-', 5, 1),
    (19, 'Bill Clearance',  'Bill Clearance',   'BC-',  5, 1),
]

table = Vouchers._meta.db_table

created = 0
skipped = 0
for vid, vtype, vname, prefix, minlen, startno in vouchers_to_create:
    if not Vouchers.objects.filter(id=vid).exists():
        with connection.cursor() as cursor:
            cursor.execute(
                f'INSERT INTO {table} (id, "VoucherType", "VoucherName", "Prefix", "Suffix", "MinLength", "StartingNo", "isDefault", created_on, updated_on) VALUES (%s, %s, %s, %s, NULL, %s, %s, false, NOW(), NOW())',
                [vid, vtype, vname, prefix, minlen, startno]
            )
        created += 1
        print(f'  Created: ID={vid} {vname}')
    else:
        existing = Vouchers.objects.get(id=vid)
        skipped += 1
        print(f'  Skipped: ID={vid} already exists as "{existing.VoucherName}"')

print(f'\nDone. Created={created}, Skipped={skipped}')
print('\nAll voucher types now:')
for v in Vouchers.objects.all().order_by('id'):
    print(f'  ID={v.id}: {v.VoucherName} (prefix={v.Prefix})')
