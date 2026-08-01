# fleet_app/common.py
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from reportlab.lib.units import cm
from reportlab.lib.units import inch
import os
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import os
from decimal import Decimal
from accounts_app.models import BillClearance, Groups, LedgerCreation, LedgerPosting , PaymentMaster
from fleet_app.models import Vouchers, VehicleProfitLoss, Vehicle
from django.db import transaction
from datetime import datetime, date
from django.conf import settings



def draw_header(canvas, doc, logo_path=None):
    """Draws header logo only on the first page."""
    if canvas.getPageNumber() != 1:
        return

    canvas.saveState()
    if logo_path and os.path.exists(logo_path):
        page_width, page_height = A4
        header_height = 100
        try:
            canvas.drawImage(
                logo_path,
                0,
                page_height - header_height,
                width=page_width,
                height=header_height,
                preserveAspectRatio=False,
                mask='auto'
            )
        except Exception as e:
            print(f"Header image load failed: {e}")
    canvas.restoreState()


def draw_footer(canvas, doc, footer_func=None, footer_image_path=None, only_last_page=False, doc_type="timesheet"):
    """
    Draws:
      - Footer image on all pages
      - 'Computer Generated <doc_type>' text only on last page
      - footer_func (signatures/totals) only on last page if provided
    """
    canvas.saveState()
    page_num = canvas.getPageNumber()
    total_pages = getattr(doc, "_page_count", None)

    # === Footer image (all pages) ===
    if footer_image_path and os.path.exists(footer_image_path):
        try:
            footer_height = 1.2 * inch
            footer_width = A4[0]
            canvas.drawImage(
                footer_image_path,
                0, 0,
                width=footer_width,
                height=footer_height,
                preserveAspectRatio=True,
                mask='auto'
            )
        except Exception as e:
            print(f"Footer image load failed: {e}")

    # === Only on last page ===
    is_last_page = (total_pages is not None and page_num == total_pages)
    if is_last_page:
        # Determine message by document type
        if doc_type.lower() == "invoice":
            message = "This is a Computer Generated Invoice"
        elif doc_type.lower() == "quotation":
            message = "This is a Computer Generated Quotation"
        elif doc_type.lower() == "delivery_contract":
            message = "This is a Computer Generated Delivery Contract"   
        elif doc_type.lower() == "purchase_order":
            message = "This is a Computer Generated Purchase Order"   
        else:
            message = "This is a Computer Generated Timesheet"

        # Draw message above footer image
        canvas.setFont("Helvetica-Oblique", 9)
        canvas.setFillColorRGB(0.25, 0.25, 0.25)
        canvas.drawCentredString(A4[0] / 2, 1.3 * inch, message)

        # Draw additional custom footer (like signatures/totals)
        if footer_func:
            canvas.saveState()
            canvas.translate(0, 1.3 * inch)
            footer_func(canvas, doc)
            canvas.restoreState()

    canvas.restoreState()


import copy

def build_pdf(
    filename,
    story,
    logo_path=None,
    include_header=True,
    include_footer=True,
    footer_func=None,
    footer_on_last_page=False,
    footer_image_path=None,
    doc_type="timesheet",
):
    # === Step 1: Pre-pass to count total pages ===
    doc = BaseDocTemplate(filename, pagesize=A4)

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin + 1.5 * cm,
        doc.width,
        doc.height - 3 * cm,
        id="normal",
    )

    class PageCounterCanvas:
        def __init__(self):
            self.page_count = 0

        def __call__(self, canvas, doc):
            self.page_count += 1

    counter = PageCounterCanvas()
    doc.addPageTemplates([PageTemplate(id="count", frames=frame, onPage=counter)])

    # ✅ Deep copy so pre-pass doesn't corrupt the original story objects
    doc.build(copy.deepcopy(story))
    total_pages = counter.page_count

    # === Step 2: Actual PDF generation ===
    doc = BaseDocTemplate(filename, pagesize=A4)
    doc._page_count = total_pages

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin + 1.5 * cm,
        doc.width,
        doc.height - 3 * cm,
        id="normal",
    )

    def on_page(canvas, doc):
        if include_header and logo_path and canvas.getPageNumber() == 1:
            draw_header(canvas, doc, logo_path)

        if include_footer:
            draw_footer(
                canvas,
                doc,
                footer_func=footer_func,
                only_last_page=footer_on_last_page,
                footer_image_path=footer_image_path,
                doc_type=doc_type,
            )

    template = PageTemplate(id="main", frames=frame, onPage=on_page)
    doc.addPageTemplates([template])
    doc.build(story)  # ✅ Original story, untouched

    return filename



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
    
