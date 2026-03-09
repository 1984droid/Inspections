from inspections.models import Inspection

i = Inspection.objects.get(pk=2)
liner_answers = i.answers.filter(question__section__title__icontains='Method')

print(f'Total Method answers: {liner_answers.count()}')
print('\nBreakdown by section:')

sections = {}
for a in liner_answers:
    title = a.question.section.title
    if title not in sections:
        sections[title] = {'pass': 0, 'fail': 0, 'na': 0}
    sections[title][a.status] += 1

for title, counts in sections.items():
    total_answered = counts['pass'] + counts['fail']
    print(f'\n{title}:')
    print(f'  PASS: {counts["pass"]}')
    print(f'  FAIL: {counts["fail"]}')
    print(f'  N/A: {counts["na"]}')
    print(f'  Total answered (non-N/A): {total_answered}')
