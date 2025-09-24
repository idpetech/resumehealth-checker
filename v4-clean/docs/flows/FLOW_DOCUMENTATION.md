# 📊 **Resume Health Checker v4.0 - Complete Flow Documentation**

## 🎯 **Flow Overview**

This document provides comprehensive documentation for all user flows in the Resume Health Checker application, including:
- Flow Diagrams
- Sequence Diagrams  
- Schema Diagrams
- Architectural Diagrams
- Test Coverage Requirements

---

## 🔄 **Flow 1: Free Resume Analysis**

### **Flow Diagram**
```mermaid
flowchart TD
    A[User Uploads Resume] --> B{File Valid?}
    B -->|No| C[Show Error Message]
    B -->|Yes| D[Extract Text from File]
    D --> E{Text Extraction Success?}
    E -->|No| F[Show File Processing Error]
    E -->|Yes| G[Validate Resume Content]
    G --> H{Content Valid?}
    H -->|No| I[Show Validation Error]
    H -->|Yes| J[Create Analysis Record]
    J --> K[Call OpenAI API]
    K --> L{AI Analysis Success?}
    L -->|No| M[Show AI Error]
    L -->|Yes| N[Store Free Results]
    N --> O[Display Free Analysis Results]
    O --> P[Show Premium Upgrade Options]
```

### **Sequence Diagram**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant FS as FileService
    participant AS as AnalysisService
    participant DB as Database
    participant OAI as OpenAI

    U->>F: Upload Resume File
    F->>A: POST /api/v1/analyze
    A->>FS: extract_text_from_file()
    FS-->>A: resume_text
    A->>AS: validate_resume_content()
    AS-->>A: validation_result
    A->>DB: create_analysis_record()
    DB-->>A: analysis_id
    A->>AS: analyze_resume()
    AS->>OAI: GPT API Call
    OAI-->>AS: analysis_result
    AS-->>A: formatted_result
    A->>DB: update_free_result()
    A-->>F: analysis_response
    F-->>U: Display Results
```

### **Schema Diagram**
```mermaid
erDiagram
    ANALYSES {
        string id PK
        string filename
        int file_size
        text resume_text
        string analysis_type
        text free_result
        text premium_result
        string payment_status
        datetime created_at
        datetime updated_at
    }
```

### **Architectural Diagram**
```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[HTML/JS Interface]
    end
    
    subgraph "API Layer"
        ROUTES[FastAPI Routes]
        VALIDATION[Input Validation]
    end
    
    subgraph "Service Layer"
        FILES[File Service]
        ANALYSIS[Analysis Service]
        GEO[Geo Service]
    end
    
    subgraph "Data Layer"
        DB[(SQLite Database)]
    end
    
    subgraph "External Services"
        OPENAI[OpenAI API]
    end
    
    UI --> ROUTES
    ROUTES --> VALIDATION
    VALIDATION --> FILES
    VALIDATION --> ANALYSIS
    FILES --> DB
    ANALYSIS --> DB
    ANALYSIS --> OPENAI
    GEO --> DB
```

### **Test Coverage Requirements**
```python
# test_free_analysis_success.py
def test_free_analysis_success():
    """Test successful free analysis flow"""
    pass

def test_free_analysis_invalid_file():
    """Test analysis with invalid file format"""
    pass

def test_free_analysis_empty_content():
    """Test analysis with empty resume content"""
    pass

def test_free_analysis_ai_failure():
    """Test analysis when OpenAI API fails"""
    pass

def test_free_analysis_database_error():
    """Test analysis when database operations fail"""
    pass
```

---

## 💳 **Flow 2: Premium Payment & Results**

### **Flow Diagram**
```mermaid
flowchart TD
    A[User Selects Premium Feature] --> B[Show Pricing Options]
    B --> C[User Enters Job Posting]
    C --> D[Click Purchase Selected]
    D --> E[Create Payment Session]
    E --> F{Payment Session Created?}
    F -->|No| G[Show Payment Error]
    F -->|Yes| H[Redirect to Stripe Checkout]
    H --> I[User Completes Payment]
    I --> J[Stripe Webhook Notification]
    J --> K[Verify Payment Status]
    K --> L{Payment Verified?}
    L -->|No| M[Show Payment Failed]
    L -->|Yes| N[Update Payment Status]
    N --> O[Generate Premium Analysis]
    O --> P[Store Premium Results]
    P --> Q[Redirect to Results Page]
    Q --> R[Display Premium Results]
```

### **Sequence Diagram**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant PS as PaymentService
    participant S as Stripe
    participant AS as AnalysisService
    participant DB as Database

    U->>F: Select Premium Feature
    F->>A: POST /api/v1/payment/create
    A->>PS: create_payment_session()
    PS->>S: Create Checkout Session
    S-->>PS: session_url
    PS-->>A: payment_session
    A-->>F: redirect_url
    F->>S: Redirect to Checkout
    U->>S: Complete Payment
    S->>A: POST /api/v1/webhooks/stripe
    A->>PS: verify_webhook()
    PS->>S: Retrieve Session
    S-->>PS: payment_status
    PS-->>A: verification_result
    A->>DB: update_payment_status()
    A->>AS: generate_premium_analysis()
    AS-->>A: premium_result
    A->>DB: update_premium_result()
    A-->>F: success_response
    F-->>U: Display Premium Results
```

