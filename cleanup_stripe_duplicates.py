#!/usr/bin/env python3
"""
Stripe Duplicate Cleanup Script
Removes duplicate products keeping only the latest version of each.

This script will:
1. Identify all products and their creation timestamps
2. Group products by app_product_id
3. Keep the most recent product for each group
4. Archive (deactivate) older duplicates
5. Provide detailed cleanup report

Usage:
    python cleanup_stripe_duplicates.py --mode test    # Use test API keys
    python cleanup_stripe_duplicates.py --mode live    # Use live API keys
"""

import stripe
import os
import argparse
from datetime import datetime
from collections import defaultdict

def cleanup_duplicate_products(test_mode=True):
    """Clean up duplicate Stripe products, keeping only the latest of each type"""
    
    # Set Stripe API key
    if test_mode:
        stripe.api_key = os.getenv("STRIPE_SECRET_TEST_KEY", "")
        print("🧪 Using Stripe TEST mode")
    else:
        stripe.api_key = os.getenv("STRIPE_SECRET_LIVE_KEY", "")
        print("🔥 Using Stripe LIVE mode")
    
    if not stripe.api_key:
        print("❌ ERROR: Stripe API key not found")
        return False

    print("\n🧹 STRIPE DUPLICATE CLEANUP")
    print("=" * 50)
    
    try:
        # Fetch all products
        products = stripe.Product.list(limit=50)
        print(f"📋 Found {len(products.data)} total products")
        
        if len(products.data) == 0:
            print("✅ No products found - nothing to clean up!")
            return True
        
        # Group products by app_product_id
        product_groups = defaultdict(list)
        
        for product in products.data:
            app_id = product.metadata.get('app_product_id', 'unknown')
            product_groups[app_id].append({
                'product': product,
                'app_id': app_id,
                'name': product.name,
                'id': product.id,
                'created': datetime.fromtimestamp(product.created),
                'active': product.active
            })
        
        print(f"\n📊 Product groups found:")
        total_to_keep = 0
        total_to_archive = 0
        
        # Analyze what will be kept vs archived
        cleanup_plan = {}
        
        for app_id, products_list in product_groups.items():
            # Sort by creation date (newest first)
            products_list.sort(key=lambda x: x['created'], reverse=True)
            
            active_products = [p for p in products_list if p['active']]
            
            if len(active_products) > 1:
                keep_product = active_products[0]  # Keep the newest
                archive_products = active_products[1:]  # Archive the rest
                
                print(f"\n📦 {app_id.upper().replace('_', ' ')}:")
                print(f"   ✅ KEEP: {keep_product['name']} ({keep_product['id']}) - {keep_product['created'].strftime('%Y-%m-%d %H:%M')}")
                
                cleanup_plan[app_id] = {
                    'keep': keep_product,
                    'archive': archive_products
                }
                
                total_to_keep += 1
                total_to_archive += len(archive_products)
                
                for archive_product in archive_products:
                    print(f"   ❌ ARCHIVE: {archive_product['name']} ({archive_product['id']}) - {archive_product['created'].strftime('%Y-%m-%d %H:%M')}")
            
            elif len(active_products) == 1:
                print(f"\n📦 {app_id.upper().replace('_', ' ')}:")
                print(f"   ✅ KEEP: {active_products[0]['name']} (only copy - no cleanup needed)")
                total_to_keep += 1
            
            elif len(active_products) == 0 and products_list:
                print(f"\n📦 {app_id.upper().replace('_', ' ')}:")
                print(f"   ⚠️  All products already archived ({len(products_list)} found)")
        
        print(f"\n📈 CLEANUP SUMMARY:")
        print(f"   📌 Products to keep active: {total_to_keep}")
        print(f"   🗂️  Products to archive: {total_to_archive}")
        print(f"   🧹 Total cleanup actions: {total_to_archive}")
        
        if total_to_archive == 0:
            print("✅ No cleanup needed - all products are already unique!")
            return True
        
        # Ask for confirmation
        print(f"\n⚠️  About to archive {total_to_archive} duplicate products.")
        print("   Note: Archiving deactivates products but preserves them for historical records.")
        
        return cleanup_plan
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False

