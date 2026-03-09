from io import BytesIO
import os
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, PageTemplate, Frame
)
from reportlab.lib import colors
from inspections.models import GeneratedDocument, CompanyInfo


def footer_with_page_number(canvas, doc, inspection):
    """Add footer with inspection info and page number to each page"""
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    footer_text = f"Inspection Report | Serial: {inspection.equipment.serial_number} | Certificate: {inspection.certificate_number or 'N/A'}"
    canvas.drawString(0.75*inch, 0.4*inch, footer_text)
    canvas.drawRightString(doc.width + 0.75*inch, 0.4*inch, f"Page {doc.page}")
    canvas.restoreState()


def generate_package_pdf(inspection):
    """
    Generate multi-page inspection package PDF with:
    - Cover page
    - Details (sections, questions, answers)
    - Defects with embedded photos
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.45*inch,
                            leftMargin=0.55*inch, rightMargin=0.55*inch)

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold',
        spaceAfter=6,
        spaceBefore=6,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=16,
        spaceBefore=20
    )

    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=12
    )

    normal_style = styles['Normal']

    # ===== COVER PAGE =====
    # Helper function to create divider lines
    def create_divider():
        """Create a thin horizontal divider line"""
        divider = Table([['']], colWidths=[7.4*inch])
        divider.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return divider

    # Helper function to create info cards
    def create_info_card(title, fields_dict, width, height):
        """
        Creates a styled information card with title and field rows.
        title: string like "CUSTOMER INFORMATION"
        fields_dict: dict like {'Customer': 'MJ Electric', 'Location': 'North Yard'}
        width: card width in inches
        height: card height in inches
        Returns: Table object
        """
        card_data = []

        # Title row - will span both columns
        title_style = ParagraphStyle(
            'CardTitle',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            alignment=TA_LEFT,
            wordWrap='LTR',
            splitLongWords=0
        )
        # Title as a single-column row (will be handled by SPAN in table style)
        card_data.append([Paragraph(title, title_style), ''])

        # Field rows - filter out None/empty values
        label_style = ParagraphStyle(
            'CardLabel',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#333333')
        )
        value_style = ParagraphStyle(
            'CardValue',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1a1a1a')
        )

        for label, value in fields_dict.items():
            if value and str(value).strip():
                card_data.append([
                    Paragraph(f"{label}:", label_style),
                    Paragraph(str(value), value_style)
                ])

        # If no fields provided, show placeholder
        if len(card_data) == 1:
            placeholder_style = ParagraphStyle(
                'Placeholder',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor('#999999'),
                fontName='Helvetica-Oblique'
            )
            card_data.append([Paragraph(fields_dict.get('_placeholder', 'No information provided'), placeholder_style)])

        # Create table
        # Calculate column widths for two-column layout (label: value)
        if any(len(row) == 2 for row in card_data):
            col_widths = [width * 0.40, width * 0.60]
        else:
            col_widths = [width]

        card_table = Table(card_data, colWidths=col_widths)
        card_styles = [
            ('SPAN', (0, 0), (1, 0)),  # Span title across both columns
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ]
        card_table.setStyle(TableStyle(card_styles))

        return card_table

    eq = inspection.equipment
    customer = eq.customer

    # Zone 1: Header with logo (height: 0.55in)
    header_style = ParagraphStyle(
        'CoverHeader',
        parent=styles['Heading1'],
        fontSize=20,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=0,
        spaceBefore=0
    )

    # Try to load company logo
    logo_path = os.path.join(settings.BASE_DIR, 'ADV hex brighter inverted.png')
    header_content = []

    if os.path.exists(logo_path):
        # Create logo image with actual aspect ratio (2479:1138 ≈ 2.18:1)
        logo_height = 0.45*inch
        logo_width = logo_height * (2479 / 1138)
        logo_img = Image(logo_path, height=logo_height, width=logo_width)

        # Header table: text on left, logo on right
        header_data = [[
            Paragraph("ANSI A92.2 PERIODIC INSPECTION REPORT", header_style),
            logo_img
        ]]
        header_table = Table(header_data, colWidths=[7.4*inch - logo_width, logo_width])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)
    else:
        # No logo - just text
        story.append(Paragraph("ANSI A92.2 PERIODIC INSPECTION REPORT", header_style))

    # Bottom border for header
    header_line = Table([['']], colWidths=[7.4*inch])
    header_line.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_line)
    story.append(Spacer(1, 5))
    story.append(create_divider())
    story.append(Spacer(1, 5))

    # Zone 2: Status Banner (height: 0.7in, margin-top: 10pt)
    if inspection.status == 'completed' and inspection.overall_result:
        result_text = inspection.overall_result.upper()
    else:
        result_text = 'IN PROGRESS'

    # Determine background color
    if result_text == 'IN PROGRESS':
        bg_color = colors.HexColor('#e0e0e0')
    else:
        bg_color = colors.white

    banner_style = ParagraphStyle(
        'StatusBanner',
        parent=styles['Heading1'],
        fontSize=28,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        alignment=TA_CENTER,
        leading=32
    )

    banner_table = Table([[Paragraph(result_text, banner_style)]], colWidths=[7.4*inch], rowHeights=[0.85*inch])
    banner_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 5))
    story.append(create_divider())
    story.append(Spacer(1, 5))

    # Zone 3: Top Info Row (height: 1.45in, margin-top: 10pt)
    # Left card: CUSTOMER INFORMATION
    customer_fields = {}
    if customer:
        if customer.name:
            customer_fields['Customer'] = customer.name
        if customer.location:
            customer_fields['Location'] = customer.location
        if customer.contact_person_name:
            customer_fields['Contact'] = customer.contact_person_name

    if not customer_fields:
        customer_fields['_placeholder'] = 'No customer information provided'

    customer_card = create_info_card('CUSTOMER&nbsp;INFORMATION', customer_fields, 3.61*inch, 1.45*inch)

    # Right card: INSPECTION INFORMATION
    inspection_fields = {}
    if inspection.started_at:
        inspection_fields['Inspection Date'] = inspection.started_at.strftime('%Y-%m-%d')

    inspector_name = inspection.inspector.get_full_name() or inspection.inspector.username
    inspection_fields['Inspector'] = inspector_name

    cert_num = inspection.certificate_number or 'Pending finalization'
    inspection_fields['Certificate #'] = cert_num

    inspection_card = create_info_card('INSPECTION&nbsp;INFORMATION', inspection_fields, 3.61*inch, 1.45*inch)

    # Create row with both cards
    top_row_table = Table([[customer_card, inspection_card]], colWidths=[3.61*inch, 3.61*inch])
    top_row_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 9),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(top_row_table)
    story.append(Spacer(1, 5))
    story.append(create_divider())
    story.append(Spacer(1, 5))

    # Zone 4: Middle Info Row (height: 1.65in, margin-top: 10pt)
    # Left card: VEHICLE / CHASSIS
    vehicle_fields = {}
    if eq.vehicle_make:
        vehicle_fields['Make'] = eq.vehicle_make
    if eq.vehicle_model:
        vehicle_fields['Model'] = eq.vehicle_model
    if eq.vehicle_unit_number:
        vehicle_fields['Unit #'] = eq.vehicle_unit_number
    if eq.vehicle_vin:
        vehicle_fields['VIN'] = eq.vehicle_vin
    if eq.vehicle_year:
        vehicle_fields['Year'] = eq.vehicle_year
    if eq.vehicle_license_plate:
        vehicle_fields['Plate'] = eq.vehicle_license_plate

    if not vehicle_fields:
        vehicle_fields['_placeholder'] = 'No vehicle information on file'

    vehicle_card = create_info_card('VEHICLE&nbsp;/&nbsp;CHASSIS', vehicle_fields, 3.61*inch, 1.65*inch)

    # Right card: AERIAL DEVICE
    aerial_fields = {}
    if eq.make:
        aerial_fields['Manufacturer'] = eq.make
    if eq.model:
        aerial_fields['Model'] = eq.model
    if eq.serial_number:
        aerial_fields['Serial Number'] = eq.serial_number
    if eq.unit_number:
        aerial_fields['Unit #'] = eq.unit_number
    if eq.max_working_height:
        aerial_fields['Max Height'] = f"{eq.max_working_height} ft"

    # Show insulation status
    if eq.insulation_type == 'insulating':
        if eq.category:
            aerial_fields['Insulation Category'] = eq.category.upper()
        else:
            aerial_fields['Insulation Category'] = 'Insulating (Category not specified)'
    elif eq.insulation_type == 'non-insulating':
        aerial_fields['Insulation Category'] = 'Non-Insulating'
    else:
        aerial_fields['Insulation Category'] = 'Not specified'

    aerial_card = create_info_card('AERIAL&nbsp;DEVICE', aerial_fields, 3.61*inch, 1.65*inch)

    # Create row with both cards
    middle_row_table = Table([[vehicle_card, aerial_card]], colWidths=[3.61*inch, 3.61*inch])
    middle_row_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, -1), 9),
        ('RIGHTPADDING', (1, 0), (1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(middle_row_table)
    story.append(Spacer(1, 5))
    story.append(create_divider())
    story.append(Spacer(1, 5))

    # Zone 5: Result Summary Strip (height: 0.72in, margin-top: 10pt)
    result_summary_data = [['RESULT SUMMARY']]

    # Determine result logic
    if inspection.status != 'completed':
        overall_result_text = 'Pending Completion'
        status_text = 'In progress'
        valid_until_text = '—'
    elif inspection.overall_result == 'pass':
        overall_result_text = 'PASS'
        status_text = 'Finalized'
        # Calculate valid until date (typically 1 year from completion)
        if inspection.completed_at:
            from datetime import timedelta
            valid_until = inspection.completed_at + timedelta(days=365)
            valid_until_text = valid_until.strftime('%Y-%m-%d')
        else:
            valid_until_text = '—'
    elif inspection.overall_result == 'fail':
        overall_result_text = 'FAIL'
        status_text = 'Finalized'
        valid_until_text = '—'
    else:
        overall_result_text = 'Pending Completion'
        status_text = 'In progress'
        valid_until_text = '—'

    # Create 3-column row
    col_style = ParagraphStyle(
        'ResultCol',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER
    )

    result_summary_data.append([
        Paragraph(f"<b>Overall Result:</b><br/>{overall_result_text}", col_style),
        Paragraph(f"<b>Status:</b><br/>{status_text}", col_style),
        Paragraph(f"<b>Valid Until:</b><br/>{valid_until_text}", col_style)
    ])

    result_summary_table = Table(result_summary_data, colWidths=[7.4*inch / 3] * 3, rowHeights=[0.25*inch, 0.47*inch])
    result_summary_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(result_summary_table)
    story.append(Spacer(1, 5))
    story.append(create_divider())
    story.append(Spacer(1, 7))

    # Zone 6: Company Footer (height: 0.55in, margin-top: 12pt)
    # Get company info
    try:
        company = CompanyInfo.objects.first()
        if company:
            # Line 1: company name, address
            line1_parts = []
            if company.name:
                line1_parts.append(company.name)
            if company.address_line1:
                addr_parts = [company.address_line1]
                if company.city and company.state:
                    addr_parts.append(f"{company.city}, {company.state} {company.zip_code or ''}".strip())
                line1_parts.append(', '.join(addr_parts))

            line1 = ' | '.join(line1_parts) if line1_parts else ''

            # Line 2: phone, email, certifications
            line2_parts = []
            if company.phone:
                line2_parts.append(f"Phone: {company.phone}")
            if company.email:
                line2_parts.append(f"Email: {company.email}")
            if company.certifications:
                line2_parts.append(company.certifications)

            line2 = ' | '.join(line2_parts) if line2_parts else ''

            footer_text = f"{line1}<br/>{line2}" if line1 or line2 else "Inspection Company Information"
        else:
            footer_text = "Inspection Company Information"
    except:
        footer_text = "Inspection Company Information"

    footer_style = ParagraphStyle(
        'CompanyFooter',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#555555')
    )

    # Top border line
    footer_line = Table([['']], colWidths=[7.4*inch])
    footer_line.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(footer_line)

    story.append(Paragraph(footer_text, footer_style))

    # Page break before executive summary
    story.append(PageBreak())

    # ===== EXECUTIVE SUMMARY =====
    # Header
    exec_summary_header_style = ParagraphStyle(
        'ExecSummaryHeader',
        parent=styles['Heading1'],
        fontSize=18,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=4,
        spaceBefore=0
    )
    exec_summary_subtitle_style = ParagraphStyle(
        'ExecSummarySubtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12
    )

    story.append(Paragraph("EXECUTIVE SUMMARY", exec_summary_header_style))
    story.append(Paragraph("ANSI A92.2 Periodic Inspection", exec_summary_subtitle_style))
    story.append(Spacer(1, 0.1*inch))

    # Calculate statistics
    total_questions = inspection.answers.count()
    pass_count = inspection.answers.filter(status='pass').count()
    fail_count = inspection.answers.filter(status='fail').count()
    na_count = inspection.answers.filter(status='na').count()
    defect_count = inspection.defects.count()
    test_module_count = inspection.test_modules.count()

    # Calculate section breakdown
    freq_answers = inspection.answers.filter(question__section__title__icontains='Frequent')
    freq_total = freq_answers.count()
    freq_complete = freq_answers.exclude(status='na').count()

    periodic_answers = inspection.answers.filter(question__section__title__icontains='Periodic')
    periodic_total = periodic_answers.count()
    periodic_complete = periodic_answers.exclude(status='na').count()

    # Get all test module templates and their completion status
    from inspections.models import Template
    all_test_templates = Template.objects.filter(kind='test').order_by('name')
    test_module_status = {}
    for template in all_test_templates:
        performed_count = inspection.test_modules.filter(template=template).count()
        test_module_status[template.name] = performed_count > 0

    # Status Block: 3-column card
    status_block_data = []

    if inspection.status == 'completed':
        status_display = 'Completed'
        result_display = inspection.overall_result.upper() if inspection.overall_result else 'N/A'
        finalized_date = inspection.completed_at.strftime('%Y-%m-%d') if inspection.completed_at else 'N/A'
    else:
        status_display = 'In Progress'
        result_display = 'Not determined'
        finalized_date = '—'

    status_style = ParagraphStyle(
        'StatusBlock',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER
    )

    status_block_data.append([
        Paragraph(f"<b>Inspection Status:</b><br/>{status_display}", status_style),
        Paragraph(f"<b>Overall Result:</b><br/>{result_display}", status_style),
        Paragraph(f"<b>Finalized Date:</b><br/>{finalized_date}", status_style)
    ])

    status_block_table = Table(status_block_data, colWidths=[7.4*inch / 3] * 3)
    status_block_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(status_block_table)
    story.append(Spacer(1, 0.15*inch))

    # Metrics Row: 5 metric cards
    # Helper function to create individual metric cards
    def create_metric_card(number, label):
        """Create a bordered metric card with number on top and label on bottom"""
        metric_number_style = ParagraphStyle(
            'MetricNumber',
            parent=styles['Normal'],
            fontSize=24,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.black
        )
        metric_label_style = ParagraphStyle(
            'MetricLabel',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666')
        )

        card_data = [
            [Paragraph(str(number), metric_number_style)],
            [Paragraph(label.upper(), metric_label_style)]
        ]

        card = Table(card_data, rowHeights=[0.6*inch, 0.4*inch])
        card.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return card

    # Create 5 separate metric cards in a single-row table
    metrics_data = [[
        create_metric_card(total_questions, "TOTAL ITEMS"),
        create_metric_card(pass_count, "PASSED"),
        create_metric_card(fail_count, "FAILED"),
        create_metric_card(na_count, "N/A"),
        create_metric_card(defect_count, "DEFECTS")
    ]]

    metrics_table = Table(metrics_data, colWidths=[7.4*inch / 5] * 5)
    metrics_table.setStyle(TableStyle([
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.15*inch))

    # Section Status Table
    section_header_style = ParagraphStyle(
        'SectionTableHeader',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=8
    )
    story.append(Paragraph("Section Status", section_header_style))

    section_table_style = ParagraphStyle(
        'SectionTableText',
        parent=styles['Normal'],
        fontSize=9
    )

    # Determine section statuses
    if inspection.status == 'completed':
        # Show PASS/FAIL/Not performed
        freq_status = 'PASS' if freq_complete > 0 and fail_count == 0 else ('FAIL' if fail_count > 0 else 'Not performed')
        periodic_status = 'PASS' if periodic_complete > 0 and fail_count == 0 else ('FAIL' if fail_count > 0 else 'Not performed')
    else:
        # Show completion status
        freq_status = f"{freq_complete} / {freq_total} complete" if freq_total > 0 else "Not started"
        periodic_status = f"{periodic_complete} / {periodic_total} complete" if periodic_total > 0 else "Not started"

    # Build section data with all test modules
    section_data = [
        ['Frequent Inspection', freq_status],
        ['Periodic Inspection', periodic_status],
    ]

    # Add all test module types
    for template_name, is_performed in test_module_status.items():
        # Shorten display name
        display_name = template_name.replace('ANSI A92.2 (2021) ', '').replace('Test - ', '').replace('Dielectric Test - ', 'Dielectric - ')
        status = 'Performed' if is_performed else 'Not Performed'
        section_data.append([display_name, status])

    section_table = Table(section_data, colWidths=[5.2*inch, 2.2*inch])
    section_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(section_table)
    story.append(Spacer(1, 0.15*inch))

    # Key Findings (state-aware)
    findings_header_style = ParagraphStyle(
        'FindingsHeader',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=8
    )
    story.append(Paragraph("Key Findings", findings_header_style))

    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=styles['Normal'],
        fontSize=9,
        leftIndent=12,
        spaceAfter=4
    )

    # STATE-AWARE logic
    if inspection.status != 'completed':
        # In progress
        story.append(Paragraph("• Inspection has not been finalized", bullet_style))
        story.append(Paragraph("• Required sections remain incomplete", bullet_style))
        if defect_count > 0:
            story.append(Paragraph(f"• {defect_count} defect(s) have been documented so far", bullet_style))
    elif inspection.overall_result == 'pass' and fail_count == 0 and defect_count == 0:
        # Completed and passed with no issues
        story.append(Paragraph("• All required inspection items passed", bullet_style))
        story.append(Paragraph("• No defects or safety concerns identified", bullet_style))
        story.append(Paragraph("• Unit is approved for continued service", bullet_style))
    else:
        # Completed with defects/failures
        if defect_count > 0:
            story.append(Paragraph(f"• {defect_count} defect(s) documented with photos and notes", bullet_style))
        if fail_count > 0:
            story.append(Paragraph(f"• {fail_count} inspection item(s) failed", bullet_style))
        story.append(Paragraph("• Unit must not be returned to service until repaired", bullet_style))
        if pass_count > 0:
            story.append(Paragraph(f"• {pass_count} item(s) passed and meet ANSI A92.2 requirements", bullet_style))

    story.append(Spacer(1, 0.15*inch))

    # Next Action
    action_header_style = ParagraphStyle(
        'ActionHeader',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.black,
        spaceAfter=8
    )
    story.append(Paragraph("Next Action", action_header_style))

    action_style = ParagraphStyle(
        'ActionStyle',
        parent=styles['Normal'],
        fontSize=9
    )

    # Determine next action
    if inspection.status != 'completed':
        next_action = "Complete all required sections and finalize the inspection."
    elif inspection.overall_result == 'pass' and fail_count == 0 and defect_count == 0:
        next_action = "File report and issue certificate."
    else:
        next_action = "Repair identified defects and perform re-inspection before returning unit to service."

    story.append(Paragraph(next_action, action_style))

    # ===== BUILD DEFECT MAPPING =====
    # Create a mapping of question_id -> defect_appendix_number for referencing
    defects = inspection.defects.prefetch_related('photos', 'question').all()
    defect_mapping = {}
    for idx, defect in enumerate(defects, 1):
        if defect.question:
            defect_mapping[defect.question.id] = idx

    # Page break before details (only if test modules or inspection answers exist)
    test_modules = inspection.test_modules.select_related('template').all()
    has_content_after_summary = test_modules.exists() or inspection.answers.exists()

    if has_content_after_summary:
        story.append(PageBreak())

        # ===== INSPECTION DISCLAIMER =====
        disclaimer_heading_style = ParagraphStyle(
            'DisclaimerHeading',
            parent=heading_style,
            fontSize=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            alignment=TA_CENTER
        )

        disclaimer_body_style = ParagraphStyle(
            'DisclaimerBody',
            parent=normal_style,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#444444'),
            alignment=TA_JUSTIFY,
            spaceAfter=10
        )

        # Read disclaimer from file
        disclaimer_path = os.path.join(settings.BASE_DIR, 'disclaimer.txt')
        if os.path.exists(disclaimer_path):
            with open(disclaimer_path, 'r', encoding='utf-8') as f:
                disclaimer_lines = f.readlines()

            # Add disclaimer heading
            story.append(Paragraph("INSPECTION DISCLAIMER", disclaimer_heading_style))
            story.append(Spacer(1, 0.1*inch))

            # Add disclaimer paragraphs (skip title line and empty lines at start)
            started = False
            for line in disclaimer_lines:
                line = line.strip()
                if not started and line and line != 'Inspection Disclaimer':
                    started = True
                if started and line:
                    story.append(Paragraph(line, disclaimer_body_style))

            story.append(Spacer(1, 0.3*inch))

    # ===== TEST MODULES SECTION (if any) =====
    # Extract and format test modules as dedicated test result pages
    for test_module in test_modules:
        if not test_module.test_data:
            continue

        story.append(PageBreak())

        # Determine test type and format accordingly
        test_name = test_module.template.name.upper()
        is_dielectric = 'DIELECTRIC' in test_name
        is_load = 'LOAD' in test_name

        # Test results header
        if is_dielectric:
            story.append(Paragraph("DIELECTRIC TEST RESULTS", heading_style))
            story.append(Paragraph("ANSI A92.2 Section 5.4.3", subheading_style))
        elif is_load:
            story.append(Paragraph("LOAD TEST RESULTS", heading_style))
        else:
            story.append(Paragraph(f"{test_name} RESULTS", heading_style))

        story.append(Spacer(1, 0.25*inch))

        import json
        # Parse template definition to get field labels
        field_labels = {}
        if hasattr(test_module.template, 'definition') and test_module.template.definition:
            try:
                template_def = json.loads(test_module.template.definition) if isinstance(test_module.template.definition, str) else test_module.template.definition
                for field in template_def.get('fields', []):
                    field_labels[field.get('code')] = field.get('label', field.get('code'))
            except (json.JSONDecodeError, AttributeError):
                pass

        # Create clean test results table (industry standard format)
        test_data_rows = []
        for key, value in test_module.test_data.items():
            label = field_labels.get(key, key.replace('_', ' ').title())
            # Format the value
            display_value = str(value)
            if isinstance(value, (int, float)) and key in ['voltage', 'test_voltage', 'applied_voltage']:
                display_value = f"{value} kV"
            elif isinstance(value, (int, float)) and 'current' in key.lower():
                display_value = f"{value} µA"
            elif isinstance(value, (int, float)) and 'capacity' in key.lower():
                display_value = f"{value} lbs"
            elif isinstance(value, (int, float)) and 'duration' in key.lower():
                display_value = f"{value} minutes"

            test_data_rows.append([label, display_value])

        # Industry-style formatting: clean, bold labels, large values
        test_table = Table(test_data_rows, colWidths=[2.5*inch, 4*inch])
        test_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, -1), 11),
            ('FONTSIZE', (1, 0), (1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        story.append(test_table)
        story.append(Spacer(1, 0.3*inch))

        # Add test conditions section for dielectric tests
        if is_dielectric:
            story.append(Paragraph("<b>Test Conditions</b>", subheading_style))
            conditions = [
                "• Vehicle grounded",
                "• Hydraulic lines filled with oil",
                "• Electrical continuity verified",
                "• Boom positioned per ANSI Figure 1"
            ]
            for condition in conditions:
                story.append(Paragraph(condition, normal_style))
            story.append(Spacer(1, 0.2*inch))

    # ===== DETAILS SECTION =====
    # Group answers hierarchically by inspection phase, then subsection
    # Separate test module answers from periodic/frequent inspection answers
    answers_by_phase = {}
    test_module_answers = {}  # Track test module answers separately

    # Get list of test module template IDs
    test_module_template_ids = set(inspection.test_modules.values_list('template_id', flat=True))

    for answer in inspection.answers.select_related('question__section').order_by(
        'question__section__order', 'question__order'
    ):
        section = answer.question.section
        section_title = section.title

        # Check if this section belongs to a test module
        is_test_module = section.template_id in test_module_template_ids

        # Extract phase and subsection from title (e.g., "Frequent Inspection - Visual Walkaround")
        if ' - ' in section_title:
            phase, subsection = section_title.split(' - ', 1)
        else:
            # Handle sections without dash (like test modules)
            phase = section_title
            subsection = None

        # Separate test module answers
        if is_test_module:
            if phase not in test_module_answers:
                test_module_answers[phase] = {
                    'ansi_ref': section.ansi_reference,
                    'sections': {}
                }
            if section_title not in test_module_answers[phase]['sections']:
                test_module_answers[phase]['sections'][section_title] = {
                    'section': section,
                    'answers': []
                }
            test_module_answers[phase]['sections'][section_title]['answers'].append(answer)
        else:
            # Regular periodic/frequent inspection answers
            # Create phase group if doesn't exist
            if phase not in answers_by_phase:
                answers_by_phase[phase] = {
                    'ansi_ref': section.ansi_reference if not subsection else None,
                    'subsections': {}
                }

            # Add to appropriate subsection or phase directly
            if subsection:
                if subsection not in answers_by_phase[phase]['subsections']:
                    answers_by_phase[phase]['subsections'][subsection] = {
                        'section': section,
                        'answers': []
                    }
                answers_by_phase[phase]['subsections'][subsection]['answers'].append(answer)
            else:
                # No subsection, add directly to phase
                if 'direct_answers' not in answers_by_phase[phase]:
                    answers_by_phase[phase]['direct_answers'] = {
                        'section': section,
                        'answers': []
                    }
                answers_by_phase[phase]['direct_answers']['answers'].append(answer)

    # Keep functional tests in Frequent Inspection section (no longer separate)

    # Define system groupings for better readability
    FREQUENT_GROUPING = {
        'General Condition': ['Visual Walkaround', 'Damaged Components'],
        'Controls': ['Controls and Interlocks'],
        'Safety Devices': ['Safety Devices'],
        'Insulating Components': ['Insulating Components'],
        'Hydraulic / Pneumatic Systems': ['Hydraulic and Pneumatic Systems'],
        'Electrical Systems': ['Electrical Systems'],
        'Functional Tests': ['Functional Tests'],
        'Markings and Decals': ['Markings and Decals'],
        'Placards and Test Expiration': ['Placards and Test Expiration']
    }

    PERIODIC_GROUPING = {
        'Structural Components': ['Structural Components', 'Welds'],
        'Mechanical Components': ['Wear Components', 'Fasteners'],
        'Hydraulic System': ['Hydraulic System Settings', 'Hoses and Fittings', 'Hydraulic Cylinders', 'Filters'],
        'Electrical Components': ['Electrical Components'],
        'Boom Operation': ['Boom Performance'],
        'Markings and Identification': ['Markings'],
        'Insulating System': ['Vacuum Limiting Systems', 'Insulating Boom Cleanliness'],
        'Upper Control Resistance': ['Upper Control Resistance']
    }

    def regroup_by_system(phase_name, subsections_dict):
        """Regroup subsections into logical equipment systems"""
        if phase_name == 'Frequent Inspection':
            grouping = FREQUENT_GROUPING
        elif phase_name == 'Periodic Inspection':
            grouping = PERIODIC_GROUPING
        else:
            # No regrouping for other phases
            return {name: [data] for name, data in subsections_dict.items()}

        # Build new structure
        system_groups = {}
        for system_name, subsection_names in grouping.items():
            system_groups[system_name] = []
            for subsection_name in subsection_names:
                if subsection_name in subsections_dict:
                    system_groups[system_name].append(subsections_dict[subsection_name])

        # Handle any subsections not in grouping (fallback)
        for subsection_name, data in subsections_dict.items():
            found = False
            for subsection_list in grouping.values():
                if subsection_name in subsection_list:
                    found = True
                    break
            if not found:
                # Create standalone system for ungrouped items
                system_groups[subsection_name] = [data]

        # Remove empty systems
        return {k: v for k, v in system_groups.items() if v}

    # Render each phase with its subsections
    for phase_name, phase_data in answers_by_phase.items():
        # Phase header (major heading)
        story.append(PageBreak())
        story.append(Paragraph(phase_name.upper(), heading_style))

        # ANSI reference below phase title - ultra-compact
        if phase_data.get('ansi_ref'):
            phase_ansi_style = ParagraphStyle(
                'PhaseANSIRef',
                parent=normal_style,
                fontSize=9,
                textColor=colors.HexColor('#666666'),
                spaceAfter=3
            )
            story.append(Paragraph(f"<i>ANSI A92.2 Section {phase_data['ansi_ref']}</i>", phase_ansi_style))

        # Render direct answers if any (for non-hierarchical sections)
        if 'direct_answers' in phase_data:
            answers = phase_data['direct_answers']['answers']
            section = phase_data['direct_answers']['section']
            render_answer_table(story, answers, section, subheading_style, normal_style, defect_mapping, show_header=True)

        # Render subsections and collect stats
        phase_total = 0
        phase_passed = 0
        phase_failed = 0
        phase_na = 0

        # Regroup subsections into logical systems
        system_groups = regroup_by_system(phase_name, phase_data['subsections'])

        # Track if we've shown the table header yet
        header_shown = False

        for system_name, subsection_list in system_groups.items():
            # System title (replaces subsection title) - ultra-compact spacing
            system_title_style = ParagraphStyle(
                'SystemTitle',
                parent=subheading_style,
                fontSize=10,
                fontName='Helvetica-Bold',
                spaceAfter=1,  # Minimal space before items
                spaceBefore=4   # Small space from previous section
            )
            story.append(Paragraph(system_name, system_title_style))

            # Collect all answers from all subsections in this system
            all_answers = []
            for subsection_data in subsection_list:
                all_answers.extend(subsection_data['answers'])

            # Sort answers: FAIL first, then PASS, then NA
            def sort_key(answer):
                status_order = {'fail': 0, 'pass': 1, 'na': 2}
                return status_order.get(answer.status.lower(), 3)
            all_answers.sort(key=sort_key)

            # Get section for ANSI reference (use first subsection's section)
            section = subsection_list[0]['section'] if subsection_list else None

            # Show header only on first system
            render_answer_table(story, all_answers, section, subheading_style, normal_style, defect_mapping, show_header=(not header_shown))
            header_shown = True

            # Count answers for summary
            for answer in all_answers:
                phase_total += 1
                if answer.status == 'pass':
                    phase_passed += 1
                elif answer.status == 'fail':
                    phase_failed += 1
                else:
                    phase_na += 1

        # Section summaries removed for compact layout (totals already in Executive Summary)

    # ===== TEST MODULE QUESTION RESULTS =====
    # Render each test module's questions on its own page
    for test_module_name, test_module_data in test_module_answers.items():
        story.append(PageBreak())

        # Test module header
        test_heading = test_module_name.upper()
        if test_module_data.get('ansi_ref'):
            test_heading = f"{test_module_name.upper()} (ANSI {test_module_data['ansi_ref']})"
        story.append(Paragraph(test_heading, heading_style))
        story.append(Spacer(1, 0.25*inch))

        # Render each section within the test module
        for section_title, section_data in test_module_data['sections'].items():
            section = section_data['section']
            answers = section_data['answers']

            # Section title if it's different from the module name
            if section_title != test_module_name:
                section_heading = section_title
                if section.ansi_reference:
                    section_heading = f"{section_title} (ANSI {section.ansi_reference})"
                story.append(Paragraph(section_heading, subheading_style))

            render_answer_table(story, answers, section, subheading_style, normal_style, defect_mapping)

    # ===== APPENDIX A: DEFECTS SECTION =====
    # Moved to end of document for better organization
    if defects.exists():
        story.append(PageBreak())
        appendix_heading_style = ParagraphStyle(
            'AppendixHeading',
            parent=heading_style,
            fontSize=18,
            fontName='Helvetica-Bold',
            textColor=colors.black,
            spaceAfter=12
        )
        story.append(Paragraph("APPENDIX A: DEFECTS", appendix_heading_style))
        story.append(Spacer(1, 0.15*inch))

        for idx, defect in enumerate(defects, 1):
            # Each defect gets its own page (except first one)
            if idx > 1:
                story.append(PageBreak())

            # Defect header with appendix number
            defect_header_style = ParagraphStyle(
                'DefectHeader',
                parent=subheading_style,
                fontSize=14,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#e74c3c'),
                spaceAfter=10,
                spaceBefore=0
            )
            story.append(Paragraph(f"Defect A-{idx}", defect_header_style))

            # Build defect information table
            defect_data = []

            if defect.question:
                # ANSI reference with parent clause (avoid duplicates)
                question_ref = ""
                section_ref = defect.question.section.ansi_reference
                question_ansi = defect.question.ansi_reference

                if section_ref and question_ansi:
                    # Only combine if they're different
                    if section_ref != question_ansi:
                        question_ref = f"ANSI A92.2 §{section_ref}/{question_ansi}"
                    else:
                        question_ref = f"ANSI A92.2 §{section_ref}"
                elif section_ref:
                    question_ref = f"ANSI A92.2 §{section_ref}"
                elif question_ansi:
                    question_ref = f"ANSI A92.2 §{question_ansi}"

                # Display ANSI reference prominently as separate row
                if question_ref:
                    defect_data.append(['Standard Reference:', Paragraph(f"<b>{question_ref}</b>", normal_style)])

                # Show the inspection question/requirement
                question_display = defect.question.prompt
                defect_data.append(['Requirement:', Paragraph(question_display, normal_style)])

                # Get the answer to show inspector's notes
                try:
                    answer = inspection.answers.filter(question=defect.question).first()
                    if answer and answer.notes:
                        inspector_note = answer.notes
                        defect_data.append(['Inspector Notes:', Paragraph(inspector_note, normal_style)])
                except:
                    pass

            # Only show defect description if it differs from the question text (not redundant)
            if defect.note and defect.question and defect.note != f"{defect.question.prompt[:100]} - Item does not meet ANSI A92.2 requirements":
                # Check if it's not just a copy of the question
                if not defect.note.startswith(defect.question.prompt[:50]):
                    defect_note_style = ParagraphStyle(
                        'DefectNote',
                        parent=normal_style,
                        fontSize=10,
                        leading=14,
                        textColor=colors.HexColor('#1a1a1a')
                    )
                    defect_data.append(['Defect Description:', Paragraph(f"<b>{defect.note}</b>", defect_note_style)])

            # Create defect info table
            defect_table = Table(defect_data, colWidths=[1.6*inch, 5.4*inch])
            defect_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e74c3c')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ]))
            story.append(defect_table)
            story.append(Spacer(1, 0.2*inch))

            # Photos - dynamic layout based on count, scaled to fit on one page
            photos = list(defect.photos.all())
            if photos:
                # Photos heading
                photo_heading_style = ParagraphStyle(
                    'PhotoHeading',
                    parent=normal_style,
                    fontSize=11,
                    fontName='Helvetica-Bold',
                    spaceAfter=6
                )
                story.append(Paragraph(f"Evidence Photos ({len(photos)})", photo_heading_style))

                num_photos = len(photos)

                if num_photos == 1:
                    # Single photo - large, centered
                    try:
                        img = Image(photos[0].image.path, width=5.5*inch, height=4.1*inch, kind='proportional')
                        story.append(img)
                        if photos[0].caption:
                            caption_style = ParagraphStyle('Caption', parent=normal_style, fontSize=9, textColor=colors.HexColor('#666'), alignment=TA_CENTER)
                            story.append(Paragraph(f"<i>{photos[0].caption}</i>", caption_style))
                    except Exception:
                        story.append(Paragraph(f"[Photo could not be loaded]", normal_style))

                elif num_photos == 2:
                    # 2 photos - stacked vertically, larger
                    for photo in photos:
                        try:
                            img = Image(photo.image.path, width=5.0*inch, height=3.75*inch, kind='proportional')
                            story.append(img)
                            if photo.caption:
                                caption_style = ParagraphStyle('PhotoCaption', parent=normal_style, fontSize=9, textColor=colors.HexColor('#666'), alignment=TA_CENTER, spaceAfter=8)
                                story.append(Paragraph(f"<i>{photo.caption}</i>", caption_style))
                        except Exception:
                            story.append(Paragraph(f"[Photo unavailable]", normal_style))
                        story.append(Spacer(1, 0.15*inch))

                elif num_photos in [3, 4]:
                    # 3-4 photos - 2 per row, medium size
                    photo_table_data = []
                    photo_row = []

                    for photo_idx, photo in enumerate(photos):
                        try:
                            img = Image(photo.image.path, width=3.0*inch, height=2.25*inch, kind='proportional')
                            photo_cell = [img]
                            if photo.caption:
                                caption_style = ParagraphStyle('PhotoCaption', parent=normal_style, fontSize=8, textColor=colors.HexColor('#666'), alignment=TA_CENTER)
                                photo_cell.append(Paragraph(f"<i>{photo.caption}</i>", caption_style))
                            photo_row.append(photo_cell)

                            if len(photo_row) == 2 or photo_idx == len(photos) - 1:
                                while len(photo_row) < 2:
                                    photo_row.append([Paragraph('', normal_style)])
                                photo_table_data.append(photo_row)
                                photo_row = []
                        except Exception:
                            photo_row.append([Paragraph("[Photo unavailable]", normal_style)])
                            if len(photo_row) == 2:
                                photo_table_data.append(photo_row)
                                photo_row = []

                    photo_table = Table(photo_table_data, colWidths=[3.5*inch, 3.5*inch])
                    photo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 3),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    story.append(photo_table)

                else:
                    # 5+ photos - 2 per row, smaller to fit all on page
                    photo_table_data = []
                    photo_row = []

                    for photo_idx, photo in enumerate(photos):
                        try:
                            # Compact size for many photos
                            img = Image(photo.image.path, width=2.5*inch, height=1.9*inch, kind='proportional')
                            photo_cell = [img]
                            if photo.caption:
                                caption_style = ParagraphStyle('PhotoCaption', parent=normal_style, fontSize=7, textColor=colors.HexColor('#666'), alignment=TA_CENTER)
                                photo_cell.append(Paragraph(f"<i>{photo.caption}</i>", caption_style))
                            photo_row.append(photo_cell)

                            if len(photo_row) == 2 or photo_idx == len(photos) - 1:
                                while len(photo_row) < 2:
                                    photo_row.append([Paragraph('', normal_style)])
                                photo_table_data.append(photo_row)
                                photo_row = []
                        except Exception:
                            photo_row.append([Paragraph("[Photo unavailable]", normal_style)])
                            if len(photo_row) == 2:
                                photo_table_data.append(photo_row)
                                photo_row = []

                    photo_table = Table(photo_table_data, colWidths=[3.5*inch, 3.5*inch])
                    photo_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 2),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(photo_table)

    # Build PDF with footer on each page
    doc.build(story, onFirstPage=lambda c, d: footer_with_page_number(c, d, inspection),
              onLaterPages=lambda c, d: footer_with_page_number(c, d, inspection))

    # Save to GeneratedDocument
    buffer.seek(0)
    filename = f"inspection_package_{inspection.id}.pdf"

    # Delete old package documents for this inspection (keep only latest)
    GeneratedDocument.objects.filter(
        inspection=inspection,
        doc_type='package'
    ).delete()

    doc_obj = GeneratedDocument.objects.create(
        inspection=inspection,
        doc_type='package',
        generator_version='1.0.0'
    )
    doc_obj.file.save(filename, ContentFile(buffer.read()), save=True)

    return doc_obj


def render_answer_table(story, answers, section, subheading_style, normal_style, defect_mapping=None, show_header=False):
    """Render inspection answers in ultra-compact format - NO HEADERS, minimal spacing"""
    if not answers:
        return

    if defect_mapping is None:
        defect_mapping = {}

    # Ultra-compact row style (PASS items)
    compact_style = ParagraphStyle(
        'CompactRow',
        parent=normal_style,
        fontSize=9,
        leftIndent=0,
        spaceAfter=1,  # Minimal spacing between rows
        leading=11
    )

    # Render all answers as simple rows (no table, no header)
    for answer in answers:
        status = answer.status.upper()
        item_text = answer.question.prompt

        # Add measurement if present
        if answer.measurement_value is not None:
            measurement = f"{answer.measurement_value} {answer.question.measurement_unit or ''}".strip()
            item_text += f" <b>[{measurement}]</b>"

        # Build row content
        status_text = f"<b>{status}</b>"

        # Check if this item has notes or is failed
        has_notes = answer.notes and answer.notes.strip() and not (answer.notes.startswith('Question ') and ' - ' in answer.notes)
        is_failed = status == 'FAIL'
        has_defect = answer.question.id in defect_mapping

        # FAIL items get background color and expanded format
        if is_failed:
            # Use table for background color
            fail_data = [[Paragraph(status_text, compact_style), Paragraph(item_text, compact_style)]]
            fail_table = Table(fail_data, colWidths=[0.9*inch, 6.5*inch])
            fail_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffebee')),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(fail_table)

            # Add notes/references for failed items
            if has_notes or has_defect:
                # Build ANSI reference if available (avoid duplicates)
                ansi_ref = ""
                section_ref = answer.question.section.ansi_reference
                question_ref = answer.question.ansi_reference

                if section_ref and question_ref:
                    # Only combine if they're different
                    if section_ref != question_ref:
                        ansi_ref = f"ANSI A92.2 §{section_ref}/{question_ref}"
                    else:
                        ansi_ref = f"ANSI A92.2 §{section_ref}"
                elif section_ref:
                    ansi_ref = f"ANSI A92.2 §{section_ref}"
                elif question_ref:
                    ansi_ref = f"ANSI A92.2 §{question_ref}"

                # Add defect appendix reference
                defect_ref = ""
                if has_defect:
                    defect_num = defect_mapping[answer.question.id]
                    defect_ref = f"See Appendix A-{defect_num}"

                # Combine note components
                note_parts = []
                if has_notes:
                    note_parts.append(f"Note: {answer.notes}")
                if ansi_ref:
                    note_parts.append(f"[{ansi_ref}]")
                if defect_ref:
                    note_parts.append(f"({defect_ref})")

                full_note = " ".join(note_parts)
                note_style = ParagraphStyle(
                    'FailNote',
                    parent=normal_style,
                    fontSize=8,
                    leftIndent=16,
                    textColor=colors.HexColor('#555555'),
                    spaceAfter=3
                )
                story.append(Paragraph(f"<i>{full_note}</i>", note_style))
        else:
            # PASS items - ultra-compact paragraph format
            story.append(Paragraph(f"{status_text}  {item_text}", compact_style))
