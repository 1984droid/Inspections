#!/bin/bash
#
# Production Deployment Script for A92.2 Inspection App
#
# This script automates the deployment of the Inspection App to a Linux VM
# with PostgreSQL 18, Python 3.14, Nginx, and SSL
#
# Usage:
#   bash deploy_production.sh                 # Interactive setup (no chmod needed)
#   bash deploy_production.sh --auto          # Automated (use defaults)
#   bash deploy_production.sh --update        # Update existing deployment
#   bash deploy_production.sh --fresh         # Wipe and fresh install with seed data
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/srv/inspection-app"
APP_USER=$(whoami)
DJANGO_PORT=8000

echo -e "${BLUE}========================================================================${NC}"
echo -e "${BLUE}A92.2 INSPECTION APP - PRODUCTION DEPLOYMENT${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo ""

# Parse arguments
AUTO_MODE=false
UPDATE_MODE=false
FRESH_MODE=false

for arg in "$@"; do
    case $arg in
        --auto)
            AUTO_MODE=true
            shift
            ;;
        --update)
            UPDATE_MODE=true
            shift
            ;;
        --fresh)
            FRESH_MODE=true
            shift
            ;;
    esac
done

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Run as your regular user."
    exit 1
fi

# Check system dependencies
check_dependencies() {
    print_info "Checking system dependencies..."

    local missing_deps=()

    # Check Python 3.14
    if ! command -v python3.14 &> /dev/null; then
        missing_deps+=("python3.14")
    else
        print_status "Python 3.14 installed: $(python3.14 --version)"
    fi

    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        missing_deps+=("postgresql")
    else
        print_status "PostgreSQL installed: $(psql --version)"
    fi

    # Check Nginx
    if ! command -v nginx &> /dev/null; then
        missing_deps+=("nginx")
    else
        print_status "Nginx installed: $(nginx -v 2>&1)"
    fi

    # Check git
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    else
        print_status "Git installed: $(git --version)"
    fi

    # Check certbot (optional, but recommended)
    if ! command -v certbot &> /dev/null; then
        print_warning "Certbot not installed (optional for SSL)"
    else
        print_status "Certbot installed: $(certbot --version 2>&1 | head -n1)"
    fi

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_info "Please install missing dependencies and try again"
        print_info ""
        print_info "Ubuntu/Debian installation commands:"
        echo "  sudo apt update"
        echo "  sudo apt install -y postgresql postgresql-contrib nginx certbot python3-certbot-nginx git"
        exit 1
    fi

    print_status "All dependencies satisfied"
}

# Setup PostgreSQL
setup_postgresql() {
    print_info "Setting up PostgreSQL database..."

    # Check if DB_PASSWORD is already set (from bootstrap script)
    if [ -z "$DB_PASSWORD" ]; then
        if ! $AUTO_MODE; then
            read -sp "Enter database password for 'inspectionapp' user: " DB_PASSWORD
            echo ""
        else
            DB_PASSWORD="inspectionapp_secure_$(openssl rand -hex 8)"
            print_warning "Auto-generated database password: $DB_PASSWORD"
        fi
    else
        print_info "Using provided database password"
    fi

    # Check PostgreSQL authentication method
    print_info "Configuring PostgreSQL authentication..."

    # Ensure peer authentication works for postgres user
    if ! sudo -u postgres psql -c '\q' 2>/dev/null; then
        print_warning "PostgreSQL peer authentication issue detected"
        print_info "Checking pg_hba.conf configuration..."

        # Backup pg_hba.conf
        PG_VERSION=$(psql --version | awk '{print $3}' | cut -d'.' -f1)
        PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

        if [ -f "$PG_HBA" ]; then
            sudo cp "$PG_HBA" "$PG_HBA.backup.$(date +%Y%m%d_%H%M%S)"

            # Ensure local peer authentication for postgres user
            if ! sudo grep -q "^local.*all.*postgres.*peer" "$PG_HBA"; then
                print_info "Adding peer authentication for postgres user..."
                sudo sed -i '1i\# Allow postgres user to connect via peer authentication' "$PG_HBA"
                sudo sed -i '2i\local   all             postgres                                peer' "$PG_HBA"
                sudo systemctl reload postgresql
                sleep 2
            fi
        fi
    fi

    # Create database user and database
    sudo -u postgres psql <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'inspectionapp') THEN
        CREATE USER inspectionapp WITH PASSWORD '$DB_PASSWORD';
    ELSE
        ALTER USER inspectionapp WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

