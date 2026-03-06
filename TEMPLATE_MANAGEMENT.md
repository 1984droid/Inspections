# Template Management Guide

## Current Template Format

The app now uses a simplified JSON template format:

```json
{
  "template": {
    "code": "a92.2-2021-periodic",
    "name": "ANSI A92.2 (2021) Periodic Inspection",
    "version": "v1",
    "kind": "periodic"
  },
  "rules": {
    "fail_requires_defect_note": true,
    "fail_requires_photo": true,
    "photo_scope": "per_defect"
  },
  "sections": [
    {
      "code": "section_code",
      "title": "Section Title",
      "questions": [
        { "prompt": "Question text here", "required": true }
      ]
    }
  ]
}
```

## Importing Templates

### Import New Template

```bash
python manage.py import_new_template periodic_a922.json
```

### Replace Existing Template

```bash
python manage.py import_new_template periodic_a922.json --replace
```

## Template Structure

### Template Metadata

| Field | Description | Example |
|-------|-------------|---------|
| `code` | Unique identifier | `a92.2-2021-periodic` |
| `name` | Display name | `ANSI A92.2 (2021) Periodic Inspection` |
| `version` | Version string | `v1` |
| `kind` | Template type | `periodic`, `frequent`, `test` |

### Section Structure

| Field | Description | Required |
|-------|-------------|----------|
| `code` | Section identifier | Yes |
| `title` | Section display title | Yes |
| `questions` | Array of questions | Yes |

### Question Structure

| Field | Description | Default |
|-------|-------------|---------|
| `prompt` | Question text | Required |
| `required` | Must be answered | `true` |

**Simple format:**
```json
{ "prompt": "Question text", "required": true }
```

**Or just a string:**
```json
"Question text"
```

## Creating a New Template

### Step 1: Create JSON File

Create a file like `frequent_a922.json`:

```json
{
  "template": {
    "code": "a92.2-2021-frequent",
    "name": "ANSI A92.2 (2021) Frequent Inspection",
    "version": "v1",
    "kind": "frequent"
  },
  "rules": {
    "fail_requires_defect_note": true,
    "fail_requires_photo": true,
    "photo_scope": "per_defect"
  },
  "sections": [
    {
      "code": "visual_inspection",
      "title": "Visual Inspection",
      "questions": [
        { "prompt": "Machine inspected for damaged components", "required": true },
        { "prompt": "All fasteners present and secure", "required": true }
      ]
    }
  ]
}
```

### Step 2: Import

```bash
python manage.py import_new_template frequent_a922.json
```

### Step 3: Verify

```bash
python manage.py shell
```

```python
from inspections.models import Template
t = Template.objects.get(code='a92.2-2021-frequent')
print(f"Sections: {t.sections.count()}")
```

## Managing Templates in Django Admin

1. Go to: **http://localhost:3000/admin/**
2. Navigate to **Templates**
3. View/edit templates, sections, and questions

## Template Types (kind)

| Kind | Description | Use Case |
|------|-------------|----------|
| `frequent` | Frequent inspections | Daily/weekly walkarounds |
| `periodic` | Periodic inspections | Monthly/annual comprehensive |
| `test` | Electrical tests | Dielectric testing |

## Viewing Templates

### List All Templates

```bash
python manage.py shell -c "from inspections.models import Template; [print(f'{t.code}: {t.name} ({t.sections.count()} sections)') for t in Template.objects.all()]"
```

### View Template Details

```bash
python manage.py shell
```

```python
from inspections.models import Template

t = Template.objects.get(code='a92.2-2021-periodic')
print(f"Template: {t.name}")
print(f"Sections: {t.sections.count()}")

for section in t.sections.all()[:5]:
    print(f"\n{section.title}")
    for q in section.questions.all()[:3]:
        print(f"  - {q.prompt[:60]}...")
```

## Updating Templates

### Option 1: Re-import with --replace

```bash
# Edit your JSON file
# Then re-import
python manage.py import_new_template periodic_a922.json --replace
```

### Option 2: Django Admin

1. Go to admin panel
2. Find template
3. Edit sections/questions manually

### Option 3: Django Shell

```python
from inspections.models import Template, SectionTemplate

# Get template
t = Template.objects.get(code='a92.2-2021-periodic')

# Add new section
section = SectionTemplate.objects.create(
    template=t,
    order=100,
    section_id='new_section',
    title='New Section Title'
)

# Add question to section
from inspections.models import QuestionTemplate
QuestionTemplate.objects.create(
    section=section,
    order=0,
    code='new_q1',
    prompt='New question text?',
    required=True
)
```

## Deleting Templates

### Delete Single Template

```bash
python manage.py shell -c "from inspections.models import Template; Template.objects.filter(code='template-code').delete()"
```

### Delete All Templates

```bash
python manage.py shell -c "from inspections.models import Template; Template.objects.all().delete()"
```

**Warning**: This will delete associated inspections!

## Best Practices

1. **Use unique codes**: `a92.2-2021-periodic`, `a92.2-2021-frequent`
2. **Version your templates**: Include version in name or code
3. **Keep sections organized**: Use meaningful section codes
4. **Clear question text**: Make prompts specific and actionable
5. **Backup before changes**: Export data before major updates

## Exporting Templates

To export a template back to JSON (for backup or sharing):

```bash
python manage.py shell
```

```python
import json
from inspections.models import Template

t = Template.objects.get(code='a92.2-2021-periodic')

output = {
    'template': {
        'code': t.code,
        'name': t.name,
        'version': t.version,
        'kind': t.kind
    },
    'sections': []
}

for section in t.sections.all():
    section_data = {
        'code': section.section_id,
        'title': section.title,
        'questions': []
    }

    for question in section.questions.all():
        section_data['questions'].append({
            'prompt': question.prompt,
            'required': question.required
        })

    output['sections'].append(section_data)

# Save to file
with open('exported_template.json', 'w') as f:
    json.dump(output, f, indent=2)

print("Template exported to exported_template.json")
```

## Troubleshooting

### Template not showing in dropdown

- Check `is_active = True`
- Restart server after import

### Questions not imported

- Verify JSON structure
- Check for typos in field names
- Look for console errors during import

### Import fails

- Check file encoding (UTF-8)
- Validate JSON syntax
- Check required fields present

### Duplicate templates

```bash
# Find duplicates
python manage.py shell -c "from inspections.models import Template; from collections import Counter; codes = [t.code for t in Template.objects.all()]; dupes = [c for c, count in Counter(codes).items() if count > 1]; print(dupes)"
```

## Next Steps: Dielectric Test Templates

When ready to add dielectric test templates:

1. Create `test_dielectric_chassis.json`
2. Set `"kind": "test"`
3. Include specific test questions
4. Import with: `python manage.py import_new_template test_dielectric_chassis.json`

Example structure:
```json
{
  "template": {
    "code": "a92.2-2021-test-chassis-dielectric",
    "name": "Chassis Insulating System Test",
    "version": "v1",
    "kind": "test"
  },
  "sections": [
    {
      "code": "test_procedure",
      "title": "Dielectric Test Procedure",
      "questions": [
        { "prompt": "Test setup completed per manufacturer specs", "required": true }
      ]
    }
  ]
}
```