### **Schema Diagram**
```mermaid
erDiagram
    ANALYSES {
        string id PK
        string filename
        text premium_result
        string payment_status
    }
    
    PAYMENTS {
        string id PK
        string analysis_id FK
        string stripe_session_id
        int amount
        string currency
        string status
        datetime created_at
    }
    
    ANALYSES ||--o{ PAYMENTS : "has"
```

### **Test Coverage Requirements**
```python
# test_premium_payment_success.py
def test_premium_payment_success():
    """Test successful premium payment flow"""
    pass

def test_premium_payment_session_creation():
    """Test payment session creation"""
    pass

def test_premium_payment_webhook_verification():
    """Test Stripe webhook verification"""
    pass

def test_premium_payment_failed():
    """Test failed payment handling"""
    pass

def test_premium_payment_duplicate():
    """Test duplicate payment prevention"""
    pass
```

---

## 📦 **Flow 3: Bundle Purchase & Delivery**

### **Flow Diagram**
```mermaid
flowchart TD
    A[User Selects Bundle] --> B[Show Bundle Pricing]
    B --> C[User Enters Job Posting]
    C --> D[Click Purchase Selected]
    D --> E[Create Payment Session]
    E --> F{Payment Session Created?}
    F -->|No| G[Show Payment Error]
    F -->|Yes| H[Redirect to Stripe Checkout]
    H --> I[User Completes Payment]
    I --> J[Stripe Webhook Notification]
    J --> K[Verify Payment Status]
    K --> L{Payment Verified?}
    L -->|No| M[Show Payment Failed]
    L -->|Yes| N[Update Payment Status]
    N --> O[Generate All Bundle Products]
    O --> P[Store Bundle Results]
    P --> Q[Redirect to Results Page]
    Q --> R[Display Bundle Results]
    R --> S[Show Individual Product Tabs]
```

### **Sequence Diagram**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant PS as PaymentService
    participant S as Stripe
    participant AS as AnalysisService
    participant DB as Database

    U->>F: Select Bundle
    F->>A: POST /api/v1/payment/create
    A->>PS: create_payment_session()
    PS->>S: Create Checkout Session
    S-->>PS: session_url
    PS-->>A: payment_session
    A-->>F: redirect_url
    F->>S: Redirect to Checkout
    U->>S: Complete Payment
    S->>A: POST /api/v1/webhooks/stripe
    A->>PS: verify_webhook()
    PS->>S: Retrieve Session
    S-->>PS: payment_status
    PS-->>A: verification_result
    A->>DB: update_payment_status()
    
    loop For Each Product in Bundle
        A->>AS: generate_product_analysis()
        AS-->>A: product_result
        A->>DB: store_product_result()
    end
    
    A-->>F: success_response
    F-->>U: Display Bundle Results
```

### **Test Coverage Requirements**
```python
# test_bundle_purchase_success.py
def test_bundle_purchase_success():
    """Test successful bundle purchase flow"""
    pass

def test_bundle_all_products_generated():
    """Test all bundle products are generated"""
    pass

def test_bundle_results_display():
    """Test bundle results display with tabs"""
    pass

def test_bundle_pricing_calculation():
    """Test bundle pricing calculation"""
    pass

def test_bundle_partial_failure():
    """Test bundle when some products fail"""
    pass
```

---

## 🎯 **Flow 4: Promotional Code Application**

### **Flow Diagram**
```mermaid
flowchart TD
    A[User Enters Promo Code] --> B[Validate Promo Code]
    B --> C{Code Valid?}
    C -->|No| D[Show Invalid Code Error]
    C -->|Yes| E{Code Active?}
    E -->|No| F[Show Expired Code Error]
    E -->|Yes| G{Usage Limit Reached?}
    G -->|Yes| H[Show Usage Limit Error]
    G -->|No| I[Calculate Discount]
    I --> J[Update Pricing Display]
    J --> K[User Proceeds to Payment]
    K --> L{Discount = 100%?}
    L -->|Yes| M[Skip Payment]
    L -->|No| N[Apply Discount to Payment]
    M --> O[Generate Premium Results]
    N --> P[Process Discounted Payment]
    P --> Q[Generate Premium Results]
    O --> R[Track Promo Usage]
    Q --> R
    R --> S[Display Results]
```

### **Sequence Diagram**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant PS as PromoService
    participant PS2 as PaymentService
    participant DB as Database

    U->>F: Enter Promo Code
    F->>A: POST /api/v1/promo/validate
    A->>PS: validate_promo_code()
    PS->>DB: check_promo_code()
    DB-->>PS: promo_details
    PS-->>A: validation_result
    A-->>F: promo_response
    
    F->>A: POST /api/v1/payment/create
    A->>PS: apply_promo_discount()
    PS-->>A: discounted_amount
    A->>PS2: create_payment_session()
    PS2-->>A: payment_session
    A-->>F: payment_response
    
    F->>A: POST /api/v1/promo/track-usage
    A->>PS: track_promo_usage()
    PS->>DB: update_usage_count()
    PS-->>A: tracking_result
    A-->>F: success_response
```

