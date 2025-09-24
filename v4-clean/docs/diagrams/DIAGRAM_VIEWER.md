# 🎨 **Resume Health Checker v4.0 - Diagram Viewer**

## 🎯 **Interactive Diagram Navigation**

This page provides direct access to all Mermaid diagrams with live rendering. Click on any diagram to view it in full detail.

---

## 🔄 **Flow Diagrams**

### **Flow 1: Free Resume Analysis**
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

### **Flow 2: Premium Payment & Results**
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

### **Flow 3: Bundle Purchase & Delivery**
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

### **Flow 4: Promotional Code Application**
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

---

## 🔄 **Sequence Diagrams**

### **Free Resume Analysis Sequence**
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

### **Premium Payment Sequence**
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

### **Promotional Code Sequence**
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

---

## 🗄️ **Schema Diagrams**

### **Core Database Schema**
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

### **Promotional Code Schema**
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

---

## 🏗️ **Architectural Diagrams**

### **System Architecture**
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

### **Security Architecture**
```mermaid
graph TB
    subgraph "Environment Layers"
        LOCAL[Local Development]
        STAGING[Staging Environment]
        PROD[Production Environment]
    end
    
    subgraph "Security Levels"
        SEC1[No Authentication]
        SEC2[Optional Authentication]
        SEC3[Required Authentication]
    end
    
    subgraph "Security Features"
        AUTH[API Key Authentication]
        RATE[Rate Limiting]
        VALID[Input Validation]
        ADMIN[Admin Protection]
    end
    
    LOCAL --> SEC1
    STAGING --> SEC2
    PROD --> SEC3
    
    SEC2 --> AUTH
    SEC3 --> AUTH
    SEC3 --> RATE
    SEC3 --> VALID
    SEC3 --> ADMIN
```

---

## 📊 **Sprint Planning Diagrams**

### **Sprint 1: Foundation & Security**
```mermaid
gantt
    title Sprint 1: Foundation & Security
    dateFormat  YYYY-MM-DD
    section Security
    Environment-Aware Security    :done, sec1, 2025-01-21, 2d
    Authentication & Authorization :active, sec2, 2025-01-23, 2d
    Security Testing              :sec3, 2025-01-25, 1d
    section Bug Fixes
    Critical Bug Fixes           :bug1, 2025-01-23, 2d
    Test Implementation           :bug2, 2025-01-25, 2d
    section Quality Assurance
    Full Test Suite              :qa1, 2025-01-27, 1d
    Security Scan                :qa2, 2025-01-27, 1d
```

### **Sprint 2: Feature Development**
```mermaid
gantt
    title Sprint 2: Feature Development
    dateFormat  YYYY-MM-DD
    section Bundle Features
    Bundle Products              :bundle1, 2025-01-28, 2d
    Bundle Testing               :bundle2, 2025-01-30, 2d
    section Data Protection
    Data Protection              :data1, 2025-01-28, 2d
    section Testing
    Integration Tests            :test1, 2025-01-30, 2d
```

---

## 🧪 **Test Coverage Diagrams**

### **Test Coverage Matrix**
```mermaid
graph TB
    subgraph "Test Categories"
        UNIT[Unit Tests]
        INTEGRATION[Integration Tests]
        E2E[End-to-End Tests]
        SECURITY[Security Tests]
        PERFORMANCE[Performance Tests]
    end
    
    subgraph "Coverage Targets"
        TARGET1[100% Function Coverage]
        TARGET2[100% API Coverage]
        TARGET3[100% Flow Coverage]
        TARGET4[100% Security Coverage]
        TARGET5[100% Performance Coverage]
    end
    
    UNIT --> TARGET1
    INTEGRATION --> TARGET2
    E2E --> TARGET3
    SECURITY --> TARGET4
    PERFORMANCE --> TARGET5
```

---

## 🎯 **Quick Diagram Access**

### **By Feature**
- **Free Analysis**: [Flow 1](#flow-1-free-resume-analysis) | [Sequence 1](#free-resume-analysis-sequence)
- **Premium Payment**: [Flow 2](#flow-2-premium-payment--results) | [Sequence 2](#premium-payment-sequence)
- **Bundle Purchase**: [Flow 3](#flow-3-bundle-purchase--delivery)
- **Promotional Codes**: [Flow 4](#flow-4-promotional-code-application) | [Sequence 3](#promotional-code-sequence)

### **By Type**
- **Flow Diagrams**: [All Flows](#flow-diagrams)
- **Sequence Diagrams**: [All Sequences](#sequence-diagrams)
- **Schema Diagrams**: [All Schemas](#schema-diagrams)
- **Architectural Diagrams**: [All Architectures](#architectural-diagrams)

### **By Sprint**
- **Sprint 1**: [Sprint 1 Gantt](#sprint-1-foundation--security)
- **Sprint 2**: [Sprint 2 Gantt](#sprint-2-feature-development)

---

## 📱 **Mobile-Friendly Viewing**

### **Diagram Viewing Tips**
- **Zoom**: Use browser zoom (Ctrl/Cmd + Plus)
- **Scroll**: Use mouse wheel or touch gestures
- **Full Screen**: Press F11 for full-screen viewing
- **Print**: Use browser print function for PDF export

### **Accessibility**
- **High Contrast**: Diagrams use high-contrast colors
- **Large Text**: All text is readable at standard sizes
- **Clear Labels**: All elements are clearly labeled
- **Logical Flow**: Diagrams follow logical reading patterns

---

## 🔄 **Diagram Updates**

### **When to Update**
- **New Features**: Add new flow diagrams
- **Architecture Changes**: Update architectural diagrams
- **Schema Changes**: Update database schemas
- **Process Changes**: Update sequence diagrams

### **Update Process**
1. Update the relevant diagram in source document
2. Copy updated diagram to this viewer
3. Test diagram rendering
4. Update navigation links

---

**This diagram viewer provides instant access to all visual documentation. Bookmark this page for quick diagram reference!**
