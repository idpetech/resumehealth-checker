#!/usr/bin/env python3
"""
Railway Staging Deployment Script

Deploys the application to Railway staging environment with proper configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_railway_cli():
    """Check if Railway CLI is installed"""
    try:
        subprocess.run(["railway", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_railway_staging():
    """Set up Railway staging environment"""
    print("🚀 Setting up Railway Staging Environment")
    print("=" * 50)
    
    # Check Railway CLI
    if not check_railway_cli():
        print("❌ Railway CLI not found. Please install it first:")
        print("   npm install -g @railway/cli")
        print("   or visit: https://docs.railway.app/develop/cli")
        return False
    
    # Initialize Railway project
    if not run_command("railway login", "Logging into Railway"):
        return False
    
    # Create staging project
    if not run_command("railway init staging-resume-checker", "Creating staging project"):
        return False
    
    # Set environment variables
    env_vars = {
        "ENVIRONMENT": "staging",
        "DEBUG": "true",
        "PORT": "8000",
        "DATABASE_PATH": "staging_database.db"
    }
    
    print("\n📝 Setting environment variables...")
    for key, value in env_vars.items():
        if not run_command(f'railway variables set {key}="{value}"', f"Setting {key}"):
            return False
    
    print("\n⚠️  IMPORTANT: You need to set these environment variables manually:")
    print("   railway variables set OPENAI_API_KEY=sk-your-key-here")
    print("   railway variables set STRIPE_SECRET_TEST_KEY=sk_test_your-key-here")
    print("   railway variables set STRIPE_PUBLISHABLE_TEST_KEY=pk_test_your-key-here")
    print("   railway variables set STRIPE_WEBHOOK_TEST_SECRET=whsec_your-secret-here")
    
    # Deploy to staging
    if not run_command("railway up", "Deploying to staging"):
        return False
    
    print("\n🎉 Staging deployment initiated!")
    print("📋 Next steps:")
    print("   1. Set the required environment variables above")
    print("   2. Wait for deployment to complete")
    print("   3. Run staging tests with: python test_staging.py")
    
    return True

def main():
    """Main deployment function"""
    print("🚀 Resume Health Checker v4.0 - Railway Staging Deployment")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ main.py not found. Please run this script from the v4-clean directory.")
        sys.exit(1)
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Please ensure all files are present.")
        sys.exit(1)
    
    # Run deployment
    if setup_railway_staging():
        print("\n✅ Staging deployment setup completed!")
    else:
        print("\n❌ Staging deployment failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()


