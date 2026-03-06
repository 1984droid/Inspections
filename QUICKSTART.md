# Quick Start Guide

## Prerequisites

1. **Python 3.14+** installed
2. **PostgreSQL 18+** installed and running
3. All JSON template files in project root

## Automated Setup (Recommended)

### Windows
```bash
setup.bat
```

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

### Cross-platform (Python)
```bash
python setup.py
```

The script will guide you through:
- Installing dependencies
- Configuring .env
- Creating database
- Running migrations
- Creating admin user
- Importing templates

## After Setup

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Open browser:**
   ```
   http://localhost:8000
   ```

3. **Login** with your superuser credentials

## First Inspection

1. Click **"New Inspection"**
2. Click **"Create New Equipment"** (first time only)
   - Enter serial number (required)
   - Fill in other details (optional)
3. Select **equipment** from dropdown
4. Select **template type** (Frequent/Periodic/Test)
5. Click **"Start Inspection"**

## Answering Questions

For each question:
1. Select **PASS**, **FAIL**, or **N/A**
2. Add notes if needed
3. Click **"Save Answer"**
4. If FAIL: Click **"Add Defect for This"**
   - Enter defect note
   - Upload at least one photo

## Complete Inspection

1. Answer all required questions
2. Add defects for all failed items
3. Click **"Complete Inspection"**
4. Confirm completion

System will:
- Validate all answers
- Check defect requirements
- Generate certificate number
- Create PDF documents
- Lock inspection

## Download PDFs

After completion:
- **Package PDF**: Full report with photos
- **Certificate PDF**: High-contrast thermal certificate

Both available at bottom of inspection detail page.

## Common Commands

```bash
# Create new user
python manage.py createsuperuser

# Re-import templates
python manage.py import_a92_templates

# Check database
python manage.py dbshell

# Access admin
http://localhost:8000/admin/
```

## Troubleshooting

**Database error?**
- Check PostgreSQL is running
- Verify .env credentials
- Ensure database exists: `createdb inspection_db`

**Template import fails?**
- Confirm JSON files are in project root
- Check file names match expected format

**Can't upload photos?**
- Ensure media directory exists
- Check file permissions

**PDF generation fails?**
- Verify Pillow is installed: `pip install Pillow`
- Check reportlab is installed: `pip install reportlab`

## Need Help?

- Check **README.md** for detailed documentation
- Review **config/settings.py** for configuration
- Access Django admin at `/admin/` for data management
