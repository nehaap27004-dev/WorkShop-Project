# reports.py
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT
from django.conf import settings
from fleet_app.common import build_pdf
from num2words import num2words
import os

styles = getSampleStyleSheet()


def create_timesheet_pdf(timesheet):
    """
    Builds and returns a Django HttpResponse containing the timesheet PDF.
    
    Components:
    - Header: Top logo image (enable_header) - TS_head.jpg
    - Footer: Bottom footer image (enable_footer) - RFT_footer.png
    - Text Labels: PREPARED BY, SITE INCHARGE, APPROVED BY (ALWAYS shown)
    - Signature: Signature image above text labels (enable_signature) - sign.jpg
    """
    buffer = BytesIO()
    filename = buffer

    # === Gather Detail Totals ===
    all_details = timesheet.details.all()
    total_days = all_details.count()
    total_hours_worked = sum(d.total_hours_worked for d in all_details)
    total_ot_hours = sum(d.ot for d in all_details)
    total_break_hours = sum(d.break_hours for d in all_details)
    total_hours = total_hours_worked + total_ot_hours - total_break_hours

    # === Story Content (Main Section) ===
    story = []
    story.append(Spacer(1, 12))

    # === TITLE ===
    title = Paragraph("<b><font size=14>TIMESHEET</font></b>", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 15))  # Increased spacer

    # === Timesheet Header Table ===
    timesheet_data = [
        ['Vehicle Reg No:', timesheet.vehicle_reg_no, 'Vehicle Name:', timesheet.vehicle_name],
        ['Project Location:', timesheet.project_location, 'Client:', str(timesheet.client)],
        ['Duration:', str(timesheet.duration), 'PO Reference:', timesheet.PO_reference_no or ''],
        ['Date:', timesheet.date.strftime('%Y-%m-%d'), 'Driver Name:', str(timesheet.driver_name)],
        ['Operator Name:', str(timesheet.operator_name or ''), 'Description:', timesheet.description or ''],
    ]

    page_width, _ = A4
    side_margin = 0.6 * inch
    usable_width = page_width - (2 * side_margin)

    header_table = Table(
        timesheet_data,
        colWidths=[usable_width * 0.25] * 4,
    )
    header_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),  # Outer border
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),  # Inner grid lines
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))

    # === Details Table - Two Column Layout ===
    # Split details into two columns (left: 16 dates, right: remaining dates)
    all_details_list = list(all_details)
    
    left_column = all_details_list[:16]  # First 16 dates
    right_column = all_details_list[16:]  # Remaining dates (15 or 14)
    
    # Table headers
    detail_headers = [
        'DATE', 'NORMAL\nHOURS', 'O\nT', 'TOTAL\nHOURS', 'REMARKS',
        '',  # Divider column
        'DATE', 'NORMAL\nHOURS', 'O\nT', 'TOTAL\nHOURS', 'REMARKS'
    ]
    detail_data = [detail_headers]
    
    # Build rows - maximum 16 rows (left side determines row count)
    max_rows = 16
    
    for i in range(max_rows):
        row = []
        
        # Left column data
        if i < len(left_column):
            d = left_column[i]
            normal_hours = d.total_hours_worked  # Normal hours = end_time - start_time - break
            total_hours = normal_hours + d.ot  # Total = normal + OT
            
            row.extend([
                d.date.strftime('%d.%m.%Y'),
                str(normal_hours) if normal_hours else '0',
                str(d.ot) if d.ot else '0',
                str(total_hours) if total_hours else '0',
                d.signature or '',
            ])
        else:
            row.extend(['', '', '', '', ''])
        
        # Divider
        row.append('')
        
        # Right column data
        if i < len(right_column):
            d = right_column[i]
            normal_hours = d.total_hours_worked
            total_hours = normal_hours + d.ot
            
            row.extend([
                d.date.strftime('%d.%m.%Y'),
                str(normal_hours) if normal_hours else '0',
                str(d.ot) if d.ot else '0',
                str(total_hours) if total_hours else '0',
                d.signature or '',
            ])
        else:
            row.extend(['', '', '', '', ''])
        
        detail_data.append(row)

    detail_table = Table(
        detail_data,
        colWidths=[
            usable_width * 0.11,  # DATE
            usable_width * 0.09,  # NORMAL HOURS
            usable_width * 0.05,  # OT
            usable_width * 0.09,  # TOTAL HOURS
            usable_width * 0.11,  # REMARKS
            usable_width * 0.02,  # Divider
            usable_width * 0.11,  # DATE
            usable_width * 0.09,  # NORMAL HOURS
            usable_width * 0.05,  # OT
            usable_width * 0.09,  # TOTAL HOURS
            usable_width * 0.11,  # REMARKS
        ],
    )
    detail_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (4, -1), 0.5, colors.black),  # Left section grid
        ('GRID', (6, 0), (10, -1), 0.5, colors.black),  # Right section grid
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Headers bold
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
        ('ALIGN', (1, 1), (4, -1), 'CENTER'),  # Left section alignment
        ('ALIGN', (7, 1), (10, -1), 'CENTER'),  # Right section alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Divider column styling
        ('BACKGROUND', (5, 0), (5, -1), colors.white),
        ('LINEAFTER', (5, 0), (5, -1), 0, colors.white),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 20))

    # === Footer Function: Text Labels + Optional Signature ===
    def footer_func(canvas, doc):
        """
        ALWAYS draws:
        - Text labels (PREPARED BY, etc.)
        Conditionally draws signature image if enabled
        NOTE: Computer generated text is handled by build_pdf, not here
        """
        canvas.saveState()
        
        # Signature image path
        signature_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'sign.jpg')
        
        # Draw signature image ABOVE text labels (if enabled and file exists)
        if timesheet.enable_signature and os.path.exists(signature_image_path):
            # Position for signature image (above text labels)
            sig_img_y = 2.9 * inch
            sig_img_x = 1 * inch
            sig_img_width = 6 * inch
            sig_img_height = 0.4 * inch
            
            canvas.drawImage(
                signature_image_path,
                sig_img_x,
                sig_img_y,
                width=sig_img_width,
                height=sig_img_height,
                preserveAspectRatio=True,
                mask='auto'
            )
        
        # ALWAYS draw text labels below signature area
        canvas.setFont("Helvetica", 10)
        y_text_labels = 1.6 * inch
        
        # Calculate equal spacing across the page width
        # Page width minus margins, divided into 3 equal sections
        left_margin = 0.75 * inch
        right_margin = 0.75 * inch
        available_width = page_width - left_margin - right_margin
        section_width = available_width / 3
        
        # Center position of each section
        x_prepared = left_margin + (section_width / 2)
        x_incharge = left_margin + section_width + (section_width / 2)
        x_approved = left_margin + (2 * section_width) + (section_width / 2)
        
        # Line width for each signature line
        line_width = section_width * 0.8

        labels = ["PREPARED BY", "SITE INCHARGE / ENGINEER", "APPROVED BY"]
        for label, x_pos in zip(labels, [x_prepared, x_incharge, x_approved]):
            canvas.drawCentredString(x_pos, y_text_labels, label)
            line_y = y_text_labels - 15
            canvas.setDash(1, 2)
            # Draw centered line under each label
            canvas.line(x_pos - (line_width / 2), line_y, x_pos + (line_width / 2), line_y)
            canvas.setDash()

        canvas.restoreState()

    # === Build PDF ===
    # logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'TS_head.jpg')
    # footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'RFT_footer.png')
    
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'azure_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'azure_footer.jpeg')

    build_pdf(
        filename=filename,
        story=story,
        logo_path=logo_path,
        include_header=timesheet.enable_header,           # Top logo image
        include_footer=True,                               # ALWAYS True so footer_func runs
        footer_func=footer_func,                           # ALWAYS runs (text + labels + signature)
        footer_on_last_page=True,
        footer_image_path=footer_image_path if timesheet.enable_footer else None,  # Footer image only if enabled
        doc_type="timesheet",
    )

    pdf = buffer.getvalue()
    buffer.close()
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="timesheet_{timesheet.id}.pdf"'
    response.write(pdf)
    return response


