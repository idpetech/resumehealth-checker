# Railway Staging Deployment Guide

## 🚀 Quick Fix: Stripe Redirect URLs

This guide shows you how to deploy the **5-line fix** for Stripe redirect URLs to your Railway staging environment.

## ✅ What Was Fixed

**Problem**: Stripe payments redirected to `localhost:8000` instead of your Railway domain.

**Solution**: Added `PUBLIC_BASE_URL` environment variable support (5 lines of code).

## 🔧 Railway Environment Variables

Set these environment variables in your Railway staging project:

```bash
# Core Configuration
ENVIRONMENT=staging
PUBLIC_BASE_URL=https://web-production-f7f3.up.railway.app

# OpenAI API (Required)
OPENAI_API_KEY=your-actual-openai-api-key

# Stripe Test Keys (Required for payments)
STRIPE_SECRET_TEST_KEY=sk_test_your-actual-stripe-test-key
STRIPE_PUBLISHABLE_TEST_KEY=pk_test_your-actual-stripe-publishable-key
STRIPE_WEBHOOK_TEST_SECRET=whsec_your-actual-webhook-secret

# Application Settings
DATABASE_PATH=database.db
PORT=8000
MAX_FILE_SIZE=10485760
```

## 📋 Step-by-Step Deployment

### 1. Set Environment Variables in Railway

1. Go to your Railway project dashboard
2. Click on your staging service
3. Go to **Variables** tab
4. Add each environment variable from the list above
5. **Important**: Replace placeholder values with your actual API keys

### 2. Deploy Code

```bash
# Commit the fix
git add app/core/config.py railway-staging-env.sh
git commit -m "Fix Stripe redirect URLs with PUBLIC_BASE_URL support"

# Push to trigger Railway deployment
git push origin main
```

### 3. Test Payment Flow

1. Visit your staging URL: `https://web-production-f7f3.up.railway.app`
2. Upload a resume and get free analysis
3. Click "Upgrade" to test payment
4. **Expected Result**: After payment, you should be redirected back to your staging domain (not localhost)

## 🎯 What This Fixes

- ✅ **Stripe redirects to correct domain** (Railway staging URL)
- ✅ **Success page shows analysis results** (existing functionality)
- ✅ **Cancel page returns to app** (existing functionality)
- ✅ **Works in all environments** (staging, production, local)
- ✅ **Zero breaking changes** (production unchanged until you set env var)

## 🔍 Testing Checklist

- [ ] Environment variables set in Railway
- [ ] Code deployed successfully
- [ ] Free analysis works
- [ ] Payment flow redirects to correct domain
- [ ] Success page shows premium results
- [ ] Cancel page returns to app

## 🚨 Troubleshooting

### If payments still redirect to localhost:
1. Check that `PUBLIC_BASE_URL` is set correctly in Railway
2. Verify the URL doesn't have trailing slashes
3. Check Railway deployment logs for any errors

### If Stripe keys are invalid:
1. Verify you're using **test keys** (start with `sk_test_` and `pk_test_`)
2. Check that keys are from the same Stripe account
3. Ensure webhook secret matches your Stripe webhook configuration

## 📈 Next Steps

Once staging works perfectly:
1. Set the same environment variables in **production**
2. Deploy to production
3. Monitor payment success rates

## 🎉 Success!

Your Stripe payment flow should now work correctly in staging, redirecting users back to your Railway domain with their analysis results intact.


