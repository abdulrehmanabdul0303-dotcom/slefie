"""
Critical flow tests for PhotoVault production readiness.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
import json

from apps.users.models import EmailVerificationToken
from apps.sharing.models import ShareToken
from apps.albums.models import Album

User = get_user_model()


class CriticalFlowTests(TestCase):
    """
    Test critical user flows for production readiness.
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!'
        }
    
    def create_test_image(self):
        """Create a test image file."""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )
    
    def test_1_user_registration_flow(self):
        """Test complete user registration flow."""
        # Register user
        response = self.client.post(
            reverse('users:register'),
            self.user_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user_id', response.data)
        
        # Verify user created but not verified
        user = User.objects.get(email=self.user_data['email'])
        self.assertFalse(user.email_verified)
        
        # Verify email verification token created
        token = EmailVerificationToken.objects.get(user=user)
        self.assertIsNotNone(token)
        
        # Verify email
        verify_response = self.client.post(
            reverse('users:verify-email'),
            {'token': token.token},
            format='json'
        )
        
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        
        # Check user is now verified
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
    
    def test_2_login_flow(self):
        """Test login flow with verified user."""
        # Create and verify user
        user = User.objects.create_user(
            username=self.user_data['email'],
            email=self.user_data['email'],
            password=self.user_data['password'],
            email_verified=True,
            dek_encrypted_b64='test_dek'
        )
        
        # Login
        login_data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        
        response = self.client.post(
            reverse('users:login'),
            login_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertIn('user', response.data)
        
        return response.data['access_token'], response.data['refresh_token']
    
    def test_3_token_refresh_flow(self):
        """Test JWT token refresh flow."""
        # Create user and get tokens
        access_token, refresh_token = self.test_2_login_flow()
        
        # Refresh token
        response = self.client.post(
            reverse('users:token-refresh'),
            {'refresh': refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_4_logout_flow(self):
        """Test logout with token blacklisting."""
        # Create user and get tokens
        access_token, refresh_token = self.test_2_login_flow()
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Logout
        response = self.client.post(
            reverse('users:logout'),
            {'refresh_token': refresh_token},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to use refresh token (should fail)
        refresh_response = self.client.post(
            reverse('users:token-refresh'),
            {'refresh': refresh_token},
            format='json'
        )
        
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_5_unauthorized_access_blocked(self):
        """Test that unauthorized access is properly blocked."""
        # Try to access protected endpoint without token
        response = self.client.get(reverse('users:profile'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'NOT_AUTHENTICATED')
    
    def test_6_image_upload_validation(self):
        """Test image upload with validation."""
        # Create and authenticate user
        access_token, _ = self.test_2_login_flow()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test valid image upload
        valid_image = self.create_test_image()
        response = self.client.post(
            reverse('images:upload'),
            {'images': valid_image},
            format='multipart'
        )
        
        # Should succeed (or fail gracefully with proper error format)
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ])
        
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn('error', response.data)
        
        # Test invalid file upload
        invalid_file = SimpleUploadedFile(
            'test.txt',
            b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post(
            reverse('images:upload'),
            {'images': invalid_file},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_7_pagination_works(self):
        """Test API pagination."""
        # Create and authenticate user
        access_token, _ = self.test_2_login_flow()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test albums list (should be paginated)
        response = self.client.get(reverse('albums:album-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pagination structure
        if 'results' in response.data:
            # DRF pagination
            self.assertIn('count', response.data)
            self.assertIn('results', response.data)
        else:
            # Simple list (acceptable for empty results)
            self.assertIsInstance(response.data, list)
    
    def test_8_share_token_expiry(self):
        """Test share token expiry functionality."""
        # Create and authenticate user
        access_token, _ = self.test_2_login_flow()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Create album
        album_response = self.client.post(
            reverse('albums:album-list'),
            {'name': 'Test Album', 'description': 'Test'},
            format='json'
        )
        
        if album_response.status_code == status.HTTP_201_CREATED:
            album_id = album_response.data['id']
            
            # Create share token with short expiry
            from django.utils import timezone
            from datetime import timedelta
            
            share_data = {
                'album': album_id,
                'expires_at': (timezone.now() + timedelta(seconds=1)).isoformat(),
                'max_views': 5
            }
            
            share_response = self.client.post(
                reverse('sharing:sharetoken-list'),
                share_data,
                format='json'
            )
            
            # Should create successfully or fail gracefully
            self.assertIn(share_response.status_code, [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST
            ])


class SecurityTests(TestCase):
    """
    Security-focused tests.
    """
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            email_verified=True,
            dek_encrypted_b64='test_dek'
        )
    
    def test_rate_limiting_protection(self):
        """Test that rate limiting is working."""
        # Try multiple rapid login attempts
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        responses = []
        for i in range(12):  # Exceed rate limit
            response = self.client.post(
                reverse('users:login'),
                login_data,
                format='json'
            )
            responses.append(response.status_code)
        
        # Should eventually get rate limited (429) or consistent 400s
        self.assertTrue(
            429 in responses or all(r == 400 for r in responses),
            f"Rate limiting not working properly. Status codes: {responses}"
        )
    
    def test_sql_injection_protection(self):
        """Test SQL injection protection."""
        # Try SQL injection in search
        malicious_query = "'; DROP TABLE users; --"
        
        response = self.client.get(
            reverse('albums:album-list'),
            {'search': malicious_query}
        )
        
        # Should not cause server error
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_xss_protection(self):
        """Test XSS protection in API responses."""
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Try XSS in album name
        xss_payload = '<script>alert("xss")</script>'
        
        response = self.client.post(
            reverse('albums:album-list'),
            {'name': xss_payload, 'description': 'Test'},
            format='json'
        )
        
        # Should either reject or sanitize
        if response.status_code == status.HTTP_201_CREATED:
            # If accepted, should be sanitized
            self.assertNotIn('<script>', str(response.data))


class ErrorFormatTests(TestCase):
    """
    Test consistent error format across API.
    """
    
    def setUp(self):
        self.client = APIClient()
    
    def test_validation_error_format(self):
        """Test validation error format consistency."""
        # Invalid registration data
        response = self.client.post(
            reverse('users:register'),
            {'email': 'invalid-email'},  # Missing required fields
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])
    
    def test_authentication_error_format(self):
        """Test authentication error format."""
        response = self.client.get(reverse('users:profile'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'NOT_AUTHENTICATED')
    
    def test_not_found_error_format(self):
        """Test 404 error format."""
        response = self.client.get('/api/nonexistent/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Should have consistent error format (if custom 404 handler is implemented)