
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse

from num2words import num2words

from pdf_generator.services.pdf_service import generate_pdf


def _get_media_uri(*parts):
    """
    Return an absolute file URI for an existing media image.
    """
    file_path = Path(settings.MEDIA_ROOT).joinpath(*parts)

    if file_path.exists():
        return file_path.resolve().as_uri()

    return ""


def generate_receipt_pdf_response(request, receipt):
    """
    Generate Receipt Voucher PDF using HTML and WeasyPrint.

    Preserves:
    - Receipt details
    - PDC / cheque information
    - Bounce charge
    - Amount in words
    - Optional header, footer and signature images
    """

    # Fetch receipt details with their associated ledgers
    receipt_details = list(
        receipt.details.select_related("Ledger").all()
    )

    # Calculate total using the existing ReportLab calculation
    total_amount = sum(
        (detail.Amount or Decimal("0.000")
         for detail in receipt_details),
        Decimal("0.000")
    )

    bounce_charge = receipt.BounceCharge or Decimal("0.000")

    if bounce_charge > 0:
        total_amount += bounce_charge

    total_amount = total_amount.quantize(
        Decimal("0.001"),
        rounding=ROUND_HALF_UP
    )

    # Convert amount into words
    riyal_part = int(total_amount)
    baisa_part = int(
        (total_amount - Decimal(riyal_part)) * 1000
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
        amount_in_words = (
            f"Omani Rial {riyal_words} Only"
        )

    amount_in_words += f" (OMR {total_amount:.3f})"

    # Company images
    logo_uri = _get_media_uri(
        "timesheet_head", "silver_head.jpg"
    )

    footer_uri = _get_media_uri(
        "timesheet_head", "silver_footer.jpg"
    )

    signature_uri = _get_media_uri(
        "timesheet_head", "sign.jpg"
    )

    # Template context
    context = {
        "receipt": receipt,
        "receipt_details": receipt_details,
        "received_from": (
            receipt.ReceivedFrom
            or (
                receipt.Ledger.ledger_name
                if receipt.Ledger else ""
            )
        ),
        "total_amount": total_amount,
        "bounce_charge": bounce_charge,
        "amount_in_words": amount_in_words,
        "logo_uri": logo_uri,
        "footer_uri": footer_uri,
        "signature_uri": signature_uri,
    }

    # Generate PDF bytes using existing WeasyPrint service
    pdf_bytes = generate_pdf(
        request=request,
        context=context,
        template_name="pdf_generator/pdf_receipt.html",
        css_name="pdf_generator/receipt.css",
    )

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="receipt_{receipt.voucher_no}.pdf"'
    )

    return response
