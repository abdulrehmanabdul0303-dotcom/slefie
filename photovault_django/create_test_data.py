#!/usr/bin/env python3
"""
Comprehensive Test Data Creation Script for PhotoVault
Creates realistic test data to validate all 47 features
"""
import os
import sys
import django
from pathlib import Path
import secrets
import hashlib
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import base64

# Setup Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.users.models import User, EmailVerificationToken, PasswordResetToken
from apps.images.models import Image as ImageModel, ImageTag, Folder
from apps.albums.models import Album, AlbumImage
from apps.sharing.models import PublicShare, ShareAccess

User = get_user_model()

class TestDataCreator:
    """Creates comprehensive test data for PhotoVault."""
    
    def __init__(self):
        self.users = []
        self.images = []
        self.albums = []
        self.folders = []
        self.share_links = []
        
    def create_test_image(self, width=800, height=600, color='blue', text="Test Image"):
        """Create a test image file."""
        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        # Add text to image
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        draw.text((x, y), text, fill='white', font=font)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return ContentFile(img_bytes.getvalue(), name=f"{text.replace(' ', '_').lower()}.jpg")
    
    def create_users(self):
        """Create test users with different roles and states."""
        print("Creating test users...")
        
        # Admin user
        admin, created = User.objects.get_or_create(
            email='admin@photovault.com',
            defaults={
                'username': 'admin@photovault.com',
                'name': 'Admin User',
                'is_admin': True,
                'email_verified': True
            }
        )
        if created:
            admin.set_password('AdminPass123!')
            admin.save()
        self.users.append(admin)
        
        # Regular verified user
        user1, created = User.objects.get_or_create(
            email='john@example.com',
            defaults={
                'username': 'john@example.com',
                'name': 'John Doe',
                'email_verified': True
            }
        )
        if created:
            user1.set_password('UserPass123!')
            user1.save()
        self.users.append(user1)
        
        # Regular verified user 2
        user2, created = User.objects.get_or_create(
            email='jane@example.com',
            defaults={
                'username': 'jane@example.com',
                'name': 'Jane Smith',
                'email_verified': True
            }
        )
        if created:
            user2.set_password('UserPass123!')
            user2.save()
        self.users.append(user2)
        
        # Unverified user
        user3, created = User.objects.get_or_create(
            email='unverified@example.com',
            defaults={
                'username': 'unverified@example.com',
                'name': 'Unverified User',
                'email_verified': False
            }
        )
        if created:
            user3.set_password('UserPass123!')
            user3.save()
            
            # Create email verification token for unverified user
            EmailVerificationToken.objects.get_or_create(
                user=user3,
                defaults={
                    'token': secrets.token_urlsafe(32),
                    'expires_at': timezone.now() + timedelta(hours=24)
                }
            )
        self.users.append(user3)
        
        # Locked user (simulate failed login attempts)
        locked_user, created = User.objects.get_or_create(
            email='locked@example.com',
            defaults={
                'username': 'locked@example.com',
                'name': 'Locked User',
                'email_verified': True,
                'failed_login_attempts': 5,
                'locked_until': timezone.now() + timedelta(minutes=30)
            }
        )
        if created:
            locked_user.set_password('UserPass123!')
            locked_user.save()
        self.users.append(locked_user)
        
        # Create password reset token for user1 if it doesn't exist
        PasswordResetToken.objects.get_or_create(
            user=user1,
            defaults={
                'token': secrets.token_urlsafe(32),
                'expires_at': timezone.now() + timedelta(hours=1)
            }
        )
        
        print(f"✅ Created/verified {len(self.users)} test users")
    
    def create_folders(self):
        """Create folder structure for organization."""
        print("Creating folder structure...")
        
        user = self.users[1]  # John Doe
        
        # Root folders
        vacation_folder = Folder.objects.get_or_create(
            name="Vacation Photos",
            user=user,
            parent_folder=None
        )[0]
        self.folders.append(vacation_folder)
        
        work_folder = Folder.objects.get_or_create(
            name="Work Events",
            user=user,
            parent_folder=None
        )[0]
        self.folders.append(work_folder)
        
        # Nested folders
        beach_folder = Folder.objects.get_or_create(
            name="Beach Trip 2024",
            user=user,
            parent_folder=vacation_folder
        )[0]
        self.folders.append(beach_folder)
        
        mountain_folder = Folder.objects.get_or_create(
            name="Mountain Hiking",
            user=user,
            parent_folder=vacation_folder
        )[0]
        self.folders.append(mountain_folder)
        
        print(f"✅ Created/verified {len(self.folders)} folders")
    
    def create_images(self):
        """Create test images with various properties."""
        print("Creating test images...")
        
        user1 = self.users[1]  # John Doe
        user2 = self.users[2]  # Jane Smith
        
        # Create images for user1
        image_configs = [
            {"text": "Beach Sunset", "color": "orange", "folder": self.folders[2] if self.folders else None},
            {"text": "Mountain View", "color": "green", "folder": self.folders[3] if self.folders else None},
            {"text": "City Skyline", "color": "blue", "folder": None},
            {"text": "Forest Path", "color": "darkgreen", "folder": None},
            {"text": "Ocean Waves", "color": "cyan", "folder": self.folders[2] if self.folders else None},
            {"text": "Desert Dunes", "color": "yellow", "folder": None},
            {"text": "Snow Peak", "color": "white", "folder": self.folders[3] if self.folders else None},
            {"text": "Flower Garden", "color": "pink", "folder": None},
        ]
        
        for i, config in enumerate(image_configs):
            image_file = self.create_test_image(
                text=config["text"],
                color=config["color"]
            )
            
            # Calculate file hash
            image_file.seek(0)
            file_hash = hashlib.sha256(image_file.read()).hexdigest()
            image_file.seek(0)
            
            image = ImageModel.objects.get_or_create(
                user=user1,
                checksum_sha256=file_hash,
                defaults={
                    'original_filename': f"{config['text'].replace(' ', '_').lower()}.jpg",
                    'content_type': 'image/jpeg',
                    'size_bytes': len(image_file.read()),
                    'folder': config["folder"],
                    'storage_key': f"images/{user1.id}/{file_hash}.jpg",
                    'thumb_storage_key': f"thumbnails/{user1.id}/{file_hash}_thumb.jpg",
                    'width': 800,
                    'height': 600,
                    'taken_at': timezone.now() - timedelta(days=i*10),
                    'camera_make': "Canon" if i % 2 == 0 else "Nikon",
                    'camera_model': f"EOS {5000 + i*100}" if i % 2 == 0 else f"D{7000 + i*100}",
                }
            )[0]
            self.images.append(image)
            
            # Add tags
            tags = [
                ["nature", "landscape", "outdoor"],
                ["mountain", "hiking", "adventure"],
                ["city", "urban", "architecture"],
                ["forest", "trees", "nature"],
                ["ocean", "water", "waves"],
                ["desert", "sand", "dry"],
                ["snow", "winter", "cold"],
                ["flowers", "garden", "colorful"]
            ]
            
            for tag_name in tags[i]:
                ImageTag.objects.get_or_create(
                    image=image,
                    tag=tag_name,
                    defaults={'source': 'user', 'confidence': 1.0}
                )
        
        # Create some images for user2
        for i in range(3):
            image_file = self.create_test_image(
                text=f"User2 Photo {i+1}",
                color="purple"
            )
            
            image_file.seek(0)
            file_hash = hashlib.sha256(image_file.read()).hexdigest()
            image_file.seek(0)
            
            image = ImageModel.objects.get_or_create(
                user=user2,
                checksum_sha256=file_hash,
                defaults={
                    'original_filename': f"user2_photo_{i+1}.jpg",
                    'content_type': 'image/jpeg',
                    'size_bytes': len(image_file.read()),
                    'storage_key': f"images/{user2.id}/{file_hash}.jpg",
                    'thumb_storage_key': f"thumbnails/{user2.id}/{file_hash}_thumb.jpg",
                    'width': 800,
                    'height': 600,
                    'taken_at': timezone.now() - timedelta(days=i*5)
                }
            )[0]
            self.images.append(image)
        
        print(f"✅ Created {len(self.images)} test images")
    
    def create_albums(self):
        """Create test albums with images."""
        print("Creating test albums...")
        
        user1 = self.users[1]  # John Doe
        user2 = self.users[2]  # Jane Smith
        
        # User1 albums
        vacation_album = Album.objects.get_or_create(
            name="Summer Vacation 2024",
            user=user1,
            defaults={
                'description': "Best moments from our summer vacation",
                'album_type': 'manual'
            }
        )[0]
        self.albums.append(vacation_album)
        
        nature_album = Album.objects.get_or_create(
            name="Nature Photography",
            user=user1,
            defaults={
                'description': "Collection of nature photographs",
                'album_type': 'manual'
            }
        )[0]
        self.albums.append(nature_album)
        
        # User2 album
        personal_album = Album.objects.get_or_create(
            name="Personal Memories",
            user=user2,
            defaults={
                'description': "My personal photo collection",
                'album_type': 'manual'
            }
        )[0]
        self.albums.append(personal_album)
        
        # Add images to albums
        user1_images = [img for img in self.images if img.user == user1]
        user2_images = [img for img in self.images if img.user == user2]
        
        # Add first 4 images to vacation album
        for i, image in enumerate(user1_images[:4]):
            AlbumImage.objects.create(
                album=vacation_album,
                image=image,
                order=i
            )
        
        # Set cover image
        if user1_images:
            vacation_album.cover_image = user1_images[0]
            vacation_album.save()
        
        # Add nature images to nature album
        nature_images = [img for img in user1_images if any(tag in img.original_filename.lower() for tag in ['mountain', 'forest', 'ocean', 'flower'])]
        for i, image in enumerate(nature_images):
            AlbumImage.objects.create(
                album=nature_album,
                image=image,
                order=i
            )
        
        if nature_images:
            nature_album.cover_image = nature_images[0]
            nature_album.save()
        
        # Add user2 images to personal album
        for i, image in enumerate(user2_images):
            AlbumImage.objects.create(
                album=personal_album,
                image=image,
                order=i
            )
        
        if user2_images:
            personal_album.cover_image = user2_images[0]
            personal_album.save()
        
        print(f"✅ Created {len(self.albums)} test albums")
    
    def create_share_links(self):
        """Create test share links with various configurations."""
        print("Creating share links...")
        
        user1 = self.users[1]  # John Doe
        
        if not self.albums:
            print("⚠️ No albums available for sharing")
            return
        
        # Public share link (no expiration)
        public_share = PublicShare.objects.create(
            album=self.albums[1],  # Nature album
            created_by=user1,
            scope='download',
            expires_at=timezone.now() + timedelta(days=30),
            require_face=False,
            share_type='PUBLIC'
        )
        public_share.generate_token()
        public_share.save()
        self.share_links.append(public_share)
        
        # Private share link with expiration
        private_share = PublicShare.objects.create(
            album=self.albums[0],  # Vacation album
            created_by=user1,
            scope='view',
            expires_at=timezone.now() + timedelta(days=7),
            max_views=10,
            require_face=True,
            share_type='FACE_CLAIM'
        )
        private_share.generate_token()
        private_share.save()
        self.share_links.append(private_share)
        
        # Expired share link
        expired_share = PublicShare.objects.create(
            album=self.albums[0],
            created_by=user1,
            scope='download',
            expires_at=timezone.now() - timedelta(days=1),
            max_views=5,
            require_face=False,
            share_type='PUBLIC'
        )
        expired_share.generate_token()
        expired_share.save()
        self.share_links.append(expired_share)
        
        # Create some access logs
        ShareAccess.objects.create(
            share=public_share,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        
        ShareAccess.objects.create(
            share=private_share,
            ip_address="10.0.0.50",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        )
        
        print(f"✅ Created {len(self.share_links)} share links")
    
    def create_all_test_data(self):
        """Create all test data."""
        print("🚀 Creating comprehensive test data for PhotoVault...")
        print("=" * 60)
        
        try:
            self.create_users()
            self.create_folders()
            self.create_images()
            self.create_albums()
            self.create_share_links()
            
            print("\n" + "=" * 60)
            print("🎉 TEST DATA CREATION COMPLETE!")
            print("=" * 60)
            print(f"📊 SUMMARY:")
            print(f"   👥 Users: {len(self.users)}")
            print(f"   📁 Folders: {len(self.folders)}")
            print(f"   📸 Images: {len(self.images)}")
            print(f"   📚 Albums: {len(self.albums)}")
            print(f"   🔗 Share Links: {len(self.share_links)}")
            print("\n🔑 TEST ACCOUNTS:")
            print("   Admin: admin@photovault.com / AdminPass123!")
            print("   User1: john@example.com / UserPass123!")
            print("   User2: jane@example.com / UserPass123!")
            print("   Unverified: unverified@example.com / UserPass123!")
            print("   Locked: locked@example.com / UserPass123!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating test data: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main function to create test data."""
    creator = TestDataCreator()
    success = creator.create_all_test_data()
    
    if success:
        print("\n✅ Ready for comprehensive feature testing!")
    else:
        print("\n❌ Test data creation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()