#!/usr/bin/env python3
"""
Local Testing Script for Resume Health Checker v4.0

Tests the complete application flow using Stripe sandbox.
Run this after setting up your environment variables.
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

import requests
from test_config import setup_test_environment, get_test_stripe_cards, get_test_resume_files

class LocalTester:
    """Comprehensive local testing for the application"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.analysis_id = None
        self.payment_session_id = None
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_health_check(self) -> bool:
        """Test application health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status')}")
                return True
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_file_upload(self) -> bool:
        """Test resume file upload and analysis with real PDF files"""
        try:
            # Use real resume files from parent directory
            test_files = get_test_resume_files()
            
            success_count = 0
            for file_info in test_files:
                filename = file_info["filename"]
                file_path = file_info["path"]
                content_type = file_info["content_type"]
                
                if not file_path.exists():
                    self.log_test(f"File Upload - {filename}", False, f"File not found: {file_path}")
                    continue
                
                # Upload file
                with open(file_path, "rb") as f:
                    files = {"file": (filename, f, content_type)}
                    data = {"analysis_type": "free"}
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/analyze",
                        files=files,
                        data=data,
                        timeout=30
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    if not self.analysis_id:  # Store first successful analysis ID
                        self.analysis_id = result.get("analysis_id")
                    self.log_test(f"File Upload - {filename}", True, 
                                f"Analysis ID: {result.get('analysis_id')}")
                    success_count += 1
                else:
                    self.log_test(f"File Upload - {filename}", False, 
                                f"Status: {response.status_code}, Response: {response.text}")
            
            if success_count > 0:
                self.log_test("File Upload & Analysis", True, 
                            f"Successfully processed {success_count}/{len(test_files)} files")
                return True
            else:
                self.log_test("File Upload & Analysis", False, "No files processed successfully")
                return False
                
        except Exception as e:
            self.log_test("File Upload & Analysis", False, f"Error: {str(e)}")
            return False
    
    def test_payment_session_creation(self) -> bool:
        """Test Stripe payment session creation"""
        if not self.analysis_id:
            self.log_test("Payment Session Creation", False, "No analysis ID available")
            return False
        
        try:
            data = {
                "analysis_id": self.analysis_id,
                "product_type": "resume_analysis"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/payment/create",
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                payment_session = result.get("payment_session", {})
                self.payment_session_id = payment_session.get("session_id")
                
                self.log_test("Payment Session Creation", True,
                            f"Session ID: {self.payment_session_id}")
                self.log_test("Payment Session URL", True,
                            f"URL: {payment_session.get('session_url', 'N/A')}")
                return True
            else:
                self.log_test("Payment Session Creation", False,
                            f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Payment Session Creation", False, f"Error: {str(e)}")
            return False
    
    def test_regional_pricing(self) -> bool:
        """Test regional pricing detection"""
        try:
            # Test different regions
            regions = ["US", "PK", "IN", "HK", "AE", "BD"]
            success_count = 0
            
            for region in regions:
                response = requests.get(f"{self.base_url}/api/v1/pricing/{region}", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    pricing = data.get("pricing", {})
                    currency = pricing.get("currency", "N/A")
                    self.log_test(f"Regional Pricing - {region}", True, f"Currency: {currency}")
                    success_count += 1
                else:
                    self.log_test(f"Regional Pricing - {region}", False,
                                f"Status: {response.status_code}")
            
            return success_count == len(regions)
            
        except Exception as e:
            self.log_test("Regional Pricing", False, f"Error: {str(e)}")
            return False
    
    def test_analysis_retrieval(self) -> bool:
        """Test analysis result retrieval"""
        if not self.analysis_id:
            self.log_test("Analysis Retrieval", False, "No analysis ID available")
            return False
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/analysis/{self.analysis_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Analysis Retrieval", True,
                            f"Type: {data.get('analysis_type')}, Status: {data.get('payment_status')}")
                return True
            else:
                self.log_test("Analysis Retrieval", False,
                            f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Analysis Retrieval", False, f"Error: {str(e)}")
            return False
    
    def test_stripe_webhook_simulation(self) -> bool:
        """Test webhook endpoint (simulation)"""
        try:
            # Simulate a webhook payload (without signature verification)
            webhook_payload = {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_123",
                        "payment_status": "paid",
                        "amount_total": 1000,
                        "currency": "usd"
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/webhooks/stripe",
                json=webhook_payload,
                headers={"stripe-signature": "test_signature"},
                timeout=10
            )
            
            # We expect this to fail due to signature verification, but endpoint should exist
            if response.status_code in [400, 401]:  # Expected for invalid signature
                self.log_test("Webhook Endpoint", True, "Endpoint exists and validates signatures")
                return True
            else:
                self.log_test("Webhook Endpoint", False,
                            f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Webhook Endpoint", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("🧪 Starting Local Testing Suite")
        print("=" * 50)
        
        # Set up test environment
        setup_test_environment()
        
        # Run tests in order
        tests = [
            ("Health Check", self.test_health_check),
            ("File Upload & Analysis", self.test_file_upload),
            ("Payment Session Creation", self.test_payment_session_creation),
            ("Regional Pricing", self.test_regional_pricing),
            ("Analysis Retrieval", self.test_analysis_retrieval),
            ("Webhook Endpoint", self.test_stripe_webhook_simulation),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
        
        print("=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Ready for Railway staging deployment.")
        else:
            print("⚠️ Some tests failed. Review issues before proceeding.")
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "failed_tests": total - passed,
            "success_rate": (passed / total) * 100,
            "test_results": self.test_results
        }

def main():
    """Main testing function"""
    print("🚀 Resume Health Checker v4.0 - Local Testing")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding. Please start the application first:")
            print("   python main.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ Server not running. Please start the application first:")
        print("   python main.py")
        sys.exit(1)
    
    # Run tests
    tester = LocalTester()
    results = tester.run_all_tests()
    
    # Save results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Test results saved to: test_results.json")
    
    # Print Stripe test cards for manual testing
    print("\n💳 Stripe Test Cards for Manual Testing:")
    test_cards = get_test_stripe_cards()
    for card_type, card_number in test_cards.items():
        print(f"   {card_type}: {card_number}")

if __name__ == "__main__":
    main()
