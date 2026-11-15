from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from weasyprint import HTML, CSS


def generate_pdf(
    request,
    context,
    template_name="pdf_generator/pdf_template.html",
    css_name="pdf_generator/pdf.css",
):
    """Render `template_name` with `context` and return the PDF as bytes."""
    html_string = render_to_string(template_name, context, request=request)

    css_path = finders.find(css_name)
    if not css_path:
        raise FileNotFoundError(f"PDF CSS file not found: {css_name}")

    base_url = (
        request.build_absolute_uri("/") if request else str(settings.BASE_DIR)
    )

    return HTML(string=html_string, base_url=base_url).write_pdf(
        stylesheets=[CSS(filename=css_path)]
    )