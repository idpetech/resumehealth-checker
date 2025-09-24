# 🚀 **Unified Premium Generation Implementation Plan**

## 🎯 **Implementation Overview**

This document outlines the step-by-step implementation of the unified premium generation architecture to eliminate code duplication and ensure consistency across all premium access methods.

---

## 📋 **Implementation Phases**

### **Phase 1: Core Service Creation (Week 1)**

#### **1.1 Create PremiumGenerationService**
```python
# app/services/premium_generation.py
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class AccessType(Enum):
    PAYMENT = "payment"
    PROMO_CODE = "promo_code"
    ADMIN_OVERRIDE = "admin_override"
    BUNDLE = "bundle"
    GIFT_CODE = "gift_code"

@dataclass
class AccessContext:
    access_type: AccessType
    payment_id: Optional[str] = None
    promo_code: Optional[str] = None
    admin_user: Optional[str] = None
    bundle_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class PremiumGenerationService:
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.database_service = DatabaseService()
        self.analytics_service = AnalyticsService()
        self.access_validator = AccessValidator()
    
    async def generate_premium_results(
        self, 
        analysis_id: str, 
        access_context: AccessContext
    ) -> PremiumResult:
        """Unified method for generating premium results"""
        try:
            # 1. Validate access rights
            await self.access_validator.validate_access(analysis_id, access_context)
            
            # 2. Generate premium analysis
            premium_result = await self.analysis_service.generate_premium_analysis(
                analysis_id=analysis_id,
                access_context=access_context
            )
            
            # 3. Store results
            await self.database_service.store_premium_results(
                analysis_id=analysis_id,
                premium_result=premium_result,
                access_context=access_context
            )
            
            # 4. Track analytics
            await self.analytics_service.track_premium_generation(
                analysis_id=analysis_id,
                access_context=access_context
            )
            
            return premium_result
            
        except Exception as e:
            await self.analytics_service.track_error(
                analysis_id=analysis_id,
                error=str(e),
                access_context=access_context
            )
            raise
```

#### **1.2 Create AccessValidator**
```python
# app/services/access_validator.py
class AccessValidator:
    async def validate_access(self, analysis_id: str, access_context: AccessContext) -> bool:
        """Validate access rights based on access type"""
        if access_context.access_type == AccessType.PAYMENT:
            return await self._validate_payment_access(analysis_id, access_context)
        elif access_context.access_type == AccessType.PROMO_CODE:
            return await self._validate_promo_access(analysis_id, access_context)
        elif access_context.access_type == AccessType.ADMIN_OVERRIDE:
            return await self._validate_admin_access(analysis_id, access_context)
        elif access_context.access_type == AccessType.BUNDLE:
            return await self._validate_bundle_access(analysis_id, access_context)
        else:
            raise InvalidAccessTypeError(f"Unknown access type: {access_context.access_type}")
    
    async def _validate_payment_access(self, analysis_id: str, context: AccessContext) -> bool:
        """Validate payment-based access"""
        payment = await self.database_service.get_payment(context.payment_id)
        return payment and payment.status == "completed" and payment.analysis_id == analysis_id
    
    async def _validate_promo_access(self, analysis_id: str, context: AccessContext) -> bool:
        """Validate promotional code access"""
        promo_code = await self.database_service.get_promo_code(context.promo_code)
        return promo_code and promo_code.is_active and promo_code.discount_value == 100
    
    async def _validate_admin_access(self, analysis_id: str, context: AccessContext) -> bool:
        """Validate admin override access"""
        admin_user = await self.database_service.get_admin_user(context.admin_user)
        return admin_user and admin_user.has_premium_override_permission
    
    async def _validate_bundle_access(self, analysis_id: str, context: AccessContext) -> bool:
        """Validate bundle purchase access"""
        bundle = await self.database_service.get_bundle(context.bundle_id)
        return bundle and bundle.status == "completed" and analysis_id in bundle.included_analyses
```

---

### **Phase 2: Update Existing Flows (Week 2)**

#### **2.1 Update Payment Flow**
```python
# app/api/payments.py
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    # ... existing webhook verification code ...
    
    if event_type == "checkout.session.completed":
        session_id = event_data["id"]
        payment = await payment_service.get_payment_by_session(session_id)
        
        if payment and payment.status == "completed":
            # Use unified service instead of direct analysis generation
            access_context = AccessContext(
                access_type=AccessType.PAYMENT,
                payment_id=payment.id,
                metadata={"stripe_session_id": session_id}
            )
            
            premium_result = await premium_generation_service.generate_premium_results(
                analysis_id=payment.analysis_id,
                access_context=access_context
            )
            
            return {"status": "success", "result": premium_result}
```

#### **2.2 Update Promotional Codes Flow**
```python
# app/api/promotional.py
@router.post("/apply")
async def apply_promo_code(request: PromoCodeRequest):
    # ... existing promo code validation ...
    
    if promo_code.discount_value == 100:
        # 100% discount - skip payment, generate premium results directly
        access_context = AccessContext(
            access_type=AccessType.PROMO_CODE,
            promo_code=promo_code.code,
            metadata={"discount_value": 100}
        )
        
        premium_result = await premium_generation_service.generate_premium_results(
            analysis_id=request.analysis_id,
            access_context=access_context
        )
        
        return {"status": "success", "result": premium_result, "payment_required": False}
    else:
        # Partial discount - proceed with discounted payment
        discounted_amount = calculate_discounted_amount(original_amount, promo_code.discount_value)
        payment_session = await payment_service.create_discounted_session(
            analysis_id=request.analysis_id,
            amount=discounted_amount,
            promo_code=promo_code.code
        )
        
        return {"status": "success", "payment_session": payment_session, "payment_required": True}
```

