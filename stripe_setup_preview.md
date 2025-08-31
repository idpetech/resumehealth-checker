# STRIPE SETUP PREVIEW

## What Will Be Created Automatically

### 📦 PRODUCTS (6 total)
1. **📋 Resume Health Check** 
   - Description: "Get your resume optimized with AI-powered analysis"
   - App ID: resume_analysis

2. **🎯 Job Fit Analysis**
   - Description: "See how perfectly your resume matches specific roles" 
   - App ID: job_fit_analysis

3. **✍️ Cover Letter Generator**
   - Description: "Create compelling cover letters that get interviews"
   - App ID: cover_letter

4. **🚀 Career Boost Bundle**
   - Description: "Complete job search optimization package (Resume + Job Fit)"
   - App ID: career_boost

5. **🎯 Job Hunter Bundle** 
   - Description: "Everything you need to land interviews (Resume + Cover Letter)"
   - App ID: job_hunter

6. **💼 Complete Job Search Package**
   - Description: "All-in-one solution for career success (All 3 products)"
   - App ID: complete_package

### 💰 REGIONAL PRICES (36 total)

Each product will have prices in 6 currencies:

| Product | US | Pakistan | India | Hong Kong | UAE | Bangladesh |
|---------|----|---------:|------:|----------:|----:|-----------:|
| Resume Health Check | $10 | ₨1,200 | ₹750 | HKD 70 | AED 40 | ৳800 |
| Job Fit Analysis | $12 | ₨1,440 | ₹900 | HKD 84 | AED 48 | ৳960 |
| Cover Letter | $8 | ₨960 | ₹600 | HKD 56 | AED 32 | ৳640 |
| Career Boost Bundle | $18 | ₨2,160 | ₹1,350 | HKD 126 | AED 72 | ৳1,440 |
| Job Hunter Bundle | $15 | ₨1,800 | ₹1,125 | HKD 105 | AED 60 | ৳1,200 |
| Complete Package | $22 | ₨2,640 | ₹1,650 | HKD 154 | AED 88 | ৳1,760 |

### 🔗 PAYMENT LINKS (36 total)
- Each regional price gets its own Payment Link
- All links include proper success/cancel URLs
- Session tracking via client_reference_id parameter

### 📊 TOTAL SETUP
- **6 Products** in Stripe
- **36 Regional Prices** across 6 currencies  
- **36 Payment Links** for direct checkout
- **1 Configuration File** with all URLs and IDs
- **Complete Integration** with your existing app

## Setup Commands

```bash
# 1. Set your Stripe API key
export STRIPE_SECRET_TEST_KEY="sk_test_YOUR_KEY_HERE"

# 2. Run setup in test mode
python setup_stripe_products.py --mode test

# 3. After testing, run in live mode  
python setup_stripe_products.py --mode live
```

## What You'll Get

After running the script, you'll have:
- ✅ All products created in Stripe Dashboard
- ✅ All regional pricing configured
- ✅ All Payment Links ready to use
- ✅ JSON file with all configuration
- ✅ Your app automatically using real Stripe pricing

No more dual maintenance! Update prices in Stripe Dashboard only.