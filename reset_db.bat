@echo off
REM Reset database and start fresh
echo.
echo ============================================================
echo        WARNING: Database Reset Script
echo ============================================================
echo.
echo This will DELETE all data including:
echo   - All inspections
echo   - All equipment records
echo   - All users (including superuser)
echo   - All templates
echo.
echo You will need to recreate the superuser after this.
echo.
set /p confirm="Are you sure you want to continue? (type YES): "

if not "%confirm%"=="YES" (
    echo.
    echo Reset cancelled.
    pause
    exit /b 0
)

echo.
echo ============================================================
echo Step 1: Installing dependencies...
echo ============================================================
.venv\Scripts\pip.exe install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

echo.
echo ============================================================
echo Step 2: Deleting database file...
echo ============================================================
if exist "db.sqlite3" (
    del /F /Q db.sqlite3
    echo [OK] Database deleted
) else (
    echo [INFO] No database file found
)

echo.
echo ============================================================
echo Step 3: Removing migration files...
echo ============================================================
if exist "inspections\migrations\0*.py" (
    del /F /Q inspections\migrations\0*.py
    echo [OK] Migration files removed
) else (
    echo [INFO] No migration files found
)

echo.
echo ============================================================
echo Step 4: Creating fresh migrations...
echo ============================================================
.venv\Scripts\python.exe manage.py makemigrations
if errorlevel 1 (
    echo [ERROR] Failed to create migrations
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 5: Applying migrations...
echo ============================================================
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 (
    echo [ERROR] Failed to apply migrations
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 6: Creating superuser...
echo ============================================================
echo Please enter superuser credentials:
.venv\Scripts\python.exe manage.py createsuperuser

echo.
echo ============================================================
echo Step 7: Importing templates...
echo ============================================================
if exist "periodic_a922.json" (
    .venv\Scripts\python.exe manage.py import_new_template periodic_a922.json
)
if exist "cat_ab.json" (
    .venv\Scripts\python.exe manage.py import_new_template cat_ab.json
)
if exist "cat_cde.json" (
    .venv\Scripts\python.exe manage.py import_new_template cat_cde.json
)
if exist "uppercontrools.json" (
    .venv\Scripts\python.exe manage.py import_new_template uppercontrools.json
)
if exist "liners.json" (
    .venv\Scripts\python.exe manage.py import_new_template liners.json
)
if exist "ladders.json" (
    .venv\Scripts\python.exe manage.py import_new_template ladders.json
)
if exist "chassis.json" (
    .venv\Scripts\python.exe manage.py import_new_template chassis.json
)
if exist "load_test_structural.json" (
    .venv\Scripts\python.exe manage.py import_new_template load_test_structural.json
)
echo [OK] Templates imported

echo.
echo ============================================================
echo Step 8: Seeding initial data...
echo ============================================================
.venv\Scripts\python.exe manage.py seed_initial_data
if errorlevel 1 (
    echo [ERROR] Failed to seed initial data
    pause
    exit /b 1
)
echo [OK] Initial data seeded

echo.
echo ============================================================
echo Step 9: Populating ANSI references...
echo ============================================================
.venv\Scripts\python.exe populate_ansi_refs.py
if errorlevel 1 (
    echo [ERROR] Failed to populate ANSI references
    pause
    exit /b 1
)
echo [OK] ANSI references populated

echo.
echo ============================================================
echo Step 10: Cleaning media files...
echo ============================================================
if exist "media\defect_photos\*.*" (
    del /F /Q media\defect_photos\*.*
    echo [OK] Defect photos cleared
)
if exist "media\generated_docs\*.*" (
    del /F /Q media\generated_docs\*.*
    echo [OK] Generated documents cleared
)

echo.
echo ============================================================
echo                DATABASE RESET COMPLETE!
echo ============================================================
echo.
echo The database has been reset with:
echo   - Templates loaded
echo   - Seed data (users, customer, company info)
echo.
echo To start the server, run:
echo     run.bat
echo.
pause
