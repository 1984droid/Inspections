#!/bin/bash
#
# Bootstrap Script for A92.2 Inspection App
#
# This is the ONLY script you need to run on a fresh Ubuntu/Debian server.
# It will install all dependencies, clone the repo, and deploy the app.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/InspectionApp/main/bootstrap_server.sh | bash
#   OR
#   wget -qO- https://raw.githubusercontent.com/YOUR_USERNAME/InspectionApp/main/bootstrap_server.sh | bash
#   OR (if you have the script locally):
#   chmod +x bootstrap_server.sh && ./bootstrap_server.sh
#
# For redeploy/recovery:
#   ./bootstrap_server.sh --redeploy
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_URL="https://github.com/1984droid/Inspections.git"  # UPDATE THIS!
APP_DIR="/srv/inspection-app"
DOMAIN_NAME=""  # Set your domain here, or leave blank for IP-only access

echo -e "${BLUE}========================================================================${NC}"
echo -e "${BLUE}A92.2 INSPECTION APP - SERVER BOOTSTRAP${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo ""

# Check if redeploy mode
REDEPLOY_MODE=false
if [[ "$1" == "--redeploy" ]]; then
    REDEPLOY_MODE=true
    echo -e "${YELLOW}REDEPLOY MODE: Reinstalling everything${NC}"
    echo ""
fi

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Run as your regular user with sudo access."
    exit 1
fi

# Check sudo access
if ! sudo -n true 2>/dev/null; then
    print_info "This script requires sudo access. You may be prompted for your password."
    sudo -v
fi

#
# STEP 1: Install System Dependencies
#
print_info "Step 1/6: Installing system dependencies..."
echo ""

sudo apt update
sudo apt install -y \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    python3-pip \
    python3-venv \
    build-essential \
    libpq-dev

print_status "System dependencies installed"
echo ""

#
# STEP 2: Install Python 3.14 (if not available, use system Python 3)
#
print_info "Step 2/6: Setting up Python..."
echo ""

# Try Python 3.14 first, fall back to python3
if command -v python3.14 &> /dev/null; then
    PYTHON_BIN="python3.14"
    print_status "Using Python 3.14"
elif command -v python3.12 &> /dev/null; then
    PYTHON_BIN="python3.12"
    print_status "Using Python 3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_BIN="python3.11"
    print_status "Using Python 3.11"
else
    PYTHON_BIN="python3"
    print_status "Using system Python 3"
fi

print_info "Python version: $($PYTHON_BIN --version)"
echo ""

#
# STEP 3: Clone/Update Repository
#
print_info "Step 3/6: Getting application code..."
echo ""

if [ -d "$APP_DIR" ]; then
    if $REDEPLOY_MODE; then
        print_info "Removing existing installation..."
        sudo rm -rf "$APP_DIR"
        sudo mkdir -p "$APP_DIR"
        sudo chown $USER:$USER "$APP_DIR"

        print_info "Cloning repository..."
        git clone "$REPO_URL" "$APP_DIR"
        print_status "Repository cloned"
    else
        print_info "App directory exists, pulling latest changes..."
        cd "$APP_DIR"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || print_info "Using existing code"
        print_status "Code updated"
    fi
else
    sudo mkdir -p "$APP_DIR"
    sudo chown $USER:$USER "$APP_DIR"

    print_info "Cloning repository from $REPO_URL..."
    git clone "$REPO_URL" "$APP_DIR"
    print_status "Repository cloned"
fi

echo ""

#
# STEP 4: Ask for Configuration (only on fresh install)
#
if [ ! -f "$APP_DIR/.env" ] || $REDEPLOY_MODE; then
    print_info "Step 4/6: Configuration setup..."
    echo ""

    # Ask for domain
    read -p "Enter domain name (leave blank to use IP only): " USER_DOMAIN
    if [ -n "$USER_DOMAIN" ]; then
        DOMAIN_NAME="$USER_DOMAIN"
        print_info "Will configure for domain: $DOMAIN_NAME"
    else
        print_info "Will configure for IP-only access"
    fi

    echo ""

    # Ask for admin credentials
    read -p "Enter admin username [admin]: " ADMIN_USERNAME
    ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

    read -p "Enter admin email [admin@inspectionapp.com]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@inspectionapp.com}

    read -sp "Enter admin password [admin]: " ADMIN_PASSWORD
    echo ""
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin}

    echo ""
else
    print_info "Step 4/6: Using existing configuration..."
    echo ""
fi

#
# STEP 5: Run Main Deployment Script
#
print_info "Step 5/6: Running deployment script..."
echo ""

cd "$APP_DIR"
chmod +x deploy_production.sh

if [ -f ".env" ] && [ "$REDEPLOY_MODE" = false ]; then
    # Update mode - preserve existing config
    ./deploy_production.sh --update
else
    # Fresh install - will prompt for passwords
    ./deploy_production.sh
fi

echo ""

#
# STEP 6: Configure SSL (if domain provided)
#
if [ -n "$DOMAIN_NAME" ]; then
    print_info "Step 6/6: SSL Certificate Setup..."
    echo ""

    print_info "Setting up Let's Encrypt SSL for $DOMAIN_NAME..."
    echo ""

    print_info "IMPORTANT: Make sure your domain DNS points to this server!"
    read -p "Press ENTER when DNS is ready, or Ctrl+C to skip SSL setup..."

    sudo certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "$ADMIN_EMAIL" || {
        print_error "SSL setup failed. You can run it manually later:"
        echo -e "  ${BLUE}sudo certbot --nginx -d $DOMAIN_NAME${NC}"
    }

    print_status "SSL configured"
else
    print_info "Step 6/6: Skipping SSL setup (no domain provided)"
    echo ""
fi

#
# DEPLOYMENT COMPLETE
#
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${BLUE}========================================================================${NC}"
echo -e "${GREEN}BOOTSTRAP COMPLETE!${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo ""
echo -e "${GREEN}Your A92.2 Inspection App is now running!${NC}"
echo ""

if [ -n "$DOMAIN_NAME" ]; then
    echo -e "${GREEN}Access your app at:${NC}"
    echo -e "  ${BLUE}https://$DOMAIN_NAME${NC}"
    echo -e "  ${BLUE}https://$DOMAIN_NAME/admin/${NC} (admin interface)"
else
    echo -e "${GREEN}Access your app at:${NC}"
    echo -e "  ${BLUE}http://$SERVER_IP${NC}"
    echo -e "  ${BLUE}http://$SERVER_IP/admin/${NC} (admin interface)"
fi

echo ""
echo -e "${GREEN}Admin Credentials:${NC}"
echo -e "  Username: ${ADMIN_USERNAME}"
echo -e "  Password: ${ADMIN_PASSWORD}"
echo ""
echo -e "${YELLOW}Recovery/Redeploy Command (save this!):${NC}"
echo -e "  ${BLUE}cd $APP_DIR && ./bootstrap_server.sh --redeploy${NC}"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  View app logs:     ${BLUE}sudo journalctl -u inspectionapp -f${NC}"
echo -e "  View nginx logs:   ${BLUE}sudo tail -f /var/log/nginx/access.log${NC}"
echo -e "  Restart app:       ${BLUE}sudo systemctl restart inspectionapp${NC}"
echo -e "  Update app:        ${BLUE}cd $APP_DIR && ./deploy_production.sh --update${NC}"
if [ -n "$DOMAIN_NAME" ]; then
    echo -e "  Renew SSL:         ${BLUE}sudo certbot renew${NC}"
fi
echo ""
echo -e "${GREEN}All done! Happy inspecting! 🚛${NC}"
echo ""
