#!/usr/bin/env python3
"""
Stripe Products Setup Script
Creates all products, regional prices, and payment links in Stripe as single source of truth.

Usage:
    python setup_stripe_products.py --mode test    # Use test API keys
    python setup_stripe_products.py --mode live    # Use live API keys

This eliminates the need to maintain pricing in both app config and Stripe dashboard.
"""

import stripe
import os
import json
import argparse
from datetime import datetime

def setup_stripe_products(test_mode=True):
    """Create all products and regional pricing in Stripe"""
    
    # Set Stripe API key
    if test_mode:
        stripe.api_key = os.getenv("STRIPE_SECRET_TEST_KEY", "sk_test_...")
        print("🧪 Using Stripe TEST mode")
    else:
        stripe.api_key = os.getenv("STRIPE_SECRET_LIVE_KEY", "sk_live_...")
        print("🔥 Using Stripe LIVE mode")
    
    if not stripe.api_key or stripe.api_key.endswith("..."):
        print("❌ ERROR: Stripe API key not found. Set STRIPE_SECRET_TEST_KEY or STRIPE_SECRET_LIVE_KEY")
        return False

    # Product definitions
    products = {
        "resume_analysis": {
            "name": "Resume Health Check",
            "description": "Get your resume optimized with AI-powered analysis",
            "emoji": "📋"
        },
        "job_fit_analysis": {
            "name": "Job Fit Analysis", 
            "description": "See how perfectly your resume matches specific roles",
            "emoji": "🎯"
        },
        "cover_letter": {
            "name": "Cover Letter Generator",
            "description": "Create compelling cover letters that get interviews",
            "emoji": "✍️"
        },
        "career_boost": {
            "name": "Career Boost Bundle",
            "description": "Complete job search optimization package (Resume + Job Fit)",
            "emoji": "🚀",
            "bundle": True,
            "includes": ["resume_analysis", "job_fit_analysis"]
        },
        "job_hunter": {
            "name": "Job Hunter Bundle",
            "description": "Everything you need to land interviews (Resume + Cover Letter)", 
            "emoji": "🎯",
            "bundle": True,
            "includes": ["resume_analysis", "cover_letter"]
        },
        "complete_package": {
            "name": "Complete Job Search Package",
            "description": "All-in-one solution for career success (All 3 products)",
            "emoji": "💼", 
            "bundle": True,
            "includes": ["resume_analysis", "job_fit_analysis", "cover_letter"]
        }
    }

    # Regional pricing based on Phase 0 data
    regional_config = {
        "US": {"currency": "usd", "multiplier": 1.0, "symbol": "$"},
        "PK": {"currency": "pkr", "multiplier": 119.8, "symbol": "₨"},  # ₨599 / $5 = 119.8
        "IN": {"currency": "inr", "multiplier": 60.0, "symbol": "₹"},   # ₹300 / $5 = 60.0  
        "HK": {"currency": "hkd", "multiplier": 7.0, "symbol": "HKD "},  # HKD 35 / $5 = 7.0
        "AE": {"currency": "aed", "multiplier": 4.0, "symbol": "AED "},  # AED 20 / $5 = 4.0
        "BD": {"currency": "bdt", "multiplier": 81.6, "symbol": "৳"},    # ৳408 / $5 = 81.6
        "default": {"currency": "usd", "multiplier": 1.0, "symbol": "$"}
    }

    # Base prices in USD cents (matching actual HTML/UI prices)
    base_prices = {
        "resume_analysis": 149,     # $1.49
        "job_fit_analysis": 299,    # $2.99  
        "cover_letter": 199,        # $1.99
        "career_boost": 399,        # $3.99 (bundle discount)
        "job_hunter": 349,          # $3.49 (bundle discount)
        "complete_package": 449     # $4.49 (bundle discount)
    }

    print(f"\n🚀 Setting up {len(products)} products across {len(regional_config)} regions...")
    print(f"📊 Total combinations: {len(products) * len(regional_config)} prices to create\n")

    setup_results = {
        "products": {},
        "prices": {},
        "payment_links": {},
        "created_at": datetime.now().isoformat(),
        "test_mode": test_mode
    }

    # Create products and regional prices
    for product_key, product_data in products.items():
        try:
            print(f"📦 Creating product: {product_data['emoji']} {product_data['name']}")
            
            # Create Stripe Product
            stripe_product = stripe.Product.create(
                name=product_data["name"],
                description=product_data["description"],
                metadata={
                    "app_product_id": product_key,
                    "emoji": product_data["emoji"],
                    "bundle": str(product_data.get("bundle", False)),
                    "includes": ",".join(product_data.get("includes", []))
                }
            )
            
            setup_results["products"][product_key] = stripe_product.id
            print(f"   ✅ Product created: {stripe_product.id}")
            
            # Create regional prices for this product
            product_prices = {}
            product_links = {}
            
            for region_code, region_data in regional_config.items():
                try:
                    # Calculate regional price
                    base_price_cents = base_prices[product_key]
                    regional_price_cents = int(base_price_cents * region_data["multiplier"])
                    
                    print(f"   🌍 {region_code}: {region_data['symbol']}{regional_price_cents/100:,.0f}")
                    
                    # Create Stripe Price
                    stripe_price = stripe.Price.create(
                        unit_amount=regional_price_cents,
                        currency=region_data["currency"],
                        product=stripe_product.id,
                        metadata={
                            "app_product_id": product_key,
                            "region": region_code,
                            "product_type": "bundle" if product_data.get("bundle") else "individual",
                            "base_price_usd": base_prices[product_key] / 100
                        }
                    )
                    
                    product_prices[region_code] = {
                        "price_id": stripe_price.id,
                        "amount": regional_price_cents // 100,
                        "currency": region_data["currency"],
                        "display": format_regional_price(regional_price_cents // 100, region_data)
                    }
                    
                    # Create Payment Link
                    payment_link = stripe.PaymentLink.create(
                        line_items=[{"price": stripe_price.id, "quantity": 1}],
                        metadata={
                            "app_product_id": product_key,
                            "region": region_code,
                            "product_type": "bundle" if product_data.get("bundle") else "individual"
                        }
                    )
                    
                    product_links[region_code] = payment_link.url
                    
                except Exception as e:
                    print(f"   ❌ Error creating {region_code} price: {e}")
                    continue
            
            setup_results["prices"][product_key] = product_prices
            setup_results["payment_links"][product_key] = product_links
            print(f"   ✅ Created {len(product_prices)} regional prices\n")
            
        except Exception as e:
            print(f"❌ Error creating product {product_key}: {e}\n")
            continue

    # Save setup results to file
    filename = f"stripe_setup_{'test' if test_mode else 'live'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(setup_results, f, indent=2)
    
    print(f"📁 Setup results saved to: {filename}")
    print(f"🎉 Setup complete! Created {len(setup_results['products'])} products")
    print(f"💰 Total prices created: {sum(len(prices) for prices in setup_results['prices'].values())}")
    print(f"🔗 Total payment links: {sum(len(links) for links in setup_results['payment_links'].values())}")
    
    return setup_results

def format_regional_price(amount: int, region_data: dict) -> str:
    """Format price with proper currency symbol and locale"""
    symbol = region_data["symbol"]
    currency = region_data["currency"]
    
    if currency in ["pkr", "inr", "bdt"]:
        # Format with commas for large numbers
        return f"{symbol}{amount:,}"
    else:
        return f"{symbol}{amount}"

def list_existing_products():
    """List existing products in Stripe for comparison"""
    try:
        products = stripe.Product.list(active=True)
        print(f"📋 Found {len(products.data)} existing active products:")
        for product in products.data:
            app_id = product.metadata.get("app_product_id", "Unknown")
            print(f"   • {product.name} (ID: {product.id}, App: {app_id})")
        return products.data
    except Exception as e:
        print(f"❌ Error listing products: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Setup Stripe products for Resume Health Checker")
    parser.add_argument("--mode", choices=["test", "live"], default="test", 
                       help="Stripe mode (test or live)")
    parser.add_argument("--list", action="store_true", help="List existing products")
    
    args = parser.parse_args()
    
    print("🏗️  STRIPE PRODUCTS SETUP")
    print("=" * 50)
    
    if args.list:
        print("📋 Listing existing products...\n")
        list_existing_products()
        return
    
    # Confirm before proceeding
    mode_str = "TEST" if args.mode == "test" else "LIVE"
    confirm = input(f"\n⚠️  About to create products in Stripe {mode_str} mode. Continue? (y/N): ")
    
    if confirm.lower() != 'y':
        print("❌ Cancelled")
        return
    
    # Run setup
    test_mode = args.mode == "test"
    results = setup_stripe_products(test_mode)
    
    if results:
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Update environment variables with Stripe API keys")
        print(f"2. Test the new /api/stripe-pricing/{'{country_code}'} endpoint")
        print(f"3. Update frontend to use Stripe pricing data")
        print(f"4. Remove old pricing_config.json files")

if __name__ == "__main__":
    main()