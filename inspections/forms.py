from django import forms
from .models import Equipment, Customer, InspectionAnswer, Defect, DefectPhoto


class CustomerForm(forms.ModelForm):
    """Form for creating/editing customers"""
    class Meta:
        model = Customer
        fields = ['name', 'address', 'phone', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Customer Name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Street, City, State, ZIP'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(555) 555-5555'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'customer@example.com'}),
        }


class EquipmentForm(forms.ModelForm):
    """Form for creating/editing equipment"""
    class Meta:
        model = Equipment
        fields = [
            # Basic Equipment Info
            'serial_number', 'asset_tag', 'make', 'model', 'year_of_manufacture',
            # ANSI A92.2 Identification Plate
            'insulation_type', 'rated_platform_height', 'category',
            'configured_for_electrical_work', 'chassis_insulating_system',
            # Load Capacity
            'platform_count', 'capacity_per_platform', 'capacity_total',
            # Test & Qualification
            'last_qualification_test_date', 'qualification_voltage',
            # Upper Controls & Attachments
            'upper_controls_high_resistance', 'material_handling_attachment',
            # System Specs
            'system_pressure', 'control_system_voltage', 'ambient_temp_range',
            # Manufacturer Info
            'manufacturer_name', 'manufacturer_city', 'manufacturer_state', 'manufacturer_country', 'installed_by',
            # Vehicle Info
            'vehicle_year', 'vehicle_make', 'vehicle_model', 'vehicle_vin', 'vehicle_license_plate',
            # Customer & Location
            'customer', 'location'
        ]
        widgets = {
            # Basic Equipment Info
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Equipment Serial Number'}),
            'asset_tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asset Tag (optional)'}),
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Aerial Device Manufacturer'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Model Number'}),
            'year_of_manufacture': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
            # ANSI A92.2 Identification Plate
            'insulation_type': forms.Select(attrs={'class': 'form-control'}),
            'rated_platform_height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Feet', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'configured_for_electrical_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'chassis_insulating_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # Load Capacity
            'platform_count': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of platforms/buckets', 'min': '1'}),
            'capacity_per_platform': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'lbs per platform', 'step': '0.01'}),
            'capacity_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total capacity (lbs)', 'step': '0.01'}),
            # Test & Qualification
            'last_qualification_test_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'qualification_voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kV', 'step': '0.01'}),
            # Upper Controls & Attachments
            'upper_controls_high_resistance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'material_handling_attachment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            # System Specs
            'system_pressure': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'PSI', 'step': '0.01'}),
            'control_system_voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Volts', 'step': '0.1'}),
            'ambient_temp_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., -20°F to 120°F'}),
            # Manufacturer Info
            'manufacturer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manufacturer Name'}),
            'manufacturer_city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'manufacturer_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State/Province'}),
            'manufacturer_country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Country'}),
            'installed_by': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Installed by'}),
            # Vehicle Info
            'vehicle_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
            'vehicle_make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ford, Chevy, etc.'}),
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'F-550, etc.'}),
            'vehicle_vin': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '17-character VIN'}),
            'vehicle_license_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'License Plate'}),
            # Customer & Location
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job Site / Location'}),
        }


class InspectionAnswerForm(forms.ModelForm):
    """Form for answering inspection questions"""
    class Meta:
        model = InspectionAnswer
        fields = ['status', 'notes']
        widgets = {
            'status': forms.RadioSelect(choices=InspectionAnswer.STATUS_CHOICES),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DefectForm(forms.ModelForm):
    """Form for recording defects"""
    class Meta:
        model = Defect
        fields = ['note', 'question']
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True}),
            'question': forms.HiddenInput(),
        }


class DefectPhotoForm(forms.ModelForm):
    """Form for uploading defect photos"""
    class Meta:
        model = DefectPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
            'caption': forms.TextInput(attrs={'class': 'form-control'}),
        }
