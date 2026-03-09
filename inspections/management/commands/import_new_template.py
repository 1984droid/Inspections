import json
from pathlib import Path
from django.core.management.base import BaseCommand
from inspections.models import Template, SectionTemplate, QuestionTemplate


class Command(BaseCommand):
    help = 'Import simplified A92.2 inspection template from JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help='Path to JSON template file',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Replace existing template with same code',
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])

        if not file_path.exists():
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        try:
            self.import_template(file_path, options.get('replace', False))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing {file_path.name}: {str(e)}'))
            if options.get('verbosity', 1) > 1:
                import traceback
                traceback.print_exc()

    def import_template(self, file_path, replace=False):
        """Import a single template from simplified JSON format"""
        self.stdout.write(f'Importing {file_path.name}...')

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract template metadata
        template_meta = data.get('template', {})
        code = template_meta.get('code')
        name = template_meta.get('name')
        version = template_meta.get('version', '1.0')
        kind = template_meta.get('kind', 'periodic')

        if not code or not name:
            self.stdout.write(self.style.ERROR('Template must have code and name'))
            return

        # Check if template exists
        if replace:
            Template.objects.filter(code=code).delete()
            self.stdout.write(f'  Deleted existing template: {code}')

        # Get or create template
        template, created = Template.objects.update_or_create(
            code=code,
            defaults={
                'kind': kind,
                'name': name,
                'version': version,
                'is_active': True,
                'definition': data,  # Store full JSON definition
            }
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(f'  {action} template: {template.name}')

        # Clear existing sections for clean re-import
        if not created:
            template.sections.all().delete()

        # Import sections and questions
        sections_data = data.get('sections', [])

        for section_idx, section_data in enumerate(sections_data):
            section_code = section_data.get('code', f'section_{section_idx}')
            section_title = section_data.get('title', section_code)
            ansi_reference = section_data.get('ansi_reference', section_data.get('ansi_ref', None))
            display_group = section_data.get('display_group', None)

            section = SectionTemplate.objects.create(
                template=template,
                order=section_idx,
                section_id=section_code,
                title=section_title,
                ansi_reference=ansi_reference,
                display_group=display_group
            )

            # Import questions
            questions = section_data.get('questions', [])

            for question_idx, question_data in enumerate(questions):
                # Handle both string and dict format
                if isinstance(question_data, str):
                    prompt = question_data
                    required = True
                    question_type = 'pass_fail'
                    measurement_unit = None
                    ansi_reference = None
                else:
                    prompt = question_data.get('prompt', question_data.get('text', ''))
                    required = question_data.get('required', True)
                    question_type = question_data.get('type', 'pass_fail')
                    measurement_unit = question_data.get('unit', None)
                    ansi_reference = question_data.get('ansi_reference', question_data.get('ansi_ref', None))

                if not prompt:
                    continue

                QuestionTemplate.objects.create(
                    section=section,
                    order=question_idx,
                    code=f'{section_code}_q{question_idx + 1}',
                    prompt=prompt,
                    required=required,
                    question_type=question_type,
                    measurement_unit=measurement_unit,
                    ansi_reference=ansi_reference
                )

        question_count = sum(s.questions.count() for s in template.sections.all())
        self.stdout.write(
            self.style.SUCCESS(
                f'  [OK] Imported {template.sections.count()} sections, '
                f'{question_count} questions'
            )
        )
