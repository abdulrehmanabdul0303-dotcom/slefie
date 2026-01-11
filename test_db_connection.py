#!/usr/bin/env python3
"""
Test PhotoVault PostgreSQL connection
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('photovault_django')
os.chdir('photovault_django')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')

try:
    django.setup()
    
    from django.db import connection
    from django.core.management.color import no_style
    
    print("🔍 Testing PhotoVault database connection...")
    
    # Test connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL!")
        print(f"   Version: {version}")
        
        # Test database name
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"   Database: {db_name}")
        
        # Test user
        cursor.execute("SELECT current_user;")
        user = cursor.fetchone()[0]
        print(f"   User: {user}")
        
    print("\n🎉 Database connection successful!")
    print("✅ Ready to run migrations!")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n📋 Troubleshooting:")
    print("1. Make sure you completed all pgAdmin steps")
    print("2. Check database name: 'photovault'")
    print("3. Check user: 'photovault_user' with password '3660'")
    print("4. Verify user has privileges on the database")
    sys.exit(1)