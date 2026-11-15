from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404

from jobcard_app.models import CustomInspection, VehicleInspection

from .services.custom_inspection_builder import build_custom_inspection_context
from .services.inspection_builder import build_inspection_context
from .services.pdf_service import generate_pdf
from .services.regular_inspection_builder import build_regular_inspection_context
from jobcard_app.models import Invoice
from .services.invoice_pdf_builder import build_invoice_pdf_context
REGULAR_TEMPLATE = "pdf_generator/pdf_regular_inspection.html"
REGULAR_CSS = "pdf_generator/regular_inspection.css"
CUSTOM_TEMPLATE = "pdf_generator/pdf_custom_inspection.html"
CUSTOM_CSS = "pdf_generator/custom_inspection.css"


def _pdf_response(pdf_bytes, filename):
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def sample_pdf(request):
    context = {
        "company": {
            "name": "Silver Line Group",
            "address": "Kerala, India",
            "phone": "9876543210",
            "email": "info@example.com",
        },
        "document": {
            "title": "SAMPLE INVOICE",
            "subtitle": "Workshop Service Invoice",
            "number": "INV-001",
            "date": "13-11-2026",
            "notes": "This is a sample PDF.",
        },
        "details": [
            {"label": "Customer", "value": "Sample Customer"},
            {"label": "Vehicle", "value": "Toyota Innova"},
        ],
        "columns": [
            {"key": "description", "label": "Description"},
            {"key": "quantity", "label": "Quantity"},
            {"key": "rate", "label": "Rate"},
            {"key": "amount", "label": "Amount"},
        ],
        "rows": [
            {"description": "Engine Service", "quantity": 1, "rate": 1500, "amount": 1500},
            {"description": "Oil Filter", "quantity": 2, "rate": 500, "amount": 1000},
        ],
        "totals": [
            {"label": "Subtotal", "value": "2500.00"},
            {"label": "Tax", "value": "450.00"},
            {"label": "Grand Total", "value": "2950.00"},
        ],
        "amount_in_words": "Two Thousand Nine Hundred Fifty Only",
        "signatures": [
            {"label": "Prepared By"},
            {"label": "Authorized Signature"},
        ],
    }
    return _pdf_response(generate_pdf(request, context), "sample_invoice.pdf")


@login_required
def inspection_pdf(request, pk):
    """Old combined (Standard + Custom) PDF - kept so existing links still work."""
    inspection = get_object_or_404(
        VehicleInspection.objects.select_related(
            "vehicle", "customer", "inspector",
        ).prefetch_related(
            "exterior_damages", "findings", "custom_inspection__answers",
        ),
        pk=pk,
    )
    context = build_inspection_context(inspection)
    return _pdf_response(
        generate_pdf(request, context), f"inspection_{inspection.pk}.pdf"
    )


@login_required
def regular_inspection_pdf(request, pk):
    """Standard flow PDF: stored file if present, otherwise built fresh."""
    inspection = get_object_or_404(
        VehicleInspection.objects.select_related(
            "vehicle", "customer", "inspector",
        ).prefetch_related("exterior_damages", "findings"),
        pk=pk,
    )

    if inspection.pdf_file:
        return FileResponse(
            inspection.pdf_file.open("rb"),
            content_type="application/pdf",
            filename=f"regular_inspection_{inspection.pk}.pdf",
        )

    context = build_regular_inspection_context(inspection)
    pdf_bytes = generate_pdf(
        request, context,
        template_name=REGULAR_TEMPLATE, css_name=REGULAR_CSS,
    )
    return _pdf_response(pdf_bytes, f"regular_inspection_{inspection.pk}.pdf")


@login_required
def custom_inspection_pdf(request, pk):
    """Custom flow PDF: stored file if present, otherwise built fresh."""
    inspection = get_object_or_404(
        CustomInspection.objects.select_related(
            "vehicle", "customer", "inspector",
        ).prefetch_related("answers"),
        pk=pk,
    )

    if inspection.pdf_file:
        return FileResponse(
            inspection.pdf_file.open("rb"),
            content_type="application/pdf",
            filename=f"custom_inspection_{inspection.pk}.pdf",
        )

    context = build_custom_inspection_context(inspection)
    pdf_bytes = generate_pdf(
        request, context,
        template_name=CUSTOM_TEMPLATE, css_name=CUSTOM_CSS,
    )
    return _pdf_response(pdf_bytes, f"custom_inspection_{inspection.pk}.pdf")


INVOICE_TEMPLATE = "pdf_generator/pdf_invoice.html"
INVOICE_CSS = "pdf_generator/invoice.css"


@login_required
def invoice_pdf(request, pk):
    """Invoice PDF - built fresh each time so it always shows current payments."""
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "customer", "jobcard",
        ).prefetch_related(
            "items__vehicle",
            "items__technician",
            "vehicles__vehicle__manufacturer",
            "vehicles__vehicle__vehicle_model",
        ),
        pk=pk,
    )

    context = build_invoice_pdf_context(invoice)
    pdf_bytes = generate_pdf(
        request, context,
        template_name=INVOICE_TEMPLATE,
        css_name=INVOICE_CSS,
    )
    return _pdf_response(pdf_bytes, f"invoice_{invoice.display_number}.pdf")
