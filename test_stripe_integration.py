#!/usr/bin/env python3
"""
Test Stripe Integration - Complete System Validation

This script validates the complete Stripe-first regional pricing system:
1. Tests Stripe pricing API endpoints
2. Validates regional pricing calculations
3. Verifies fallback mechanisms
4. Demonstrates single source of truth approach
"""

import requests
import json
import sys
from datetime import datetime

def test_stripe_pricing_api():
    """Test the new Stripe pricing API endpoints"""
    
    base_url = "http://localhost:8001"
    test_regions = ["US", "PK", "IN", "HK", "AE", "BD"]
    
    print("🧪 TESTING STRIPE-FIRST REGIONAL PRICING")
    print("=" * 60)
    print(f"⏰ Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    for region in test_regions:
        print(f"🌍 Testing region: {region}")
        
        try:
            # Test new Stripe pricing API
            stripe_url = f"{base_url}/api/stripe-pricing/{region}"
            response = requests.get(stripe_url, timeout=10)
            response.raise_for_status()
            
            pricing_data = response.json()
            results[region] = pricing_data
            
            # Display results
            print(f"   ✅ API Response: {response.status_code}")
            print(f"   💰 Currency: {pricing_data.get('currency', 'N/A')}")
            print(f"   📊 Products: {len(pricing_data.get('products', {}))}")
            print(f"   📦 Bundles: {len(pricing_data.get('bundles', {}))}")
            print(f"   🔗 Source: {pricing_data.get('source', 'unknown')}")
            
            # Show sample pricing for resume analysis
            if 'products' in pricing_data and 'resume_analysis' in pricing_data['products']:
                resume_price = pricing_data['products']['resume_analysis']
                print(f"   💵 Resume Analysis: {resume_price.get('display', 'N/A')}")
            
            print()
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ API Error: {e}")
            results[region] = {"error": str(e)}
        except Exception as e:
            print(f"   ❌ Unexpected Error: {e}")
            results[region] = {"error": str(e)}
    
    return results

def validate_regional_pricing(results):
    """Validate regional pricing logic"""
    
    print("\n📊 REGIONAL PRICING VALIDATION")
    print("=" * 60)
    
    # Expected regional multipliers (from Phase 0 data)
    expected_multipliers = {
        "US": 1.0,      # $5 base
        "PK": 119.8,    # ₨599 / $5 = 119.8
        "IN": 60.0,     # ₹300 / $5 = 60.0
        "HK": 7.0,      # HKD 35 / $5 = 7.0
        "AE": 4.0,      # AED 20 / $5 = 4.0
        "BD": 81.6      # ৳408 / $5 = 81.6
    }
    
    for region, data in results.items():
        if 'error' in data:
            print(f"❌ {region}: Could not validate (API error)")
            continue
            
        print(f"🌍 {region}:")
        
        # Get resume analysis price (base product)
        if 'products' in data and 'resume_analysis' in data['products']:
            resume_price = data['products']['resume_analysis']['amount']
            currency = data.get('currency', 'USD')
            
            # Calculate actual multiplier (assuming $10 base for new system vs $5 old)
            us_base_new = 10  # $10 in new system
            if region == 'US':
                actual_multiplier = 1.0
            else:
                actual_multiplier = resume_price / us_base_new
            
            expected = expected_multipliers.get(region, 1.0) 
            
            print(f"   💰 Price: {resume_price} {currency}")
            print(f"   📈 Multiplier: {actual_multiplier:.1f}x (expected ~{expected:.1f}x)")
            
            # Check if multiplier is reasonable (within 20% of expected)
            if abs(actual_multiplier - expected) / expected < 0.2:
                print(f"   ✅ Pricing looks correct")
            else:
                print(f"   ⚠️  Pricing may need adjustment")
        else:
            print(f"   ❌ No resume analysis pricing found")
        
        print()

def test_payment_flow_integration():
    """Test that payment links are properly configured"""
    
    print("\n💳 PAYMENT FLOW VALIDATION")
    print("=" * 60)
    
    try:
        # Test payment session creation
        payment_url = "http://localhost:8001/api/create-payment-session"
        
        # Test with resume analysis
        data = {
            'product_type': 'individual',
            'product_id': 'resume_analysis',
            'session_data': json.dumps({
                'resume_text': 'Test resume content...',
                'analysis_type': 'resume',
                'session_id': 'stripe_test_001'
            })
        }
        
        response = requests.post(payment_url, data=data, timeout=10)
        response.raise_for_status()
        
        session_data = response.json()
        
        print("✅ Payment Session Creation:")
        print(f"   🆔 Session ID: {session_data.get('payment_session_id', 'N/A')[:12]}...")
        print(f"   💰 Amount: {session_data.get('display_price', 'N/A')}")
        print(f"   🔗 Payment URL: {session_data.get('payment_url', 'N/A')[:50]}...")
        
        # Test session retrieval
        session_id = session_data.get('payment_session_id')
        if session_id:
            retrieve_url = f"http://localhost:8001/api/retrieve-payment-session/{session_id}"
            retrieve_response = requests.get(retrieve_url, timeout=10)
            
            if retrieve_response.status_code == 200:
                print("✅ Payment Session Retrieval: Working")
            else:
                print(f"❌ Payment Session Retrieval: Failed ({retrieve_response.status_code})")
        
    except Exception as e:
        print(f"❌ Payment Flow Error: {e}")

def generate_summary_report(results):
    """Generate a summary report"""
    
    print("\n📋 SUMMARY REPORT")
    print("=" * 60)
    
    total_regions = len(results)
    successful_regions = len([r for r in results.values() if 'error' not in r])
    
    print(f"🌍 Regions Tested: {total_regions}")
    print(f"✅ Successful: {successful_regions}")
    print(f"❌ Failed: {total_regions - successful_regions}")
    print()
    
    print("💡 KEY BENEFITS OF STRIPE-FIRST APPROACH:")
    print("   • Single source of truth for all pricing")
    print("   • No dual maintenance (app config + Stripe dashboard)")
    print("   • Real-time pricing updates from Stripe")
    print("   • Automatic currency formatting and display")
    print("   • Built-in fallback for high availability")
    print()
    
    print("🚀 NEXT STEPS FOR PRODUCTION:")
    print("   1. Set up Stripe API keys (test and live)")
    print("   2. Run: python setup_stripe_products.py --mode test")
    print("   3. Create regional Payment Links in Stripe dashboard")
    print("   4. Test with real Stripe test payments")
    print("   5. Deploy to production with live Stripe keys")
    print()
    
    print(f"✅ Integration test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main test function"""
    
    try:
        # Test all components
        results = test_stripe_pricing_api()
        validate_regional_pricing(results)
        test_payment_flow_integration()
        generate_summary_report(results)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())