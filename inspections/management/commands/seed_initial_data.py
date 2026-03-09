import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inspections.models import CompanyInfo, InspectorProfile, Customer, Equipment


class Command(BaseCommand):
    help = 'Seed initial company info, inspectors, and customers from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='seed_data.json',
            help='Path to seed data JSON file (default: seed_data.json)',
        )
        parser.add_argument(
            '--force-passwords',
            action='store_true',
            help='Force update passwords for existing users',
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])

        if not file_path.exists():
            self.stdout.write(self.style.WARNING(f'Seed file not found: {file_path}'))
            self.stdout.write(self.style.WARNING('Creating template file...'))
            self.create_template_file(file_path)
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Seed company info
            if 'company' in data:
                self.seed_company(data['company'])

            # Seed inspectors
            if 'inspectors' in data:
                self.seed_inspectors(data['inspectors'], options.get('force_passwords', False))

            # Seed customers
            if 'customers' in data:
                self.seed_customers(data['customers'])

            # Seed equipment
            if 'equipment' in data:
                self.seed_equipment(data['equipment'])

            self.stdout.write(self.style.SUCCESS('Successfully seeded initial data!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding data: {str(e)}'))
            if options.get('verbosity', 1) > 1:
                import traceback
                traceback.print_exc()

    def seed_company(self, company_data):
        """Seed or update company information"""
        company, created = CompanyInfo.objects.update_or_create(
            name=company_data['name'],
            defaults={
                'address_line1': company_data.get('address_line1', ''),
                'address_line2': company_data.get('address_line2', ''),
                'city': company_data.get('city', ''),
                'state': company_data.get('state', ''),
                'zip_code': company_data.get('zip_code', ''),
                'country': company_data.get('country', 'USA'),
                'phone': company_data.get('phone', ''),
                'email': company_data.get('email', ''),
                'website': company_data.get('website', ''),
                'license_number': company_data.get('license_number', ''),
                'certifications': company_data.get('certifications', ''),
            }
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} company: {company.name}'))

    def seed_inspectors(self, inspectors_data, force_passwords=False):
        """Seed or update inspector profiles and create users if needed"""
        for inspector_data in inspectors_data:
            username = inspector_data['username']

            # Get or create user
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': inspector_data.get('first_name', ''),
                    'last_name': inspector_data.get('last_name', ''),
                    'email': inspector_data.get('email', ''),
                    'is_staff': inspector_data.get('is_staff', True),
                    'is_active': True,
                }
            )

            # Set password if user was just created OR if force_passwords is enabled
            if 'password' in inspector_data:
                if user_created:
                    user.set_password(inspector_data['password'])
                    self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
                elif force_passwords:
                    user.set_password(inspector_data['password'])
                    self.stdout.write(self.style.SUCCESS(f'Updated password for user: {username}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Updated user: {username}'))

            # Always update user info (name, email) if not just created
            if not user_created:
                if 'first_name' in inspector_data:
                    user.first_name = inspector_data['first_name']
                if 'last_name' in inspector_data:
                    user.last_name = inspector_data['last_name']
                if 'email' in inspector_data:
                    user.email = inspector_data['email']
                user.save()

            # Create or update inspector profile
            profile, created = InspectorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': inspector_data.get('phone', ''),
                    'email': inspector_data.get('inspector_email', ''),
                    'certification_number': inspector_data.get('certification_number', ''),
                    'certifications': inspector_data.get('certifications', ''),
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} inspector profile: {user.get_full_name() or username}'))

    def seed_customers(self, customers_data):
        """Seed or update customers"""
        for customer_data in customers_data:
            customer, created = Customer.objects.update_or_create(
                name=customer_data['name'],
                defaults={
                    'location': customer_data.get('location', ''),
                    'asset_id': customer_data.get('asset_id', ''),
                    'address_line1': customer_data.get('address_line1', ''),
                    'address_line2': customer_data.get('address_line2', ''),
                    'city': customer_data.get('city', ''),
                    'state': customer_data.get('state', ''),
                    'zip_code': customer_data.get('zip_code', ''),
                    'country': customer_data.get('country', 'USA'),
                    'phone': customer_data.get('phone', ''),
                    'phone_secondary': customer_data.get('phone_secondary', ''),
                    'email': customer_data.get('email', ''),
                    'email_secondary': customer_data.get('email_secondary', ''),
                    'website': customer_data.get('website', ''),
                    'contact_person_name': customer_data.get('contact_person_name', ''),
                    'contact_person_title': customer_data.get('contact_person_title', ''),
                    'contact_person_phone': customer_data.get('contact_person_phone', ''),
                    'contact_person_email': customer_data.get('contact_person_email', ''),
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} customer: {customer.name}'))

    def seed_equipment(self, equipment_data):
        """Seed or update equipment"""
        for equip_data in equipment_data:
            # Find customer by name
            customer_name = equip_data.get('customer_name')
            if not customer_name:
                self.stdout.write(self.style.WARNING(f'Skipping equipment without customer_name'))
                continue

            try:
                customer = Customer.objects.get(name=customer_name)
            except Customer.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Customer not found: {customer_name}'))
                continue

            # Create or update equipment by serial number
            equipment, created = Equipment.objects.update_or_create(
                serial_number=equip_data['serial_number'],
                defaults={
                    'customer': customer,
                    'make': equip_data.get('make', ''),
                    'model': equip_data.get('model', ''),
                    'unit_number': equip_data.get('unit_number', ''),
                    'max_working_height': equip_data.get('max_working_height'),
                    'year_of_manufacture': equip_data.get('year_of_manufacture'),
                    'vehicle_make': equip_data.get('vehicle_make', ''),
                    'vehicle_model': equip_data.get('vehicle_model', ''),
                    'vehicle_unit_number': equip_data.get('vehicle_unit_number', ''),
                    'vehicle_vin': equip_data.get('vehicle_vin', ''),
                    'vehicle_year': equip_data.get('vehicle_year'),
                    'vehicle_license_plate': equip_data.get('vehicle_license_plate', ''),
                    'insulation_type': equip_data.get('insulation_type', ''),
                    'category': equip_data.get('category', ''),
                    'upper_controls_high_resistance': equip_data.get('upper_controls_high_resistance', False),
                }
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} equipment: {equipment.serial_number}'))

    def create_template_file(self, file_path):
        """Create a template seed_data.json file"""
        template = {
            "company": {
                "name": "Your Company Name LLC",
                "address_line1": "123 Business Street",
                "address_line2": "Suite 100",
                "city": "Seattle",
                "state": "WA",
                "zip_code": "98101",
                "country": "USA",
                "phone": "(206) 555-1234",
                "email": "info@yourcompany.com",
                "website": "https://www.yourcompany.com",
                "license_number": "WA-INSP-2024-001",
                "certifications": "ANSI A92.2 Certified, OSHA 1910.67 Compliant"
            },
            "inspectors": [
                {
                    "username": "josh",
                    "password": "changeme123!",
                    "first_name": "Josh",
                    "last_name": "Inspector",
                    "email": "josh@yourcompany.com",
                    "is_staff": True,
                    "phone": "(206) 555-5678",
                    "inspector_email": "josh.inspector@yourcompany.com",
                    "certification_number": "ANSI-2024-JI-001",
                    "certifications": "ANSI A92.2 Level II Inspector, OSHA 30-Hour"
                }
            ],
            "customers": [
                {
                    "name": "ABC Utilities Company",
                    "location": "North Yard - Spokane",
                    "asset_id": "ABC-FLEET-001",
                    "address_line1": "456 Fleet Street",
                    "address_line2": "",
                    "city": "Spokane",
                    "state": "WA",
                    "zip_code": "99201",
                    "country": "USA",
                    "phone": "(509) 555-9876",
                    "phone_secondary": "(509) 555-9877",
                    "email": "fleet@abcutilities.com",
                    "email_secondary": "",
                    "website": "https://www.abcutilities.com",
                    "contact_person_name": "Bob Johnson",
                    "contact_person_title": "Fleet Manager",
                    "contact_person_phone": "(509) 555-9878",
                    "contact_person_email": "bjohnson@abcutilities.com"
                }
            ]
        }

        with open(file_path, 'w') as f:
            json.dump(template, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Created template file: {file_path}'))
        self.stdout.write(self.style.WARNING('Please edit this file with your actual data, then run the command again.'))
