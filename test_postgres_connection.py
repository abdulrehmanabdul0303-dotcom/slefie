#!/usr/bin/env python3
"""
Test PostgreSQL connection and setup database
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_connection():
    """Test different connection methods"""
    
    # Common passwords to try
    passwords = ['postgres', 'admin', 'password', '123456', 'root', '']
    
    print("🔍 Testing PostgreSQL connection...")
    
    for password in passwords:
        try:
            print(f"   Trying password: '{password}'")
            
            # Try to connect
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password=password,
                database='postgres'
            )
            
            print(f"✅ SUCCESS! Connected with password: '{password}'")
            
            # Set up database
            setup_database(conn, password)
            return True
            
        except psycopg2.OperationalError as e:
            if "password authentication failed" in str(e):
                print(f"   ❌ Wrong password: '{password}'")
                continue
            else:
                print(f"   ❌ Connection error: {e}")
                continue
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            continue
    
    print("\n❌ Could not connect with any common password")
    print("\n📋 Manual Setup Required:")
    print("1. Open pgAdmin or psql")
    print("2. Connect as postgres user")
    print("3. Run these commands:")
    print("   CREATE DATABASE photovault_db;")
    print("   CREATE USER photovault_user WITH PASSWORD '3660';")
    print("   GRANT ALL PRIVILEGES ON DATABASE photovault_db TO photovault_user;")
    return False

def setup_database(conn, postgres_password):
    """Set up PhotoVault database"""
    
    try:
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("\n🔧 Setting up PhotoVault database...")
        
        # Create database
        try:
            cursor.execute("CREATE DATABASE photovault_db;")
            print("✅ Database 'photovault_db' created")
        except psycopg2.errors.DuplicateDatabase:
            print("ℹ️  Database 'photovault_db' already exists")
        
        # Create user
        try:
            cursor.execute("CREATE USER photovault_user WITH PASSWORD '3660';")
            print("✅ User 'photovault_user' created")
        except psycopg2.errors.DuplicateObject:
            print("ℹ️  User 'photovault_user' already exists")
        
        # Grant privileges
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE photovault_db TO photovault_user;")
        print("✅ Privileges granted")
        
        # Connect to new database for schema permissions
        cursor.close()
        conn.close()
        
        # Connect to photovault_db
        conn2 = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password=postgres_password,
            database='photovault_db'
        )
        conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor2 = conn2.cursor()
        
        # Set schema permissions
        cursor2.execute("GRANT ALL ON SCHEMA public TO photovault_user;")
        cursor2.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO photovault_user;")
        print("✅ Schema permissions set")
        
        # Install pgvector extension
        try:
            cursor2.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print("✅ pgvector extension installed")
        except Exception as e:
            print(f"⚠️  pgvector extension not available: {e}")
        
        cursor2.close()
        conn2.close()
        
        print("\n🎉 PostgreSQL setup completed successfully!")
        print("\nDatabase Details:")
        print("  Database: photovault_db")
        print("  User: photovault_user")
        print("  Password: 3660")
        print("  Host: 127.0.0.1")
        print("  Port: 5432")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    
    if success:
        print("\n✅ Ready for Django migrations!")
        print("Run: python manage.py migrate")
    else:
        print("\n❌ Manual setup required")
        sys.exit(1)