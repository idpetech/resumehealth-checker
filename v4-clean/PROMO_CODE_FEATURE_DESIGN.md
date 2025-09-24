# 🎯 Promotional Code Feature Design
**Resume Health Checker v4.0 - Clean Implementation**

## 📋 Requirements Summary

### **Core Functionality:**
- ✅ User enters promo code (e.g., "CresSoft2025")
- ✅ 20% discount applied to any feature
- ✅ Price differential shown on screen
- ✅ Discount reflected in Stripe payment
- ✅ 100% discount = no payment required
- ✅ Same premium flow executed for free features
- ✅ Traffic and usage tracking

---

## 🏗️ Architecture Design

### **1. Database Schema**

```sql
-- Promotional Codes Table
CREATE TABLE promotional_codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,                    -- "CresSoft2025"
    discount_type TEXT NOT NULL,                  -- "percentage" or "fixed_amount"
    discount_value DECIMAL(10,2) NOT NULL,        -- 20.00 for 20%
    max_uses INTEGER DEFAULT NULL,               -- NULL = unlimited
    current_uses INTEGER DEFAULT 0,              -- Track usage
    max_uses_per_user INTEGER DEFAULT 1,         -- Per user limit
    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP DEFAULT NULL,           -- NULL = no expiration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Promotional Usage Tracking
CREATE TABLE promotional_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    promo_code_id INTEGER NOT NULL,
    analysis_id TEXT NOT NULL,
    user_session_id TEXT NOT NULL,                -- Track anonymous users
    discount_applied DECIMAL(10,2) NOT NULL,
    original_amount DECIMAL(10,2) NOT NULL,
    final_amount DECIMAL(10,2) NOT NULL,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (promo_code_id) REFERENCES promotional_codes(id),
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

-- Site Traffic Tracking
CREATE TABLE site_traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    page_visited TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT,
    referrer TEXT,
    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature Usage Tracking
CREATE TABLE feature_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    feature_type TEXT NOT NULL,                  -- "resume_analysis", "cover_letter", etc.
    analysis_id TEXT,
    promo_code_used TEXT DEFAULT NULL,
    usage_type TEXT NOT NULL,                    -- "free", "paid", "promo_free", "promo_discounted"
    amount_paid DECIMAL(10,2) DEFAULT 0,
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **2. API Endpoints**

```python
# New API Routes
@router.post("/promo/validate")
async def validate_promo_code(
    code: str,
    product_type: str,
    original_amount: float
) -> PromoValidationResponse:
    """Validate promo code and return discount info"""

@router.post("/promo/apply")
async def apply_promo_code(
    analysis_id: str,
    promo_code: str,
    product_type: str
) -> PromoApplicationResponse:
    """Apply promo code to analysis"""

@router.get("/analytics/traffic")
async def get_traffic_analytics() -> TrafficAnalytics:
    """Get site traffic statistics"""

@router.get("/analytics/feature-usage")
async def get_feature_usage_analytics() -> FeatureUsageAnalytics:
    """Get feature usage statistics"""
```

### **3. Frontend Components**

#### **A. Promo Code Input Section**
```html
<!-- Add to existing pricing cards -->
<div class="promo-code-section mb-4">
    <div class="flex items-center space-x-2">
        <input 
            type="text" 
            id="promoCodeInput" 
            placeholder="Enter promo code (e.g., CresSoft2025)"
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
        <button 
            id="applyPromoBtn"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
            Apply
        </button>
    </div>
    <div id="promoStatus" class="mt-2 text-sm"></div>
</div>
```

#### **B. Dynamic Pricing Display**
```html
<!-- Updated pricing cards with promo discount -->
<div class="pricing-card">
    <div class="original-price">$1.49</div>
    <div class="promo-price" style="display: none;">
        <span class="discounted-price">$1.19</span>
        <span class="discount-badge">20% OFF</span>
    </div>
