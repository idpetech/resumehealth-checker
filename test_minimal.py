#!/usr/bin/env python3
import asyncio
from fastapi.testclient import TestClient
from main_minimal import app

client = TestClient(app)

def test_docx_upload():
    """Test uploading a DOCX file"""
    print("Testing DOCX upload...")
    
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
    response = client.get("/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_health()
    test_docx_upload()