def create_ledger_postings_for_invoice(invoice):
    try:
        # ✅ Ensure we have a proper Vouchers instance
        voucher_type = Vouchers.objects.get(pk=2)

        # ✅ Ledger for invoice posting (fixed one)
        invoice_ledger = LedgerCreation.objects.get(pk=1002)
        # selected Cash and Bank Ledger
        ledger = invoice.ledger

        # --- Debit Entry (Customer Ledger)
        LedgerPosting.objects.create(
            date=invoice.date,
            VoucherType=voucher_type,  # must be instance, not string
            VoucherNo=invoice.id,
            ledger=ledger,
            debit=invoice.grand_total,
            credit=None,
        )

        # --- Credit Entry (Invoice Ledger)
        LedgerPosting.objects.create(
            date=invoice.date,
            VoucherType=voucher_type,
            VoucherNo=invoice.id,
            ledger=invoice_ledger,
            debit=None,
            credit=invoice.grand_total,
        )

        print(f"Ledger postings created for Invoice #{invoice.id}")

    except Vouchers.DoesNotExist:
        print("❌ VoucherType with ID 2 not found.")
    except LedgerCreation.DoesNotExist:
        print("LedgerCreation with ID 1001 (Invoice Ledger) not found.")
    except Exception as e:
        print(f" Ledger posting failed for Invoice #{invoice.id}: {e}")
        
        
def create_ledger_postings_for_hire(fleet_hire):
    
    try:
        # ✅ Voucher type for Hire
        voucher_type = Vouchers.objects.get(pk=1)

        # ✅ LedgerCreation id=1001 (Hire Ledger)
        hire_ledger = LedgerCreation.objects.get(pk=1001)

        ledger = fleet_hire.ledger

        # ✅ Supplier Ledger from hire
        supplier_ledger = fleet_hire.supplier
        
         # --- Credit Entry (Supplier Ledger)
        LedgerPosting.objects.create(
            date=fleet_hire.date,
            VoucherType=voucher_type,
            VoucherNo=fleet_hire.id,
            ledger=ledger,
            debit=None,
            credit=fleet_hire.grand_total,
        )

        # --- Debit Entry (Hire Ledger)
        LedgerPosting.objects.create(
            date=fleet_hire.date,
            VoucherType=voucher_type,
            VoucherNo=fleet_hire.id,
            ledger=hire_ledger,
            debit=fleet_hire.grand_total,
            credit=None,
        )


        print(f" Ledger postings created for Hire #{fleet_hire.id}")

    except Vouchers.DoesNotExist:
        print(" VoucherType with ID 1 (Hire) not found.")
    except LedgerCreation.DoesNotExist:
        print("LedgerCreation with ID 1001 (Hire Ledger) not found.")
    except Exception as e:
        print(f" Ledger posting failed for Hire #{fleet_hire.id}: {e}")       

      

def create_ledger_postings_for_receiptbillclr(receipt_master):
    """
    Creates LedgerPosting entries for a Receipt Bill Clearance.

    🔹 VoucherType ID = 5 (Receipt Bill Clearance)
    🔹 Debit: Customer Ledger
    🔹 Credit: Receipt Bill Clearance Ledger (LedgerCreation ID = 1003)
    """
    try:
        # Ensure we have the correct voucher type
        voucher_type = Vouchers.objects.get(pk=5)

        # Fixed Ledger for Receipt Bill Clearance
        # receipt_clearance_ledger = LedgerCreation.objects.get(pk=1006)

        # Customer Ledger (selected in the receipt bill form)
        ledger = receipt_master.Ledger
        customer_ledger = receipt_master.Customer

        # ✅ Debit Entry (Customer Ledger)
        LedgerPosting.objects.create(
            date=receipt_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_master.id,
            ledger=ledger,
            debit=receipt_master.TotalAmount or Decimal('0.00'),
            credit=Decimal('0.00'),
        )

        # ✅ Credit Entry (Receipt Bill Clearance Ledger)
        LedgerPosting.objects.create(
            date=receipt_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_master.id,
            ledger=customer_ledger,
            debit=Decimal('0.00'),
            credit=receipt_master.TotalAmount or Decimal('0.00'),
        )

        print(f"Ledger postings created for Receipt Bill Clearance #{receipt_master.id}")

    except Vouchers.DoesNotExist:
        print("VoucherType with ID 5 not found.")
    except LedgerCreation.DoesNotExist:
        print("LedgerCreation with ID 1002 (Receipt Bill Clearance Ledger) not found.")
    except Exception as e:
        print(f"Ledger posting failed for Receipt Bill Clearance #{receipt_master.id}: {e}")

