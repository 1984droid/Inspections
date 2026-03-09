"""
Update remaining template JSON files with display_group and ansi_reference fields
"""
import json

# uppercontrols.json
with open('uppercontrools.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for section in data['sections']:
    if section['code'] == 'setup':
        section['ansi_reference'] = '5.4.2.2'
        section['display_group'] = 'Setup'
    elif section['code'] == 'execution':
        section['ansi_reference'] = '5.4.2.2'
        section['display_group'] = 'Test Execution and Results'

with open('uppercontrools.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print('[OK] Updated uppercontrools.json')

# ladders.json
with open('ladders.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for section in data['sections']:
    if 'Positioning' in section['title']:
        section['ansi_reference'] = '5.4.2.3'
        section['display_group'] = 'Test Setup and Positioning'

with open('ladders.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print('[OK] Updated ladders.json')

# load_test_structural.json
with open('load_test_structural.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for section in data['sections']:
    title = section['title']
    if 'Pre-Test Inspection' in title:
        section['ansi_reference'] = '5.3.1'
        section['display_group'] = 'Pre-Test Inspection'
    elif 'Level Surface' in title:
        section['ansi_reference'] = '5.3.2'
        section['display_group'] = 'Level Surface Test'
    elif 'Slope Stability' in title:
        section['ansi_reference'] = '5.3.2'
        section['display_group'] = 'Slope Stability Test'
    elif 'Post-Test Inspection' in title:
        section['ansi_reference'] = '5.3.3'
        section['display_group'] = 'Post-Test Inspection'
    elif 'Test Documentation' in title:
        section['ansi_reference'] = '5.3.3'
        section['display_group'] = 'Test Documentation'

with open('load_test_structural.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print('[OK] Updated load_test_structural.json')
print('\nAll template JSON files updated successfully!')
