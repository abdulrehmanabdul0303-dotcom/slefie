@echo off
echo === PhotoVault PostgreSQL Setup ===
echo.

REM Set PostgreSQL path
set PGPATH=C:\Program Files\PostgreSQL\17\bin

REM Check if psql exists
if not exist "%PGPATH%\psql.exe" (
    echo ERROR: PostgreSQL not found at %PGPATH%
    echo Please check your PostgreSQL installation
    pause
    exit /b 1
)

echo Found PostgreSQL at: %PGPATH%
echo.

REM Prompt for password
set /p PGPASSWORD=Enter PostgreSQL 'postgres' user password: 

echo.
echo Testing connection...

REM Test connection
"%PGPATH%\psql.exe" -U postgres -h localhost -c "SELECT 1;" >nul 2>&1

if %errorlevel% neq 0 (
    echo ERROR: Cannot connect to PostgreSQL
    echo Please check:
    echo 1. PostgreSQL service is running
    echo 2. Password is correct
    echo 3. Port 5432 is available
    pause
    exit /b 1
)

echo SUCCESS: Connected to PostgreSQL
echo.
echo Creating database and user...

REM Run setup script
"%PGPATH%\psql.exe" -U postgres -h localhost -f "photovault_django\setup_postgres.sql"

if %errorlevel% eq 0 (
    echo.
    echo SUCCESS: Database setup completed!
    echo.
    echo Database Details:
    echo   Database: photovault
    echo   User: photovault_user
    echo   Password: 3660
    echo   Host: 127.0.0.1
    echo   Port: 5432
    echo.
    echo You can now update your .env file to use PostgreSQL!
) else (
    echo ERROR: Database setup failed
)

REM Clear password
set PGPASSWORD=

echo.
pause