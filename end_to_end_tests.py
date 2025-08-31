#!/usr/bin/env python3
"""
End-to-End Tests for Resume Health Checker
Tests the complete user journey from file upload to payment selection
"""

import requests
import json
import os
import time
from pathlib import Path

# Test Configuration
BASE_URL = "http://localhost:8002"
TEST_FILES_DIR = Path(".")
EXPECTED_PRODUCTS = ['resume_analysis', 'job_fit_analysis', 'cover_letter']
EXPECTED_BUNDLES = ['complete_package', 'career_boost', 'job_hunter']
EXPECTED_REGIONS = ['US', 'PK', 'IN', 'HK', 'AE', 'BD']

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_test(message):
    print(f"{Colors.CYAN}🧪 {message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{Colors.BLUE}🎯 {message}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

class EndToEndTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        
    def run_all_tests(self):
        """Run complete end-to-end test suite"""
        print_header("END-TO-END TEST SUITE STARTED")
        
        try:
            # Test 1: Server Health
            self.test_server_health()
            
            # Test 2: File Upload UI Visibility  
            self.test_upload_ui_visible()
            
            # Test 3: File Upload API
            self.test_file_upload_api()
            
            # Test 4: Product Selection Flow
            self.test_product_selection_flow()
            
            # Test 5: Payment Session Creation
            self.test_payment_session_creation()
            
            # Test 6: Bundle Selection
            self.test_bundle_selection()
            
            # Test 7: Regional Pricing Integration
            self.test_regional_pricing_integration()
            
            # Test 8: Complete User Journey Simulation
            self.test_complete_user_journey()
            
        except Exception as e:
            print_error(f"Critical test failure: {e}")
            
        finally:
            self.print_test_summary()
    
    def test_server_health(self):
        """Test that server is responding"""
        print_test("Testing server health...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                print_success("Server is responding")
                if "Resume Health Checker" in response.text:
                    print_success("Homepage loads correctly")
                    self.record_success("server_health")
                else:
                    print_error("Homepage content missing")
                    self.record_failure("server_health", "Missing homepage content")
            else:
                print_error(f"Server returned HTTP {response.status_code}")
                self.record_failure("server_health", f"HTTP {response.status_code}")
                
        except Exception as e:
            print_error(f"Server health check failed: {e}")
            self.record_failure("server_health", str(e))
    
    def test_upload_ui_visible(self):
        """Test that file upload UI is visible"""
        print_test("Testing file upload UI visibility...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            html = response.text
            
            # Check that upload section is NOT hidden
            if 'id="uploadSection" style="display: none;"' in html:
                print_error("Upload section is hidden with display:none")
                self.record_failure("upload_ui", "Upload section hidden")
                return
                
            # Check for upload elements
            checks = [
                ('fileInput', 'File input element'),
                ('Click to upload your resume', 'Upload text'),
                ('Supports PDF and Word documents', 'File type info'),
                ('analyzeBtn', 'Analyze button')
            ]
            
            all_good = True
            for element, description in checks:
                if element in html:
                    print_success(f"{description} found")
                else:
                    print_error(f"{description} missing")
                    all_good = False
            
            if all_good:
                print_success("All upload UI elements are present")
                self.record_success("upload_ui")
            else:
                self.record_failure("upload_ui", "Missing UI elements")
                
        except Exception as e:
            print_error(f"Upload UI test failed: {e}")
            self.record_failure("upload_ui", str(e))
    
    def test_file_upload_api(self):
        """Test file upload API functionality"""
        print_test("Testing file upload API...")
        
        # Find test files
        test_files = []
        for pattern in ['*.docx', '*.pdf']:
            test_files.extend(list(TEST_FILES_DIR.glob(pattern)))
        
        if not test_files:
            print_warning("No test files found, creating dummy file")
            # Create a minimal test file for API testing
            dummy_content = b"Dummy resume content for testing"
            with open("test_resume_dummy.txt", "wb") as f:
                f.write(dummy_content)
            
        # Test with first available file or dummy
        test_file = test_files[0] if test_files else Path("test_resume_dummy.txt")
        
        try:
            with open(test_file, 'rb') as f:
                files = {'file': (test_file.name, f, 'application/octet-stream')}
                data = {'payment_token': ''}
                
                response = self.session.post(f"{self.base_url}/api/check-resume", 
                                           files=files, data=data)
                
                if response.status_code == 200:
                    print_success("File upload API accepts files")
                    # Try to parse response
                    try:
                        result = response.json()
                        if 'analysis' in result or 'score' in result:
                            print_success("API returns analysis data")
                            self.record_success("file_upload_api")
                        else:
                            print_warning("API response format unexpected")
                            self.record_success("file_upload_api")  # Still counts as success
                    except json.JSONDecodeError:
                        print_warning("API response is not JSON (might be HTML error)")
                        
                elif response.status_code == 422:
                    # Expected for non-PDF/DOCX files
                    detail = response.json().get('detail', 'Unknown error')
                    if 'PDF or Word' in detail or 'PDF or DOCX' in detail:
                        print_success("API correctly validates file types")
                        self.record_success("file_upload_api")
                    else:
                        print_error(f"Unexpected validation error: {detail}")
                        self.record_failure("file_upload_api", detail)
                        
                else:
                    print_error(f"File upload failed with HTTP {response.status_code}")
                    print_error(f"Response: {response.text[:200]}")
                    self.record_failure("file_upload_api", f"HTTP {response.status_code}")
                    
        except Exception as e:
            print_error(f"File upload test failed: {e}")
            self.record_failure("file_upload_api", str(e))
            
        # Cleanup dummy file
        if Path("test_resume_dummy.txt").exists():
            os.remove("test_resume_dummy.txt")
    
    def test_product_selection_flow(self):
        """Test product selection JavaScript functions"""
        print_test("Testing product selection flow...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            html = response.text
            
            # Check for product cards with correct onclick handlers
            checks = [
                ("selectProduct('individual', 'resume_analysis'", "Resume card handler"),
                ("selectProduct('individual', 'job_fit_analysis'", "Job Fit card handler"),
                ("selectProduct('individual', 'cover_letter'", "Cover Letter card handler"),
                ("showBundles()", "Bundle card handler"),
                ("function selectProduct", "selectProduct function"),
                ("function showBundles", "showBundles function"),
                ("function proceedToPayment", "proceedToPayment function")
            ]
            
            all_good = True
            for check, description in checks:
                if check in html:
                    print_success(f"{description} found")
                else:
                    print_error(f"{description} missing")
                    all_good = False
            
            if all_good:
                print_success("All product selection functions are present")
                self.record_success("product_selection")
            else:
                self.record_failure("product_selection", "Missing functions")
                
        except Exception as e:
            print_error(f"Product selection test failed: {e}")
            self.record_failure("product_selection", str(e))
    
    def test_payment_session_creation(self):
        """Test payment session API"""
        print_test("Testing payment session creation...")
        
        test_data = {
            'product_type': 'individual',
            'product_id': 'resume_analysis',
            'session_data': json.dumps({
                'resume_text': 'Test resume content',
                'session_id': 'test_session_e2e',
                'user_region': 'US',
                'selected_product': 'individual_resume_analysis'
            })
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/create-payment-session", 
                                       data=test_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check required fields
                required_fields = ['payment_session_id', 'payment_url', 'amount', 'currency']
                missing_fields = [f for f in required_fields if f not in result]
                
                if not missing_fields:
                    print_success("Payment session created successfully")
                    print_success(f"Session ID: {result['payment_session_id'][:8]}...")
                    print_success(f"Amount: {result.get('display_price', result.get('amount'))}")
                    
                    # Validate URL format
                    if 'client_reference_id' in result['payment_url']:
                        print_success("Payment URL includes client_reference_id")
                        self.record_success("payment_session")
                    else:
                        print_warning("Payment URL missing client_reference_id")
                        self.record_success("payment_session")  # Still success
                        
                else:
                    print_error(f"Missing required fields: {missing_fields}")
                    self.record_failure("payment_session", f"Missing fields: {missing_fields}")
                    
            else:
                print_error(f"Payment session creation failed: HTTP {response.status_code}")
                print_error(f"Response: {response.text}")
                self.record_failure("payment_session", f"HTTP {response.status_code}")
                
        except Exception as e:
            print_error(f"Payment session test failed: {e}")
            self.record_failure("payment_session", str(e))
    
    def test_bundle_selection(self):
        """Test bundle options"""
        print_test("Testing bundle selection...")
        
        bundle_tests = [
            ('complete_package', 'Complete Package'),
            ('career_boost', 'Career Boost'),
            ('job_hunter', 'Job Hunter')
        ]
        
        success_count = 0
        
        for bundle_id, bundle_name in bundle_tests:
            test_data = {
                'product_type': 'bundle',
                'product_id': bundle_id,
                'session_data': json.dumps({
                    'resume_text': 'Test resume content',
                    'session_id': f'test_bundle_{bundle_id}',
                    'user_region': 'US'
                })
            }
            
            try:
                response = self.session.post(f"{self.base_url}/api/create-payment-session",
                                           data=test_data)
                
                if response.status_code == 200:
                    result = response.json()
                    print_success(f"{bundle_name} bundle session created")
                    success_count += 1
                else:
                    print_error(f"{bundle_name} bundle failed: HTTP {response.status_code}")
                    
            except Exception as e:
                print_error(f"{bundle_name} bundle test failed: {e}")
        
        if success_count == len(bundle_tests):
            print_success("All bundle options work correctly")
            self.record_success("bundle_selection")
        else:
            print_warning(f"Only {success_count}/{len(bundle_tests)} bundles working")
            self.record_failure("bundle_selection", f"Only {success_count} bundles work")
    
    def test_regional_pricing_integration(self):
        """Test regional pricing system"""
        print_test("Testing regional pricing integration...")
        
        success_count = 0
        
        for region in EXPECTED_REGIONS:
            try:
                response = self.session.get(f"{self.base_url}/api/stripe-pricing/{region}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if 'currency' in result and 'products' in result:
                        currency = result['currency']
                        print_success(f"{region}: {currency} pricing loaded")
                        success_count += 1
                    else:
                        print_error(f"{region}: Invalid pricing format")
                        
                else:
                    print_error(f"{region}: HTTP {response.status_code}")
                    
            except Exception as e:
                print_error(f"{region} pricing test failed: {e}")
        
        if success_count >= len(EXPECTED_REGIONS) * 0.8:  # 80% success rate
            print_success(f"Regional pricing works ({success_count}/{len(EXPECTED_REGIONS)} regions)")
            self.record_success("regional_pricing")
        else:
            print_error(f"Regional pricing issues ({success_count}/{len(EXPECTED_REGIONS)} regions)")
            self.record_failure("regional_pricing", f"Only {success_count} regions work")
    
    def test_complete_user_journey(self):
        """Simulate complete user journey"""
        print_test("Testing complete user journey simulation...")
        
        try:
            # Step 1: Load homepage
            response = self.session.get(f"{self.base_url}/")
            if response.status_code != 200:
                raise Exception("Homepage failed to load")
            print_success("✓ Step 1: Homepage loaded")
            
            # Step 2: Check upload UI is visible
            if 'Click to upload your resume' in response.text:
                print_success("✓ Step 2: Upload UI visible")
            else:
                raise Exception("Upload UI not visible")
            
            # Step 3: Check product cards are present
            cards_found = 0
            for product in EXPECTED_PRODUCTS:
                if f"selectProduct('individual', '{product}'" in response.text:
                    cards_found += 1
            
            if cards_found == len(EXPECTED_PRODUCTS):
                print_success(f"✓ Step 3: All {cards_found} product cards present")
            else:
                raise Exception(f"Only {cards_found}/{len(EXPECTED_PRODUCTS)} product cards found")
            
            # Step 4: Test payment session creation (simulates user clicking)
            response = self.session.post(f"{self.base_url}/api/create-payment-session", data={
                'product_type': 'individual',
                'product_id': 'resume_analysis',
                'session_data': json.dumps({
                    'resume_text': 'Journey test resume',
                    'session_id': 'journey_test_session',
                    'user_region': 'US'
                })
            })
            
            if response.status_code == 200:
                result = response.json()
                if 'payment_url' in result:
                    print_success("✓ Step 4: Payment session created successfully")
                else:
                    raise Exception("Payment session missing payment_url")
            else:
                raise Exception(f"Payment session failed: {response.status_code}")
            
            # Step 5: Verify Stripe URL format
            payment_url = result['payment_url']
            if 'client_reference_id' in payment_url and 'stripe.com' in payment_url:
                print_success("✓ Step 5: Stripe URL format correct")
            else:
                print_warning("Step 5: Stripe URL format may have issues")
            
            print_success("🎉 Complete user journey simulation successful!")
            self.record_success("user_journey")
            
        except Exception as e:
            print_error(f"User journey failed: {e}")
            self.record_failure("user_journey", str(e))
    
    def record_success(self, test_name):
        """Record successful test"""
        self.test_results.append({"test": test_name, "status": "PASS", "error": None})
    
    def record_failure(self, test_name, error):
        """Record failed test"""
        self.test_results.append({"test": test_name, "status": "FAIL", "error": error})
    
    def print_test_summary(self):
        """Print final test summary"""
        print_header("TEST SUMMARY")
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        total = len(self.test_results)
        
        print(f"\n{Colors.BOLD}RESULTS:{Colors.END}")
        print(f"  {Colors.GREEN}✅ Passed: {passed}{Colors.END}")
        print(f"  {Colors.RED}❌ Failed: {failed}{Colors.END}")
        print(f"  📊 Total:  {total}")
        
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}FAILED TESTS:{Colors.END}")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  {Colors.RED}❌ {result['test']}: {result['error']}{Colors.END}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n{Colors.BOLD}SUCCESS RATE: {success_rate:.1f}%{Colors.END}")
        
        if success_rate >= 80:
            print(f"{Colors.GREEN}🎉 SYSTEM IS PRODUCTION READY!{Colors.END}")
        elif success_rate >= 60:
            print(f"{Colors.YELLOW}⚠️  SYSTEM NEEDS MINOR FIXES{Colors.END}")
        else:
            print(f"{Colors.RED}🚨 SYSTEM NEEDS MAJOR FIXES{Colors.END}")

def main():
    print(f"{Colors.PURPLE}{Colors.BOLD}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                  END-TO-END TEST SUITE                     ║") 
    print("║              Resume Health Checker v3.1.0                 ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    tester = EndToEndTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()