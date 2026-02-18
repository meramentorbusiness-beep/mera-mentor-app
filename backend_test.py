#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime
import time

class MeraMentorAPITester:
    def __init__(self, base_url="https://learn-earn-19.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {details}")
        else:
            self.failed_tests.append(name)
            print(f"❌ {name}: FAILED {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status=None, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.session_token:
            test_headers['Authorization'] = f'Bearer {self.session_token}'
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            if expected_status and response.status_code != expected_status:
                return self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {}
            
            return self.log_test(name, True, f"Status: {response.status_code}"), response_data, response.status_code

        except Exception as e:
            return self.log_test(name, False, f"Error: {str(e)}"), {}, 0

    def setup_test_user(self):
        """Create test user and session using MongoDB as per auth_testing.md"""
        print("\n🔧 Setting up test user and session...")
        import subprocess
        
        timestamp = int(time.time())
        user_id = f"test-user-{timestamp}"
        session_token = f"test_session_{timestamp}"
        email = f"test.user.{timestamp}@example.com"
        referral_code = f"REF{str(timestamp)[-6:].upper()}"
        
        mongo_script = f"""
use('test_database');
db.users.insertOne({{
  user_id: '{user_id}',
  email: '{email}',
  name: 'Test User',
  picture: 'https://via.placeholder.com/150',
  referral_code: '{referral_code}',
  referred_by: null,
  referral_chain: [],
  phone: '+919876543210',
  status: 'active',
  is_admin: false,
  created_at: new Date().toISOString()
}});
db.user_sessions.insertOne({{
  user_id: '{user_id}',
  session_token: '{session_token}',
  expires_at: new Date(Date.now() + 7*24*60*60*1000).toISOString(),
  created_at: new Date().toISOString()
}});
"""
        
        try:
            result = subprocess.run(['mongosh', '--eval', mongo_script], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.session_token = session_token
                self.user_data = {
                    'user_id': user_id,
                    'email': email,
                    'referral_code': referral_code
                }
                print(f"✅ Test user created: {email}")
                print(f"✅ Session token: {session_token}")
                return True
            else:
                print(f"❌ MongoDB setup failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error setting up test user: {str(e)}")
            return False

    def test_public_endpoints(self):
        """Test public endpoints that don't require auth"""
        print("\n📂 Testing Public Endpoints...")
        
        # Test courses endpoint
        success, data, status = self.run_test("Get Courses", "GET", "courses", 200)
        if success and isinstance(data, list):
            print(f"   Found {len(data)} courses")
            for course in data[:2]:  # Show first 2 courses
                lesson_count = course.get('lesson_count', 0)
                print(f"   - {course.get('title', 'Unknown')}: {lesson_count} lessons, ₹{course.get('price', 0)}")
        
        # Test commission levels endpoint
        success, data, status = self.run_test("Get Commission Levels", "GET", "commission-levels", 200)
        if success and 'levels' in data:
            print(f"   Commission structure: {len(data['levels'])} levels")
            for level in data['levels'][:3]:  # Show first 3 levels
                print(f"   - Level {level['level']}: {level['percentage']}% (₹{level['example_earning']} on ₹500)")

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n🔐 Testing Auth Endpoints...")
        
        # Test /auth/me with valid session
        success, data, status = self.run_test("Get Current User", "GET", "auth/me", 200)
        if success:
            print(f"   User: {data.get('name', 'Unknown')} ({data.get('email', 'No email')})")
            print(f"   Referral Code: {data.get('referral_code', 'None')}")
            return data
        return None

    def test_referral_endpoints(self):
        """Test referral-related endpoints"""
        print("\n👥 Testing Referral Endpoints...")
        
        # Test referral stats
        success, data, status = self.run_test("Get Referral Stats", "GET", "referrals/stats", 200)
        if success:
            print(f"   Today: ₹{data.get('earned_today', 0)}, Week: ₹{data.get('earned_week', 0)}, Lifetime: ₹{data.get('earned_lifetime', 0)}")
            print(f"   Total Referred: {data.get('total_referred', 0)}")
        
        # Test referral counts
        success, data, status = self.run_test("Get Referral Counts", "GET", "referrals/counts", 200)
        if success:
            print(f"   Pending: {data.get('pending', 0)}, Active: {data.get('active', 0)}, Churned: {data.get('churned', 0)}")
        
        # Test referred users
        success, data, status = self.run_test("Get Referred Users", "GET", "referrals/users?status=all", 200)
        if success:
            print(f"   Total referred users retrieved: {len(data) if isinstance(data, list) else 0}")

    def test_wallet_endpoints(self):
        """Test wallet-related endpoints"""
        print("\n💰 Testing Wallet Endpoints...")
        
        # Test wallet info
        success, data, status = self.run_test("Get Wallet", "GET", "wallet", 200)
        if success:
            print(f"   Balance: ₹{data.get('balance', 0)}")
            print(f"   Total Earned: ₹{data.get('total_earned', 0)}")
            print(f"   Total Withdrawn: ₹{data.get('total_withdrawn', 0)}")
        
        # Test wallet transactions
        success, data, status = self.run_test("Get Wallet Transactions", "GET", "wallet/transactions", 200)
        if success:
            commissions = data.get('commissions', [])
            payouts = data.get('payouts', [])
            print(f"   Commissions: {len(commissions)}, Payouts: {len(payouts)}")

    def test_payment_endpoints(self):
        """Test payment-related endpoints"""
        print("\n💳 Testing Payment Endpoints (MOCK Mode)...")
        
        # First get a course to create order for
        success, courses, status = self.run_test("Get Courses for Payment", "GET", "courses", 200)
        if not success or not courses:
            print("   ⚠️ No courses available for payment testing")
            return
        
        test_course = courses[0]
        course_id = test_course.get('course_id')
        print(f"   Testing with course: {test_course.get('title')} (₹{test_course.get('price')})")
        
        # Test create order
        success, order_data, status = self.run_test(
            "Create Payment Order", 
            "POST", 
            "payments/create-order", 
            200,
            {"course_id": course_id}
        )
        
        if success:
            print(f"   Order ID: {order_data.get('order_id')}")
            print(f"   Amount: ₹{order_data.get('amount', 0) / 100}")
            print(f"   Razorpay Enabled: {order_data.get('razorpay_enabled', False)}")
            
            # Test verify payment (mock)
            order_id = order_data.get('order_id')
            success, purchase_data, status = self.run_test(
                "Verify Payment (Mock)", 
                "POST", 
                "payments/verify", 
                200,
                {
                    "order_id": order_id,
                    "course_id": course_id,
                    "razorpay_order_id": f"mock_{order_id}",
                    "razorpay_payment_id": "mock_payment_123",
                    "razorpay_signature": "mock_signature"
                }
            )
            
            if success:
                print(f"   Purchase ID: {purchase_data.get('purchase_id')}")
                print(f"   Course: {purchase_data.get('course_title')}")
                print("   ✅ Mock payment flow completed successfully")

    def test_admin_endpoints(self):
        """Test admin endpoints (if user is admin)"""
        print("\n🛡️ Testing Admin Endpoints...")
        
        # Make current user admin for testing
        if self.user_data:
            import subprocess
            mongo_script = f"""
use('test_database');
db.users.updateOne(
    {{user_id: '{self.user_data['user_id']}'}},
    {{$set: {{is_admin: true}}}}
);
"""
            try:
                subprocess.run(['mongosh', '--eval', mongo_script], 
                             capture_output=True, text=True, timeout=10)
                print("   Made test user admin for testing")
            except:
                print("   ⚠️ Could not make user admin")
        
        # Test admin stats
        success, data, status = self.run_test("Get Admin Stats", "GET", "admin/stats", expected_status=200)
        if success:
            print(f"   Total Users: {data.get('total_users', 0)}")
            print(f"   Total Purchases: {data.get('total_purchases', 0)}")
            print(f"   Total Revenue: ₹{data.get('total_revenue', 0)}")
            print(f"   Total Commissions: ₹{data.get('total_commissions', 0)}")

    def test_course_access(self):
        """Test course access after purchase"""
        print("\n📚 Testing Course Access...")
        
        # Get courses to test access
        success, courses, status = self.run_test("Get Courses for Access Test", "GET", "courses", 200)
        if success and courses:
            course_id = courses[0].get('course_id')
            
            # Test course lessons (should work if purchased, else 403)
            success, data, status = self.run_test(
                f"Get Course Lessons", 
                "GET", 
                f"courses/{course_id}/lessons"
            )
            
            if status == 200:
                lessons = data.get('lessons', [])
                resources = data.get('resources', [])
                print(f"   ✅ Access granted: {len(lessons)} lessons, {len(resources)} resources")
            elif status == 403:
                print(f"   ⚠️ Access denied (403) - purchase required (expected)")
            else:
                print(f"   ❓ Unexpected status: {status}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Mera Mentor API Testing...")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Setup test user
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Cannot proceed with auth tests.")
            return False
        
        # Test public endpoints
        self.test_public_endpoints()
        
        # Test authenticated endpoints
        user = self.test_auth_endpoints()
        if user:
            self.test_referral_endpoints()
            self.test_wallet_endpoints()
            self.test_payment_endpoints()
            self.test_admin_endpoints()
            self.test_course_access()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        return len(self.failed_tests) == 0

def main():
    tester = MeraMentorAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())