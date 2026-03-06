from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image
)
from reportlab.lib import colors
from inspections.models import GeneratedDocument


def generate_package_pdf(inspection):
    """
    Generate multi-page inspection package PDF with:
    - Cover page
    - Details (sections, questions, answers)
    - Defects with embedded photos
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )

    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=8
    )

    normal_style = styles['Normal']

    # ===== COVER PAGE =====
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(settings.COMPANY_NAME, title_style))
    story.append(Spacer(1, 0.3*inch))

    inspection_type = inspection.template.kind.title() + " Inspection"
    if inspection.template.kind == 'test':
        inspection_type = f"Test: {inspection.template.name}"

    story.append(Paragraph(f"<b>{inspection_type}</b>", heading_style))
    story.append(Spacer(1, 0.5*inch))

    # Equipment info table
    customer_name = inspection.equipment.customer.name if inspection.equipment.customer else 'N/A'
    eq = inspection.equipment

    equipment_data = [
        ['Equipment Information', ''],
        ['Serial Number:', eq.serial_number or 'N/A'],
        ['Make:', eq.make or 'N/A'],
        ['Model:', eq.model or 'N/A'],
        ['Year of Manufacture:', eq.year_of_manufacture or 'N/A'],
        ['Customer:', customer_name],
        ['Location:', eq.location or 'N/A'],
    ]

    # Add ANSI A92.2 identification plate data if available
    if eq.insulation_type:
        equipment_data.append(['Insulation Type:', eq.get_insulation_type_display()])
    if eq.category:
        equipment_data.append(['Category:', eq.get_category_display()])
    if eq.rated_platform_height:
        equipment_data.append(['Rated Platform Height:', f"{eq.rated_platform_height} ft"])
    if eq.capacity_per_platform:
        equipment_data.append(['Capacity per Platform:', f"{eq.capacity_per_platform} lbs"])
    if eq.capacity_total:
        equipment_data.append(['Total Capacity:', f"{eq.capacity_total} lbs"])
    if eq.qualification_voltage:
        equipment_data.append(['Qualification Voltage:', f"{eq.qualification_voltage} kV"])
    if eq.configured_for_electrical_work:
        equipment_data.append(['Configured for Electrical Work:', 'Yes'])
    if eq.chassis_insulating_system:
        equipment_data.append(['Chassis Insulating System:', 'Yes'])
    if eq.upper_controls_high_resistance:
        equipment_data.append(['Upper Controls High Resistance:', 'Yes'])

    equipment_table = Table(equipment_data, colWidths=[2.5*inch, 3.5*inch])
    equipment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(equipment_table)
    story.append(Spacer(1, 0.3*inch))

    # Inspection info table
    inspection_data = [
        ['Inspection Information', ''],
        ['Inspector:', inspection.inspector.get_full_name() or inspection.inspector.username],
        ['Date:', inspection.started_at.strftime('%Y-%m-%d %H:%M')],
        ['Certificate #:', inspection.certificate_number or 'N/A'],
        ['Reference:', inspection.reference or 'N/A'],
        ['Overall Result:', inspection.overall_result.upper() if inspection.overall_result else 'N/A'],
    ]

    inspection_table = Table(inspection_data, colWidths=[2*inch, 4*inch])
    inspection_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(inspection_table)

    # Page break before executive summary
    story.append(PageBreak())

    # ===== EXECUTIVE SUMMARY =====
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Spacer(1, 0.2*inch))

    # Calculate statistics
    total_questions = inspection.answers.count()
    pass_count = inspection.answers.filter(status='pass').count()
    fail_count = inspection.answers.filter(status='fail').count()
    na_count = inspection.answers.filter(status='na').count()
    defect_count = inspection.defects.count()

    # Summary text
    result_color = '#27ae60' if inspection.overall_result == 'pass' else '#e74c3c' if inspection.overall_result == 'fail' else '#95a5a6'
    result_text = inspection.overall_result.upper() if inspection.overall_result else 'N/A'

    summary_text = f"""
    This inspection has been completed with an overall result of <b><font color="{result_color}">{result_text}</font></b>.
    A total of {total_questions} questions were evaluated across all sections.
    """
    story.append(Paragraph(summary_text, normal_style))
    story.append(Spacer(1, 0.2*inch))

    # Statistics table
    stats_data = [
        ['Inspection Statistics', 'Count', 'Percentage'],
        ['✓ Pass', str(pass_count), f'{(pass_count/total_questions*100) if total_questions > 0 else 0:.1f}%'],
        ['✗ Fail', str(fail_count), f'{(fail_count/total_questions*100) if total_questions > 0 else 0:.1f}%'],
        ['— N/A', str(na_count), f'{(na_count/total_questions*100) if total_questions > 0 else 0:.1f}%'],
        ['Total Questions', str(total_questions), '100%'],
        ['Defects Recorded', str(defect_count), '—'],
    ]

    stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#d4edda')),  # Pass row green
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#f8d7da')),  # Fail row red
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#f0f0f0')),  # N/A row gray
    ]))

    story.append(stats_table)
    story.append(Spacer(1, 0.3*inch))

    # Key findings
    if fail_count > 0:
        story.append(Paragraph("<b>Key Findings:</b>", subheading_style))
        story.append(Paragraph(
            f"• {fail_count} item(s) failed inspection",
            normal_style
        ))
        story.append(Paragraph(
            f"• {defect_count} defect(s) documented with photos and notes",
            normal_style
        ))
        story.append(Paragraph(
            "• Detailed defect information can be found in the Defects section of this report",
            normal_style
        ))
    else:
        story.append(Paragraph("<b>Key Findings:</b>", subheading_style))
        story.append(Paragraph(
            "• All inspected items passed or were marked as not applicable",
            normal_style
        ))
        story.append(Paragraph(
            "• No defects were identified during this inspection",
            normal_style
        ))

    # Page break before details
    story.append(PageBreak())

    # ===== DETAILS SECTION =====
    story.append(Paragraph("Inspection Details", heading_style))
    story.append(Spacer(1, 0.2*inch))

    # Group answers by section
    answers_by_section = {}
    for answer in inspection.answers.select_related('question__section').order_by(
        'question__section__order', 'question__order'
    ):
        section_title = answer.question.section.title
        if section_title not in answers_by_section:
            answers_by_section[section_title] = []
        answers_by_section[section_title].append(answer)

    # Render each section
    for section_title, answers in answers_by_section.items():
        story.append(Paragraph(section_title, subheading_style))

        for answer in answers:
            # Question prompt
            question_text = answer.question.prompt[:200]  # Truncate if too long
            story.append(Paragraph(f"<b>Q:</b> {question_text}", normal_style))

            # Answer status
            status_text = answer.status.upper()
            story.append(Paragraph(f"<b>Answer:</b> {status_text}", normal_style))

            # Notes if present
            if answer.notes:
                story.append(Paragraph(f"<b>Notes:</b> {answer.notes}", normal_style))

            story.append(Spacer(1, 0.1*inch))

        story.append(Spacer(1, 0.2*inch))

    # ===== DEFECTS SECTION =====
    defects = inspection.defects.prefetch_related('photos').all()

    if defects.exists():
        story.append(PageBreak())
        story.append(Paragraph("Defects", heading_style))
        story.append(Spacer(1, 0.2*inch))

        for idx, defect in enumerate(defects, 1):
            story.append(Paragraph(f"<b>Defect #{idx}</b>", subheading_style))

            if defect.question:
                story.append(Paragraph(
                    f"<b>Related Question:</b> {defect.question.prompt[:150]}",
                    normal_style
                ))

            story.append(Paragraph(f"<b>Note:</b> {defect.note}", normal_style))
            story.append(Spacer(1, 0.1*inch))

            # Embed photos
            for photo in defect.photos.all():
                try:
                    img = Image(photo.image.path, width=4*inch, height=3*inch)
                    story.append(img)
                    if photo.caption:
                        story.append(Paragraph(f"<i>{photo.caption}</i>", normal_style))
                    story.append(Spacer(1, 0.1*inch))
                except Exception as e:
                    story.append(Paragraph(f"[Photo could not be loaded: {str(e)}]", normal_style))

            story.append(Spacer(1, 0.2*inch))

    # Build PDF
    doc.build(story)

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
