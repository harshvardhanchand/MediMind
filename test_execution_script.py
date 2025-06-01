#!/usr/bin/env python3
"""
Medical Data Hub - E2E Testing Script
Automated testing of backend API endpoints
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.results = {"passed": 0, "failed": 0, "tests": []}
    
    def log_test(self, name, status, details=""):
        """Log test results"""
        self.results["tests"].append({
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        if status == "PASS":
            self.results["passed"] += 1
            print(f"✅ {name}")
        else:
            self.results["failed"] += 1
            print(f"❌ {name}: {details}")
    
    def test_api_health(self):
        """Test if API is responding"""
        try:
            response = self.session.get(f"{API_BASE_URL}/docs")
            if response.status_code == 200:
                self.log_test("API Documentation Accessible", "PASS")
            else:
                self.log_test("API Documentation", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Health", "FAIL", str(e))
    
    def test_protected_endpoint_without_auth(self):
        """Test that protected endpoints reject unauthenticated requests"""
        try:
            response = self.session.get(f"{API_BASE_URL}/users/me")
            # Accept either 401 or 403 - both are valid for missing authentication
            if response.status_code in [401, 403]:
                self.log_test("Protected Endpoint Rejects Unauth", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Protected Endpoint Security", "FAIL", f"Expected 401 or 403, got {response.status_code}")
        except Exception as e:
            self.log_test("Protected Endpoint Test", "FAIL", str(e))
    
    def test_openapi_spec(self):
        """Test that OpenAPI spec is available"""
        try:
            response = self.session.get(f"{API_BASE_URL}/openapi.json")
            if response.status_code == 200:
                spec = response.json()
                if "paths" in spec and len(spec["paths"]) > 0:
                    self.log_test("OpenAPI Spec Available", "PASS", f"Found {len(spec['paths'])} endpoints")
                else:
                    self.log_test("OpenAPI Spec", "FAIL", "No paths found in spec")
            else:
                self.log_test("OpenAPI Spec", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("OpenAPI Spec", "FAIL", str(e))
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            # Test preflight request with proper headers
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization, content-type"
            }
            response = self.session.options(f"{API_BASE_URL}/health/", headers=headers)
            
            required_cors_headers = [
                "access-control-allow-origin",
                "access-control-allow-methods",
                "access-control-allow-credentials"
            ]
            
            missing_headers = []
            for header in required_cors_headers:
                if header not in [h.lower() for h in response.headers.keys()]:
                    missing_headers.append(header)
            
            if not missing_headers and response.status_code == 200:
                self.log_test("CORS Headers Present", "PASS", f"All required headers found")
            else:
                self.log_test("CORS Headers", "FAIL", f"Status: {response.status_code}, Missing: {missing_headers}")
        except Exception as e:
            self.log_test("CORS Headers", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 Starting Backend API E2E Tests...")
        print(f"⏰ Testing API at: {API_BASE_URL}")
        print("-" * 50)
        
        # Test basic connectivity
        self.test_api_health()
        self.test_openapi_spec()
        self.test_protected_endpoint_without_auth()
        self.test_cors_headers()
        
        # Print summary
        print("-" * 50)
        print(f"📊 Test Summary:")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"📈 Success Rate: {(self.results['passed']/(self.results['passed']+self.results['failed'])*100):.1f}%")
        
        # Return status for script exit code
        return self.results['failed'] == 0

def main():
    """Main test execution"""
    tester = APITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open("test_results.json", "w") as f:
        json.dump(tester.results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: test_results.json")
    
    if not success:
        print("\n⚠️  Some tests failed. Check the issues before proceeding to frontend testing.")
        sys.exit(1)
    else:
        print("\n🎉 All backend tests passed! Ready for frontend testing.")
        sys.exit(0)

if __name__ == "__main__":
    main() 