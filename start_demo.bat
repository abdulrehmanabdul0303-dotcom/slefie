@echo off
echo ========================================
echo PhotoVault Demo Launcher
echo ========================================

echo.
echo Starting PhotoVault services...
echo.

echo [1/2] Starting Backend Server...
start "PhotoVault Backend" cmd /k "cd photovault_django && .venv\Scripts\activate && python manage.py runserver 0.0.0.0:8000"

echo [2/2] Starting Frontend Server...
timeout /t 3 /nobreak >nul
start "PhotoVault Frontend" cmd /k "cd photovault-frontend && npm run dev"

echo.
echo ========================================
echo Demo Environment Starting...
echo ========================================
echo.
echo Services will be available at:
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Demo Login Credentials:
echo Email: admin@photovault.com
echo Password: admin123
echo.
echo Additional Demo Users:
echo photographer@demo.com / demo123
echo family@demo.com / demo123
echo business@demo.com / demo123
echo.
echo Press any key to open PhotoVault in browser...
pause >nul

start http://localhost:3000

echo.
echo Demo environment is ready!
echo Close this window when done with demo.
pause