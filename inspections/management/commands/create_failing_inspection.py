from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from inspections.models import Inspection, Equipment, Template, InspectionAnswer, Defect, DefectPhoto
from datetime import datetime
import random
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Create a complete inspection with several FAIL answers (periodic + frequent only)'

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

            # Select random questions to fail (about 10-15% of total)
            total_questions = len(questions)
            num_to_fail = max(5, int(total_questions * 0.12))  # At least 5 failures, or 12% of total
            questions_to_fail = random.sample(questions, num_to_fail)

            fail_count = 0
            pass_count = 0
            defects_list = []

            # Answer all questions
            for question in questions:
                if question in questions_to_fail:
                    InspectionAnswer.objects.create(
                        inspection=inspection,
                        question=question,
                        status='fail',
                        notes='Failed during inspection'
                    )

                    # Create defect for failed item
                    defect = Defect.objects.create(
                        inspection=inspection,
                        question=question,
                        note=f'{question.prompt[:100]} - Item does not meet ANSI A92.2 requirements'
                    )
                    defects_list.append(defect)
                    fail_count += 1
                else:
                    InspectionAnswer.objects.create(
                        inspection=inspection,
                        question=question,
                        status='pass'
                    )
                    pass_count += 1

            self.stdout.write(self.style.SUCCESS(f'Answered {pass_count} questions with PASS'))
            self.stdout.write(self.style.WARNING(f'Answered {fail_count} questions with FAIL'))
            self.stdout.write(self.style.WARNING(f'Created {fail_count} defects'))

            # Add placeholder photos to defects (defect # = number of photos)
            placeholder_path = os.path.join(settings.BASE_DIR, 'media', 'placeholder', 'defect_placeholder.png')
            if os.path.exists(placeholder_path):
                photo_count = 0
                for idx, defect in enumerate(defects_list, 1):
                    # Defect #1 gets 1 photo, defect #2 gets 2 photos, etc.
                    num_photos = idx
                    for photo_num in range(num_photos):
                        with open(placeholder_path, 'rb') as f:
                            DefectPhoto.objects.create(
                                defect=defect,
                                image=File(f, name=f'defect_{defect.id}_photo_{photo_num+1}.png'),
                                caption=f'Defect #{idx} - Photo {photo_num+1}'
                            )
                        photo_count += 1
                self.stdout.write(self.style.SUCCESS(f'Added {photo_count} placeholder photos to defects'))
            else:
                self.stdout.write(self.style.WARNING(f'Placeholder image not found at {placeholder_path}'))

            # Complete the inspection
            inspection.status = 'completed'
            inspection.overall_result = 'fail'
            inspection.completed_at = datetime.now()
            inspection.certificate_number = f'CERT-FAIL-{inspection.id:04d}'
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
