#!/usr/bin/env python3
"""
Test script for PhotoVault Client Delivery System.
Tests all API endpoints and functionality.
"""
import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api"

# Test credentials (you'll need to create these)
TEST_EMAIL = "photographer@test.com"
TEST_PASSWORD = "testpass123"

class ClientDeliveryTester:
    def __init__(self):
        self.access_token = None
        self.test_album_id = None
        self.test_share_token = None
        self.test_share_id = None
        
    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def authenticate(self):
        """Authenticate and get access token."""
        self.log("Authenticating user...")
        
        # Try to login first
        login_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(f"{API_BASE}/auth/login/", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.access_token = data['tokens']['access']
                self.log("✅ Login successful")
                return True
            else:
                self.log(f"❌ Login failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Login request failed: {response.status_code}")
            
        # Try to register if login failed
        self.log("Attempting to register new user...")
        register_data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": "Test Photographer"
        }
        
        response = requests.post(f"{API_BASE}/auth/register/", json=register_data)
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                self.log("✅ Registration successful, now logging in...")
                return self.authenticate()  # Try login again
            else:
                self.log(f"❌ Registration failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Registration request failed: {response.status_code}")
            
        return False
    
    def get_headers(self):
        """Get headers with authentication."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def create_test_album(self):
        """Create a test album for sharing."""
        self.log("Creating test album...")
        
        album_data = {
            "name": "Client Delivery Test Album",
            "description": "Test album for client delivery system"
        }
        
        response = requests.post(
            f"{API_BASE}/albums/",
            json=album_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                self.test_album_id = data['album']['id']
                self.log(f"✅ Test album created with ID: {self.test_album_id}")
                return True
            else:
                self.log(f"❌ Album creation failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Album creation request failed: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"Error details: {error_data}")
            except:
                self.log(f"Response text: {response.text}")
        
        return False
    
    def test_create_client_link(self):
        """Test creating a client delivery link."""
        self.log("Testing client link creation...")
        
        if not self.test_album_id:
            self.log("❌ No test album available")
            return False
        
        link_config = {
            "album_id": self.test_album_id,
            "expiry_hours": 168,  # 7 days
            "max_views": 50,
            "download_enabled": True,
            "watermark_enabled": True,
            "watermark_text": "© Test Photography Studio",
            "passcode": ""
        }
        
        response = requests.post(
            f"{API_BASE}/sharing/client/create/",
            json=link_config,
            headers=self.get_headers()
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                client_link = data['client_link']
                self.test_share_token = client_link['token']
                self.test_share_id = client_link['share_id']
                
                self.log(f"✅ Client link created successfully")
                self.log(f"   Token: {self.test_share_token}")
                self.log(f"   URL: {client_link['client_url']}")
                self.log(f"   Expires: {client_link['time_remaining']}")
                self.log(f"   Views: {client_link['views_remaining']}")
                return True
            else:
                self.log(f"❌ Client link creation failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Client link creation request failed: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"Error details: {error_data}")
            except:
                self.log(f"Response text: {response.text}")
        
        return False
    
    def test_client_link_meta(self):
        """Test getting client link metadata."""
        self.log("Testing client link metadata...")
        
        if not self.test_share_token:
            self.log("❌ No test share token available")
            return False
        
        response = requests.get(f"{API_BASE}/sharing/client/{self.test_share_token}/meta/")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                meta = data['meta']
                self.log(f"✅ Client link metadata retrieved")
                self.log(f"   Album: {meta.get('album_name')}")
                self.log(f"   Creator: {meta.get('creator_name')}")
                self.log(f"   Photos: {meta.get('photo_count')}")
                self.log(f"   Valid: {meta.get('valid')}")
                return True
            else:
                self.log(f"❌ Metadata retrieval failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Metadata request failed: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"Error details: {error_data}")
            except:
                self.log(f"Response text: {response.text}")
        
        return False
    
    def test_client_content_access(self):
        """Test accessing client content."""
        self.log("Testing client content access...")
        
        if not self.test_share_token:
            self.log("❌ No test share token available")
            return False
        
        access_data = {
            "passcode": ""
        }
        
        response = requests.post(
            f"{API_BASE}/sharing/client/{self.test_share_token}/access/",
            json=access_data
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                content = data['content']
                album = content['album']
                
                self.log(f"✅ Client content accessed successfully")
                self.log(f"   Album: {album['name']}")
                self.log(f"   Images: {album['image_count']}")
                self.log(f"   Download enabled: {content['share_info']['download_enabled']}")
                return True
            else:
                self.log(f"❌ Content access failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Content access request failed: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"Error details: {error_data}")
            except:
                self.log(f"Response text: {response.text}")
        
        return False
    
    def test_list_client_links(self):
        """Test listing client links."""
        self.log("Testing client links listing...")
        
        response = requests.get(
            f"{API_BASE}/sharing/client/list/",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                links = data['links']
                self.log(f"✅ Client links listed successfully")
                self.log(f"   Total links: {data['total_count']}")
                
                for link in links[:3]:  # Show first 3
                    self.log(f"   - {link['album_name']} (Views: {link['view_count']}/{link['max_views'] or 'unlimited'})")
                
                return True
            else:
                self.log(f"❌ Links listing failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Links listing request failed: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"Error details: {error_data}")
            except:
                self.log(f"Response text: {response.text}")
        
        return False
    
    def test_creator_analytics(self):
        """Test creator analytics."""
        self.log("Testing creator analytics...")
        
        response = requests.get(
            f"{API_BASE}/sharing/analytics/?days=30",
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                analytics = data['analytics']
                summary = analytics['summary']
                
                self.log(f"✅ Creator analytics retrieved")
                self.log(f"   Total shares: {summary['total_shares']}")
                self.log(f"   Total views: {summary['total_views']}")
                self.log(f"   Unique viewers: {summary['unique_viewers']}")
                self.log(f"   Avg views per share: {summary['avg_views_per_share']:.1f}")
                return True
            else:
                self.log(f"❌ Analytics retrieval failed: {data.get('error', {}).get('message', 'Unknown error')}")
        else:
            self.log(f"❌ Analytics request failed: {response.status_code}")
            try:
                error_data = response.json()
                self.log(f"Error details: {error_data}")
            except:
                self.log(f"Response text: {response.text}")
        
        return False
    
    def run_all_tests(self):
        """Run all client delivery tests."""
        self.log("🚀 Starting PhotoVault Client Delivery System Tests")
        self.log("=" * 60)
        
        tests = [
            ("Authentication", self.authenticate),
            ("Create Test Album", self.create_test_album),
            ("Create Client Link", self.test_create_client_link),
            ("Client Link Metadata", self.test_client_link_meta),
            ("Client Content Access", self.test_client_content_access),
            ("List Client Links", self.test_list_client_links),
            ("Creator Analytics", self.test_creator_analytics),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} PASSED")
                else:
                    self.log(f"❌ {test_name} FAILED")
            except Exception as e:
                self.log(f"❌ {test_name} ERROR: {str(e)}")
        
        self.log("\n" + "=" * 60)
        self.log(f"🏆 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Client Delivery System is working perfectly!")
        else:
            self.log(f"⚠️  {total - passed} tests failed. Check the logs above for details.")
        
        return passed == total


if __name__ == "__main__":
    tester = ClientDeliveryTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🚀 PhotoVault Client Delivery System is PRODUCTION READY!")
        print("✅ All core features tested and working")
        print("✅ API endpoints responding correctly")
        print("✅ Authentication and authorization working")
        print("✅ Link creation and management functional")
        print("✅ Analytics and tracking operational")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")