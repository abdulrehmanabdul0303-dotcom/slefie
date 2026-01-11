#!/usr/bin/env python3
"""
Quick test to create user and test API.
"""
import os
import sys
import django

# Setup Django
os.chdir('photovault_django')
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
django.setup()

from apps.users.models import User
from apps.albums.models import Album

def create_test_data():
    """Create test user and album."""
    try:
        # Create test user
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
            print(f"✅ Created user: {user.email}")
        else:
            user.email_verified = True
            user.is_active = True
            user.save()
            print(f"✅ Updated user: {user.email}")
        
        # Create test album
        album, created = Album.objects.get_or_create(
            name="Test Client Album",
            user=user,
            defaults={
                'description': 'Test album for client delivery'
            }
        )
        
        print(f"✅ Album ready: {album.name} (ID: {album.id})")
        
        # Add test images to album
        from apps.images.models import Image
        
        # Create test images
        for i in range(3):
            image, created = Image.objects.get_or_create(
                user=user,
                original_filename=f"test_image_{i+1}.jpg",
                defaults={
                    'content_type': 'image/jpeg',
                    'size_bytes': 1024000,  # 1MB
                    'width': 1920,
                    'height': 1080,
                    'storage_key': f'test/image_{i+1}.jpg',
                    'checksum_sha256': f'test_hash_{i+1}' + '0' * 50,  # Dummy hash
                }
            )
            
            if created:
                # Add image to album
                album.images.add(image)
                print(f"✅ Added test image: {image.original_filename}")
        
        album.save()
        print(f"✅ Album now has {album.images.count()} images")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_test_data()
    if success:
        print("\n🎉 Test data created successfully!")
        print("Now run: python test_client_delivery.py")
    else:
        print("\n❌ Failed to create test data")