def create_simplequotation_pdf(quotation):
    """
    Build and return PDF response for Simple Quotation.
    
    Components:
    - Header: Top logo image (enable_header) - TS_head.jpg
    - Footer: Bottom footer image (enable_footer) - RFT_footer.png
    - Signature: Signature image above footer (enable_signature) - sign.jpg
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === QUOTATION NUMBER AND DATE HEADER ===
    blue_style = ParagraphStyle(
        'BlueHeader',
        parent=styles['Normal'],
        textColor=colors.HexColor('#1E3A8A'),
        fontSize=11,
        fontName='Helvetica-Bold'
    )
    
    date_style = ParagraphStyle(
        'DateHeader',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        alignment=TA_RIGHT
    )

    quote_header_data = [[
        Paragraph(f"{quotation.voucher_no}", blue_style),
        Paragraph(quotation.date.strftime("%d-%m-%Y"), date_style)
    ]]
    
    quote_header_table = Table(quote_header_data, colWidths=[300, 210])
    quote_header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(quote_header_table)
    story.append(Spacer(1, 8))

    # === FROM AND TO SECTION ===
    customer = quotation.customer
    
    from_text = """<b>From:</b><br/>
    RABWA FAHOUD TRAD & TRANSPORT CO SPC<br/>
    CR NO : 5029392 <br/>
    P.O Box : 108,P.C : 618<br/>
    GHALA, MUSCATER<br/>
    SULTANATE OF OMAN<br/>
    VATN : OM1100101048<br/>
    Contact : +986 24035989, +968 93355707<br/>
    E-Mail: rabwa.fahud@gmail.com<br/>
    Website: www.rabwafahud.com"""
    
    customer_name = customer.ledger_name if customer and customer.ledger_name else "."
    customer_trn = customer.trn_number if customer and customer.trn_number else "."
    customer_mobile = customer.mobile if customer and customer.mobile else "."
    customer_email = customer.email if customer and customer.email else "."
    
    to_text = f"""<b>To:</b><br/>
    {customer_name}<br/>
    CR NO : {customer_trn}<br/>
    GSM : {customer_mobile}<br/>
    Email : {customer_email}<br/>
    <br/>
    <b>Hiring Period :</b> ______"""

    from_to_data = [[
        Paragraph(from_text, styles['Normal']),
        Paragraph(to_text, styles['Normal'])
    ]]
    
    from_to_table = Table(from_to_data, colWidths=[255, 255])
    from_to_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(from_to_table)
    story.append(Spacer(1, 12))

    # === TITLE ===
    title = Paragraph("<b><font size=14>QUOTATION</font></b>", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 12))

    # === GREETING ===
    story.append(Paragraph("Dear Sir,", styles["Normal"]))
    story.append(Paragraph(
        "We would like to submit to you our best discount price quotation, kindly confirm waiting for your reply.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === DETAILS TABLE ===
    details = quotation.details.all()
    detail_data = [["SI", "DESCRIPTION", "QTY", "UNIT", "RENT"]]
    total_amount = 0

    for idx, d in enumerate(details, start=1):
        row_total = d.quantity * d.rent
        total_amount += row_total
        detail_data.append([
            f"{idx:02d}",
            d.description.upper(),
            f"{d.quantity} Nos",
            d.period,  # Added UNIT column with period value
            f"{d.rent:.3f}",
        ])

    detail_data.append(["", "VAT - 5% APPLIED WITH INVOICE", "", "", "0.000"])
    detail_data.append(["", "GRAND TOTAL", "", "", f"{total_amount:.3f}"])

    detail_table = Table(detail_data, colWidths=[40, 240, 80, 80, 80])  # Adjusted widths
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),  # Aligns QTY, UNIT, and RENT columns
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TERMS & CONDITIONS ===
    story.append(Paragraph("<b>Terms & Conditions</b>", styles["Heading4"]))
    terms = [
        "• Vehicle will be provided as per PDO-OPAL specifications.",
        "• Payment terms 45 days from the date of invoice submission.",
        "• Fuel for the vehicle provided by your scope.",
        "• Maximum working normal day 10 hours/day or 260 hrs/month additional working time will be charged as overtime.",
        "• Mobilization & Demobilization will be provided by your scope.",
        "• Demobilization notice give 1 month prior. Vehicle maintenance is our scope."
    ]
    for term in terms:
        story.append(Paragraph(term, styles["Normal"]))
    story.append(Spacer(1, 12))

    # === Footer Function: ALWAYS RUNS - Computer Generated Text + Optional Signature ===
    def footer_func(canvas, doc):
        """
        ALWAYS draws (regardless of enable_footer):
        - Computer generated text
        Conditionally draws signature image if enabled
        """
        canvas.saveState()
        
        
        # Draw signature image if enabled
        if quotation.enable_signature:
            signature_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'sign.jpg')
            
            if os.path.exists(signature_image_path):
                sig_img_y = 2.2 * inch
                sig_img_x = 1 * inch
                sig_img_width = 3 * inch
                sig_img_height = 0.8 * inch
                
                canvas.drawImage(
                    signature_image_path,
                    sig_img_x,
                    sig_img_y,
                    width=sig_img_width,
                    height=sig_img_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
        
        canvas.restoreState()

    # === Build PDF ===
    # logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'TS_head.jpg')
    # footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'RFT_footer.png')
    
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'azure_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'azure_footer.jpeg')

    
    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=quotation.enable_header,      # Top logo image
        include_footer=quotation.enable_footer,      # Bottom footer image
        footer_func=footer_func,                      # ALWAYS runs (computer text + signature)
        footer_on_last_page=True,
        footer_image_path=footer_image_path if quotation.enable_footer else None,  # Only include footer image if enabled
        doc_type="quotation",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="quotation_{quotation.voucher_no}.pdf"'
    response.write(pdf)
    return response


def create_invoice_pdf(invoice):
    """
    Build and return PDF response for Invoice.
    
    Components:
    - Header: Top logo image (enable_header) - TS_head.jpg
    - Footer: Bottom footer image (enable_footer) - RFT_footer.png
    - Signature: Signature image above footer (enable_signature) - sign.jpg
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # ==== COMPANY & CUSTOMER BLOCK ====
    from_text = """<b>From:</b><br/>
    RABWA FAHOUD TRAD & TRANSPORT CO SPC<br/>
    CR NO : 5029392<br/>
    P.O Box : 108, P.C : 618<br/>
    GHALA, MUSCAT<br/>
    SULTANATE OF OMAN<br/>
    VATN : OM1100101048<br/>
    Contact : +968 24035989, +968 93355707<br/>
    E-Mail: rabwa.fahud@gmail.com<br/>
    Website: www.rabwafahud.com"""

    customer = invoice.customer
    to_text = f"""<b>To:</b><br/>
    {customer.ledger_name if customer else ''}<br/>
    Mobile: {customer.mobile if customer else ''}<br/>
    TR No: {customer.trn_number if customer else ''}<br/>
    Email: {customer.email if customer else ''}<br/>"""

    from_para = Paragraph(from_text, styles["Normal"])
    to_para = Paragraph(to_text, styles["Normal"])

    left_data = [[from_para], [Spacer(1, 10)], [to_para]]
    left_table = Table(left_data, colWidths=[280])

    right_data = [
        ["Invoice No:", invoice.voucher_no],
        ["Date:", invoice.date.strftime("%d-%m-%Y")],
        ["Mode of Payment:", invoice.payment_mode or ""],
        ["Supplier Ref:", invoice.supplier_ref or ""],
        ["Other Ref:", invoice.other_ref or ""],
        ["PO:", invoice.buyer_order_no or ""],
    ]
    right_table = Table(right_data, colWidths=[130, 130])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    invoice_title = "TAX INVOICE" if invoice.is_taxable else "INVOICE"
    story.append(Paragraph(f"<b><font size=14>{invoice_title}</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE ===
    if invoice.is_taxable:
        detail_data = [["Particulars", "Amount (OMR)", "VAT (OMR)", "Total (OMR)"]]
    else:
        detail_data = [["Particulars", "Amount (OMR)"]]
    
    total_amount = 0
    total_vat = 0

    for d in invoice.details.all():
        if hasattr(d, 'vehicle') and d.vehicle:
            plate_code = getattr(d.vehicle, 'license_plate_code', '') or ''
            plate_number = getattr(d.vehicle, 'license_plate_number', '') or ''
            license_text = f"{plate_number}-{plate_code}" if plate_number or plate_code else ''
            vehicle_name = str(d.vehicle.model.model_name).upper()

            location_text = getattr(d, 'location', '') or ''
            if location_text:
                particulars_html = f"""
                    <b>{vehicle_name}</b> - {license_text}<br/>
                    <font size="10" color="grey"><i>{location_text}</i></font>
                """
            else:
                particulars_html = f"<b>{vehicle_name}</b> - {license_text}"
        else:
            desc_text = d.description or ''
            particulars_html = f"{desc_text.upper()}"

        particulars = Paragraph(particulars_html, styles["Normal"])

        amount = float(d.amount)
        vat = float(d.tax_amount or 0)
        total = amount + vat
        total_amount += amount
        total_vat += vat

        if invoice.is_taxable:
            detail_data.append([
                particulars,
                f"{amount:.3f}",
                f"{vat:.3f}",
                f"{total:.3f}",
            ])
        else:
            detail_data.append([
                particulars,
                f"{amount:.3f}",
            ])

    grand_total = total_amount + total_vat
    
    if invoice.is_taxable:
        detail_data.append([
            "",
            "",
            "Net Total",
            f"{total_amount:.3f}"
        ])
        detail_data.append([
            Paragraph("OUTPUT VAT@5%", styles["Normal"]),
            "",
            "Tax Total",
            f"{total_vat:.3f}"
        ])
        detail_data.append([
            "",
            "",
            "Total",
            f"{grand_total:.3f}"
        ])
        
        detail_table = Table(detail_data, colWidths=[300, 80, 80, 80])
        detail_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (-2, -2), (-1, -2), 'Helvetica-Bold'),
            ('FONTNAME', (-2, -3), (-1, -3), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
    else:
        detail_data.append(["Net Total", f"{total_amount:.3f}"])
        
        detail_table = Table(detail_data, colWidths=[380, 160])
        detail_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
    
    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    total_words = num2words(round(grand_total, 3), to='cardinal', lang='en').capitalize()
    story.append(Paragraph(
        f"<b>Amount (in words):</b> Omani Rial {total_words} Only (OMR {grand_total:.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === DECLARATION ===
    story.append(Paragraph("<b>Declaration:</b>", styles["Heading4"]))
    story.append(Paragraph(
        "We declare that this invoice shows the actual price of the goods described and that all particulars are true and correct.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        """
        Conditionally draws signature image if enabled
        NOTE: Computer generated text is handled by build_pdf, not here
        """
        canvas.saveState()
        
        # Draw signature image if enabled
        if invoice.enable_signature:
            signature_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'sign.jpg')
            
            if os.path.exists(signature_image_path):
                sig_img_y = 2.2 * inch
                sig_img_x = 1 * inch
                sig_img_width = 3 * inch
                sig_img_height = 0.8 * inch
                
                canvas.drawImage(
                    signature_image_path,
                    sig_img_x,
                    sig_img_y,
                    width=sig_img_width,
                    height=sig_img_height,
                    preserveAspectRatio=True,
                    mask='auto'
                )
        
        canvas.restoreState()

    # === BUILD PDF ===
    # logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'TS_head.jpg')
    # footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'RFT_footer.png')
    
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'azure_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'azure_footer.jpeg')

    
    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=invoice.enable_header,             # Top logo image
        include_footer=True,                               # ALWAYS True so footer_func runs
        footer_func=footer_func,                           # ALWAYS runs (computer text + signature)
        footer_on_last_page=True,
        footer_image_path=footer_image_path if invoice.enable_footer else None,  # Footer image only if enabled
        doc_type="invoice",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{invoice.voucher_no}.pdf"'
    response.write(pdf)
    return response