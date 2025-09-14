# Resume Health Checker v4.0 - TODO List

**Status**: 🚧 ACTIVE DEVELOPMENT  
**Current Priority**: Phase 1 - Repository Restructuring  
**Last Updated**: 2025-09-02 12:00 UTC

---

## 🎯 PHASE 1: Repository Restructuring [IN PROGRESS]

### ✅ COMPLETED
- [x] **Repository Analysis** - Complete codebase analysis done
- [x] **Architecture Planning** - v4 clean architecture designed
- [x] **Documentation Setup** - V4_EXECUTION_LOG.md and V4_TODO.md created

### 🚧 IN PROGRESS
- [ ] **Create v4-clean Directory Structure**
  - **Action**: `mkdir v4-clean && cd v4-clean`
  - **Expected**: Clean directory with proper app structure
  - **Files to Create**:
    ```
    v4-clean/
    ├── main.py
    ├── requirements.txt
    ├── app/
    │   ├── __init__.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   └── exceptions.py
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── analysis.py
    │   │   ├── payments.py
    │   │   ├── files.py
    │   │   └── geo.py
    │   ├── api/
    │   │   ├── __init__.py
    │   │   └── routes.py
    │   ├── data/
    │   │   ├── prompts.json
    │   │   ├── pricing.json
    │   │   └── geo.json
    │   └── static/
    │       └── index.html
    └── .env.example
    ```

### 🔜 NEXT TASKS
- [ ] **Archive Legacy Code**
  - **Action**: Move all current code to `archive/v1-v3-legacy/`
  - **Command**: 
    ```bash
    mkdir -p archive/v1-v3-legacy
    mv app/ main_modular.py requirements*.txt archive/v1-v3-legacy/
    mv archive/monolith/ archive/v1-v3-legacy/monolith/
    ```
  - **Verify**: Only `v4-clean/`, docs, and `.env` remain in root

- [ ] **Extract Working Business Logic**
  - **Source**: `archive/v1-v3-legacy/prompts/prompts.json`
  - **Target**: `v4-clean/app/data/prompts.json`
  - **Source**: `archive/v1-v3-legacy/pricing_config_multi_product.json`
  - **Target**: `v4-clean/app/data/pricing.json` (cleaned up)
  - **Source**: `archive/v1-v3-legacy/app/templates/index.html`
  - **Target**: `v4-clean/app/static/index.html` (static version)

---

## 🎯 PHASE 2: Core Application [PENDING]

### 📋 Core Infrastructure
- [ ] **main.py - Single Entry Point**
  - FastAPI app initialization
  - Static file serving
  - Environment detection
  - Port configuration for Railway

- [ ] **app/core/config.py - Environment Configuration**
  - Multi-environment support (local/staging/production)
  - OpenAI API key validation
  - Stripe key configuration
  - Database path settings

- [ ] **app/core/database.py - SQLite Database**
  - Connection management
  - Table creation (analyses, payments)
  - Basic CRUD operations
  - No ORM - pure SQL for simplicity

- [ ] **app/core/exceptions.py - Error Handling**
  - Custom exception classes
  - HTTP exception mapping
  - Structured error responses

### 📋 Services Layer
- [ ] **app/services/analysis.py - AI Analysis**
  - OpenAI client initialization
  - Prompt loading from JSON
  - Free vs Premium analysis logic
  - Error handling and retries

- [ ] **app/services/files.py - File Processing**
  - PDF text extraction (built-in tools + fallback)
  - DOCX text extraction (zipfile + XML parsing)
  - File validation (size, type, content)
  - Clean text processing

- [ ] **app/services/payments.py - Stripe Integration**
  - Session creation with bulletproof URLs
  - Payment verification
  - Multi-environment key management
  - Webhook handling

- [ ] **app/services/geo.py - IP Geolocation**
  - Static IP range database
  - Country detection from IP
  - Currency mapping
  - No external API dependencies

### 📋 API Layer
- [ ] **app/api/routes.py - All Endpoints**
  - `GET /` - Frontend (static file)
  - `POST /api/analyze` - File upload + analysis
  - `POST /api/payment/create` - Create Stripe session
  - `GET /api/payment/success` - Handle successful payment
  - `GET /api/payment/cancel` - Handle cancelled payment
  - `POST /webhooks/stripe` - Stripe webhook handler
  - `GET /api/pricing/{country}` - Regional pricing
  - `GET /health` - Health check

---

## 🎯 PHASE 3: Stripe Integration [PENDING]

### 📋 Multi-Environment Setup
- [ ] **Environment Configuration**
  - Local: Test keys + localhost URLs
  - Staging: Test keys + Railway staging URLs  
  - Production: Live keys + Railway production URLs

