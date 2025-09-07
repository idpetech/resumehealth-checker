#!/usr/bin/env python3
"""
Test script to compare OpenAI responses between local and Railway environments.
This will help identify if the issue is response truncation or parsing.
"""
import json
import os
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

async def test_openai_premium_response():
    """Test actual OpenAI API call with premium prompt"""
    try:
        from app.services.analysis import analysis_service
        
        # Test resume text
        test_resume = """
        John Doe
        Senior Software Engineer
        
        Experience:
        • 5 years developing Python applications
        • Led team of 3 developers on microservices project
        • Reduced system latency by 40% through optimization
        
        Skills: Python, JavaScript, AWS, Docker, Kubernetes
        Education: BS Computer Science, University of Technology
        """
        
        print("🚀 Testing OpenAI Premium Analysis...")
        print(f"Resume length: {len(test_resume)} characters")
        print(f"OpenAI API Key set: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
        
        # Call premium analysis
        result = await analysis_service.analyze_resume(
            resume_text=test_resume,
            analysis_type="premium"
        )
        
        print(f"✅ Premium analysis result type: {type(result)}")
        print(f"✅ Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check if result contains expected premium fields
        expected_premium_fields = [
            "overall_score", 
            "strength_highlights", 
            "ats_optimization",
            "content_enhancement", 
            "text_rewrites",
            "competitive_advantages"
        ]
        
        missing_fields = []
        for field in expected_premium_fields:
            if field not in result:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing expected fields: {missing_fields}")
            print(f"🔍 Actual result: {json.dumps(result, indent=2)}")
        else:
            print("✅ All expected premium fields present")
            
        return result
        
    except Exception as e:
        print(f"❌ Premium analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Main test function"""
    print("🔍 TESTING PREMIUM OPENAI RESPONSES")
    print("=" * 50)
    
    # Load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Test premium response
    result = await test_openai_premium_response()
    
    if result and isinstance(result, dict):
        if "error" in result:
            print(f"\n❌ ISSUE FOUND: {result['error']}")
            if "raw_response" in result:
                print(f"📄 Raw OpenAI Response (first 500 chars):")
                print(result["raw_response"])
        else:
            print("\n✅ Premium analysis working correctly!")
    else:
        print("\n❌ Premium analysis returned None or invalid result")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())