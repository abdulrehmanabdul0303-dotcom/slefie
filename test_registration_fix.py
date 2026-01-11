#!/usr/bin/env python3
"""
Test the registration fix
"""
import requests
import json
import time

def test_registration_fix():
    """Test registration with correct fields"""
    print("🔧 Testing Registration Fix")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    try:
        # Get CSRF token
        csrf_response = requests.get(f"{base_url}/api/auth/csrf/")
        csrf_token = csrf_response.json().get('csrfToken')
        print(f"✅ CSRF Token: {csrf_token[:20]}...")
        
        # Test with correct fields (like frontend will send)
        test_data = {
            'name': 'Frontend Test User',
            'email': f'frontend_test_{int(time.time())}@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'  # This was missing before
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token,
            'Accept': 'application/json'
        }
        
        print(f"\n📤 Sending registration data:")
        print(f"Name: {test_data['name']}")
        print(f"Email: {test_data['email']}")
        print(f"Password: {'*' * len(test_data['password'])}")
        print(f"Password Confirm: {'*' * len(test_data['password_confirm'])}")
        
        response = requests.post(
            f"{base_url}/api/auth/register/",
            json=test_data,
            headers=headers
        )
        
        print(f"\n📥 Response:")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            response_data = response.json()
            print(f"✅ User ID: {response_data.get('user_id')}")
            print(f"✅ Message: {response_data.get('message')}")
            return True
        else:
            print(f"❌ Registration failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_registration_fix()
    if success:
        print("\n🎉 Registration fix working correctly!")
    else:
        print("\n💥 Registration fix needs more work.")