SELECT 'CREATE DATABASE inspectionapp OWNER inspectionapp'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'inspectionapp')\gexec

GRANT ALL PRIVILEGES ON DATABASE inspectionapp TO inspectionapp;
ALTER USER inspectionapp CREATEDB;
EOF

    print_status "PostgreSQL database created"
    export DB_PASSWORD
}

# Setup Python environment
setup_python_env() {
    print_info "Setting up Python virtual environment..."

    cd "$APP_DIR"

    # Create venv if doesn't exist
    if [ ! -d ".venv" ]; then
        python3.14 -m venv .venv
        print_status "Virtual environment created"
    fi

    # Activate and install dependencies
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt

    print_status "Python dependencies installed"
}

# Create .env file
create_env_file() {
    print_info "Creating production .env file..."

    # Generate Django secret key (activate venv first)
    cd "$APP_DIR"
    source .venv/bin/activate
    SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    # Check if DOMAIN_NAME is already set (from bootstrap script)
    if [ -z "$DOMAIN_NAME" ]; then
        # Check if .env already exists (for updates) and preserve domain
        EXISTING_DOMAIN=""
        if [ -f .env ]; then
            EXISTING_DOMAIN=$(grep "^ALLOWED_HOSTS=" .env | cut -d'=' -f2 | cut -d',' -f1)
        fi

        # Ask for domain name
        if ! $AUTO_MODE; then
            if [ -n "$EXISTING_DOMAIN" ] && [ "$EXISTING_DOMAIN" != "localhost" ] && [ "$EXISTING_DOMAIN" != "$SERVER_IP" ]; then
                DEFAULT_DOMAIN="$EXISTING_DOMAIN"
            else
                DEFAULT_DOMAIN=""
            fi

            read -p "Enter domain name (leave blank to use IP only) [$DEFAULT_DOMAIN]: " DOMAIN_NAME
            DOMAIN_NAME=${DOMAIN_NAME:-$DEFAULT_DOMAIN}
        else
            DOMAIN_NAME=""
        fi
    else
        print_info "Using provided domain: $DOMAIN_NAME"
    fi

    # Build ALLOWED_HOSTS
    if [ -n "$DOMAIN_NAME" ]; then
        ALLOWED_HOSTS="$DOMAIN_NAME,$SERVER_IP,localhost,127.0.0.1"
        ACCESS_URL="https://$DOMAIN_NAME"
    else
        ALLOWED_HOSTS="$SERVER_IP,localhost,127.0.0.1"
        ACCESS_URL="http://$SERVER_IP"
    fi

    cat > .env <<EOF
# Django settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS

# Database (PostgreSQL) - PRODUCTION
USE_SQLITE=False
DB_NAME=inspectionapp
DB_USER=inspectionapp
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
EOF

    chmod 600 .env
    print_status "Production .env file created"
    print_info "Server will be accessible at: $ACCESS_URL"
}

# Run migrations and setup database
setup_database() {
    print_info "Running database migrations..."

    cd "$APP_DIR"
    source .venv/bin/activate

    python manage.py migrate
    print_status "Migrations completed"

    # Seed company, inspectors, and customers
    print_info "Seeding company, inspectors, and customers..."
    python manage.py seed_initial_data --force-passwords
    print_status "Initial data seeded"

    # Collect static files for Django admin
    print_info "Collecting static files..."
    python manage.py collectstatic --noinput
    print_status "Static files collected"

    if ! $UPDATE_MODE; then
        # Import templates (only on fresh install, updates handle this separately)
        print_info "Importing inspection templates..."
        cd "$APP_DIR"

        if [ -f "setup.py" ]; then
            python setup.py
            print_status "Templates imported successfully"
        else
            print_warning "setup.py not found - skipping template import"
            print_info "Run 'python setup.py' manually to import templates"
        fi
    fi
}

