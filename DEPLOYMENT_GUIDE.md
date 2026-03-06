# A92.2 Inspection App - Deployment Guide

## 🚀 Fresh Server Deployment (The Easy Way)

### One-Command Deploy

On a fresh Ubuntu/Debian server, run ONE of these commands:

```bash
# Option 1: Using curl
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/InspectionApp/main/bootstrap_server.sh | bash

# Option 2: Using wget
wget -qO- https://raw.githubusercontent.com/YOUR_USERNAME/InspectionApp/main/bootstrap_server.sh | bash

# Option 3: Clone repo first, then run
git clone https://github.com/YOUR_USERNAME/InspectionApp.git
cd InspectionApp
chmod +x bootstrap_server.sh
./bootstrap_server.sh
```

That's it! The script will:
- ✅ Install all dependencies (PostgreSQL, Nginx, Python, certbot)
- ✅ Clone your repository
- ✅ Set up database
- ✅ Configure Nginx
- ✅ Set up SSL with Let's Encrypt
- ✅ Import inspection templates
- ✅ Create systemd service
- ✅ Start everything

---

## 🆘 Emergency Recovery/Redeploy

**If something breaks and you need to start over:**

```bash
cd /srv/inspection-app
./bootstrap_server.sh --redeploy
```

This will wipe everything and reinstall from scratch.

---

## 🔧 Daily Operations

### View Live Logs
```bash
# Application logs
sudo journalctl -u inspectionapp -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart inspection app
sudo systemctl restart inspectionapp

# Restart Nginx
sudo systemctl restart nginx

# Check app status
sudo systemctl status inspectionapp
```

### Update to Latest Code
```bash
cd /srv/inspection-app
./deploy_production.sh --update
```

### Database Operations
```bash
# Access PostgreSQL
sudo -u postgres psql inspectionapp

# Backup database
sudo -u postgres pg_dump inspectionapp > backup_$(date +%Y%m%d).sql

# Restore database
sudo -u postgres psql inspectionapp < backup_20260306.sql

# Reset database (DANGER!)
cd /srv/inspection-app
python -c "from setup import reset_database; reset_database()"
python setup.py
```

---

## 🔐 SSL Certificate Management

### Initial SSL Setup
```bash
sudo certbot --nginx -d yourdomain.com
```

### Renew SSL Certificate
```bash
# Manual renewal (usually automatic)
sudo certbot renew

# Test renewal process
sudo certbot renew --dry-run
```

### Check Certificate Expiry
```bash
sudo certbot certificates
```

---

## 📁 Important File Locations

```
/srv/inspection-app/          # Application root
├── .env                       # Environment variables (SECRET!)
├── manage.py                  # Django management
├── db.sqlite3                 # Database (if using SQLite)
├── media/                     # Uploaded defect photos
├── staticfiles/               # Collected static files
├── .venv/                     # Python virtual environment
└── inspections/               # Main Django app

/etc/nginx/sites-available/inspectionapp    # Nginx config
/etc/systemd/system/inspectionapp.service   # Systemd service
/var/log/nginx/                             # Nginx logs
```

---

## 🐛 Troubleshooting

### App Won't Start
```bash
# Check service status
sudo systemctl status inspectionapp

# View recent errors
sudo journalctl -u inspectionapp -n 50

# Check if port 8000 is in use
sudo netstat -tulpn | grep 8000

# Restart the service
sudo systemctl restart inspectionapp
```

### Nginx Issues
```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check nginx status
sudo systemctl status nginx
```

### Database Connection Issues
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -c "SELECT version();"

# Check database exists
sudo -u postgres psql -l | grep inspectionapp
```

### Permission Issues with Photos
```bash
# Fix media directory permissions
cd /srv/inspection-app
sudo chown -R $USER:www-data media/
sudo chmod -R 775 media/
```

---

## 📊 Server Requirements

**Minimum:**
- Ubuntu 20.04+ or Debian 11+
- 1 CPU core
- 2GB RAM
- 20GB disk space

**Recommended:**
- Ubuntu 22.04 LTS
- 2 CPU cores
- 4GB RAM
- 50GB disk space

---

## 🔄 Backup Strategy

### Automated Daily Backup Script

Create `/home/$USER/backup_inspection.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump inspectionapp > $BACKUP_DIR/db_$DATE.sql

# Backup media files (photos)
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /srv/inspection-app/media/

# Backup .env file
cp /srv/inspection-app/.env $BACKUP_DIR/env_$DATE.txt

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Add to crontab:
```bash
crontab -e
# Add this line for daily 2 AM backup:
0 2 * * * /home/$USER/backup_inspection.sh
```

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Fresh deploy | `./bootstrap_server.sh` |
| Redeploy/recover | `./bootstrap_server.sh --redeploy` |
| Update app | `cd /srv/inspection-app && ./deploy_production.sh --update` |
| View logs | `sudo journalctl -u inspectionapp -f` |
| Restart app | `sudo systemctl restart inspectionapp` |
| Restart nginx | `sudo systemctl restart nginx` |
| Setup SSL | `sudo certbot --nginx -d yourdomain.com` |
| Renew SSL | `sudo certbot renew` |
| Backup DB | `sudo -u postgres pg_dump inspectionapp > backup.sql` |
| Django shell | `cd /srv/inspection-app && source .venv/bin/activate && python manage.py shell` |

---

## 🌐 Before You Deploy

1. **Update the repository URL** in `bootstrap_server.sh`:
   ```bash
   REPO_URL="https://github.com/YOUR_USERNAME/InspectionApp.git"
   ```

2. **Set up your domain's DNS** to point to your server's IP

3. **Open firewall ports** (if needed):
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

4. **Save your admin credentials** somewhere safe!

---

## ✅ Post-Deployment Checklist

- [ ] App accessible via browser
- [ ] Admin panel login works
- [ ] Can create customer
- [ ] Can create equipment
- [ ] Can start inspection
- [ ] Can upload defect photo
- [ ] SSL certificate installed (if using domain)
- [ ] Backup script configured
- [ ] Saved admin credentials securely

---

**Last updated:** 2026-03-06
**Script version:** 1.0