def delete_ledger_postings_for_receiptbillclr(receipt_master):
    """
    Delete LedgerPosting entries for Receipt Bill Clearance.
    """

    try:
        voucher_type = Vouchers.objects.get(pk=5)

        deleted_count, _ = LedgerPosting.objects.filter(
            VoucherType=voucher_type,
            VoucherNo=receipt_master.id
        ).delete()

        print(f"🗑️ Deleted {deleted_count} ledger posting(s) for Receipt Bill Clearance #{receipt_master.id}")

    except Vouchers.DoesNotExist:
        print("❌ VoucherType with ID 5 not found.")
    except Exception as e:
        print(f"❌ Failed to delete ledger postings for Receipt Bill Clearance #{receipt_master.id}: {e}")        
        
def create_ledger_postings_for_paymentbillclr(payment_master):
    """
    Creates LedgerPosting entries for a payment Bill Clearance.

    🔹 VoucherType ID = 6 (payment Bill Clearance)
    🔹 Debit: Customer Ledger
    🔹 Credit: payment Bill Clearance Ledger (LedgerCreation ID = 1004)
    """
    try:
        # Ensure we have the correct voucher type
        voucher_type = Vouchers.objects.get(pk=6)

        # Fixed Ledger for payment Bill Clearance
        receipt_clearance_ledger = LedgerCreation.objects.get(pk=1007)

        # Customer Ledger (selected in the payment bill form)
        supplier_ledger = payment_master.Supplier
        ledger = payment_master.Ledger

        # ✅ Credit Entry (Supplier Ledger)
        LedgerPosting.objects.create(
            date=payment_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_master.id,
            ledger=ledger,
            debit= None,
            credit=payment_master.TotalAmount or Decimal('0.00'),
        )

        # ✅ Debit Entry (payment Bill Clearance Ledger)
        LedgerPosting.objects.create(
            date=payment_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_master.id,
            ledger=supplier_ledger,
            debit=payment_master.TotalAmount or Decimal('0.00'),
            credit= None,
        )

        print(f"Ledger postings created for payment Bill Clearance #{payment_master.id}")

    except Vouchers.DoesNotExist:
        print("VoucherType with ID 5 not found.")
    except LedgerCreation.DoesNotExist:
        print("LedgerCreation with ID 1002 (payment Bill Clearance Ledger) not found.")
    except Exception as e:
        print(f"Ledger posting failed for payment Bill Clearance #{payment_master.id}: {e}")        

def delete_ledger_postings_for_paymentbillclr(payment_master):
    """
    Delete LedgerPosting entries for Payment Bill Clearance.
    """

    try:
        voucher_type = Vouchers.objects.get(pk=6)

        deleted_count, _ = LedgerPosting.objects.filter(
            VoucherType=voucher_type,
            VoucherNo=payment_master.id
        ).delete()

        print(f"🗑️ Deleted {deleted_count} ledger posting(s) for Payment Bill Clearance #{payment_master.id}")

    except Vouchers.DoesNotExist:
        print("❌ VoucherType with ID 6 not found.")
    except Exception as e:
        print(f"❌ Failed to delete ledger postings for Payment Bill Clearance #{payment_master.id}: {e}")

def create_ledger_postings_for_payment(payment_master):
    """
    Create LedgerPosting entries for Payment Voucher.
    
    Rules:
    - VoucherType ID = 3
    - MASTER ENTRY:
        credit PaymentMaster.Ledger with total amount
    - DETAIL ENTRIES:
        for each PaymentDetails -> debit detail ledger by its amount
    """

    try:
        voucher_type = Vouchers.objects.get(pk=3)

        # -------- MASTER CREDIT ENTRY --------
        LedgerPosting.objects.create(
            date=payment_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_master.id,          # <-- Master VoucherNo
            ledger=payment_master.Ledger,         # <-- Ledger selected in PaymentMaster
            debit=None,
            credit=payment_master.TotalAmount or Decimal('0.00'),
            
        )

        # -------- DETAIL DEBIT ENTRIES --------
        for det in payment_master.details.all():
            LedgerPosting.objects.create(
                date=payment_master.Date,
                VoucherType=voucher_type,
                VoucherNo=det.id,                 # <-- detail row voucher ref
                ledger=det.Ledger,                # <-- ledger from PaymentDetails
                debit=det.Amount or Decimal('0.00'),
                credit=None,
                
            )

        print(f" Ledger postings created for Payment #{payment_master.id}")

    except Exception as e:
        print(f"❌ Ledger posting failed for Payment #{payment_master.id}: {e}")
        
