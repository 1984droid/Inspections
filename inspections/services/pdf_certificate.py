from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from inspections.models import GeneratedDocument, CompanyInfo


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

    # Company Logo (high contrast for thermal printing)
    logo_path = settings.BASE_DIR / 'inspections' / 'static' / 'inspections' / 'images' / 'logo_hi_contrast.png'
    if logo_path.exists():
        c.drawImage(str(logo_path), width / 2 - 1*inch, height - 1.2*inch, width=2*inch, height=1*inch, preserveAspectRatio=True, mask='auto')
        y_start = height - 1.5*inch
    else:
        y_start = height - 1*inch

    # Title - smaller, less prominent
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, y_start, "ANSI A92.2 INSPECTION CERTIFICATE")

    # HUGE PASS or FAIL - this is the star
    result = inspection.overall_result.upper() if inspection.overall_result else 'N/A'

    # Massive font size for result
    if result == 'PASS':
        c.setFont("Helvetica-Bold", 90)
        c.drawCentredString(width / 2, height - 2.7*inch, "PASS")
    elif result == 'FAIL':
        c.setFont("Helvetica-Bold", 90)
        c.drawCentredString(width / 2, height - 2.7*inch, "FAIL")
    else:
        c.setFont("Helvetica-Bold", 80)
        c.drawCentredString(width / 2, height - 2.7*inch, "N/A")

    # Heavy box around result for thermal visibility
    c.setLineWidth(5)
    c.rect(1.5*inch, height - 3.4*inch, width - 3*inch, 1.8*inch, stroke=1, fill=0)

    # Brutal simplicity: key identifiers only, compact layout
    eq = inspection.equipment
    customer = eq.customer
    y_pos = height - 4*inch

    # Single-line compact format for maximum clarity
    c.setFont("Helvetica-Bold", 11)
    label_x = 1.5*inch
    value_x = 3*inch

    # Customer
    if customer:
        c.drawString(label_x, y_pos, "Customer:")
        c.setFont("Helvetica", 11)
        c.drawString(value_x, y_pos, customer.name)
        y_pos -= 0.22*inch
        c.setFont("Helvetica-Bold", 11)

    # Aerial Device essentials
    c.drawString(label_x, y_pos, "Make/Model:")
    c.setFont("Helvetica", 11)
    make_model = f"{eq.make or 'N/A'} {eq.model or ''}"
    c.drawString(value_x, y_pos, make_model.strip())
    y_pos -= 0.22*inch

    c.setFont("Helvetica-Bold", 11)
    c.drawString(label_x, y_pos, "Serial #:")
    c.setFont("Helvetica", 11)
    c.drawString(value_x, y_pos, eq.serial_number or 'N/A')
    y_pos -= 0.22*inch

    if eq.unit_number:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(label_x, y_pos, "Unit #:")
        c.setFont("Helvetica", 11)
        c.drawString(value_x, y_pos, eq.unit_number)
        y_pos -= 0.22*inch

    # Vehicle - only if exists
    if eq.vehicle_unit_number or eq.vehicle_vin:
        y_pos -= 0.1*inch
        if eq.vehicle_unit_number:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(label_x, y_pos, "Truck Unit #:")
            c.setFont("Helvetica", 11)
            c.drawString(value_x, y_pos, eq.vehicle_unit_number)
            y_pos -= 0.22*inch

        if eq.vehicle_vin:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(label_x, y_pos, "VIN:")
            c.setFont("Helvetica", 11)
            c.drawString(value_x, y_pos, eq.vehicle_vin)
            y_pos -= 0.22*inch

    # Dates - critical info
    y_pos -= 0.1*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(label_x, y_pos, "Inspected:")
    c.setFont("Helvetica", 11)
    c.drawString(value_x, y_pos, inspection.started_at.strftime('%Y-%m-%d'))
    y_pos -= 0.22*inch

    # Expiration date
    from datetime import timedelta
    inspection_date = inspection.started_at.date() if inspection.started_at else None
    if inspection_date:
        if inspection.template.kind == 'periodic':
            expiration_date = inspection_date + timedelta(days=365)
        else:
            expiration_date = inspection_date + timedelta(days=90)

        c.setFont("Helvetica-Bold", 11)
        c.drawString(label_x, y_pos, "Valid Until:")
        c.setFont("Helvetica", 11)
        c.drawString(value_x, y_pos, expiration_date.strftime('%Y-%m-%d'))
        y_pos -= 0.22*inch

    # Inspector
    inspector_name = inspection.inspector.get_full_name() or inspection.inspector.username
    if hasattr(inspection.inspector, 'inspector_profile'):
        profile = inspection.inspector.inspector_profile
        if profile.certification_number:
            inspector_name += f" (#{profile.certification_number})"

    c.setFont("Helvetica-Bold", 11)
    c.drawString(label_x, y_pos, "Inspector:")
    c.setFont("Helvetica", 11)
    c.drawString(value_x, y_pos, inspector_name)
    y_pos -= 0.22*inch

    # Certificate number
    c.setFont("Helvetica-Bold", 11)
    c.drawString(label_x, y_pos, "Certificate #:")
    c.setFont("Helvetica", 11)
    c.drawString(value_x, y_pos, inspection.certificate_number or 'N/A')
    y_pos -= 0.3*inch

    # Bottom: company info (compact)
    c.setLineWidth(2)
    c.line(1.5*inch, y_pos, 7*inch, y_pos)
    y_pos -= 0.25*inch

    # Company Information - minimal footer
    company = CompanyInfo.objects.first()
    if company:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(label_x, y_pos, company.name)
        y_pos -= 0.18*inch

        c.setFont("Helvetica", 9)
        if company.phone:
            c.drawString(label_x, y_pos, f"Phone: {company.phone}")
            y_pos -= 0.18*inch

        if company.license_number:
            c.drawString(label_x, y_pos, f"License #: {company.license_number}")
            y_pos -= 0.18*inch

    # Bottom note
    y_pos -= 0.1*inch
    c.setFont("Helvetica", 8)
    c.drawString(label_x, y_pos, "For full inspection report, see accompanying documentation.")

    # ANSI reference at very bottom
    c.setFont("Helvetica", 8)
    c.drawCentredString(width / 2, 0.5*inch, "ANSI/SAIA A92.2 (2021) Compliance")

    # Save PDF
    c.showPage()
    c.save()

    # Save to GeneratedDocument
    buffer.seek(0)
    filename = f"inspection_certificate_{inspection.id}.pdf"

    # Delete old certificate documents
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
