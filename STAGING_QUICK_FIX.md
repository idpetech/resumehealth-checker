# 🚀 Staging Quick Fix - Just Add One Variable

## The Problem
Stripe payments redirect to `localhost:8000` instead of your Railway staging domain.

## The Solution (1 Line)
Add this **single environment variable** to your existing Railway staging project:

```bash
PUBLIC_BASE_URL=https://web-production-f7f3.up.railway.app
```

## How to Add It

### Option 1: Railway Dashboard
1. Go to your Railway project dashboard
2. Click on your **staging service**
3. Go to **Variables** tab
4. Click **+ New Variable**
5. Name: `PUBLIC_BASE_URL`
6. Value: `https://web-production-f7f3.up.railway.app`
7. Click **Add**

### Option 2: Railway CLI
```bash
railway variables set PUBLIC_BASE_URL=https://web-production-f7f3.up.railway.app
```

## That's It! 

Your existing staging environment already has:
- ✅ `ENVIRONMENT=staging`
- ✅ `OPENAI_API_KEY`
- ✅ `STRIPE_SECRET_TEST_KEY`
- ✅ `STRIPE_PUBLISHABLE_TEST_KEY`
- ✅ All other required variables

You just need to add the **one missing variable** to fix the redirect URLs.

## Test It
1. Deploy the code (if not already deployed)
2. Visit your staging URL
3. Upload resume → get free analysis
4. Click "Upgrade" → test payment
5. **Should now redirect to your staging domain** (not localhost)

## What This Fixes
- ✅ Stripe success URL: `https://web-production-f7f3.up.railway.app/payment/success?...`
- ✅ Stripe cancel URL: `https://web-production-f7f3.up.railway.app/payment/cancel?...`
- ✅ Users see their analysis results after payment
- ✅ No more "localhost" redirects

**Total effort: 30 seconds to add one environment variable!** 🎯