def create_ledger_postings_for_receipt(receipt_master):
    """
    Creates ledger postings for a Receipt voucher
    """
    try:
        voucher_type = Vouchers.objects.get(pk=4)  # Receipt

        # 🔹 MASTER ENTRY (Cash / Bank - Debit)
        LedgerPosting.objects.create(
            date=receipt_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_master.id,     # ✅ ALWAYS master id
            ledger=receipt_master.Ledger,
            debit=receipt_master.TotalAmount or Decimal("0.00"),
            credit=None,
        )

        # 🔹 DETAIL ENTRIES (Income / Expense - Credit)
        for det in receipt_master.details.all():
            LedgerPosting.objects.create(
                date=receipt_master.Date,
                VoucherType=voucher_type,
                VoucherNo=receipt_master.id,  # ✅ SAME VoucherNo
                ledger=det.Ledger,
                debit=None,
                credit=det.Amount or Decimal("0.00"),
            )

        print(f"✅ Ledger postings created for Receipt #{receipt_master.id}")

    except Exception as e:
        print(f"❌ Ledger posting failed for Receipt #{receipt_master.id}: {e}")
        raise

def delete_ledger_postings_for_receipt(receipt_master):
    """
    Delete all LedgerPosting entries related to a Receipt voucher.
    VoucherType ID = 4
    VoucherNo = receipt_master.id
    """
    try:
        deleted_count, _ = LedgerPosting.objects.filter(
            VoucherType_id=4,
            VoucherNo=receipt_master.id
        ).delete()

        print(f"🗑️ Deleted {deleted_count} ledger postings for Receipt #{receipt_master.id}")

    except Exception as e:
        print(f"❌ Failed to delete ledger postings for Receipt #{receipt_master.id}: {e}")
        raise

def create_ledger_postings_for_local_payment(local_payment):
    """
    Create LedgerPosting entries for Local Payment.

    Rules:
    - VoucherType = LocalPayment.voucherType (default = 11)
    - MASTER ENTRY:
        Credit payment_mode ledger with net_amount
    - DETAIL ENTRIES:
        Debit each LocalPaymentItems.ledger with item.amount
    - Skip ledger posting if PDC and not cleared
    """

    try:
        # ⛔ Skip ledger posting if PDC and not cleared
        if local_payment.IsPDC and local_payment.Cleared != "Cleared":
            print(f"⏸️ LocalPayment #{local_payment.id} skipped (PDC Not Cleared)")
            return

        voucher_type = local_payment.voucherType

        # -------- MASTER CREDIT ENTRY --------
        LedgerPosting.objects.create(
            date=local_payment.date,
            VoucherType=voucher_type,
            VoucherNo=local_payment.id,                 # Master voucher reference
            ledger=local_payment.payment_mode,          # Cash / Bank / Cheque ledger
            debit=None,
            credit=local_payment.net_amount or Decimal('0.00'),
            RefVoucherNo=None,
            RefVoucherType=None,
            FY=local_payment.date.year,
            IsDeleted=False,
        )

        # -------- DETAIL DEBIT ENTRIES --------
        for item in local_payment.items.all():
            LedgerPosting.objects.create(
                date=local_payment.date,
                VoucherType=voucher_type,
                VoucherNo=item.id,                       # Detail row reference
                ledger=item.ledger,                      # Expense / Party ledger
                debit=item.amount or Decimal('0.00'),
                credit=None,
                RefVoucherNo=local_payment.id,
                RefVoucherType=voucher_type,
                FY=local_payment.date.year,
                IsDeleted=False,
            )

        print(f"✅ Ledger postings created for Local Payment #{local_payment.id}")

    except Exception as e:
        print(f"❌ Ledger posting failed for Local Payment #{local_payment.id}: {e}")
    

