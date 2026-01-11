"""
Pytest configuration and fixtures for PhotoVault tests.
"""
import os
import django
from django.conf import settings

# Configure Django settings before importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
django.setup()

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    """DRF API client for testing."""
    return APIClient()


@pytest.fixture
def django_client():
    """Django test client."""
    return Client()


@pytest.fixture
def user_data():
    """Standard user data for testing."""
    return {
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!'
    }


@pytest.fixture
def admin_data():
    """Admin user data for testing."""
    return {
        'name': 'Admin User',
        'email': 'admin@example.com',
        'password': 'AdminPassword123!',
        'password_confirm': 'AdminPassword123!'
    }


@pytest.fixture
def create_user(db, user_data):
    """Create a test user."""
    user = User.objects.create_user(
        username=user_data['email'],
        email=user_data['email'],
        name=user_data['name'],
        password=user_data['password']
    )
    user.email_verified = True
    user.save()
    return user


@pytest.fixture
def create_admin_user(db, admin_data):
    """Create an admin test user."""
    user = User.objects.create_user(
        username=admin_data['email'],
        email=admin_data['email'],
        name=admin_data['name'],
        password=admin_data['password'],
        is_admin=True,
        is_staff=True,
        is_superuser=True
    )
    user.email_verified = True
    user.save()
    return user


@pytest.fixture
def authenticated_client(api_client, create_user):
    """API client with authenticated user."""
    refresh = RefreshToken.for_user(create_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client, create_user


@pytest.fixture
def admin_client(api_client, create_admin_user):
    """API client with authenticated admin user."""
    refresh = RefreshToken.for_user(create_admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client, create_admin_user


@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    import io
    from PIL import Image
    
    # Create a simple test image
    image = Image.new('RGB', (100, 100), color='red')
    image_io = io.BytesIO()
    image.save(image_io, format='JPEG')
    image_io.seek(0)
    
    return {
        'file': image_io,
        'filename': 'test_image.jpg',
        'content_type': 'image/jpeg'
    }


@pytest.fixture
def malicious_file_data():
    """Malicious file data for security testing."""
    import io
    
    # Create a fake image with script content
    malicious_content = b'<?php echo "malicious code"; ?>'
    file_io = io.BytesIO(malicious_content)
    
    return {
        'file': file_io,
        'filename': 'malicious.php',
        'content_type': 'image/jpeg'  # Fake content type
    }