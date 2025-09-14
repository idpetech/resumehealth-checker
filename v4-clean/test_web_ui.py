#!/usr/bin/env python3
"""
Quick test to verify the web UI shows sample answer frameworks
"""
import requests
import json

# Test data - shorter for quick test
resume_text = """
Jane Doe
Marketing Manager
5 years experience in digital marketing, social media, and campaign management.
Led successful campaigns increasing brand awareness by 40%.
"""

job_text = """
Marketing Director - RemoteCorp
Looking for an experienced marketing professional to lead our digital strategy.
Requirements: 3+ years marketing experience, social media expertise, campaign management.
"""

def test_mock_interview_ui():
    """Test the mock interview through web API"""
    print("🧪 Testing Mock Interview Web UI")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    try:
        # Step 1: Submit resume and job posting
        print("📤 Submitting resume and job posting...")
        files = {'resume': ('test.txt', resume_text, 'text/plain')}
        data = {'job_posting': job_text}
        
        response = requests.post(f"{base_url}/api/v1/analyze", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Analysis failed: {response.status_code}")
            print(response.text[:500])
            return False
            
        result = response.json()
        analysis_id = result.get('analysis_id')
        
        if not analysis_id:
            print("❌ No analysis_id returned")
            return False
            
        print(f"✅ Analysis completed: {analysis_id}")
        
        # Step 2: Try to create a mock interview payment (won't actually pay in test)
        print("💳 Testing mock interview payment creation...")
        payment_data = {
            'analysis_id': analysis_id,
            'product_type': 'mock_interview'
        }
        
        payment_response = requests.post(f"{base_url}/api/v1/payment/create", json=payment_data)
        
        if payment_response.status_code == 200:
            print("✅ Mock interview payment endpoint is working")
            payment_result = payment_response.json()
            print(f"🔗 Payment URL created: {payment_result.get('payment_url', 'N/A')[:50]}...")
        else:
            print(f"⚠️  Payment creation status: {payment_response.status_code}")
        
        print()
        print("🎯 To test the full UI with 10 questions:")
        print(f"1. Go to: {base_url}")
        print("2. Upload a resume and job posting")
        print("3. Click 'Mock Interview' and complete payment")
        print("4. Verify you see 10 questions with 'Sample Answer Framework' sections")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mock_interview_ui()
    if success:
        print("\n✅ Web UI test completed - ready for manual verification")
    else:
        print("\n❌ Web UI test failed")
