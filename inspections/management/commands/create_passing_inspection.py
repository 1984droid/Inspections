from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inspections.models import Inspection, Equipment, Template, InspectionAnswer
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a complete inspection with all PASS answers (periodic + frequent only)'

    def handle(self, *args, **options):
        try:
            # Get the periodic template
            template = Template.objects.filter(kind='periodic', is_active=True).first()
            if not template:
                self.stdout.write(self.style.ERROR('No active periodic template found'))
                return

            # Get test equipment
            equipment = Equipment.objects.filter(serial_number='TEST-SN-001').first()
            if not equipment:
                self.stdout.write(self.style.ERROR('Equipment TEST-SN-001 not found. Run seed_initial_data first.'))
                return

            # Get inspector (josh user)
            inspector = User.objects.filter(username='josh').first()
            if not inspector:
                self.stdout.write(self.style.ERROR('User "josh" not found'))
                return

            # Create inspection
            inspection = Inspection.objects.create(
                template=template,
                equipment=equipment,
                inspector=inspector,
                status='draft',
                started_at=datetime.now()
            )

            self.stdout.write(self.style.SUCCESS(f'Created inspection {inspection.id}'))

            # Get all questions from periodic template (includes frequent and periodic sections)
            questions = []
            for section in template.sections.all():
                questions.extend(section.questions.all())

            self.stdout.write(f'Found {len(questions)} questions')

            # Answer all questions with PASS
            for question in questions:
                InspectionAnswer.objects.create(
                    inspection=inspection,
                    question=question,
                    status='pass'
                )

            self.stdout.write(self.style.SUCCESS(f'Answered all {len(questions)} questions with PASS'))

            # Complete the inspection
            inspection.status = 'completed'
            inspection.overall_result = 'pass'
            inspection.completed_at = datetime.now()
            inspection.certificate_number = f'CERT-PASS-{inspection.id:04d}'
            inspection.save()

            self.stdout.write(self.style.SUCCESS(f'Completed inspection {inspection.id}'))
            self.stdout.write(self.style.SUCCESS(f'Certificate: {inspection.certificate_number}'))

            # Generate PDF
            self.stdout.write('Generating PDF...')
            from inspections.services.pdf_package import generate_package_pdf
            pdf = generate_package_pdf(inspection)
            self.stdout.write(self.style.SUCCESS(f'PDF generated: {pdf}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
