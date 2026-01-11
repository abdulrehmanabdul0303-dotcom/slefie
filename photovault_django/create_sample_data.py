#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive sample data generator for PhotoVault project.

This script creates realistic sample data to test all features:
- Users (photographers and clients)
- Folders and Albums
- Images with metadata
- Sharing links
- Memory Time Machine data
- Flashback Reels
- Feature flags
- Audit logs

Usage:
    python manage.py shell < create_sample_data.py
    # OR
    python create_sample_data.py
"""

import os
import sys
import django
from datetime import date, datetime, timedelta
import random
import json

# Setup Django
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
    django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from apps.images.models import Image, Folder
from apps.albums.models import Album
from apps.sharing.models import PublicShare
from apps.memories.models import Memory, FlashbackReel, MemoryEngagement, MemoryPreferences
from apps.feature_flags.models import FeatureFlag
from apps.audit.models import AuditEvent

User = get_user_model()

class SampleDataGenerator:
    """Generates comprehensive sample data for PhotoVault"""
    
    def __init__(self):
        self.users = []
        self.folders = []
        self.albums = []
        self.images = []
        self.shares = []
        self.memories = []
        self.reels = []
        
        # Sample data configurations
        self.camera_makes = ['Canon', 'Nikon', 'Sony', 'Fujifilm', 'Leica', 'Olympus']
        self.camera_models = {
            'Canon': ['EOS R5', 'EOS 5D Mark IV', '1DX Mark III', 'EOS R6'],
            'Nikon': ['D850', 'Z7 II', 'D780', 'Z6 II'],
            'Sony': ['A7R IV', 'A7 III', 'A9 II', 'FX3'],
            'Fujifilm': ['X-T4', 'GFX 100S', 'X-Pro3', 'X100V'],
            'Leica': ['M10-R', 'SL2', 'Q2', 'M11'],
            'Olympus': ['OM-D E-M1X', 'OM-D E-M5 III', 'PEN-F', 'OM-D E-M10 IV']
        }
        
        self.locations = [
            'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
            'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
            'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Jacksonville, FL',
            'Paris, France', 'London, UK', 'Tokyo, Japan', 'Sydney, Australia',
            'Rome, Italy', 'Barcelona, Spain', 'Amsterdam, Netherlands', 'Berlin, Germany'
        ]
        
        self.photo_subjects = [
            'Portrait', 'Landscape', 'Wedding', 'Event', 'Street Photography',
            'Architecture', 'Nature', 'Wildlife', 'Fashion', 'Product',
            'Food', 'Travel', 'Sports', 'Concert', 'Family', 'Corporate'
        ]
        
        self.album_themes = [
            'Wedding Collection', 'Portrait Session', 'Travel Adventures',
            'Corporate Event', 'Family Gathering', 'Nature Photography',
            'Street Art', 'Architecture Study', 'Fashion Shoot', 'Product Catalog'
        ]
    
    def generate_all_data(self):
        """Generate all sample data"""
        print("🚀 Starting comprehensive sample data generation...")
        
        # Clear existing data (optional - comment out to preserve existing data)
        self.clear_existing_data()
        
        # Generate core data
        self.create_feature_flags()
        self.create_users()
        self.create_folders()
        self.create_images()
        self.create_albums()
        self.create_sharing_links()
        
        # Generate Memory Time Machine data
        self.create_memories()
        self.create_memory_engagements()
        self.create_flashback_reels()
        self.create_memory_preferences()
        
        # Generate audit logs
        self.create_audit_logs()
        
        print("\n✅ Sample data generation completed!")
        self.print_summary()
    
    def clear_existing_data(self):
        """Clear existing data (use with caution!)"""
        print("🧹 Clearing existing data...")
        
        # Clear in reverse dependency order
        AuditEvent.objects.all().delete()
        MemoryEngagement.objects.all().delete()
        FlashbackReel.objects.all().delete()
        Memory.objects.all().delete()
        MemoryPreferences.objects.all().delete()
        PublicShare.objects.all().delete()
        Album.objects.all().delete()
        Image.objects.all().delete()
        Folder.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()  # Keep superuser
        FeatureFlag.objects.all().delete()
        
        print("   Existing data cleared.")
    
    def create_feature_flags(self):
        """Create feature flags for testing"""
        print("🏁 Creating feature flags...")
        
        flags = [
            {
                'key': 'memory_time_machine',
                'name': 'Memory Time Machine',
                'description': 'Enable Memory Time Machine feature',
                'is_active': True,
                'rollout_percentage': 100,
                'environments': ['DEVELOPMENT', 'STAGING', 'PRODUCTION']
            },
            {
                'key': 'flashback_reels',
                'name': 'Flashback Reels',
                'description': 'Enable Flashback Reel generation',
                'is_active': True,
                'rollout_percentage': 100,
                'environments': ['DEVELOPMENT', 'STAGING', 'PRODUCTION']
            },
            {
                'key': 'client_delivery_mode',
                'name': 'Client Delivery Mode',
                'description': 'Enable client delivery features',
                'is_active': True,
                'rollout_percentage': 100,
                'environments': ['DEVELOPMENT', 'STAGING', 'PRODUCTION']
            },
            {
                'key': 'advanced_sharing',
                'name': 'Advanced Sharing',
                'description': 'Enable advanced sharing options',
                'is_active': True,
                'rollout_percentage': 80,
                'environments': ['DEVELOPMENT', 'STAGING', 'PRODUCTION']
            },
            {
                'key': 'ai_photo_tagging',
                'name': 'AI Photo Tagging',
                'description': 'Enable AI-powered photo tagging',
                'is_active': False,
                'rollout_percentage': 25,
                'environments': ['DEVELOPMENT', 'STAGING']
            }
        ]
        
        for flag_data in flags:
            flag, created = FeatureFlag.objects.get_or_create(
                key=flag_data['key'],
                defaults=flag_data
            )
            if created:
                print(f"   Created feature flag: {flag.key}")
    
    def create_users(self):
        """Create sample users with different roles"""
        print("👥 Creating users...")
        
        # Professional photographers
        photographers = [
            {
                'username': 'john_photographer',
                'email': 'john@photoexample.com',
                'name': 'John Smith',
                'role': 'photographer',
                'business_name': 'Smith Photography Studio',
                'bio': 'Professional wedding and portrait photographer with 10+ years experience.'
            },
            {
                'username': 'sarah_creative',
                'email': 'sarah@creativestudio.com',
                'name': 'Sarah Johnson',
                'role': 'photographer',
                'business_name': 'Creative Vision Studio',
                'bio': 'Specializing in fashion and commercial photography.'
            },
            {
                'username': 'mike_events',
                'email': 'mike@eventphoto.com',
                'name': 'Mike Davis',
                'role': 'photographer',
                'business_name': 'Davis Event Photography',
                'bio': 'Corporate and event photographer serving the metropolitan area.'
            }
        ]
        
        # Client users
        clients = [
            {
                'username': 'emma_client',
                'email': 'emma@example.com',
                'name': 'Emma Wilson',
                'role': 'client'
            },
            {
                'username': 'david_client',
                'email': 'david@example.com',
                'name': 'David Brown',
                'role': 'client'
            }
        ]
        
        all_users = photographers + clients
        
        for user_data in all_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'is_active': True,
                    'email_verified': True,
                    'dek_encrypted_b64': 'sample_encrypted_key_' + user_data['username']
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
                print(f"   Created user: {user.username} ({user_data['role']})")
            
            # Add to users list regardless of whether it was created or already existed
            self.users.append(user)
    
    def create_folders(self):
        """Create folder structure for photographers"""
        print("📁 Creating folders...")
        
        photographers = [u for u in self.users if 'photographer' in u.username]
        
        folder_structures = [
            'Weddings/2024', 'Weddings/2023', 'Portraits/Studio', 'Portraits/Outdoor',
            'Events/Corporate', 'Events/Private', 'Travel/Europe', 'Travel/Asia',
            'Nature/Landscapes', 'Nature/Wildlife', 'Architecture/Modern', 'Architecture/Historic',
            'Fashion/Studio', 'Fashion/Location', 'Products/Commercial', 'Products/Lifestyle'
        ]
        
        for photographer in photographers:
            for folder_path in folder_structures:
                folder_name = folder_path.split('/')[-1]
                parent_name = folder_path.split('/')[0] if '/' in folder_path else None
                
                # Create parent folder if needed
                parent_folder = None
                if parent_name:
                    parent_folder, _ = Folder.objects.get_or_create(
                        name=parent_name,
                        user=photographer,
                        parent_folder=None
                    )
                
                # Create subfolder
                folder, created = Folder.objects.get_or_create(
                    name=folder_name,
                    user=photographer,
                    parent_folder=parent_folder
                )
                
                if created:
                    self.folders.append(folder)
        
        print(f"   Created {len(self.folders)} folders")
    
    def create_images(self):
        """Create sample images with realistic metadata"""
        print("📸 Creating images...")
        
        photographers = [u for u in self.users if 'photographer' in u.username]
        
        # Create images for each photographer
        for photographer in photographers:
            user_folders = Folder.objects.filter(user=photographer)
            
            # Create 50-100 images per photographer
            num_images = random.randint(50, 100)
            
            for i in range(num_images):
                folder = random.choice(user_folders)
                camera_make = random.choice(self.camera_makes)
                camera_model = random.choice(self.camera_models[camera_make])
                location = random.choice(self.locations)
                subject = random.choice(self.photo_subjects)
                
                # Generate realistic date (within last 3 years)
                days_ago = random.randint(1, 1095)  # 3 years
                taken_date = timezone.now() - timedelta(days=days_ago)
                
                # Generate realistic EXIF data
                exif_data = {
                    'make': camera_make,
                    'model': camera_model,
                    'lens': f'{random.randint(24, 200)}mm f/{random.choice([1.4, 1.8, 2.8, 4.0])}',
                    'focal_length': f'{random.randint(24, 200)}mm',
                    'aperture': f'f/{random.choice([1.4, 1.8, 2.8, 4.0, 5.6, 8.0])}',
                    'shutter_speed': f'1/{random.choice([60, 125, 250, 500, 1000])}',
                    'iso': random.choice([100, 200, 400, 800, 1600, 3200]),
                    'flash': random.choice(['No Flash', 'Flash', 'Auto'])
                }
                
                image = Image.objects.create(
                    user=photographer,
                    folder=folder,
                    original_filename=f'{subject.lower().replace(" ", "_")}_{i+1:04d}.jpg',
                    storage_key=f'{photographer.username}/{folder.name}/{subject.lower().replace(" ", "_")}_{i+1:04d}.jpg',
                    checksum_sha256=f'{photographer.id:02d}{folder.id:04d}{i:058d}',  # Unique checksum
                    size_bytes=random.randint(2_000_000, 15_000_000),  # 2-15MB
                    width=random.choice([3840, 4000, 5472, 6000, 7360]),
                    height=random.choice([2160, 2667, 3648, 4000, 4912]),
                    content_type='image/jpeg',
                    taken_at=taken_date,
                    camera_make=camera_make,
                    camera_model=camera_model,
                    location_text=location,
                    gps_lat=random.uniform(25.0, 49.0),  # US latitude range
                    gps_lng=random.uniform(-125.0, -66.0),  # US longitude range
                    exif_data=exif_data
                )
                
                self.images.append(image)
        
        print(f"   Created {len(self.images)} images")
    
    def create_albums(self):
        """Create albums and add images to them"""
        print("📚 Creating albums...")
        
        photographers = [u for u in self.users if 'photographer' in u.username]
        
        for photographer in photographers:
            user_images = [img for img in self.images if img.user == photographer]
            
            # Create 5-10 albums per photographer
            num_albums = random.randint(5, 10)
            
            for i in range(num_albums):
                theme = random.choice(self.album_themes)
                
                album = Album.objects.create(
                    name=f'{theme} - {random.choice(["Spring", "Summer", "Fall", "Winter"])} {random.randint(2022, 2024)}',
                    user=photographer,
                    description=f'Professional {theme.lower()} featuring high-quality photography.',
                    album_type='manual',
                    cover_image=None  # Will set after adding images
                )
                
                # Add 10-30 random images to album
                album_images = random.sample(user_images, min(random.randint(10, 30), len(user_images)))
                album.images.set(album_images)
                
                # Set cover image
                if album_images:
                    album.cover_image = random.choice(album_images)
                    album.save()
                
                self.albums.append(album)
        
        print(f"   Created {len(self.albums)} albums")
    
    def create_sharing_links(self):
        """Create public sharing links"""
        print("🔗 Creating sharing links...")
        
        # Create shares for random albums
        shareable_albums = random.sample(self.albums, min(len(self.albums) // 2, 20))
        
        for album in shareable_albums:
            # Create expiration date (1 month to 1 year from now)
            expires_at = timezone.now() + timedelta(days=random.randint(30, 365))
            
            # Generate a simple token hash (in production this would be properly hashed)
            import hashlib
            token = f'share_{album.id}_{random.randint(1000, 9999)}'
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            share = PublicShare.objects.create(
                album=album,
                created_by=album.user,
                token_hash=token_hash,
                raw_token=token,
                scope=random.choice(['view', 'download']),
                expires_at=expires_at,
                max_views=random.choice([None, 100, 500, 1000]),
                watermark_enabled=random.choice([True, False]),
                share_type='PUBLIC'
            )
            
            # Simulate some views
            share.total_views = random.randint(0, 50)
            share.view_count = share.total_views
            share.unique_visitors = random.randint(0, share.total_views)
            share.last_accessed = timezone.now() - timedelta(days=random.randint(0, 30))
            share.save()
            
            self.shares.append(share)
        
        print(f"   Created {len(self.shares)} sharing links")
    
    def create_memories(self):
        """Create Memory Time Machine memories"""
        print("🧠 Creating memories...")
        
        photographers = [u for u in self.users if 'photographer' in u.username]
        
        for photographer in photographers:
            user_images = [img for img in self.images if img.user == photographer]
            
            # Create memories for various dates
            memory_dates = []
            for days_back in range(1, 100):  # Last 100 days
                if random.random() < 0.1:  # 10% chance per day
                    memory_dates.append(date.today() - timedelta(days=days_back))
            
            for memory_date in memory_dates:
                # Find images from same date in previous years
                memory_images = []
                for img in user_images:
                    if img.taken_at:
                        img_date = img.taken_at.date()
                        if (img_date.month == memory_date.month and 
                            img_date.day == memory_date.day and 
                            img_date.year < memory_date.year):
                            memory_images.append(img)
                
                if len(memory_images) >= 3:  # Need at least 3 images for a memory
                    # Calculate significance score
                    significance_score = random.uniform(2.0, 8.0)
                    
                    memory = Memory.objects.create(
                        user=photographer,
                        target_date=memory_date,
                        significance_score=significance_score,
                        engagement_count=random.randint(0, 10)
                    )
                    
                    # Add photos to memory
                    selected_images = random.sample(memory_images, min(len(memory_images), 15))
                    for order, img in enumerate(selected_images):
                        from apps.memories.models import MemoryPhoto
                        MemoryPhoto.objects.create(
                            memory=memory,
                            photo=img,
                            significance_score=random.uniform(1.0, 5.0),
                            order=order
                        )
                    
                    self.memories.append(memory)
        
        print(f"   Created {len(self.memories)} memories")
    
    def create_memory_engagements(self):
        """Create memory engagement data"""
        print("💝 Creating memory engagements...")
        
        engagement_types = ['view', 'share', 'like', 'download']
        
        for memory in self.memories:
            # Create 0-20 engagements per memory
            num_engagements = random.randint(0, 20)
            
            for _ in range(num_engagements):
                MemoryEngagement.objects.create(
                    memory=memory,
                    interaction_type=random.choice(engagement_types),
                    timestamp=timezone.now() - timedelta(
                        days=random.randint(0, 30),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    ),
                    ip_address=f'192.168.1.{random.randint(1, 254)}',
                    user_agent='Mozilla/5.0 (Sample Data Generator)'
                )
        
        print(f"   Created memory engagements")
    
    def create_flashback_reels(self):
        """Create flashback reels"""
        print("🎬 Creating flashback reels...")
        
        photographers = [u for u in self.users if 'photographer' in u.username]
        
        for photographer in photographers:
            user_images = [img for img in self.images if img.user == photographer]
            
            # Create 2-5 reels per photographer
            num_reels = random.randint(2, 5)
            
            for i in range(num_reels):
                # Random date range for reel
                end_date = date.today() - timedelta(days=random.randint(30, 365))
                start_date = end_date - timedelta(days=random.randint(30, 90))
                
                reel = FlashbackReel.objects.create(
                    user=photographer,
                    title=f'{random.choice(["Memories", "Journey", "Collection", "Highlights"])} from {start_date.strftime("%B %Y")}',
                    duration=random.choice([30, 45, 60, 90]),
                    theme=random.choice(['classic', 'modern', 'vintage', 'cinematic']),
                    status=random.choice(['completed', 'completed', 'completed', 'processing', 'pending']),
                    start_date=start_date,
                    end_date=end_date,
                    photo_count=random.randint(10, 20)
                )
                
                # Add random photos to reel
                reel_images = random.sample(user_images, min(reel.photo_count, len(user_images)))
                reel.photos.set(reel_images)
                
                # Set completion date for completed reels
                if reel.status == 'completed':
                    reel.completed_at = timezone.now() - timedelta(days=random.randint(1, 30))
                    reel.save()
                
                self.reels.append(reel)
        
        print(f"   Created {len(self.reels)} flashback reels")
    
    def create_memory_preferences(self):
        """Create memory preferences for users"""
        print("⚙️ Creating memory preferences...")
        
        for user in self.users:
            if 'photographer' in user.username:
                from apps.memories.models import MemoryPreferences
                
                MemoryPreferences.objects.get_or_create(
                    user=user,
                    defaults={
                        'enable_notifications': random.choice([True, False]),
                        'notification_frequency': random.choice(['daily', 'weekly', 'monthly']),
                        'include_private_albums': random.choice([True, False]),
                        'auto_generate_reels': random.choice([True, False]),
                        'feature_enabled': True
                    }
                )
        
        print("   Created memory preferences")
    
    def create_audit_logs(self):
        """Create audit log entries"""
        print("📋 Creating audit logs...")
        
        event_types = [
            'LOGIN_SUCCESS', 'LOGOUT', 'MEDIA_UPLOAD', 'MEDIA_DELETE',
            'ALBUM_CREATE', 'ALBUM_DELETE', 'SHARE_CREATE', 'SHARE_ACCESS'
        ]
        
        categories = {
            'LOGIN_SUCCESS': 'AUTH',
            'LOGOUT': 'AUTH',
            'MEDIA_UPLOAD': 'MEDIA',
            'MEDIA_DELETE': 'MEDIA',
            'ALBUM_CREATE': 'ALBUM',
            'ALBUM_DELETE': 'ALBUM',
            'SHARE_CREATE': 'SHARE',
            'SHARE_ACCESS': 'SHARE'
        }
        
        # Create 100-200 audit log entries
        num_logs = random.randint(100, 200)
        
        for _ in range(num_logs):
            user = random.choice(self.users)
            event_type = random.choice(event_types)
            category = categories[event_type]
            
            # Create realistic details based on event type
            details = {
                'user_agent': 'Mozilla/5.0 (Sample Data)',
                'event_details': f'Sample {event_type} event'
            }
            
            resource_type = ''
            resource_id = ''
            
            if 'MEDIA' in event_type:
                if self.images:
                    resource_type = 'Image'
                    resource_id = str(random.choice(self.images).id)
            elif 'ALBUM' in event_type:
                if self.albums:
                    resource_type = 'Album'
                    resource_id = str(random.choice(self.albums).id)
            elif 'SHARE' in event_type:
                if self.shares:
                    resource_type = 'PublicShare'
                    resource_id = str(random.choice(self.shares).id)
            
            AuditEvent.objects.create(
                user=user,
                category=category,
                event_type=event_type,
                ip_address=f'192.168.1.{random.randint(1, 254)}',
                user_agent='Mozilla/5.0 (Sample Data Generator)',
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                success=random.choice([True, True, True, False]),  # Mostly successful
                timestamp=timezone.now() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
            )
        
        print(f"   Created {num_logs} audit log entries")
    
    def print_summary(self):
        """Print summary of created data"""
        print("\n📊 SAMPLE DATA SUMMARY")
        print("=" * 50)
        print(f"👥 Users: {len(self.users)}")
        print(f"📁 Folders: {len(self.folders)}")
        print(f"📸 Images: {len(self.images)}")
        print(f"📚 Albums: {len(self.albums)}")
        print(f"🔗 Sharing Links: {len(self.shares)}")
        print(f"🧠 Memories: {len(self.memories)}")
        print(f"🎬 Flashback Reels: {len(self.reels)}")
        print(f"🏁 Feature Flags: {FeatureFlag.objects.count()}")
        print(f"📋 Audit Logs: {AuditEvent.objects.count()}")
        print("=" * 50)
        
        # Print sample login credentials
        print("\n🔑 SAMPLE LOGIN CREDENTIALS")
        print("-" * 30)
        photographers = User.objects.filter(username__contains='photographer')
        for user in photographers:
            print(f"Username: {user.username}")
            print(f"Password: testpass123")
            print(f"Email: {user.email}")
            print(f"Role: Photographer")
            print("-" * 30)
        
        clients = User.objects.filter(username__contains='client')
        for user in clients:
            print(f"Username: {user.username}")
            print(f"Password: testpass123")
            print(f"Email: {user.email}")
            print(f"Role: Client")
            print("-" * 30)


def main():
    """Main function to generate sample data"""
    generator = SampleDataGenerator()
    generator.generate_all_data()
    
    print("\n🎉 Sample data generation completed successfully!")
    print("\nYou can now:")
    print("1. Start the Django server: python manage.py runserver")
    print("2. Login with the credentials shown above")
    print("3. Test all PhotoVault features with realistic data")
    print("4. Run the comprehensive feature test script")


if __name__ == '__main__':
    main()