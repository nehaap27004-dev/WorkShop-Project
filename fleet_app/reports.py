# reports.py
from fleet_app.models import Invoice
from django.db.models import Sum
from accounts_app.models import DebitNoteDetail
from accounts_app.models import PaymentBillDetails
from asset_app.models import AssetMaster
from item_master.models import PurchaseMaster
from accounts_app.models import BillWiseOpening
from fleet_app.models import FleetHire
from accounts_app.common import build_customer_outstanding_data
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
from reportlab.lib.pagesizes import A4, landscape
styles = getSampleStyleSheet()
from reportlab.platypus.flowables import KeepTogether
from accounts_app.common import build_customer_pdc_list






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

    payment_mode_para = Paragraph(
        f"<b>Mode of Payment:</b> {invoice.payment_mode or ''}",
        styles["Normal"]
    )

    payment_terms_para = Paragraph(
        f"<b>Payment Terms:</b> {customer.payment_terms or ''}",   # Change field if needed
        styles["Normal"]
    )

    left_data = [
        [to_para],
        [Spacer(1, 8)],
        [payment_mode_para],
        [Spacer(1, 3)],
        [payment_terms_para],
    ]

    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Different for Simple vs Complex ===

    vat_para = Paragraph(
        "<para alignment='right'><b>VAT No:</b> OM1100340532</para>",
        styles["Normal"]
    )
    if invoice.invoice_type == 'complex':
        # Complex invoice - include additional fields
        right_data = [
            ["Invoice No:", invoice.voucher_no],
            ["Date:", invoice.date.strftime("%d-%m-%Y")],
            ["LPO Date:", invoice.lpo_date.strftime("%d-%m-%Y") if invoice.lpo_date else ""],
            ["Hire Contract No:", invoice.hire_contract_no or ""],
            ["Location:", invoice.location or ""],
            
            ["PO:", invoice.buyer_order_no or ""],
        ]
    else:
        # Simple invoice - original fields
        right_data = [
            ["Invoice No:", invoice.voucher_no],
            ["Date:", invoice.date.strftime("%d-%m-%Y")],
            
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

    right_section = Table(
        [
            [vat_para],
            [right_table],
        ],
        colWidths=[250]
    )

    right_section.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    header_table = Table(
        [[left_table, right_section]],
        colWidths=[290, 260]
    )

    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
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
            detail_data = [["Sl.No", "Particulars", "Qty", "Units", "Unit Rate", "Amount", "VAT", "Total"]]
            col_widths = [35, 145, 40, 60, 60, 60, 60, 80]
        else:
            detail_data = [["Sl.No", "Particulars", "Qty", "Period", "Rate", "Amount"]]
            col_widths = [35, 205, 60, 80, 80, 80]
    else:
        # Simple invoice table headers
        if invoice.is_taxable:
            detail_data = [["Sl.No", "Particulars", "Amount", "VAT", "Total"]]
            col_widths = [35, 265, 80, 80, 80]
        else:
            detail_data = [["Sl.No", "Particulars", "Amount"]]
            col_widths = [35, 345, 160]
    
    total_amount = 0
    total_vat = 0

    sl_no = 1

    for d in invoice.details.all():
        # Build particulars text
        if hasattr(d, 'vehicle') and d.vehicle:
            plate_code = getattr(d.vehicle, 'license_plate_code', '') or ''
            plate_number = getattr(d.vehicle, 'license_plate_number', '') or ''
            license_text = f"{plate_code}-{plate_number}" if plate_code or plate_number else ''
            vehicle_name = str(d.vehicle.vehicle_name).upper()
            vehicle_type = str(d.vehicle.vehicle_category.category_name).upper()
            description = d.description or ''
            from_date = getattr(d, 'from_date', None)
            to_date = getattr(d, 'to_date', None)

            from_date_str = from_date.strftime("%d-%b-%Y") if from_date else ""
            to_date_str = to_date.strftime("%d-%b-%Y") if to_date else ""

            date = f"From {from_date_str} To {to_date_str}" if from_date and to_date else ""

            location_text = getattr(d, 'location', '') or ''
        
            # Build particulars HTML based on invoice type
            if invoice.invoice_type == 'complex':
                # Complex invoice - include location and date range
                particulars_parts = [f"<b>{vehicle_name}</b> - {description}"]
                
                
                    
                if date:
                    particulars_parts.append(date)
                
                particulars_html = "<br/>".join(particulars_parts)
            else:
                # Simple invoice - original format (no dates)
                if location_text:
                    particulars_html = f"""
                        <b>{vehicle_name}</b> - {description}<br/>
                        
                    """
                else:
                    particulars_html = f"<b>{vehicle_name}</b> - {description}"
        
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
                    str(sl_no),
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
                    str(sl_no),
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
                    str(sl_no),
                    particulars,
                    f"{amount:.3f}",
                    f"{vat:.3f}",
                    f"{total:.3f}",
                ])
            else:
                detail_data.append([
                    str(sl_no),
                    particulars,
                    f"{amount:.3f}",
                ])
        
        sl_no += 1

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
               "",
               "Net Total",
               f"{total_amount:.3f}"
            ])
            detail_data.append([
                "",
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
                "",
                "Total",
                f"{grand_total:.3f}"
            ])
        else:
            detail_data.append([
                "",
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
                "",
                "Net Total",
                f"{total_amount:.3f}"
            ])
            detail_data.append([
                "",
                Paragraph("OUTPUT VAT@5%", styles["Normal"]),
                "",
                "Tax Total",
                f"{total_vat:.3f}"
            ])
            detail_data.append([
                "",
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
    # === SIGNATURE AREA ===
    # =========================================================================

    sig_left_text = Paragraph(
        "<b>Customers Seal and Signature</b>",
        styles["Normal"]
    )

    sig_right_text = Paragraph(
        "<b>For Silver Line Group Business</b>",
        styles["Normal"]
    )

    sig_data = [[sig_left_text, sig_right_text]]

    # Smaller table, centered on the page
    sig_table = Table(
        sig_data,
        colWidths=[220, 220],
        rowHeights=[70],
        hAlign='CENTER'
    )

    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
    - Equipment Details Table
    - Spare Parts Delivered Table (if any)
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
    LPO Date : {contract.buyer_order_no or ''} <br/>
    """

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Contract Information ===
    vat_para = Paragraph(
        "<para alignment='right'><b>VATIN:</b> OM1100340532</para>",
        styles["Normal"]
    )
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

    # Wrap VAT No + contract table together so VAT No sits above the contract no
    right_column = Table(
        [[vat_para], [right_table]],
        colWidths=[240]
    )
    right_column.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, 0), 0),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ]))

    header_table = Table(
        [[left_table, right_column]],
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
        description = d.description or ""
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

    # === SPARE PARTS DELIVERED TABLE (only if any exist) ===
    spare_parts = contract.spare_parts.select_related('sparepart', 'item_group').all()

    if spare_parts.exists():
        story.append(Paragraph("<b>Spare Parts Delivered</b>", styles["Heading4"]))
        story.append(Spacer(1, 6))

        spare_header_style = ParagraphStyle(
            'SpareHeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            alignment=1,
            leading=10,
        )

        spare_data = [[
            Paragraph("SI No", spare_header_style),
            Paragraph("Spare Part", spare_header_style),
            Paragraph("Part No", spare_header_style),
            Paragraph("Qty", spare_header_style),
            Paragraph("Rate", spare_header_style),
            Paragraph("Amount", spare_header_style),
            Paragraph("Warranty", spare_header_style),
            Paragraph("Condition", spare_header_style),
        ]]

        for idx, sp in enumerate(spare_parts, start=1):
            part_name = str(sp.sparepart) if sp.sparepart else ''
            part_no = sp.part_no or ""
            qty = f"{float(sp.quantity):.2f}" if sp.quantity else "0.00"
            rate = f"{float(sp.rate):.3f}" if sp.rate else "0.000"
            amount = f"{float(sp.amount):.3f}" if sp.amount else "0.000"
            warranty = "Yes" if sp.warranty else "No"
            condition = sp.condition or ""

            spare_data.append([
                str(idx),
                Paragraph(part_name, styles["Normal"]),
                part_no,
                qty,
                rate,
                amount,
                warranty,
                condition,
            ])

        spare_table = Table(spare_data, colWidths=[30, 140, 80, 50, 60, 70, 60, 60])
        spare_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(spare_table)
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

    # Small font style for Terms & Conditions
    terms_style = ParagraphStyle(
        'TermsStyle',
        parent=styles['Normal'],
        fontSize=8,      # Reduce font size
        leading=15      # Line spacing
    )

    # === TERMS & CONDITIONS ===
    if contract.terms_and_condition:
        for term in contract.terms_and_condition.split('\n'):
            if term.strip():
                story.append(Paragraph(term, terms_style))
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

def create_offhire_pdf(offhire):
    """
    Build and return PDF response for OffHire.

    Components:
    - Header: Top logo image (silver_head.jpg)  — always shown
    - Footer: Bottom footer image (silver_footer.jpg) — always shown
    - Signature: Not applicable for OffHire

    Table columns:
      Sl.No | Equipment | Location | Period | Quantity | Total Amount
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # ── CUSTOMER / TO BLOCK ──────────────────────────────────────────────────
    customer = offhire.customer
    to_text = f"""<b>To:</b><br/>
    {customer.ledger_name if customer else ''}<br/>
    Mobile: {customer.mobile if customer else ''}<br/>
    Address: {customer.address1 if customer else ''}<br/>
    VATIN: {customer.trn_number if customer else ''}<br/>
    E-Mail: {customer.email if customer else ''}"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_table = Table([[to_para]], colWidths=[280])

    # ── RIGHT BLOCK ──────────────────────────────────────────────────────────
    contract_no = offhire.delivery_contract.voucher_no if offhire.delivery_contract else ''
    delivery_contract_date = offhire.delivery_contract.date.strftime("%d-%m-%Y")
    offhire_dt  = (
        offhire.offhire_date_time.strftime("%d-%m-%Y %H:%M")
        if offhire.offhire_date_time else ''
    )

    right_data = [
        ["OffHire No:",        offhire.voucher_no],
        ["Date:",              offhire.date.strftime("%d-%m-%Y")],
        ["OffHire Date/Time:", offhire_dt],
        ["Contract No:",       contract_no],
        [" Delivery Contract Date:",     delivery_contract_date],
    ]
    if offhire.remarks:
        right_data.append(["Remarks:", offhire.remarks])

    right_table = Table(right_data, colWidths=[120, 120])
    right_table.setStyle(TableStyle([
        ('GRID',    (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME',(0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',(0, 0), (-1, -1), 9),
        ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',   (0, 0), (0, -1),  'LEFT'),
        ('ALIGN',   (1, 0), (1, -1),  'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph(
        "<b><font size=14>OFF HIRE REPORT</font></b>",
        ParagraphStyle('center', alignment=1)
    ))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # ── DETAILS TABLE ────────────────────────────────────────────────────────
    # Columns: Sl.No | Equipment | Period | Quantity

    col_widths = [40, 320, 90, 100]

    detail_data = [[
        "Sl.No", "Equipment", "Period", "Quantity"
    ]]

    grand_total = 0
    sl_no       = 1

    for d in offhire.details.all():
        vehicle      = d.vehicle
        vehicle_name = str(vehicle.vehicle_name).upper()

        plate_code   = getattr(vehicle, 'license_plate_code',   '') or ''
        plate_number = getattr(vehicle, 'license_plate_number', '') or ''
        license_text = f"{plate_code}-{plate_number}" if (plate_code or plate_number) else ''

        particulars_parts = [f"<b>{vehicle_name}</b>"]
        if license_text:
            particulars_parts.append(license_text)
        particulars = Paragraph("<br/>".join(particulars_parts), styles["Normal"])

        period_display = str(d.period).capitalize() if d.period else "-"
        quantity       = float(d.quantity) if d.quantity else 0
        total          = float(d.total_amount)
        grand_total   += total

        detail_data.append([
            str(sl_no),
            particulars,
            period_display,
            f"{quantity:.2f}" if quantity else "-",
        ])
        sl_no += 1

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID',    (0, 0),  (-1, -1),  0.5, colors.black),
        ('FONTNAME',(0, 0),  (-1,  0),  'Helvetica-Bold'),
        ('FONTSIZE',(0, 0),  (-1, -1),  9),
        ('ALIGN',   (0, 0),  (-1, -1),  'CENTER'),
        ('ALIGN',   (1, 1),  (1, -1),   'LEFT'),   # Equipment left-aligned
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN',  (0, 0),  (-1, -1),  'MIDDLE'),
        ('PADDING', (0, 0),  (-1, -1),  6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    

    # ── REMARKS ─────────────────────────────────────

    remarks = offhire.remarks or " "

    remarks_table = Table(
        [
            [Paragraph("<b>Remarks</b>", styles["Normal"])],
            [Paragraph(remarks, styles["Normal"])]
        ],
        colWidths=[550]
    )

    remarks_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(remarks_table)
    story.append(Spacer(1, 20))

    # ── SIGNATURE BOXES ──────────────────────────────────────────────────────
    sig_data = [[
        Paragraph("<b>Customers Seal and Signature</b>", styles["Normal"]),
        Paragraph("<b>For Silver Line Group Business</b>", styles["Normal"]),
    ]]
    sig_table = Table(sig_data, colWidths=[270, 270], rowHeights=[70])
    sig_table.setStyle(TableStyle([
        ('GRID',    (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',   (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 25))

    # ── FOOTER FUNC ──────────────────────────────────────────────────────────
    def footer_func(canvas, doc):
        canvas.saveState()
        canvas.restoreState()

    # ── BUILD PDF ─────────────────────────────────────────────────────────────
    logo_path         = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path,
        doc_type="offhire",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="offhire_{offhire.voucher_no}.pdf"'
    )
    response.write(pdf)
    return response


def create_replacement_pdf(replacement):
    """
    Build and return PDF response for Replacement Note.
 
    Structure mirrors create_delivery_contract_pdf:
    - Header image (build_pdf handles it)
    - Title
    - Customer / Contract info block (left/right)
    - Replacement details table  (old → new per row)
    - Handover / sign-off box
    - Footer image
    """
    buffer = BytesIO()
    story  = []
    styles = getSampleStyleSheet()
 
    contract = replacement.delivery_contract
    customer = replacement.customer or contract.customer
 
    # ─────────────────────────────────────────
    #  LEFT BLOCK — Customer details
    # ─────────────────────────────────────────
    to_text = f"""<b>Customer Details:</b><br/>
    {customer.ledger_name if customer else ''}<br/>
    Mobile: {customer.mobile if customer else ''}<br/>
    Address: {customer.address1 if customer else ''}<br/>
    E-Mail: {customer.email if customer else ''}<br/><br/>
    Hire Contract No: {contract.voucher_no}<br/>
    Hire Contract Date: {contract.date.strftime('%d-%m-%Y') if contract.date else ''}<br/>
    """
    to_para    = Paragraph(to_text, styles["Normal"])
    left_table = Table([[to_para]], colWidths=[280])
 
    # ─────────────────────────────────────────
    #  RIGHT BLOCK — Replacement note info
    # ─────────────────────────────────────────
    right_data = [
        ["Replacement Note No:", replacement.voucher_no or ""],
        ["Date:",                replacement.date.strftime("%d-%m-%Y") if replacement.date else ""],
        ["Replacement Date/Time:",
            replacement.replacement_date_time.strftime("%d-%m-%Y %H:%M")
            if replacement.replacement_date_time else ""],
        ["Remarks:", replacement.remarks or ""],
    ]
 
    right_table = Table(right_data, colWidths=[130, 110])
    right_table.setStyle(TableStyle([
        ('GRID',      (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME',  (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',  (0, 0), (-1, -1), 9),
        ('VALIGN',    (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',     (0, 0), (0, -1), 'LEFT'),
        ('ALIGN',     (1, 0), (1, -1), 'LEFT'),
        ('PADDING',   (0, 0), (-1, -1), 4),
    ]))
 
    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
 
    # ─────────────────────────────────────────
    #  TITLE
    # ─────────────────────────────────────────
    title_style = ParagraphStyle(
        'TitleCenter',
        parent=styles['Normal'],
        fontSize=14,
        fontName='Helvetica-Bold',
        alignment=1,
    )
    story.append(Paragraph("REPLACEMENT NOTE", title_style))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))
 
    # ─────────────────────────────────────────
    #  REPLACEMENT DETAILS TABLE
    #
    #  Columns:
    #  SI | Old Equipment ID | Old Vehicle | Reason / Issue |
    #  New Equipment ID | New Vehicle | Old Meter | New Meter |
    #  Old Fuel | Condition
    # ─────────────────────────────────────────
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        alignment=1,
        leading=10,
    )
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
    )
 
    detail_data = [[
        Paragraph("SI<br/>No",          header_style),
        Paragraph("Breakdown<br/>Equipment ID", header_style),
        Paragraph("Breakdown<br/>Vehicle",      header_style),
        Paragraph("Reason / Issue",             header_style),
        Paragraph("Replacement<br/>Equipment ID", header_style),
        Paragraph("Replacement<br/>Vehicle",    header_style),
        Paragraph("Old<br/>Meter",              header_style),
        Paragraph("New<br/>Meter",              header_style),
        Paragraph("Old<br/>Fuel",               header_style),
        Paragraph("Condition",                  header_style),
    ]]
 
    details = replacement.details.select_related(
        'old_vehicle', 'new_vehicle', 'delivery_contract_detail'
    ).all()
 
    for idx, d in enumerate(details, start=1):
 
        def get_equip_id(vehicle):
            if not vehicle:
                return ""
            plate_code   = getattr(vehicle, 'license_plate_code',   '') or ''
            plate_number = getattr(vehicle, 'license_plate_number', '') or ''
            if plate_code or plate_number:
                return f"{plate_code}-{plate_number}"
            return vehicle.vehicle_name or ""
 
        old_equip_id = get_equip_id(d.old_vehicle)
        new_equip_id = get_equip_id(d.new_vehicle)
 
        old_vehicle_name = d.old_vehicle.vehicle_name  if d.old_vehicle else ""
        new_vehicle_name = d.new_vehicle.vehicle_name  if d.new_vehicle else ""
        vehicle_category = d.new_vehicle.vehicle_category.category_name
 
        old_meter = f"{float(d.old_meter_reading):.2f}" if d.old_meter_reading else "-"
        new_meter = f"{float(d.new_meter_reading):.2f}" if d.new_meter_reading else "-"
        old_fuel  = d.old_fuel_level or "-"
        condition = d.old_vehicle_condition or "-"
        reason    = d.reason or "-"
 
        detail_data.append([
            str(idx),
            Paragraph(old_equip_id,      cell_style),
            Paragraph(old_vehicle_name,  cell_style),
            Paragraph(reason,            cell_style),
            Paragraph(new_equip_id,      cell_style),
            Paragraph(vehicle_category,  cell_style),
            old_meter,
            new_meter,
            old_fuel,
            Paragraph(condition,         cell_style),
        ])
 
    # Empty row at bottom (matches DC style)
    detail_data.append(["", "", "", "", "", "", "", "", "", ""])
 
    # Column widths — total = 540
    # SI(25) | OldID(60) | OldVeh(70) | Reason(75) |
    # NewID(60) | NewVeh(70) | OldMtr(40) | NewMtr(40) | Fuel(35) | Cond(65)
    col_widths = [25, 60, 70, 75, 60, 70, 40, 40, 35, 65]
 
    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID',        (0, 0),  (-1, -1), 0.5, colors.black),
        ('BACKGROUND',  (0, 0),  (-1,  0), colors.lightgrey),
        ('VALIGN',      (0, 0),  (-1, -1), 'MIDDLE'),
        ('ALIGN',       (0, 0),  (-1,  0), 'CENTER'),   # header row centred
        ('ALIGN',       (0, 1),  (0,  -1), 'CENTER'),   # SI No col
        ('ALIGN',       (6, 1),  (8,  -1), 'CENTER'),   # meter + fuel cols
        ('TOPPADDING',  (0, 0),  (-1,  0), 8),
        ('BOTTOMPADDING',(0, 0), (-1,  0), 8),
        ('FONTSIZE',    (0, 1),  (-1, -1), 8),
    ]))
 
    story.append(detail_table)
    story.append(Spacer(1, 15))
 
    # ─────────────────────────────────────────
    #  HANDOVER / SIGN-OFF BOX
    #  Mirrors the hire details + signature box in DC PDF
    # ─────────────────────────────────────────
    replace_dt = (
        replacement.replacement_date_time.strftime("%d-%m-%Y %H:%M")
        if replacement.replacement_date_time else ""
    )
    site_location = contract.location or ""
    site_contact  = contract.site_contact_person or ""
    contact_no    = contract.contact_no or ""
 
    signoff_data = [
        # Row 0 — header (spanned)
        [
            Paragraph(
                "<b>Vehicle replacement carried out as per the terms and conditions of the hire contract</b>",
                styles["Normal"]
            ),
            ""
        ],
        # Row 1-3 — detail fields
        [f"Replacement Date/Time: {replace_dt}",  f"Site Location: {site_location}"],
        [f"Site Contact Person: {site_contact}",   f"Contact No: {contact_no}"],
        ["", ""],
        # Row 4 — signature labels
        [
            Paragraph("<b>Silver Line Group (as Owner)</b>", styles["Normal"]),
            Paragraph("<b>Hirer's Name</b>",                 styles["Normal"]),
        ],
        # Row 5 — signature area (tall)
        [
            Paragraph("<br/><br/>Signature: ", styles["Normal"]),
            Paragraph("<br/><br/>Signature: ", styles["Normal"]),
        ],
    ]
 
    signoff_table = Table(
        signoff_data,
        colWidths=[270, 270],
        rowHeights=[None, None, None, None, None, 60],
    )
    signoff_table.setStyle(TableStyle([
        ('BOX',           (0, 0), (-1, -1), 0.5, colors.black),
        # Header row — span both cols
        ('SPAN',          (0, 0), (1,  0)),
        ('BACKGROUND',    (0, 0), (1,  0), colors.whitesmoke),
        ('BOTTOMPADDING', (0, 0), (1,  0), 8),
        # Detail rows typography
        ('FONTNAME',      (0, 1), (-1, 3), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, 3), 9),
        # Separator before signature labels
        ('LINEABOVE',     (0, 4), (-1, 4), 0.5, colors.black),
        # Vertical divider between Owner / Hirer
        ('LINEBEFORE',    (1, 4), (1,  5), 0.5, colors.black),
        ('VALIGN',        (0, 4), (-1, 5), 'TOP'),
        # Padding
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
 
    story.append(signoff_table)
    story.append(Spacer(1, 20))
 
    # ─────────────────────────────────────────
    #  FOOTER FUNCTION  (signature image)
    # ─────────────────────────────────────────
    def footer_func(canvas, doc):
        canvas.saveState()
 
        signature_image_path = os.path.join(
            settings.MEDIA_ROOT, 'timesheet_head', 'sign.jpg'
        )
        if os.path.exists(signature_image_path):
            canvas.drawImage(
                signature_image_path,
                1 * inch,
                2.2 * inch,
                width=3 * inch,
                height=0.8 * inch,
                preserveAspectRatio=True,
                mask='auto',
            )
 
        canvas.restoreState()
 
    # ─────────────────────────────────────────
    #  BUILD PDF
    # ─────────────────────────────────────────
    logo_path         = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')
 
    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path,
        doc_type="replacement",
    )
 
    pdf = buffer.getvalue()
    buffer.close()
 
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="replacement_{replacement.voucher_no}.pdf"'
    )
    response.write(pdf)
    return response    


def create_receipt_pdf(receipt):
    """
    Build and return PDF response for Receipt Voucher.

    Components:
    - Header: Top logo image (enable_header)
    - Footer: Bottom footer image (enable_footer)
    - Signature: Signature image above footer (enable_signature)
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Received From / Ledger ===
    received_from = receipt.ReceivedFrom or (receipt.Ledger.ledger_name if receipt.Ledger else '')
    to_text = f"""<b>Received From:</b><br/>
    {received_from}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Cheque details if PDC ===
    right_data = [
        ["Voucher No:", receipt.voucher_no],
        ["Date:", receipt.Date.strftime("%d-%m-%Y")],
    ]

    if receipt.IsPDC:
        right_data.append(["Cheque No:", receipt.ChequeNo or ""])
        right_data.append(["Cheque Date:", receipt.ChequeDate.strftime("%d-%m-%Y") if receipt.ChequeDate else ""])
        right_data.append(["Cleared:", receipt.Cleared or ""])

    right_table = Table(right_data, colWidths=[120, 120])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>RECEIPT VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: minimal - Sl.No, Ledger, Description, Amount ===
    detail_data = [["Sl.No", "Ledger", "Description", "Amount"]]
    col_widths = [35, 150, 220, 115]

    total_amount = 0
    sl_no = 1

    for d in receipt.details.all():
        ledger_name = d.Ledger.ledger_name if d.Ledger else ''
        desc = d.Desc or ''
        amount = float(d.Amount)
        total_amount += amount

        detail_data.append([
            str(sl_no),
            Paragraph(ledger_name, styles["Normal"]),
            Paragraph(desc, styles["Normal"]),
            f"{amount:.3f}",
        ])
        sl_no += 1

    # Bounce charge row if applicable
    if receipt.BounceCharge and float(receipt.BounceCharge) > 0:
        detail_data.append([
            "", "", Paragraph("Bounce Charge", styles["Normal"]), f"{float(receipt.BounceCharge):.3f}"
        ])
        total_amount += float(receipt.BounceCharge)

    detail_data.append(["", "", "Total", f"{total_amount:.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(total_amount)
    baisa_part = int(round((total_amount - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {total_amount:.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Received By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        """
        Conditionally draws signature image if enabled
        """
        canvas.saveState()

        if receipt.enable_signature:
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
        include_header=receipt.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if receipt.enable_footer else None,
        doc_type="receipt",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receipt_{receipt.voucher_no}.pdf"'
    response.write(pdf)
    return response    

def create_payment_pdf(payment):
    """
    Build and return PDF response for Payment Voucher.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Paid To / Ledger ===
    paid_to = payment.PaidTo or (payment.Ledger.ledger_name if payment.Ledger else '')
    to_text = f"""<b>Paid To:</b><br/>
    {paid_to}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    right_data = [
        ["Voucher No:", payment.voucher_no],
        ["Date:", payment.Date.strftime("%d-%m-%Y")],
    ]

    if payment.IsPDC:
        right_data.append(["Cheque No:", payment.ChequeNo or ""])
        right_data.append(["Cheque Date:", payment.ChequeDate.strftime("%d-%m-%Y") if payment.ChequeDate else ""])
        right_data.append(["Cleared:", payment.Cleared or ""])

    right_table = Table(right_data, colWidths=[120, 120])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>PAYMENT VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    vat_type_labels = {1: "No VAT", 2: "Inclusive VAT (5%)", 3: "Exclusive VAT (5%)"}

    total_taxable = 0
    total_vat = 0
    total_amount = 0   # sum of stored Amount (= net/total), the source of truth
    sl_no = 1

    if payment.is_detailed:
        detail_data = [["Sl.No", "Inv. Date", "Inv. No", "Ledger", "VAT Type", "Taxable", "VAT", "Total"]]
        col_widths = [30, 65, 60, 130, 90, 65, 60, 65]

        for d in payment.details.all():
            ledger_name = d.Ledger.ledger_name if d.Ledger else ''

            amount = float(d.Amount)            # = Total for this line
            vat_amount = float(d.vat_amount or 0)
            taxable = amount - vat_amount        # base amount, derived only

            total_amount += amount
            total_vat += vat_amount
            total_taxable += taxable

            detail_data.append([
                str(sl_no),
                d.invoice_date.strftime("%d-%m-%Y") if d.invoice_date else "",
                d.invoice_no or "",
                Paragraph(ledger_name, styles["Normal"]),
                vat_type_labels.get(d.vat_type, ""),
                f"{taxable:.3f}",
                f"{vat_amount:.3f}",
                f"{amount:.3f}",
            ])
            sl_no += 1

        detail_data.append([
            "", "", "", "", "", "Taxable Total", f"{total_taxable:.3f}", ""
        ])
        detail_data.append([
            "", "", "", "", "", "VAT Total", f"{total_vat:.3f}", ""
        ])
        detail_data.append([
            "", "", "", "", "", "", "Total", f"{total_amount:.3f}"
        ])

    else:
        detail_data = [["Sl.No", "Ledger", "Amount"]]
        col_widths = [40, 350, 100]

        for d in payment.details.all():
            ledger_name = d.Ledger.ledger_name if d.Ledger else ''
            amount = float(d.Amount)
            total_amount += amount

            detail_data.append([
                str(sl_no),
                Paragraph(ledger_name, styles["Normal"]),
                f"{amount:.3f}",
            ])
            sl_no += 1

        detail_data.append(["", "Total", f"{total_amount:.3f}"])

    # Bounce charge row if applicable
    if payment.BounceCharge and float(payment.BounceCharge) > 0:
        bounce = float(payment.BounceCharge)
        if payment.is_detailed:
            detail_data.insert(-3, ["", "", "", "", "", "Bounce Charge", f"{bounce:.3f}", ""])
        else:
            detail_data.insert(-1, ["", "Bounce Charge", f"{bounce:.3f}"])
        total_amount += bounce

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('FONTNAME', (-3, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    # Prefer the voucher's saved TotalAmount (computed by the form) — fall
    # back to the summed line Amounts only if it's missing/zero.
    grand_total = float(payment.TotalAmount) if payment.TotalAmount else total_amount

    riyal_part = int(grand_total)
    baisa_part = int(round((grand_total - riyal_part) * 1000))

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

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Received By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    def footer_func(canvas, doc):
        canvas.saveState()
        if payment.enable_signature:
            signature_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'sign.jpg')
            if os.path.exists(signature_image_path):
                canvas.drawImage(
                    signature_image_path,
                    1 * inch, 2.2 * inch,
                    width=3 * inch, height=0.8 * inch,
                    preserveAspectRatio=True,
                    mask='auto'
                )
        canvas.restoreState()

    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=payment.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if payment.enable_footer else None,
        doc_type="payment",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="payment_{payment.voucher_no}.pdf"'
    response.write(pdf)
    return response

def create_receiptbill_pdf(receiptbill):
    """
    Build and return PDF response for Receipt Bill Clearance.

    Components:
    - Header: Top logo image (enable_header)
    - Footer: Bottom footer image (enable_footer)
    - Signature: Signature image above footer (enable_signature)
    - Details table lists cleared Invoices / Openings with amounts
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Customer ===
    customer_name = receiptbill.Customer.ledger_name if receiptbill.Customer else ''
    to_text = f"""<b>Customer:</b><br/>
    {customer_name}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Date, Ledger, TR No, Cheque details if PDC ===
    right_data = [
        ["Date:", receiptbill.Date.strftime("%d-%m-%Y")],
        ["Ledger:", receiptbill.Ledger.ledger_name if receiptbill.Ledger else ""],
    ]

    if receiptbill.TrnNo:
        right_data.append(["TR No:", str(receiptbill.TrnNo)])

    if receiptbill.IsPDC:
        right_data.append(["Cheque No:", receiptbill.ChequeNo or ""])
        right_data.append(["Cheque Date:", receiptbill.ChequeDate.strftime("%d-%m-%Y") if receiptbill.ChequeDate else ""])
        right_data.append(["Cheque Status:", receiptbill.get_ChequeStatus_display() if receiptbill.ChequeStatus else ""])

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>RECEIPT BILL CLEARANCE</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: Type, Voucher No, Current Amount, Amount Cleared, Balance ===
    detail_data = [["Sl.No", "Type", "Voucher No", "Current Amount", "Amount Cleared", "Balance"]]
    col_widths = [35, 80, 100, 100, 100, 110]

    total_amount = 0
    total_balance = 0
    sl_no = 1

    for d in receiptbill.receiptbilldetails_set.all():
        is_invoice = d.voucherType_id == 2
        is_opening = d.voucherType_id == 16

        # Resolve human-readable voucher number
        display_voucher_no = str(d.VoucherNo)
        try:
            if is_invoice:
                inv = Invoice.objects.get(pk=d.VoucherNo)
                display_voucher_no = inv.voucher_no
                type_label = "Invoice"
            elif is_opening:
                opening = BillWiseOpening.objects.get(pk=d.VoucherNo)
                display_voucher_no = getattr(opening, 'voucher_no', str(d.VoucherNo))
                type_label = "Opening"
            else:
                type_label = "Unknown"
        except Exception:
            type_label = "Invoice" if is_invoice else ("Opening" if is_opening else "Unknown")

        current_amount = float(d.CurrentAmount or 0)
        amount = float(d.Amount or 0)
        balance = current_amount - amount
        total_amount += amount
        total_balance += balance 

        detail_data.append([
            str(sl_no),
            type_label,
            display_voucher_no,
            f"{current_amount:.3f}",
            f"{amount:.3f}",
            f"{balance:.3f}",
        ])
        sl_no += 1

    detail_data.append(["", "", "", "Total", f"{total_amount:.3f}", f"{total_balance:.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(total_amount)
    baisa_part = int(round((total_amount - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {total_amount:.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Received By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if receiptbill.enable_signature:
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
        include_header=receiptbill.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if receiptbill.enable_footer else None,
        doc_type="receiptbill",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receiptbill_{receiptbill.id}.pdf"'
    response.write(pdf)
    return response  

def get_original_amount_and_total_cleared(voucher_type_id, voucher_no):
    """
    Returns (original_amount, total_cleared) for a bill, matching
    the same voucherType semantics used in update_*_cleared_status.
    """
    if voucher_type_id == 1:  # Hire
        original = FleetHire.objects.get(pk=voucher_no).grand_total
    elif voucher_type_id == 13:  # Purchase
        original = PurchaseMaster.objects.get(pk=voucher_no).grand_total_amount
    elif voucher_type_id == 17:  # Opening / AssetPurchase share this marker
        obj = BillWiseOpening.objects.filter(pk=voucher_no).first()
        original = obj.InvBalance if obj else AssetPurchase.objects.get(pk=voucher_no).grand_total
    else:
        return Decimal('0.000'), Decimal('0.000')

    payment_total = PaymentBillDetails.objects.filter(
        VoucherNo=voucher_no, voucherType__id=voucher_type_id
    ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

    debit_total = DebitNoteDetail.objects.filter(
        VoucherNo=voucher_no, voucherType__id=voucher_type_id
    ).aggregate(total=Sum('Amount'))['total'] or Decimal('0.000')

    return original, payment_total + debit_total      


def create_paymentbill_pdf(paymentbill):
    """
    Build and return PDF response for Payment Bill Clearance.

    Components:
    - Header: Top logo image (enable_header)
    - Footer: Bottom footer image (enable_footer)
    - Signature: Signature image above footer (enable_signature)
    - Details table lists cleared Hire / Purchase / Asset Purchase / Opening with amounts
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Supplier ===
    supplier_name = paymentbill.Supplier.ledger_name if paymentbill.Supplier else ''
    to_text = f"""<b>Supplier:</b><br/>
    {supplier_name}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Date, Ledger, TR No, Cheque details if PDC ===
    right_data = [
        ["Date:", paymentbill.Date.strftime("%d-%m-%Y")],
        ["Ledger:", paymentbill.Ledger.ledger_name if paymentbill.Ledger else ""],
    ]

    if paymentbill.TrnNo:
        right_data.append(["TR No:", str(paymentbill.TrnNo)])

    if paymentbill.IsPDC:
        right_data.append(["Cheque No:", paymentbill.ChequeNo or ""])
        right_data.append(["Cheque Date:", paymentbill.ChequeDate.strftime("%d-%m-%Y") if paymentbill.ChequeDate else ""])
        right_data.append(["Cheque Status:", paymentbill.get_ChequeStatus_display() if paymentbill.ChequeStatus else ""])

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>PAYMENT BILL CLEARANCE</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: Type, Voucher No, Current Amount, Amount Cleared, Balance ===
    detail_data = [["Sl.No", "Type", "Voucher No", "Current Amount", "Amount Cleared", "Balance"]]
    col_widths = [35, 90, 90, 100, 100, 110]

    total_amount = 0
    sl_no = 1

    for d in paymentbill.paymentbilldetails_set.all():
        voucher_type_id = d.voucherType_id

        display_voucher_no = str(d.VoucherNo)
        type_label = "Unknown"

        try:
            if voucher_type_id == 1:  # Hire
                hire = FleetHire.objects.get(pk=d.VoucherNo)
                display_voucher_no = hire.voucher_no
                type_label = "Hire"
            elif voucher_type_id == 16:  # BillWiseOpening
                opening = BillWiseOpening.objects.get(pk=d.VoucherNo)
                display_voucher_no = getattr(opening, 'voucher_no', str(d.VoucherNo))
                type_label = "Opening"
            elif voucher_type_id == 13:  # Purchase
                purchase = PurchaseMaster.objects.get(pk=d.VoucherNo)
                display_voucher_no = getattr(purchase, 'voucher_no', str(d.VoucherNo))
                type_label = "Purchase"
            elif voucher_type_id == 17:  # AssetPurchase
                asset_purchase = AssetPurchase.objects.get(pk=d.VoucherNo)
                display_voucher_no = getattr(asset_purchase, 'voucher_no', str(d.VoucherNo))
                type_label = "Asset Purchase"
        except Exception:
            type_label = {1: "Hire", 16: "Opening", 13: "Purchase", 17: "Asset Purchase"}.get(voucher_type_id, "Unknown")

        current_amount = float(d.CurrentAmount or 0)
        amount = float(d.Amount or 0)
        balance = current_amount - amount
        total_amount += amount

        detail_data.append([
            str(sl_no),
            type_label,
            display_voucher_no,
            f"{float(d.CurrentAmount or 0):.3f}", 
            f"{amount:.3f}",
            f"{balance:.3f}",
        ])
        sl_no += 1

    detail_data.append(["", "", "", "", "Total", f"{total_amount:.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(total_amount)
    baisa_part = int(round((total_amount - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {total_amount:.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Received By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if paymentbill.enable_signature:
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
        include_header=paymentbill.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if paymentbill.enable_footer else None,
        doc_type="paymentbill",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="paymentbill_{paymentbill.id}.pdf"'
    response.write(pdf)
    return response    

def create_journal_pdf(journal):
    """
    Build and return PDF response for Journal Voucher.

    Components:
    - Header: Top logo image (enable_header)
    - Footer: Bottom footer image (enable_footer)
    - Signature: Signature image above footer (enable_signature)
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Cost Center / Staff ===
    cost_center_name = str(journal.cost_center) if journal.cost_center else ''
    staff_name = str(journal.staff) if journal.staff else ''

    to_text = f"""<b>Cost Center:</b> {cost_center_name}<br/>
    <b>Staff:</b> {staff_name}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Voucher Type ===
    right_data = [
        ["Voucher No:", journal.voucher_no],
        ["Date:", journal.date.strftime("%d-%m-%Y")],
        ["Voucher Type:", str(journal.voucherType)],
    ]

    right_table = Table(right_data, colWidths=[120, 120])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>JOURNAL VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: Sl.No, Debit Ledger, Credit Ledger, Amount, Narration ===
    detail_data = [["Sl.No", "Debit Ledger", "Credit Ledger", "Amount", "Narration"]]
    col_widths = [35, 140, 140, 80, 155]

    total_amount = 0
    sl_no = 1

    for d in journal.details.all():
        debit_name = str(d.debit) if d.debit else '-'
        credit_name = str(d.credit) if d.credit else '-'
        narration = d.narration or ''
        amount = float(d.amount)
        total_amount += amount

        detail_data.append([
            str(sl_no),
            Paragraph(debit_name, styles["Normal"]),
            Paragraph(credit_name, styles["Normal"]),
            f"{amount:.3f}",
            Paragraph(narration, styles["Normal"]),
        ])
        sl_no += 1

    detail_data.append(["", "", "Total", f"{total_amount:.3f}", ""])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
        ('FONTNAME', (-3, -1), (-2, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(total_amount)
    baisa_part = int(round((total_amount - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {total_amount:.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Prepared By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if journal.enable_signature:
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
        include_header=journal.enable_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if journal.enable_footer else None,
        doc_type="journal",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="journal_{journal.voucher_no}.pdf"'
    response.write(pdf)
    return response    


def create_purchase_pdf(purchase, include_header=True, include_footer=True, include_signature=True):
    """
    Build and return PDF response for Purchase Voucher.

    Components:
    - Header: Top logo image (include_header)
    - Footer: Bottom footer image (include_footer)
    - Signature: Signature image above footer (include_signature)
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Supplier / Vendor Invoice info ===
    supplier_name = str(purchase.ledger) if purchase.ledger else ''
    to_text = f"""<b>Supplier:</b><br/>
    {supplier_name}<br/>
    Vendor Inv No: {purchase.VendorInvNo or ''}<br/>
    Invoice Date: {purchase.InvoiceDate.strftime("%d-%m-%Y") if purchase.InvoiceDate else ''}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Payment Mode, Cost Center, LR No, Transport ===
    right_data = [
        ["Voucher No:", purchase.voucher_no],
        ["Date:", purchase.transaction_date.strftime("%d-%m-%Y")],
        ["Payment Mode:", purchase.payment_mode or ""],
        ["Cost Center:", str(purchase.cost_center) if purchase.cost_center else ""],
    ]

    if purchase.lrNo:
        right_data.append(["LR No:", purchase.lrNo])
    if purchase.transportCompany:
        right_data.append(["Transport Co:", purchase.transportCompany])

    right_table = Table(right_data, colWidths=[110, 130])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>PURCHASE VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === ITEMS TABLE ===
    detail_data = [["Sl.No", "Item", "Qty", "Unit", "Rate", "Amount", "Tax", "Total"]]
    col_widths = [30, 155, 45, 55, 65, 70, 60, 70]

    sl_no = 1
    for d in purchase.items.all():
        item_name = str(d.item_name) if d.item_name else ''
        unit_name = str(d.unit) if d.unit else ''
        qty = d.quantity or 0
        rate = float(d.purchase_rate or 0)
        amount = float(d.item_net_amount or 0)
        tax_amount = float(d.item_tax_amount or 0)
        total = float(d.item_total_amount or (amount + tax_amount))

        detail_data.append([
            str(sl_no),
            Paragraph(item_name, styles["Normal"]),
            str(qty),
            unit_name,
            f"{rate:.3f}",
            f"{amount:.3f}",
            f"{tax_amount:.3f}",
            f"{total:.3f}",
        ])
        sl_no += 1

    # === TOTALS ===
    net_value = float(purchase.total_net_value or 0)
    tax_amount = float(purchase.total_tax_amount or 0)
    discount = float(purchase.discount or 0)
    freight = float(purchase.Freight or 0)
    grand_total = float(purchase.grand_total_amount or 0)

    detail_data.append(["", "", "", "", "", "", "Net Total", f"{net_value:.3f}"])
    detail_data.append(["", "", "", "", "", "", "Tax Total", f"{tax_amount:.3f}"])
    if discount:
        detail_data.append(["", "", "", "", "", "", "Discount", f"{discount:.3f}"])
    if freight:
        detail_data.append(["", "", "", "", "", "", "Freight", f"{freight:.3f}"])
    detail_data.append(["", "", "", "", "", "", "Grand Total", f"{grand_total:.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(grand_total)
    baisa_part = int(round((grand_total - riyal_part) * 1000))

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

    if purchase.remarks:
        story.append(Paragraph(f"<b>Remarks:</b> {purchase.remarks}", styles["Normal"]))
        story.append(Spacer(1, 12))

    if purchase.payment_terms:
        story.append(Paragraph(f"<b>Payment Terms:</b> {purchase.payment_terms}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Supplier Signature</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if include_signature:
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
        include_header=include_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if include_footer else None,
        doc_type="purchase",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="purchase_{purchase.voucher_no}.pdf"'
    response.write(pdf)
    return response    


def create_client_outstanding_pdf(customer_id, from_date=None, to_date=None):
    """
    Client Outstanding Statement PDF — one client, bills + totals + PDC list.
    Rebuilt on top of build_client_outstanding_data() (the same LedgerPosting /
    FIFO-credit-allocation logic that powers the new Client Outstanding Report),
    so the PDF always matches what's shown on screen.
    """
    from accounts_app.views import build_client_outstanding_data
    customers, _ = build_client_outstanding_data(
        customer_id=customer_id, from_date=from_date, to_date=to_date
    )
    if not customers:
        response = HttpResponse("No outstanding balance for this customer.", status=404)
        return response

    cust = customers[0]
    customer = cust['ledger']

    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("<b><font size=14>STATEMENT OF ACCOUNT</font></b>",
                            ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 10))

    period_text = f"{to_date}" if to_date else "-"

    info_data = [
        [
            Paragraph(f"<b>Client :</b> {customer.ledger_name}", styles["Normal"]),
            Paragraph(f"<b>As Of Date :</b> {period_text}", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>Address :</b> {getattr(customer, 'address1', None) or '-'}", styles["Normal"]),
            "",
        ],
    ]

    info_table = Table(info_data, colWidths=[4.5 * inch, 2.5 * inch])
    info_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.black),
        ('LINEAFTER', (0, 0), (0, 0), 0.75, colors.black),
        ('SPAN', (0, 1), (1, 1)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------
    # BILLS
    # Sl.No, Date, Voucher/Invoice No, PO No, Debit,
    # Credit, Outstanding, Cumulative, Age
    # ---------------------------------------------------

    detail_data = [
        [
            "Sl.No",
            "Date",
            "Voucher/Inv No",
            "PO No",
            "Debit",
            "Credit",
            "Outstanding",
            "Cumulative",
            "Age"
        ]
    ]

    col_widths = [30, 60, 80, 70, 60, 60, 70, 70, 35]

    for sl_no, bill in enumerate(cust['bills'], start=1):
        detail_data.append([
            str(sl_no),
            bill['date'].strftime("%d-%m-%Y") if bill['date'] else "",
            str(bill['voucher_invoice_no']),
            bill['po_no'] or "-",
            f"{float(bill['debit']):.3f}",
            f"{float(bill['credit']):.3f}",
            f"{float(bill['outstanding']):.3f}",
            f"{float(bill['cumulative']):.3f}",
            str(bill['age_days']),
        ])

    # Total Row
    detail_data.append([
        "",
        "",
        "",
        "Total",
        f"{float(cust['total_debit_amt']):.3f}",
        f"{float(cust['total_credit_amt']):.3f}",
        f"{float(cust['total_balance_amt']):.3f}",
        f"{float(cust['total_balance_amt']):.3f}",
        "",
    ])

    detail_table = Table(detail_data, colWidths=col_widths)

    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),

        # Sl.No, Date, Voucher No, PO No
        ('ALIGN', (0, 1), (3, -1), 'CENTER'),

        # Amount columns
        ('ALIGN', (4, 1), (7, -1), 'RIGHT'),

        # Age
        ('ALIGN', (8, 1), (8, -1), 'CENTER'),

        # Total label
        ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),

        ('PADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------
    # PDC LIST — already built inside build_client_outstanding_data()
    # (opening_balance = this customer's current outstanding), so we reuse
    # cust['pdc_list'] / cust['pdc_grand_credit'] rather than calling
    # build_customer_pdc_list() a second time.
    # ---------------------------------------------------
    pdc_list = cust['pdc_list']
    pdc_grand_credit = cust['pdc_grand_credit']

    if pdc_list:
        story.append(Paragraph("<b><font size=11>List of PDCs</font></b>",
                                ParagraphStyle('pdc_title', alignment=1)))
        story.append(Spacer(1, 6))

        pdc_data = [["Sl.No", "Date", "Voucher No", "Cheque No", "Maturity Date",
                     "Debit", "Credit", "Balance", "Remark"]]
        pdc_col_widths = [30, 55, 65, 60, 65, 50, 50, 60, 65]

        for pdc in pdc_list:
            pdc_data.append([
                str(pdc['sl_no']),
                pdc['date'].strftime("%d/%m/%Y") if pdc['date'] else "",
                str(pdc['voucher_no']),
                pdc['cheque_no'] or "-",
                pdc['cheque_date'].strftime("%d/%m/%Y") if pdc['cheque_date'] else "-",
                "0.000",
                f"{float(pdc['credit']):.3f}",
                f"{float(pdc['balance']):.3f}",
                pdc['remark'] or "-",
            ])

        pdc_data.append([
            "", "", "", "", "Total",
            "0.000",
            f"{float(pdc_grand_credit):.3f}",
            f"{float(pdc_list[-1]['balance']):.3f}",
            "",
        ])

        pdc_table = Table(pdc_data, colWidths=pdc_col_widths)
        pdc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
            ('FONTNAME', (4, -1), (4, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(pdc_table)
        story.append(Spacer(1, 12))

    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=True,
        footer_image_path=footer_image_path,
        doc_type="client_statement",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="statement_{customer.ledger_name}_{customer.id}.pdf"'
    response.write(pdf)
    return response

def create_supplier_outstanding_pdf(supplier_id, from_date=None, to_date=None):
    """
    Supplier Outstanding Statement PDF — one supplier, bills + totals + PDC list.
    Mirrors create_client_outstanding_pdf, built on build_supplier_outstanding_data().
    """
    from accounts_app.views import build_supplier_outstanding_data
    suppliers, _ = build_supplier_outstanding_data(
        supplier_id=supplier_id, from_date=from_date, to_date=to_date
    )
    if not suppliers:
        return HttpResponse("No outstanding balance for this supplier.", status=404)

    sup = suppliers[0]
    supplier = sup['ledger']

    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("<b><font size=14>SUPPLIER STATEMENT OF ACCOUNT</font></b>",
                            ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 10))

    period_text = f"{to_date}" if to_date else "-"

    info_data = [
        [
            Paragraph(f"<b>Supplier :</b> {supplier.ledger_name}", styles["Normal"]),
            Paragraph(f"<b>As Of Date :</b> {period_text}", styles["Normal"]),
        ],
        [
            Paragraph(f"<b>Address :</b> {getattr(supplier, 'address1', None) or '-'}", styles["Normal"]),
            "",
        ],
    ]

    info_table = Table(info_data, colWidths=[4.5 * inch, 2.5 * inch])
    info_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.black),
        ('LINEAFTER', (0, 0), (0, 0), 0.75, colors.black),
        ('SPAN', (0, 1), (1, 1)),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------
    # BILLS
    # ---------------------------------------------------
    detail_data = [["Sl.No", "Type", "Voucher/Bill No", "PO No", "Date", "Age",
                     "Debit", "Credit", "Outstanding", "Cumulative"]]
    col_widths = [25, 45, 75, 65, 55, 30, 55, 55, 65, 65]

    for sl_no, bill in enumerate(sup['bills'], start=1):
        detail_data.append([
            str(sl_no),
            bill['type'],
            str(bill['voucher_invoice_no']),
            bill['po_no'] or "-",
            bill['date'].strftime("%d-%m-%Y") if bill['date'] else "",
            str(bill['age_days']),
            f"{float(bill['debit']):.3f}",
            f"{float(bill['credit']):.3f}",
            f"{float(bill['outstanding']):.3f}",
            f"{float(bill['cumulative']):.3f}",
        ])

    detail_data.append([
        "", "", "", "", "", "Total",
        f"{float(sup['total_paid_amt']):.3f}",
        f"{float(sup['total_purchase_amt'] + sup['total_opening_amt']):.3f}",
        f"{float(sup['total_balance_amt']):.3f}",
        f"{float(sup['total_balance_amt']):.3f}",
    ])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 1), (5, -1), 'CENTER'),
        ('ALIGN', (6, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (5, -1), (5, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # ---------------------------------------------------
    # PDC LIST — already built inside build_supplier_outstanding_data()
    # ---------------------------------------------------
    pdc_list = sup['pdc_list']
    pdc_grand_credit = sup['pdc_grand_credit']

    if pdc_list:
        story.append(Paragraph("<b><font size=11>List of PDCs Issued</font></b>",
                                ParagraphStyle('pdc_title', alignment=1)))
        story.append(Spacer(1, 6))

        pdc_data = [["Sl.No", "Date", "Voucher No", "Cheque No", "Maturity Date",
                     "Debit", "Credit", "Balance", "Remark"]]
        pdc_col_widths = [30, 55, 65, 60, 65, 50, 50, 60, 65]

        for pdc in pdc_list:
            pdc_data.append([
                str(pdc['sl_no']),
                pdc['date'].strftime("%d/%m/%Y") if pdc['date'] else "",
                str(pdc['voucher_no']),
                pdc['cheque_no'] or "-",
                pdc['cheque_date'].strftime("%d/%m/%Y") if pdc['cheque_date'] else "-",
                "0.000",
                f"{float(pdc['credit']):.3f}",
                f"{float(pdc['balance']):.3f}",
                pdc['remark'] or "-",
            ])

        pdc_data.append([
            "", "", "", "", "Total",
            "0.000",
            f"{float(pdc_grand_credit):.3f}",
            f"{float(pdc_list[-1]['balance']):.3f}",
            "",
        ])

        pdc_table = Table(pdc_data, colWidths=pdc_col_widths)
        pdc_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
            ('FONTNAME', (4, -1), (4, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))

        story.append(pdc_table)
        story.append(Spacer(1, 12))

    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=True,
        footer_image_path=footer_image_path,
        doc_type="supplier_statement",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="statement_{supplier.ledger_name}_{supplier.id}.pdf"'
    response.write(pdf)
    return response    


def create_expense_pdf(expense, include_header=True, include_footer=True, include_signature=True):
    """
    Build and return PDF response for Expense Voucher.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Ledger / Expense Source ===
    ledger_name = str(expense.ledger) if expense.ledger else ''
    to_text = f"""<b>Ledger:</b> {ledger_name}<br/>
    <b>Expense Source:</b> {expense.expense_source}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Ref No, Staff ===
    right_data = [
        ["Voucher No:", expense.voucher_no],
        ["Date:", expense.Date.strftime("%d-%m-%Y")],
    ]

    if expense.ref_no:
        right_data.append(["Ref No:", expense.ref_no])
    if expense.staff:
        right_data.append(["Staff:", str(expense.staff)])

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>EXPENSE VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    total_amount = 0
    total_vat = 0
    sl_no = 1

    # === DETAILS TABLE: essential columns only ===
    if expense.is_detailed_expense:
        detail_data = [["Sl.No", "Ledger", "Description", "Amount", "VAT", "Total"]]
        col_widths = [35, 150, 190, 80, 60, 80]

        for d in expense.details.all():
            ledger_name = d.Ledger.ledger_name if d.Ledger else ''
            desc = d.Desc or ''
            amount = float(d.Amount)          # this is the line TOTAL (VAT-inclusive)
            vat_amount = float(d.vat_amount or 0)
            total = amount                     # 👈 no longer amount + vat

            total_amount += amount
            total_vat += vat_amount

            detail_data.append([
                str(sl_no),
                Paragraph(ledger_name, styles["Normal"]),
                Paragraph(desc, styles["Normal"]),
                f"{amount:.3f}",
                f"{vat_amount:.3f}",
                f"{total:.3f}",
            ])
            sl_no += 1

        grand_total = total_amount              # 👈 no longer total_amount + total_vat
        net_total = total_amount - total_vat    # 👈 back-calculated taxable base

        detail_data.append(["", "", "", "Net Total", "", f"{net_total:.3f}"])
        detail_data.append(["", "", "", "VAT Total", "", f"{total_vat:.3f}"])
        detail_data.append(["", "", "", "Total", "", f"{grand_total:.3f}"])

    else:
        detail_data = [["Sl.No", "Ledger", "Description", "Amount"]]
        col_widths = [35, 190, 250, 120]

        for d in expense.details.all():
            ledger_name = d.Ledger.ledger_name if d.Ledger else ''
            desc = d.Desc or ''
            amount = float(d.Amount)
            total_amount += amount

            detail_data.append([
                str(sl_no),
                Paragraph(ledger_name, styles["Normal"]),
                Paragraph(desc, styles["Normal"]),
                f"{amount:.3f}",
            ])
            sl_no += 1

        grand_total = total_amount
        detail_data.append(["", "", "Total", f"{grand_total:.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(grand_total)
    baisa_part = int(round((grand_total - riyal_part) * 1000))

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

    if expense.narration:
        story.append(Paragraph(f"<b>Narration:</b> {expense.narration}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Prepared By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if include_signature:
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
        include_header=include_header,
        include_footer=True,
        footer_func=False,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if include_footer else None,
        doc_type="expense",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="expense_{expense.voucher_no}.pdf"'
    response.write(pdf)
    return response    

def create_invoice_tax_report_pdf(rows, start_date=None, end_date=None):
    """
    Build and return PDF response for Invoice Tax Report.
    Landscape orientation to fit all columns comfortably.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("<b><font size=14>INVOICE TAX REPORT</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 8))

    if start_date or end_date:
        story.append(Paragraph(f"<b>Period:</b> {start_date or '—'} to {end_date or '—'}", styles["Normal"]))
        story.append(Spacer(1, 10))

        # === TABLE ===
    detail_data = [["Date", "Voucher No", "Taxable", "Tax Amt", "Grand Total", "Party", "5%", "0%"]]
    col_widths = [55, 65, 65, 60, 70, 140, 55, 55]

    total_taxable = Decimal('0.000')
    total_tax_amount = Decimal('0.000')
    total_rate5 = Decimal('0.000')
    total_rate0 = Decimal('0.000')

    seen_invoice_ids = set()
    total_grand_total = Decimal('0.000')

    for row in rows:
        detail_data.append([
            row['invoice_date'].strftime("%d-%m-%Y") if row['invoice_date'] else "",
            row['voucher_no'] or "",
            f"{row['taxable']:.3f}",
            f"{row['tax_amount']:.3f}",
            f"{row['grand_total']:.3f}",
            Paragraph(row['party'] or "", styles["Normal"]),
            f"{row['rate_5']:.3f}",
            f"{row['rate_0']:.3f}",
        ])

        total_taxable += row['taxable']
        total_tax_amount += row['tax_amount']
        total_rate5 += row['rate_5']
        total_rate0 += row['rate_0']

        # Grand total counted once per invoice — matches template JS logic
        if row['invoice_id'] not in seen_invoice_ids:
            seen_invoice_ids.add(row['invoice_id'])
            total_grand_total += row['grand_total']

    detail_data.append([
        "Total", "",
        f"{total_taxable:.3f}",
        f"{total_tax_amount:.3f}",
        f"{total_grand_total:.3f}",
        "",
        f"{total_rate5:.3f}",
        f"{total_rate0:.3f}",
    ])

    detail_table = Table(detail_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
        ('ALIGN', (6, 1), (7, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(detail_table)

    # === BUILD PDF (landscape) ===
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')

    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=False,
        doc_type="Invoice Tax Report",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="invoice_tax_report.pdf"'
    response.write(pdf)
    return response    


def create_purchase_tax_report_pdf(rows, start_date=None, end_date=None):
    """
    Build and return PDF response for Purchase Tax Report.
    Landscape orientation to fit all columns comfortably.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    story.append(Paragraph("<b><font size=14>PURCHASE TAX REPORT</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 8))

    if start_date or end_date:
        story.append(Paragraph(f"<b>Period:</b> {start_date or '—'} to {end_date or '—'}", styles["Normal"]))
        story.append(Spacer(1, 10))

    # === TABLE ===
    detail_data = [["Date", "Voucher No", "Taxable", "Tax Amt", "Grand Total", "Party", "5%", "0%"]]
    col_widths = [55, 65, 65, 60, 70, 140, 55, 55]

    total_taxable = Decimal('0.000')
    total_tax_amount = Decimal('0.000')
    total_rate5 = Decimal('0.000')
    total_rate0 = Decimal('0.000')

    seen_row_keys = set()
    total_grand_total = Decimal('0.000')

    for row in rows:
        detail_data.append([
            row['invoice_date'].strftime("%d-%m-%Y") if row['invoice_date'] else "",
            row['voucher_no'] or "",
            f"{row['taxable']:.3f}",
            f"{row['tax_amount']:.3f}",
            f"{row['grand_total']:.3f}",
            Paragraph(row['party'] or "", styles["Normal"]),
            f"{row['rate_5']:.3f}",
            f"{row['rate_0']:.3f}",
        ])

        total_taxable += row['taxable']
        total_tax_amount += row['tax_amount']
        total_rate5 += row['rate_5']
        total_rate0 += row['rate_0']

        # Grand total counted once per row_key — matches template JS logic
        if row['row_key'] not in seen_row_keys:
            seen_row_keys.add(row['row_key'])
            total_grand_total += row['grand_total']

    detail_data.append([
        "Total", "",
        f"{total_taxable:.3f}",
        f"{total_tax_amount:.3f}",
        f"{total_grand_total:.3f}",
        "",
        f"{total_rate5:.3f}",
        f"{total_rate0:.3f}",
    ])

    detail_table = Table(detail_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
        ('ALIGN', (6, 1), (7, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(detail_table)

    # === BUILD PDF (landscape) ===
    logo_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_head.jpg')
    footer_image_path = os.path.join(settings.MEDIA_ROOT, 'timesheet_head', 'silver_footer.jpg')
    
    build_pdf(
        filename=buffer,
        story=story,
        logo_path=logo_path,
        include_header=True,
        include_footer=True,
        footer_image_path=footer_image_path,
        doc_type="purchase_tax_report",
       
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="purchase_tax_report.pdf"'
    response.write(pdf)
    return response    

def create_asset_opening_pdf(asset_opening, include_header=True, include_footer=True, include_signature=True):
    """
    Build and return PDF response for Asset Opening Voucher.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Ledger ===
    ledger_name = str(asset_opening.ledger) if asset_opening.ledger else ''
    to_text = f"""<b>Ledger:</b> {ledger_name}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, FY Date ===
    right_data = [
        ["Voucher No:", asset_opening.voucher_no],
        ["Date:", asset_opening.date.strftime("%d-%m-%Y")],
        ["FY Date:", asset_opening.FY_date.strftime("%d-%m-%Y") if asset_opening.FY_date else ""],
    ]

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>ASSET OPENING VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: essential fields only ===
    detail_data = [["Sl.No", "Asset", "Description", "Serial No", "Location", "Purchase Date", "Cost", "Book Value"]]
    col_widths = [30, 85, 110, 65, 75, 65, 65, 65]

    total_cost = Decimal('0.000')
    total_book_value = Decimal('0.000')
    sl_no = 1

    for d in asset_opening.details.all():
        asset_name = str(d.asset) if d.asset else ''
        cost = d.cost or Decimal('0.000')
        book_value = d.book_value or Decimal('0.000')

        total_cost += cost
        total_book_value += book_value

        detail_data.append([
            str(sl_no),
            Paragraph(asset_name, styles["Normal"]),
            Paragraph(d.description or '', styles["Normal"]),
            d.serial_no or "-",
            Paragraph(d.location or '-', styles["Normal"]),
            d.purchase_date.strftime("%d-%m-%Y") if d.purchase_date else "-",
            f"{float(cost):.3f}",
            f"{float(book_value):.3f}",
        ])
        sl_no += 1

    detail_data.append(["", "", "", "", "", "Total", f"{float(total_cost):.3f}", f"{float(total_book_value):.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (-2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-3, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === OPENING TOTAL ===
    story.append(Paragraph(
        f"<b>Opening Total:</b> OMR {float(asset_opening.opening_total):.3f}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 20))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Prepared By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if include_signature:
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
        include_header=include_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if include_footer else None,
        doc_type="asset_opening",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="asset_opening_{asset_opening.voucher_no}.pdf"'
    response.write(pdf)
    return response    


def create_creditnote_pdf(creditnote, include_header=True, include_footer=True, include_signature=True):
    """
    Build and return PDF response for Credit Note.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Client ===
    client_name = creditnote.client.ledger_name if creditnote.client else ''
    to_text = f"""<b>Client:</b><br/>
    {client_name}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Ref No, Ledger ===
    right_data = [
        ["Voucher No:", creditnote.voucher_no],
        ["Date:", creditnote.date.strftime("%d-%m-%Y")],
        ["Ledger:", creditnote.ledger.ledger_name if creditnote.ledger else ""],
    ]

    if creditnote.ref_no:
        right_data.append(["Ref No:", creditnote.ref_no])

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>CREDIT NOTE</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: Type, Voucher No, Current Amount, Amount, Balance ===
    detail_data = [["Sl.No", "Type", "Voucher No", "Current Amount", "Amount", "Balance"]]
    col_widths = [35, 80, 100, 100, 100, 110]

    total_amount = Decimal('0.000')
    sl_no = 1

    for d in creditnote.creditnotedetail_set.all():
        voucher_type_id = d.voucherType_id

        display_voucher_no = str(d.VoucherNo)
        type_label = "Unknown"

        try:
            if voucher_type_id == 2:  # Invoice
                inv = Invoice.objects.get(pk=d.VoucherNo)
                display_voucher_no = inv.voucher_no
                type_label = "Invoice"
            elif voucher_type_id == 16:  # BillWiseOpening
                opening = BillWiseOpening.objects.get(pk=d.VoucherNo)
                display_voucher_no = getattr(opening, 'voucher_no', str(d.VoucherNo))
                type_label = "Opening"
        except Exception:
            type_label = {2: "Invoice", 16: "Opening"}.get(voucher_type_id, "Unknown")

        current_amount = d.CurrentAmount or Decimal('0.000')
        amount = d.Amount or Decimal('0.000')
        balance = current_amount - amount
        total_amount += amount

        detail_data.append([
            str(sl_no),
            type_label,
            display_voucher_no,
            f"{float(current_amount):.3f}",
            f"{float(amount):.3f}",
            f"{float(balance):.3f}",
        ])
        sl_no += 1

    detail_data.append(["", "", "", "", "Total", f"{float(total_amount):.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(total_amount)
    baisa_part = int(round((total_amount - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {float(total_amount):.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    if creditnote.remark:
        story.append(Paragraph(f"<b>Remark:</b> {creditnote.remark}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Received By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if include_signature:
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
        include_header=include_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if include_footer else None,
        doc_type="creditnote",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="creditnote_{creditnote.voucher_no}.pdf"'
    response.write(pdf)
    return response    


def create_debitnote_pdf(debitnote, include_header=True, include_footer=True, include_signature=True):
    """
    Build and return PDF response for Debit Note.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Supplier ===
    supplier_name = debitnote.supplier.ledger_name if debitnote.supplier else ''
    to_text = f"""<b>Supplier:</b><br/>
    {supplier_name}<br/>"""

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Ref No, Ledger ===
    right_data = [
        ["Voucher No:", debitnote.voucher_no],
        ["Date:", debitnote.date.strftime("%d-%m-%Y")],
        ["Ledger:", debitnote.ledger.ledger_name if debitnote.ledger else ""],
    ]

    if debitnote.ref_no:
        right_data.append(["Ref No:", debitnote.ref_no])

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>DEBIT NOTE</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === DETAILS TABLE: Type, Voucher No, Current Amount, Amount, Balance ===
    detail_data = [["Sl.No", "Type", "Voucher No", "Current Amount", "Amount", "Balance"]]
    col_widths = [35, 80, 100, 100, 100, 110]

    voucher_type_map = {
        1: ("Hire", FleetHire),
        13: ("Purchase", PurchaseMaster),
        16: ("Opening", BillWiseOpening),
        17: ("Asset Purchase", AssetPurchase),
    }

    total_amount = Decimal('0.000')
    sl_no = 1

    for d in debitnote.debitnotedetail_set.all():
        voucher_type_id = d.voucherType_id

        display_voucher_no = str(d.VoucherNo)
        type_label, model_cls = voucher_type_map.get(voucher_type_id, ("Unknown", None))

        if model_cls:
            try:
                obj = model_cls.objects.get(pk=d.VoucherNo)
                display_voucher_no = getattr(obj, 'voucher_no', str(d.VoucherNo))
            except Exception:
                pass

        current_amount = d.CurrentAmount or Decimal('0.000')
        amount = d.Amount or Decimal('0.000')
        balance = current_amount - amount
        total_amount += amount

        detail_data.append([
            str(sl_no),
            type_label,
            display_voucher_no,
            f"{float(current_amount):.3f}",
            f"{float(amount):.3f}",
            f"{float(balance):.3f}",
        ])
        sl_no += 1

    detail_data.append(["", "", "", "", "Total", f"{float(total_amount):.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(total_amount)
    baisa_part = int(round((total_amount - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {float(total_amount):.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    if debitnote.remark:
        story.append(Paragraph(f"<b>Remark:</b> {debitnote.remark}", styles["Normal"]))
        story.append(Spacer(1, 12))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Prepared By</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if include_signature:
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
        include_header=include_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if include_footer else None,
        doc_type="debitnote",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="debitnote_{debitnote.voucher_no}.pdf"'
    response.write(pdf)
    return response    


def create_asset_purchase_pdf(purchase, include_header=True, include_footer=True, include_signature=True):
    """
    Build and return PDF response for Asset Purchase Voucher.
    """
    buffer = BytesIO()
    story = []
    styles = getSampleStyleSheet()

    # === LEFT DATA: Supplier ===
    supplier_name = purchase.supplier.ledger_name if purchase.supplier else ''
    to_text = f"""<b>Supplier:</b><br/>
    {supplier_name}<br/>"""

    if purchase.mobile:
        to_text += f"Mobile: {purchase.mobile}<br/>"
    if purchase.agent:
        to_text += f"Agent: {purchase.agent}<br/>"

    to_para = Paragraph(to_text, styles["Normal"])
    left_data = [[to_para]]
    left_table = Table(left_data, colWidths=[280])

    # === RIGHT DATA: Voucher No, Date, Payment Mode, Invoice No, Ledger ===
    right_data = [
        ["Voucher No:", purchase.voucher_no],
        ["Date:", purchase.date.strftime("%d-%m-%Y")],
        ["Payment Mode:", purchase.payment_mode or ""],
        ["Ledger:", purchase.ledger.ledger_name if purchase.ledger else ""],
    ]

    if purchase.invoice_no:
        right_data.append(["Invoice No:", purchase.invoice_no])

    right_table = Table(right_data, colWidths=[100, 160])
    right_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))

    header_table = Table(
        [[left_table, right_table]],
        colWidths=[290, 260]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(Paragraph("<b><font size=14>ASSET PURCHASE VOUCHER</font></b>", ParagraphStyle('center', alignment=1)))
    story.append(Spacer(1, 12))
    story.append(header_table)
    story.append(Spacer(1, 15))

    # === ITEMS TABLE: essential columns only ===
    detail_data = [["Sl.No", "Asset", "Description", "Qty", "Rate", "Taxable", "VAT", "Total"]]
    col_widths = [30, 90, 130, 40, 60, 65, 55, 65]

    sl_no = 1
    for d in purchase.details.all():
        asset_name = str(d.asset) if d.asset else ''
        desc = d.description or ''
        qty = d.quantity or 0
        rate = d.rate or Decimal('0.000')
        taxable = d.taxable or Decimal('0.000')
        tax_amount = d.tax_amount or Decimal('0.000')
        total = d.total_amount or Decimal('0.000')

        detail_data.append([
            str(sl_no),
            Paragraph(asset_name, styles["Normal"]),
            Paragraph(desc, styles["Normal"]),
            f"{float(qty):.2f}",
            f"{float(rate):.3f}",
            f"{float(taxable):.3f}",
            f"{float(tax_amount):.3f}",
            f"{float(total):.3f}",
        ])
        sl_no += 1

    # === TOTALS (as saved, no recalculation) ===
    total_cost = purchase.total_cost or Decimal('0.000')
    total_discount = purchase.total_discount or Decimal('0.000')
    total_taxable = purchase.total_taxable or Decimal('0.000')
    total_vat_amount = purchase.total_vat_amount or Decimal('0.000')
    grand_total = purchase.grand_total or Decimal('0.000')

    detail_data.append(["", "", "", "", "", "", "Taxable", f"{float(total_taxable):.3f}"])
    detail_data.append(["", "", "", "", "", "", "VAT", f"{float(total_vat_amount):.3f}"])
    if total_discount:
        detail_data.append(["", "", "", "", "", "", "Discount", f"{float(total_discount):.3f}"])
    detail_data.append(["", "", "", "", "", "", "Grand Total", f"{float(grand_total):.3f}"])

    detail_table = Table(detail_data, colWidths=col_widths)
    detail_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(detail_table)
    story.append(Spacer(1, 12))

    # === TOTAL IN WORDS ===
    riyal_part = int(grand_total)
    baisa_part = int(round((grand_total - riyal_part) * 1000))

    riyal_words = num2words(riyal_part, to='cardinal', lang='en').capitalize()

    if baisa_part > 0:
        baisa_words = num2words(baisa_part, to='cardinal', lang='en').capitalize()
        amount_in_words = f"Omani Rial {riyal_words} and {baisa_words} Baisa Only"
    else:
        amount_in_words = f"Omani Rial {riyal_words} Only"

    story.append(Paragraph(
        f"<b>Amount (in words):</b> {amount_in_words} (OMR {float(grand_total):.3f})",
        styles["Normal"]
    ))
    story.append(Spacer(1, 20))

    # === SIGNATURE BOXES ===
    sig_left_text = Paragraph("<b>Supplier Signature</b>", styles["Normal"])
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
    story.append(Spacer(1, 25))

    # === Footer Function: Optional Signature Only ===
    def footer_func(canvas, doc):
        canvas.saveState()

        if include_signature:
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
        include_header=include_header,
        include_footer=True,
        footer_func=footer_func,
        footer_on_last_page=True,
        footer_image_path=footer_image_path if include_footer else None,
        doc_type="asset_purchase",
    )

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="asset_purchase_{purchase.voucher_no}.pdf"'
    response.write(pdf)
    return response    