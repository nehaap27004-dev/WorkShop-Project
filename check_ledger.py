import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'accounts.settings')
django.setup()

from item_master.forms import PurchaseVoucherForm

# Simulate exact POST - with VendorInvNo showing 00001 (from screenshot)
# This is what the browser POSTs
post_data = {
    'voucher_no': '',         # readonly - might be empty from POST
    'auto_no': '',            # auto - might be empty
    'transaction_date': '2026-08-14',
    'payment_mode': 'Cash',
    'ledger': '22',
    'cost_center': '1',
    'total_net_value': '0.0',
    'total_tax_amount': '0.0',
    'discount': '0.0',
    'grand_total_amount': '0.0',
    'Freight': '0.0',
    'VendorInvNo': '00001',
    'InvoiceDate': '2026-08-14',
    'voucherType': '13',
}

form = PurchaseVoucherForm(post_data)
print("Form valid:", form.is_valid())
print("Errors:", form.errors)

# Also test with ledger = '' (empty - if dropdown had no selection)
print()
print("--- Test with empty ledger ---")
post_data2 = dict(post_data)
post_data2['ledger'] = ''
form2 = PurchaseVoucherForm(post_data2)
print("Form valid:", form2.is_valid())
print("Errors:", form2.errors)
