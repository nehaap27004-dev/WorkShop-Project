# reports.py
from decimal import Decimal
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_RIGHT
from django.conf import settings
from fleet_app.common import build_pdf
from num2words import num2words
import os
styles = getSampleStyleSheet()
from reportlab.platypus.flowables import KeepTogether



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
        ['Project Location:', timesheet.project_location, 'Duration:', str(timesheet.duration)],
        ['Date:', timesheet.date.strftime('%Y-%m-%d'), 'PO Reference:', timesheet.PO_reference_no or ''],
        ['Description:', timesheet.description or '', '', ''],
    ]

    page_width, _ = A4
    side_margin = 0.6 * inch
    usable_width = page_width - (2 * side_margin)

    header_table = Table(
        timesheet_data,
        colWidths=[usable_width * 0.25] * 4,
    )
    header_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),  # Outer border
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),  # Inner grid lines
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONT', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Span description field across remaining columns
        ('SPAN', (1, 3), (3, 3)),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # === Separate Rows for Long Data Fields ===
    # Client Row
    client_data = [['Client:', str(timesheet.client)]]
    client_table = Table(
        client_data,
        colWidths=[usable_width * 0.25, usable_width * 0.75],
    )
    client_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 4))

    # Driver Name Row
    driver_data = [['Driver Name:', str(timesheet.driver_name)]]
    driver_table = Table(
        driver_data,
        colWidths=[usable_width * 0.25, usable_width * 0.75],
    )
    driver_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(driver_table)
    story.append(Spacer(1, 4))

    # Operator Name Row
    operator_data = [['Operator Name:', str(timesheet.operator_name or '')]]
    operator_table = Table(
        operator_data,
        colWidths=[usable_width * 0.25, usable_width * 0.75],
    )
    operator_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(operator_table)
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

    # Calculate grand totals for ALL dates (left + right columns combined)
    grand_total_normal = sum(d.total_hours_worked for d in all_details_list)
    grand_total_ot = sum(d.ot for d in all_details_list)
    grand_total_hours = grand_total_normal + grand_total_ot

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

    # Add total row - only in right section (showing grand total of all dates)
    total_row = [
        '',  # Empty left DATE
        '',  # Empty left NORMAL HOURS
        '',  # Empty left OT
        '',  # Empty left TOTAL HOURS
        '',  # Empty left REMARKS
        '',  # Divider
        'TOTAL',  # Right DATE shows "TOTAL"
        str(grand_total_normal) if grand_total_normal else '0',
        str(grand_total_ot) if grand_total_ot else '0',
        str(grand_total_hours) if grand_total_hours else '0',
        '',  # Empty right REMARKS
    ]
    detail_data.append(total_row)

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
        # Total row styling (last row) - only right section styled
        ('FONT', (6, -1), (10, -1), 'Helvetica-Bold'),  # Right section bold
        ('BACKGROUND', (6, -1), (10, -1), colors.lightgrey),  # Right total background
        ('ALIGN', (6, -1), (6, -1), 'CENTER'),  # Right "TOTAL" text centered
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
        y_text_labels = 1.0 * inch
        
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
    
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

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
    
     # === TITLE ===
    title = Paragraph("<b><font size=14>QUOTATION</font></b>", styles["Title"])
    story.append(title)
    story.append(Spacer(1, 12))

    # # === QUOTATION NUMBER AND DATE HEADER ===
    # blue_style = ParagraphStyle(
    #     'BlueHeader',
    #     parent=styles['Normal'],
    #     textColor=colors.HexColor('#1E3A8A'),
    #     fontSize=11,
    #     fontName='Helvetica-Bold'
    # )
    
    # date_style = ParagraphStyle(
    #     'DateHeader',
    #     parent=styles['Normal'],
    #     fontSize=10,
    #     fontName='Helvetica',
    #     alignment=TA_RIGHT
    # )

    # quote_header_data = [[
    #     Paragraph(f"{quotation.voucher_no}", blue_style),
    #     Paragraph(quotation.date.strftime("%d-%m-%Y"), date_style)
    # ]]
    
    # quote_header_table = Table(quote_header_data, colWidths=[300, 210])
    # quote_header_table.setStyle(TableStyle([
    #     ('ALIGN', (0, 0), (0, 0), 'LEFT'),
    #     ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    #     ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    #     ('TOPPADDING', (0, 0), (-1, -1), 0),
    #     ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    # ]))
    # story.append(quote_header_table)
    # story.append(Spacer(1, 8))

    # === FROM AND TO SECTION ===
    customer = quotation.customer
    
    customer_name = customer.ledger_name if customer and customer.ledger_name else "."
    customer_mobile = customer.mobile if customer and customer.mobile else "."
    customer_email = customer.email if customer and customer.email else "."
    attention = quotation.attention if quotation and quotation.attention else "."
    attention_contact = quotation.attention_contact if quotation and quotation.attention_contact else "."
    address = customer.address1 if customer and customer.address1 else "."
    mobile = customer.mobile if customer and customer.mobile else "."

    # --- Left Box: Customer Details ---
    to_text = f"<b>To:</b><br/>"
    to_text += f"<b>{customer_name}</b><br/>"
    to_text += f"<b>GSM : </b>{mobile}<br/>"
    to_text += f"<b>Address : </b>{address}<br/>"
    to_text += f"<b>Email : </b>{customer_email}<br/>"
    to_text += f"<b>Attention : </b>{attention}<br/>"
    to_text += f"<b>Contact : </b>{attention_contact}<br/>"
    

    # --- Right Box: Quotation Info ---
    staff = getattr(quotation, 'staff', None)
    staff_name = staff.full_name if staff else "___________"
    contact = staff.contact_number if staff and hasattr(staff, 'contact_number') else "___________"

    ref_text = f"<b>Quotation No :</b> {quotation.voucher_no}<br/>"
    ref_text += f"<b>Date :</b> {quotation.date.strftime('%d-%m-%Y')}<br/>"
    ref_text += f"<b>From :</b> {staff_name}<br/>"
    ref_text += f"<b>GSM :</b> {contact}<br/>"

    # --- Two-column Table ---
    from_to_data = [[
        Paragraph(to_text,styles["Normal"]),
        Paragraph(ref_text, styles["Normal"]),
    ]]

    from_to_table = Table(from_to_data, colWidths=[300, 210])
    from_to_table.setStyle(TableStyle([
        ('BOX',          (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID',    (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 8),
    ]))
    story.append(from_to_table)
    story.append(Spacer(1, 12))

   

    # === GREETING ===
    story.append(Paragraph("Dear Sir,", styles["Normal"]))
    story.append(Paragraph(
        "We would like to submit to you our best discount price quotation, kindly confirm waiting for your reply.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === DETAILS TABLE ===
    details = quotation.details.select_related('vehicle', 'vehicle__model', 'vehicle__license_plate_code').all()
    
    # Updated header with tax_amount and total_amount columns
    detail_data = [["SI", "DESCRIPTION", "QTY", "UNIT", "RENT", "TAX (5%)", "TOTAL"]]
    
    subtotal_amount = 0
    total_tax_amount = 0
    grand_total = 0

    for idx, d in enumerate(details, start=1):
        # Get tax_amount and total_amount from the detail object
        tax_amt = d.tax_amount if hasattr(d, 'tax_amount') else Decimal('0')
        total_amt = d.total_amount if hasattr(d, 'total_amount') else (d.quantity * d.rent)
        
        subtotal_amount += (d.quantity * d.rent)
        total_tax_amount += tax_amt
        grand_total += total_amt
        
        # Build description with vehicle info if available
        if hasattr(d, 'vehicle') and d.vehicle:
            vehicle = d.vehicle
            vehicle_model = str(vehicle.model.model_name).upper() if vehicle.model else ''
            
            
            # Build description HTML with description at top and vehicle info below
            if d.description.strip():
                description_html = f"""
                    <b>{d.description.upper()}</b><br/>
                    <font size="9" color="grey"><i>{vehicle_model}</i></font>
                """
            else:
                description_html = f"<b>{vehicle_model}</b>"
            
            description_para = Paragraph(description_html, styles["Normal"])
        else:
            # No vehicle, just show description
            description_para = d.description.upper()
        
        detail_data.append([
            f"{idx:02d}",
            description_para,
            f"{d.quantity} Nos",
            d.period,
            f"{d.rent:.3f}",
            f"{tax_amt:.3f}",
            f"{total_amt:.3f}",
        ])

    # Add VAT row with actual total tax amount
    detail_data.append([
        "", 
        "VAT - 5% APPLIED WITH INVOICE", 
        "", 
        "", 
        "", 
        f"{total_tax_amount:.3f}",
        ""
    ])
    
    # Add GRAND TOTAL row
    detail_data.append([
        "", 
        "GRAND TOTAL", 
        "", 
        "", 
        "", 
        "", 
        f"{grand_total:.3f}"
    ])

    # Updated column widths to fit all columns
    detail_table = Table(detail_data, colWidths=[30, 180, 60, 50, 60, 60, 80])
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),  # Aligns QTY, UNIT, RENT, TAX, and TOTAL columns
        ('FONTNAME', (1, -2), (-1, -2), 'Helvetica-Bold'),  # VAT row
        ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),  # GRAND TOTAL row
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 12))

    # Add this near your other ParagraphStyle definitions (top of the function)
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading4'],
        keepWithNext=0,          # ← This is the key fix
        spaceAfter=6,
        spaceBefore=6,
    )

    # === TERMS & CONDITIONS ===
    if quotation.terms_and_condition:
        for term in quotation.terms_and_condition.split('\n'):
            if term.strip():
                story.append(Paragraph(term, styles["Normal"]))
        story.append(Spacer(1, 12))

    # =========================================================================
    # === SIGNATURE BOXES ===
    # =========================================================================
    
    sig_left_text = Paragraph("<b>Customers Seal and Signature</b>", styles["Normal"])
    sig_right_text = Paragraph("<b>For Silver Line Group Business</b>", styles["Normal"])
    
    sig_data = [[sig_left_text, sig_right_text]]
    
    sig_table = Table(sig_data, colWidths=[270, 270], rowHeights=[70])
    
    sig_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(sig_table)    

    # # === REMARK ===
    # if quotation.remark:
    #     story.append(Paragraph("<b>Remark</b>", section_heading_style))  # ← changed
    #     for remark_line in quotation.remark.split('\n'):
    #         if remark_line.strip():
    #             story.append(Paragraph(remark_line, styles["Normal"]))
    #     story.append(Spacer(1, 12))

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
    
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    
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
    response["Content-Disposition"] = f'inline; filename="quotation_{quotation.quotation_no}.pdf"'
    response.write(pdf)
    return response