def delete_ledger_postings_for_invoice(invoice):
    """
    Delete existing ledger postings for an invoice
    Called before creating new postings in edit mode
    """
    try:
        from accounts_app.models import LedgerPosting
        
        # Delete all ledger postings related to this invoice
        deleted_count = LedgerPosting.objects.filter(
            VoucherNo=invoice.id,  # Adjust based on what you use in create function
            VoucherType=invoice.voucherType  # or VoucherType__pk=2
        ).delete()
        
        print(f"✅ Deleted {deleted_count[0]} ledger postings for Invoice #{invoice.voucher_no}")
        
    except Exception as e:
        print(f"❌ Failed to delete ledger postings for Invoice #{invoice.id}: {e}")        


def delete_ledger_postings_for_hire(fleet_hire):
    """
    Delete existing ledger postings for a fleet hire
    Called before creating new postings in edit mode
    """
    try:
        from accounts_app.models import LedgerPosting
        
        # Delete all ledger postings related to this fleet hire
        deleted_count = LedgerPosting.objects.filter(
            VoucherNo=fleet_hire.id,
            VoucherType=fleet_hire.voucherType  # or VoucherType__pk=1
        ).delete()
        
        print(f"✅ Deleted {deleted_count[0]} ledger postings for Hire #{fleet_hire.id}")
        
    except Exception as e:
        print(f"❌ Failed to delete ledger postings for Hire #{fleet_hire.id}: {e}")      

def create_bounce_charge_ledger_posting(payment_master):
    """
    Create ledger postings for bounce charge
    Debit: Bank Charges (Ledger ID 16)
    Credit: Cash/Bank account (from payment)
    """
    try:
        if not payment_master.BounceCharge or payment_master.BounceCharge <= 0:
            print("⏸️ No bounce charge to post")
            return
        
        voucher_type = Vouchers.objects.get(pk=3)  # Payment voucher type
        
        # ✅ Get Bank Charges ledger (ID: 16)
        try:
            bank_charges_ledger = LedgerCreation.objects.get(pk=16)  # Bank Charges
            print(f"Using ledger: {bank_charges_ledger.ledger_name}")
        except LedgerCreation.DoesNotExist:
            print("❌ Ledger ID 16 (Bank Charges) not found!")
            return
        
        # -------- DEBIT: Bank Charges (Expense - ID 16) --------
        LedgerPosting.objects.create(
            date=payment_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_master.id,
            ledger=bank_charges_ledger,  # Ledger ID 16
            debit=payment_master.BounceCharge,
            credit=None,
        )
        
        # -------- CREDIT: Cash/Bank Account --------
        LedgerPosting.objects.create(
            date=payment_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_master.id,
            ledger=payment_master.Ledger,  # The cash/bank account from payment
            debit=None,
            credit=payment_master.BounceCharge,
        )
        
        print(f"✅ Bounce charge ledger postings created for Payment #{payment_master.id}")
        print(f"   Debit: Bank Charges (ID 16) - ₹{payment_master.BounceCharge}")
        print(f"   Credit: {payment_master.Ledger.LedgerName} - ₹{payment_master.BounceCharge}")
        
    except Exception as e:
        print(f"❌ Bounce charge ledger posting failed for Payment #{payment_master.id}: {e}")
        import traceback
        traceback.print_exc()                  


def create_bounce_charge_ledger_posting_receipt(receipt_master):
    """
    Create ledger postings for bounce charge on Receipt
    Debit: Cash/Bank account (from receipt)
    Credit: Bank Charges (Ledger ID 16)
    """
    try:
        if not receipt_master.BounceCharge or receipt_master.BounceCharge <= 0:
            print("⏸️ No bounce charge to post")
            return
        
        voucher_type = Vouchers.objects.get(pk=4)  # Receipt voucher type
        
        # ✅ Get Bank Charges ledger (ID: 16)
        try:
            bank_charges_ledger = LedgerCreation.objects.get(pk=16)  # Bank Charges
            print(f"Using ledger: {bank_charges_ledger.LedgerName}")
        except LedgerCreation.DoesNotExist:
            print("❌ Ledger ID 16 (Bank Charges) not found!")
            return
        
        # -------- DEBIT: Cash/Bank Account --------
        LedgerPosting.objects.create(
            date=receipt_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_master.id,
            ledger=receipt_master.Ledger,  # The cash/bank account from receipt
            debit=receipt_master.BounceCharge,
            credit=None,
        )
        
        # -------- CREDIT: Bank Charges (Expense - ID 16) --------
        LedgerPosting.objects.create(
            date=receipt_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_master.id,
            ledger=bank_charges_ledger,  # Ledger ID 16
            debit=None,
            credit=receipt_master.BounceCharge,
        )
        
        print(f"✅ Bounce charge ledger postings created for Receipt #{receipt_master.id}")
        print(f"   Debit: {receipt_master.Ledger.LedgerName} - ₹{receipt_master.BounceCharge}")
        print(f"   Credit: Bank Charges (ID 16) - ₹{receipt_master.BounceCharge}")
        
    except Exception as e:
        print(f"❌ Bounce charge ledger posting failed for Receipt #{receipt_master.id}: {e}")
        import traceback
        traceback.print_exc()

