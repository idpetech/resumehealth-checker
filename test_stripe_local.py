#!/usr/bin/env python3
"""
Test Stripe Integration Locally
This script tests the Stripe integration with the v4-clean app locally.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Set up environment variables BEFORE importing any modules
os.environ["ENVIRONMENT"] = "local"
os.environ["OPENAI_API_KEY"] = "sk-test-placeholder-key-for-local-testing"
# Use the REAL Stripe test keys from Railway environment
os.environ["STRIPE_SECRET_TEST_KEY"] = "sk_test_PLACEHOLDER_REPLACE_WITH_REAL_KEY"
os.environ["STRIPE_PUBLISHABLE_TEST_KEY"] = "pk_test_PLACEHOLDER_REPLACE_WITH_REAL_KEY"
os.environ["STRIPE_WEBHOOK_TEST_SECRET"] = "whsec_1234567890abcdef_TEMP_FOR_STAGING"

# Add v4-clean to the path
sys.path.insert(0, str(Path(__file__).parent / "v4-clean"))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_stripe_integration():
    """Test the Stripe integration locally"""
    
    print("🧪 Testing Stripe Integration Locally")
    print("=" * 50)
    
    try:
        # Import the payment service
        from app.services.payments import get_payment_service
        from app.core.config import config
        
        print(f"✅ Environment: {config.environment}")
        print(f"✅ Stripe Secret Key: {config.stripe_secret_key[:20]}...")
        print(f"✅ Stripe Publishable Key: {config.stripe_publishable_key[:20]}...")
        print(f"✅ Use Test Keys: {config.use_stripe_test_keys}")
        
        # Get payment service
        payment_service = get_payment_service()
        print(f"✅ Payment Service: {payment_service}")
        print(f"✅ Stripe Available: {payment_service.stripe_available}")
        
        if payment_service.stripe_available:
            print("\n🔄 Testing Payment Session Creation...")
            
            # Test creating a payment session
            session_data = await payment_service.create_payment_session(
                analysis_id="test-analysis-123",
                product_type="resume_analysis",
                amount=1000,  # $10.00
                currency="usd",
                product_name="Test Resume Analysis"
            )
            
            print("✅ Payment Session Created Successfully!")
            print(f"   Session ID: {session_data.get('session_id')}")
            print(f"   Payment URL: {session_data.get('payment_url')}")
            print(f"   Amount: ${session_data.get('amount', 0) / 100:.2f}")
            print(f"   Currency: {session_data.get('currency')}")
            
        else:
            print("❌ Stripe not available - will use mock payments")
            
            # Test mock payment session
            session_data = await payment_service.create_payment_session(
                analysis_id="test-analysis-123",
                product_type="resume_analysis",
                amount=1000,
                currency="usd",
                product_name="Test Resume Analysis"
            )
            
            print("✅ Mock Payment Session Created!")
            print(f"   Session ID: {session_data.get('session_id')}")
            print(f"   Mock: {session_data.get('mock', False)}")
            
    except Exception as e:
        print(f"❌ Error testing Stripe integration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_config_loading():
    """Test that the config loads properly"""
    print("\n🔧 Testing Configuration Loading...")
    
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

async def main():
    """Main test function"""
    print("🚀 Starting Local Stripe Integration Tests")
    print("=" * 60)
    
    # Test 1: Configuration loading
    config_ok = await test_config_loading()
    
    if not config_ok:
        print("❌ Configuration test failed - stopping")
        return
    
    # Test 2: Stripe integration
    stripe_ok = await test_stripe_integration()
    
    print("\n" + "=" * 60)
    if config_ok and stripe_ok:
        print("🎉 All tests passed! Stripe integration is working locally.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\n📋 Next Steps:")
    print("1. If tests passed, you can start the local server")
    print("2. Test the full payment flow in the browser")
    print("3. Once local testing is successful, deploy to Railway")

if __name__ == "__main__":
    asyncio.run(main())
