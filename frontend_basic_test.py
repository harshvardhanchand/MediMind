#!/usr/bin/env python3
"""
Frontend Basic Testing Script
Tests basic connectivity and configuration of the React Native app
"""

import requests
import json
import time
import subprocess
import re
from datetime import datetime

class FrontendTester:
    def __init__(self):
        self.results = {"passed": 0, "failed": 0, "tests": []}
        self.expo_url = "http://localhost:19006"
        self.backend_url = "http://localhost:8000"
    
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
    
    def test_expo_server_running(self):
        """Test if Expo development server is running"""
        try:
            # Check if Expo process is running
            result = subprocess.run(['pgrep', '-f', 'expo start'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.log_test("Expo Server Running", "PASS", "Process found")
            else:
                self.log_test("Expo Server Running", "FAIL", "No expo process found")
        except Exception as e:
            self.log_test("Expo Server Running", "FAIL", str(e))
    
    def test_expo_web_interface(self):
        """Test if Expo web interface is accessible"""
        try:
            response = requests.get(f"{self.expo_url}/", timeout=5)
            if response.status_code == 200:
                self.log_test("Expo Web Interface", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("Expo Web Interface", "FAIL", f"Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.log_test("Expo Web Interface", "FAIL", f"Connection failed: {str(e)}")
    
    def test_backend_connectivity_from_frontend(self):
        """Test if frontend can reach backend"""
        try:
            # Simulate what the frontend would do - check CORS preflight
            headers = {
                "Origin": "http://localhost:19006",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization, content-type"
            }
            response = requests.options(f"{self.backend_url}/api/health/", 
                                      headers=headers, timeout=5)
            
            if response.status_code == 200:
                required_headers = ["access-control-allow-origin", "access-control-allow-methods"]
                has_cors = all(header in [h.lower() for h in response.headers.keys()] 
                             for header in required_headers)
                
                if has_cors:
                    self.log_test("Frontend-Backend CORS", "PASS", "CORS headers present")
                else:
                    self.log_test("Frontend-Backend CORS", "FAIL", "Missing CORS headers")
            else:
                self.log_test("Frontend-Backend CORS", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend-Backend CORS", "FAIL", str(e))
    
    def test_app_configuration(self):
        """Test app configuration files"""
        try:
            # Check if app.config.js exists and has required fields
            import os
            config_path = "frontend/app.config.js"
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read()
                    
                required_configs = ['supabaseUrl', 'supabaseAnonKey']
                missing_configs = []
                
                for config in required_configs:
                    if config not in content:
                        missing_configs.append(config)
                
                if not missing_configs:
                    self.log_test("App Configuration", "PASS", "All required configs found")
                else:
                    self.log_test("App Configuration", "FAIL", f"Missing: {missing_configs}")
            else:
                self.log_test("App Configuration", "FAIL", "app.config.js not found")
        except Exception as e:
            self.log_test("App Configuration", "FAIL", str(e))
    
    def test_environment_variables(self):
        """Test if required environment variables are accessible"""
        try:
            # Check if .env file exists in frontend directory
            import os
            env_path = "frontend/.env"
            
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    content = f.read()
                    
                required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
                missing_vars = []
                
                for var in required_vars:
                    if var not in content:
                        missing_vars.append(var)
                
                if not missing_vars:
                    self.log_test("Environment Variables", "PASS", "All required vars found")
                else:
                    self.log_test("Environment Variables", "FAIL", f"Missing: {missing_vars}")
            else:
                self.log_test("Environment Variables", "WARN", ".env file not found")
        except Exception as e:
            self.log_test("Environment Variables", "FAIL", str(e))
    
    def check_dependencies(self):
        """Check if key dependencies are installed"""
        try:
            # Check package.json for critical dependencies
            with open("frontend/package.json", 'r') as f:
                package_data = json.load(f)
                
            critical_deps = [
                'expo', 'react', 'react-native', '@supabase/supabase-js',
                '@react-navigation/native', 'axios'
            ]
            
            dependencies = {**package_data.get('dependencies', {}), 
                          **package_data.get('devDependencies', {})}
            
            missing_deps = []
            for dep in critical_deps:
                if dep not in dependencies:
                    missing_deps.append(dep)
            
            if not missing_deps:
                self.log_test("Critical Dependencies", "PASS", f"All {len(critical_deps)} found")
            else:
                self.log_test("Critical Dependencies", "FAIL", f"Missing: {missing_deps}")
                
        except Exception as e:
            self.log_test("Critical Dependencies", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run all frontend tests"""
        print("🧪 Starting Frontend Basic Tests...")
        print(f"📱 Testing Expo app and configuration...")
        print("-" * 50)
        
        # Basic connectivity tests
        self.test_expo_server_running()
        self.test_expo_web_interface()
        self.test_backend_connectivity_from_frontend()
        
        # Configuration tests
        self.test_app_configuration()
        self.test_environment_variables()
        self.check_dependencies()
        
        # Print summary
        print("-" * 50)
        print(f"📊 Frontend Test Summary:")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        total_tests = self.results['passed'] + self.results['failed']
        if total_tests > 0:
            success_rate = (self.results['passed'] / total_tests) * 100
            print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.results['failed'] == 0

def main():
    """Main test execution"""
    tester = FrontendTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open("frontend_test_results.json", "w") as f:
        json.dump(tester.results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: frontend_test_results.json")
    
    if success:
        print("\n🎉 All frontend basic tests passed!")
        print("✅ Ready for manual app testing on device/simulator")
        print("\n📱 Next steps:")
        print("   1. Open Expo Go app on your device")
        print("   2. Scan QR code from terminal")
        print("   3. Test app manually using frontend_test_checklist.md")
    else:
        print("\n⚠️  Some frontend tests failed.")
        print("   Fix issues before proceeding to manual testing")

if __name__ == "__main__":
    main() 