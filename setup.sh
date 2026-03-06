#!/bin/bash
# Setup script for A92.2 Inspection App (Linux/Mac)

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "============================================================"
echo "         A92.2 Inspection App - Quick Setup"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Python 3 not found! Please install Python 3.14+"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python found"
python3 --version
echo ""

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo -e "${RED}[ERROR]${NC} manage.py not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Project directory confirmed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[WARNING]${NC} .env file not found"
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}[INFO]${NC} Copying .env.example to .env"
        cp .env.example .env
        echo -e "${GREEN}[OK]${NC} Created .env file"
        echo -e "${YELLOW}[WARNING]${NC} Please edit .env with your database credentials!"
        echo ""
        read -p "Press Enter to continue after editing .env..."
    else
        echo -e "${RED}[ERROR]${NC} No .env.example found!"
        exit 1
    fi
fi

# Install dependencies
echo "============================================================"
echo "Installing dependencies..."
echo "============================================================"
python3 -m pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK]${NC} Dependencies installed"
else
    echo -e "${YELLOW}[WARNING]${NC} Some dependencies may have failed to install"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Database setup prompt
echo "============================================================"
echo "Database Setup"
echo "============================================================"
echo "Make sure PostgreSQL is running and configured in .env"
echo ""
read -p "Have you created the database? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "To create the database, run:"
    echo "  createdb inspection_db"
    echo ""
    echo "Or in PostgreSQL shell:"
    echo "  CREATE DATABASE inspection_db;"
    echo ""
    exit 1
fi

# Run migrations
echo ""
echo "============================================================"
echo "Creating database migrations..."
echo "============================================================"
python3 manage.py makemigrations
echo -e "${GREEN}[OK]${NC} Migrations created"
echo ""

echo "============================================================"
echo "Running migrations..."
echo "============================================================"
python3 manage.py migrate
echo -e "${GREEN}[OK]${NC} Migrations applied"
echo ""

# Create superuser
echo "============================================================"
echo "Create superuser account"
echo "============================================================"
echo "Follow the prompts to create an admin user..."
echo ""
python3 manage.py createsuperuser
echo ""

# Import templates
echo "============================================================"
echo "Importing A92.2 templates..."
echo "============================================================"
[ -f "periodic_a922.json" ] && python3 manage.py import_new_template periodic_a922.json
[ -f "cat_ab.json" ] && python3 manage.py import_new_template cat_ab.json
[ -f "cat_cde.json" ] && python3 manage.py import_new_template cat_cde.json
[ -f "uppercontrools.json" ] && python3 manage.py import_new_template uppercontrools.json
[ -f "liners.json" ] && python3 manage.py import_new_template liners.json
[ -f "ladders.json" ] && python3 manage.py import_new_template ladders.json
[ -f "chassis.json" ] && python3 manage.py import_new_template chassis.json
echo -e "${GREEN}[OK]${NC} Templates imported"
echo ""

# Create media directories
echo "============================================================"
echo "Creating media directories..."
echo "============================================================"
mkdir -p media/defect_photos
mkdir -p media/generated_docs
echo -e "${GREEN}[OK]${NC} Media directories created"
echo ""

# Final message
echo "============================================================"
echo "                   SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "To start the development server, run:"
echo ""
echo "    python3 manage.py runserver"
echo ""
echo "Then open your browser to: http://localhost:8000"
echo ""
echo "Login with the superuser credentials you just created."
echo ""
echo "Check README.md for detailed usage instructions."
echo ""
