"""
Add ANSI A92.2 references to sections that are missing them
Based on ANSI A92.2 (2021) standard
"""
from inspections.models import SectionTemplate

# Mapping of section titles to ANSI references
# Section 8.2.4 = Frequent Inspection
# Section 8.2.5 = Periodic Inspection

section_references = {
    # Frequent Inspection sections (8.2.4)
    'Frequent Inspection - Visual Walkaround': '8.2.4.1',
    'Frequent Inspection - Controls and Interlocks': '8.2.4.2',
    'Frequent Inspection - Safety Devices': '8.2.4.3',
    'Frequent Inspection - Insulating Components': '8.2.4.4',
    'Frequent Inspection - Hydraulic and Pneumatic Systems': '8.2.4.5',
    'Frequent Inspection - Electrical Systems': '8.2.4.6',
    'Frequent Inspection - Functional Tests': '8.2.4.7',
    'Frequent Inspection - Markings and Decals': '8.2.4.8',
    'Frequent Inspection - Placards and Test Expiration': '8.2.4.9',

    # Periodic Inspection sections (8.2.5)
    'Periodic Inspection - Structural Components': '8.2.5.1',
    'Periodic Inspection - Welds': '8.2.5.1',
    'Periodic Inspection - Wear Components': '8.2.5.2',
    'Periodic Inspection - Fasteners': '8.2.5.2',
    'Periodic Inspection - Hydraulic System Settings': '8.2.5.3',
    'Periodic Inspection - Hoses and Fittings': '8.2.5.3',
    'Periodic Inspection - Hydraulic and Pneumatic Valves': '8.2.5.3',
    'Periodic Inspection - Cylinders and Holding Valves': '8.2.5.3',
    'Periodic Inspection - Hydraulic and Pneumatic Filters': '8.2.5.3',
    'Periodic Inspection - Pumps, Motors, and Generators': '8.2.5.3',
    'Periodic Inspection - Electrical Components': '8.2.5.4',
    'Periodic Inspection - Boom Performance': '8.2.5.5',
    'Periodic Inspection - Identification and Markings': '8.2.5.6',
    'Periodic Inspection - Vacuum Limiting Systems': '8.2.5.7',
    'Periodic Inspection - Insulating System Condition': '8.2.5.7',
    'Periodic Inspection - High Resistance Upper Controls': '8.2.5.8',
}

# Update sections
updated_count = 0
for section_title, ansi_ref in section_references.items():
    sections = SectionTemplate.objects.filter(title=section_title)
    if sections.exists():
        count = sections.update(ansi_reference=ansi_ref)
        updated_count += count
        print(f'✓ Updated {count} section(s): {section_title} → {ansi_ref}')
    else:
        print(f'✗ Section not found: {section_title}')

print(f'\nTotal sections updated: {updated_count}')
