#!/usr/bin/env python3
"""
Check Test Files Script

Verifies that the real resume files exist and are accessible for testing.
"""
from pathlib import Path
from test_config import get_test_resume_files

def check_test_files():
    """Check if all test resume files exist"""
    print("🔍 Checking Test Resume Files")
    print("=" * 40)
    
    test_files = get_test_resume_files()
    all_exist = True
    
    for file_info in test_files:
        filename = file_info["filename"]
        file_path = file_info["path"]
        content_type = file_info["content_type"]
        
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✅ {filename}")
            print(f"   Path: {file_path}")
            print(f"   Size: {file_size:,} bytes")
            print(f"   Type: {content_type}")
        else:
            print(f"❌ {filename}")
            print(f"   Path: {file_path}")
            print(f"   Status: FILE NOT FOUND")
            all_exist = False
        print()
    
    if all_exist:
        print("🎉 All test files are available!")
        print("✅ Ready to run: python test_local.py")
    else:
        print("⚠️ Some test files are missing.")
        print("Please ensure the resume files are in the parent directory.")
    
    return all_exist

if __name__ == "__main__":
    check_test_files()


