import logging

from django.core.files.base import ContentFile

from .pdf_service import generate_pdf
from .custom_inspection_builder import build_custom_inspection_context

logger = logging.getLogger(__name__)

CUSTOM_TEMPLATE = "pdf_generator/pdf_custom_inspection.html"
CUSTOM_CSS = "pdf_generator/custom_inspection.css"


def render_custom_inspection_pdf(inspection, request=None):
    context = build_custom_inspection_context(inspection)
    return generate_pdf(
        request, context,
        template_name=CUSTOM_TEMPLATE,
        css_name=CUSTOM_CSS,
    )


def save_custom_inspection_pdf(inspection, request=None):
    """
    Generate the Custom Inspection PDF and store it on the record.
    Never raises: a PDF problem must not break saving the inspection.
    Returns True on success.
    """
    try:
        pdf_bytes = render_custom_inspection_pdf(inspection, request)

        if inspection.pdf_file:
            inspection.pdf_file.delete(save=False)  # replace old version

        inspection.pdf_file.save(
            f"custom_inspection_{inspection.pk}.pdf",
            ContentFile(pdf_bytes),
            save=False,
        )
        inspection.save(update_fields=["pdf_file"])
        return True
    except Exception:
        logger.exception(
            "Custom inspection PDF failed for pk=%s", inspection.pk
        )
        return False