### **Schema Diagram**
```mermaid
erDiagram
    PROMO_CODES {
        string id PK
        string code
        string discount_type
        decimal discount_value
        int max_uses
        int current_uses
        datetime expires_at
        boolean is_active
        datetime created_at
    }
    
    PROMO_USAGE {
        string id PK
        string promo_code_id FK
        string analysis_id FK
        string user_ip
        datetime used_at
    }
    
    PROMO_CODES ||--o{ PROMO_USAGE : "has"
```

### **Test Coverage Requirements**
```python
# test_promo_code_validation.py
def test_promo_code_valid():
    """Test valid promo code validation"""
    pass

def test_promo_code_invalid():
    """Test invalid promo code validation"""
    pass

def test_promo_code_expired():
    """Test expired promo code validation"""
    pass

def test_promo_code_usage_limit():
    """Test promo code usage limit"""
    pass

def test_promo_code_100_percent_discount():
    """Test 100% discount promo code"""
    pass
```

---

## 📊 **Flow 5: Export & Download**

### **Flow Diagram**
```mermaid
flowchart TD
    A[User Clicks Export] --> B[Select Export Format]
    B --> C{Format Valid?}
    C -->|No| D[Show Format Error]
    C -->|Yes| E[Check Analysis Access]
    E --> F{Has Access?}
    F -->|No| G[Show Access Denied]
    F -->|Yes| H[Generate Export File]
    H --> I{Generation Success?}
    I -->|No| J[Show Generation Error]
    I -->|Yes| K[Return File Download]
    K --> L[User Downloads File]
```

### **Sequence Diagram**
```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant ES as ExportService
    participant DB as Database

    U->>F: Click Export Button
    F->>A: GET /api/v1/export/{id}/pdf
    A->>DB: get_analysis()
    DB-->>A: analysis_data
    A->>ES: generate_pdf()
    ES-->>A: pdf_content
    A-->>F: file_response
    F-->>U: Download File
```

### **Test Coverage Requirements**
```python
# test_export_functionality.py
def test_export_pdf_success():
    """Test successful PDF export"""
    pass

def test_export_docx_success():
    """Test successful DOCX export"""
    pass

def test_export_access_denied():
    """Test export without proper access"""
    pass

def test_export_invalid_format():
    """Test export with invalid format"""
    pass
```

---

## 🔧 **Flow 6: Admin & Debug**

### **Flow Diagram**
```mermaid
flowchart TD
    A[Admin Access] --> B[Authenticate Admin]
    B --> C{Authentication Success?}
    C -->|No| D[Show Access Denied]
    C -->|Yes| E[Show Admin Dashboard]
    E --> F[Select Admin Function]
    F --> G{Function Type?}
    G -->|Stats| H[Display System Statistics]
    G -->|Debug| I[Show Debug Information]
    G -->|Test| J[Run Test Functions]
    H --> K[Return Statistics]
    I --> L[Return Debug Data]
    J --> M[Return Test Results]
```

### **Test Coverage Requirements**
```python
# test_admin_functionality.py
def test_admin_authentication():
    """Test admin authentication"""
    pass

def test_admin_stats_access():
    """Test admin statistics access"""
    pass

def test_admin_debug_access():
    """Test admin debug access"""
    pass

def test_admin_unauthorized_access():
    """Test unauthorized admin access"""
    pass
```

---

## 🧪 **Test Coverage Matrix**

| Flow | Unit Tests | Integration Tests | E2E Tests | Security Tests |
|------|------------|-------------------|-----------|----------------|
| Free Analysis | ✅ | ✅ | ✅ | ✅ |
| Premium Payment | ✅ | ✅ | ✅ | ✅ |
| Bundle Purchase | ✅ | ✅ | ✅ | ✅ |
| Promo Code | ✅ | ✅ | ✅ | ✅ |
| Export | ✅ | ✅ | ✅ | ✅ |
| Admin | ✅ | ✅ | ✅ | ✅ |

---

## 📋 **Implementation Checklist**

### **For Each Flow:**
- [ ] Flow diagram created
- [ ] Sequence diagram created
- [ ] Schema diagram created (if applicable)
- [ ] Architectural diagram created
- [ ] Unit tests written (100% coverage)
- [ ] Integration tests written
- [ ] E2E tests written
- [ ] Security tests written
- [ ] Error handling implemented
- [ ] Input validation implemented
- [ ] Documentation updated

### **Quality Gates:**
- [ ] All tests pass
- [ ] Code coverage = 100%
- [ ] Security scan passes
- [ ] Performance tests pass
- [ ] Documentation complete

---

**This document will be updated as new flows are added or existing flows are modified.**
