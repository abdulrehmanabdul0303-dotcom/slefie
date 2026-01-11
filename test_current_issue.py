#!/usr/bin/env python3
"""
Test current frontend-backend connection issue
"""
import requests
import json
import time

def test_current_issue():
    """Test what's causing the 400 errors"""
    print("🔍 Testing Current Frontend-Backend Issue")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Basic connectivity
    print("1. Testing basic connectivity...")
    try:
        response = requests.get(f"{base_url}/api/auth/csrf/", timeout=5)
        print(f"✅ CSRF endpoint: {response.status_code}")
        if response.status_code == 200:
            csrf_token = response.json().get('csrfToken')
            print(f"✅ CSRF token: {csrf_token[:20]}...")
        else:
            print(f"❌ CSRF failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Test 2: Registration with missing password_confirm (old frontend behavior)
    print("\n2. Testing registration without password_confirm (old behavior)...")
    old_data = {
        'name': 'Test User Old',
        'email': f'old_test_{int(time.time())}@example.com',
        'password': 'TestPassword123!'
        # Missing password_confirm
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf_token,
        'Accept': 'application/json'
    }
    
    response = requests.post(f"{base_url}/api/auth/register/", json=old_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 3: Registration with password_confirm (new frontend behavior)
    print("\n3. Testing registration with password_confirm (new behavior)...")
    new_data = {
        'name': 'Test User New',
        'email': f'new_test_{int(time.time())}@example.com',
        'password': 'TestPassword123!',
        'password_confirm': 'TestPassword123!'
    }
    
    response = requests.post(f"{base_url}/api/auth/register/", json=new_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 4: Login attempt (should fail - no verified users)
    print("\n4. Testing login...")
    login_data = {
        'email': 'test@example.com',
        'password': 'TestPassword123!'
    }
    
    response = requests.post(f"{base_url}/api/auth/login/", json=login_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Test 5: Check what frontend might be sending
    print("\n5. Testing common frontend issues...")
    
    # Empty request
    response = requests.post(f"{base_url}/api/auth/register/", json={}, headers=headers)
    print(f"Empty data - Status: {response.status_code}, Response: {response.text}")
    
    # Missing headers
    response = requests.post(f"{base_url}/api/auth/register/", json=new_data)
    print(f"No headers - Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    test_current_issue()