- [ ] **Bulletproof Payment URLs**
  - Success URL with all parameters: `session_id`, `analysis_id`, `product_type`
  - Cancel URL with context preservation
  - Proper error handling for URL failures

- [ ] **Payment Session Management**
  - Unique session reference generation
  - Database tracking of payment sessions
  - Session expiry handling (30 minutes)
  - Metadata preservation in Stripe

- [ ] **Webhook Integration**
  - Signature verification
  - Event handling (`checkout.session.completed`)
  - Duplicate event prevention
  - Error recovery

### 📋 Payment Flow Logic
- [ ] **Free Analysis Flow**
  - File upload → text extraction → AI analysis
  - Show preview with upgrade CTA
  - Store analysis with "pending" payment status

- [ ] **Premium Upgrade Flow**
  - Create Stripe session with analysis context
  - Redirect to Stripe Checkout
  - Handle success/cancel returns
  - Complete premium analysis on success

- [ ] **Regional Pricing**
  - IP-based country detection
  - Currency mapping (USD, PKR, INR, HKD, AED, BDT)
  - Price calculation based on region
  - Fallback to USD for unknown regions

---

## 🎯 PHASE 4: Testing & Deployment [PENDING]

### 📋 Local Testing
- [ ] **Unit Tests**
  - File processing with sample PDF/DOCX
  - OpenAI integration with mock responses
  - Database operations
  - Pricing calculations

- [ ] **Integration Tests**
  - Complete analysis flow
  - Stripe session creation
  - Payment webhook handling
  - Error scenarios

- [ ] **Manual Testing**
  - Upload different file types
  - Test payment flow with test cards
  - Verify success/cancel redirects
  - Test regional pricing

### 📋 Staging Environment
- [ ] **Railway Staging Setup**
  - Create separate Railway project
  - Set staging environment variables
  - Deploy v4-clean to staging
  - Configure Stripe test webhooks

- [ ] **End-to-End Testing**
  - Full user journey testing
  - Payment flow validation
  - Error handling verification
  - Performance benchmarking

### 📋 Production Deployment
- [ ] **Railway Production Setup**
  - Production environment variables
  - Live Stripe keys configuration
  - Production webhook endpoints
  - Domain configuration

- [ ] **Launch Validation**
  - Health check endpoint
  - Payment flow verification
  - Error monitoring setup
  - Performance monitoring

---

## 📊 SUCCESS CRITERIA

### ✅ Technical Requirements
- [ ] **Single Entry Point**: `python main.py` starts everything
- [ ] **Minimal Dependencies**: Only 5 packages in requirements.txt
- [ ] **Fast Response Times**: <200ms for non-AI endpoints
- [ ] **Error Handling**: Graceful failures with user-friendly messages
- [ ] **Environment Separation**: Clean local/staging/production configuration

### ✅ Business Requirements  
- [ ] **Complete Payment Flow**: Upload → Analysis → Payment → Results
- [ ] **Stripe Integration**: Zero payment failures or user confusion
- [ ] **Multi-Product Support**: Resume ($10), Job Fit ($12), Cover Letter ($8)
- [ ] **Regional Pricing**: 6 currencies with proper formatting
- [ ] **File Processing**: PDF, DOCX, TXT support with error handling

### ✅ Deployment Requirements
- [ ] **Railway Compatibility**: Zero-config deployment
- [ ] **Environment Variables**: Proper configuration management
- [ ] **Database Persistence**: SQLite data survives deployments
- [ ] **Static File Serving**: Frontend loads correctly
- [ ] **HTTPS Support**: Secure payment processing

---

## 🚨 CRITICAL REMINDERS

### **For Current AI Agent:**
- Work ONLY in `v4-clean/` directory
- Never modify `archive/v1-v3-legacy/` files
- Update this TODO with [x] as tasks complete
- Commit frequently with descriptive messages
- Test locally before moving to next phase

### **For Next AI Agent:**
- Read `V4_EXECUTION_LOG.md` for full context
- Check what's [x] completed in this file
- Continue from first [ ] uncompleted task
- Update progress in real-time
- Preserve all business logic from archive

### **Emergency Contacts:**
- Original working code: `archive/v1-v3-legacy/main_vercel.py`
- Working prompts: `archive/v1-v3-legacy/prompts/prompts.json`
- Working pricing: `archive/v1-v3-legacy/pricing_config_multi_product.json`

---

**NEXT ACTION**: Create v4-clean directory structure (Phase 1, Task 1)  
**ESTIMATED TIME**: 30 minutes for directory setup  
**SUCCESS METRIC**: Clean directory structure ready for core development