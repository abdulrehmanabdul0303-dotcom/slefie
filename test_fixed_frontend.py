#!/usr/bin/env python3
"""
Test the fixed frontend behavior
"""
import requests
import json
import time

def test_fixed_frontend():
    """Test registration as the fixed frontend would do it"""
    print("🔧 Testing Fixed Frontend Registration")
    print("=" * 45)
    
    base_url = "http://localhost:8000"
    
    try:
        # Step 1: Get CSRF token (as frontend does)
        print("1. Getting CSRF token...")
        csrf_response = requests.get(f"{base_url}/api/auth/csrf/")
        csrf_token = csrf_response.json().get('csrfToken')
        print(f"✅ CSRF Token received")
        
        # Step 2: Simulate frontend registration with password_confirm
        print("\n2. Simulating frontend registration...")
        
        # This is what the fixed frontend auth service will send
        frontend_data = {
            'name': 'Fixed Frontend User',
            'email': f'fixed_frontend_{int(time.time())}@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'  # Added by the fix
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': csrf_token,
            'Accept': 'application/json'
        }
        
        print(f"📤 Sending data: {list(frontend_data.keys())}")
        
        response = requests.post(
            f"{base_url}/api/auth/register/",
            json=frontend_data,
            headers=headers
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            print("✅ Frontend fix is working correctly!")
            return True
        else:
            print("❌ Registration failed")
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
    success = test_fixed_frontend()
    if success:
        print("\n🎉 Frontend fix confirmed working!")
        print("The 400 errors should now be resolved.")
    else:
        print("\n💥 Frontend fix needs more work.")