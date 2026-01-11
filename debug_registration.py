#!/usr/bin/env python3
"""
Debug registration endpoint to see what's causing 400 errors
"""
import requests
import json

def debug_registration():
    """Debug the registration endpoint"""
    print("🔍 Debugging Registration Endpoint")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Step 1: Get CSRF token
        print("1. Getting CSRF token...")
        csrf_response = requests.get(f"{base_url}/api/auth/csrf/")
        print(f"CSRF Status: {csrf_response.status_code}")
        
        if csrf_response.status_code != 200:
            print(f"❌ CSRF failed: {csrf_response.text}")
            return
            
        csrf_token = csrf_response.json().get('csrfToken')
        print(f"✅ CSRF Token: {csrf_token[:20]}...")
        
        # Step 2: Test registration with various data
        print("\n2. Testing registration...")
        
        test_cases = [
            {
                "name": "Valid Registration",
                "data": {
                    'name': 'Debug User',
                    'email': 'debug@example.com',
                    'password': 'DebugPassword123!',
                    'password_confirm': 'DebugPassword123!'
                }
            },
            {
                "name": "Missing Field",
                "data": {
                    'name': 'Debug User',
                    'email': 'debug2@example.com',
                    'password': 'DebugPassword123!'
                    # Missing password_confirm
                }
            },
            {
                "name": "Invalid Email",
                "data": {
                    'name': 'Debug User',
                    'email': 'invalid-email',
                    'password': 'DebugPassword123!',
                    'password_confirm': 'DebugPassword123!'
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n2.{i} {test_case['name']}:")
            
            headers = {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrf_token,
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f"{base_url}/api/auth/register/",
                json=test_case['data'],
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    print(f"Error Details: {json.dumps(error_data, indent=2)}")
                except:
                    print("Could not parse error response as JSON")
                    
        # Step 3: Test without CSRF token
        print(f"\n3. Testing without CSRF token:")
        
        headers_no_csrf = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(
            f"{base_url}/api/auth/register/",
            json={
                'name': 'No CSRF User',
                'email': 'nocsrf@example.com',
                'password': 'Password123!',
                'password_confirm': 'Password123!'
            },
            headers=headers_no_csrf
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Step 4: Test with wrong CSRF token
        print(f"\n4. Testing with invalid CSRF token:")
        
        headers_bad_csrf = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': 'invalid-token-12345',
            'Accept': 'application/json'
        }
        
        response = requests.post(
            f"{base_url}/api/auth/register/",
            json={
                'name': 'Bad CSRF User',
                'email': 'badcsrf@example.com',
                'password': 'Password123!',
                'password_confirm': 'Password123!'
            },
            headers=headers_bad_csrf
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_registration()