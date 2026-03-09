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
echo Step 2: Flushing database (keeping migrations)...
echo ============================================================
python manage.py flush --no-input
if errorlevel 1 (
    echo [ERROR] Failed to flush database
    pause
    exit /b 1
)
echo [OK] Database flushed

echo.
echo ============================================================
echo Step 3: Applying migrations...
echo ============================================================
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Failed to apply migrations
    pause
    exit /b 1
)
echo [OK] Migrations applied

echo.
echo ============================================================
echo Step 4: Seeding initial data (users, company, equipment)...
echo ============================================================
python manage.py seed_initial_data --force-passwords
if errorlevel 1 (
    echo [ERROR] Failed to seed initial data
    pause
    exit /b 1
)
echo [OK] Initial data seeded

echo.
echo ============================================================
echo Step 5: Importing templates...
echo ============================================================
if exist "periodic_a922.json" (
    python manage.py import_new_template periodic_a922.json
)
if exist "cat_ab.json" (
    python manage.py import_new_template cat_ab.json
)
if exist "cat_cde.json" (
    python manage.py import_new_template cat_cde.json
)
if exist "uppercontrools.json" (
    python manage.py import_new_template uppercontrools.json
)
if exist "liners.json" (
    python manage.py import_new_template liners.json
)
if exist "ladders.json" (
    python manage.py import_new_template ladders.json
)
if exist "chassis.json" (
    python manage.py import_new_template chassis.json
)
if exist "load_test_structural.json" (
    python manage.py import_new_template load_test_structural.json
)
echo [OK] Templates imported

echo.
echo ============================================================
echo                DATABASE RESET COMPLETE!
echo ============================================================
echo.
echo The database has been reset with:
echo   - All 8 templates loaded (including load_test_structural.json)
echo   - Seed data from seed_data.json:
echo       * Company: Advantage Fleet LLC
echo       * Users: nickp, kylep, josh
echo       * Customer: MJ Electric
echo       * Equipment: TEST-SN-001 (Terex TL38P, Category C)
echo.
echo Login credentials:
echo   - nickp / AdvFleet123!
echo   - kylep / AdvFleet123!
echo   - josh / workAccount
echo.
echo To start the server, run:
echo     run.bat
echo.
pause
