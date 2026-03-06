# Quick Fix - PostgreSQL Not Running

## The Problem

You got this error:
```
connection to server at "localhost" failed: Connection refused
```

This means PostgreSQL is not running on your computer.

## Quick Solution (Use SQLite Instead)

I've already configured your `.env` file to use SQLite instead of PostgreSQL. **Just run the setup again!**

```bash
setup.bat
```

That's it! SQLite requires no additional installation or configuration.

---

## What Changed?

Your `.env` file now has:
```
USE_SQLITE=True
```

This tells the app to use SQLite (a simple file-based database) instead of PostgreSQL.

**✅ Pros:**
- No installation needed
- Works immediately
- Perfect for testing and development

**⚠️ Limitations:**
- SQLite is single-user (fine for testing)
- PostgreSQL recommended for production

---

## Want to Use PostgreSQL Later?

### Step 1: Install PostgreSQL

**Windows:**
1. Download from: https://www.postgresql.org/download/windows/
2. Run installer
3. Remember the password you set!
4. Start the service: `net start postgresql-x64-18`

**Check if running:**
```bash
python check_postgres.py
```

### Step 2: Update .env

Change this line in `.env`:
```
USE_SQLITE=False
```

And update PostgreSQL password:
```
DATABASE_PASSWORD=your_actual_password
```

### Step 3: Create Database

```bash
# Command line
psql -U postgres -c "CREATE DATABASE inspection_db;"

# Or use pgAdmin (graphical interface)
```

### Step 4: Run Migrations

```bash
python manage.py migrate
```

---

## Continue Setup Now (with SQLite)

Since your `.env` is configured for SQLite, just run:

```bash
setup.bat
```

Or step by step:

```bash
# 1. Run migrations (will use SQLite)
python manage.py migrate

# 2. Create admin user
python manage.py createsuperuser

# 3. Import templates
python manage.py import_a92_templates

# 4. Start server
python manage.py runserver
```

Then open: http://localhost:8000

---

## More Help

- **INSTALL_POSTGRES.md** - Detailed PostgreSQL setup guide
- **check_postgres.py** - Test PostgreSQL connection
- **README.md** - Full documentation
- **QUICKSTART.md** - Quick reference guide
