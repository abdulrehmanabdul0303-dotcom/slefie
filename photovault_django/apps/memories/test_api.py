"""
Unit tests for Memory Time Machine API endpoints.

These tests validate specific examples, edge cases, and integration points
for the memory discovery and engagement API endpoints.
"""
import json
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.images.models import Image, Folder
from apps.albums.models import Album
from .models import Memory, MemoryPhoto, MemoryEngagement, MemoryPreferences

User = get_user_model()


class MemoryAPITestCase(TestCase):
    """Base test case for Memory API tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create another user for permission testing
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create test folder and album
        self.folder = Folder.objects.create(
            name='Test Folder',
            user=self.user
        )
        
        self.album = Album.objects.create(
            name='Test Album',
            user=self.user
        )
        
        # Authenticate as test user
        self.client.force_authenticate(user=self.user)
    
    def create_test_image(self, filename='test.jpg', taken_at=None):
        """Helper method to create test images"""
        if taken_at is None:
            taken_at = timezone.now()
        
        # Generate unique checksum to avoid conflicts
        import uuid
        unique_id = str(uuid.uuid4()).replace('-', '')
        
        return Image.objects.create(
            user=self.user,
            folder=self.folder,
            original_filename=filename,
            storage_key=f'test/{filename}',
            checksum_sha256=unique_id[:64],  # 64-char hex string
            size_bytes=1024,
            width=800,
            height=600,
            content_type='image/jpeg',
            taken_at=taken_at
        )
    
    def create_test_memory(self, target_date=None, photos=None):
        """Helper method to create test memories"""
        if target_date is None:
            target_date = date.today()
        
        memory = Memory.objects.create(
            user=self.user,
            target_date=target_date,
            significance_score=5.0
        )
        
        if photos:
            for i, photo in enumerate(photos):
                MemoryPhoto.objects.create(
                    memory=memory,
                    photo=photo,
                    significance_score=5.0 - i * 0.5,
                    order=i
                )
        
        return memory


class DailyMemoriesAPITests(MemoryAPITestCase):
    """Tests for daily memories API endpoint"""
    
    def test_get_daily_memories_success(self):
        """Test successful daily memories retrieval"""
        # Create photos from previous years
        target_date = date.today()
        last_year = target_date.replace(year=target_date.year - 1)
        
        photo1 = self.create_test_image(
            'memory1.jpg',
            timezone.make_aware(timezone.datetime.combine(last_year, timezone.datetime.min.time()))
        )
        photo2 = self.create_test_image(
            'memory2.jpg',
            timezone.make_aware(timezone.datetime.combine(last_year, timezone.datetime.min.time()))
        )
        
        # Create memory
        memory = self.create_test_memory(target_date, [photo1, photo2])
        
        # Make API request
        url = reverse('memories:daily-memories')
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['target_date'], str(target_date))
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['memories']), 1)
        
        memory_data = data['memories'][0]
        self.assertEqual(memory_data['id'], memory.id)
        self.assertEqual(memory_data['target_date'], str(target_date))
        self.assertEqual(len(memory_data['photos']), 2)
    
    def test_get_daily_memories_with_date_parameter(self):
        """Test daily memories with specific date parameter"""
        # Create memory for specific date
        target_date = date(2024, 6, 15)
        photo = self.create_test_image('specific_date.jpg')
        memory = self.create_test_memory(target_date, [photo])
        
        # Make API request with date parameter
        url = reverse('memories:daily-memories')
        response = self.client.get(url, {'date': '2024-06-15'})
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['target_date'], '2024-06-15')
        self.assertEqual(data['count'], 1)
    
    def test_get_daily_memories_invalid_date(self):
        """Test daily memories with invalid date parameter"""
        url = reverse('memories:daily-memories')
        response = self.client.get(url, {'date': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid date format', response.json()['error'])
    
    def test_get_daily_memories_no_memories(self):
        """Test daily memories when no memories exist"""
        url = reverse('memories:daily-memories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['memories']), 0)
    
    def test_get_daily_memories_authentication_required(self):
        """Test that authentication is required"""
        self.client.force_authenticate(user=None)
        
        url = reverse('memories:daily-memories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MemoryDetailAPITests(MemoryAPITestCase):
    """Tests for memory detail API endpoint"""
    
    def test_get_memory_detail_success(self):
        """Test successful memory detail retrieval"""
        # Create memory with photos
        photo1 = self.create_test_image('detail1.jpg')
        photo2 = self.create_test_image('detail2.jpg')
        memory = self.create_test_memory(photos=[photo1, photo2])
        
        # Make API request
        url = reverse('memories:memory-detail', kwargs={'memory_id': memory.id})
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check memory data
        self.assertIn('memory', data)
        self.assertEqual(data['memory']['id'], memory.id)
        
        # Check context data
        self.assertIn('context', data)
        context = data['context']
        self.assertEqual(context['photo_count'], 2)
        self.assertIn('target_date', context)
        
        # Check engagement data
        self.assertIn('engagement', data)
        
        # Check photos metadata
        self.assertIn('photos_metadata', data)
        self.assertEqual(len(data['photos_metadata']), 2)
        
        # Verify photo metadata structure
        photo_metadata = data['photos_metadata'][0]
        self.assertIn('filename', photo_metadata)
        self.assertIn('significance_score', photo_metadata)
        self.assertIn('order', photo_metadata)
    
    def test_get_memory_detail_not_found(self):
        """Test memory detail for non-existent memory"""
        url = reverse('memories:memory-detail', kwargs={'memory_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_memory_detail_wrong_user(self):
        """Test memory detail access by wrong user"""
        # Create memory for other user
        other_memory = Memory.objects.create(
            user=self.other_user,
            target_date=date.today(),
            significance_score=5.0
        )
        
        # Try to access as current user
        url = reverse('memories:memory-detail', kwargs={'memory_id': other_memory.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_memory_detail_authentication_required(self):
        """Test that authentication is required"""
        memory = self.create_test_memory()
        
        self.client.force_authenticate(user=None)
        
        url = reverse('memories:memory-detail', kwargs={'memory_id': memory.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MemoryEngagementAPITests(MemoryAPITestCase):
    """Tests for memory engagement tracking API endpoint"""
    
    def test_track_engagement_success(self):
        """Test successful engagement tracking"""
        memory = self.create_test_memory()
        
        # Track engagement
        url = reverse('memories:memory-engagement', kwargs={'memory_id': memory.id})
        data = {'interaction_type': 'view'}
        response = self.client.post(url, data, format='json')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['memory_id'], memory.id)
        self.assertEqual(response_data['interaction_type'], 'view')
        self.assertIn('message', response_data)
        
        # Verify engagement was recorded
        engagement = MemoryEngagement.objects.filter(memory=memory).first()
        self.assertIsNotNone(engagement)
        self.assertEqual(engagement.interaction_type, 'view')
        
        # Verify memory engagement count was updated
        memory.refresh_from_db()
        self.assertEqual(memory.engagement_count, 1)
        self.assertIsNotNone(memory.last_viewed)
    
    def test_track_engagement_all_types(self):
        """Test tracking all valid engagement types"""
        memory = self.create_test_memory()
        url = reverse('memories:memory-engagement', kwargs={'memory_id': memory.id})
        
        valid_types = ['view', 'share', 'like', 'download']
        
        for interaction_type in valid_types:
            data = {'interaction_type': interaction_type}
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify engagement was recorded
            engagement = MemoryEngagement.objects.filter(
                memory=memory,
                interaction_type=interaction_type
            ).first()
            self.assertIsNotNone(engagement)
    
    def test_track_engagement_missing_type(self):
        """Test engagement tracking without interaction type"""
        memory = self.create_test_memory()
        
        url = reverse('memories:memory-engagement', kwargs={'memory_id': memory.id})
        response = self.client.post(url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('interaction_type is required', response.json()['error'])
    
    def test_track_engagement_invalid_type(self):
        """Test engagement tracking with invalid interaction type"""
        memory = self.create_test_memory()
        
        url = reverse('memories:memory-engagement', kwargs={'memory_id': memory.id})
        data = {'interaction_type': 'invalid_type'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid interaction_type', response.json()['error'])
    
    def test_track_engagement_memory_not_found(self):
        """Test engagement tracking for non-existent memory"""
        url = reverse('memories:memory-engagement', kwargs={'memory_id': 99999})
        data = {'interaction_type': 'view'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_track_engagement_wrong_user(self):
        """Test engagement tracking by wrong user"""
        # Create memory for other user
        other_memory = Memory.objects.create(
            user=self.other_user,
            target_date=date.today(),
            significance_score=5.0
        )
        
        # Try to track engagement as current user
        url = reverse('memories:memory-engagement', kwargs={'memory_id': other_memory.id})
        data = {'interaction_type': 'view'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_track_engagement_authentication_required(self):
        """Test that authentication is required"""
        memory = self.create_test_memory()
        
        self.client.force_authenticate(user=None)
        
        url = reverse('memories:memory-engagement', kwargs={'memory_id': memory.id})
        data = {'interaction_type': 'view'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MemoryAnalyticsAPITests(MemoryAPITestCase):
    """Tests for memory analytics API endpoint"""
    
    def test_get_analytics_success(self):
        """Test successful analytics retrieval"""
        # Create memories and engagements
        memory1 = self.create_test_memory()
        memory2 = self.create_test_memory(target_date=date.today() - timedelta(days=1))
        
        # Create engagements
        MemoryEngagement.objects.create(memory=memory1, interaction_type='view')
        MemoryEngagement.objects.create(memory=memory1, interaction_type='share')
        MemoryEngagement.objects.create(memory=memory2, interaction_type='like')
        
        # Make API request
        url = reverse('memories:memory-analytics')
        response = self.client.get(url)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('total_memories', data)
        self.assertIn('total_engagements', data)
        self.assertIn('avg_significance_score', data)
        self.assertIn('engagement_by_type', data)
        self.assertIn('period_days', data)
        
        self.assertEqual(data['total_memories'], 2)
        self.assertEqual(data['total_engagements'], 3)
        self.assertEqual(data['period_days'], 30)  # Default
    
    def test_get_analytics_with_days_parameter(self):
        """Test analytics with custom days parameter"""
        url = reverse('memories:memory-analytics')
        response = self.client.get(url, {'days': 7})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['period_days'], 7)
    
    def test_get_analytics_invalid_days(self):
        """Test analytics with invalid days parameter"""
        url = reverse('memories:memory-analytics')
        response = self.client.get(url, {'days': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid days parameter', response.json()['error'])
    
    def test_get_analytics_negative_days(self):
        """Test analytics with negative days parameter"""
        url = reverse('memories:memory-analytics')
        response = self.client.get(url, {'days': -5})
        
        # Should default to 30 days
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['period_days'], 30)
    
    def test_get_analytics_authentication_required(self):
        """Test that authentication is required"""
        self.client.force_authenticate(user=None)
        
        url = reverse('memories:memory-analytics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MemoryPreferencesAPITests(MemoryAPITestCase):
    """Tests for memory preferences API endpoint"""
    
    def test_get_preferences_success(self):
        """Test successful preferences retrieval"""
        url = reverse('memories:memory-preferences')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Check default values
        self.assertTrue(data['enable_notifications'])
        self.assertEqual(data['notification_frequency'], 'daily')
        self.assertFalse(data['include_private_albums'])
        self.assertTrue(data['auto_generate_reels'])
        self.assertTrue(data['feature_enabled'])
    
    def test_update_preferences_success(self):
        """Test successful preferences update"""
        url = reverse('memories:memory-preferences')
        
        # Update preferences
        update_data = {
            'enable_notifications': False,
            'notification_frequency': 'weekly',
            'include_private_albums': True,
            'auto_generate_reels': False
        }
        
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify updates
        self.assertFalse(data['enable_notifications'])
        self.assertEqual(data['notification_frequency'], 'weekly')
        self.assertTrue(data['include_private_albums'])
        self.assertFalse(data['auto_generate_reels'])
        
        # Verify in database
        preferences = MemoryPreferences.objects.get(user=self.user)
        self.assertFalse(preferences.enable_notifications)
        self.assertEqual(preferences.notification_frequency, 'weekly')
    
    def test_update_preferences_partial(self):
        """Test partial preferences update"""
        url = reverse('memories:memory-preferences')
        
        # Update only one field
        update_data = {'enable_notifications': False}
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify only the updated field changed
        self.assertFalse(data['enable_notifications'])
        self.assertEqual(data['notification_frequency'], 'daily')  # Should remain default
    
    def test_update_preferences_invalid_data(self):
        """Test preferences update with invalid data"""
        url = reverse('memories:memory-preferences')
        
        # Invalid notification frequency
        update_data = {'notification_frequency': 'invalid_frequency'}
        response = self.client.post(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())
    
    def test_preferences_authentication_required(self):
        """Test that authentication is required"""
        self.client.force_authenticate(user=None)
        
        url = reverse('memories:memory-preferences')
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test POST
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_preferences_user_isolation(self):
        """Test that users can only access their own preferences"""
        # Create preferences for current user
        url = reverse('memories:memory-preferences')
        self.client.post(url, {'enable_notifications': False}, format='json')
        
        # Switch to other user
        self.client.force_authenticate(user=self.other_user)
        
        # Get preferences (should create new default preferences)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Should have default values, not the other user's values
        self.assertTrue(data['enable_notifications'])  # Default, not False
        
        # Verify separate preferences objects exist
        user1_prefs = MemoryPreferences.objects.get(user=self.user)
        user2_prefs = MemoryPreferences.objects.get(user=self.other_user)
        
        self.assertFalse(user1_prefs.enable_notifications)
        self.assertTrue(user2_prefs.enable_notifications)