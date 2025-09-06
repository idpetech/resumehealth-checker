# 🚀 Railway Staging Deployment Checklist

## ✅ STAGING-ONLY SAFEGUARDS

### 🏷️ **Project Isolation**
- [x] Project name: `staging-resume-checker` (explicitly staging)
- [x] Separate Railway project for staging
- [x] No connection to production resources

### 🔧 **Environment Variables (Staging Only)**
```bash
ENVIRONMENT=staging                    # Forces staging mode
DEBUG=true                            # Enables debug features
PORT=8000                            # Standard port
DATABASE_PATH=staging_database.db     # Separate staging database
```

### 🛡️ **Payment Safety (Test Keys Only)**
```bash
# ✅ STAGING: Test keys only
STRIPE_SECRET_TEST_KEY=sk_test_...     # Test secret key
STRIPE_PUBLISHABLE_TEST_KEY=pk_test_... # Test publishable key
STRIPE_WEBHOOK_TEST_SECRET=whsec_...   # Test webhook secret

# ❌ PRODUCTION: Live keys (NOT SET in staging)
# STRIPE_SECRET_LIVE_KEY=sk_live_...   # Never set in staging
# STRIPE_PUBLISHABLE_LIVE_KEY=pk_live_... # Never set in staging
```

### 🔒 **Configuration Safety**
- [x] **Staging Mode**: `config.environment == "staging"`
- [x] **Test Payments**: `config.use_stripe_test_keys = True`
- [x] **Debug Enabled**: API docs visible, detailed logging
- [x] **Separate Database**: `staging_database.db` (not production)
- [x] **Mock Payments**: Fallback to mock if Stripe not configured

### 🚫 **Production Safeguards**
- [x] **No Live Stripe Keys**: Only test keys in staging
- [x] **No Production Database**: Separate staging database
- [x] **Debug Mode**: Shows errors and API docs
- [x] **Test Environment**: All payments are test transactions

## 🚀 **Deployment Commands**

### 1. **Initialize Staging Project**
```bash
railway login
railway init staging-resume-checker
```

### 2. **Set Staging Environment Variables**
```bash
railway variables set ENVIRONMENT=staging
railway variables set DEBUG=true
railway variables set PORT=8000
railway variables set DATABASE_PATH=staging_database.db
```

### 3. **Set API Keys (Test Keys Only)**
```bash
railway variables set OPENAI_API_KEY=sk-your-openai-key
railway variables set STRIPE_SECRET_TEST_KEY=sk_test_your-test-key
railway variables set STRIPE_PUBLISHABLE_TEST_KEY=pk_test_your-test-key
railway variables set STRIPE_WEBHOOK_TEST_SECRET=whsec_your-test-secret
```

### 4. **Deploy to Staging**
```bash
railway up
```

## ✅ **Verification Steps**

### 1. **Environment Check**
- [ ] Visit staging URL
- [ ] Check `/health` endpoint
- [ ] Verify debug mode (API docs visible)
- [ ] Confirm staging database created

### 2. **Payment Safety Check**
- [ ] Test payment flow
- [ ] Verify test Stripe keys used
- [ ] Confirm no live transactions possible
- [ ] Check mock payment fallback

### 3. **Feature Testing**
- [ ] Free analysis works
- [ ] Premium features work
- [ ] File upload works
- [ ] Results display correctly

## 🚨 **CRITICAL SAFETY NOTES**

1. **NEVER** set live Stripe keys in staging
2. **NEVER** use production database in staging
3. **ALWAYS** verify `ENVIRONMENT=staging` before deployment
4. **ALWAYS** test payment flow before considering production
5. **ALWAYS** use separate Railway project for staging

## 🎯 **Next Steps After Staging**

1. **Test All Features** in staging environment
2. **Verify Payment Flow** with test transactions
3. **Check Performance** and error handling
4. **Create Production Project** (separate from staging)
5. **Deploy to Production** only after staging validation

---

**✅ STAGING DEPLOYMENT IS SAFE:**
- Separate project, database, and environment
- Test keys only, no live transactions
- Debug mode enabled for testing
- Mock payment fallback for safety
