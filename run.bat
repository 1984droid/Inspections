@echo off
REM Start Django development server on port 3000
echo.
echo ============================================================
echo       Starting A92.2 Inspection App on port 3000
echo ============================================================
echo.
echo Server will be available at:
echo   http://localhost:3000
echo   http://127.0.0.1:3000
echo.
echo Press CTRL+C to stop the server
echo.
python manage.py runserver 3000