</div>
```

#### **C. Payment Flow Integration**
```javascript
// Enhanced payment creation with promo code
async function createPaymentWithPromo(analysisId, productType, promoCode) {
    const response = await fetch('/api/v1/promo/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            analysis_id: analysisId,
            promo_code: promoCode,
            product_type: productType
        })
    });
    
    const result = await response.json();
    
    if (result.final_amount === 0) {
        // 100% discount - skip payment, execute premium flow directly
        return await executePremiumFeature(analysisId, productType);
    } else {
        // Partial discount - create Stripe session with discounted amount
        return await createStripeSession(analysisId, productType, result.final_amount);
    }
}
```

---

## 🔄 User Flow Design

### **Scenario 1: 20% Discount (CresSoft2025)**
1. User uploads resume → gets free analysis
2. User sees premium options with pricing
3. User enters "CresSoft2025" → validation shows "20% OFF - $1.19 instead of $1.49"
4. User clicks "Buy Now" → Stripe checkout for $1.19
5. Payment successful → premium feature executed
6. Usage tracked: `feature_usage` + `promotional_usage` tables

### **Scenario 2: 100% Discount (FREE100)**
1. User uploads resume → gets free analysis
2. User enters "FREE100" → validation shows "100% OFF - FREE!"
3. User clicks "Get Premium" → **NO PAYMENT** required
4. Premium feature executed immediately
5. Usage tracked: `feature_usage` + `promotional_usage` tables

### **Scenario 3: Invalid/Expired Code**
1. User enters invalid code → "Invalid or expired promo code"
2. Pricing reverts to original amounts
3. Normal payment flow continues

---

## 🛠️ Implementation Plan

### **Phase 1: Database & Backend (Week 1)**
- [ ] Create database tables
- [ ] Implement promo code validation API
- [ ] Add promo code application logic
- [ ] Update payment service for discounted amounts

### **Phase 2: Frontend Integration (Week 2)**
- [ ] Add promo code input UI
- [ ] Implement dynamic pricing display
- [ ] Update payment flow for discounts
- [ ] Add promo status indicators

### **Phase 3: Analytics & Tracking (Week 3)**
- [ ] Implement traffic tracking
- [ ] Add feature usage tracking
- [ ] Create analytics dashboard
- [ ] Add promo code usage reports

### **Phase 4: Testing & Optimization (Week 4)**
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Security validation
- [ ] Production deployment

---

## 🔒 Security Considerations

### **Promo Code Security:**
- Rate limiting on validation attempts (10 per minute per IP)
- Case-insensitive but exact match validation
- Secure session tracking for usage limits
- Protection against brute force code guessing

### **Payment Security:**
- Server-side validation of all discounts
- Stripe webhook verification for payment completion
- No client-side price manipulation possible
- Audit trail for all promo code applications

---

## 📊 Analytics & Tracking

### **Traffic Metrics:**
- Page views and unique visitors
- Conversion rates (free → premium)
- Promo code usage rates
- Geographic distribution

### **Feature Usage Metrics:**
- Most popular features
- Promo code effectiveness
- Revenue impact of promotions
- User behavior patterns

### **Promo Code Analytics:**
- Usage count per code
- Revenue generated vs. discounted
- Conversion rate by promo code
- Expiration and renewal patterns

---

## 🎯 Success Metrics

### **Technical Metrics:**
- ✅ Promo code validation < 200ms
- ✅ Payment flow integration seamless
- ✅ 100% discount flow works without payment
- ✅ Analytics data accurate and real-time

### **Business Metrics:**
- 📈 Increased conversion rates
- 📈 Higher user engagement
- 📈 Better customer acquisition
- 📈 Improved revenue tracking

---

## 🚀 Next Steps

1. **Review this design** - Does this meet your requirements?
2. **Database schema approval** - Any changes needed?
3. **API design validation** - Endpoints look correct?
4. **Frontend flow confirmation** - User experience acceptable?
5. **Implementation priority** - Which phase to start with?

**Questions for Discussion:**
- Should promo codes be case-sensitive?
- What's the maximum discount percentage allowed?
- How long should promo codes be valid?
- Should we track user email for promo code limits?
- Any specific analytics requirements?

What are your thoughts on this design? Any changes or additions needed?