# Configure Nginx
configure_nginx() {
    print_info "Configuring Nginx..."

    # Get domain name for config
    if [ -n "$DOMAIN_NAME" ]; then
        SERVER_NAME="$DOMAIN_NAME"
    else
        SERVER_NAME="_"
    fi

    sudo tee /etc/nginx/sites-available/inspectionapp > /dev/null <<EOF
# Nginx configuration for InspectionApp
server {
    server_name $SERVER_NAME;

    # Increase timeouts for inspection operations
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
    send_timeout 600;

    # Increase body size for defect photo uploads (20MB)
    client_max_body_size 20M;

    # Django application
    location / {
        proxy_pass http://localhost:$DJANGO_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Django Static Files
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Django Media Files (defect photos)
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    listen 80;
}
EOF

    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/inspectionapp /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default

    # Test nginx config
    if sudo nginx -t; then
        sudo systemctl reload nginx
        print_status "Nginx configured successfully"

        if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "_" ]; then
            print_info ""
            print_warning "⚠️  SSL Setup Required for Production!"
            print_info ""
            print_info "Run this command to enable HTTPS with Let's Encrypt:"
            echo -e "  ${GREEN}sudo certbot --nginx -d $DOMAIN_NAME${NC}"
            print_info ""
            print_info "Certbot will:"
            print_info "  ✓ Obtain SSL certificates from Let's Encrypt"
            print_info "  ✓ Configure nginx for HTTPS (port 443)"
            print_info "  ✓ Set up HTTP → HTTPS redirect"
            print_info "  ✓ Enable auto-renewal of certificates"
            print_info ""
            print_info "After certbot, your site will be available at:"
            echo -e "  ${BLUE}https://$DOMAIN_NAME${NC}"
            print_info ""
        fi
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
}

# Create systemd service
create_systemd_service() {
    print_info "Creating systemd service file..."

    sudo tee /etc/systemd/system/inspectionapp.service > /dev/null <<EOF
[Unit]
Description=A92.2 Inspection App Django Backend
After=network.target postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/.venv/bin"
ExecStart=$APP_DIR/.venv/bin/gunicorn --workers 3 --bind 0.0.0.0:$DJANGO_PORT config.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Install gunicorn if not already installed
    source $APP_DIR/.venv/bin/activate
    pip install gunicorn

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable inspectionapp

    print_status "Systemd service created and enabled"
}

# Start service
start_service() {
    print_info "Starting service..."

    sudo systemctl restart inspectionapp

    sleep 3

    # Check status
    if systemctl is-active --quiet inspectionapp; then
        print_status "InspectionApp service is running"
    else
        print_error "InspectionApp service failed to start"
        sudo journalctl -u inspectionapp -n 20
    fi
}

