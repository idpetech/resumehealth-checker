# Resume Health Checker - Application Flow Diagram

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           RESUME HEALTH CHECKER APPLICATION                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐            │
│  │   LEGACY        │    │   NEW MODULAR   │    │   EXTERNAL      │            │
│  │   (Port 3000)   │    │   (Port 8000)   │    │   SERVICES      │            │
│  │                 │    │                 │    │                 │            │
│  │ • Old Frontend  │    │ • FastAPI       │    │ • OpenAI API    │            │
│  │ • Static Files  │    │ • File Process  │    │ • Stripe API    │            │
│  │ • Legacy UI     │    │ • AI Analysis   │    │ • Payment Proc  │            │
│  │ • Old Version   │    │ • Session Mgmt  │    │                 │            │
│  │                 │    │ • Template Svc  │    │                 │            │
│  │                 │    │ • Main App      │    │                 │            │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Structure

### Legacy Frontend Components (Port 3000) - OLD VERSION
```
frontend/
├── index.html              # Legacy main application page
├── success.html            # Legacy payment success page
├── css/
│   └── styles.css          # Legacy application styling
└── js/
    ├── app.js              # Legacy application logic
    └── config.js           # Legacy API endpoint configuration
```

### New Modular Backend Components (Port 8000) - CURRENT VERSION
```
app/
├── routes/
│   ├── main.py             # Main routes (/, /health, /clear-cache)
│   ├── analysis.py         # Resume analysis endpoint (/api/check-resume)
│   ├── legacy_proxy.py     # Payment & pricing endpoints
│   └── payments.py         # Payment processing
├── services/
│   └── template_service.py # HTML template management
├── utils/
│   └── file_processing.py  # File upload & text extraction
└── config/
    └── settings.py         # Application configuration
```

## Complete User Flow

### 1. Initial Page Load
```
User → http://localhost:8000
  ↓
New Modular Backend serves main application
  ↓
Template Service loads index.html
  ↓
Displays file upload interface
```

### 2. File Upload & Free Analysis
```
User selects resume file (PDF/DOCX/TXT)
  ↓
Frontend: handleFileSelect() → stores file in selectedFile
  ↓
User clicks "Analyze Resume"
  ↓
Frontend: analyzeResume() → creates FormData with file
  ↓
POST /api/check-resume (Same Port 8000 - Internal API)
  ↓
Backend: app/routes/analysis.py
  ├── Validates file type & size
  ├── Calls app/utils/file_processing.py
  │   ├── PDF: pdfplumber extraction
  │   ├── DOCX: python-docx extraction  
  │   └── TXT: direct text reading
  ├── Calls OpenAI API (gpt-4o-mini)
  │   ├── Free analysis prompt
  │   └── Returns structured JSON
  └── Returns analysis to frontend
  ↓
Frontend: displayResults() → shows free analysis
  ├── Overall score
  ├── Major issues
  ├── Teaser message
  └── "Unlock Full Report" button
```

### 3. Payment Flow
```
User clicks "Unlock Full Report - $5"
  ↓
Frontend: createPaymentSession()
  ├── Stores currentAnalysis in session_data
  ├── POST /api/create-payment-session (Same Port 8000)
  └── Sends: product_type, product_id, session_data
  ↓
Backend: app/routes/legacy_proxy.py
  ├── Creates unique session_id (UUID)
  ├── Stores analysis data in memory store
  ├── Gets Stripe payment URL
  ├── Adds session_id to success_url
  └── Returns payment_url to frontend
  ↓
Frontend: redirects to Stripe payment page
  ↓
User completes payment on Stripe
  ↓
Stripe redirects to: success.html?session_id=abc123 (Port 8000)
```

### 4. Payment Success & Analysis Restoration
```
Stripe → http://localhost:8000/success.html?session_id=abc123
  ↓
Backend: app/routes/main.py serves success.html
  ├── Shows success message
  ├── Auto-redirects after 3 seconds
  └── Calls returnToAnalysis() function
  ↓
Frontend: returnToAnalysis()
  ├── Extracts session_id from URL
  ├── GET /api/get-session-data/{session_id} (Same Port 8000)
  └── Backend returns stored analysis data
  ↓
Frontend: stores data in localStorage
  ├── premiumAnalysis: analysis data
  └── paymentToken: payment_success_123
  ↓
Frontend: redirects to /?payment_token=payment_success_123&session_restored=true
  ↓
Frontend: app.js detects session_restored=true
  ├── Retrieves data from localStorage
  ├── Calls displayResults(analysis, true)
  ├── Shows complete premium analysis
  └── Cleans up localStorage
```

