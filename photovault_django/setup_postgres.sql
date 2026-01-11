-- PostgreSQL setup script for PhotoVault
-- Run this as postgres superuser

-- Create user
CREATE USER photovault_user WITH PASSWORD '3660';

-- Create database
CREATE DATABASE photovault OWNER photovault_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE photovault TO photovault_user;

-- Connect to the photovault database
\c photovault

-- Create pgvector extension (for AI features)
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO photovault_user;
GRANT CREATE ON SCHEMA public TO photovault_user;

-- Show created objects
\l
\du