"""
Test Configuration for Stripe Sandbox Testing

This file contains test-specific settings and utilities for local testing.
"""
import os
from pathlib import Path

# Test Environment Variables
TEST_ENV_VARS = {
    "ENVIRONMENT": "local",
    "DEBUG": "true", 
    "PORT": "8000",
    "DATABASE_PATH": "test_database.db",
    "RAILWAY_STAGING_URL": "http://localhost:8000",
    "RAILWAY_PRODUCTION_URL": "http://localhost:8000"
}

def setup_test_environment():
    """Set up environment variables for testing"""
    for key, value in TEST_ENV_VARS.items():
        os.environ[key] = value
    
    print("✅ Test environment variables set")
    print("📝 Required environment variables:")
    print("   - OPENAI_API_KEY=sk-...")
    print("   - STRIPE_SECRET_TEST_KEY=sk_test_...")
    print("   - STRIPE_PUBLISHABLE_TEST_KEY=pk_test_...")
    print("   - STRIPE_WEBHOOK_TEST_SECRET=whsec_...")

def get_test_stripe_cards():
    """Return Stripe test card numbers for testing"""
    return {
        "success": "4242424242424242",
        "declined": "4000000000000002", 
        "insufficient_funds": "4000000000009995",
        "expired": "4000000000000069",
        "cvc_fail": "4000000000000127",
        "processing_error": "4000000000000119"
    }

def get_test_resume_files():
    """Return list of real resume files for testing"""
    parent_dir = Path(__file__).parent.parent
    return [
        {
            "filename": "ResumeLAW.docx",
            "path": parent_dir / "ResumeLAW.docx", 
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
    ]

def get_test_analysis_data():
    """Return sample resume text for testing (fallback)"""
    return """
    John Doe
    Software Engineer
    john.doe@email.com | (555) 123-4567
    
    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2020-2023
    - Led development of microservices architecture
    - Improved system performance by 40%
    - Mentored 5 junior developers
    
    Software Engineer | StartupXYZ | 2018-2020
    - Built REST APIs using Python and FastAPI
    - Implemented automated testing pipeline
    - Collaborated with cross-functional teams
    
    EDUCATION
    Bachelor of Computer Science | University of Tech | 2018
    
    SKILLS
    Python, FastAPI, SQL, Docker, AWS, Git
    """
