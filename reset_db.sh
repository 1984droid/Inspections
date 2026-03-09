#!/bin/bash
# Reset database and start fresh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo "       WARNING: Database Reset Script"
echo "============================================================"
echo ""
echo "This will DELETE all data including:"
echo "  - All inspections"
echo "  - All equipment records"
echo "  - All users (including superuser)"
echo "  - All templates"
echo ""
echo "You will need to recreate the superuser after this."
echo ""
read -p "Are you sure you want to continue? (type YES): " confirm

if [ "$confirm" != "YES" ]; then
    echo ""
    echo "Reset cancelled."
    exit 0
fi

echo ""
echo "============================================================"
echo "Step 1: Deleting database file..."
echo "============================================================"
if [ -f "db.sqlite3" ]; then
    rm -f db.sqlite3
    echo -e "${GREEN}[OK]${NC} Database deleted"
else
    echo -e "${YELLOW}[INFO]${NC} No database file found"
fi

echo ""
echo "============================================================"
echo "Step 2: Removing migration files..."
echo "============================================================"
if ls inspections/migrations/0*.py 1> /dev/null 2>&1; then
    rm -f inspections/migrations/0*.py
    echo -e "${GREEN}[OK]${NC} Migration files removed"
else
    echo -e "${YELLOW}[INFO]${NC} No migration files found"
fi

echo ""
echo "============================================================"
echo "Step 3: Creating fresh migrations..."
echo "============================================================"
python3 manage.py makemigrations

echo ""
echo "============================================================"
echo "Step 4: Applying migrations..."
echo "============================================================"
python3 manage.py migrate

echo ""
echo "============================================================"
echo "Step 5: Seeding company, inspectors, and customers..."
echo "============================================================"
python3 manage.py seed_initial_data
echo -e "${GREEN}[OK]${NC} Initial data seeded"

echo ""
echo "============================================================"
echo "Step 6: Creating superuser..."
echo "============================================================"
echo "Please enter superuser credentials:"
python3 manage.py createsuperuser

echo ""
echo "============================================================"
echo "Step 7: Importing templates..."
echo "============================================================"
[ -f "periodic_a922.json" ] && python3 manage.py import_new_template periodic_a922.json
[ -f "cat_ab.json" ] && python3 manage.py import_new_template cat_ab.json
[ -f "cat_cde.json" ] && python3 manage.py import_new_template cat_cde.json
[ -f "uppercontrools.json" ] && python3 manage.py import_new_template uppercontrools.json
[ -f "liners.json" ] && python3 manage.py import_new_template liners.json
[ -f "ladders.json" ] && python3 manage.py import_new_template ladders.json
[ -f "chassis.json" ] && python3 manage.py import_new_template chassis.json
[ -f "load_test_structural.json" ] && python3 manage.py import_new_template load_test_structural.json
echo -e "${GREEN}[OK]${NC} Templates imported"

echo ""
echo "============================================================"
echo "Step 8: Cleaning media files..."
echo "============================================================"
if [ -d "media/defect_photos" ]; then
    rm -f media/defect_photos/*
    echo -e "${GREEN}[OK]${NC} Defect photos cleared"
fi
if [ -d "media/generated_docs" ]; then
    rm -f media/generated_docs/*
    echo -e "${GREEN}[OK]${NC} Generated documents cleared"
fi

echo ""
echo "============================================================"
echo "               DATABASE RESET COMPLETE!"
echo "============================================================"
echo ""
echo "The database has been reset to a clean state."
echo ""
echo "To start the server, run:"
echo "    python3 manage.py runserver"
echo ""
