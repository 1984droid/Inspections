from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
    # Company Logo
    logo_path = settings.BASE_DIR / 'inspections' / 'static' / 'inspections' / 'images' / 'logo_color.png'
    if logo_path.exists():
        logo = Image(str(logo_path), width=1.5*inch, height=1.5*inch, kind='proportional')
        story.append(logo)
        story.append(Spacer(1, 0.05*inch))
    else:
        story.append(Spacer(1, 0.1*inch))

    # Title
    story.append(Paragraph("ANSI A92.2 Periodic Inspection Report", title_style))
    story.append(Spacer(1, 0.1*inch))

    # RESULT BANNER
    result = inspection.overall_result.upper() if inspection.overall_result else 'IN PROGRESS'
    result_color = colors.HexColor('#27ae60') if result == 'PASS' else colors.HexColor('#e74c3c') if result == 'FAIL' else colors.HexColor('#f39c12')
    result_style = ParagraphStyle(
        'ResultBanner',
        parent=styles['Heading1'],
        fontSize=36,
        fontName='Helvetica-Bold',
        textColor=colors.whitesmoke,
        spaceAfter=6,
        spaceBefore=6,
        alignment=TA_CENTER,
        backColor=result_color,
        borderPadding=15,
        leading=48
    )
    story.append(Paragraph(f"<b>{result}</b>", result_style))
    story.append(Spacer(1, 0.1*inch))

    eq = inspection.equipment
    customer = eq.customer

    # Section heading style - colored headers like the old PDF
    def create_section_header(text, bg_color):
        header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.whitesmoke,
            spaceAfter=0,
            spaceBefore=0,
            leftIndent=6,
            alignment=TA_LEFT,
            backColor=bg_color
        )
        return Paragraph(text, header_style)

    def create_data_table(data, col_widths):
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        return table

    # Customer Information (Blue header)
    story.append(create_section_header("Customer Information", colors.HexColor('#3498db')))
    customer_data = []
    if customer:
        customer_data.append(['Customer:', customer.name or 'N/A'])
        if customer.location:
            customer_data.append(['Location / Yard:', customer.location])
        if customer.address_line1:
            address_parts = [customer.address_line1]
            if customer.address_line2:
                address_parts.append(customer.address_line2)
            if customer.city or customer.state or customer.zip_code:
                city_state_zip = ', '.join(filter(None, [customer.city, customer.state, customer.zip_code]))
                address_parts.append(city_state_zip)
            customer_data.append(['Address:', '\n'.join(address_parts)])
        if customer.asset_id:
            customer_data.append(['Asset ID:', customer.asset_id])
        if customer.phone:
            customer_data.append(['Phone:', customer.phone])
        if customer.email:
            customer_data.append(['Email:', customer.email])
        if customer.contact_person_name:
            customer_data.append(['Contact Person:', customer.contact_person_name])
        if customer.contact_person_phone:
            customer_data.append(['Contact Phone:', customer.contact_person_phone])
    else:
        customer_data.append(['Customer:', 'N/A'])

    story.append(create_data_table(customer_data, [1.5*inch, 5*inch]))

    # Vehicle Information (Purple header) - only if there's vehicle data
    has_vehicle_data = any([eq.vehicle_make, eq.vehicle_model, eq.vehicle_unit_number, eq.vehicle_vin, eq.vehicle_year, eq.vehicle_license_plate])
    if has_vehicle_data:
        story.append(create_section_header("Vehicle Information (Chassis)", colors.HexColor('#9b59b6')))
        vehicle_data = []
        if eq.vehicle_make:
            vehicle_data.append(['Make:', eq.vehicle_make])
        if eq.vehicle_model:
            vehicle_data.append(['Model:', eq.vehicle_model])
        if eq.vehicle_unit_number:
            vehicle_data.append(['Unit Number:', eq.vehicle_unit_number])
        if eq.vehicle_vin:
            vehicle_data.append(['VIN:', eq.vehicle_vin])
        if eq.vehicle_year:
            vehicle_data.append(['Year:', eq.vehicle_year])
        if eq.vehicle_license_plate:
            vehicle_data.append(['License Plate:', eq.vehicle_license_plate])

        story.append(create_data_table(vehicle_data, [1.5*inch, 5*inch]))

    # Aerial Device Information (Orange header)
    story.append(create_section_header("Aerial Device Information", colors.HexColor('#e67e22')))
    aerial_data = []
    if eq.make:
        aerial_data.append(['Manufacturer:', eq.make])
    if eq.model:
        aerial_data.append(['Model:', eq.model])
    if eq.serial_number:
        aerial_data.append(['Serial Number:', eq.serial_number])
    if eq.unit_number:
        aerial_data.append(['Unit Number:', eq.unit_number])
    if eq.max_working_height:
        aerial_data.append(['Max Working Height:', f"{eq.max_working_height} ft"])
    if eq.year_of_manufacture:
        aerial_data.append(['Year of Manufacture:', str(eq.year_of_manufacture)])

    story.append(create_data_table(aerial_data, [1.5*inch, 5*inch]))

    # Inspection Information (Dark blue/gray header)
    story.append(create_section_header("Inspection Information", colors.HexColor('#2c3e50')))
    inspection_data = []

    # Inspector info with phone and email
    inspector_name = inspection.inspector.get_full_name() or inspection.inspector.username
    inspector_phone = None
    inspector_email = inspection.inspector.email if inspection.inspector.email else None

    if hasattr(inspection.inspector, 'inspector_profile'):
        profile = inspection.inspector.inspector_profile
        if profile.phone:
            inspector_phone = profile.phone
            inspection_data.append(['Inspector Phone:', inspector_phone])
        if inspector_email:
            inspection_data.append(['Inspector Email:', inspector_email])
        if profile.certification_number:
            inspector_name += f" (Cert# {profile.certification_number})"

    inspection_data.extend([
        ['Inspector:', inspector_name],
        ['Date:', inspection.started_at.strftime('%Y-%m-%d %H:%M')],
        ['Certificate #:', inspection.certificate_number or 'N/A'],
        ['Reference Standard:', 'ANSI/SAIA A92.2 (2021)'],
        ['Overall Result:', inspection.overall_result.upper() if inspection.overall_result else 'IN PROGRESS'],
    ])

    story.append(create_data_table(inspection_data, [1.5*inch, 5*inch]))

    # Inspection Company (Green header)
    story.append(create_section_header("Inspection Company", colors.HexColor('#27ae60')))
    company_data = []

    # Get company info
    try:
        from inspections.models import CompanyInfo
        company = CompanyInfo.objects.first()
        if company:
            company_data.append(['Company:', company.name or 'N/A'])
            if company.address_line1:
                address_parts = [company.address_line1]
                if company.address_line2:
                    address_parts.append(company.address_line2)
                if company.city or company.state or company.zip_code:
                    city_state_zip = ', '.join(filter(None, [company.city, company.state, company.zip_code]))
                    address_parts.append(city_state_zip)
                company_data.append(['Address:', '\n'.join(address_parts)])
            if company.phone:
                company_data.append(['Phone:', company.phone])
            if company.email:
                company_data.append(['Email:', company.email])
            if company.website:
                company_data.append(['Website:', company.website])
            if company.license_number:
                company_data.append(['License #:', company.license_number])
            if company.certifications:
                company_data.append(['Certifications:', company.certifications])
    except:
        company_data.append(['Company:', 'N/A'])

    story.append(create_data_table(company_data, [1.5*inch, 5*inch]))

    # Page break before executive summary
    story.append(PageBreak())

    # ===== EXECUTIVE SUMMARY =====
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Spacer(1, 0.15*inch))

    # Calculate statistics
    total_questions = inspection.answers.count()
    pass_count = inspection.answers.filter(status='pass').count()
    fail_count = inspection.answers.filter(status='fail').count()
    na_count = inspection.answers.filter(status='na').count()
    defect_count = inspection.defects.count()
    test_module_count = inspection.test_modules.count()

    # Calculate section breakdown
    freq_count = inspection.answers.filter(question__section__title__icontains='Frequent').count()
    periodic_count = inspection.answers.filter(question__section__title__icontains='Periodic').count()

    # Summary text with more context
    result_color = '#27ae60' if inspection.overall_result == 'pass' else '#e74c3c' if inspection.overall_result == 'fail' else '#95a5a6'
    result_text = inspection.overall_result.upper() if inspection.overall_result else 'N/A'

    inspection_date = inspection.started_at.strftime('%B %d, %Y') if inspection.started_at else 'N/A'
    inspector_name = inspection.inspector.get_full_name() or inspection.inspector.username

    summary_text = f"""
    This ANSI A92.2 periodic inspection was completed on <b>{inspection_date}</b> by <b>{inspector_name}</b> with
    an overall result of <b><font color="{result_color}">{result_text}</font></b>. The inspection evaluated {total_questions} items
    across Frequent Inspection ({freq_count} items) and Periodic Inspection ({periodic_count} items) sections.
    """
    if test_module_count > 0:
        summary_text += f" {test_module_count} formal test procedure(s) were performed."

    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Statistics table with modern styling
    stats_data = [
        ['Inspection Results', 'Count', 'Percentage'],
        ['✓ Passed', str(pass_count), f'{(pass_count/total_questions*100) if total_questions > 0 else 0:.1f}%'],
        ['✗ Failed', str(fail_count), f'{(fail_count/total_questions*100) if total_questions > 0 else 0:.1f}%'],
        ['— Not Applicable', str(na_count), f'{(na_count/total_questions*100) if total_questions > 0 else 0:.1f}%'],
        ['Total Items Inspected', str(total_questions), '100%'],
    ]

    if test_module_count > 0 or defect_count > 0:
        stats_data.append(['', '', ''])  # Separator row
        if test_module_count > 0:
            stats_data.append(['Formal Tests Performed', str(test_module_count), '—'])
        if defect_count > 0:
            stats_data.append(['Defects Documented', str(defect_count), '—'])

    stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    stats_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#d4edda')),  # Pass row green
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f8d7da')),  # Fail row red
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f0f0f0')),  # N/A row gray
    ]

    # Add separator row styling if present
    if test_module_count > 0 or defect_count > 0:
        separator_row = 5
        stats_styles.append(('LINEABOVE', (0, separator_row), (-1, separator_row), 1.5, colors.HexColor('#2c3e50')))
        stats_styles.append(('BACKGROUND', (0, separator_row), (-1, separator_row), colors.white))
        stats_styles.append(('TOPPADDING', (0, separator_row), (-1, separator_row), 2))
        stats_styles.append(('BOTTOMPADDING', (0, separator_row), (-1, separator_row), 2))

    stats_table.setStyle(TableStyle(stats_styles))
    story.append(stats_table)
    story.append(Spacer(1, 0.25*inch))

    # Key findings with actionable information
    story.append(Paragraph("<b>Key Findings & Recommendations:</b>", subheading_style))
    story.append(Spacer(1, 0.1*inch))

    if fail_count > 0 or defect_count > 0:
        if fail_count > 0:
            story.append(Paragraph(
                f"• <b>{fail_count} inspection item(s) failed</b> - Equipment requires corrective action before return to service",
                normal_style
            ))
        if defect_count > 0:
            story.append(Paragraph(
                f"• <b>{defect_count} defect(s) documented</b> with photographic evidence - Refer to Defects section for details and repair recommendations",
                normal_style
            ))
        if pass_count > 0:
            story.append(Paragraph(
                f"• {pass_count} item(s) passed inspection and meet ANSI A92.2 requirements",
                normal_style
            ))
    else:
        story.append(Paragraph(
            "• <b>All inspected items passed</b> - Equipment meets ANSI A92.2 compliance standards",
            normal_style
        ))
        story.append(Paragraph(
            "• No defects or safety concerns identified during this inspection",
            normal_style
        ))
        story.append(Paragraph(
            "• Equipment is approved for continued service per inspection requirements",
            normal_style
        ))

    # Page break before details
    story.append(PageBreak())

    # ===== TEST MODULES SECTION (if any) =====
    # Extract and format test modules as dedicated test result pages
    test_modules = inspection.test_modules.select_related('template').all()
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

    # Separate functional tests from other sections
    functional_tests_data = None
    if 'Frequent Inspection' in answers_by_phase:
        freq_subsections = answers_by_phase['Frequent Inspection']['subsections']
        if 'Functional Tests' in freq_subsections:
            functional_tests_data = freq_subsections.pop('Functional Tests')

    # Render each phase with its subsections
    for phase_name, phase_data in answers_by_phase.items():
        # Phase header (major heading)
        story.append(PageBreak())
        phase_heading = phase_name.upper()
        if phase_data.get('ansi_ref'):
            phase_heading = f"{phase_name.upper()} (ANSI {phase_data['ansi_ref']})"
        story.append(Paragraph(phase_heading, heading_style))
        story.append(Spacer(1, 0.25*inch))

        # Render direct answers if any (for non-hierarchical sections)
        if 'direct_answers' in phase_data:
            answers = phase_data['direct_answers']['answers']
            section = phase_data['direct_answers']['section']
            render_answer_table(story, answers, section, subheading_style, normal_style)

        # Render subsections
        for subsection_name, subsection_data in phase_data['subsections'].items():
            section = subsection_data['section']
            answers = subsection_data['answers']

            # Subsection title with ANSI reference
            subsection_heading = subsection_name
            if section.ansi_reference:
                subsection_heading = f"{subsection_name} (ANSI {section.ansi_reference})"
            story.append(Paragraph(subsection_heading, subheading_style))

            render_answer_table(story, answers, section, subheading_style, normal_style)

    # ===== FUNCTIONAL TEST RESULTS PAGE =====
    if functional_tests_data:
        story.append(PageBreak())
        story.append(Paragraph("FUNCTIONAL TEST RESULTS", heading_style))
        story.append(Spacer(1, 0.25*inch))

        section = functional_tests_data['section']
        answers = functional_tests_data['answers']

        # Group functional tests by test type for cleaner presentation
        for answer in answers:
            # Extract test name from question
            test_item = answer.question.prompt
            status = answer.status.upper()

            # Format status
            if status == 'PASS':
                status_display = 'PASS'
                status_color = colors.HexColor('#27ae60')
            elif status == 'FAIL':
                status_display = 'FAIL'
                status_color = colors.HexColor('#e74c3c')
            else:
                status_display = 'N/A'
                status_color = colors.HexColor('#95a5a6')

            # Display test item and result
            test_style = ParagraphStyle(
                'TestItem',
                parent=normal_style,
                fontSize=11,
                fontName='Helvetica-Bold',
                spaceAfter=4
            )
            story.append(Paragraph(test_item, test_style))

            result_text = f'<font color="{status_color}"><b>{status_display}</b></font>'
            if answer.notes and not (answer.notes.startswith('Question') and ' - ' in answer.notes):
                result_text += f' – {answer.notes}'

            story.append(Paragraph(result_text, normal_style))
            story.append(Spacer(1, 0.15*inch))

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

            render_answer_table(story, answers, section, subheading_style, normal_style)

    # ===== DEFECTS SECTION =====
    defects = inspection.defects.prefetch_related('photos').all()

    if defects.exists():
        story.append(PageBreak())
        story.append(Paragraph("Defects", heading_style))
        story.append(Spacer(1, 0.15*inch))

        for idx, defect in enumerate(defects, 1):
            # Defect header with number
            defect_header_style = ParagraphStyle(
                'DefectHeader',
                parent=subheading_style,
                fontSize=12,
                fontName='Helvetica-Bold',
                textColor=colors.HexColor('#e74c3c'),
                spaceAfter=8,
                spaceBefore=0
            )
            story.append(Paragraph(f"Defect #{idx}", defect_header_style))

            # Build defect information table (compact, no huge boxes)
            defect_data = []

            if defect.question:
                # Related question with ANSI reference
                question_ref = ""
                if defect.question.section.ansi_reference:
                    question_ref = f"ANSI {defect.question.section.ansi_reference}"
                    if defect.question.ansi_reference:
                        question_ref += f" / {defect.question.ansi_reference}"
                elif defect.question.ansi_reference:
                    question_ref = f"ANSI {defect.question.ansi_reference}"

                question_display = defect.question.prompt
                if question_ref:
                    question_display += f"<br/><i><font size=8 color='#666'>{question_ref}</font></i>"

                defect_data.append(['Related Question:', Paragraph(question_display, normal_style)])

            # Defect note (emphasis on this)
            defect_note_style = ParagraphStyle(
                'DefectNote',
                parent=normal_style,
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#1a1a1a')
            )
            defect_data.append(['Note:', Paragraph(f"<b>{defect.note}</b>", defect_note_style)])

            # Create compact defect info table
            defect_table = Table(defect_data, colWidths=[1.5*inch, 5*inch])
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
                ('LINEBELOW', (0, -1), (-1, -1), 1, colors.HexColor('#e74c3c')),
            ]))
            story.append(defect_table)
            story.append(Spacer(1, 0.15*inch))

            # Photos - side by side when multiple, proper sizing
            photos = list(defect.photos.all())
            if photos:
                if len(photos) == 1:
                    # Single photo - larger, centered
                    try:
                        img = Image(photos[0].image.path, width=5*inch, height=3.75*inch, kind='proportional')
                        story.append(img)
                        if photos[0].caption:
                            caption_style = ParagraphStyle('Caption', parent=normal_style, fontSize=9, textColor=colors.HexColor('#666'), alignment=TA_CENTER)
                            story.append(Paragraph(f"<i>{photos[0].caption}</i>", caption_style))
                        story.append(Spacer(1, 0.1*inch))
                    except Exception as e:
                        story.append(Paragraph(f"[Photo could not be loaded]", normal_style))
                else:
                    # Multiple photos - create grid (2 per row)
                    photo_table_data = []
                    photo_row = []

                    for photo_idx, photo in enumerate(photos):
                        try:
                            img = Image(photo.image.path, width=3*inch, height=2.25*inch, kind='proportional')
                            caption = ""
                            if photo.caption:
                                caption = f"<i><font size=8>{photo.caption}</font></i>"

                            photo_cell = [img]
                            if caption:
                                caption_style = ParagraphStyle('PhotoCaption', parent=normal_style, fontSize=8, textColor=colors.HexColor('#666'))
                                photo_cell.append(Paragraph(caption, caption_style))

                            photo_row.append(photo_cell)

                            # Two photos per row
                            if len(photo_row) == 2 or photo_idx == len(photos) - 1:
                                # Pad last row if odd number of photos
                                while len(photo_row) < 2:
                                    photo_row.append([''])
                                photo_table_data.append(photo_row)
                                photo_row = []
                        except Exception:
                            photo_row.append([Paragraph("[Photo unavailable]", normal_style)])
                            if len(photo_row) == 2:
                                photo_table_data.append(photo_row)
                                photo_row = []

                    if photo_table_data:
                        photo_table = Table(photo_table_data, colWidths=[3.25*inch, 3.25*inch])
                        photo_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 4),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ]))
                        story.append(photo_table)

            story.append(Spacer(1, 0.25*inch))

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


