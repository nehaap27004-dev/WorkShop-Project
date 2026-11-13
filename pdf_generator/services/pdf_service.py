from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS


def generate_pdf(request, context):
    html_string = render_to_string(
        "pdf_generator/pdf_template.html",
        context,
        request=request,
    )

    css_path = finders.find("pdf_generator/pdf.css")

    if not css_path:
        raise FileNotFoundError(
            "PDF CSS file not found: pdf_generator/pdf.css"
        )

    pdf_file = HTML(
        string=html_string,
        base_url=request.build_absolute_uri("/"),
    ).write_pdf(
        stylesheets=[CSS(filename=css_path)]
    )

    return pdf_file