def create_bounce_charge_ledger_posting_receiptbill(receipt_bill_master):
    """
    Create ledger postings for bounce charge on Receipt Bill
    Debit: Cash/Bank account (from receipt bill)
    Credit: Bank Charges (Ledger ID 16)
    """
    try:
        if not receipt_bill_master.BounceCharge or receipt_bill_master.BounceCharge <= 0:
            print("⏸️ No bounce charge to post")
            return
        
        voucher_type = Vouchers.objects.get(pk=14)  # Receipt Bill voucher type (adjust ID as needed)
        
        # ✅ Get Bank Charges ledger (ID: 16)
        try:
            bank_charges_ledger = LedgerCreation.objects.get(pk=16)  # Bank Charges
            print(f"Using ledger: {bank_charges_ledger.ledger_name}")
        except LedgerCreation.DoesNotExist:
            print("❌ Ledger ID 16 (Bank Charges) not found!")
            return
        
        # -------- DEBIT: Cash/Bank Account --------
        LedgerPosting.objects.create(
            date=receipt_bill_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_bill_master.id,
            ledger=receipt_bill_master.Ledger,  # The cash/bank account from receipt bill
            debit=receipt_bill_master.BounceCharge,
            credit=None,
        )
        
        # -------- CREDIT: Bank Charges (Expense - ID 16) --------
        LedgerPosting.objects.create(
            date=receipt_bill_master.Date,
            VoucherType=voucher_type,
            VoucherNo=receipt_bill_master.id,
            ledger=bank_charges_ledger,  # Ledger ID 16
            debit=None,
            credit=receipt_bill_master.BounceCharge,
        )
        
        print(f"✅ Bounce charge ledger postings created for Receipt Bill #{receipt_bill_master.id}")
        print(f"   Debit: {receipt_bill_master.Ledger.ledger_name} - ₹{receipt_bill_master.BounceCharge}")
        print(f"   Credit: Bank Charges (ID 16) - ₹{receipt_bill_master.BounceCharge}")
        
    except Exception as e:
        print(f"❌ Bounce charge ledger posting failed for Receipt Bill #{receipt_bill_master.id}: {e}")
        import traceback
        traceback.print_exc()     

def create_bounce_charge_ledger_posting_paymentbill(payment_bill_master):
    """
    Create ledger postings for bounce charge on Payment Bill
    Debit: Bank Charges (Ledger ID 16)
    Credit: Cash/Bank account (from payment bill)
    """
    try:
        if not payment_bill_master.BounceCharge or payment_bill_master.BounceCharge <= 0:
            print("⏸️ No bounce charge to post")
            return
        
        voucher_type = Vouchers.objects.get(pk=13)  # Payment Bill voucher type (adjust ID as needed)
        
        # ✅ Get Bank Charges ledger (ID: 16)
        try:
            bank_charges_ledger = LedgerCreation.objects.get(pk=16)  # Bank Charges
            print(f"Using ledger: {bank_charges_ledger.ledger_name}")
        except LedgerCreation.DoesNotExist:
            print("❌ Ledger ID 16 (Bank Charges) not found!")
            return
        
        # -------- DEBIT: Bank Charges (Expense - ID 16) --------
        LedgerPosting.objects.create(
            date=payment_bill_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_bill_master.id,
            ledger=bank_charges_ledger,  # Ledger ID 16
            debit=payment_bill_master.BounceCharge,
            credit=None,
        )
        
        # -------- CREDIT: Cash/Bank Account --------
        LedgerPosting.objects.create(
            date=payment_bill_master.Date,
            VoucherType=voucher_type,
            VoucherNo=payment_bill_master.id,
            ledger=payment_bill_master.Ledger,  # The cash/bank account from payment bill
            debit=None,
            credit=payment_bill_master.BounceCharge,
        )
        
        print(f"✅ Bounce charge ledger postings created for Payment Bill #{payment_bill_master.id}")
        print(f"   Debit: Bank Charges (ID 16) - ₹{payment_bill_master.BounceCharge}")
        print(f"   Credit: {payment_bill_master.Ledger.ledger_name} - ₹{payment_bill_master.BounceCharge}")
        
    except Exception as e:
        print(f"❌ Bounce charge ledger posting failed for Payment Bill #{payment_bill_master.id}: {e}")
        import traceback
        traceback.print_exc()           






