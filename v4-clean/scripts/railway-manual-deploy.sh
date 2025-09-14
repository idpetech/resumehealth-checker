#!/bin/bash
# Manual Railway Deployment Script
# For when Railway services are configured with manual deploy triggers

set -e

echo "🚀 Manual Railway Deployment Helper"
echo ""

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not installed"
    echo "💡 Install: npm install -g @railway/cli"
    echo "💡 Or use Railway dashboard manually"
    exit 1
fi

# Login check
if ! railway whoami &> /dev/null; then
    echo "🔑 Please login to Railway first:"
    echo "railway login"
    exit 1
fi

echo "📋 Available deployment options:"
echo "1. Deploy to Staging only"
echo "2. Deploy to Production only"  
echo "3. Deploy to both (current behavior)"
echo ""

read -p "Choose option (1-3): " option

case $option in
    1)
        echo "🚀 Deploying to STAGING only..."
        echo "💡 Use Railway dashboard to trigger staging deployment"
        echo "🌐 Staging: https://web-staging-f53d.up.railway.app"
        ;;
    2)
        echo "🚀 Deploying to PRODUCTION only..."
        echo "⚠️  WARNING: This affects real users!"
        read -p "🤔 Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "💡 Use Railway dashboard to trigger production deployment"
            echo "🌐 Production: https://web-production-f7f3.up.railway.app"
        else
            echo "❌ Production deployment cancelled"
        fi
        ;;
    3)
        echo "🚀 Deploying to BOTH environments..."
        echo "⚠️  This is the current auto-deploy behavior"
        git push origin v4.0-deployment
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "💡 TO FIX THIS PROPERLY:"
echo "1. Go to Railway Dashboard"
echo "2. For each service, go to Settings → Deploy Triggers"
echo "3. Disable 'Auto-deploy on push'"
echo "4. Use manual deploy buttons instead"