def execute_cleanup(cleanup_plan, test_mode=True):
    """Execute the cleanup plan by archiving duplicate products"""
    
    if not cleanup_plan:
        print("✅ Nothing to clean up!")
        return True
    
    print(f"\n🔄 EXECUTING CLEANUP...")
    print("=" * 30)
    
    archived_count = 0
    errors = []
    
    try:
        for app_id, plan in cleanup_plan.items():
            archive_products = plan['archive']
            
            print(f"\n📦 Cleaning up {app_id}...")
            
            for product_info in archive_products:
                product_id = product_info['id']
                product_name = product_info['name']
                
                try:
                    # Archive (deactivate) the product
                    stripe.Product.modify(product_id, active=False)
                    print(f"   ✅ Archived: {product_name} ({product_id})")
                    archived_count += 1
                    
                except Exception as e:
                    error_msg = f"Failed to archive {product_name} ({product_id}): {e}"
                    print(f"   ❌ {error_msg}")
                    errors.append(error_msg)
        
        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"   ✅ Successfully archived: {archived_count} products")
        
        if errors:
            print(f"   ❌ Errors encountered: {len(errors)}")
            for error in errors:
                print(f"      • {error}")
        
        return len(errors) == 0
        
    except Exception as e:
        print(f"❌ Critical error during cleanup: {e}")
        return False

def verify_cleanup(test_mode=True):
    """Verify the cleanup was successful"""
    
    print(f"\n🔍 VERIFYING CLEANUP...")
    print("=" * 25)
    
    try:
        # Fetch active products only
        products = stripe.Product.list(limit=50, active=True)
        active_products = products.data
        
        print(f"📊 Active products remaining: {len(active_products)}")
        
        # Group by app_product_id to check for remaining duplicates
        product_groups = defaultdict(list)
        
        for product in active_products:
            app_id = product.metadata.get('app_product_id', 'unknown')
            product_groups[app_id].append({
                'name': product.name,
                'id': product.id,
                'created': datetime.fromtimestamp(product.created)
            })
        
        duplicates_found = 0
        expected_products = ['resume_analysis', 'job_fit_analysis', 'cover_letter', 
                           'career_boost', 'job_hunter', 'complete_package']
        
        for app_id, products_list in product_groups.items():
            if len(products_list) > 1:
                print(f"   ⚠️  {app_id}: Still has {len(products_list)} active products")
                duplicates_found += len(products_list) - 1
            else:
                product_name = products_list[0]['name']
                created_date = products_list[0]['created'].strftime('%Y-%m-%d %H:%M')
                print(f"   ✅ {app_id}: {product_name} ({created_date})")
        
        if duplicates_found > 0:
            print(f"\n⚠️  Warning: {duplicates_found} duplicates still remain")
            return False
        else:
            print(f"\n🎯 Perfect! Clean dashboard with {len(product_groups)} unique products")
            
            # Check if we have all expected products
            missing_products = set(expected_products) - set(product_groups.keys())
            if missing_products:
                print(f"⚠️  Missing expected products: {', '.join(missing_products)}")
            else:
                print("✅ All expected products present and unique!")
            
            return True
    
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Clean up duplicate Stripe products")
    parser.add_argument("--mode", choices=["test", "live"], default="test", 
                       help="Stripe mode (test or live)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, don't execute cleanup")
    
    args = parser.parse_args()
    
    test_mode = args.mode == "test"
    
    # Step 1: Analyze and create cleanup plan
    cleanup_plan = cleanup_duplicate_products(test_mode)
    
    if cleanup_plan is False:
        print("❌ Analysis failed")
        return 1
    elif cleanup_plan is True:
        print("✅ No cleanup needed")
        return 0
    elif args.dry_run:
        print("🔍 Dry run complete - no changes made")
        return 0
    
    # Step 2: Ask for confirmation
    confirm = input(f"\n⚠️  Proceed with archiving duplicate products? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Cleanup cancelled")
        return 1
    
    # Step 3: Execute cleanup
    success = execute_cleanup(cleanup_plan, test_mode)
    
    if not success:
        print("❌ Cleanup completed with errors")
        return 1
    
    # Step 4: Verify cleanup
    verification_success = verify_cleanup(test_mode)
    
    if verification_success:
        print("\n🎉 STRIPE CLEANUP SUCCESSFUL!")
        print("Your dashboard now has clean, unique products ready for production! 🚀")
        return 0
    else:
        print("\n⚠️  Cleanup completed but verification found issues")
        return 1

if __name__ == "__main__":
    exit(main())