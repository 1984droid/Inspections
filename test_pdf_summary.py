#!/usr/bin/env python
"""Test script to verify PDF summary logic"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'InspectionApp.settings')
django.setup()

from inspections.models import Inspection

# Get latest inspection
inspection = Inspection.objects.latest('created_at')

# Calculate counts (same as pdf_package.py lines 294-298)
total_questions = inspection.answers.count()
pass_count = inspection.answers.filter(status='pass').count()
fail_count = inspection.answers.filter(status='fail').count()
na_count = inspection.answers.filter(status='na').count()
defect_count = inspection.defects.count()

print(f"Inspection ID: {inspection.id}")
print(f"Overall Result: {inspection.overall_result}")
print(f"\nCounts:")
print(f"  Total Questions: {total_questions}")
print(f"  Pass: {pass_count}")
print(f"  Fail: {fail_count}")
print(f"  N/A: {na_count}")
print(f"  Defects: {defect_count}")

print(f"\nCondition check (fail_count > 0 or defect_count > 0): {fail_count > 0 or defect_count > 0}")

print("\nKey Findings would show:")
if fail_count > 0 or defect_count > 0:
    print("  [Failure/Defect branch]")
    if fail_count > 0:
        print(f"  • {fail_count} item(s) failed inspection")
    if defect_count > 0:
        print(f"  • {defect_count} defect(s) documented with photos and notes")
    if pass_count > 0:
        print(f"  • {pass_count} item(s) passed inspection")
else:
    print("  [No failure/defect branch]")
    print("  • All inspected items passed or were marked as not applicable")
    print("  • No defects were identified during this inspection")

print("\nStatistics Table shows:")
print(f"  Defects Recorded: {defect_count}")
