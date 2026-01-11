#!/usr/bin/env python3
"""
Create a test user for testing.
"""
import os
import sys
import django

# Add the Django project to the path
sys.path.append('photovault_django')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
django.setup()

from apps.users.models import User
from apps.albums.models import Album

def create_test_user():
    """Create a test user and album."""
    try:
        # Create or get test user
        user, created = User.objects.get_or_create(
            email="photographer@test.com",
            defaults={
                'name': 'Test Photographer',
                'email_verified': True,
                'is_active': True,
            }
        )
        
        if created:
            user.set_password("testpass123")
            user.save()
            print(f"✅ Created test user: {user.email}")
        else:
            user.email_verified = True
            user.is_active = True
            user.save()
            print(f"✅ Updated existing user: {user.email}")
        
        # Create test album
        album, created = Album.objects.get_or_create(
            name="Test Client Album",
            created_by=user,
            defaults={
                'description': 'Test album for client delivery testing'
            }
        )
        
        if created:
            print(f"✅ Created test album: {album.name}")
        else:
            print(f"✅ Found existing album: {album.name}")
        
        print(f"\nTest data ready:")
        print(f"  Email: {user.email}")
        print(f"  Password: testpass123")
        print(f"  Album ID: {album.id}")
        print(f"  Album Name: {album.name}")
        
        return user, album
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None, None

if __name__ == "__main__":
    create_test_user()