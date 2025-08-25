#!/usr/bin/env python3
import base64
from fastapi.testclient import TestClient
from main_original_monolith import app

client = TestClient(app)

def test_base64_upload():
    """Test base64 DOCX upload"""
    print("Testing base64 DOCX upload...")
    
    # Read and encode the test DOCX file
    with open("test-resume.docx", "rb") as f:
        file_content = f.read()
        file_content_b64 = base64.b64encode(file_content).decode('utf-8')
    
    # Prepare request data
    request_data = {
        "file_content": file_content_b64,
        "filename": "test-resume.docx",
        "payment_token": None
    }
    
    response = client.post("/api/check-resume-base64", json=request_data)
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success! Analysis Type: {result.get('analysis_type')}")
        print(f"Overall Score: {result.get('overall_score')}")
        print(f"Major Issues: {result.get('major_issues')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_base64_upload()