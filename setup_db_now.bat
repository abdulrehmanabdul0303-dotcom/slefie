@echo off
echo === PhotoVault PostgreSQL Setup ===
echo.

set PGPATH=C:\Program Files\PostgreSQL\17\bin

echo Step 1: Testing PostgreSQL connection...
echo Please enter your PostgreSQL 'postgres' user password when prompted.
echo.

REM Create the database
echo Creating database 'photovault_db'...
"%PGPATH%\psql.exe" -U postgres -h localhost -c "CREATE DATABASE photovault_db WITH OWNER = postgres ENCODING = 'UTF8' LC_COLLATE = 'English_United States.1252' LC_CTYPE = 'English_United States.1252' TEMPLATE = template0;"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create database
    pause
    exit /b 1
)

echo SUCCESS: Database created!
echo.

REM Create the user
echo Creating user 'photovault_user'...
"%PGPATH%\psql.exe" -U postgres -h localhost -c "CREATE USER photovault_user WITH PASSWORD '3660';"

echo SUCCESS: User created!
echo.

REM Grant privileges
echo Granting privileges...
"%PGPATH%\psql.exe" -U postgres -h localhost -c "GRANT ALL PRIVILEGES ON DATABASE photovault_db TO photovault_user;"

echo SUCCESS: Privileges granted!
echo.

REM Connect to database and set schema permissions
echo Setting schema permissions...
"%PGPATH%\psql.exe" -U postgres -h localhost -d photovault_db -c "GRANT ALL ON SCHEMA public TO photovault_user; ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO photovault_user;"

echo SUCCESS: Schema permissions set!
echo.

REM Create pgvector extension
echo Installing pgvector extension...
"%PGPATH%\psql.exe" -U postgres -h localhost -d photovault_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo SUCCESS: Extensions installed!
echo.

echo === PostgreSQL Setup Complete! ===
echo.
echo Database Details:
echo   Database: photovault_db
echo   User: photovault_user
echo   Password: 3660
echo   Host: 127.0.0.1
echo   Port: 5432
echo.
echo Next steps:
echo 1. Update your .env file
echo 2. Run Django migrations
echo.
pause