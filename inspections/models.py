from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid


class Customer(models.Model):
    """Customer/client information"""
    name = models.CharField(max_length=200, unique=True, db_index=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Equipment being inspected (MEWP units)"""
    # Basic Equipment Info
    serial_number = models.CharField(max_length=100, unique=True, db_index=True)
    asset_tag = models.CharField(max_length=100, blank=True, null=True)
    make = models.CharField(max_length=100, blank=True, null=True, help_text="Make of aerial device")
    model = models.CharField(max_length=100, blank=True, null=True, help_text="Model of aerial device")

    # ANSI A92.2 Identification Plate Data (Figure 7)
    year_of_manufacture = models.CharField(max_length=4, blank=True, null=True)

    # Insulation Classification
    INSULATION_CHOICES = [
        ('insulating', 'Insulating'),
        ('non-insulating', 'Non-Insulating'),
    ]
    insulation_type = models.CharField(max_length=20, choices=INSULATION_CHOICES, blank=True, null=True)

    # Platform & Capacity
    rated_platform_height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Feet")

    CATEGORY_CHOICES = [
        ('a', 'Category A'),
        ('b', 'Category B'),
        ('c', 'Category C'),
        ('d', 'Category D'),
        ('e', 'Category E'),
    ]
    category = models.CharField(max_length=1, choices=CATEGORY_CHOICES, blank=True, null=True)

    configured_for_electrical_work = models.BooleanField(default=False, help_text="Configured for electrical work rubber gloving")
    chassis_insulating_system = models.BooleanField(default=False)

    # Load Capacity
    platform_count = models.PositiveIntegerField(default=1, help_text="Number of platforms/buckets")
    capacity_per_platform = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, help_text="lbs per bucket/platform")
    capacity_total = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True, help_text="lbs total (both buckets/platforms)")

    # Test & Qualification
    last_qualification_test_date = models.DateField(blank=True, null=True)
    qualification_voltage = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="kV")

    # Upper Controls & Attachments
    upper_controls_high_resistance = models.BooleanField(default=False, help_text="Upper controls with high electrical resistance")
    material_handling_attachment = models.BooleanField(default=False)

    # System Specs
    system_pressure = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="PSI")
    control_system_voltage = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Volts")
    ambient_temp_range = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., -20°F to 120°F")

    # Manufacturer Info
    manufacturer_name = models.CharField(max_length=200, blank=True, null=True)
    manufacturer_city = models.CharField(max_length=100, blank=True, null=True)
    manufacturer_state = models.CharField(max_length=100, blank=True, null=True)
    manufacturer_country = models.CharField(max_length=100, blank=True, null=True)
    installed_by = models.CharField(max_length=200, blank=True, null=True)

    # Vehicle Info
    vehicle_year = models.CharField(max_length=4, blank=True, null=True)
    vehicle_make = models.CharField(max_length=100, blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True, null=True)
    vehicle_vin = models.CharField(max_length=17, blank=True, null=True)
    vehicle_license_plate = models.CharField(max_length=20, blank=True, null=True)

    # Customer relationship
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='equipment', null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Job site or specific location")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['serial_number']
        verbose_name_plural = 'Equipment'

    def __str__(self):
        return f"{self.serial_number} ({self.make} {self.model})".strip()


class Template(models.Model):
    """Inspection template (frequent, periodic, or test)"""
    KIND_CHOICES = [
        ('frequent', 'Frequent'),
        ('periodic', 'Periodic'),
        ('test', 'Test'),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['kind', 'code']

    def __str__(self):
        return f"{self.name} (v{self.version})"


class SectionTemplate(models.Model):
    """Section within a template"""
    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name='sections')
    order = models.IntegerField(default=0)
    section_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)

    class Meta:
        ordering = ['template', 'order']
        unique_together = [['template', 'section_id']]

    def __str__(self):
        return f"{self.template.code} - {self.title}"


class QuestionTemplate(models.Model):
    """Question within a section"""
    section = models.ForeignKey(SectionTemplate, on_delete=models.CASCADE, related_name='questions')
    order = models.IntegerField(default=0)
    code = models.CharField(max_length=100, blank=True, null=True)
    prompt = models.TextField()
    required = models.BooleanField(default=True)

    class Meta:
        ordering = ['section', 'order']

    def __str__(self):
        return f"{self.section.section_id} - Q{self.order}"


class Inspection(models.Model):
    """An inspection instance"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('locked', 'Locked'),
    ]

    RESULT_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ]

    template = models.ForeignKey(Template, on_delete=models.PROTECT, related_name='inspections')
    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name='inspections')
    inspector = models.ForeignKey(User, on_delete=models.PROTECT, related_name='inspections')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    overall_result = models.CharField(max_length=10, choices=RESULT_CHOICES, null=True, blank=True)

    certificate_number = models.CharField(max_length=100, unique=True, null=True, blank=True, db_index=True)
    reference = models.CharField(max_length=200, blank=True, null=True, help_text="Inspector reference or job number")

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.template.kind.title()} - {self.equipment.serial_number} - {self.started_at.strftime('%Y-%m-%d')}"

    def is_editable(self):
        """Check if inspection can be edited"""
        return self.status == 'draft'

    def can_finalize(self):
        """Check if inspection can be finalized"""
        return self.status == 'draft'


class InspectionTestModule(models.Model):
    """Test modules added to an inspection (e.g., dielectric tests)"""
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='test_modules')
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    order = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        unique_together = [['inspection', 'template']]

    def __str__(self):
        return f"{self.inspection} - {self.template.name}"


class InspectionAnswer(models.Model):
    """Answer to a question in an inspection"""
    STATUS_CHOICES = [
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'N/A'),
    ]

    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(QuestionTemplate, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['inspection', 'question']]
        ordering = ['question__section__order', 'question__order']

    def __str__(self):
        return f"{self.inspection.id} - Q{self.question.id}: {self.status}"


class Defect(models.Model):
    """Defect found during inspection"""
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='defects')
    question = models.ForeignKey(QuestionTemplate, on_delete=models.PROTECT, null=True, blank=True)
    note = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Defect #{self.id} - {self.inspection}"

    def clean(self):
        if not self.note or not self.note.strip():
            raise ValidationError({'note': 'Defect note is required.'})


class DefectPhoto(models.Model):
    """Photo evidence for a defect"""
    defect = models.ForeignKey(Defect, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='defect_photos/%Y/%m/%d/')
    caption = models.CharField(max_length=200, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Photo for Defect #{self.defect.id}"


class GeneratedDocument(models.Model):
    """Generated PDF documents for inspections"""
    DOC_TYPE_CHOICES = [
        ('package', 'Package'),
        ('certificate', 'Certificate'),
    ]

    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    file = models.FileField(upload_to='generated_docs/%Y/%m/%d/')
    generator_version = models.CharField(max_length=50, default='1.0.0')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['inspection', 'doc_type', 'generator_version']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.doc_type.title()} - {self.inspection}"
