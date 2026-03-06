from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from inspections.models import GeneratedDocument


def generate_certificate_pdf(inspection):
    """
    Generate single-page high-contrast thermal certificate PDF
    Black/white only, very large PASS/FAIL
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Set to black and white only
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)

    # Title
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 1*inch, "INSPECTION CERTIFICATE")

    # Large PASS or FAIL
    result = inspection.overall_result.upper() if inspection.overall_result else 'N/A'

    # Set font size based on result
    if result == 'PASS':
        c.setFont("Helvetica-Bold", 72)
        c.drawCentredString(width / 2, height - 2.5*inch, "PASS")
    elif result == 'FAIL':
        c.setFont("Helvetica-Bold", 72)
        c.drawCentredString(width / 2, height - 2.5*inch, "FAIL")
    else:
        c.setFont("Helvetica-Bold", 60)
        c.drawCentredString(width / 2, height - 2.5*inch, "N/A")

    # Draw a box around result
    c.setLineWidth(4)
    c.rect(2*inch, height - 3.2*inch, width - 4*inch, 1.5*inch, stroke=1, fill=0)

    # Equipment information
    c.setFont("Helvetica-Bold", 14)
    y_pos = height - 4.5*inch

    c.drawString(1.5*inch, y_pos, "Equipment Serial Number:")
    c.setFont("Helvetica", 14)
    c.drawString(4.5*inch, y_pos, inspection.equipment.serial_number or 'N/A')

    y_pos -= 0.3*inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5*inch, y_pos, "Make / Model:")
    c.setFont("Helvetica", 14)
    make_model = f"{inspection.equipment.make or ''} {inspection.equipment.model or ''}".strip() or 'N/A'
    c.drawString(4.5*inch, y_pos, make_model)

    # Inspection information
    y_pos -= 0.5*inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5*inch, y_pos, "Inspection Date:")
    c.setFont("Helvetica", 14)
    c.drawString(4.5*inch, y_pos, inspection.started_at.strftime('%Y-%m-%d'))

    y_pos -= 0.3*inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5*inch, y_pos, "Inspector:")
    c.setFont("Helvetica", 14)
    inspector_name = inspection.inspector.get_full_name() or inspection.inspector.username
    c.drawString(4.5*inch, y_pos, inspector_name)

    y_pos -= 0.3*inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1.5*inch, y_pos, "Certificate Number:")
    c.setFont("Helvetica", 14)
    c.drawString(4.5*inch, y_pos, inspection.certificate_number or 'N/A')

    # Standard reference
    y_pos -= 0.5*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5*inch, y_pos, "Reference Standard:")
    c.setFont("Helvetica", 12)
    c.drawString(4.5*inch, y_pos, "ANSI/SAIA A92.2 (2021)")

    # Inspection type
    y_pos -= 0.3*inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5*inch, y_pos, "Inspection Type:")
    c.setFont("Helvetica", 12)
    inspection_type = inspection.template.kind.title()
    if inspection.template.kind == 'test':
        inspection_type = 'Test'
    c.drawString(4.5*inch, y_pos, inspection_type)

    # Footer box with thick border
    c.setLineWidth(3)
    c.rect(1*inch, 1*inch, width - 2*inch, 1.5*inch, stroke=1, fill=0)

    # Footer text
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width / 2, 2*inch, "This certificate is valid only for the equipment and date specified above.")
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 1.7*inch, "Inspection performed in accordance with ANSI/SAIA A92.2-2021 standard.")
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 1.4*inch, f"Certificate issued: {inspection.completed_at.strftime('%Y-%m-%d %H:%M') if inspection.completed_at else 'N/A'}")

    # Save PDF
    c.showPage()
    c.save()

    # Save to GeneratedDocument
    buffer.seek(0)
    filename = f"inspection_certificate_{inspection.id}.pdf"

    # Delete old certificate documents for this inspection (keep only latest)
    GeneratedDocument.objects.filter(
        inspection=inspection,
        doc_type='certificate'
    ).delete()

    doc_obj = GeneratedDocument.objects.create(
        inspection=inspection,
        doc_type='certificate',
        generator_version='1.0.0'
    )
    doc_obj.file.save(filename, ContentFile(buffer.read()), save=True)

    return doc_obj
