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
echo Step 1: Deleting database file...
echo ============================================================
if exist "db.sqlite3" (
    del /F /Q db.sqlite3
    echo [OK] Database deleted
) else (
    echo [INFO] No database file found
)

echo.
echo ============================================================
echo Step 2: Removing migration files...
echo ============================================================
if exist "inspections\migrations\0*.py" (
    del /F /Q inspections\migrations\0*.py
    echo [OK] Migration files removed
) else (
    echo [INFO] No migration files found
)

echo.
echo ============================================================
echo Step 3: Creating fresh migrations...
echo ============================================================
python manage.py makemigrations
if errorlevel 1 (
    echo [ERROR] Failed to create migrations
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 4: Applying migrations...
echo ============================================================
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Failed to apply migrations
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Step 5: Creating superuser...
echo ============================================================
echo Please enter superuser credentials:
python manage.py createsuperuser

echo.
echo ============================================================
echo Step 6: Importing templates...
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
echo [OK] Templates imported

echo.
echo ============================================================
echo Step 7: Cleaning media files...
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
echo The database has been reset to a clean state.
echo.
echo To start the server, run:
echo     run.bat
echo.
pause
