#!/bin/bash
#
# Quick Update Script for InspectionApp
#
# Run this anytime to pull latest code and restart the app
# Usage: ./update.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}InspectionApp - Quick Update${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd /srv/inspection-app

echo -e "${BLUE}[1/4]${NC} Pulling latest code from GitHub..."
git fetch --all
git reset --hard origin/main
echo -e "${GREEN}✓${NC} Code updated"

echo -e "${BLUE}[2/5]${NC} Syncing database password..."
DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
if [ -n "$DB_PASSWORD" ]; then
    sudo -u postgres psql -c "ALTER USER inspectionapp WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null
    echo -e "${GREEN}✓${NC} Database password synced"
else
    echo -e "${GREEN}✓${NC} Using existing database password"
fi

echo -e "${BLUE}[3/5]${NC} Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Dependencies updated"

echo -e "${BLUE}[4/5]${NC} Running migrations..."
python manage.py migrate --noinput
echo -e "${GREEN}✓${NC} Migrations complete"

echo -e "${BLUE}[5/5]${NC} Restarting service..."
sudo systemctl restart inspectionapp
sleep 2
echo -e "${GREEN}✓${NC} Service restarted"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Visit: https://mouseion.advfleet.com"
echo ""
