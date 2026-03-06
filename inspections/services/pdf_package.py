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
    equipment_data = [
        ['Equipment Information', ''],
        ['Serial Number:', inspection.equipment.serial_number or 'N/A'],
        ['Make:', inspection.equipment.make or 'N/A'],
        ['Model:', inspection.equipment.model or 'N/A'],
        ['Customer:', inspection.equipment.customer_name or 'N/A'],
        ['Location:', inspection.equipment.location or 'N/A'],
    ]

    equipment_table = Table(equipment_data, colWidths=[2*inch, 4*inch])
    equipment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
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
