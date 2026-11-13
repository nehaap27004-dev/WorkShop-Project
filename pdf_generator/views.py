from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from .services.pdf_service import generate_pdf
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from jobcard_app.models import VehicleInspection
from .services.inspection_builder import build_inspection_context



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
            {
                "description": "Engine Service",
                "quantity": 1,
                "rate": 1500,
                "amount": 1500,
            },
            {
                "description": "Oil Filter",
                "quantity": 2,
                "rate": 500,
                "amount": 1000,
            },
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

    pdf_file = generate_pdf(request, context)

    response = HttpResponse(
        pdf_file,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        'inline; filename="sample_invoice.pdf"'
    )

    return response

@login_required
def inspection_pdf(request, pk):

    inspection = get_object_or_404(
        VehicleInspection.objects.select_related(
            "vehicle",
            "customer",
            "inspector",
        ).prefetch_related(
            "exterior_damages",
            "findings",
            "custom_inspection__answers",
        ),
        pk=pk
    )

    # Prepare inspection data for PDF
    context = build_inspection_context(inspection)

    # Generate PDF
    pdf_file = generate_pdf(request, context)

    response = HttpResponse(
        pdf_file,
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'inline; filename="inspection_{inspection.pk}.pdf"'
    )

    return response
