from django.contrib import admin
from .models import (
    Customer, Equipment, Template, SectionTemplate, QuestionTemplate,
    Inspection, InspectionAnswer, Defect, DefectPhoto, GeneratedDocument,
    InspectionTestModule
)


class SectionTemplateInline(admin.TabularInline):
    model = SectionTemplate
    extra = 0


class QuestionTemplateInline(admin.TabularInline):
    model = QuestionTemplate
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email')
    search_fields = ('name', 'phone', 'email')


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'make', 'model', 'customer', 'location')
    search_fields = ('serial_number', 'make', 'model', 'customer__name')
    list_filter = ('make', 'model', 'customer')


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'kind', 'version', 'is_active')
    list_filter = ('kind', 'is_active')
    search_fields = ('code', 'name')
    inlines = [SectionTemplateInline]


@admin.register(SectionTemplate)
class SectionTemplateAdmin(admin.ModelAdmin):
    list_display = ('template', 'order', 'section_id', 'title')
    list_filter = ('template',)
    search_fields = ('section_id', 'title')
    inlines = [QuestionTemplateInline]


@admin.register(QuestionTemplate)
class QuestionTemplateAdmin(admin.ModelAdmin):
    list_display = ('section', 'order', 'code', 'prompt_preview', 'required')
    list_filter = ('required', 'section__template')
    search_fields = ('code', 'prompt')

    def prompt_preview(self, obj):
        return obj.prompt[:100] + '...' if len(obj.prompt) > 100 else obj.prompt
    prompt_preview.short_description = 'Prompt'


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'equipment', 'template', 'inspector', 'status', 'overall_result', 'started_at')
    list_filter = ('status', 'overall_result', 'template__kind')
    search_fields = ('equipment__serial_number', 'certificate_number', 'inspector__username')
    readonly_fields = ('certificate_number', 'started_at', 'completed_at', 'locked_at')


@admin.register(InspectionAnswer)
class InspectionAnswerAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'question', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('inspection__id', 'notes')


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ('id', 'inspection', 'question', 'note_preview', 'created_at')
    search_fields = ('note', 'inspection__id')

    def note_preview(self, obj):
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    note_preview.short_description = 'Note'


@admin.register(DefectPhoto)
class DefectPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'defect', 'image', 'caption', 'created_at')
    search_fields = ('caption', 'defect__id')


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'doc_type', 'generator_version', 'created_at')
    list_filter = ('doc_type',)
    search_fields = ('inspection__id',)


@admin.register(InspectionTestModule)
class InspectionTestModuleAdmin(admin.ModelAdmin):
    list_display = ('inspection', 'template', 'order', 'created_at')
    list_filter = ('template',)
    search_fields = ('inspection__id', 'template__name')
