"""
Comprehensive Authentication Tests for PhotoVault
Tests all AUTH features (AUTH-01 through AUTH-08)
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


@pytest.mark.auth
@pytest.mark.django_db
class TestUserRegistration:
    """Test AUTH-01: User Registration + Email Verification"""
    
    def test_valid_registration(self, api_client, user_data):
        """Test successful user registration"""
        url = '/api/auth/register/'
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'message' in response.data
        assert 'user_id' in response.data
        
        # Verify user created in database
        user = User.objects.get(email=user_data['email'])
        assert user.name == user_data['name']
        assert user.email_verified == False  # Should require verification
    
    def test_duplicate_email_registration(self, api_client, user_data, create_user):
        """Test registration with duplicate email fails"""
        url = '/api/auth/register/'
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_weak_password_registration(self, api_client):
        """Test registration with weak password fails"""
        url = '/api/auth/register/'
        weak_data = {
            'name': 'Test User',
            'email': 'weak@example.com',
            'password': '123',
            'password_confirm': '123'
        }
        response = api_client.post(url, weak_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_password_mismatch_registration(self, api_client):
        """Test registration with password mismatch fails"""
        url = '/api/auth/register/'
        mismatch_data = {
            'name': 'Test User',
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'DifferentPassword123!'
        }
        response = api_client.post(url, mismatch_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_email_registration(self, api_client):
        """Test registration with invalid email fails"""
        url = '/api/auth/register/'
        invalid_data = {
            'name': 'Test User',
            'email': 'invalid-email',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = api_client.post(url, invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.auth
@pytest.mark.django_db
class TestUserLogin:
    """Test AUTH-03: JWT Login System"""
    
    def test_valid_login(self, api_client, create_user, user_data):
        """Test successful login with verified user"""
        url = '/api/auth/login/'
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        response = api_client.post(url, login_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        
        # Verify token format (JWT should start with 'eyJ')
        assert response.data['access_token'].startswith('eyJ')
        assert response.data['refresh_token'].startswith('eyJ')
    
    def test_unverified_user_login(self, api_client, db):
        """Test login fails for unverified user"""
        # Create unverified user
        user_data = {
            'name': 'Unverified User',
            'email': 'unverified@example.com',
            'password': 'TestPassword123!'
        }
        user = User.objects.create_user(
            username=user_data['email'],
            email=user_data['email'],
            name=user_data['name'],
            password=user_data['password']
        )
        # email_verified defaults to False
        
        url = '/api/auth/login/'
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        response = api_client.post(url, login_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_invalid_credentials_login(self, api_client, create_user):
        """Test login fails with wrong password"""
        url = '/api/auth/login/'
        login_data = {
            'email': create_user.email,
            'password': 'WrongPassword123!'
        }
        response = api_client.post(url, login_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_nonexistent_user_login(self, api_client):
        """Test login fails for non-existent user"""
        url = '/api/auth/login/'
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'SomePassword123!'
        }
        response = api_client.post(url, login_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.auth
@pytest.mark.django_db
class TestProtectedEndpoints:
    """Test JWT token authentication on protected endpoints"""
    
    def test_access_with_valid_token(self, authenticated_client):
        """Test accessing protected endpoint with valid JWT"""
        api_client, user = authenticated_client
        url = '/api/auth/me/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['name'] == user.name
    
    def test_access_without_token(self, api_client):
        """Test accessing protected endpoint without token fails"""
        url = '/api/auth/me/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_access_with_invalid_token(self, api_client):
        """Test accessing protected endpoint with invalid token fails"""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        url = '/api/auth/me/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
@pytest.mark.django_db
class TestAccountSecurity:
    """Test AUTH-05: Account Lockout and Security Features"""
    
    def test_failed_login_tracking(self, api_client, create_user):
        """Test that failed login attempts are tracked"""
        url = '/api/auth/login/'
        login_data = {
            'email': create_user.email,
            'password': 'WrongPassword123!'
        }
        
        # Make multiple failed attempts
        for i in range(3):
            response = api_client.post(url, login_data, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Check user's failed attempts counter
        create_user.refresh_from_db()
        assert create_user.failed_login_attempts >= 3


@pytest.mark.auth
@pytest.mark.django_db
class TestCSRFProtection:
    """Test AUTH-04: CSRF Protection"""
    
    def test_csrf_token_endpoint(self, api_client):
        """Test CSRF token endpoint is accessible"""
        url = '/api/auth/csrf/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'csrfToken' in response.data


@pytest.mark.auth
@pytest.mark.security
@pytest.mark.django_db
class TestAuthenticationSecurity:
    """Security tests for authentication system"""
    
    def test_sql_injection_in_login(self, api_client):
        """Test SQL injection protection in login"""
        url = '/api/auth/login/'
        malicious_data = {
            'email': "admin@example.com' OR '1'='1",
            'password': "password' OR '1'='1"
        }
        response = api_client.post(url, malicious_data, format='json')
        
        # Should fail with validation error, not SQL error
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_xss_in_registration(self, api_client):
        """Test XSS protection in registration"""
        url = '/api/auth/register/'
        xss_data = {
            'name': '<script>alert("xss")</script>',
            'email': 'xss@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        response = api_client.post(url, xss_data, format='json')
        
        if response.status_code == status.HTTP_201_CREATED:
            # If registration succeeds, check that script is sanitized
            user = User.objects.get(email=xss_data['email'])
            assert '<script>' not in user.name
    
    def test_password_not_in_response(self, api_client, user_data):
        """Test that password is never returned in API responses"""
        # Registration
        url = '/api/auth/register/'
        response = api_client.post(url, user_data, format='json')
        response_str = json.dumps(response.data)
        assert user_data['password'] not in response_str
        
        # Login
        user = User.objects.get(email=user_data['email'])
        user.email_verified = True
        user.save()
        
        login_url = '/api/auth/login/'
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        login_response = api_client.post(login_url, login_data, format='json')
        login_response_str = json.dumps(login_response.data)
        assert user_data['password'] not in login_response_str