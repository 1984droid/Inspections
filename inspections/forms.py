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
            # Equipment Info
            'serial_number', 'asset_tag', 'make', 'model',
            # Vehicle Info
            'vehicle_year', 'vehicle_make', 'vehicle_model', 'vehicle_vin', 'vehicle_license_plate',
            # Customer & Location
            'customer', 'location'
        ]
        widgets = {
            # Equipment Info
            'serial_number': forms.TextInput(attrs={'class': 'form-control', 'required': True, 'placeholder': 'Equipment Serial Number'}),
            'asset_tag': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asset Tag (optional)'}),
            'make': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment Manufacturer'}),
            'model': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Equipment Model'}),
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