def create_invoice_pdf(invoice):
    """
    Build and return PDF response for Invoice.
    
    Components:
    - Header: Top logo image (enable_header) - TS_head.jpg
    - Footer: Bottom footer image (enable_footer) - RFT_footer.png
    - Signature: Signature image above footer (enable_signature) - sign.jpg
    
    Supports both Simple and Complex invoice types.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    
    customer = invoice.customer
    to_text = f"""<b>To:</b><br/>
    {customer.ledger_name if customer else ''}<br/>
    Mobile: {customer.mobile if customer else ''}<br/>
    Address: {customer.address1 if customer else ''}<br/>
    VATIN: {customer.trn_number if customer else ''}<br/>
    E-Mail: {customer.email if customer else ''}<br/>"""


    to_para = Paragraph(to_text, styles["Normal"])

    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Different for Simple vs Complex ===
    if invoice.invoice_type == 'complex':
        # Complex invoice - include additional fields
        right_data = [
            ["Invoice No:", invoice.voucher_no],
            ["Date:", invoice.date.strftime("%d-%m-%Y")],
            ["LPO Date:", invoice.lpo_date.strftime("%d-%m-%Y") if invoice.lpo_date else ""],
            ["Hire Contract No:", invoice.hire_contract_no or ""],
            ["Location:", invoice.location or ""],
            ["Mode of Payment:", invoice.payment_mode or ""],
            ["PO:", invoice.buyer_order_no or ""],
        ]
    else:
        # Simple invoice - original fields
        right_data = [
            ["Invoice No:", invoice.voucher_no],
            ["Date:", invoice.date.strftime("%d-%m-%Y")],
            ["Mode of Payment:", invoice.payment_mode or ""],
            ["PO:", invoice.buyer_order_no or ""],
        ]
    
    right_table = Table(right_data, colWidths=[120, 120])
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

    # === DETAILS TABLE: Different structure for Simple vs Complex ===
    if invoice.invoice_type == 'complex':
        # Complex invoice table headers - NEW ORDER: Particulars, Qty, Period, Unit Rate, Amount, VAT, Total
        if invoice.is_taxable:
            detail_data = [["Particulars", "Qty", "Units", "Unit Rate", "Amount", "VAT", "Total"]]
            col_widths = [180, 40, 60, 60, 60, 60, 80]
        else:
            detail_data = [["Particulars", "Qty", "Period", "Rate", "Amount"]]
            col_widths = [240, 60, 80, 80, 80]
    else:
        # Simple invoice table headers
        if invoice.is_taxable:
            detail_data = [["Particulars", "Amount", "VAT", "Total"]]
            col_widths = [300, 80, 80, 80]
        else:
            detail_data = [["Particulars", "Amount"]]
            col_widths = [380, 160]
    
    total_amount = 0
    total_vat = 0

    for d in invoice.details.all():
        # Build particulars text
        if hasattr(d, 'vehicle') and d.vehicle:
            plate_code = getattr(d.vehicle, 'license_plate_code', '') or ''
            plate_number = getattr(d.vehicle, 'license_plate_number', '') or ''
            license_text = f"{plate_code}-{plate_number}" if plate_code or plate_number else ''
            vehicle_name = str(d.vehicle.vehicle_name).upper()
            vehicle_type = str(d.vehicle.vehicle_category.category_name).upper()
            from_date = getattr(d, 'from_date', '') or ''
            to_date = getattr(d, 'to_date', '') or ''
            date = f"From {from_date} To {to_date}" if from_date and to_date else ''

            location_text = getattr(d, 'location', '') or ''
        
            # Build particulars HTML based on invoice type
            if invoice.invoice_type == 'complex':
                # Complex invoice - include location and date range
                particulars_parts = [f"<b>{vehicle_name}</b> - {vehicle_type}-{license_text}"]
                
                
                    
                if date:
                    particulars_parts.append(date)
                
                particulars_html = "<br/>".join(particulars_parts)
            else:
                # Simple invoice - original format (no dates)
                if location_text:
                    particulars_html = f"""
                        <b>{vehicle_name}</b> - {vehicle_type}-{license_text}<br/>
                        
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

        # Build row based on invoice type
        if invoice.invoice_type == 'complex':
            # Complex invoice - NEW ORDER: Particulars, Qty, Period, Unit Rate, Amount, VAT, Total
            period_display = str(d.period).capitalize() if d.period else ""
            quantity = float(d.quantity) if d.quantity else 0
            unit_rate = float(d.unit_rate) if d.unit_rate else 0
            
            if invoice.is_taxable:
                detail_data.append([
                    particulars,
                    f"{quantity:.2f}",
                    period_display,
                    f"{unit_rate:.3f}",
                    f"{amount:.3f}",
                    f"{vat:.3f}",
                    f"{total:.3f}",
                ])
            else:
                detail_data.append([
                    particulars,
                    f"{quantity:.2f}",
                    period_display,
                    f"{unit_rate:.3f}",
                    f"{amount:.3f}",
                ])
        else:
            # Simple invoice - original format
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
    
    # Add totals rows based on invoice type and tax settings
    if invoice.invoice_type == 'complex':
        if invoice.is_taxable:
            detail_data.append([
                "",
                "",
                "",
                "",
                "",
                "Net Total",
                f"{total_amount:.3f}"
            ])
            detail_data.append([
                Paragraph("OUTPUT VAT@5%", styles["Normal"]),
                "",
                "",
                "",
                "",
                "Tax Total",
                f"{total_vat:.3f}"
            ])
            detail_data.append([
                "",
                "",
                "",
                "",
                "",
                "Total",
                f"{grand_total:.3f}"
            ])
        else:
            detail_data.append([
                "",
                "",
                "",
                "Net Total",
                f"{total_amount:.3f}"
            ])
    else:
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
        else:
            detail_data.append(["Net Total", f"{total_amount:.3f}"])
    
    # Create table with appropriate column widths
    detail_table = Table(detail_data, colWidths=col_widths)
    
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTNAME', (-2, -2), (-1, -2), 'Helvetica-Bold'),
        ('FONTNAME', (-2, -3), (-1, -3), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    # Split amount into Riyal (integer) and Baisa (decimal) parts
    riyal_part = int(grand_total)
    baisa_part = int(round((grand_total - riyal_part) * 1000))  # Convert decimal to baisa (1 OMR = 1000 Baisa)

    # Convert to words
    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {grand_total:.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === DECLARATION ===
    story.append(Paragraph("<b>Declaration:</b>", styles["Heading4"]))
    story.append(Paragraph(
        "Discrepancies if any, Should be notified to us within 7 days from the invoice submission date.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 20))

    # =========================================================================
    # === SIGNATURE BOXES ===
    # =========================================================================
    
    # Left content
    sig_left_text = Paragraph("<b>Customers Seal and Signature</b>", styles["Normal"])
    
    # Right content
    sig_right_text = Paragraph("<b>For Silver Line Group Business</b>", styles["Normal"])
    
    # Data row
    sig_data = [[sig_left_text, sig_right_text]]
    
    # Create Table
    sig_table = Table(sig_data, colWidths=[270, 270], rowHeights=[70])
    
    # Styling for the boxes
    sig_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(sig_table)
    # =========================================================================

    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        """
        Conditionally draws signature image if enabled
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
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')
    
    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=invoice.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if invoice.enable_footer else None,
        doc_type="invoice",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="invoice_{invoice.invoice_no}.pdf"'
    response.write(pdf)
    return response

def create_delivery_contract_pdf(contract):
    """
    Build and return PDF response for Delivery Contract.
    
    Components:
    - Header: Top logo image (enable_header)
    - Footer: Bottom footer image (enable_footer)
    - Signature: Signature image (enable_signature)
    - Hire Details Box
    - Off-Hire Note Box
    
    Structure matches create_invoice_pdf exactly.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # ==== CUSTOMER BLOCK (No FROM address) ====
    customer = contract.customer
    to_text = f"""<b>Customer Details:</b><br/>
    {customer.ledger_name if customer else ''}<br/>
    Mobile: {customer.mobile if customer else ''}<br/>
    Address: {customer.address1 if customer else ''}<br/>
    E-Mail: {customer.email if customer else ''}<br/><br/>
    Ordered By: {contract.other_ref or ''} <br/>
    LPO No : {contract.buyer_order_no or ''} <br/>
    """

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Contract Information ===
    right_data = [
        ["Hire Contract No:", contract.voucher_no or ""],
        ["Hire Contract Date:", contract.date.strftime("%d-%m-%Y") if contract.date else ""],
        ["From:", contract.salesman.full_name if contract.salesman else ""],
        ["Delivery Person:", contract.delivery_person if contract.delivery_person else ""],
        ["Ref:", contract.ref_no or ""],
    ]
    
    right_table = Table(right_data, colWidths=[120, 120])
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

    # Title
    story.append(Paragraph("<b><font size=14>DELIVERY CONTRACT</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === EQUIPMENT DETAILS TABLE ===
    # Create a custom style for the headers to ensure they are bold and centered
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold',
        alignment=1, # 1 is for Center
        leading=10,  # Space between the stacked lines
    )

    # Wrap the long titles in Paragraphs to force them to stack "up and down"
    detail_data = [[
        Paragraph("SI No", header_style),
        Paragraph("Equipment<br/>Id No", header_style),
        Paragraph("Description", header_style),
        Paragraph("Make", header_style),
        Paragraph("Replacement<br/>Value", header_style),
        Paragraph("Qty", header_style)
    ]]
    
    # Use select_related for better performance
    contract_details = contract.details.select_related('vehicle', 'vehicle__model', 'vehicle__model__manufacturer').all()

    for idx, d in enumerate(contract_details, start=1):
        equipment_id = ""
        description = d.location or ""
        make = ""
        replacement_value = ""
        quantity = "0"
        
        if d.vehicle:
            # Equipment ID logic
            plate_code = getattr(d.vehicle, 'license_plate_code', '') or ''
            plate_number = getattr(d.vehicle, 'license_plate_number', '') or ''
            equipment_id = f"{plate_code}-{plate_number}" if plate_code or plate_number else str(d.vehicle.vehicle_name)
            
            # Make logic
            if d.vehicle.model and d.vehicle.model.manufacturer:
                make = str(d.vehicle.model.manufacturer.manufacturer_name).upper()
            
            # Quantity logic
            if d.quantity:
                quantity = f"{float(d.quantity):.0f}"

            # Replacement Value logic
            if d.vehicle and hasattr(d.vehicle, 'replacement_value') and d.vehicle.replacement_value:
                replacement_value = f"{float(d.vehicle.replacement_value):.3f}"
            else:
                replacement_value = "0.000"
        
        detail_data.append([
            str(idx),
            equipment_id,
            Paragraph(description, styles["Normal"]), # Paragraph here prevents layout errors if description is long
            make,
            replacement_value,
            quantity,
        ])

    # === ADD EMPTY ROW AT BOTTOM ===
    detail_data.append([
        "",   # SI No
        "",   # Equipment Id
        "",   # Description
        "",   # Make
        "",   # Replacement Value
        ""    # Qty
    ])    
    detail_table = Table(
        detail_data,
        colWidths=[30, 90, 180, 90, 90, 60],
        rowHeights=[None] * (len(detail_data) - 1) + [25]  # last row taller
    )
    # Column widths (Total 540)
    detail_table = Table(detail_data, colWidths=[30, 90, 180, 90, 90, 60])
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Keeps text centered vertically
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),   # Centers the header row
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),   # Centers SI No column
        ('ALIGN', (4, 1), (5, -1), 'CENTER'),   # Centers Value and Qty columns
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, 0), 8),     # Extra padding for the taller header
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ]))
    
    story.append(detail_table)
    story.append(Spacer(1, 15))

    # === COMBINED HIRE DETAILS & SIGNATURE BOX ===
    hire_date = contract.onhire_date_time.strftime("%d-%m-%Y") if contract.onhire_date_time else ""
    hire_time = contract.onhire_date_time.strftime("%H:%M") if contract.onhire_date_time else ""
    site_location = contract.location or ""
    site_contact = contract.site_contact_person or ""
    contact_no = contract.contact_no or ""

    # 1. Define the content for the combined table
    # We use Paragraphs for the text to prevent LayoutErrors
    combined_hire_data = [
        # Row 0: Header Text (Spanned)
        [Paragraph("<b>The above offered/delivered for hire as per the terms and conditions of the contract</b>", styles["Normal"]), ""],
        # Row 1-3: Hire Details
        [f"On Hire Date: {hire_date}", f"On Hire Time: {hire_time}"],
        [f"Site Location: {site_location}", f"Contact No: {contact_no}"],
        [f"Site Contact Person: {site_contact}", ""],
        # Row 4: Signature Labels
        [Paragraph("<b>Silver Line Group (as Owner)</b>", styles["Normal"]), 
         Paragraph("<b>Hirer's Name</b>", styles["Normal"])],
        # Row 5: Signature Lines (Tall row)
        [Paragraph("<br/><br/>Signature: ", styles["Normal"]), 
         Paragraph("<br/><br/>Signature: ", styles["Normal"])]
    ]

    # 2. Create the Table
    # rowHeights: None for auto, 70 for the signature area
    hire_combined_table = Table(combined_hire_data, colWidths=[270, 270], rowHeights=[None, None, None, None, None, 60])

    # 3. Apply Styles to create the "Single Box" look
    hire_combined_table.setStyle(TableStyle([
        # Outer Border for the whole box
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        
        # Header Styling
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.whitesmoke),
        ('BOTTOMPADDING', (0, 0), (1, 0), 8),
        
        # Details Styling
        ('FONTNAME', (0, 1), (-1, 3), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, 3), 9),
        
        # Signature Section Styling
        ('LINEABOVE', (0, 4), (-1, 4), 0.5, colors.black), # Line to separate details from signatures
        ('LINEBEFORE', (1, 4), (1, 5), 0.5, colors.black), # Vertical line between Owner and Hirer
        ('VALIGN', (0, 4), (-1, 5), 'TOP'),
        
        # General Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(hire_combined_table)
    story.append(Spacer(1, 20))

    # === TERMS & CONDITIONS ===
    if contract.terms_and_condition:
        for term in contract.terms_and_condition.split('\n'):
            if term.strip():
                story.append(Paragraph(term, styles["Normal"]))
        story.append(Spacer(1, 12))

    
    # === Footer Function ===
    def footer_func(canvas, doc):
        """
        Conditionally draws signature image if enabled
        """
        canvas.saveState()
        
        # Draw signature image if enabled
        if contract.enable_signature:
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
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')
    
    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=contract.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if contract.enable_footer else None,
        doc_type="delivery_contract",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="delivery_contract_{contract.voucher_no}.pdf"'
    response.write(pdf)
    return response

# ─────────────────────────────────────────────────────────────
#  AMOUNT IN WORDS  (OMR)
# ─────────────────────────────────────────────────────────────
def _amount_in_words(amount):
    """Convert Decimal/float to 'OMR: X Rials And Y Baisa Only' string."""
    try:
        from num2words import num2words
        amount   = Decimal(str(amount))
        rials    = int(amount)
        baisa    = int(round((amount - rials) * 1000))   # OMR has 1000 baisa
        rial_txt = num2words(rials,  lang='en').title()
        if baisa:
            baisa_txt = num2words(baisa, lang='en').title()
            return f"OMR : {rial_txt} Rials And {baisa_txt} Baisa Only"
        return f"OMR : {rial_txt} Rials Only"
    except Exception:
        return f"OMR : {amount}"


# ─────────────────────────────────────────────────────────────
#  MAIN PDF FUNCTION
# ─────────────────────────────────────────────────────────────
def create_po_pdf(po):
    """
    Build and return an HttpResponse containing the PO PDF.

    Layout (matches screenshot):
      • Letterhead header image
      • Title  "PURCHASE ORDER"  +  VATIN right-aligned
      • Two-column info box  [Supplier details | PO details]
      • Line-items table  (SNo / Description / Units / Qty / Rate / Amount)
      • Amount-in-words  +  Delivery Date
      • Totals block  (Gross / Taxable Amt / VAT 5% / Grand Total)
      • Signatures row  (Prepared By | Silver Line Global Business)
      • Footer image
    """
    buffer = BytesIO()
    story  = []
    styles = getSampleStyleSheet()

    normal   = styles["Normal"]
    centered = ParagraphStyle('centered', parent=normal, alignment=1)
    bold9    = ParagraphStyle('bold9',    parent=normal, fontName='Helvetica-Bold', fontSize=9)
    reg9     = ParagraphStyle('reg9',     parent=normal, fontName='Helvetica',      fontSize=9)
    bold10   = ParagraphStyle('bold10',   parent=normal, fontName='Helvetica-Bold', fontSize=10)

    # ── helpers ──────────────────────────────────────────────
    def safe(val, default=''):
        return str(val) if val else default

    supplier = po.supplier   # LedgerCreation FK

    # ── VATIN line (right-aligned beside title) ───────────────
    vatin = safe(getattr(supplier, 'vat_id', '') or getattr(supplier, 'vat_no', ''))
    title_data = [[
        Paragraph("<b><font size=14>PURCHASE ORDER</font></b>", centered),
        # Paragraph(f"<b>VATIN : {vatin}</b>", ParagraphStyle('right', parent=normal, alignment=2, fontSize=9)),
    ]]
    title_table = Table(title_data, colWidths=[380, 160])
    title_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(title_table)
    story.append(Spacer(1, 10))

    # ── TWO-COLUMN INFO BOX ───────────────────────────────────
    #  Left: supplier details
    left_text = f"""<b>NAME</b>   :  {safe(supplier.ledger_name)}<br/>
<b>Address</b>  :  {safe(getattr(supplier, 'address1', ''))}<br/>
<br/>
<b>Tel No</b>   :  {safe(getattr(supplier, 'mobile', ''))}<br/>
<b>Kind Attn</b>:  {safe(getattr(po, 'kind_attn', ''))}<br/>
<b>Email Id</b> :  {safe(getattr(supplier, 'email', ''))}<br/>
<b>Vat </b>   :  {safe(getattr(supplier, 'trn_number', ''))}"""
    left_para = Paragraph(left_text, reg9)

    #  Right: PO meta
    right_data = [
        [Paragraph("<b>PO No</b>",             bold9), Paragraph(f":  {safe(po.PO_no)}",             reg9)],
        [Paragraph("<b>PO Date</b>",           bold9), Paragraph(f":  {po.PO_date.strftime('%d/%m/%Y') if po.PO_date else ''}", reg9)],
        [Paragraph("<b>Quote Ref</b>",         bold9), Paragraph(f":  {safe(po.quote_ref)}",         reg9)],
        [Paragraph("<b>Quote Ref Date</b>",    bold9), Paragraph(f":  {po.quote_ref_date.strftime('%d/%m/%Y') if po.quote_ref_date else ''}", reg9)],
        [Paragraph("<b>Payment Terms 1</b>",   bold9), Paragraph(f":  {safe(po.payment_terms1)}",    reg9)],
        [Paragraph("<b>Payment Terms 2</b>",   bold9), Paragraph(f":  {safe(po.payment_terms2)}",    reg9)],
    ]
    right_table = Table(right_data, colWidths=[100, 140])
    right_table.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN',   (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING',    (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    info_box = Table([[left_para, right_table]], colWidths=[270, 270])
    info_box.setStyle(TableStyle([
        ('BOX',      (0,0), (-1,-1), 0.8, colors.black),
        ('LINEBEFORE',(1,0), (1,-1), 0.5, colors.black),
        ('VALIGN',   (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
    ]))
    story.append(info_box)
    story.append(Spacer(1, 12))

    # ── LINE ITEMS TABLE ──────────────────────────────────────
    hdr_style = ParagraphStyle('hdr', parent=normal, fontName='Helvetica-Bold',
                                fontSize=9, alignment=1)
    cell_r    = ParagraphStyle('cellr', parent=normal, fontSize=9, alignment=2)  # right
    cell_c    = ParagraphStyle('cellc', parent=normal, fontSize=9, alignment=1)  # center

    detail_rows = [[
        Paragraph("SNo",         hdr_style),
        Paragraph("Description", hdr_style),
        Paragraph("Units",       hdr_style),
        Paragraph("Qty",         hdr_style),
        Paragraph("Rate",        hdr_style),
        Paragraph("Amount",      hdr_style),
    ]]

    details = po.po_details.all()
    for idx, d in enumerate(details, 1):
        detail_rows.append([
            Paragraph(str(idx),                                    cell_c),
            Paragraph(safe(d.description),                         reg9),
            Paragraph(safe(d.units),                               cell_c),
            Paragraph(f"{float(d.quantity):.3f}",                  cell_r),
            Paragraph(f"{float(d.rate):.3f}",                      cell_r),
            Paragraph(f"{float(d.amount):.3f}",                    cell_r),
        ])

    # Add blank padding rows so the table looks like the sample (min 6 data rows)
    MIN_ROWS = 6
    while len(detail_rows) - 1 < MIN_ROWS:
        detail_rows.append(["", "", "", "", "", ""])

    detail_table = Table(
        detail_rows,
        colWidths=[30, 195, 55, 60, 80, 80],
        repeatRows=1,                          # repeat header on new pages
    )
    detail_table.setStyle(TableStyle([
        ('GRID',       (0,0), (-1,-1), 0.5, colors.black),
        ('BACKGROUND', (0,0), (-1,0),  colors.lightgrey),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWHEIGHT',  (0,1), (-1,-1), 18),
    ]))
    story.append(detail_table)
    story.append(Spacer(1, 10))

    # ── AMOUNT IN WORDS  +  DELIVERY DATE ────────────────────
    words_text = _amount_in_words(po.grand_total)
    delivery   = po.delivery_date.strftime('%d/%m/%Y') if po.delivery_date else '—'

    words_data = [
        [Paragraph(f"<b>{words_text}</b>", bold9), ""],
        [Paragraph(f"<b>Delivery Date :</b>  {delivery}", reg9), ""],
    ]
    words_table = Table(words_data, colWidths=[380, 160])
    words_table.setStyle(TableStyle([
        ('BOX',    (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN',   (0,0), (1,0)),
        ('SPAN',   (0,1), (1,1)),
        ('LEFTPADDING',  (0,0), (-1,-1), 8),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
    ]))

    # ── TOTALS BLOCK  (right-aligned) ────────────────────────
    gross    = po.taxable_amount           # Gross = sum of line amounts (before VAT)
    taxable  = po.taxable_amount
    vat_amt  = po.vat_amount
    grand    = po.grand_total

    totals_data = [
        ["Gross",        f"{float(gross):.3f}"],
        ["Taxable Amt",  f"{float(taxable):.3f}"],
        ["VAT 5%",       f"{float(vat_amt):.3f}"],
        [Paragraph("<b>Total</b>", bold9), Paragraph(f"<b>{float(grand):.3f}</b>", ParagraphStyle('rb', parent=normal, fontSize=9, alignment=2))],
    ]
    totals_table = Table(totals_data, colWidths=[80, 80])
    totals_table.setStyle(TableStyle([
        ('GRID',      (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN',     (1,0), (1,-1), 'RIGHT'),
        ('FONTSIZE',  (0,0), (-1,-1), 9),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,3), (-1,3), colors.lightgrey),
    ]))

    # Place words_table left, totals_table right on same row
    combined_row = Table(
        [[words_table, totals_table]],
        colWidths=[380, 160],
    )
    combined_row.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(combined_row)
    story.append(Spacer(1, 20))

    # ── SIGNATURES ROW ────────────────────────────────────────
    sig_data = [[
        Paragraph("For<br/><br/><br/><b>Prepared By</b>", reg9),
        Paragraph("For<br/><br/><br/><b>Silver Line Global Business</b><br/>Authorised Signature", reg9),
    ]]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('BOX',       (0,0), (-1,-1), 0.5, colors.black),
        ('LINEBEFORE',(1,0), (1, 0),  0.5, colors.black),
        ('VALIGN',    (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING',  (0,0), (-1,-1), 15),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 20),
    ]))
    story.append(KeepTogether([sig_table]))

    # ── FOOTER FUNC ───────────────────────────────────────────
    def footer_func(canvas, doc):
        pass   # no extra canvas drawing needed; footer image handled by build_pdf

    # ── BUILD PDF ─────────────────────────────────────────────
    logo_path          = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path  = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path,
        doc_type="purchase_order",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="PO_{po.PO_no}.pdf"'
    response.write(pdf)
    return response    