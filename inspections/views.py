from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from django.db.models import Q
from django.core.exceptions import ValidationError
from .models import (
    Equipment, Customer, Template, Inspection, InspectionAnswer,
    Defect, DefectPhoto, SectionTemplate, GeneratedDocument, InspectionTestModule
)
from .forms import EquipmentForm, CustomerForm, DefectForm, DefectPhotoForm
from .services import finalize_inspection


@login_required
def dashboard(request):
    """Main dashboard/home page"""
    recent_inspections = Inspection.objects.filter(
        inspector=request.user
    ).select_related('template', 'equipment')[:10]

    context = {
        'recent_inspections': recent_inspections,
    }
    return render(request, 'inspections/dashboard.html', context)


@login_required
def inspection_list(request):
    """List/search inspections"""
    query = request.GET.get('q', '')

    inspections = Inspection.objects.select_related(
        'template', 'equipment', 'inspector'
    ).order_by('-started_at')

    if query:
        inspections = inspections.filter(
            Q(equipment__serial_number__icontains=query) |
            Q(certificate_number__icontains=query) |
            Q(equipment__customer_name__icontains=query)
        )

    context = {
        'inspections': inspections,
        'query': query,
    }
    return render(request, 'inspections/inspection_list.html', context)


@login_required
def new_inspection(request):
    """Start a new inspection - select equipment and template"""
    if request.method == 'POST':
        equipment_id = request.POST.get('equipment_id')
        template_id = request.POST.get('template_id')
        reference = request.POST.get('reference', '').strip()
        test_module_ids = request.POST.getlist('test_modules')  # Get selected test modules

        if not equipment_id or not template_id:
            messages.error(request, 'Please select both equipment and template.')
            return redirect('new_inspection')

        try:
            equipment = Equipment.objects.get(id=equipment_id)
            template = Template.objects.get(id=template_id, is_active=True)
        except (Equipment.DoesNotExist, Template.DoesNotExist):
            messages.error(request, 'Invalid equipment or template selected.')
            return redirect('new_inspection')

        # Create inspection
        inspection = Inspection.objects.create(
            equipment=equipment,
            template=template,
            inspector=request.user,
            reference=reference if reference else None,
            status='draft'
        )

        # Add selected test modules
        if test_module_ids:
            for order, test_id in enumerate(test_module_ids):
                try:
                    test_template = Template.objects.get(id=test_id, kind='test', is_active=True)

                    # Validate dielectric test matches equipment category
                    if 'dielectric' in test_template.code.lower():
                        equipment_category = equipment.category.lower() if equipment.category else None

                        # Check if Cat A/B test selected
                        if 'cat-a-b' in test_template.code:
                            if equipment_category not in ['a', 'b']:
                                messages.warning(
                                    request,
                                    f'Skipped "{test_template.name}" - equipment is Category {equipment.get_category_display() if equipment.category else "Unknown"}, not A or B.'
                                )
                                continue

                        # Check if Cat C/D/E test selected
                        elif 'cat-c' in test_template.code or 'cde' in test_template.code:
                            if equipment_category not in ['c', 'd', 'e']:
                                messages.warning(
                                    request,
                                    f'Skipped "{test_template.name}" - equipment is Category {equipment.get_category_display() if equipment.category else "Unknown"}, not C/D/E.'
                                )
                                continue

                    InspectionTestModule.objects.create(
                        inspection=inspection,
                        template=test_template,
                        order=order
                    )
                except Template.DoesNotExist:
                    pass  # Skip invalid test modules

        test_count = inspection.test_modules.count()
        if test_count > 0:
            messages.success(request, f'Inspection #{inspection.id} created with {test_count} test module(s).')
        else:
            messages.success(request, f'Inspection #{inspection.id} created.')

        return redirect('inspection_detail', inspection_id=inspection.id)

    # GET request - show form
    equipment_list = Equipment.objects.all().order_by('serial_number')
    # Split templates into main templates and test modules
    main_templates = Template.objects.filter(is_active=True).exclude(kind='test').order_by('kind', 'name')
    test_templates = Template.objects.filter(is_active=True, kind='test').order_by('name')

    # Pre-select equipment if passed in URL
    selected_equipment_id = request.GET.get('equipment_id')

    # Get selected equipment category for filtering
    selected_equipment = None
    if selected_equipment_id:
        try:
            selected_equipment = Equipment.objects.get(id=selected_equipment_id)
        except Equipment.DoesNotExist:
            pass

    # Default to first periodic template if only one exists
    default_template = None
    if main_templates.count() == 1:
        default_template = main_templates.first()

    context = {
        'equipment_list': equipment_list,
        'main_templates': main_templates,
        'test_templates': test_templates,
        'selected_equipment_id': selected_equipment_id,
        'selected_equipment': selected_equipment,
        'default_template': default_template,
    }
    return render(request, 'inspections/new_inspection.html', context)


