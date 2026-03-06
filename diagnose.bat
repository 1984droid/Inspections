@echo off
REM Diagnostic script to check installation status
echo.
echo ============================================================
echo           A92.2 Inspection App - Diagnostics
echo ============================================================
echo.

echo [1/6] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)
echo.

echo [2/6] Checking database file...
if exist "db.sqlite3" (
    echo [OK] Database file exists
    dir db.sqlite3 | findstr "db.sqlite3"
) else (
    echo [ERROR] Database not found! Run: python manage.py migrate
)
echo.

echo [3/6] Checking migrations...
python manage.py showmigrations --list | findstr "\[X\]" >nul
if errorlevel 1 (
    echo [WARNING] Some migrations may not be applied
) else (
    echo [OK] Migrations appear to be applied
)
echo.

echo [4/6] Checking users...
python manage.py shell -c "from django.contrib.auth.models import User; print('Users:', User.objects.count())"
echo.

echo [5/6] Checking templates...
python manage.py shell -c "from inspections.models import Template; print('Templates:', Template.objects.count())"
echo.

echo [6/6] Testing server startup...
echo Starting server for 3 seconds...
start /B python manage.py runserver 6000 >nul 2>&1
timeout /t 3 /nobreak >nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Administrator:*python*" >nul 2>&1

echo.
echo ============================================================
echo                    Diagnostic Summary
echo ============================================================
echo.
echo If you see:
echo   - Python version OK
echo   - Database file exists
echo   - Migrations applied
echo   - At least 1 user
echo   - 7 templates
echo.
echo Then everything is set up correctly!
echo.
echo ============================================================
echo                    Next Steps
echo ============================================================
echo.
echo 1. Start the server:
echo      run.bat
echo.
echo 2. Open browser to one of these URLs:
echo      http://localhost:6000/login/
echo      http://localhost:6000/admin/
echo.
echo 3. Login with your superuser credentials
echo.
echo If you see errors above, check TROUBLESHOOTING.md
echo.
pause
