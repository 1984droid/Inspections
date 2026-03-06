import json
from pathlib import Path
from django.core.management.base import BaseCommand
from inspections.models import Template, SectionTemplate, QuestionTemplate


class Command(BaseCommand):
    help = 'Import A92.2 inspection templates from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            default='.',
            help='Path to directory containing JSON template files',
        )

    def handle(self, *args, **options):
        base_path = Path(options['path'])

        # List of template files to import
        template_files = [
            'insp.a92_2_2021.frequent.full.v1.json',
            'insp.a92_2_2021.periodic.full.v1.json',
            'insp.a92_2_2021.test.chassis_insulating_system.v1.json',
            'insp.a92_2_2021.test.high_resistance_upper_controls.v1.json',
            'insp.a92_2_2021.test.insulating_liner.v1.json',
            'insp.a92_2_2021.test.lower_insulating_boom_section.v1.json',
            'insp.a92_2_2021.test.upper_insulating_boom_section.v1.json',
        ]

        for filename in template_files:
            file_path = base_path / filename

            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f'File not found: {file_path}'))
                continue

            try:
                self.import_template(file_path)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error importing {filename}: {str(e)}'))
                if options.get('verbosity', 1) > 1:
                    import traceback
                    traceback.print_exc()

    def import_template(self, file_path):
        """Import a single template from JSON file"""
        self.stdout.write(f'Importing {file_path.name}...')

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Determine kind from template_id or archetype
        template_id = data.get('template_id', '')
        archetype = data.get('archetype', '')

        if 'frequent' in template_id or archetype == 'walkaround':
            kind = 'frequent'
        elif 'periodic' in template_id or archetype == 'regulatory_periodic':
            kind = 'periodic'
        elif 'test' in template_id or archetype == 'test_procedure':
            kind = 'test'
        else:
            kind = 'frequent'  # default

        # Get or create template
        template, created = Template.objects.update_or_create(
            code=template_id,
            defaults={
                'kind': kind,
                'name': data.get('name', template_id),
                'version': data.get('version', '1.0.0'),
                'is_active': data.get('status', 'active') == 'active',
            }
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(f'  {action} template: {template.name}')

        # Clear existing sections for clean re-import
        if not created:
            template.sections.all().delete()

        # Import sections and questions
        sections_data = data.get('sections', [])
        section_order_list = data.get('ui', {}).get('section_order', [])

        # Create order mapping
        section_order_map = {sid: idx for idx, sid in enumerate(section_order_list)}

        for section_data in sections_data:
            section_id = section_data.get('section_id')
            section_title = section_data.get('title', section_id)

            # Get order from section_order list
            order = section_order_map.get(section_id, 999)

            section = SectionTemplate.objects.create(
                template=template,
                order=order,
                section_id=section_id,
                title=section_title
            )

            # Import questions (items in the JSON)
            items = section_data.get('items', [])

            for item_idx, item_data in enumerate(items):
                # Build prompt from title and description
                item_title = item_data.get('title', '')
                item_desc = item_data.get('description', '')

                # Combine title and description for prompt
                if item_desc and item_desc.strip() and item_desc != item_title:
                    prompt = f"{item_title}\n{item_desc}"
                else:
                    prompt = item_title

                # Extract question code
                item_id = item_data.get('item_id', '')

                # Check if required (default to True)
                required = item_data.get('required', True)

                QuestionTemplate.objects.create(
                    section=section,
                    order=item_idx,
                    code=item_id,
                    prompt=prompt,
                    required=required
                )

        question_count = sum(s.questions.count() for s in template.sections.all())
        self.stdout.write(
            self.style.SUCCESS(
                f'  Imported {template.sections.count()} sections, '
                f'{question_count} questions'
            )
        )
