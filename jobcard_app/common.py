from decimal import Decimal
from django.db import transaction
from decimal import Decimal
from accounts_app.models import UserPrivilege

from accounts_app.models import LedgerCreation, LedgerPosting
from fleet_app.models import Vouchers

class PostingError(Exception):
    pass

def create_ledger_postings_for_invoice(invoice):
    """
    Create workshop invoice double-entry ledger postings.

    Debit:
        Customer / Cash / Bank = Grand Total
        Discount               = Discount amount (if > 0)

    Credit:
        Spare Parts            = Parts subtotal (if > 0)
        Labour Charges         = Labour subtotal (if > 0)
        Other Charge Income    = Other subtotal (if > 0)
        Tax                    = Total tax (if > 0)

    Only creates a posting when its amount is greater than zero.
    """

    try:
        # ---------------------------------------------------------
        # 1. Voucher Type
        # ---------------------------------------------------------
        voucher_type = (
            getattr(invoice, 'voucherType', None)
            or Vouchers.objects.filter(pk=2).first()
            or Vouchers.objects.filter(
                VoucherType__icontains='Invoice'
            ).first()
        )

        if not voucher_type:
            raise Exception("Invoice voucher type not found.")

        # ---------------------------------------------------------
        # 2. Delete old postings first
        # ---------------------------------------------------------
        delete_ledger_postings_for_invoice(invoice)

        # ---------------------------------------------------------
        # 3. Calculate invoice amounts
        # ---------------------------------------------------------
        parts_amount = Decimal(str(
            invoice.get_parts_subtotal() or 0
        ))

        labour_amount = Decimal(str(
            invoice.get_labour_subtotal() or 0
        ))

        other_amount = Decimal(str(
            invoice.get_other_subtotal() or 0
        ))

        tax_amount = Decimal(str(
            invoice.get_total_tax() or 0
        ))

        discount_amount = Decimal(str(
            invoice.get_discount_amount() or 0
        ))

        grand_total = Decimal(str(
            invoice.get_grand_total() or 0
        ))

        # ---------------------------------------------------------
        # 4. Don't post zero/negative invoice
        # ---------------------------------------------------------
        if grand_total <= 0:
            return

        # ---------------------------------------------------------
        # 5. Get ledgers
        # ---------------------------------------------------------

        # Customer ledger
        customer_ledger = invoice.customer

        # Spare Parts / Sales
        spare_parts_ledger = LedgerCreation.objects.filter(
            pk=1002
        ).first()

        # Labour
        labour_ledger = LedgerCreation.objects.filter(
            pk=1001
        ).first()

        # Other Charge Income
        other_charge_ledger = LedgerCreation.objects.filter(
            pk=1003
        ).first()

        # Tax
        tax_ledger = LedgerCreation.objects.filter(
            pk=2
        ).first()

        # Discount
        discount_ledger = LedgerCreation.objects.filter(
            pk=19
        ).first()

        # ---------------------------------------------------------
        # 6. Validate required ledgers
        # ---------------------------------------------------------
        if not customer_ledger:
            raise Exception(
                f"Customer ledger not found for Invoice #{invoice.id}"
            )

        if parts_amount > 0 and not spare_parts_ledger:
            raise Exception(
                "Spare Parts ledger not found."
            )

        if labour_amount > 0 and not labour_ledger:
            raise Exception(
                "Labour Charges ledger not found."
            )

        if other_amount > 0 and not other_charge_ledger:
            raise Exception(
                "Other Charge Income ledger not found."
            )

        if tax_amount > 0 and not tax_ledger:
            raise Exception(
                "Tax ledger not found."
            )

        if discount_amount > 0 and not discount_ledger:
            raise Exception(
                "Discount ledger not found."
            )

        # ---------------------------------------------------------
        # 7. Helper function
        # ---------------------------------------------------------
        def add_debit(ledger, amount):
            if amount > 0:
                LedgerPosting.objects.create(
                    date=invoice.invoice_date,
                    VoucherType=voucher_type,
                    VoucherNo=invoice.id,
                    ledger=ledger,
                    debit=amount,
                    credit=None,
                    created_by=invoice.created_by
                )

        def add_credit(ledger, amount):
            if amount > 0:
                LedgerPosting.objects.create(
                    date=invoice.invoice_date,
                    VoucherType=voucher_type,
                    VoucherNo=invoice.id,
                    ledger=ledger,
                    debit=None,
                    credit=amount,
                    created_by=invoice.created_by
                )

        # ---------------------------------------------------------
        # 8. DEBIT - Customer
        # ---------------------------------------------------------
        add_debit(
            customer_ledger,
            grand_total
        )

        # ---------------------------------------------------------
        # 9. DEBIT - Discount
        # ---------------------------------------------------------
        add_debit(
            discount_ledger,
            discount_amount
        )

        # ---------------------------------------------------------
        # 10. CREDIT - Spare Parts
        # ---------------------------------------------------------
        add_credit(
            spare_parts_ledger,
            parts_amount
        )

        # ---------------------------------------------------------
        # 11. CREDIT - Labour
        # ---------------------------------------------------------
        add_credit(
            labour_ledger,
            labour_amount
        )

        # ---------------------------------------------------------
        # 12. CREDIT - Other Charges
        # ---------------------------------------------------------
        add_credit(
            other_charge_ledger,
            other_amount
        )

        # ---------------------------------------------------------
        # 13. CREDIT - Tax
        # ---------------------------------------------------------
        add_credit(
            tax_ledger,
            tax_amount
        )

        print(
            f"✅ Invoice #{invoice.id} ledger postings created."
        )

        print(
            f"   DR Customer: {grand_total}"
        )
        print(
            f"   DR Discount: {discount_amount}"
        )
        print(
            f"   CR Parts: {parts_amount}"
        )
        print(
            f"   CR Labour: {labour_amount}"
        )
        print(
            f"   CR Other: {other_amount}"
        )
        print(
            f"   CR Tax: {tax_amount}"
        )

    except Exception as e:
        print(
            f"❌ Invoice #{invoice.id} ledger posting failed: {e}"
        )
        raise

def delete_ledger_postings_for_invoice(invoice):
    """
    Delete all existing LedgerPosting records for a workshop invoice.

    Used before recreating invoice ledger postings, especially when
    editing an existing invoice.
    """
    try:
        from accounts_app.models import LedgerPosting
        from fleet_app.models import Vouchers

        voucher_type = (
            getattr(invoice, 'voucherType', None)
            or Vouchers.objects.filter(pk=2).first()
            or Vouchers.objects.filter(
                VoucherType__icontains='Invoice'
            ).first()
        )

        if not voucher_type:
            print(
                f"⚠️ Invoice #{invoice.id}: "
                "Invoice voucher type not found."
            )
            return

        deleted_count, deleted_details = LedgerPosting.objects.filter(
            VoucherNo=invoice.id,
            VoucherType=voucher_type
        ).delete()

        print(
            f"✅ Deleted {deleted_count} existing ledger posting(s) "
            f"for Invoice #{invoice.id}"
        )

    except Exception as e:
        print(
            f"❌ Failed to delete ledger postings "
            f"for Invoice #{invoice.id}: {e}"
        )
        raise

