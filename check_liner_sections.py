from inspections.models import Inspection

i = Inspection.objects.get(pk=2)

# Find all test module templates
test_modules = i.test_modules.all()
print(f'Test modules: {test_modules.count()}\n')

for tm in test_modules:
    print(f'\n=== {tm.template.name} ===')
    sections = tm.template.sections.all().order_by('order')
    print(f'Sections: {sections.count()}')
    for section in sections:
        answers = i.answers.filter(question__section=section)
        non_na = answers.exclude(status='n/a').count()
        print(f'  {section.order}. {section.title} - {answers.count()} answers ({non_na} non-N/A)')

        # Check for measurements
        with_measurements = answers.exclude(measurement_value__isnull=True)
        if with_measurements.exists():
            print(f'     HAS MEASUREMENTS:')
            for a in with_measurements:
                print(f'       - {a.question.prompt[:50]}... = {a.measurement_value} {a.question.measurement_unit}')
