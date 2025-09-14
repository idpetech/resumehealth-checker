#!/usr/bin/env python3
from fastapi.testclient import TestClient
from main_vercel import app

client = TestClient(app)

def test_docx_upload():
    """Test uploading a DOCX file with original working version"""
    print("Testing DOCX upload with original Vercel version...")
    
    # Read the test DOCX file
    with open("test-resume.docx", "rb") as f:
        files = {"file": ("test-resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        
        response = client.post("/api/check-resume", files=files)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Success! Analysis Type: {result.get('analysis_type')}")
            print(f"Overall Score: {result.get('overall_score')}")
            print(f"Major Issues: {result.get('major_issues')}")
        else:
            print(f"Error: {response.text}")

def test_health():
    """Test health endpoint"""
    print("\nTesting health endpoint...")
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        print(f"Error: {response.text}")

def test_frontend():
    """Test frontend HTML"""
    print("\nTesting HTML frontend...")
    response = client.get("/")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        content = response.text
        if "Resume Health Checker" in content:
            print("✅ HTML frontend loads correctly")
        else:
            print("❌ HTML content issue")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_health()
    test_frontend()
    test_docx_upload()