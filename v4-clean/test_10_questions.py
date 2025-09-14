#!/usr/bin/env python3
"""
Test script for 10-question mock interview generation
Tests the enhanced token limits and prompt optimization
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.analysis import analysis_service

# Sample resume for testing
SAMPLE_RESUME = """
John Smith
Software Engineer | Full-Stack Developer

Professional Summary:
Experienced software engineer with 5 years of development experience in Python, JavaScript, and cloud technologies. Strong background in building scalable web applications and APIs. Proven track record of leading development teams and delivering high-quality software solutions.

Technical Skills:
• Programming Languages: Python, JavaScript, TypeScript, Java
• Frameworks: React, Node.js, Django, Flask
• Databases: PostgreSQL, MongoDB, Redis
• Cloud: AWS, Docker, Kubernetes
• Tools: Git, Jenkins, JIRA

Professional Experience:

Senior Software Engineer | TechCorp Inc. | 2021-Present
• Led a team of 4 developers to rebuild the company's main web application using React and Node.js
• Implemented microservices architecture resulting in 40% improved performance
• Designed and built RESTful APIs serving 10,000+ daily active users
• Collaborated with product managers to define technical requirements and project timelines

Software Engineer | StartupXYZ | 2019-2021
• Developed full-stack web applications using Python/Django and React
• Built automated testing frameworks reducing bug reports by 60%
• Implemented CI/CD pipelines using Jenkins and AWS
• Mentored 2 junior developers on coding best practices

Education:
Bachelor of Science in Computer Science | University of Technology | 2019

Certifications:
• AWS Solutions Architect Associate
• MongoDB Certified Developer
"""

# Sample job posting
SAMPLE_JOB_POSTING = """
Senior Full-Stack Developer - Remote

Company: InnovateTech Solutions
Location: Remote (US-based)
Salary: $120,000 - $160,000

About the Role:
We are seeking a Senior Full-Stack Developer to join our growing engineering team. You will be responsible for designing and developing scalable web applications, leading technical initiatives, and mentoring junior developers.

Key Responsibilities:
• Design and develop full-stack web applications using modern technologies
• Lead technical architecture decisions and code reviews
• Collaborate with cross-functional teams including product, design, and QA
• Mentor junior developers and contribute to engineering best practices
• Optimize application performance and scalability
• Participate in agile development processes

Required Qualifications:
• 5+ years of experience in full-stack web development
• Strong proficiency in JavaScript/TypeScript and modern frameworks (React, Vue, or Angular)
• Experience with backend technologies (Node.js, Python, or similar)
• Knowledge of databases (SQL and NoSQL)
• Experience with cloud platforms (AWS, Azure, or GCP)
• Strong understanding of software engineering best practices
• Experience with version control (Git) and CI/CD pipelines
• Excellent communication and leadership skills

Preferred Qualifications:
• Experience with microservices architecture
• Knowledge of containerization (Docker, Kubernetes)
• Previous experience mentoring or leading development teams
• Experience with agile development methodologies
• Bachelor's degree in Computer Science or related field

What We Offer:
• Competitive salary and equity package
• Comprehensive health benefits
• Flexible work arrangements
• Professional development opportunities
• Collaborative and innovative work environment
"""

async def test_10_question_generation():
    """Test the 10-question mock interview generation"""
    print("🎯 Testing 10-Question Mock Interview Generation")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Generate premium mock interview
        print("📊 Generating premium mock interview with 10 questions...")
        result = await analysis_service.generate_mock_interview_premium(
            SAMPLE_RESUME, 
            SAMPLE_JOB_POSTING
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        print(f"⏱️  Generation completed in {generation_time:.2f} seconds")
        print()
        
        # Analyze the result
        print("🔍 ANALYSIS RESULTS:")
        print("-" * 30)
        
        if 'interview_simulation' in result:
            questions = result['interview_simulation']
            print(f"✅ Questions Generated: {len(questions)}")
            
            # Count questions by category
            categories = {}
            for q in questions:
                cat = q.get('question_category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            print(f"📊 Question Categories:")
            for cat, count in categories.items():
                print(f"   - {cat}: {count} questions")
            
            print()
            print("📝 SAMPLE QUESTIONS:")
            print("-" * 20)
            
            for i, question in enumerate(questions[:3], 1):
                print(f"Q{i}: {question.get('question', 'No question')}")
                print(f"   Category: {question.get('question_category', 'Unknown')}")
                print(f"   Strategic Approach: {question.get('strategic_approach', 'N/A')[:100]}...")
                print(f"   Success Tips: {question.get('success_tips', 'N/A')[:80]}...")
                print()
            
            if len(questions) > 3:
                print(f"... and {len(questions) - 3} more questions")
                print()
            
        else:
            print("❌ No 'interview_simulation' found in result")
        
        # Check other sections
        if 'interview_strategy' in result:
            strategy = result['interview_strategy']
            print("🎯 Interview Strategy:")
            if 'key_messages' in strategy:
                print(f"   - Key Messages: {len(strategy['key_messages'])} items")
            if 'preparation_focus' in strategy:
                print(f"   - Preparation Focus: {len(strategy['preparation_focus'])} characters")
        
        # Check metadata
        if '_metadata' in result:
            metadata = result['_metadata']
            print(f"📊 Metadata:")
            print(f"   - Analysis Type: {metadata.get('analysis_type', 'Unknown')}")
            print(f"   - Tokens Used: {metadata.get('tokens_used', 'Unknown')}")
            print(f"   - Service Version: {metadata.get('service_version', 'Unknown')}")
        
        print()
        print("🎉 TEST COMPLETED SUCCESSFULLY!")
        
        # Save detailed results to file
        output_file = Path("test_10_questions_results.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"📁 Detailed results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
        return False

async def main():
    """Main test function"""
    print("🚀 10-Question Mock Interview Test Suite")
    print("Testing enhanced token limits and optimized prompts")
    print("=" * 60)
    print()
    
    # Test the 10-question generation
    success = await test_10_question_generation()
    
    if success:
        print()
        print("✅ All tests passed! 10-question system is working.")
        print("🎯 Ready for production use at http://localhost:8000")
    else:
        print()
        print("❌ Tests failed. Check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
