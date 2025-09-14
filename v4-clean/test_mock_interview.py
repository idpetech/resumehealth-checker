#!/usr/bin/env python3
"""
Test script to debug mock interview generation issue
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.analysis import AnalysisService
from app.core.config import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_mock_interview():
    """Test mock interview generation with sample data"""
    
    # Sample resume text
    resume_text = """
    John Smith
    Software Engineer
    john.smith@email.com
    
    PROFESSIONAL SUMMARY
    Experienced software engineer with 5 years of experience in web development, 
    specializing in Python, JavaScript, and database design. Proven track record 
    of delivering scalable applications and leading development teams.
    
    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2021-2023
    • Developed and maintained web applications serving 10,000+ users
    • Led team of 3 junior developers on e-commerce platform
    • Implemented CI/CD pipelines reducing deployment time by 50%
    
    Software Engineer | StartupXYZ | 2019-2021
    • Built RESTful APIs using Python Flask and PostgreSQL
    • Collaborated with product team to deliver new features
    • Improved application performance by 30% through code optimization
    
    EDUCATION
    Bachelor of Science in Computer Science | University of Tech | 2019
    
    SKILLS
    Python, JavaScript, React, Flask, Django, PostgreSQL, AWS, Docker
    """
    
    # Sample job posting
    job_posting = """
    Senior Full Stack Developer - TechStartup Inc.
    
    We are looking for a Senior Full Stack Developer to join our growing team. 
    You will be responsible for developing and maintaining our web applications 
    using modern technologies.
    
    Requirements:
    • 4+ years of experience in web development
    • Strong proficiency in Python and JavaScript
    • Experience with React and modern frontend frameworks
    • Database design and optimization skills
    • Experience with cloud platforms (AWS preferred)
    • Leadership experience and mentoring junior developers
    
    Responsibilities:
    • Design and implement scalable web applications
    • Collaborate with cross-functional teams
    • Code review and maintain code quality standards
    • Mentor junior developers
    """
    
    try:
        # Initialize analysis service
        analysis_service = AnalysisService()
        
        print("🧪 Testing Mock Interview Generation")
        print("=" * 50)
        
        # Test free version
        print("\n📋 Testing FREE mock interview...")
        free_result = await analysis_service.generate_mock_interview_preview(
            resume_text, job_posting
        )
        
        print(f"Free result keys: {list(free_result.keys())}")
        if 'sample_questions' in free_result:
            print(f"Free sample questions count: {len(free_result['sample_questions'])}")
            for i, q in enumerate(free_result.get('sample_questions', [])):
                print(f"  Q{i+1}: {q.get('question', 'No question')[:100]}...")
        
        print("\n💎 Testing PREMIUM mock interview...")
        premium_result = await analysis_service.generate_mock_interview_premium(
            resume_text, job_posting
        )
        
        print(f"Premium result keys: {list(premium_result.keys())}")
        if 'interview_simulation' in premium_result:
            print(f"Premium interview simulation count: {len(premium_result['interview_simulation'])}")
            for i, q in enumerate(premium_result.get('interview_simulation', [])):
                print(f"  Q{i+1}: {q.get('question', 'No question')[:100]}...")
                print(f"       Category: {q.get('question_category', 'Unknown')}")
        else:
            print("❌ No 'interview_simulation' key found in premium result!")
            print(f"Available keys: {list(premium_result.keys())}")
        
        # Save results for inspection
        with open('mock_interview_test_results.json', 'w') as f:
            json.dump({
                'free_result': free_result,
                'premium_result': premium_result
            }, f, indent=2)
        
        print(f"\n📄 Results saved to: mock_interview_test_results.json")
        
        # Check if we can render the template
        from app.api.routes import generate_embedded_mock_interview_html
        try:
            html_output = generate_embedded_mock_interview_html(premium_result, "test-id")
            print(f"\n🎭 Template rendering: SUCCESS")
            print(f"HTML length: {len(html_output)} characters")
            
            # Save HTML for inspection
            with open('mock_interview_test_output.html', 'w') as f:
                f.write(html_output)
            print(f"HTML saved to: mock_interview_test_output.html")
            
        except Exception as e:
            print(f"\n❌ Template rendering FAILED: {e}")
        
        print("\n✅ Mock interview test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mock_interview())
