from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid


class CompanyInfo(models.Model):
    """Company information for the inspection service provider"""
    name = models.CharField(max_length=200, help_text="Company Name")

    # Address
    address_line1 = models.CharField(max_length=200, blank=True, null=True, help_text="Street Address")
    address_line2 = models.CharField(max_length=200, blank=True, null=True, help_text="Suite, Unit, etc.")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default="USA")

    # Contact
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    # Certifications & License
    license_number = models.CharField(max_length=100, blank=True, null=True, help_text="Business License Number")
    certifications = models.TextField(blank=True, null=True, help_text="Certifications (e.g., ANSI, OSHA)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company Information"
        verbose_name_plural = "Company Information"

    def __str__(self):
        return self.name

    def get_full_address(self):
        """Returns formatted full address"""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)

        city_state_zip = []
        if self.city:
            city_state_zip.append(self.city)
        if self.state:
            city_state_zip.append(self.state)
        if self.zip_code:
            city_state_zip.append(self.zip_code)

        if city_state_zip:
            parts.append(', '.join(city_state_zip[:2]) + (' ' + city_state_zip[2] if len(city_state_zip) > 2 else ''))

        if self.country and self.country != "USA":
            parts.append(self.country)

        return '\n'.join(parts) if parts else 'N/A'


class InspectorProfile(models.Model):
    """Extended profile for inspectors (users)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='inspector_profile')

    # Contact Information
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Inspector Phone Number")
    email = models.EmailField(blank=True, null=True, help_text="Inspector Email (if different from user email)")

    # Certifications
    certification_number = models.CharField(max_length=100, blank=True, null=True, help_text="Inspector Certification Number")
    certifications = models.TextField(blank=True, null=True, help_text="Inspector Certifications")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - Inspector Profile"

    def get_email(self):
        """Returns inspector email, falling back to user email"""
        return self.email or self.user.email


class Customer(models.Model):
    """Customer/client information"""
    name = models.CharField(max_length=200, unique=True, db_index=True)
    location = models.CharField(max_length=200, blank=True, null=True, help_text="Location/Yard (e.g., North Yard - Spokane)")

    # Address Information
    address_line1 = models.CharField(max_length=200, blank=True, null=True, help_text="Street Address")
    address_line2 = models.CharField(max_length=200, blank=True, null=True, help_text="Suite, Unit, Building, Floor, etc.")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default="USA")

    # Legacy address field (for backward compatibility)
    address = models.TextField(blank=True, null=True, help_text="Full address (legacy field)")

    # Contact Information
    asset_id = models.CharField(max_length=100, blank=True, null=True, help_text="Customer Asset ID")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Primary Phone Number")
    phone_secondary = models.CharField(max_length=20, blank=True, null=True, help_text="Secondary Phone Number")
    email = models.EmailField(blank=True, null=True, help_text="Primary Email")
    email_secondary = models.EmailField(blank=True, null=True, help_text="Secondary Email")
    website = models.URLField(blank=True, null=True, help_text="Company Website")

    # Contact Person
    contact_person_name = models.CharField(max_length=200, blank=True, null=True, help_text="Primary Contact Name")
    contact_person_title = models.CharField(max_length=100, blank=True, null=True, help_text="Primary Contact Title")
    contact_person_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Primary Contact Phone")
    contact_person_email = models.EmailField(blank=True, null=True, help_text="Primary Contact Email")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_full_address(self):
        """Returns formatted full address"""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)

        city_state_zip = []
        if self.city:
            city_state_zip.append(self.city)
        if self.state:
            city_state_zip.append(self.state)
        if self.zip_code:
            city_state_zip.append(self.zip_code)

        if city_state_zip:
            parts.append(', '.join(city_state_zip[:2]) + (' ' + city_state_zip[2] if len(city_state_zip) > 2 else ''))

        if self.country and self.country != "USA":
            parts.append(self.country)

        return '\n'.join(parts) if parts else (self.address or 'N/A')


class Equipment(models.Model):
    """Equipment being inspected (MEWP units)"""
    # Basic Equipment Info
    serial_number = models.CharField(max_length=100, unique=True, db_index=True, help_text="Aerial Device Serial Number")
    asset_tag = models.CharField(max_length=100, blank=True, null=True)
    unit_number = models.CharField(max_length=100, blank=True, null=True, help_text="Aerial Device Unit Number")
    make = models.CharField(max_length=100, blank=True, null=True, help_text="Aerial Device Manufacturer")
    model = models.CharField(max_length=100, blank=True, null=True, help_text="Aerial Device Model")
    max_working_height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Maximum Working Height (ft)")

    # ANSI A92.2 Identification Plate Data (Figure 7)
    year_of_manufacture = models.CharField(max_length=4, blank=True, null=True)

    # Insulation Classification
    INSULATION_CHOICES = [
        ('insulating', 'Insulating'),
        ('non-insulating', 'Non-Insulating'),
    ]
    insulation_type = models.CharField(max_length=20, choices=INSULATION_CHOICES, blank=True, null=True)

    # Platform & Capacity
    rated_platform_height = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    CATEGORY_CHOICES = [
        ('a', 'Category A'),
        ('b', 'Category B'),
        ('c', 'Category C'),
        ('d', 'Category D'),
        ('e', 'Category E'),
    ]
    category = models.CharField(max_length=1, choices=CATEGORY_CHOICES, blank=True, null=True)

    configured_for_electrical_work = models.BooleanField(default=False)
    chassis_insulating_system = models.BooleanField(default=False)

    # Load Capacity
    platform_count = models.PositiveIntegerField(default=1)
    capacity_per_platform = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    capacity_total = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)

    # Test & Qualification
    last_qualification_test_date = models.DateField(blank=True, null=True)
    qualification_voltage = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)

    # Upper Controls & Attachments
    upper_controls_high_resistance = models.BooleanField(default=False)
    material_handling_attachment = models.BooleanField(default=False)

    # System Specs
    system_pressure = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    control_system_voltage = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    ambient_temp_range = models.CharField(max_length=50, blank=True, null=True)

    # Manufacturer Info
    manufacturer_name = models.CharField(max_length=200, blank=True, null=True)
    manufacturer_city = models.CharField(max_length=100, blank=True, null=True)
    manufacturer_state = models.CharField(max_length=100, blank=True, null=True)
    manufacturer_country = models.CharField(max_length=100, blank=True, null=True)
    installed_by = models.CharField(max_length=200, blank=True, null=True)

    # Vehicle/Truck Info (Chassis)
    vehicle_year = models.CharField(max_length=4, blank=True, null=True, help_text="Truck Year")
    vehicle_make = models.CharField(max_length=100, blank=True, null=True, help_text="Truck Make")
    vehicle_model = models.CharField(max_length=100, blank=True, null=True, help_text="Truck Model")
    vehicle_vin = models.CharField(max_length=17, blank=True, null=True, help_text="Truck VIN")
    vehicle_unit_number = models.CharField(max_length=100, blank=True, null=True, help_text="Truck Unit Number")
    vehicle_license_plate = models.CharField(max_length=20, blank=True, null=True, help_text="License Plate")

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
    definition = models.JSONField(null=True, blank=True, help_text="Full JSON template definition including fields, rules, etc.")
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
    ansi_reference = models.CharField(max_length=50, blank=True, null=True, help_text="ANSI section reference (e.g., 5.2)")
    display_group = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Display grouping for PDF reports (e.g., 'Setup', 'Test Execution'). Multiple sections can share the same display_group to appear under one heading."
    )

    class Meta:
        ordering = ['template', 'order']
        unique_together = [['template', 'section_id']]

    def __str__(self):
        return f"{self.template.code} - {self.title}"

    def get_display_group(self):
        """Returns display_group if set, otherwise falls back to title"""
        return self.display_group or self.title


class QuestionTemplate(models.Model):
    """Question within a section"""
    QUESTION_TYPE_CHOICES = [
        ('pass_fail', 'Pass/Fail'),
        ('measurement', 'Measurement'),
    ]

    section = models.ForeignKey(SectionTemplate, on_delete=models.CASCADE, related_name='questions')
    order = models.IntegerField(default=0)
    code = models.CharField(max_length=100, blank=True, null=True)
    prompt = models.TextField()
    required = models.BooleanField(default=True)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='pass_fail')
    measurement_unit = models.CharField(max_length=20, blank=True, null=True, help_text="Unit for measurement (e.g., kV, mA, lbs)")
    ansi_reference = models.CharField(max_length=50, blank=True, null=True, help_text="ANSI section reference (e.g., 5.2.1.a)")

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
    test_data = models.JSONField(default=dict, blank=True, help_text="Stores test-specific data like voltage, duration, etc.")

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

    # For measurement-type questions
    measurement_value = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text="Measured value")

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
