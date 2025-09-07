#!/usr/bin/env python3
"""
Debug script to isolate the premium analysis issue.
Test format string handling and JSON structure parsing.
"""
import json
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

def test_format_strings():
    """Test if format strings work correctly in both free and premium prompts"""
    print("🔍 TESTING FORMAT STRINGS...")
    
    # Load prompts
    prompts_file = Path("app/data/prompts.json")
    with open(prompts_file) as f:
        prompts = json.load(f)
    
    # Test data
    test_resume = "John Doe\nSoftware Engineer with 5 years experience in Python and JavaScript."
    
    # Test free prompt formatting
    try:
        free_prompt = prompts["resume_analysis"]["free"]["user_prompt"]
        formatted_free = free_prompt.format(resume_text=test_resume)
        print("✅ Free prompt formatting: SUCCESS")
    except Exception as e:
        print(f"❌ Free prompt formatting: FAILED - {e}")
        return False
    
    # Test premium prompt formatting
    try:
        premium_prompt = prompts["resume_analysis"]["premium"]["user_prompt"]
        formatted_premium = premium_prompt.format(resume_text=test_resume)
        print("✅ Premium prompt formatting: SUCCESS")
    except Exception as e:
        print(f"❌ Premium prompt formatting: FAILED - {e}")
        print(f"Premium prompt preview: {premium_prompt[:200]}...")
        return False
    
    return True

def test_json_structure():
    """Test if the JSON structures in prompts are valid"""
    print("\n🔍 TESTING JSON STRUCTURES...")
    
    # Load prompts
    prompts_file = Path("app/data/prompts.json")
    with open(prompts_file) as f:
        prompts = json.load(f)
    
    # Extract JSON structures from prompts
    free_prompt = prompts["resume_analysis"]["free"]["user_prompt"]
    premium_prompt = prompts["resume_analysis"]["premium"]["user_prompt"]
    
    # Find JSON structures in prompts (look for {{ patterns)
    import re
    
    # Free JSON structure
    free_json_match = re.search(r'\{\{[\s\S]*?\}\}', free_prompt)
    if free_json_match:
        free_json_str = free_json_match.group(0).replace('{{', '{').replace('}}', '}')
        try:
            # Try to parse it with placeholder values
            free_test_json = free_json_str.replace('"A number from 60-85 (stay encouraging)"', '"75"')
            free_test_json = free_test_json.replace('"Specific strength 1 with impact"', '"Test strength"')
            free_test_json = free_test_json.replace('"Specific strength 2 with impact"', '"Test strength 2"')
            free_test_json = free_test_json.replace('"Specific strength 3 with impact"', '"Test strength 3"')
            free_test_json = free_test_json.replace('"Opportunity 1: How to enhance what\'s already good"', '"Test opportunity 1"')
            free_test_json = free_test_json.replace('"Opportunity 2: Quick win that will make a big difference"', '"Test opportunity 2"')
            free_test_json = free_test_json.replace('"Opportunity 3: Strategic addition for maximum impact"', '"Test opportunity 3"')
            free_test_json = free_test_json.replace('"Uplifting message about their potential and next steps - make them feel hopeful and capable"', '"Test message"')
            
            json.loads(free_test_json)
            print("✅ Free JSON structure: VALID")
        except Exception as e:
            print(f"❌ Free JSON structure: INVALID - {e}")
            print(f"Free JSON: {free_test_json}")
    
    # Premium JSON structure
    premium_json_match = re.search(r'\{\{[\s\S]*?\}\}', premium_prompt)
    if premium_json_match:
        premium_json_str = premium_json_match.group(0).replace('{{', '{').replace('}}', '}')
        try:
            # Try to parse it with placeholder values - this is complex due to nested structure
            print(f"Premium JSON structure found: {len(premium_json_str)} characters")
            print("✅ Premium JSON structure: EXTRACTED")
        except Exception as e:
            print(f"❌ Premium JSON structure: EXTRACTION FAILED - {e}")

def main():
    """Main debug function"""
    print("🚀 DEBUGGING PREMIUM ANALYSIS ISSUE")
    print("=" * 50)
    
    # Test format strings
    if not test_format_strings():
        print("\n❌ FORMAT STRING TEST FAILED - This is likely the issue!")
        return
    
    # Test JSON structures
    test_json_structure()
    
    print("\n🔍 SUMMARY:")
    print("If format strings pass but premium still fails in Railway,")
    print("the issue is likely in:")
    print("1. OpenAI response parsing (complex nested JSON)")
    print("2. Token limits being exceeded")
    print("3. OpenAI model struggling with complex JSON structure")

if __name__ == "__main__":
    main()