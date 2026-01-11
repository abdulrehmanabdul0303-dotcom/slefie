#!/usr/bin/env python3
"""
Debug authentication endpoints.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

def test_registration():
    print("Testing registration...")
    
    register_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "name": "Test User"
    }
    
    response = requests.post(f"{API_BASE}/auth/register/", json=register_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

def test_login():
    print("\nTesting login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response

def verify_user_manually():
    """Manually verify the user in database."""
    print("\nManually verifying user...")
    
    import os
    import sys
    import django
    
    # Add the Django project to the path
    sys.path.append('photovault_django')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photovault.settings')
    django.setup()
    
    from apps.users.models import User
    
    try:
        user = User.objects.get(email="test@example.com")
        user.email_verified = True
        user.save()
        print(f"✅ User {user.email} verified successfully")
        return True
    except User.DoesNotExist:
        print("❌ User not found")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Test registration
    reg_response = test_registration()
    
    # If registration was successful or user already exists, verify manually
    if reg_response.status_code in [201, 400]:
        verify_user_manually()
    
    # Test login
    login_response = test_login()
    
    if login_response.status_code == 200:
        print("✅ Authentication working!")
        data = login_response.json()
        print(f"Access token: {data.get('access_token', 'N/A')[:50]}...")
    else:
        print("❌ Authentication failed")