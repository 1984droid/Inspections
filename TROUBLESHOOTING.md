# Troubleshooting Guide

## "Nothing there" at http://localhost:6000

### Quick Fix

The root URL redirects to login. Try these URLs directly:

1. **Login page**: http://localhost:6000/login/
2. **Admin page**: http://localhost:6000/admin/

### Why This Happens

The homepage (`/`) requires authentication. When you're not logged in:
- Django redirects you to `/login/`
- Your browser should follow this redirect automatically
- If you see "nothing there", the redirect might not be working

### Solution Steps

**Step 1: Make sure the server is running**

```bash
python manage.py runserver 6000
```

You should see:
```
Starting development server at http://127.0.0.1:6000/
Quit the server with CTRL-BREAK.
```

**Step 2: Test with curl (if available)**

```bash
curl -v http://localhost:6000/
```

Look for: `HTTP/1.1 302 Found` (this is correct - it's redirecting)

**Step 3: Access the login page directly**

Open your browser and go to:
```
http://localhost:6000/login/
```

**Step 4: Clear browser cache**

- Press `Ctrl+Shift+Delete`
- Clear cache and cookies
- Try again

**Step 5: Try different browser**

- Chrome/Edge: http://localhost:6000/login/
- Firefox: http://localhost:6000/login/
- Incognito/Private mode

**Step 6: Check for errors**

Look at the terminal where `runserver` is running:
- Are there any red error messages?
- Do you see requests being logged?

Example of good output:
```
[05/Mar/2026 15:30:45] "GET / HTTP/1.1" 302 0
[05/Mar/2026 15:30:45] "GET /login/?next=/ HTTP/1.1" 200 1234
```

**Step 7: Test the server is actually responding**

Run our test script:
```bash
python test_server.py
```

---

## Common Issues

### Issue 1: "This site can't be reached"

**Cause**: Server is not running

**Solution**:
```bash
python manage.py runserver 6000
```

### Issue 2: Blank white page

**Cause**: JavaScript error or CSS not loading

**Solution**:
1. Open browser DevTools (F12)
2. Check Console tab for errors
3. Check Network tab to see if files are loading
4. Try: `python manage.py collectstatic`

### Issue 3: Port already in use

**Error**: `Address already in use`

**Solution**: Use different port:
```bash
python manage.py runserver 6001
```

### Issue 4: Database errors

**Error**: `no such table: django_session`

**Solution**: Run migrations:
```bash
python manage.py migrate
```

### Issue 5: Static files not loading

**Symptom**: Page has no styling

**Solution**:
```bash
python manage.py collectstatic --noinput
```

---

## Step-by-Step Test

Run these commands in order:

```bash
# 1. Check database exists
ls -la db.sqlite3

# 2. Check migrations
python manage.py showmigrations

# 3. Check users exist
python manage.py shell -c "from django.contrib.auth.models import User; print(f'Users: {User.objects.count()}')"

# 4. Check templates imported
python manage.py shell -c "from inspections.models import Template; print(f'Templates: {Template.objects.count()}')"

# 5. Start server
python manage.py runserver 6000
```

Expected results:
1. Database file exists (200+ KB)
2. All migrations have `[X]`
3. At least 1 user
4. 7 templates
5. Server starts without errors

---

## URL Reference

Once logged in, these URLs should work:

| URL | Description |
|-----|-------------|
| http://localhost:6000/ | Dashboard (requires login) |
| http://localhost:6000/login/ | Login page |
| http://localhost:6000/admin/ | Django admin |
| http://localhost:6000/inspections/ | Inspection list |
| http://localhost:6000/inspections/new/ | New inspection |
| http://localhost:6000/equipment/new/ | New equipment |

---

## Browser DevTools

If page is blank:

1. Open DevTools: Press `F12`
2. Go to **Console** tab
   - Look for JavaScript errors (red text)
   - Common: "Failed to load resource"
3. Go to **Network** tab
   - Reload page (`Ctrl+R`)
   - Look for failed requests (red status codes)
   - Check if main page returns 200 or 302

---

## Django Debug

If you see an error page:

1. **Yellow Django error page** = Good! Django is working
   - Read the error message
   - Check the traceback
   - Look at the line number mentioned

2. **"Server Error (500)"** = Check terminal for traceback

3. **"Not Found (404)"** = URL doesn't exist
   - Check URL spelling
   - See URL Reference above

---

## Verify Installation

Run this checklist:

```bash
# Database
[ ] db.sqlite3 exists
[ ] Migrations applied (python manage.py migrate)

# User account
[ ] Superuser created (python manage.py createsuperuser)

# Templates
[ ] Templates imported (python manage.py import_a92_templates)

# Server
[ ] Server starts without errors
[ ] Can access http://localhost:6000/login/
[ ] Can login with superuser credentials
```

---

## Still Not Working?

### Option 1: Start from scratch

```bash
# Delete database
del db.sqlite3  # Windows
rm db.sqlite3   # Linux/Mac

# Run setup again
setup.bat
```

### Option 2: Check settings

Verify `.env` file has:
```
USE_SQLITE=True
DEBUG=True
```

### Option 3: Manual setup

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py import_a92_templates
python manage.py runserver 6000
```

### Option 4: Get detailed error info

Enable verbose mode:

Edit `config/settings.py`, find:
```python
DEBUG = True
```

Make sure it's `True`, then restart server.

---

## Getting Help

When asking for help, provide:

1. **What you did**:
   ```
   Ran: setup.bat
   Opened: http://localhost:6000
   ```

2. **What you see**:
   - Screenshot of browser
   - Screenshot of terminal

3. **Server output**:
   ```
   Copy the last 20 lines from the terminal
   ```

4. **Browser console**:
   - Press F12 → Console tab
   - Copy any red error messages

5. **Environment**:
   - Windows/Linux/Mac
   - Python version: `python --version`
   - Browser: Chrome/Firefox/etc.
