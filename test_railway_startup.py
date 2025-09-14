#!/usr/bin/env python3
"""
Test Railway Startup
This script tests if the v4-clean application can start properly with Railway environment variables.
"""

import os
import sys
from pathlib import Path

# Set up Railway-like environment variables
os.environ["ENVIRONMENT"] = "staging"
os.environ["OPENAI_API_KEY"] = "sk-proj-PLACEHOLDER_REPLACE_WITH_REAL_KEY"
os.environ["STRIPE_SECRET_TEST_KEY"] = "sk_test_PLACEHOLDER_REPLACE_WITH_REAL_KEY"
os.environ["STRIPE_PUBLISHABLE_TEST_KEY"] = "pk_test_PLACEHOLDER_REPLACE_WITH_REAL_KEY"
os.environ["STRIPE_WEBHOOK_TEST_SECRET"] = "whsec_1234567890abcdef_TEMP_FOR_STAGING"
os.environ["RAILWAY_STAGING_URL"] = "https://web-staging-f53d.up.railway.app"
os.environ["DATABASE_PATH"] = "staging_database.db"
os.environ["PORT"] = "8000"

# Add v4-clean to the path
sys.path.insert(0, str(Path(__file__).parent / "v4-clean"))

def test_config_loading():
    """Test that configuration loads properly"""
    print("🔧 Testing Configuration Loading...")
    
    try:
        from app.core.config import config
        
        print(f"✅ Environment: {config.environment}")
        print(f"✅ Base URL: {config.base_url}")
        print(f"✅ Database Path: {config.database_path}")
        print(f"✅ OpenAI Key Length: {len(config.openai_api_key)}")
        print(f"✅ Stripe Secret Key Length: {len(config.stripe_secret_key)}")
        print(f"✅ Use Test Keys: {config.use_stripe_test_keys}")
        
        return True
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_init():
    """Test database initialization"""
    print("\n🗄️ Testing Database Initialization...")
    
    try:
        from app.core.database import init_db
        
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("\n🚀 Testing FastAPI App Creation...")
    
    try:
        from fastapi import FastAPI
        from app.core.config import config
        from app.core.exceptions import add_exception_handlers
        
        app = FastAPI(
            title="Resume Health Checker",
            description="AI-powered resume analysis with premium upgrades",
            version="4.0.0"
        )
        
        add_exception_handlers(app)
        print("✅ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating FastAPI app: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_health_endpoint():
    """Test health endpoint creation"""
    print("\n🏥 Testing Health Endpoint...")
    
    try:
        from fastapi import FastAPI
        from app.core.config import config
        
        app = FastAPI()
        
        @app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "version": "4.0.0",
                "environment": config.environment,
                "timestamp": "2025-09-02T12:00:00Z"
            }
        
        print("✅ Health endpoint created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating health endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Testing Railway Startup Process")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_database_init,
        test_app_creation,
        test_health_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Railway startup should work.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

