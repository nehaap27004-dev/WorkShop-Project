from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from num2words import num2words

from pdf_generator.services.pdf_service import generate_pdf


def to_decimal(value):
    """Convert a value safely to a 3-decimal Decimal."""
    return Decimal(str(value or "0")).quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP
    )


def get_media_uri(*parts):
    """Return a local file URI if the media file exists."""
    file_path = Path(settings.MEDIA_ROOT).joinpath(*parts)

    if file_path.exists():
        return file_path.resolve().as_uri()

    return ""


def generate_payment_pdf_response(request, payment):

    payment_details = list(
        payment.details.select_related("Ledger").all()
    )

    vat_type_labels = {
        1: "No VAT",
        2: "Inclusive VAT (5%)",
        3: "Exclusive VAT (5%)",
    }

    payment_rows = []

    total_taxable = Decimal("0.000")
    total_vat = Decimal("0.000")
    line_total = Decimal("0.000")

    # Build detailed or non-detailed payment rows
    for index, detail in enumerate(payment_details, start=1):

        ledger_name = (
            detail.Ledger.ledger_name if detail.Ledger else ""
        )

        amount = to_decimal(detail.Amount)
        line_total += amount

        if payment.is_detailed:

            vat_amount = to_decimal(detail.vat_amount)
            taxable = amount - vat_amount

            total_taxable += taxable
            total_vat += vat_amount

            payment_rows.append({
                "sl_no": index,
                "invoice_date": (
                    detail.invoice_date.strftime("%d-%m-%Y")
                    if detail.invoice_date else ""
                ),
                "invoice_no": detail.invoice_no or "",
                "ledger_name": ledger_name,
                "vat_type": vat_type_labels.get(detail.vat_type, ""),
                "taxable": taxable,
                "vat_amount": vat_amount,
                "amount": amount,
            })

        else:
            payment_rows.append({
                "sl_no": index,
                "ledger_name": ledger_name,
                "amount": amount,
            })

    # Bounce charge
    bounce_charge = to_decimal(payment.BounceCharge)

    # Preserve the existing TotalAmount calculation:
    # use saved TotalAmount when available;
    # otherwise use detail amounts plus bounce charge.
    if payment.TotalAmount:
        grand_total = to_decimal(payment.TotalAmount)
    else:
        grand_total = line_total + bounce_charge

    # Amount in words
    riyal_part = int(grand_total)
    baisa_part = int(
        (grand_total - Decimal(riyal_part)) * 1000
    )

    riyal_words = num2words(
        riyal_part,
        to="cardinal",
        lang="en"
    ).capitalize()

    if baisa_part > 0:
        baisa_words = num2words(
            baisa_part,
            to="cardinal",
            lang="en"
        ).capitalize()

        amount_in_words = (
            f"Omani Rial {riyal_words} "
            f"and {baisa_words} Baisa Only"
        )
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    amount_in_words += f" (OMR {grand_total:.3f})"

    # Optional signature image only.
    # Company header and footer images are intentionally excluded.
    signature_uri = ""

    if payment.enable_signature:
        signature_uri = get_media_uri(
            "timesheet_head",
            "sign.jpg"
        )

    context = {
        "payment": payment,
        "paid_to": (
            payment.PaidTo
            or (payment.Ledger.ledger_name if payment.Ledger else "")
        ),
        "payment_rows": payment_rows,
        "is_detailed": payment.is_detailed,
        "total_taxable": total_taxable,
        "total_vat": total_vat,
        "line_total": line_total,
        "bounce_charge": bounce_charge,
        "grand_total": grand_total,
        "amount_in_words": amount_in_words,
        "signature_uri": signature_uri,
    }

    pdf_bytes = generate_pdf(
        request=request,
        context=context,
        template_name="pdf_generator/pdf_payment.html",
        css_name="pdf_generator/payment.css",
    )

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="payment_{payment.voucher_no}.pdf"'
    )

    return response