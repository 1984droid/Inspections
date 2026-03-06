@echo off
REM Setup script for A92.2 Inspection App (Windows)
echo.
echo ============================================================
echo          A92.2 Inspection App - Quick Setup
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.14+
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check if manage.py exists
if not exist "manage.py" (
    echo [ERROR] manage.py not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

echo [OK] Project directory confirmed
echo.

REM Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found
    if exist ".env.example" (
        echo [INFO] Copying .env.example to .env
        copy ".env.example" ".env"
        echo [OK] Created .env file
        echo [WARNING] Please edit .env with your database credentials!
        echo.
        pause
    ) else (
        echo [ERROR] No .env.example found!
        pause
        exit /b 1
    )
)

REM Install dependencies
echo ============================================================
echo Installing dependencies...
echo ============================================================
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some dependencies may have failed to install
    pause
) else (
    echo [OK] Dependencies installed
)
echo.

REM Run migrations
echo ============================================================
echo Creating database migrations...
echo ============================================================
python manage.py makemigrations
if errorlevel 1 (
    echo [ERROR] Failed to create migrations
    pause
    exit /b 1
)
echo [OK] Migrations created
echo.

echo ============================================================
echo Running migrations...
echo ============================================================
python manage.py migrate
if errorlevel 1 (
    echo [ERROR] Failed to run migrations
    echo [INFO] Make sure PostgreSQL is running and .env is configured correctly
    pause
    exit /b 1
)
echo [OK] Migrations applied
echo.

REM Create superuser
echo ============================================================
echo Create superuser account
echo ============================================================
echo Follow the prompts to create an admin user...
echo.
python manage.py createsuperuser
echo.

REM Import templates
echo ============================================================
echo Importing A92.2 templates...
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

REM Create media directories
echo ============================================================
echo Creating media directories...
echo ============================================================
if not exist "media\defect_photos" mkdir "media\defect_photos"
if not exist "media\generated_docs" mkdir "media\generated_docs"
echo [OK] Media directories created
echo.

REM Final message
echo ============================================================
echo                    SETUP COMPLETE!
echo ============================================================
echo.
echo To start the development server, run:
echo.
echo     run.bat
echo.
echo Or manually:
echo     python manage.py runserver 6000
echo.
echo Then open your browser to: http://localhost:6000
echo.
echo Login with the superuser credentials you just created.
echo.
echo Check README.md for detailed usage instructions.
echo.
pause
