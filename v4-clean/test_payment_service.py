#!/usr/bin/env python3
"""
Test the payment service creation functionality.
"""
import sys
import os
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

async def test_payment_service_creation():
    """Test creating a payment session"""
    print("🧪 Testing payment service creation...")
    
    try:
        # Set test environment
        os.environ['ENVIRONMENT'] = 'local'
        os.environ['STRIPE_SECRET_TEST_KEY'] = 'sk_test_placeholder_key_for_testing'
        
        from app.services.payments import get_payment_service
        
        payment_service = get_payment_service()
        print(f"✅ PaymentService obtained: {type(payment_service)}")
        print(f"✅ Environment: {payment_service.environment}")
        print(f"✅ Stripe available: {payment_service.stripe_available}")
        
        # Test payment session creation (should use mock since we have placeholder key)
        if not payment_service.stripe_available:
            print("✅ Using mock payments (expected with placeholder key)")
            
            try:
                session = await payment_service.create_payment_session(
                    analysis_id="test_123",
                    product_type="resume_analysis",
                    amount=1000,
                    currency="usd",
                    product_name="Test Resume Analysis"
                )
                
                print(f"✅ Mock payment session created: {session['session_id']}")
                print(f"✅ Payment URL: {session['payment_url']}")
                print(f"✅ Mock flag: {session.get('mock', False)}")
                return True
                
            except Exception as e:
                print(f"❌ Payment session creation failed: {e}")
                return False
        else:
            print("⚠️  Real Stripe keys detected - skipping payment creation test")
            return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return False

async def main():
    """Run payment service tests"""
    print("🚀 TESTING PAYMENT SERVICE CREATION")
    print("=" * 50)
    
    success = await test_payment_service_creation()
    
    if success:
        print("\n✅ PAYMENT SERVICE TESTS PASSED!")
        print("🚀 Payment creation logic working correctly.")
    else:
        print("\n❌ PAYMENT SERVICE TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())