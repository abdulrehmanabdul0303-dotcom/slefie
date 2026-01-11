-- Fix permissions for PhotoVault database
\c photovault

-- Grant all privileges on existing tables to photovault_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO photovault_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO photovault_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO photovault_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO photovault_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO photovault_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO photovault_user;

-- Make photovault_user owner of existing tables
ALTER TABLE IF EXISTS users OWNER TO photovault_user;
ALTER TABLE IF EXISTS user OWNER TO photovault_user;
ALTER TABLE IF EXISTS image OWNER TO photovault_user;
ALTER TABLE IF EXISTS album OWNER TO photovault_user;
ALTER TABLE IF EXISTS albumimage OWNER TO photovault_user;
ALTER TABLE IF EXISTS face OWNER TO photovault_user;
ALTER TABLE IF EXISTS personcluster OWNER TO photovault_user;
ALTER TABLE IF EXISTS person_clusters OWNER TO photovault_user;

-- Show current permissions
\dp