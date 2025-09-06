# 🧪 Testing Guide - Resume Health Checker v4.0

## **Testing Strategy: Stripe Sandbox → Railway Staging → Production**

This guide walks you through comprehensive testing using Stripe's sandbox environment before deploying to production.

---

## **Phase 1: Local Testing with Stripe Sandbox**

### **Step 1: Environment Setup**

1. **Install Dependencies**
   ```bash
   cd /Users/haseebtoor/Projects/resumehealth-checker/v4-clean
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

2. **Set Up Environment Variables**
   Create a `.env` file with your test credentials:
   ```bash
   # Core Settings
   ENVIRONMENT=local
   DEBUG=true
   PORT=8000
   
   # OpenAI API Key (required for AI analysis)
   OPENAI_API_KEY=sk-your-openai-key-here
   
   # Stripe Test Keys (Sandbox Mode)
   STRIPE_SECRET_TEST_KEY=sk_test_your_stripe_test_key_here
   STRIPE_PUBLISHABLE_TEST_KEY=pk_test_your_stripe_publishable_key_here
   STRIPE_WEBHOOK_TEST_SECRET=whsec_your_webhook_secret_here
   
   # Database
   DATABASE_PATH=test_database.db
   ```

3. **Start the Application**
   ```bash
   python main.py
   ```
   You should see:
   ```
   🚀 Starting Resume Health Checker v4.0 in local mode
   ✅ Database initialized successfully
   ✅ Serving on http://localhost:8000
   ```

### **Step 2: Automated Testing**

Run the comprehensive test suite:
```bash
python test_local.py
```

**Expected Output:**
```
🧪 Starting Local Testing Suite
==================================================
✅ PASS Health Check
    Status: healthy
✅ PASS File Upload & Analysis
    Analysis ID: abc123-def456-ghi789
✅ PASS Payment Session Creation
    Session ID: cs_test_1234567890
✅ PASS Regional Pricing - US
    Currency: USD
✅ PASS Regional Pricing - PK
    Currency: PKR
...
==================================================
📊 Test Results: 6/6 tests passed
🎉 All tests passed! Ready for Railway staging deployment.
```

### **Step 3: Manual Testing**

1. **Open Browser**: `http://localhost:8000`
2. **Upload Resume**: The test will automatically use the real resume file:
   - `ResumeLAW.docx` (Word document - 18,227 bytes)
3. **Get Free Analysis**: Verify AI response is generated
4. **Test Payment Flow**: Click "Upgrade to Premium"
5. **Use Stripe Test Cards**:
   - Success: `4242424242424242`
   - Declined: `4000000000000002`
   - Insufficient Funds: `4000000000009995`

### **Step 4: Stripe Webhook Testing**

1. **Install Stripe CLI**:
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Or download from: https://stripe.com/docs/stripe-cli
   ```

2. **Login to Stripe**:
   ```bash
   stripe login
   ```

3. **Forward Webhooks**:
   ```bash
   stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
   ```

4. **Test Payment**: Complete a test payment and verify webhook is received

---

## **Phase 2: Railway Staging Deployment**

### **Step 1: Deploy to Staging**

```bash
python deploy_staging.py
```

This will:
- Create a Railway staging project
- Set up environment variables
- Deploy the application

### **Step 2: Configure Staging Environment**

1. **Set Required Environment Variables**:
   ```bash
   railway variables set OPENAI_API_KEY=sk-your-key-here
   railway variables set STRIPE_SECRET_TEST_KEY=sk_test_your-key-here
   railway variables set STRIPE_PUBLISHABLE_TEST_KEY=pk_test_your-key-here
   railway variables set STRIPE_WEBHOOK_TEST_SECRET=whsec_your-secret-here
   ```

2. **Get Staging URL**: Railway will provide a staging URL like:
   `https://staging-resume-checker-production.up.railway.app`

### **Step 3: Test Staging Deployment**

1. **Health Check**:
   ```bash
   curl https://your-staging-url.up.railway.app/health
   ```

2. **Full Payment Flow Test**:
   - Upload resume
   - Get analysis
   - Create payment session
   - Complete payment with test card
   - Verify webhook handling

3. **Configure Stripe Webhooks for Staging**:
   - Add webhook endpoint: `https://your-staging-url.up.railway.app/api/v1/webhooks/stripe`
   - Enable events: `checkout.session.completed`, `payment_intent.succeeded`

---

## **Phase 3: Production Deployment (After Staging Success)**

### **Prerequisites**
- ✅ All local tests pass
- ✅ Staging deployment works perfectly
- ✅ Payment flow tested end-to-end
- ✅ Webhooks working correctly

### **Production Setup**
1. **Create Production Railway Project**
2. **Set Live Stripe Keys** (not test keys)
3. **Configure Production Webhooks**
4. **Deploy and Test**

---

## **Test Scenarios**

### **Critical Test Cases**

1. **File Upload Tests**:
   - ✅ DOCX upload and text extraction (`ResumeLAW.docx`)
   - ✅ Real resume content processing
   - ❌ Invalid file types (should fail gracefully)
   - ❌ Files too large (should fail gracefully)

2. **AI Analysis Tests**:
   - ✅ Free analysis generation
   - ✅ Premium analysis generation
   - ✅ Job fit analysis with job posting
   - ❌ Empty resume (should fail gracefully)
   - ❌ Very short resume (should warn)

3. **Payment Flow Tests**:
   - ✅ Payment session creation
   - ✅ Successful payment with test card
   - ✅ Declined payment handling
   - ✅ Payment cancellation
   - ✅ Webhook processing

4. **Regional Pricing Tests**:
   - ✅ US pricing (USD)
   - ✅ Pakistan pricing (PKR)
   - ✅ India pricing (INR)
   - ✅ Hong Kong pricing (HKD)
   - ✅ UAE pricing (AED)
   - ✅ Bangladesh pricing (BDT)

5. **Error Handling Tests**:
   - ✅ Network errors
   - ✅ API timeouts
   - ✅ Invalid requests
   - ✅ Database errors

---

## **Troubleshooting**

### **Common Issues**

1. **"Server not running" Error**:
   ```bash
   # Make sure the application is started
   python main.py
   ```

2. **"OpenAI API Key not found" Error**:
   ```bash
   # Check your .env file has the correct key
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **"Stripe authentication failed" Error**:
   ```bash
   # Verify your Stripe test keys are correct
   STRIPE_SECRET_TEST_KEY=sk_test_your-actual-test-key
   ```

4. **Webhook signature verification failed**:
   ```bash
   # Make sure webhook secret matches
   STRIPE_WEBHOOK_TEST_SECRET=whsec_your-actual-secret
   ```

### **Debug Mode**

Enable debug logging by setting:
```bash
DEBUG=true
```

This will show detailed error messages and API responses.

---

## **Success Criteria**

### **Local Testing ✅**
- [ ] All automated tests pass (6/6)
- [ ] Manual payment flow works
- [ ] Webhook handling verified
- [ ] All file types process correctly
- [ ] Regional pricing displays correctly

### **Staging Testing ✅**
- [ ] Application deploys successfully
- [ ] Health check responds
- [ ] Complete payment flow works
- [ ] Webhooks process correctly
- [ ] No errors in logs

### **Production Ready ✅**
- [ ] Staging tests pass 100%
- [ ] Performance acceptable (<2s response times)
- [ ] Error handling graceful
- [ ] Monitoring in place

---

**🎯 Goal**: Achieve 100% test success rate before production deployment.

**⏱️ Timeline**: 2-4 hours for complete testing cycle.

**🚀 Next Step**: Run `python test_local.py` to begin testing!
