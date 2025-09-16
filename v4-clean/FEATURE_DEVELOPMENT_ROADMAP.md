# Feature Development Roadmap: Bundling & Credit Points

## 🎯 Strategic Priority Framework

**Decision Date**: September 16, 2025  
**New Features**: Bundling System + Credit Points System  
**Approach**: Foundation-First Development  

## 📋 Implementation Timeline

### **Phase 1: Foundation Stabilization (Weeks 1-2)**
**Goal**: Prepare codebase for new feature development

#### **Critical Fixes (Must Do First)**
- [ ] **Standardize Error Handling Patterns**
  - Location: `app/services/analysis.py`, API endpoints
  - Impact: Prevents duplicate error handling across new features
  - Effort: Medium (3-5 days)
  - **Blocker for**: Both credit points and bundling

- [ ] **Refactor Payment/Database Layer**
  - Location: `app/services/payments.py`, `app/core/database.py`
  - Impact: Credit points need payment changes, bundles need transaction handling
  - Effort: High (1-2 weeks)
  - **Blocker for**: Credit system foundation

- [ ] **Add Core Input Validation**
  - Location: All API endpoints
  - Impact: New endpoints will need server-side validation
  - Effort: Low-Medium (2-3 days)
  - **Blocker for**: Security compliance

#### **Database Schema Planning**
- [ ] Design credit points table structure
- [ ] Design bundle definition tables
- [ ] Plan transaction logging for both systems
- [ ] Migration strategy for existing data

### **Phase 2: Credit Points System (Weeks 3-4)**
**Goal**: Implement user credit/wallet system

#### **New Components to Build**
```
app/services/credits.py          # Credit balance management
app/core/database.py            # Credit transaction tables
app/api/credits.py              # Credit management endpoints
```

#### **Features to Implement**
- [ ] Credit purchase flow integration
- [ ] Credit balance tracking
- [ ] Credit consumption logic
- [ ] Credit transaction history
- [ ] Credit-based product access

#### **Database Schema**
```sql
CREATE TABLE user_credits (
    id TEXT PRIMARY KEY,
    user_session_id TEXT,
    balance INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE credit_transactions (
    id TEXT PRIMARY KEY,
    user_session_id TEXT,
    type TEXT NOT NULL, -- 'purchase', 'consume', 'refund'
    amount INTEGER NOT NULL,
    description TEXT,
    analysis_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Phase 3: Bundle System (Weeks 5-6)**
**Goal**: Implement multi-product bundling

#### **New Components to Build**
```
app/services/bundles.py         # Bundle logic and pricing
app/services/cart.py           # Multi-product cart handling
app/api/bundles.py             # Bundle management endpoints
```

#### **Features to Implement**
- [ ] Bundle definition and pricing
- [ ] Multi-product cart functionality
- [ ] Bundle purchase workflow
- [ ] Bundle activation and tracking
- [ ] Bundle-specific discounting logic

#### **Database Schema**
```sql
CREATE TABLE bundles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    products JSON NOT NULL, -- Array of product types
    price INTEGER NOT NULL,
    discount_percentage INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bundle_purchases (
    id TEXT PRIMARY KEY,
    user_session_id TEXT,
    bundle_id TEXT,
    stripe_session_id TEXT,
    status TEXT NOT NULL,
    products_used JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Phase 4: Polish & Remaining Fixes (Week 7+)**
**Goal**: Address remaining technical debt

#### **Deferred Fixes (Post-Feature Launch)**
- [ ] Frontend modularization (`index.html` → separate files)
- [ ] Performance optimizations (connection pooling, lazy loading)
- [ ] Comprehensive test suite
- [ ] Monitoring and metrics setup

## 🏗️ Architecture Decisions

### **Credit Points System Architecture**
```
User Flow:
1. User purchases credits via Stripe
2. Credits added to user_credits table
3. When using premium features, credits consumed
4. Credit balance checked before feature access
5. Transaction logged for audit trail

Technical Components:
- CreditService: Balance management and consumption
- CreditDB: Database operations for credits
- Credit middleware: Check balance before premium features
```

### **Bundle System Architecture**
```
User Flow:
1. User selects bundle (e.g., "Power Pack" = Cover Letter + Resume Rewrite)
2. Bundle added to cart with discounted pricing
3. Single payment for entire bundle
4. Bundle "unlocks" access to included products
5. User can consume bundle products as needed

Technical Components:
- BundleService: Bundle logic and pricing calculations
- CartService: Multi-product cart management
- Bundle middleware: Check bundle access for products
```

## ⚠️ Risk Mitigation

### **High Risk Areas**
1. **Payment Integration Complexity**
   - Mitigation: Build on existing Stripe foundation
   - Testing: Extensive payment flow testing required

2. **User Session Management**
   - Current: File-based sessions
   - Risk: Credit/bundle tracking across sessions
   - Mitigation: Implement robust session persistence

3. **Database Transaction Integrity**
   - Risk: Credit balance inconsistencies
   - Mitigation: Use database transactions for credit operations

### **Technical Debt Impact**
- **Frontend Monolith**: Won't block backend features
- **Service Layer Size**: Will grow with new features - monitor complexity
- **Test Coverage**: Build tests as features are developed

## 🚀 Success Metrics

### **Phase 1 Success**
- [ ] All new API endpoints use consistent error handling
- [ ] Server-side validation on all inputs
- [ ] Payment system ready for extension

### **Phase 2 Success** 
- [ ] Users can purchase and spend credits
- [ ] Credit balance accurately tracked
- [ ] Credit transactions properly logged

### **Phase 3 Success**
- [ ] Users can purchase bundles with discounts
- [ ] Bundle products accessible after purchase
- [ ] Bundle usage properly tracked

## 📊 Resource Allocation

### **Development Effort**
- Foundation fixes: 1-2 weeks (high priority)
- Credit Points: 1-2 weeks (medium complexity)
- Bundle System: 1-2 weeks (high complexity)
- Polish/cleanup: Ongoing (low priority)

### **Testing Strategy**
- Unit tests: Build with each feature
- Integration tests: Payment flows critical
- User acceptance testing: Before each phase release

---

**Next Steps**: Complete Phase 1 foundation work before starting feature development. This ensures new features are built on solid architectural patterns.

*This roadmap prioritizes foundation stability over speed to ensure maintainable, scalable feature development.*