## API Endpoints

### New Modular Backend API Routes (Port 8000) - CURRENT VERSION
```
GET  /                           # Serve main HTML (via template service)
GET  /health                     # Health check
GET  /clear-cache                # Clear template cache
GET  /success.html               # Payment success page (served by backend)
POST /api/check-resume           # Resume analysis endpoint
POST /api/create-payment-session # Create payment session
GET  /api/get-session-data/{id}  # Retrieve session data
GET  /api/multi-product-pricing  # Get pricing information
GET  /api/stripe-pricing/{code}  # Get Stripe pricing by country
GET  /api/retrieve-payment-session/{id} # Payment session retrieval
```

### Legacy Frontend Routes (Port 3000) - OLD VERSION
```
GET  /                           # Legacy main application page
GET  /success.html               # Legacy payment success page
GET  /css/styles.css             # Legacy application styles
GET  /js/app.js                  # Legacy application JavaScript
GET  /js/config.js               # Legacy API configuration
```

## Data Flow

### Session Data Storage
```
Payment Session Creation:
├── Frontend sends analysis data
├── Backend stores in memory: payment_session_proxy._session_store
├── Structure: {session_id: {session_data, product_type, product_id, created_at}}
└── Expiration: 1 hour (3600 seconds)

Session Data Retrieval:
├── Frontend requests by session_id
├── Backend validates session exists & not expired
├── Returns stored analysis data
└── Cleans up expired sessions
```

### Analysis Data Structure
```
Free Analysis:
{
  "overall_score": 75,
  "major_issues": ["Issue 1", "Issue 2"],
  "teaser_message": "Your resume shows potential..."
}

Premium Analysis:
{
  "overall_score": 75,
  "ats_optimization": {score, issues, improvements},
  "content_clarity": {score, issues, improvements},
  "impact_metrics": {score, issues, improvements},
  "formatting": {score, issues, improvements},
  "text_rewrites": [{"original": "...", "improved": "..."}],
  "action_plan": ["Step 1", "Step 2"]
}
```

## External Service Integration

### OpenAI Integration
```
Backend → OpenAI API
├── Model: gpt-4o-mini
├── Prompts: Free analysis, Premium analysis, Job matching
├── Response: Structured JSON
└── Error handling: Retry logic, fallback responses
```

### Stripe Integration
```
Backend → Stripe API
├── Static payment links (test mode)
├── Success URL with session_id parameter
├── Product pricing configuration
└── Payment session tracking
```

## Error Handling & Fallbacks

### Frontend Error Handling
```
File Upload Errors:
├── Invalid file type → User notification
├── File too large → User notification
└── Upload failure → Retry option

Analysis Errors:
├── API timeout → Retry button
├── Invalid response → Fallback message
└── Network error → Error notification

Payment Errors:
├── Session creation failure → Alert message
├── Stripe redirect failure → Manual retry
└── Session restoration failure → Basic payment token fallback
```

### Backend Error Handling
```
File Processing:
├── Unsupported format → HTTP 400
├── Extraction failure → HTTP 500
└── File corruption → HTTP 422

AI Analysis:
├── OpenAI API failure → Fallback response
├── JSON parsing error → Retry with cleaned response
└── Rate limiting → Exponential backoff

Payment Processing:
├── Session creation failure → HTTP 500
├── Invalid session data → HTTP 400
└── Session not found → HTTP 404
```

## Security Considerations

### Data Protection
```
Session Storage:
├── In-memory storage (development)
├── 1-hour expiration
├── No persistent storage of sensitive data
└── Session cleanup on expiration

File Handling:
├── File type validation
├── Size limits
├── Temporary processing only
└── No persistent file storage

Payment Security:
├── Stripe handles payment data
├── No credit card data storage
├── Session-based tracking only
└── HTTPS in production
```

## Development vs Production

### Development Setup
```
Legacy Frontend: http://localhost:3000 (Python HTTP server - OLD VERSION)
New Backend:     http://localhost:8000 (Uvicorn - CURRENT VERSION)
Database:        In-memory session storage
Stripe:          Test mode with test keys
```

### Production Configuration
```
Legacy Frontend: https://resume.idpetech.com (OLD VERSION)
New Backend:     https://q752325o84.execute-api.us-east-1.amazonaws.com/Prod (CURRENT)
Database:        Redis or persistent storage (recommended)
Stripe:          Live mode with production keys
```

This flow diagram shows the complete architecture and data flow of the Resume Health Checker application, from initial file upload through payment processing to premium analysis display.
