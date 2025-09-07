#!/usr/bin/env python3
"""
Check Stripe Configuration
Quick script to verify your Stripe keys are properly configured
"""
import os
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

try:
    from app.core.config import config
    import stripe
    
    print("🔍 Checking Stripe Configuration...")
    print(f"Environment: {config.environment}")
    print(f"Base URL: {config.base_url}")
    print()
    
    # Check Stripe keys
    if config.stripe_secret_key:
        if "placeholder" in config.stripe_secret_key or "your-" in config.stripe_secret_key:
            print("❌ Stripe Secret Key: PLACEHOLDER (not configured)")
            print(f"   Current value: {config.stripe_secret_key[:20]}...")
        else:
            print(f"✅ Stripe Secret Key: CONFIGURED ({config.stripe_secret_key[:20]}...)")
            
            # Test the connection
            try:
                stripe.api_key = config.stripe_secret_key
                balance = stripe.Balance.retrieve()
                print("✅ Stripe Connection: WORKING")
                print(f"   Account balance: {balance.available[0].amount / 100:.2f} {balance.available[0].currency.upper()}")
            except stripe.error.AuthenticationError as e:
                print(f"❌ Stripe Connection: AUTHENTICATION FAILED")
                print(f"   Error: {e}")
            except Exception as e:
                print(f"❌ Stripe Connection: FAILED")
                print(f"   Error: {e}")
    else:
        print("❌ Stripe Secret Key: NOT SET")
    
    print()
    
    if config.stripe_publishable_key:
        if "placeholder" in config.stripe_publishable_key or "your-" in config.stripe_publishable_key:
            print("❌ Stripe Publishable Key: PLACEHOLDER (not configured)")
        else:
            print(f"✅ Stripe Publishable Key: CONFIGURED ({config.stripe_publishable_key[:20]}...)")
    else:
        print("❌ Stripe Publishable Key: NOT SET")
    
    print()
    print("🔧 To fix mock payments:")
    print("1. Set real Stripe test keys in your environment variables")
    print("2. Keys should start with 'sk_test_' and 'pk_test_'")
    print("3. Get them from: https://dashboard.stripe.com/test/apikeys")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
except Exception as e:
    print(f"❌ Error: {e}")


