# PostgreSQL Setup Script for PhotoVault
# This script will help you set up the PostgreSQL database

Write-Host "=== PhotoVault PostgreSQL Setup ===" -ForegroundColor Green
Write-Host ""

# Check if PostgreSQL is running
$pgService = Get-Service -Name "*postgresql*" -ErrorAction SilentlyContinue
if ($pgService -and $pgService.Status -eq "Running") {
    Write-Host "✅ PostgreSQL service is running" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL service is not running" -ForegroundColor Red
    Write-Host "Please start PostgreSQL service first" -ForegroundColor Yellow
    exit 1
}

# PostgreSQL paths
$pgPath = "C:\Program Files\PostgreSQL\17\bin"
$psqlPath = "$pgPath\psql.exe"

if (!(Test-Path $psqlPath)) {
    Write-Host "❌ PostgreSQL not found at expected location" -ForegroundColor Red
    Write-Host "Please check your PostgreSQL installation" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found PostgreSQL at: $pgPath" -ForegroundColor Green
Write-Host ""

# Prompt for postgres password
Write-Host "Please enter the PostgreSQL 'postgres' user password:" -ForegroundColor Yellow
$pgPassword = Read-Host -AsSecureString
$env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pgPassword))

Write-Host ""
Write-Host "Setting up PhotoVault database..." -ForegroundColor Yellow

# Test connection first
Write-Host "Testing PostgreSQL connection..." -ForegroundColor Yellow
$testResult = & $psqlPath -U postgres -h localhost -c "SELECT version();" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL connection successful" -ForegroundColor Green
    
    # Run setup script
    Write-Host "Creating database and user..." -ForegroundColor Yellow
    & $psqlPath -U postgres -h localhost -f "photovault_django/setup_postgres.sql"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database setup completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Database Details:" -ForegroundColor Cyan
        Write-Host "  Database: photovault" -ForegroundColor White
        Write-Host "  User: photovault_user" -ForegroundColor White
        Write-Host "  Password: 3660" -ForegroundColor White
        Write-Host "  Host: 127.0.0.1" -ForegroundColor White
        Write-Host "  Port: 5432" -ForegroundColor White
        Write-Host ""
        Write-Host "You can now update your .env file to use PostgreSQL!" -ForegroundColor Green
    } else {
        Write-Host "❌ Database setup failed" -ForegroundColor Red
    }
} else {
    Write-Host "❌ PostgreSQL connection failed" -ForegroundColor Red
    Write-Host "Error: $testResult" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "1. Check if the postgres password is correct" -ForegroundColor White
    Write-Host "2. Make sure PostgreSQL service is running" -ForegroundColor White
    Write-Host "3. Check if port 5432 is available" -ForegroundColor White
}

# Clear password from environment
$env:PGPASSWORD = $null