@login_required
def create_customer(request):
    """Create new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" created.')
            return redirect('create_equipment')
    else:
        form = CustomerForm()

    context = {'form': form}
    return render(request, 'inspections/create_customer.html', context)


@login_required
def create_equipment(request):
    """Create new equipment"""
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save()
            messages.success(request, f'Equipment {equipment.serial_number} created.')
            # Redirect with equipment pre-selected
            return redirect(f'/inspections/new/?equipment_id={equipment.id}')
    else:
        form = EquipmentForm()

    context = {'form': form}
    return render(request, 'inspections/create_equipment.html', context)


@login_required
def inspection_detail(request, inspection_id):
    """View/edit inspection details"""
    inspection = get_object_or_404(
        Inspection.objects.select_related('template', 'equipment', 'inspector'),
        id=inspection_id
    )

    # Check if user can edit
    can_edit = inspection.is_editable() and inspection.inspector == request.user

    # Get main template sections with questions
    sections = inspection.template.sections.prefetch_related('questions').order_by('order')

    # Group sections by category (parse from title)
    grouped_sections = {}
    for section in sections:
        # Extract category from title (e.g., "Frequent Inspection - Controls" -> "Frequent Inspection")
        if ' - ' in section.title:
            category = section.title.split(' - ')[0]
        else:
            category = 'General'

        if category not in grouped_sections:
            grouped_sections[category] = []
        grouped_sections[category].append(section)

    # Get test module sections
    test_modules = []
    for test_module in inspection.test_modules.select_related('template').prefetch_related('template__sections__questions'):
        test_sections = test_module.template.sections.prefetch_related('questions').order_by('order')

        # Group test module sections by category
        grouped_test_sections = {}
        for section in test_sections:
            if ' - ' in section.title:
                category = section.title.split(' - ')[0]
            else:
                category = 'General'

            if category not in grouped_test_sections:
                grouped_test_sections[category] = []
            grouped_test_sections[category].append(section)

        # Parse template definition to get field definitions
        import json
        field_defs = []
        if hasattr(test_module.template, 'definition') and test_module.template.definition:
            try:
                template_def = json.loads(test_module.template.definition) if isinstance(test_module.template.definition, str) else test_module.template.definition
                field_defs = template_def.get('fields', [])
            except (json.JSONDecodeError, AttributeError):
                pass

        test_modules.append({
            'id': test_module.id,
            'name': test_module.template.name,
            'grouped_sections': grouped_test_sections,
            'field_defs': field_defs,
            'test_data': test_module.test_data or {}
        })

    # Get existing answers
    answers = inspection.answers.all()
    answers_dict = {
        answer.question_id: {
            'status': answer.status,
            'notes': answer.notes,
        }
        for answer in answers
    }

    # Get defects
    defects = inspection.defects.prefetch_related('photos').all()
    defect_question_ids = set(defects.values_list('question_id', flat=True))

    # Calculate stats for each section and category
    def calculate_section_stats(section):
        """Calculate answered/total and defect count for a section"""
        question_ids = list(section.questions.values_list('id', flat=True))
        total = len(question_ids)
        answered = sum(1 for qid in question_ids if qid in answers_dict)
        defect_count = sum(1 for qid in question_ids if qid in defect_question_ids)
        return {'total': total, 'answered': answered, 'defect_count': defect_count}

    # Add stats to each section in grouped_sections
    section_stats = {}
    category_stats = {}
    for category, sections in grouped_sections.items():
        cat_total = 0
        cat_answered = 0
        cat_defects = 0
        for section in sections:
            stats = calculate_section_stats(section)
            section_stats[section.id] = stats
            cat_total += stats['total']
            cat_answered += stats['answered']
            cat_defects += stats['defect_count']
        category_stats[category] = {'total': cat_total, 'answered': cat_answered, 'defect_count': cat_defects}

    # Add stats to test modules
    test_module_stats = {}
    for test_module in test_modules:
        tm_total = 0
        tm_answered = 0
        tm_defects = 0
        for category, sections in test_module['grouped_sections'].items():
            for section in sections:
                stats = calculate_section_stats(section)
                section_stats[section.id] = stats
                tm_total += stats['total']
                tm_answered += stats['answered']
                tm_defects += stats['defect_count']
        test_module_stats[test_module['name']] = {'total': tm_total, 'answered': tm_answered, 'defect_count': tm_defects}

    # Get generated documents
    documents = inspection.documents.all()

    context = {
        'inspection': inspection,
        'can_edit': can_edit,
        'grouped_sections': grouped_sections,
        'test_modules': test_modules,
        'answers_dict': answers_dict,
        'defects': defects,
        'documents': documents,
        'section_stats': section_stats,
        'category_stats': category_stats,
        'test_module_stats': test_module_stats,
    }
    print(f"[DEBUG] Inspection {inspection.id}: can_edit={can_edit}, sections={len(grouped_sections)}, test_modules={len(test_modules)}")
    return render(request, 'inspections/inspection_detail.html', context)


@login_required
def answer_question(request, inspection_id, question_id):
    """Answer a single question (AJAX-style)"""
    if request.method != 'POST':
        return redirect('inspection_detail', inspection_id=inspection_id)

    inspection = get_object_or_404(Inspection, id=inspection_id)

    # Check permissions
    if not inspection.is_editable() or inspection.inspector != request.user:
        messages.error(request, 'Cannot edit this inspection.')
        return redirect('inspection_detail', inspection_id=inspection_id)

    status = request.POST.get('status')
    notes = request.POST.get('notes', '')
    measurement_value = request.POST.get('measurement_value', '').strip()

    if status not in ['pass', 'fail', 'na']:
        messages.error(request, 'Invalid status.')
        return redirect('inspection_detail', inspection_id=inspection_id)

    # Prepare defaults for answer
    answer_defaults = {
        'status': status,
        'notes': notes,
    }

    # Add measurement value if provided
    if measurement_value:
        try:
            answer_defaults['measurement_value'] = float(measurement_value)
        except (ValueError, TypeError):
            answer_defaults['measurement_value'] = None
    else:
        answer_defaults['measurement_value'] = None

    # Update or create answer
    answer, created = InspectionAnswer.objects.update_or_create(
        inspection=inspection,
        question_id=question_id,
        defaults=answer_defaults
    )

    # If status is 'fail', create defect with note and photo (both required)
    if status == 'fail':
        defect_note = request.POST.get('defect_note', '').strip()
        defect_photo = request.FILES.get('defect_photo')

        # Validate defect note
        if not defect_note:
            messages.error(request, 'Defect note is required when marking a question as "Fail".')
            return redirect(f'/inspections/{inspection_id}/#question-{question_id}')

        # Validate defect photo (required)
        if not defect_photo:
            messages.error(request, 'Defect photo is required when marking a question as "Fail".')
            return redirect(f'/inspections/{inspection_id}/#question-{question_id}')

        # Create or update defect for this question
        defect, defect_created = Defect.objects.update_or_create(
            inspection=inspection,
            question_id=question_id,
            defaults={
                'note': defect_note,
            }
        )

        # Save photo
        photo_caption = request.POST.get('photo_caption', '')
        DefectPhoto.objects.create(
            defect=defect,
            image=defect_photo,
            caption=photo_caption
        )

        messages.success(request, 'Answer and defect saved.')
    else:
        # If changing from fail to pass/na, optionally delete the defect
        # (For now, we'll keep defects even if status changes)
        messages.success(request, 'Answer saved.')

    return redirect(f'/inspections/{inspection_id}/#question-{question_id}')


@login_required
def add_defect(request, inspection_id):
    """Add a defect to an inspection"""
    inspection = get_object_or_404(Inspection, id=inspection_id)

    # Check permissions
    if not inspection.is_editable() or inspection.inspector != request.user:
        messages.error(request, 'Cannot edit this inspection.')
        return redirect('inspection_detail', inspection_id=inspection_id)

    if request.method == 'POST':
        form = DefectForm(request.POST)
        if form.is_valid():
            defect = form.save(commit=False)
            defect.inspection = inspection
            defect.save()

            messages.success(request, f'Defect #{defect.id} added. Now add at least one photo.')
            return redirect('add_defect_photo', defect_id=defect.id)
    else:
        question_id = request.GET.get('question_id')
        initial = {}
        if question_id:
            initial['question'] = question_id
        form = DefectForm(initial=initial)

    context = {
        'inspection': inspection,
        'form': form,
    }
    return render(request, 'inspections/add_defect.html', context)


@login_required
def add_defect_photo(request, defect_id):
    """Add photo(s) to a defect"""
    defect = get_object_or_404(Defect.objects.select_related('inspection'), id=defect_id)
    inspection = defect.inspection

    # Check permissions
    if not inspection.is_editable() or inspection.inspector != request.user:
        messages.error(request, 'Cannot edit this inspection.')
        return redirect('inspection_detail', inspection_id=inspection.id)

    if request.method == 'POST':
        form = DefectPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.defect = defect
            photo.save()

            messages.success(request, 'Photo added.')

            # Check if user wants to add more photos
            if request.POST.get('add_another'):
                return redirect('add_defect_photo', defect_id=defect.id)
            else:
                return redirect('inspection_detail', inspection_id=inspection.id)
    else:
        form = DefectPhotoForm()

    existing_photos = defect.photos.all()

    context = {
        'defect': defect,
        'inspection': inspection,
        'form': form,
        'existing_photos': existing_photos,
    }
    return render(request, 'inspections/add_defect_photo.html', context)


@login_required
def complete_inspection(request, inspection_id):
    """Finalize and complete an inspection"""
    inspection = get_object_or_404(Inspection, id=inspection_id)

    # Check permissions
    if inspection.inspector != request.user:
        messages.error(request, 'You do not have permission to complete this inspection.')
        return redirect('inspection_detail', inspection_id=inspection_id)

    if not inspection.can_finalize():
        messages.error(request, 'This inspection cannot be finalized.')
        return redirect('inspection_detail', inspection_id=inspection_id)

    if request.method == 'POST':
        try:
            result = finalize_inspection(inspection.id, request.user.id)
            messages.success(
                request,
                f'Inspection completed successfully. '
                f'Certificate: {result["inspection"].certificate_number}'
            )
            return redirect('inspection_detail', inspection_id=inspection_id)
        except ValidationError as e:
            messages.error(request, f'Cannot finalize inspection: {str(e)}')
            return redirect('inspection_detail', inspection_id=inspection_id)
        except Exception as e:
            messages.error(request, f'Error finalizing inspection: {str(e)}')
            return redirect('inspection_detail', inspection_id=inspection_id)

    # GET request - show confirmation page
    context = {
        'inspection': inspection,
    }
    return render(request, 'inspections/complete_inspection.html', context)


@login_required
def save_test_module_data(request, inspection_id, test_module_id):
    """Save test module metadata (voltage, duration, etc.)"""
    if request.method != 'POST':
        return redirect('inspection_detail', inspection_id=inspection_id)

    inspection = get_object_or_404(Inspection, id=inspection_id)
    test_module = get_object_or_404(InspectionTestModule, id=test_module_id, inspection=inspection)

    # Check permissions
    if not inspection.is_editable() or inspection.inspector != request.user:
        messages.error(request, 'Cannot edit this inspection.')
        return redirect('inspection_detail', inspection_id=inspection_id)

    # Extract all form data and save to test_data JSON field
    test_data = {}
    for key, value in request.POST.items():
        if key not in ['csrfmiddlewaretoken']:
            test_data[key] = value

    test_module.test_data = test_data
    test_module.save()

    messages.success(request, f'Test data saved for {test_module.template.name}')
    return redirect('inspection_detail', inspection_id=inspection_id)


@login_required
def download_document(request, document_id):
    """Download a generated document"""
    document = get_object_or_404(GeneratedDocument, id=document_id)

    # Check permissions (basic check - user should be able to see their own or if staff)
    if not (request.user.is_staff or document.inspection.inspector == request.user):
        raise Http404("Document not found")

    try:
        return FileResponse(
            document.file.open('rb'),
            as_attachment=True,
            filename=document.file.name.split('/')[-1]
        )
    except Exception:
        raise Http404("Document file not found")
