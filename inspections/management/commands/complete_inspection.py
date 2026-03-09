"""
Management command to complete an existing inspection with realistic data
Usage: python manage.py complete_inspection <inspection_id>
"""
from django.core.management.base import BaseCommand
from inspections.models import Inspection, InspectionAnswer
from datetime import datetime
import random


class Command(BaseCommand):
    help = 'Complete an existing inspection with realistic passing data'

    def add_arguments(self, parser):
        parser.add_argument('inspection_id', type=int, help='ID of the inspection to complete')
        parser.add_argument('--fail', action='store_true', help='Create some failures')

    def handle(self, *args, **options):
        inspection_id = options['inspection_id']
        create_failures = options.get('fail', False)

        try:
            inspection = Inspection.objects.get(id=inspection_id)
        except Inspection.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Inspection {inspection_id} not found'))
            return

        self.stdout.write(f'Completing inspection {inspection_id}...')

        # Get all questions from the template and any test modules
        all_questions = []

        # Main template questions
        for section in inspection.template.sections.all():
            all_questions.extend(section.questions.all())

        # Test module questions
        for test_module in inspection.test_modules.all():
            for section in test_module.template.sections.all():
                all_questions.extend(section.questions.all())

        self.stdout.write(f'Found {len(all_questions)} questions to answer')

        # Realistic measurement values for different types
        measurement_values = {
            'voltage': [46.0, 48.5, 50.0, 52.3, 54.0],
            'current': [1.2, 1.5, 1.8, 2.0, 2.3],
            'leakage': [0.5, 0.8, 1.0, 1.2, 1.5],
            'resistance': [1000000, 1200000, 1500000, 2000000, 2500000],
            'pressure': [2500, 2600, 2700, 2800, 2900],
            'capacity': [500, 600, 750, 1000, 1200],
            'duration': [3, 5, 10, 15, 20],
            'temperature': [75, 80, 85, 90, 95],
        }

        # Determine which questions to fail (if --fail flag is used)
        fail_indices = set()
        if create_failures:
            # Pick 3-5 random questions to fail
            num_failures = random.randint(3, 5)
            fail_indices = set(random.sample(range(len(all_questions)), num_failures))

        answers_created = 0
        answers_updated = 0

        for idx, question in enumerate(all_questions):
            # Check if answer already exists
            answer = InspectionAnswer.objects.filter(
                inspection=inspection,
                question=question
            ).first()

            # Skip Method 1 for liner test (mark as N/A) - only use Method 2
            section_title = question.section.title
            if 'Method 1' in section_title and 'Conductive Liquid' in section_title:
                status = 'n/a'
                notes = ''
                measurement_value = None
            # Determine status
            elif idx in fail_indices:
                status = 'fail'
                notes = f'Item failed during inspection - requires attention'
            else:
                status = 'pass'
                notes = ''

            # Determine measurement value if question has measurement unit (only for passing questions)
            measurement_value = None
            if status == 'pass' and question.measurement_unit:
                unit_lower = question.measurement_unit.lower()

                # Match unit to appropriate value range
                if 'kv' in unit_lower or 'volt' in unit_lower:
                    measurement_value = random.choice(measurement_values['voltage'])
                elif 'µa' in unit_lower or 'microamp' in unit_lower or 'ua' in unit_lower:
                    measurement_value = random.choice(measurement_values['current'])
                elif 'ma' in unit_lower or 'milliamp' in unit_lower:
                    measurement_value = random.choice(measurement_values['leakage'])
                elif 'ohm' in unit_lower or 'megohm' in unit_lower:
                    measurement_value = random.choice(measurement_values['resistance'])
                elif 'psi' in unit_lower or 'pressure' in unit_lower:
                    measurement_value = random.choice(measurement_values['pressure'])
                elif 'lb' in unit_lower or 'capacity' in unit_lower or 'weight' in unit_lower:
                    measurement_value = random.choice(measurement_values['capacity'])
                elif 'min' in unit_lower or 'duration' in unit_lower or 'time' in unit_lower:
                    measurement_value = random.choice(measurement_values['duration'])
                elif '°f' in unit_lower or 'temp' in unit_lower:
                    measurement_value = random.choice(measurement_values['temperature'])
                else:
                    # Generic numeric value
                    measurement_value = round(random.uniform(50, 100), 1)

            if answer:
                # Update existing answer
                answer.status = status
                answer.notes = notes
                answer.measurement_value = measurement_value
                answer.save()
                answers_updated += 1
            else:
                # Create new answer
                InspectionAnswer.objects.create(
                    inspection=inspection,
                    question=question,
                    status=status,
                    notes=notes,
                    measurement_value=measurement_value
                )
                answers_created += 1

        # Mark inspection as completed
        inspection.status = 'completed'
        inspection.completed_at = datetime.now()

        if create_failures and fail_indices:
            inspection.overall_result = 'fail'
        else:
            inspection.overall_result = 'pass'

        if not inspection.certificate_number:
            inspection.certificate_number = f'CERT-{"FAIL" if create_failures else "PASS"}-{inspection.id:04d}'

        inspection.save()

        self.stdout.write(self.style.SUCCESS(
            f'\n[OK] Inspection {inspection_id} completed!'
        ))
        self.stdout.write(f'  Created: {answers_created} answers')
        self.stdout.write(f'  Updated: {answers_updated} answers')
        self.stdout.write(f'  Status: {inspection.status}')
        self.stdout.write(f'  Result: {inspection.overall_result}')
        self.stdout.write(f'  Certificate: {inspection.certificate_number}')

        if create_failures:
            self.stdout.write(self.style.WARNING(f'  Failures: {len(fail_indices)} items marked as FAIL'))

        # Generate PDF
        self.stdout.write('\nGenerating PDF...')
        from inspections.services.pdf_package import generate_package_pdf
        try:
            pdf = generate_package_pdf(inspection)
            self.stdout.write(self.style.SUCCESS(f'[OK] PDF generated: {pdf.file.name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[ERROR] PDF generation failed: {str(e)}'))