#### **2.3 Update Bundle Flow**
```python
# app/api/bundles.py
@router.post("/purchase")
async def purchase_bundle(request: BundleRequest):
    # ... existing bundle purchase logic ...
    
    if bundle_payment.status == "completed":
        # Generate premium results for all included analyses
        access_context = AccessContext(
            access_type=AccessType.BUNDLE,
            bundle_id=bundle_payment.bundle_id,
            metadata={"bundle_type": bundle_payment.bundle_type}
        )
        
        premium_results = []
        for analysis_id in bundle_payment.included_analyses:
            premium_result = await premium_generation_service.generate_premium_results(
                analysis_id=analysis_id,
                access_context=access_context
            )
            premium_results.append(premium_result)
        
        return {"status": "success", "results": premium_results}
```

---

### **Phase 3: Testing & Validation (Week 3)**

#### **3.1 Unit Tests**
```python
# tests/test_premium_generation_service.py
class TestPremiumGenerationService:
    async def test_generate_premium_results_payment(self):
        """Test premium generation for payment access"""
        access_context = AccessContext(
            access_type=AccessType.PAYMENT,
            payment_id="test_payment_123"
        )
        
        result = await self.premium_generation_service.generate_premium_results(
            analysis_id="test_analysis_123",
            access_context=access_context
        )
        
        assert result is not None
        assert result.analysis_id == "test_analysis_123"
        assert result.access_type == AccessType.PAYMENT
    
    async def test_generate_premium_results_promo_code(self):
        """Test premium generation for 100% promo code"""
        access_context = AccessContext(
            access_type=AccessType.PROMO_CODE,
            promo_code="FREEPREMIUM2025"
        )
        
        result = await self.premium_generation_service.generate_premium_results(
            analysis_id="test_analysis_123",
            access_context=access_context
        )
        
        assert result is not None
        assert result.access_type == AccessType.PROMO_CODE
    
    async def test_access_validation_failure(self):
        """Test access validation failure"""
        access_context = AccessContext(
            access_type=AccessType.PAYMENT,
            payment_id="invalid_payment"
        )
        
        with pytest.raises(AccessDeniedError):
            await self.premium_generation_service.generate_premium_results(
                analysis_id="test_analysis_123",
                access_context=access_context
            )
```

#### **3.2 Integration Tests**
```python
# tests/test_integration_premium_flows.py
class TestPremiumFlowIntegration:
    async def test_complete_payment_flow(self):
        """Test complete payment flow with unified service"""
        # 1. Create analysis
        analysis = await self.create_test_analysis()
        
        # 2. Create payment session
        payment_session = await self.payment_service.create_payment_session(
            analysis_id=analysis.id,
            amount=2500
        )
        
        # 3. Simulate payment completion
        await self.payment_service.complete_payment(payment_session.id)
        
        # 4. Verify premium results generated
        premium_result = await self.database_service.get_premium_result(analysis.id)
        assert premium_result is not None
        assert premium_result.access_type == AccessType.PAYMENT
    
    async def test_complete_promo_code_flow(self):
        """Test complete promo code flow with unified service"""
        # 1. Create analysis
        analysis = await self.create_test_analysis()
        
        # 2. Apply 100% promo code
        promo_result = await self.promotional_service.apply_promo_code(
            analysis_id=analysis.id,
            promo_code="FREEPREMIUM2025"
        )
        
        # 3. Verify premium results generated
        premium_result = await self.database_service.get_premium_result(analysis.id)
        assert premium_result is not None
        assert premium_result.access_type == AccessType.PROMO_CODE
```

---

### **Phase 4: Migration & Deployment (Week 4)**

#### **4.1 Database Migration**
```sql
-- Add access_type and access_context to premium_results table
ALTER TABLE premium_results 
ADD COLUMN access_type VARCHAR(50) NOT NULL DEFAULT 'payment',
ADD COLUMN access_context JSONB;

-- Create index for access_type queries
CREATE INDEX idx_premium_results_access_type ON premium_results(access_type);

-- Create index for access_context queries
CREATE INDEX idx_premium_results_access_context ON premium_results USING GIN(access_context);
```

#### **4.2 Gradual Migration Strategy**
1. **Deploy unified service** alongside existing code
2. **Feature flag** to switch between old and new flows
3. **A/B test** with small percentage of users
4. **Monitor** performance and error rates
5. **Gradually increase** percentage using new flow
6. **Remove** old code once migration is complete

---

## 📊 **Success Metrics**

### **Code Quality Metrics**
- **Duplication Reduction**: 100% elimination of duplicate premium generation logic
- **Test Coverage**: 100% coverage for unified service
- **Maintainability**: Single point of change for premium generation

### **Performance Metrics**
- **Response Time**: < 2 seconds for premium generation
- **Error Rate**: < 0.1% for premium generation
- **Consistency**: 100% consistent results across access types

### **Business Metrics**
- **User Experience**: Consistent premium experience regardless of access method
- **Analytics**: Unified tracking of all premium access methods
- **Scalability**: Easy addition of new access types

---

## 🔗 **Related Documentation**
- **Architecture**: [Unified Premium Generation Architecture](../architecture/UNIFIED_PREMIUM_GENERATION.md)
- **Service Design**: [Premium Generation Service Design](../services/premium-generation-service.md)
- **API Design**: [Unified Premium API](../api/premium-generation-api.md)
- **Testing Strategy**: [Unified Premium Testing](../tests/premium-generation-tests.md)
