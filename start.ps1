# PhotoVault Quick Start Script
# Starts both backend and frontend in separate terminals

Write-Host "🚀 Starting PhotoVault..." -ForegroundColor Green

# Start Backend
Write-Host "Starting Django backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd photovault_django; C:\Users\REHMAN\AppData\Local\Programs\Python\Python311\python.exe manage.py runserver 8000"

# Wait a moment
Start-Sleep -Seconds 2

# Start Frontend  
Write-Host "Starting Next.js frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd photovault-frontend; npm run dev"

Write-Host "✅ PhotoVault started!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Admin: http://localhost:8000/admin/" -ForegroundColor Cyan