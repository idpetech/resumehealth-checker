#!/usr/bin/env python3
"""
Test the dynamic Stripe loading functionality locally before deploying to Railway.
"""
import sys
from pathlib import Path
import os

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_stripe_loading():
    """Test the get_stripe_lib function"""
    print("🧪 Testing dynamic Stripe library loading...")
    
    try:
        from app.services.payments import get_stripe_lib, PaymentService
        
        # Test 1: Check if get_stripe_lib works
        print("\n1️⃣ Testing get_stripe_lib() function...")
        stripe = get_stripe_lib()
        
        if stripe is None:
            print("❌ Stripe library not available (expected in environment without stripe)")
            return False
        
        print("✅ Stripe library loaded successfully")
        print(f"✅ Stripe version: {stripe.version.VERSION if hasattr(stripe, 'version') else 'unknown'}")
        
        # Test 2: Check required attributes
        print("\n2️⃣ Testing Stripe library attributes...")
        required_attrs = ['checkout', 'Balance', 'Webhook']
        
        for attr in required_attrs:
            if hasattr(stripe, attr):
                print(f"✅ stripe.{attr} available")
            else:
                print(f"❌ stripe.{attr} missing")
                return False
        
        # Test 3: Check checkout.Session
        if hasattr(stripe.checkout, 'Session'):
            print("✅ stripe.checkout.Session available")
        else:
            print("❌ stripe.checkout.Session missing")
            return False
        
        # Test 4: Initialize PaymentService
        print("\n3️⃣ Testing PaymentService initialization...")
        
        # Set a test environment
        os.environ['ENVIRONMENT'] = 'local'
        os.environ['STRIPE_SECRET_TEST_KEY'] = 'sk_test_placeholder_key_for_testing'
        
        payment_service = PaymentService()
        print(f"✅ PaymentService initialized")
        print(f"✅ Environment: {payment_service.environment}")
        print(f"✅ Stripe available: {payment_service.stripe_available}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

def test_import_path():
    """Test that imports work correctly"""
    print("\n🔍 Testing import paths...")
    
    try:
        from app.core.config import config
        print(f"✅ Config loaded - Environment: {config.environment}")
        
        from app.services.payments import get_payment_service
        print("✅ Payment service import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING STRIPE DYNAMIC LOADING BEFORE DEPLOYMENT")
    print("=" * 60)
    
    # Test imports first
    if not test_import_path():
        print("\n❌ IMPORT TESTS FAILED - Do not deploy!")
        sys.exit(1)
    
    # Test Stripe loading
    if not test_stripe_loading():
        print("\n❌ STRIPE LOADING TESTS FAILED - Do not deploy!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Safe to deploy to Railway!")
    print("🚀 The dynamic Stripe loading fix should work correctly.")

if __name__ == "__main__":
    main()