def update_vehicle_profit_loss_for_invoice(invoice):
    """
    Create/Update VehicleProfitLoss entries for an Invoice.
    Income entries: Amount is positive (total_amount from InvoiceDetails)
    """
    with transaction.atomic():
        # Delete old entries for this invoice
        VehicleProfitLoss.objects.filter(
            InvNo=f"INV-{invoice.voucher_no}"
        ).delete()
        
        # Create new entries for each vehicle in invoice details
        for detail in invoice.details.all():
            vehicle = detail.vehicle
            
            VehicleProfitLoss.objects.create(
                Vehicle=vehicle,
                Date=invoice.date,
                Details=f"Invoice #{invoice.voucher_no} - {detail.location}",
                Amount=detail.total_amount,  # Positive (Income)
                InvNo=f"INV-{invoice.voucher_no}",
                InvAmount=invoice.grand_total,
                Balance=0  # Will be calculated in recalculate_balance
            )
        
        # Recalculate balances for all affected vehicles
        affected_vehicles = set(detail.vehicle for detail in invoice.details.all())
        for vehicle in affected_vehicles:
            recalculate_vehicle_balance(vehicle)


def update_vehicle_profit_loss_for_hire(fleet_hire):
    """
    Create/Update VehicleProfitLoss entries for FleetHire.
    Expense entries: Amount is negative (rate_per_period * no_of_unit)
    """
    with transaction.atomic():
        # Delete old entries for this hire
        VehicleProfitLoss.objects.filter(
            InvNo=f"HIRE-{fleet_hire.voucher_no}"
        ).delete()
        
        # Create new entries for each vehicle in hire details
        for detail in fleet_hire.details.all():
            vehicle = detail.vehicle
            expense_amount = detail.rate_per_period * detail.no_of_unit
            
            VehicleProfitLoss.objects.create(
                Vehicle=vehicle,
                Date=fleet_hire.date,
                Details=f"Hire #{fleet_hire.voucher_no} - {detail.unit} ({detail.start_date} to {detail.end_date})",
                Amount=-expense_amount,  # Negative (Expense)
                InvNo=f"HIRE-{fleet_hire.voucher_no}",
                InvAmount=fleet_hire.grand_total,
                Balance=0  # Will be calculated in recalculate_balance
            )
        
        # Recalculate balances for all affected vehicles
        affected_vehicles = set(detail.vehicle for detail in fleet_hire.details.all())
        for vehicle in affected_vehicles:
            recalculate_vehicle_balance(vehicle)


def update_vehicle_profit_loss_for_payment(payment_master):
    """
    Create/Update VehicleProfitLoss entries for PaymentMaster.
    Only creates entries for payment details that have a Vehicle assigned.
    Expense entries: Amount is negative
    """
    with transaction.atomic():
        # Delete old entries for this payment
        VehicleProfitLoss.objects.filter(
            InvNo=f"PAY-{payment_master.voucher_no}"
        ).delete()
        
        # Create new entries only for details with vehicles
        affected_vehicles = set()
        for detail in payment_master.details.all():
            if detail.Vehicle:  # Only process if vehicle is assigned
                vehicle = detail.Vehicle
                affected_vehicles.add(vehicle)
                
                desc = f"Payment #{payment_master.voucher_no} - {payment_master.PaidTo}"
                if detail.Desc:
                    desc += f" ({detail.Desc})"
                
                VehicleProfitLoss.objects.create(
                    Vehicle=vehicle,
                    Date=payment_master.Date,
                    Details=desc,
                    Amount=-detail.Amount,  # Negative (Expense)
                    InvNo=f"PAY-{payment_master.voucher_no}",
                    InvAmount=payment_master.TotalAmount,
                    Balance=0  # Will be calculated in recalculate_balance
                )
        
        # Recalculate balances for all affected vehicles
        for vehicle in affected_vehicles:
            recalculate_vehicle_balance(vehicle)


