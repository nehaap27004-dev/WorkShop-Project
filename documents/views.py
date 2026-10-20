from django.shortcuts import render

# Create your views here.
# views.py
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .services.invoice_pdf import generate_invoice_pdf, render_invoice_html

def invoice_pdf_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)   # add your permission/company checks
    pdf = generate_invoice_pdf(invoice)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
    return response

def invoice_html_preview(request, invoice_id):
    """Open in browser for fast design work. No PDF step."""
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return HttpResponse(render_invoice_html(invoice))