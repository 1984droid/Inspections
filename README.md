# A92.2 Inspection App

Django-based web application for ANSI/SAIA A92.2 (2021) inspections with PostgreSQL backend.

## Features

- **Inspection Types**: Frequent, Periodic, and Test module inspections
- **Question Management**: PASS/FAIL/NA answers with notes
- **Defect Tracking**: Record defects with required notes and photos
- **Automatic Validation**: Ensures all required questions answered and failed items have defects
- **PDF Generation**:
  - Multi-page inspection package with embedded photos
  - High-contrast thermal certificate (single page)
- **Inspection Locking**: Completed inspections are locked to prevent tampering
- **Certificate Numbers**: Auto-generated unique certificate numbers
- **Template Import**: JSON-based template import from existing A92.2 templates

## Tech Stack

- **Backend**: Django 6.0
- **Database**: PostgreSQL 18
- **PDF Generation**: ReportLab
- **Image Handling**: Pillow
- **Templates**: Django Templates (simple, no HTMX/DRF for v1)

## Prerequisites

- Python 3.14+
- PostgreSQL 18+ (or compatible version)
- pip

## Installation

### Quick Setup (Automated)

**Windows:**
```bash
setup.bat
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Cross-platform Python script:**
```bash
python setup.py
```

The setup scripts will:
1. Check Python installation
2. Install dependencies from requirements.txt
3. Create/check .env configuration
4. Create PostgreSQL database (if tools available)
5. Run migrations
6. Create superuser account
7. Import A92.2 templates
8. Create media directories

---

### Manual Setup (Step-by-Step)

If you prefer manual setup or the automated scripts don't work:

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 2. Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```
DATABASE_NAME=inspection_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432
COMPANY_NAME=Your Company Name
```

#### 3. Create Database

Create the PostgreSQL database:

```bash
# Using psql
createdb inspection_db

# Or in PostgreSQL shell:
CREATE DATABASE inspection_db;
```

#### 4. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 5. Create Superuser

```bash
python manage.py createsuperuser
```

#### 6. Import Templates

Import the A92.2 templates from JSON files:

```bash
python manage.py import_a92_templates
```

This will import:
- Frequent inspection template
- Periodic inspection template
- Test module templates (5 types)

#### 7. Run Development Server

```bash
python manage.py runserver
```

Access the application at: `http://localhost:8000`

## Usage

### Login

Navigate to `http://localhost:8000/login/` and log in with your superuser credentials.

### Create Equipment

1. Click "New Inspection"
2. Click "Create New Equipment"
3. Fill in equipment details (serial number is required)

### Start Inspection

1. Click "New Inspection"
2. Select equipment from dropdown
3. Select template type (Frequent/Periodic/Test)
4. Click "Start Inspection"

### Answer Questions

1. For each question, select PASS/FAIL/N/A
2. Add optional notes
3. Click "Save Answer"
4. For FAIL answers, click "Add Defect for This"

### Record Defects

1. When adding a defect:
   - Enter defect note (required)
   - Upload at least one photo (required)
   - Add caption (optional)
2. Can add multiple photos per defect

### Complete Inspection

1. Click "Complete Inspection" button
2. System validates:
   - All required questions answered
   - All failed items have defects with notes and photos
3. On success:
   - Overall result computed (PASS/FAIL)
   - Certificate number generated
   - PDF documents generated
   - Inspection locked

### Download Documents

After completion:
- Download "Package PDF" (full inspection report)
- Download "Certificate PDF" (thermal certificate)

## Project Structure

```
InspectionApp/
├── config/                  # Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── inspections/            # Main app
│   ├── management/
│   │   └── commands/
│   │       └── import_a92_templates.py
│   ├── services/
│   │   ├── finalize.py
│   │   ├── pdf_package.py
│   │   └── pdf_certificate.py
│   ├── templates/
│   │   └── inspections/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   └── urls.py
├── media/                  # User uploads (photos, PDFs)
├── staticfiles/            # Static files (after collectstatic)
├── insp.a92_2_2021.*.json # Template JSON files
├── requirements.txt
├── .env
└── manage.py
```

## Database Models

- **Equipment**: MEWP units being inspected
- **Template**: Inspection template definitions (frequent/periodic/test)
- **SectionTemplate**: Sections within templates
- **QuestionTemplate**: Questions within sections
- **Inspection**: Individual inspection instances
- **InspectionAnswer**: Answers to questions (PASS/FAIL/NA)
- **Defect**: Defects found during inspection
- **DefectPhoto**: Photo evidence for defects
- **GeneratedDocument**: PDF documents (package/certificate)

## Business Rules

### Completion Requirements

An inspection can be marked "Completed" only if:

1. All required questions have answers (PASS/FAIL/NA)
2. If any answer is FAIL:
   - At least one Defect must exist
   - Each Defect must have a note
   - Each Defect must have ≥1 photo

### Locking

After completion and PDF generation:
- Inspection status changes to LOCKED
- Answers/defects cannot be edited
- (Admin unlock feature is optional for v1)

## Admin Interface

Access Django admin at `http://localhost:8000/admin/`

Available models:
- Equipment management
- Template management (view imported templates)
- Inspection monitoring
- Defect tracking

## API Endpoints (Views)

- `/` - Dashboard
- `/login/` - Login page
- `/inspections/` - Inspection list/search
- `/inspections/new/` - Create new inspection
- `/inspections/<id>/` - Inspection detail (answer questions)
- `/inspections/<id>/complete/` - Complete inspection
- `/inspections/<id>/defect/add/` - Add defect
- `/defects/<id>/photo/add/` - Add defect photo
- `/equipment/new/` - Create equipment
- `/documents/<id>/download/` - Download PDF

## Development Notes

### PDF Generation

- Uses ReportLab for PDF creation
- Package PDF: Multi-page with cover, details, defects, photos
- Certificate PDF: Single page, high-contrast black/white
- PDFs stored in `media/generated_docs/`

### Template Import

The importer reads JSON files and:
- Creates Template records
- Creates SectionTemplate records (ordered)
- Creates QuestionTemplate records
- Simplifies complex JSON (ignores advanced fields)

### File Storage

- Defect photos: `media/defect_photos/YYYY/MM/DD/`
- Generated PDFs: `media/generated_docs/YYYY/MM/DD/`

## Troubleshooting

### Database Connection Error

Ensure PostgreSQL is running and credentials in `.env` are correct.

### Template Import Issues

Check that JSON files are in the project root directory.

### PDF Generation Errors

Ensure Pillow is installed for image handling:
```bash
pip install Pillow
```

### Media Files Not Loading

In production, configure proper media file serving (nginx/Apache).

## Production Deployment

For production:

1. Set `DEBUG=False` in `.env`
2. Set strong `SECRET_KEY`
3. Configure `ALLOWED_HOSTS` in `settings.py`
4. Use gunicorn/uWSGI
5. Configure nginx/Apache for static/media files
6. Set up proper PostgreSQL security
7. Enable HTTPS
8. Set up backup procedures for database and media files

## License

Proprietary - All rights reserved

## Support

Contact: [Your support email/info]