def delete_vehicle_profit_loss_for_invoice(invoice):
    """Delete VehicleProfitLoss entries when an invoice is deleted"""
    with transaction.atomic():
        affected_vehicles = set(detail.vehicle for detail in invoice.details.all())
        
        VehicleProfitLoss.objects.filter(
            InvNo=f"INV-{invoice.voucher_no}"
        ).delete()
        
        # Recalculate balances for affected vehicles
        for vehicle in affected_vehicles:
            recalculate_vehicle_balance(vehicle)


def delete_vehicle_profit_loss_for_hire(fleet_hire):
    """Delete VehicleProfitLoss entries when a hire is deleted"""
    with transaction.atomic():
        affected_vehicles = set(detail.vehicle for detail in fleet_hire.details.all())
        
        VehicleProfitLoss.objects.filter(
            InvNo=f"HIRE-{fleet_hire.voucher_no}"
        ).delete()
        
        # Recalculate balances for affected vehicles
        for vehicle in affected_vehicles:
            recalculate_vehicle_balance(vehicle)


def delete_vehicle_profit_loss_for_payment(payment_master):
    """Delete VehicleProfitLoss entries when a payment is deleted"""
    with transaction.atomic():
        affected_vehicles = set(
            detail.Vehicle for detail in payment_master.details.all() 
            if detail.Vehicle
        )
        
        VehicleProfitLoss.objects.filter(
            InvNo=f"PAY-{payment_master.voucher_no}"
        ).delete()
        
        # Recalculate balances for affected vehicles
        for vehicle in affected_vehicles:
            recalculate_vehicle_balance(vehicle)


def recalculate_vehicle_balance(vehicle):
    """
    Recalculate running balance for all entries of a specific vehicle.
    Orders by Date and ID, then updates Balance field with cumulative sum.
    """
    entries = VehicleProfitLoss.objects.filter(
        Vehicle=vehicle
    ).order_by('Date', 'id')
    
    running_balance = Decimal('0')
    for entry in entries:
        running_balance += entry.Amount
        entry.Balance = running_balance
        entry.save(update_fields=['Balance'])


def get_vehicle_profit_loss_summary(vehicle, start_date=None, end_date=None):
    """
    Get profit/loss summary for a vehicle within date range.
    Returns dict with income, expense, and profit.
    """
    queryset = VehicleProfitLoss.objects.filter(Vehicle=vehicle)
    
    if start_date:
        queryset = queryset.filter(Date__gte=start_date)
    if end_date:
        queryset = queryset.filter(Date__lte=end_date)
    
    income = Decimal('0')
    expense = Decimal('0')
    
    for entry in queryset:
        if entry.Amount > 0:
            income += entry.Amount
        else:
            expense += abs(entry.Amount)
    
    profit = income - expense
    
    return {
        'vehicle': vehicle,
        'income': income,
        'expense': expense,
        'profit': profit,
        'profit_percentage': (profit / income * 100) if income > 0 else 0
    }



OPENING_VOUCHER_ID = 16
OPENING_VOUCHER_NO = 0
@transaction.atomic
def handle_opening_balance_ledger_posting(ledger, action="create"):
    """
    Handles Opening Balance LedgerPosting
    action: create | update | delete
    """

    # 🔹 Financial Year logic (adjust if FY stored elsewhere)
    fy_year = date.today().year
    fy_start_date = datetime.strptime(settings.FINYEAR, "%Y-%m-%d").date()


    opening_voucher = Vouchers.objects.get(pk=OPENING_VOUCHER_ID)

    posting = LedgerPosting.objects.filter(
        ledger=ledger,
        VoucherType=opening_voucher,
        VoucherNo=OPENING_VOUCHER_NO,
        IsDeleted=False
    ).first()

    # ================= DELETE =================
    if action == "delete":
        if posting:
            posting.delete()
        return

    opening_amount = Decimal(str(ledger.opening_balance or 0))

    # ❌ No opening balance → remove posting
    if opening_amount <= 0 or not ledger.types:
        if posting:
            posting.delete()
        return

    debit = credit = None

    if ledger.types == 'DR':
        debit = opening_amount
        credit = None
    elif ledger.types == 'CR':
        credit = opening_amount
        debit = None

    # 🔁 Update existing posting
    if posting:
        posting.date = fy_start_date
        posting.debit = debit
        posting.credit = credit
        posting.FY = fy_year
        posting.save()

    # ➕ Create new posting
    else:
        LedgerPosting.objects.create(
            date=fy_start_date,
            VoucherType=opening_voucher,
            VoucherNo=OPENING_VOUCHER_NO,
            ledger=ledger,
            debit=debit,
            credit=credit,
            FY=fy_year
        )    