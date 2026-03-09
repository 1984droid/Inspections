"""
Update display_group field in existing SectionTemplate records based on template JSON structure
"""
import django
import os
import sys

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inspections.models import SectionTemplate

# Update mapping based on JSON files
updates = [
    # Liner test
    ('a92.2-2021-test-insulating-liner', 'method_1_conductive_liquid', {'display_group': 'Test Method', 'ansi_reference': '5.4.2.5'}),
    ('a92.2-2021-test-insulating-liner', 'method_2_alternate_electrodes', {'display_group': 'Test Method', 'ansi_reference': '5.4.2.5'}),

    # Cat A/B
    ('a92.2-2021-test-dielectric-cat-a-b', 'ab_bonding_and_platform', {'display_group': 'Setup', 'ansi_reference': '5.4.3.2'}),
    ('a92.2-2021-test-dielectric-cat-a-b', 'ab_pretest_system_checks', {'display_group': 'Setup', 'ansi_reference': '5.4.3.2'}),
    ('a92.2-2021-test-dielectric-cat-a-b', 'ab_grounding_and_metering', {'display_group': 'Setup', 'ansi_reference': '5.4.3.2'}),
    ('a92.2-2021-test-dielectric-cat-a-b', 'ab_test_method_and_results', {'display_group': 'Test Execution and Results', 'ansi_reference': '5.4.3.3'}),

    # Cat C/D/E
    ('a92.2-2021-test-dielectric-cat-cde', 'cde_bonding_and_oil', {'display_group': 'Setup', 'ansi_reference': '5.4.3.2'}),
    ('a92.2-2021-test-dielectric-cat-cde', 'cde_shunting', {'display_group': 'Setup', 'ansi_reference': '5.4.3.2'}),
    ('a92.2-2021-test-dielectric-cat-cde', 'cde_test_method_and_config', {'display_group': 'Test Execution', 'ansi_reference': '5.4.3.3'}),
    ('a92.2-2021-test-dielectric-cat-cde', 'cde_results', {'display_group': 'Test Results', 'ansi_reference': '5.4.3.3'}),

    # Chassis
    ('a92.2-2021-test-chassis-insulating-system', 'setup', {'display_group': 'Setup', 'ansi_reference': '5.4.2.4'}),
    ('a92.2-2021-test-chassis-insulating-system', 'execution', {'display_group': 'Test Execution and Results', 'ansi_reference': '5.4.2.4'}),

    # Upper Controls
    ('a92.2-2021-test-upper-controls-high-electrical-resistance', 'setup', {'display_group': 'Setup', 'ansi_reference': '5.4.2.2'}),
    ('a92.2-2021-test-upper-controls-high-electrical-resistance', 'execution', {'display_group': 'Test Execution and Results', 'ansi_reference': '5.4.2.2'}),

    # Ladders
    ('a92.2-2021-test-aerial-ladders-vertical-towers', 'positioning_and_config', {'display_group': 'Test Setup and Positioning', 'ansi_reference': '5.4.2.3'}),

    # Load Test
    ('a92.2-2021-major-structural-load-test', 'pre_test_inspection', {'display_group': 'Pre-Test Inspection', 'ansi_reference': '5.3.1'}),
    ('a92.2-2021-major-structural-load-test', 'level_surface_test', {'display_group': 'Level Surface Test', 'ansi_reference': '5.3.2'}),
    ('a92.2-2021-major-structural-load-test', 'slope_stability_test', {'display_group': 'Slope Stability Test', 'ansi_reference': '5.3.2'}),
    ('a92.2-2021-major-structural-load-test', 'post_test_inspection', {'display_group': 'Post-Test Inspection', 'ansi_reference': '5.3.3'}),
    ('a92.2-2021-major-structural-load-test', 'test_documentation', {'display_group': 'Test Documentation', 'ansi_reference': '5.3.3'}),
]

updated_count = 0
for template_code, section_code, fields in updates:
    try:
        section = SectionTemplate.objects.get(template__code=template_code, section_id=section_code)
        for field_name, value in fields.items():
            setattr(section, field_name, value)
        section.save()
        print(f'[OK] Updated {template_code} / {section_code}')
        updated_count += 1
    except SectionTemplate.DoesNotExist:
        print(f'[SKIP] Section not found: {template_code} / {section_code}')
    except Exception as e:
        print(f'[ERROR] {template_code} / {section_code}: {str(e)}')

print(f'\n[DONE] Updated {updated_count} sections')
