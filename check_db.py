#!/usr/bin/env python3
"""
Check database tables.
"""
import os
import sys
import django

# Add the Django project to the path
sys.path.append('photovault_django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
django.setup()

from django.db import connection

def check_tables():
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables in database:")
    for table in tables:
        print(f"  - {table}")
    
    # Check for user-related tables
    user_tables = [t for t in tables if 'user' in t.lower()]
    print(f"\nUser-related tables: {user_tables}")
    
    # Try to find the correct users table
    from apps.users.models import User
    print(f"\nUser model table name: {User._meta.db_table}")
    
    # Check if the table exists
    if User._meta.db_table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {User._meta.db_table};")
        count = cursor.fetchone()[0]
        print(f"Users table has {count} records")
    else:
        print(f"❌ Users table '{User._meta.db_table}' not found!")
    
    cursor.close()

if __name__ == "__main__":
    check_tables()