def render_answer_table(story, answers, section, subheading_style, normal_style):
    """Helper function to render a table of inspection answers"""
    # Pre-check what columns we actually need
    has_measurements = any(answer.measurement_value is not None for answer in answers)
    has_notes = any(answer.notes and not (answer.notes.startswith('Question ') and ' - ' in answer.notes) for answer in answers)

    # Build table data for compact layout
    table_data = []
    table_styles = [
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]

    for idx, answer in enumerate(answers):
        # Status indicator
        status = answer.status.upper()
        if status == 'PASS':
            status_display = '✓ PASS'
            status_color = colors.HexColor('#27ae60')
            bg_color = colors.white if idx % 2 == 0 else colors.HexColor('#f9f9f9')
        elif status == 'FAIL':
            status_display = '✗ FAIL'
            status_color = colors.HexColor('#e74c3c')
            bg_color = colors.HexColor('#ffebee')  # Light red background for failures
            # Add bold styling to failed rows
            table_styles.append(('BACKGROUND', (0, idx), (-1, idx), bg_color))
            table_styles.append(('LINEABOVE', (0, idx), (-1, idx), 1.5, colors.HexColor('#e74c3c')))
            table_styles.append(('LINEBELOW', (0, idx), (-1, idx), 1.5, colors.HexColor('#e74c3c')))
        else:  # NA
            status_display = '— N/A'
            status_color = colors.HexColor('#95a5a6')
            bg_color = colors.white if idx % 2 == 0 else colors.HexColor('#f9f9f9')

        # Apply background for non-failed items
        if status != 'FAIL':
            table_styles.append(('BACKGROUND', (0, idx), (-1, idx), bg_color))

        # Question text with ANSI reference
        question_text = answer.question.prompt
        if answer.question.ansi_reference:
            question_text = f"{question_text}<br/><i><font size=7 color='#666'>ANSI {answer.question.ansi_reference}</font></i>"

        # Build row - only add columns that are actually used
        row = [
            Paragraph(f'<font color="{status_color}"><b>{status_display}</b></font>', normal_style),
            Paragraph(question_text, normal_style)
        ]

        # Only add measurement column if any answer has measurements
        if has_measurements:
            if answer.measurement_value is not None:
                measurement = f"{answer.measurement_value} {answer.question.measurement_unit or ''}".strip()
                row.append(Paragraph(f'<b>{measurement}</b>', normal_style))
            else:
                row.append('')

        # Only add notes column if any answer has meaningful notes
        if has_notes:
            if answer.notes and not (answer.notes.startswith('Question ') and ' - ' in answer.notes):
                row.append(Paragraph(answer.notes, normal_style))
            else:
                row.append('')

        table_data.append(row)

    # Create table with compact layout
    if table_data:
        # Determine column widths based on what columns we're actually using
        if has_measurements and has_notes:
            col_widths = [0.7*inch, 3.5*inch, 0.9*inch, 1.4*inch]
        elif has_measurements:
            col_widths = [0.7*inch, 5*inch, 0.8*inch]
        elif has_notes:
            col_widths = [0.7*inch, 4*inch, 1.8*inch]
        else:
            # Just status and question - tightest layout
            col_widths = [0.7*inch, 5.8*inch]

        section_table = Table(table_data, colWidths=col_widths, repeatRows=0)
        section_table.setStyle(TableStyle(table_styles))
        story.append(section_table)

    story.append(Spacer(1, 0.15*inch))
