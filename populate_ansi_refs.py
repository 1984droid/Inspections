"""
Populate ANSI A92.2 section 8.2 references into the database
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inspections.models import SectionTemplate, QuestionTemplate

# ANSI Section 8.2.3 - Frequent Inspection and Test
frequent_mappings = {
    'frequent_visual_walkaround': {
        'section_ref': '8.2.3(1)',
        'questions': {
            0: '8.2.3(1)',  # Conduct walk around visual inspection
            1: '8.2.3(1)',  # damaged components, cracks, corrosion, wear, loose/missing fasteners
        }
    },
    'frequent_controls': {
        'section_ref': '8.2.3(2)',
        'questions': {
            0: '8.2.3(2)',      # Check all controls for proper operation
            1: '8.2.3(2)(a)',   # Proper operation of interlocks
            2: '8.2.3(2)(b)',   # Controls return to neutral when released
            3: '8.2.3(2)(c)',   # Control functions clearly marked
        }
    },
    'frequent_safety_devices': {
        'section_ref': '8.2.3(3)',
        'questions': {
            0: '8.2.3(3)',  # Visual safety devices
            1: '8.2.3(3)',  # Audible safety devices
        }
    },
    'frequent_insulating_components': {
        'section_ref': '8.2.3(4)',
        'questions': {
            0: '8.2.3(4)',  # Fiberglass and insulating components for visible damage
            1: '8.2.3(4)',  # Insulating components for contamination
        }
    },
    'frequent_markings': {
        'section_ref': '8.2.3(5)',
        'questions': {
            0: '8.2.3(5)',  # Missing or illegible markings
        }
    },
    'frequent_hydraulics': {
        'section_ref': '8.2.3(6)',
        'questions': {
            0: '8.2.3(6)',  # Observable deterioration and excessive leakage
            1: '8.2.3(6)',  # Hydraulic and pneumatic systems
        }
    },
    'frequent_electrical': {
        'section_ref': '8.2.3(7)',
        'questions': {
            0: '8.2.3(7)',  # Electrical systems for malfunctions
            1: '8.2.3(7)',  # Deterioration, dirt and moisture accumulation
        }
    },
    'frequent_function_test': {
        'section_ref': '8.2.3(8)',
        'questions': {
            0: '8.2.3(8)(a)',  # Set up aerial device, including stabilizers
            1: '8.2.3(8)(b)',  # Cycle aerial device through complete range of motion
            2: '8.2.3(8)(c)',  # Check emergency stop(s)
        }
    },
    'frequent_placards': {
        'section_ref': '8.2.3(9)',
        'questions': {
            0: '8.2.3(9)',  # Periodic inspection placard expiration
            1: '8.2.3(9)',  # Electrical test placard expiration
        }
    },
}

# ANSI Section 8.2.4 - Periodic Inspection or Test
periodic_mappings = {
    'periodic_structure': {
        'section_ref': '8.2.4(1)',
        'questions': {
            0: '8.2.4(1)',  # Structural members for deformation, cracks, or corrosion
        }
    },
    'periodic_wear_components': {
        'section_ref': '8.2.4(2)',
        'questions': {
            0: '8.2.4(2)',  # Pins, bearings, shafts, gears, rollers, locking devices
            1: '8.2.4(2)',  # Chains, sprockets, wire ropes, synthetic ropes, sheaves
        }
    },
    'periodic_hydraulic_settings': {
        'section_ref': '8.2.4(3)',
        'questions': {
            0: '8.2.4(3)',  # Hydraulic and pneumatic relief valve settings
            1: '8.2.4(4)',  # Hydraulic system oil level
        }
    },
    'periodic_hoses_fittings': {
        'section_ref': '8.2.4(5)',
        'questions': {
            0: '8.2.4(5)',  # Hoses and fittings for leakage
            1: '8.2.4(5)',  # Abnormal deformation or excessive abrasion
        }
    },
    'periodic_power_components': {
        'section_ref': '8.2.4(6)',
        'questions': {
            0: '8.2.4(6)',  # Compressors, pumps, motors, generators secure and free of leaks
            1: '8.2.4(6)',  # Unusual noises, vibration, overheating, loss of speed
        }
    },
    'periodic_valves': {
        'section_ref': '8.2.4(7)',
        'questions': {
            0: '8.2.4(7)',  # Hydraulic and pneumatic valves operate correctly
            1: '8.2.4(7)',  # Valve housings free of cracks and leaks
            2: '8.2.4(7)',  # Valve spools operate freely
        }
    },
    'periodic_vacuum_system': {
        'section_ref': '8.2.4(8)',
        'questions': {
            0: '8.2.4(8)',  # Vacuum limiting system inspection and function
        }
    },
    'periodic_cylinders': {
        'section_ref': '8.2.4(9)',
        'questions': {
            0: '8.2.4(9)',  # Hydraulic and pneumatic cylinders operate correctly
            1: '8.2.4(9)',  # Holding valves operate correctly
        }
    },
    'periodic_filters': {
        'section_ref': '8.2.4(10)',
        'questions': {
            0: '8.2.4(10)',  # Filters clean and free of contamination
            1: '8.2.4(10)',  # No foreign material in system
        }
    },
    'periodic_electrical': {
        'section_ref': '8.2.4(11)',
        'questions': {
            0: '8.2.4(11)',  # Electrical systems and components for deterioration
        }
    },
    'periodic_performance_test': {
        'section_ref': '8.2.4(12)',
        'questions': {
            0: '8.2.4(12)',  # Performance test of all boom movements
        }
    },
    'periodic_fasteners': {
        'section_ref': '8.2.4(13)',
        'questions': {
            0: '8.2.4(13)',  # Bolts and fasteners tight and secure
        }
    },
    'periodic_welds': {
        'section_ref': '8.2.4(14)',
        'questions': {
            0: '8.2.4(14)',  # Welds free of cracks or defects
        }
    },
    'periodic_markings': {
        'section_ref': '8.2.4(15)',
        'questions': {
            0: '8.2.4(15)',  # Identification, operational, instructional markings
        }
    },
    'periodic_insulation_condition': {
        'section_ref': '8.2.4(16)',
        'questions': {
            0: '8.2.4(16)',  # Insulating components clean and free of conditions compromising insulation
        }
    },
    'periodic_upper_control_resistance': {
        'section_ref': '8.2.4(17)',
        'questions': {
            0: '8.2.4(17)',  # Upper controls high-resistance components maintained
        }
    },
}

# ANSI Section 5.4.3.1 - Periodic/Maintenance Test Procedures for Category A & B Aerial Devices
category_ab_mappings = {
    'ab_bonding_and_platform': {
        'section_ref': '5.4.3.1(1-2)',
        'questions': {
            0: '5.4.3.1(1)',  # All conductive material at platform end bonded
            1: '5.4.3.1(2)',  # Category A non-conductive platform with metal liner
        }
    },
    'ab_pretest_system_checks': {
        'section_ref': '5.4.3.1(3-7)',
        'questions': {
            0: '5.4.3.1(3)',  # Vacuum limiting system inspected and verified
            1: '5.4.3.1(4)',  # Lower test electrode system inspected for continuity
            2: '5.4.3.1(5)',  # Hydraulic lines filled with oil
            3: '5.4.3.1(6)',  # Shunting if continuity cannot be ensured
            4: '5.4.3.1(7)',  # Chassis insulating system shunted
        }
    },
    'ab_grounding_and_metering': {
        'section_ref': '5.4.3.1(8-10)',
        'questions': {
            0: '5.4.3.1(8)',  # Vehicle chassis grounded
            1: '5.4.3.1(9)',  # Current meter receptacle connected through shielded cable
            2: '5.4.3.1(10)',  # Booms positioned per figures
        }
    },
    'ab_test_method_and_results': {
        'section_ref': '5.4.3.1(11-12)',
        'questions': {
            0: '5.4.3.1(11)',  # Test method selected (ac, dc, line contact, or energized line)
            1: '5.4.3.1(12)',  # Test voltage documented
            2: '5.4.3.1(12)',  # Final leakage current documented
            3: '5.4.3.1',     # Pass/fail result
        }
    },
}

# ANSI Section 5.4.3.2 - Periodic/Maintenance Test Procedures for Category C, D and E Aerial Devices
category_cde_mappings = {
    'cde_bonding_and_oil': {
        'section_ref': '5.4.3.2(1-2)',
        'questions': {
            0: '5.4.3.2(1)',  # Platform-end conductive material bonded
            1: '5.4.3.2(2)',  # Hydraulic lines filled with oil
        }
    },
    'cde_shunting': {
        'section_ref': '5.4.3.2(3-4)',
        'questions': {
            0: '5.4.3.2(3)',  # Shunting required if continuity cannot be ensured
            1: '5.4.3.2(4)',  # Chassis insulating systems shunted
        }
    },
    'cde_test_method_and_config': {
        'section_ref': '5.4.3.2(5)',
        'questions': {
            0: '5.4.3.2(5)',  # Test method selected (ac/dc per Table 2, alternate dc, or energized line contact)
        }
    },
    'cde_results': {
        'section_ref': '5.4.3.2(6)',
        'questions': {
            0: '5.4.3.2(6)',  # Test voltage documented
            1: '5.4.3.2(6)',  # Final leakage current documented
            2: '5.4.3.2',     # Pass/fail result
        }
    },
}

# ANSI Section 5.4.2.3 - Test Procedures for Aerial Ladders and Vertical Towers
positioning_mappings = {
    'positioning': {
        'section_ref': '5.4.2.3',
        'questions': {
            0: '5.4.2.3(1)',  # Aerial ladder test with upper section extended
            1: '5.4.2.3(3)',  # Vertical tower with platform rails raised
            2: '5.4.2.3(2)',  # Insulated units tested per 5.4.2.2
        }
    },
}

# ANSI Section 5.4.2.4 - Test Procedures for Chassis Insulating Systems
chassis_insulation_mappings = {
    ('setup', 'ANSI A92.2 (2021) Test - Chassis Insulating System'): {
        'section_ref': '5.4.2.4',
        'questions': {
            0: '5.4.2.4(4)',  # Voltage applied to metal above insulating system
            1: '5.4.2.4(1)',  # Hydraulic lines filled with oil
            2: '5.4.2.4(2)',  # MEWP connected to current meter and ground
            3: '5.4.2.4(3)',  # Booms positioned per Figure 3
        }
    },
    ('execution', 'ANSI A92.2 (2021) Test - Chassis Insulating System'): {
        'section_ref': '5.4.2.4(5-6)',
        'questions': {
            0: '5.4.2.4(5)',  # Test performed (50 kV ac for 3 minutes, max 3mA)
            1: '5.4.2.4(5)',  # Test voltage documented
            2: '5.4.2.4(6)',  # Final current documented
        }
    },
}

# ANSI Section 5.4.2.6 - Test Procedures for Upper Controls with High Electrical Resistance
upper_controls_mappings = {
    ('setup', 'ANSI A92.2 (2021) Test - Upper Controls High Electrical Resistance Components'): {
        'section_ref': '5.4.2.6',
        'questions': {
            0: '5.4.2.6',  # Test configured per Figure 6
        }
    },
    ('execution', 'ANSI A92.2 (2021) Test - Upper Controls High Electrical Resistance Components'): {
        'section_ref': '5.4.2.6',
        'questions': {
            0: '5.4.2.6',  # Test performed (40 kV ac for 3 minutes, max 400 microamperes)
            1: '5.4.2.6',  # Test voltage documented
            2: '5.4.2.6',  # Final current documented
        }
    },
}

# ANSI Section 5.4.2.5 - Test Procedures for Insulating Liners
liner_test_mappings = {
    'method_1_conductive_liquid': {
        'section_ref': '5.4.2.5',
        'questions': {
            0: '5.4.2.5',  # Liner tested in conductive liquid
            1: '5.4.2.5',  # Test completed without breakdown (50 kV ac for 1 minute)
        }
    },
    'method_2_alternate_electrodes': {
        'section_ref': '5.4.2.5',
        'questions': {
            0: '5.4.2.5',  # Inside and outside surfaces tested
            1: '5.4.2.5',  # All sides and bottom tested
            2: '5.4.2.5',  # Test completed without puncture/breakdown
        }
    },
}

def update_references():
    """Update all ANSI references"""
    updated_sections = 0
    updated_questions = 0

    # Update Frequent Inspection sections and questions
    print("Updating Frequent Inspection references...")
    for section_id, data in frequent_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            # Update questions in this section
            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} not found")

    # Update Periodic Inspection sections
    print("\nUpdating Periodic Inspection references...")
    for section_id, data in periodic_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            # Update questions if any are specified
            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} not found")

    # Update Category A&B Periodic/Maintenance Electrical Test sections
    print("\nUpdating Category A&B Periodic/Maintenance Electrical Test references...")
    for section_id, data in category_ab_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            # Update questions if any are specified
            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} not found")

    # Update Category C,D,E Periodic/Maintenance Electrical Test sections
    print("\nUpdating Category C,D,E Periodic/Maintenance Electrical Test references...")
    for section_id, data in category_cde_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            # Update questions if any are specified
            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} not found")

    # Update Positioning and Configuration sections
    print("\nUpdating Positioning and Configuration references...")
    for section_id, data in positioning_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} not found")

    # Update Chassis Insulating System sections
    print("\nUpdating Chassis Insulating System references...")
    for (section_id, template_name), data in chassis_insulation_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id, template__name=template_name)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} in template {template_name} not found")

    # Update Upper Controls High Resistance sections
    print("\nUpdating Upper Controls High Resistance references...")
    for (section_id, template_name), data in upper_controls_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id, template__name=template_name)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} in template {template_name} not found")

    # Update Insulating Liner Test sections
    print("\nUpdating Insulating Liner Test references...")
    for section_id, data in liner_test_mappings.items():
        try:
            section = SectionTemplate.objects.get(section_id=section_id)
            section.ansi_reference = data['section_ref']
            section.save()
            updated_sections += 1
            print(f"  [OK] {section.title} -> {data['section_ref']}")

            for q_order, q_ref in data['questions'].items():
                try:
                    question = QuestionTemplate.objects.get(section=section, order=q_order)
                    question.ansi_reference = q_ref
                    question.save()
                    updated_questions += 1
                    print(f"    [OK] Q{q_order}: {question.prompt[:50]}... -> {q_ref}")
                except QuestionTemplate.DoesNotExist:
                    print(f"    [SKIP] Question order {q_order} not found in {section_id}")
        except SectionTemplate.DoesNotExist:
            print(f"  [SKIP] Section {section_id} not found")

    print(f"\n[COMPLETE] Updated {updated_sections} sections and {updated_questions} questions")

if __name__ == '__main__':
    update_references()
