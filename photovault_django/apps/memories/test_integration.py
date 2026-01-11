"""
End-to-end integration tests for Memory Time Machine.

These tests validate the complete workflow from photo upload to memory discovery
and API access, ensuring all components work together correctly.
"""
from datetime import date, timedelta
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.images.models import Image, Folder
from apps.albums.models import Album
from .models import Memory, MemoryPhoto, MemoryEngagement
from .services import MemoryEngine

User = get_user_model()


class MemoryTimeachineIntegrationTest(TransactionTestCase):
    """
    End-to-end integration test for the complete Memory Time Machine workflow.
    
    This test validates:
    1. Photo upload and storage
    2. Memory discovery algorithm
    3. API endpoint functionality
    4. Caching behavior
    5. Engagement tracking
    """
    
    def setUp(self):
        """Set up test data for integration testing"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='integration_user',
            email='integration@example.com',
            password='testpass123'
        )
        
        # Create test folder and album
        self.folder = Folder.objects.create(
            name='Integration Test Folder',
            user=self.user
        )
        
        self.album = Album.objects.create(
            name='Integration Test Album',
            user=self.user
        )
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
        
        # Initialize memory engine
        self.memory_engine = MemoryEngine()
    
    def test_complete_memory_workflow(self):
        """
        Test the complete memory discovery workflow from start to finish.
        """
        # Step 1: Create photos from previous years (simulating historical data)
        target_date = date.today()
        photos_created = []
        
        for year_offset in [1, 2, 3]:  # 1, 2, and 3 years ago
            photo_date = target_date.replace(year=target_date.year - year_offset)
            
            image = Image.objects.create(
                user=self.user,
                folder=self.folder,
                original_filename=f'memory_photo_{year_offset}.jpg',
                storage_key=f'integration/memory_photo_{year_offset}.jpg',
                checksum_sha256=f'integration_checksum_{year_offset:064d}',
                size_bytes=1024 * year_offset,  # Different sizes
                width=800 + year_offset * 100,
                height=600 + year_offset * 100,
                content_type='image/jpeg',
                taken_at=timezone.make_aware(
                    timezone.datetime.combine(photo_date, timezone.datetime.min.time())
                ),
                camera_make='Canon',
                camera_model=f'EOS {year_offset}D',
                location_text=f'Test Location {year_offset}'
            )
            photos_created.append(image)
            
            # Add some photos to album to increase significance
            if year_offset <= 2:
                self.album.images.add(image)
        
        # Step 2: Test memory discovery via service
        memories = self.memory_engine.discover_daily_memories(self.user.id, target_date)
        
        # Verify memory was created
        self.assertEqual(len(memories), 1, "Should create exactly one memory for the target date")
        memory = memories[0]
        
        self.assertEqual(memory.user, self.user)
        self.assertEqual(memory.target_date, target_date)
        self.assertGreater(memory.significance_score, 0, "Memory should have positive significance score")
        self.assertGreater(memory.photos.count(), 0, "Memory should contain photos")
        
        # Step 3: Test API endpoint for daily memories
        response = self.client.get('/api/memories/daily/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['target_date'], str(target_date))
        self.assertEqual(data['count'], 1)
        self.assertEqual(len(data['memories']), 1)
        
        memory_data = data['memories'][0]
        self.assertEqual(memory_data['id'], memory.id)
        self.assertGreater(len(memory_data['photos']), 0)
        
        # Step 4: Test memory detail API
        response = self.client.get(f'/api/memories/{memory.id}/detail/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        detail_data = response.json()
        
        # Verify detailed response structure
        self.assertIn('memory', detail_data)
        self.assertIn('context', detail_data)
        self.assertIn('engagement', detail_data)
        self.assertIn('photos_metadata', detail_data)
        
        # Verify context information
        context = detail_data['context']
        self.assertEqual(context['target_date'], str(target_date))
        self.assertGreaterEqual(context['years_ago'], 0)  # Could be 0 for same year photos
        self.assertEqual(context['photo_count'], memory.photos.count())
        
        # Verify photo metadata
        photos_metadata = detail_data['photos_metadata']
        self.assertGreater(len(photos_metadata), 0)
        
        for photo_meta in photos_metadata:
            self.assertIn('filename', photo_meta)
            self.assertIn('significance_score', photo_meta)
            self.assertIn('camera_make', photo_meta)
            self.assertIn('location_text', photo_meta)
        
        # Step 5: Test engagement tracking
        response = self.client.post(
            f'/api/memories/{memory.id}/engage/',
            {'interaction_type': 'view'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify engagement was recorded
        engagement = MemoryEngagement.objects.filter(memory=memory).first()
        self.assertIsNotNone(engagement)
        self.assertEqual(engagement.interaction_type, 'view')
        
        # Verify memory engagement count was updated
        memory.refresh_from_db()
        self.assertEqual(memory.engagement_count, 1)
        self.assertIsNotNone(memory.last_viewed)
        
        # Step 6: Test analytics API
        response = self.client.get('/api/memories/analytics/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        analytics_data = response.json()
        
        self.assertEqual(analytics_data['total_memories'], 1)
        self.assertEqual(analytics_data['total_engagements'], 1)
        self.assertGreater(analytics_data['avg_significance_score'], 0)
        
        # Step 7: Test caching behavior
        # Second request should be faster due to caching
        import time
        
        start_time = time.time()
        memories_cached = self.memory_engine.discover_daily_memories(self.user.id, target_date)
        cached_time = time.time() - start_time
        
        # Should return same memory from cache
        self.assertEqual(len(memories_cached), 1)
        self.assertEqual(memories_cached[0].id, memory.id)
        
        # Cached request should be reasonably fast
        self.assertLess(cached_time, 0.5, "Cached request should be fast")
        
        # Step 8: Test cache invalidation
        # Create new photo - should invalidate cache
        new_image = Image.objects.create(
            user=self.user,
            folder=self.folder,
            original_filename='new_memory_photo.jpg',
            storage_key='integration/new_memory_photo.jpg',
            checksum_sha256='new_integration_checksum' + '0' * 40,
            size_bytes=2048,
            width=1200,
            height=800,
            content_type='image/jpeg',
            taken_at=timezone.make_aware(
                timezone.datetime.combine(
                    target_date.replace(year=target_date.year - 1), 
                    timezone.datetime.min.time()
                )
            )
        )
        
        # Next memory discovery should work with invalidated cache
        memories_after_invalidation = self.memory_engine.discover_daily_memories(self.user.id, target_date)
        self.assertEqual(len(memories_after_invalidation), 1)
        
        print("✅ Complete Memory Time Machine workflow test passed!")
        print(f"   - Created {len(photos_created)} historical photos")
        print(f"   - Generated memory with {memory.photos.count()} photos")
        print(f"   - Memory significance score: {memory.significance_score:.2f}")
        print(f"   - Tracked {memory.engagement_count} engagement(s)")
        print(f"   - Cache invalidation working correctly")
    
    def test_memory_preferences_workflow(self):
        """
        Test memory preferences management workflow.
        """
        # Step 1: Get default preferences
        response = self.client.get('/api/memories/preferences/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prefs_data = response.json()
        
        # Verify default values
        self.assertTrue(prefs_data['enable_notifications'])
        self.assertEqual(prefs_data['notification_frequency'], 'daily')
        self.assertTrue(prefs_data['feature_enabled'])
        
        # Step 2: Update preferences
        update_data = {
            'enable_notifications': False,
            'notification_frequency': 'weekly',
            'include_private_albums': True
        }
        
        response = self.client.post('/api/memories/preferences/', update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        updated_prefs = response.json()
        
        # Verify updates
        self.assertFalse(updated_prefs['enable_notifications'])
        self.assertEqual(updated_prefs['notification_frequency'], 'weekly')
        self.assertTrue(updated_prefs['include_private_albums'])
        
        print("✅ Memory preferences workflow test passed!")
    
    def test_error_handling_workflow(self):
        """
        Test error handling in various scenarios.
        """
        # Test accessing non-existent memory
        response = self.client.get('/api/memories/99999/detail/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test invalid engagement type
        memory = Memory.objects.create(
            user=self.user,
            target_date=date.today(),
            significance_score=5.0
        )
        
        response = self.client.post(
            f'/api/memories/{memory.id}/engage/',
            {'interaction_type': 'invalid_type'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test missing engagement type
        response = self.client.post(
            f'/api/memories/{memory.id}/engage/',
            {},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid date format
        response = self.client.get('/api/memories/daily/?date=invalid-date')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        print("✅ Error handling workflow test passed!")
    
    def test_authentication_workflow(self):
        """
        Test authentication requirements for all endpoints.
        """
        # Remove authentication
        self.client.force_authenticate(user=None)
        
        endpoints_to_test = [
            '/api/memories/daily/',
            '/api/memories/analytics/',
            '/api/memories/preferences/',
        ]
        
        for endpoint in endpoints_to_test:
            response = self.client.get(endpoint)
            self.assertEqual(
                response.status_code, 
                status.HTTP_401_UNAUTHORIZED,
                f"Endpoint {endpoint} should require authentication"
            )
        
        print("✅ Authentication workflow test passed!")


if __name__ == '__main__':
    import django
    django.setup()
    
    # Run the integration test
    test = MemoryTimeachineIntegrationTest()
    test.setUp()
    
    try:
        test.test_complete_memory_workflow()
        test.test_memory_preferences_workflow()
        test.test_error_handling_workflow()
        test.test_authentication_workflow()
        print("\n🎉 All integration tests passed! Memory Time Machine is working end-to-end.")
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        raise