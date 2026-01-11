@echo off
echo ========================================
echo PhotoVault Quick Setup for Windows
echo ========================================

echo.
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 16+ from nodejs.org
    pause
    exit /b 1
)

echo [3/6] Setting up Python virtual environment...
cd photovault_django
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt

echo [4/6] Setting up database...
python manage.py makemigrations
python manage.py migrate

echo [5/6] Creating admin user...
echo Creating admin user (admin@photovault.com / admin123)
python manage.py shell -c "from apps.users.models import User; User.objects.create_superuser('admin@photovault.com', 'admin123', name='Admin User', email_verified=True) if not User.objects.filter(email='admin@photovault.com').exists() else print('Admin user already exists')"

echo [6/6] Setting up frontend...
cd ..\photovault-frontend
npm install

echo.
echo ========================================
echo Setup Complete! 
echo ========================================
echo.
echo To start the application:
echo 1. Backend:  cd photovault_django ^&^& .venv\Scripts\activate ^&^& python manage.py runserver 0.0.0.0:8000
echo 2. Frontend: cd photovault-frontend ^&^& npm run dev
echo.
echo Login credentials:
echo Email: admin@photovault.com
echo Password: admin123
echo.
echo Backend URL: http://localhost:8000
echo Frontend URL: http://localhost:3000
echo.
pause