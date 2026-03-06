# PostgreSQL Installation and Setup Guide

## The Error You're Seeing

```
connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

This means PostgreSQL is either:
1. Not installed
2. Not running
3. Running on a different port

## Option 1: Install and Start PostgreSQL (Recommended)

### Windows

#### Download and Install
1. Download PostgreSQL 18 from: https://www.postgresql.org/download/windows/
2. Run the installer
3. During installation:
   - Set a password for the `postgres` user (remember this!)
   - Default port: 5432 (keep this)
   - Install pgAdmin 4 (recommended)

#### Start PostgreSQL Service
```bash
# Start PostgreSQL service
net start postgresql-x64-18

# Or use Services app (Win+R, type services.msc)
# Find "postgresql-x64-18" and click Start
```

#### Verify PostgreSQL is Running
```bash
# Check if service is running
sc query postgresql-x64-18

# Or try connecting
psql -U postgres
```

#### Create Database
```bash
# Option 1: Command line
psql -U postgres -c "CREATE DATABASE inspection_db;"

# Option 2: pgAdmin
# Open pgAdmin → Right-click Databases → Create → Database
# Name: inspection_db
```

### Linux (Ubuntu/Debian)

```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database
sudo -u postgres createdb inspection_db

# Create user (optional)
sudo -u postgres psql -c "CREATE USER myuser WITH PASSWORD 'mypassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE inspection_db TO myuser;"
```

### macOS

```bash
# Using Homebrew
brew install postgresql@18

# Start PostgreSQL
brew services start postgresql@18

# Create database
createdb inspection_db
```

## Option 2: Use SQLite Instead (Quick Test)

If you just want to test the app quickly without PostgreSQL, you can switch to SQLite:

### Edit `config/settings.py`

Find this section:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'inspection_db'),
        'USER': os.getenv('DATABASE_USER', 'postgres'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', 'postgres'),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
    }
}
```

Replace with:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Note:** SQLite is fine for testing but PostgreSQL is recommended for production use.

## Option 3: Use Docker PostgreSQL

If you have Docker installed:

```bash
# Run PostgreSQL in Docker
docker run --name inspection-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=inspection_db -p 5432:5432 -d postgres:18

# Check if running
docker ps

# Stop when done
docker stop inspection-postgres

# Start again later
docker start inspection-postgres
```

## After PostgreSQL is Running

Update your `.env` file with correct credentials:

```
DATABASE_NAME=inspection_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

Then run the setup script again:

```bash
setup.bat
```

Or run migrations manually:

```bash
python manage.py migrate
```

## Verify Connection

Test PostgreSQL connection:

```bash
# Windows
psql -U postgres -d inspection_db

# Linux/Mac
psql -U postgres -d inspection_db

# Or from Python
python -c "import psycopg2; conn = psycopg2.connect('dbname=inspection_db user=postgres password=postgres host=localhost'); print('✅ Connected!'); conn.close()"
```

## Common Issues

### Issue: "role 'postgres' does not exist"

**Solution:** Create the postgres user:
```bash
createuser -s postgres
```

### Issue: "password authentication failed"

**Solution:** Update `.env` with the correct password you set during installation.

### Issue: "could not connect to server"

**Solution:** Check if PostgreSQL service is running:
```bash
# Windows
sc query postgresql-x64-18

# Linux/Mac
sudo systemctl status postgresql
```

### Issue: "port 5432 is already in use"

**Solution:** Either:
1. Stop the other service using port 5432
2. Change PostgreSQL port in postgresql.conf
3. Use a different port in .env: `DATABASE_PORT=5433`

## Quick Check Script

Save as `check_postgres.py` and run to verify setup:

```python
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DATABASE_NAME', 'inspection_db'),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', 'postgres'),
        host=os.getenv('DATABASE_HOST', 'localhost'),
        port=os.getenv('DATABASE_PORT', '5432')
    )
    print("✅ PostgreSQL connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Need More Help?

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Django Database Setup: https://docs.djangoproject.com/en/6.0/ref/databases/
- Stack Overflow: https://stackoverflow.com/questions/tagged/postgresql
