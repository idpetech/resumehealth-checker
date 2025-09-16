#!/usr/bin/env python3
"""
UI Regression Test Suite
Automated tests to prevent breaking existing functionality in future sprints.
Run this before any deployment to verify all UI/export functionality works.
"""

import requests
import time
import sys
from bs4 import BeautifulSoup
import json

BASE_URL = "http://localhost:8000"

class UIRegressionTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    def log(self, message, status="INFO"):
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "🔍"
        print(f"{emoji} {message}")
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
            
    def test_javascript_functions_exist(self, analysis_id, template_type):
        """Test that required JavaScript functions exist in the HTML"""
        self.log(f"Testing JavaScript functions for {template_type} template...")
        
        url = f"{BASE_URL}/api/v1/premium-results/{analysis_id}?embedded=true&product_type={template_type}"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                self.log(f"Failed to get {template_type} template: {response.status_code}", "FAIL")
                return False
            
            html_content = response.text
            
            # Test 1: Main page should have global functions
            main_response = requests.get(f"{BASE_URL}/", timeout=30)
            main_html = main_response.text
            
            required_functions = ['exportToPDFClient', 'exportToWord', 'copyToClipboard']
            if template_type == 'mock_interview':
                required_functions.extend(['toggleQuestion', 'toggleAllQuestions'])
                
            for func in required_functions:
                if f"function {func}" in main_html:
                    self.log(f"✓ Function {func} found in main page", "PASS")
                else:
                    self.log(f"✗ Function {func} missing from main page", "FAIL")
                    return False
            
            # Test 2: Template should call the functions correctly
            if template_type == 'mock_interview':
                if 'onclick="toggleAllQuestions()"' in html_content:
                    self.log("✓ Expand All button has correct onclick handler", "PASS")
                else:
                    self.log("✗ Expand All button missing or wrong handler", "FAIL")
                    return False
            
            if 'onclick="exportToPDFClient(' in html_content:
                self.log("✓ PDF export button has correct onclick handler", "PASS")
            else:
                self.log("✗ PDF export button missing or wrong handler", "FAIL")
                return False
                
            if 'onclick="exportToWord(' in html_content:
                self.log("✓ DOCX export button has correct onclick handler", "PASS")
            else:
                self.log("✗ DOCX export button missing or wrong handler", "FAIL")
                return False
            
            # Test 3: Required libraries should be loaded
            libraries = ['jspdf', 'html2canvas']
            for lib in libraries:
                if lib in main_html.lower():
                    self.log(f"✓ Library {lib} found", "PASS")
                else:
                    self.log(f"✗ Library {lib} missing", "FAIL")
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Error testing {template_type}: {e}", "FAIL")
            return False
    
    def test_template_structure(self, analysis_id, template_type):
        """Test that templates have the correct structure for exports"""
        self.log(f"Testing template structure for {template_type}...")
        
        url = f"{BASE_URL}/api/v1/premium-results/{analysis_id}?embedded=true&product_type={template_type}"
        try:
            response = requests.get(url, timeout=30)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Test 1: Premium results container exists
            premium_results = soup.find(class_='premium-results')
            if premium_results:
                self.log("✓ .premium-results container found", "PASS")
            else:
                self.log("✗ .premium-results container missing", "FAIL")
                return False
            
            # Test 2: Template-specific structure
            if template_type == 'mock_interview':
                # Should have expandable questions
                questions = soup.find_all(id=lambda x: x and x.startswith('details-'))
                if len(questions) > 0:
                    self.log(f"✓ Found {len(questions)} expandable questions", "PASS")
                else:
                    self.log("✗ No expandable questions found", "FAIL")
                    return False
                
                # Should have expand all button
                expand_btn = soup.find('button', {'onclick': 'toggleAllQuestions()'})
                if expand_btn:
                    self.log("✓ Expand All button found", "PASS")
                else:
                    self.log("✗ Expand All button missing", "FAIL")
                    return False
            
            elif template_type == 'resume_rewrite':
                # Should have analysis section
                analysis_section = soup.find(class_='analysis-section')
                if analysis_section:
                    self.log("✓ Analysis section found", "PASS")
                else:
                    self.log("✗ Analysis section missing", "FAIL")
                    return False
                
                # Analysis section should have page break style
                if 'page-break-before: always' in str(analysis_section):
                    self.log("✓ Analysis section has page break styling", "PASS")
                else:
                    self.log("✗ Analysis section missing page break styling", "FAIL")
                    return False
            
            # Test 3: Export buttons exist
            pdf_btn = soup.find('button', class_='pdf-btn') or soup.find(attrs={'onclick': lambda x: x and 'exportToPDFClient' in x})
            if pdf_btn:
                self.log("✓ PDF export button found", "PASS")
            else:
                self.log("✗ PDF export button missing", "FAIL")
                return False
            
            docx_btn = soup.find('button', class_='docx-btn') or soup.find(attrs={'onclick': lambda x: x and 'exportToWord' in x})
            if docx_btn:
                self.log("✓ DOCX export button found", "PASS")
            else:
                self.log("✗ DOCX export button missing", "FAIL")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Error testing template structure: {e}", "FAIL")
            return False
    
    def test_export_logic_implementation(self):
        """Test that export functions have the correct logic implemented"""
        self.log("Testing export function logic implementation...")
        
        try:
            # Get main page to check function implementations
            response = requests.get(f"{BASE_URL}/", timeout=30)
            html_content = response.text
            
            # Test 1: PDF export should have interview expansion logic
            if 'Interview template detected, expanding all questions for PDF export' in html_content:
                self.log("✓ PDF export has interview expansion logic", "PASS")
            else:
                self.log("✗ PDF export missing interview expansion logic", "FAIL")
                return False
            
            # Test 2: PDF export should have resume analysis hiding logic
            if 'Resume rewrite template detected, hiding analysis section for PDF export' in html_content:
                self.log("✓ PDF export has analysis section hiding logic", "PASS")
            else:
                self.log("✗ PDF export missing analysis section hiding logic", "FAIL")
                return False
            
            # Test 3: DOCX export should have analysis section removal logic
            if 'Resume rewrite template detected, removing analysis section from DOCX export' in html_content:
                self.log("✓ DOCX export has analysis section removal logic", "PASS")
            else:
                self.log("✗ DOCX export missing analysis section removal logic", "FAIL")
                return False
            
            # Test 4: State restoration logic exists
            if 'Restore original interview question states' in html_content:
                self.log("✓ State restoration logic found", "PASS")
            else:
                self.log("✗ State restoration logic missing", "FAIL")
                return False
            
            # Test 5: ToggleAllQuestions should use .every() logic
            if '.every(detail =>' in html_content:
                self.log("✓ toggleAllQuestions uses .every() logic", "PASS")
            else:
                self.log("✗ toggleAllQuestions missing .every() logic", "FAIL")
                return False
            
            return True
            
        except Exception as e:
            self.log(f"Error testing export logic: {e}", "FAIL")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.log("🚀 Starting UI Regression Test Suite...")
        self.log("=" * 60)
        
        # Test data - using IDs from recent server logs
        test_cases = [
            ("7727435f-88a4-4d29-8ab7-638e37b50b82", "mock_interview"),
            ("79e0c5bb-12b5-4cd5-936d-6e86ede37bb4", "resume_rewrite"),
        ]
        
        all_passed = True
        
        # Test 1: JavaScript Functions
        self.log("\n📋 Testing JavaScript Functions...")
        for analysis_id, template_type in test_cases:
            if not self.test_javascript_functions_exist(analysis_id, template_type):
                all_passed = False
        
        # Test 2: Template Structure
        self.log("\n🏗️ Testing Template Structure...")
        for analysis_id, template_type in test_cases:
            if not self.test_template_structure(analysis_id, template_type):
                all_passed = False
        
        # Test 3: Export Logic Implementation
        self.log("\n⚙️ Testing Export Logic Implementation...")
        if not self.test_export_logic_implementation():
            all_passed = False
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        self.log(f"Total Tests: {self.passed + self.failed}")
        self.log(f"Passed: {self.passed}")
        self.log(f"Failed: {self.failed}")
        
        if all_passed and self.failed == 0:
            self.log("\n🎉 ALL TESTS PASSED - UI functionality is preserved!", "PASS")
            return True
        else:
            self.log(f"\n💥 {self.failed} TESTS FAILED - Regressions detected!", "FAIL")
            return False

def main():
    """Main test runner"""
    tester = UIRegressionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Safe to deploy - no regressions detected")
        sys.exit(0)
    else:
        print("\n❌ DO NOT DEPLOY - fix regressions first")
        sys.exit(1)

if __name__ == "__main__":
    main()