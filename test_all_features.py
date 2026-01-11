#!/usr/bin/env python3
"""
Comprehensive Feature Testing Script for PhotoVault
Tests all 47 features systematically with detailed reporting
"""
import requests
import json
import time
import os
from datetime import datetime

BASE_URL = "http://localhost:8000"

class PhotoVaultFeatureTester:
    """Comprehensive tester for all PhotoVault features."""
    
    def __init__(self):
        self.results = {}
        self.tokens = {}
        self.test_data = {}
        
    def log_test(self, category, feature, status, details=""):
        """Log test result."""
        if category not in self.results:
            self.results[category] = {}
        
        self.results[category][feature] = {
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"   {status_icon} {feature}: {status}")
        if details and status != "PASS":
            print(f"      Details: {details}")
    
    def make_request(self, method, endpoint, data=None, token=None, files=None):
        """Make HTTP request with proper headers."""
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, headers=headers, files=files, data=data)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'PATCH':
                response = requests.patch(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                return None
            
            return response
        except Exception as e:
            return None
    
    def test_authentication_system(self):
        """Test all 8 authentication features."""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM (8 Features)")
        print("=" * 60)
        
        # 1. User registration with email verification
        reg_data = {
            "name": "Test Feature User",
            "email": "featuretest@example.com",
            "password": "FeatureTest123!",
            "password_confirm": "FeatureTest123!"
        }
        
        response = self.make_request('POST', '/api/auth/register/', reg_data)
        if response and response.status_code == 201:
            self.log_test("Authentication", "User Registration", "PASS")
        else:
            self.log_test("Authentication", "User Registration", "FAIL", 
                         f"Status: {response.status_code if response else 'No response'}")
        
        # 2. Secure login with JWT tokens
        login_data = {
            "email": "john@example.com",
            "password": "UserPass123!"
        }
        
        response = self.make_request('POST', '/api/auth/login/', login_data)
        if response and response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                self.tokens['john'] = data['access_token']
                self.log_test("Authentication", "JWT Login", "PASS")
            else:
                self.log_test("Authentication", "JWT Login", "FAIL", "No access token in response")
        else:
            self.log_test("Authentication", "JWT Login", "FAIL", 
                         f"Status: {response.status_code if response else 'No response'}")
        
        # 3. Password reset via email
        reset_data = {"email": "john@example.com"}
        response = self.make_request('POST', '/api/auth/password/reset/', reset_data)
        if response and response.status_code == 200:
            self.log_test("Authentication", "Password Reset Request", "PASS")
        else:
            self.log_test("Authentication", "Password Reset Request", "FAIL",
                         f"Status: {response.status_code if response else 'No response'}")
        
        # 4. Account lockout protection
        # Test with locked user
        locked_login = {
            "email": "locked@example.com",
            "password": "UserPass123!"
        }
        response = self.make_request('POST', '/api/auth/login/', locked_login)
        if response and response.status_code == 400:
            data = response.json()
            if 'locked' in str(data).lower():
                self.log_test("Authentication", "Account Lockout Protection", "PASS")
            else:
                self.log_test("Authentication", "Account Lockout Protection", "PARTIAL", 
                             "Account exists but lockout message unclear")
        else:
            self.log_test("Authentication", "Account Lockout Protection", "FAIL",
                         f"Expected 400, got {response.status_code if response else 'No response'}")
        
        # 5. Profile management
        if 'john' in self.tokens:
            response = self.make_request('GET', '/api/auth/me/', token=self.tokens['john'])
            if response and response.status_code == 200:
                self.log_test("Authentication", "Profile Management", "PASS")
            else:
                self.log_test("Authentication", "Profile Management", "FAIL",
                             f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Authentication", "Profile Management", "SKIP", "No valid token")
        
        # 6. Google OAuth (structure check)
        response = self.make_request('POST', '/api/auth/google/', {"access_token": "fake_token"})
        if response and response.status_code in [400, 401]:  # Expected for fake token
            self.log_test("Authentication", "Google OAuth Structure", "PASS")
        else:
            self.log_test("Authentication", "Google OAuth Structure", "FAIL",
                         f"Endpoint not responding correctly")
        
        # 7. Session management
        if 'john' in self.tokens:
            response = self.make_request('POST', '/api/auth/logout/', 
                                       {"refresh_token": "fake"}, self.tokens['john'])
            if response and response.status_code in [200, 400]:  # Either works or validates token
                self.log_test("Authentication", "Session Management", "PASS")
            else:
                self.log_test("Authentication", "Session Management", "FAIL",
                             f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Authentication", "Session Management", "SKIP", "No valid token")
        
        # 8. Admin user roles
        admin_login = {
            "email": "admin@photovault.com",
            "password": "AdminPass123!"
        }
        response = self.make_request('POST', '/api/auth/login/', admin_login)
        if response and response.status_code == 200:
            data = response.json()
            if 'access_token' in data:
                self.tokens['admin'] = data['access_token']
                # Check if user has admin privileges
                response = self.make_request('GET', '/api/auth/me/', token=self.tokens['admin'])
                if response and response.status_code == 200:
                    user_data = response.json()
                    if user_data.get('is_admin', False):
                        self.log_test("Authentication", "Admin User Roles", "PASS")
                    else:
                        self.log_test("Authentication", "Admin User Roles", "PARTIAL", 
                                     "Admin login works but is_admin flag not set")
                else:
                    self.log_test("Authentication", "Admin User Roles", "FAIL", "Cannot get admin profile")
            else:
                self.log_test("Authentication", "Admin User Roles", "FAIL", "No admin token")
        else:
            self.log_test("Authentication", "Admin User Roles", "FAIL", "Admin login failed")
    
    def test_image_management_system(self):
        """Test all 12 image management features."""
        print("\n📸 TESTING IMAGE MANAGEMENT SYSTEM (12 Features)")
        print("=" * 60)
        
        if 'john' not in s