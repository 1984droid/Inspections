from datetime import datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from inspections.models import Inspection, InspectionAnswer, Defect, DefectPhoto
from .pdf_package import generate_package_pdf
from .pdf_certificate import generate_certificate_pdf


def finalize_inspection(inspection_id, user_id):
    """
    Finalize an inspection:
    1. Validate all required questions are answered
    2. If any FAIL, ensure defects exist with notes and photos
    3. Compute overall_result
    4. Generate certificate_number
    5. Generate PDFs
    6. Lock the inspection
    """
    try:
        inspection = Inspection.objects.select_related(
            'template', 'equipment', 'inspector'
        ).prefetch_related(
            'answers__question__section',
            'defects__photos'
        ).get(id=inspection_id)
    except Inspection.DoesNotExist:
        raise ValidationError(f"Inspection {inspection_id} not found")

    # Check if inspection can be finalized
    if not inspection.can_finalize():
        raise ValidationError(f"Inspection cannot be finalized (status: {inspection.status})")

    # Validation: All required questions must be answered
    template = inspection.template
    all_questions = []
    for section in template.sections.all():
        all_questions.extend(section.questions.filter(required=True))

    answered_question_ids = set(
        inspection.answers.values_list('question_id', flat=True)
    )

    required_question_ids = set(q.id for q in all_questions)
    missing_questions = required_question_ids - answered_question_ids

    if missing_questions:
        raise ValidationError(
            f"Cannot finalize: {len(missing_questions)} required question(s) not answered"
        )

    # Check for failed answers
    failed_answers = inspection.answers.filter(status='fail')
    has_failures = failed_answers.exists()

    if has_failures:
        # Validation: Must have at least one defect
        defects = inspection.defects.all()
        if not defects.exists():
            raise ValidationError(
                "Cannot finalize: Inspection has failed items but no defects recorded"
            )

        # Validation: Each defect must have a note
        for defect in defects:
            if not defect.note or not defect.note.strip():
                raise ValidationError(
                    f"Cannot finalize: Defect #{defect.id} is missing a note"
                )

        # Validation: Each defect must have at least one photo
        for defect in defects:
            if not defect.photos.exists():
                raise ValidationError(
                    f"Cannot finalize: Defect #{defect.id} is missing a photo"
                )

    # Compute overall_result
    if has_failures:
        overall_result = 'fail'
    else:
        # Check if all answers are NA
        all_na = all(
            answer.status == 'na'
            for answer in inspection.answers.all()
        )
        overall_result = 'na' if all_na else 'pass'

    # Generate certificate number if not present
    if not inspection.certificate_number:
        date_str = datetime.now().strftime('%Y%m%d')
        # Simple sequential number (could be improved with proper counter)
        count = Inspection.objects.filter(
            certificate_number__startswith=f'A922-{date_str}-'
        ).count()
        inspection.certificate_number = f'A922-{date_str}-{count + 1:04d}'

    # Use atomic transaction for all updates
    with transaction.atomic():
        # Update inspection
        inspection.status = 'completed'
        inspection.overall_result = overall_result
        inspection.completed_at = datetime.now()
        inspection.save()

        # Generate PDFs
        package_doc = generate_package_pdf(inspection)
        certificate_doc = generate_certificate_pdf(inspection)

        # Lock the inspection
        inspection.status = 'locked'
        inspection.locked_at = datetime.now()
        inspection.save()

    return {
        'success': True,
        'inspection': inspection,
        'package_doc': package_doc,
        'certificate_doc': certificate_doc,
    }
