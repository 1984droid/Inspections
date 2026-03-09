#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inspections.models import Customer, Equipment, Inspection, InspectionTemplate, TestModule
from inspections.services.pdf_package import generate_package_pdf

# Create test customer
customer = Customer.objects.create(
    name="PDF Test Customer",
    address="123 Test St",
    city="Test City",
    state="TS",
    zip_code="12345"
)

# Create test equipment
equipment = Equipment.objects.create(
    customer=customer,
    serial_number=f"PDF-TEST-001",
    make="Test Make",
    model="Test Model"
)

# Get first template
template = InspectionTemplate.objects.first()
if not template:
    print("No templates found!")
    exit(1)

# Get first test module
test_module = TestModule.objects.first()

# Create inspection
inspection = Inspection.objects.create(
    equipment=equipment,
    template=template,
    assigned_to_id=1  # admin user
)

if test_module:
    inspection.test_modules.add(test_module)

# Answer all questions with PASS
from inspections.models import InspectionAnswer
for section in inspection.sections.all():
    for question in section.questions.all():
        InspectionAnswer.objects.create(
            inspection=inspection,
            question=question,
            answer='pass'
        )

# Mark as complete
inspection.overall_result = 'pass'
inspection.save()

print(f"Created inspection #{inspection.id}")

# Generate PDF
pdf_path = generate_package_pdf(inspection)
print(f"PDF generated: {pdf_path}")