# Main deployment flow
main() {
    if $FRESH_MODE; then
        print_info "FRESH INSTALL MODE: Wiping and starting clean..."

        # Stop service if running
        if systemctl is-active --quiet inspectionapp 2>/dev/null; then
            print_info "Stopping inspectionapp service..."
            sudo systemctl stop inspectionapp
        fi

        # Load DB password from existing .env if available
        cd "$APP_DIR"
        if [ -f ".env" ]; then
            DB_PASSWORD=$(grep "^DB_PASSWORD=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '\r')
            if [ -n "$DB_PASSWORD" ]; then
                print_info "Using database password from existing .env"
                export DB_PASSWORD
            fi
        fi

        # Wipe PostgreSQL database
        print_warning "Dropping existing database..."
        sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS inspectionapp;
DROP USER IF EXISTS inspectionapp;
EOF
        print_status "Database wiped"

        # Remove old virtualenv
        if [ -d "$APP_DIR/.venv" ]; then
            print_info "Removing old virtual environment..."
            rm -rf "$APP_DIR/.venv"
        fi

        # Remove media files (generated PDFs, photos)
        if [ -d "$APP_DIR/media" ]; then
            print_info "Removing old media files..."
            rm -rf "$APP_DIR/media"/*
        fi

        # Remove SQLite db if exists
        if [ -f "$APP_DIR/db.sqlite3" ]; then
            rm -f "$APP_DIR/db.sqlite3"
        fi

        print_status "Clean slate ready"

        # Now proceed with fresh install
        check_dependencies
        setup_postgresql
        setup_python_env

        # Check if .env exists, create if not
        if [ ! -f "$APP_DIR/.env" ]; then
            print_warning "No .env found, creating new one..."
            create_env_file
        else
            print_status "Using existing .env file"
        fi

        # Ensure production settings
        print_info "Ensuring production database settings..."
        sed -i "s|USE_SQLITE=.*|USE_SQLITE=False|g" .env
        sed -i "s|DEBUG=.*|DEBUG=False|g" .env
        sed -i "s|DB_NAME=.*|DB_NAME=inspectionapp|g" .env
        sed -i "s|DB_USER=.*|DB_USER=inspectionapp|g" .env
        sed -i "s|DB_HOST=.*|DB_HOST=localhost|g" .env
        sed -i "s|DB_PORT=.*|DB_PORT=5432|g" .env
        if [ -n "$DB_PASSWORD" ]; then
            sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|g" .env
        fi
        print_status "Production settings confirmed"

        setup_database
        configure_nginx
        create_systemd_service
        start_service

    elif $UPDATE_MODE; then
        print_info "UPDATE MODE: Updating existing deployment..."

        cd "$APP_DIR"

        # Pull latest changes
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || print_warning "Git pull failed - continuing with local files"

        # Check if .env exists and has required fields
        if [ ! -f .env ]; then
            print_error ".env file not found!"
            print_info "Creating new .env file for production..."

            # Setup PostgreSQL first
            setup_postgresql

            # Create new .env file
            create_env_file
        else
            print_status "Found existing .env file"

            # Check if DB_PASSWORD exists
            DB_PASSWORD=$(grep "^DB_PASSWORD=" .env 2>/dev/null | cut -d'=' -f2 | tr -d '\r')

            if [ -z "$DB_PASSWORD" ]; then
                print_warning "DB_PASSWORD not found in .env, setting up database..."
                setup_postgresql

                # Add database settings to .env
                cat >> .env <<EOF

# Database (PostgreSQL) - PRODUCTION
USE_SQLITE=False
DB_NAME=inspectionapp
DB_USER=inspectionapp
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432
EOF
            fi
        fi

        # Generate unique SECRET_KEY
        print_info "Generating unique SECRET_KEY..."
        source .venv/bin/activate
        NEW_SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$NEW_SECRET_KEY|g" .env

        # Update ALLOWED_HOSTS
        SERVER_IP=$(hostname -I | awk '{print $1}')
        if [ -n "$DOMAIN_NAME" ]; then
            sed -i "s|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=$DOMAIN_NAME,$SERVER_IP,localhost,127.0.0.1|g" .env
        fi

        # Ensure USE_SQLITE=False for production
        sed -i "s|USE_SQLITE=.*|USE_SQLITE=False|g" .env
        sed -i "s|DEBUG=.*|DEBUG=False|g" .env
        print_status ".env configured"

        # Sync PostgreSQL password with .env
        print_info "Syncing database password..."
        DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2 | tr -d '\r')
        if [ -n "$DB_PASSWORD" ]; then
            print_info "Setting PostgreSQL password for inspectionapp user..."
            sudo -u postgres psql <<EOF
ALTER USER inspectionapp WITH PASSWORD '$DB_PASSWORD';
EOF
            print_status "Database password synced: inspectionapp"
        else
            print_error "Still no DB_PASSWORD in .env after configuration!"
            exit 1
        fi

        # Remove SQLite database if it exists
        if [ -f db.sqlite3 ]; then
            print_warning "Removing SQLite database (switching to PostgreSQL)..."
            rm -f db.sqlite3
            print_status "SQLite database removed"
        fi

        # Check if PostgreSQL database needs reset
        print_info "Checking PostgreSQL database schema..."
        source .venv/bin/activate

        # Try to check if tables exist
        TABLE_CHECK=$(sudo -u postgres psql -d inspectionapp -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'inspections_companyinfo');" 2>/dev/null || echo "f")

        if [ "$TABLE_CHECK" = "f" ]; then
            print_warning "Database schema incomplete or corrupted. Resetting database..."

            # Drop and recreate database
            sudo -u postgres psql <<EOF
DROP DATABASE IF EXISTS inspectionapp;
CREATE DATABASE inspectionapp OWNER inspectionapp;
GRANT ALL PRIVILEGES ON DATABASE inspectionapp TO inspectionapp;
EOF
            print_status "Database reset complete"
        fi

        setup_python_env
        setup_database

        # Seed company, inspectors, and customers (update mode)
        print_info "Updating company, inspectors, and customers..."
        source .venv/bin/activate
        python manage.py seed_initial_data --force-passwords
        print_status "Initial data updated"

        # Import templates
        print_info "Importing/updating inspection templates..."
        cd "$APP_DIR"
        source .venv/bin/activate
        [ -f "periodic_a922.json" ] && python manage.py import_new_template periodic_a922.json
        [ -f "cat_ab.json" ] && python manage.py import_new_template cat_ab.json
        [ -f "cat_cde.json" ] && python manage.py import_new_template cat_cde.json
        [ -f "uppercontrools.json" ] && python manage.py import_new_template uppercontrools.json
        [ -f "liners.json" ] && python manage.py import_new_template liners.json
        [ -f "ladders.json" ] && python manage.py import_new_template ladders.json
        [ -f "chassis.json" ] && python manage.py import_new_template chassis.json
        [ -f "load_test_structural.json" ] && python manage.py import_new_template load_test_structural.json
        print_status "Templates imported"

        # Populate ANSI references
        print_info "Populating ANSI references..."
        python populate_ansi_refs.py
        print_status "ANSI references populated"

        start_service

    else
        print_info "FRESH INSTALL: Setting up new deployment..."

        check_dependencies
        setup_postgresql
        setup_python_env
        create_env_file

        # Ensure production settings after env file creation
        print_info "Ensuring production database settings..."
        sed -i "s|USE_SQLITE=.*|USE_SQLITE=False|g" .env
        sed -i "s|DEBUG=.*|DEBUG=False|g" .env
        sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASSWORD|g" .env
        print_status "Production settings confirmed"

        setup_database
        configure_nginx
        create_systemd_service
        start_service
    fi

    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    echo ""
    echo -e "${BLUE}========================================================================${NC}"
    echo -e "${GREEN}DEPLOYMENT COMPLETE!${NC}"
    echo -e "${BLUE}========================================================================${NC}"
    echo ""
    echo -e "${GREEN}Application URLs:${NC}"
    if [ -n "$DOMAIN_NAME" ]; then
        echo -e "  Main URL:  https://$DOMAIN_NAME (after running certbot)"
        echo -e "  HTTP URL:  http://$SERVER_IP"
    else
        echo -e "  Main URL:  http://$SERVER_IP"
    fi
    echo -e "  Admin:     http://$SERVER_IP/admin/"
    echo ""
    echo -e "${GREEN}Admin Credentials:${NC}"
    echo -e "  Username:  $ADMIN_USERNAME"
    echo -e "  Password:  $ADMIN_PASSWORD"
    echo ""
    if [ -n "$DOMAIN_NAME" ] && [ "$DOMAIN_NAME" != "_" ]; then
        echo -e "${YELLOW}Next Steps:${NC}"
        echo -e "  1. Run SSL setup:  ${GREEN}sudo certbot --nginx -d $DOMAIN_NAME${NC}"
        echo ""
    fi
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "  View logs:         ${BLUE}sudo journalctl -u inspectionapp -f${NC}"
    echo -e "  View Nginx logs:   ${BLUE}sudo tail -f /var/log/nginx/access.log${NC}"
    echo -e "  Restart app:       ${BLUE}sudo systemctl restart inspectionapp${NC}"
    echo -e "  Reload Nginx:      ${BLUE}sudo systemctl reload nginx${NC}"
    echo -e "  Update app:        ${BLUE}cd $APP_DIR && ./deploy_production.sh --update${NC}"
    echo ""
}

# Run main function
main
