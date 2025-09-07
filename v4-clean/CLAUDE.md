# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Resume Health Checker v4.0 is a clean, modular FastAPI application that provides AI-powered resume analysis with premium upgrade options. This is a complete rewrite from a previous 3,800-line monolithic version, now architected as a maintainable service with proper separation of concerns.

**Key Features:**
- AI-powered resume analysis (free and premium tiers)
- Multi-format file processing (PDF, DOCX, TXT)
- Stripe payment integration with regional pricing
- Six supported currencies with geolocation detection
- Multiple premium services (job fit analysis, cover letters, interview prep)

## Architecture

### Clean Modular Structure
```
main.py                 # Single entry point with environment detection
app/
├── core/              # Core infrastructure
│   ├── config.py      # Multi-environment configuration
│   ├── database.py    # SQLite database abstraction
│   └── exceptions.py  # Custom exception handling
├── services/          # Business logic services
│   ├── analysis.py    # OpenAI integration and AI analysis
│   ├── files.py       # File processing (PDF/DOCX/TXT)
│   ├── payments.py    # Stripe payment integration
│   └── geo.py         # Regional pricing and geolocation
├── api/
│   └── routes.py      # All API endpoints in organized structure
├── data/              # Configuration files
│   ├── prompts.json   # AI prompts (externalized)
│   ├── pricing.json   # Regional pricing configuration
│   └── geo.json       # Geographic region mappings
└── static/            # Frontend assets (if needed)
```

### Environment-Based Configuration
- **Local**: Development with hot reload, debug logging, test Stripe keys
- **Staging**: Railway staging deployment with test environment
- **Production**: Railway production with live Stripe keys, optimized logging

## Common Development Commands

### Local Development
```bash
# Start development server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run comprehensive test suite
python test_local.py

# Test specific configuration
python test_config.py
```

### Testing Strategy
The project follows a comprehensive testing approach from local → staging → production:

1. **Local Testing**: `python test_local.py` - Tests all endpoints with real resume files
2. **Stripe Sandbox**: Full payment flow testing with test cards
3. **Railway Staging**: Production-like environment testing
4. **Production Deployment**: Only after all tests pass

### Environment Variables Required

**Core Settings:**
```bash
ENVIRONMENT=local|staging|production
DEBUG=true|false
PORT=8000
OPENAI_API_KEY=sk-your-openai-key
```

**Stripe Integration:**
```bash
# For local/staging (test keys)
STRIPE_SECRET_TEST_KEY=sk_test_...
STRIPE_PUBLISHABLE_TEST_KEY=pk_test_...
STRIPE_WEBHOOK_TEST_SECRET=whsec_...

# For production (live keys)
STRIPE_SECRET_LIVE_KEY=sk_live_...
STRIPE_PUBLISHABLE_LIVE_KEY=pk_live_...
STRIPE_WEBHOOK_LIVE_SECRET=whsec_...
```

**Railway Deployment:**
```bash
RAILWAY_PRODUCTION_URL=https://your-app.railway.app
DATABASE_PATH=database.db
```

## Development Patterns

### Service Layer Architecture
- **analysis_service**: Singleton for OpenAI integration and AI prompts
- **file_service**: File processing with automatic format detection
- **payment_service**: Stripe integration with environment-aware key selection
- **geo_service**: Regional pricing and currency detection

### Database Design
Simple SQLite with analysis tracking:
- Stores resume analysis results (free/premium)
- Payment status tracking
- Session management for payment flow
- No user accounts (stateless design for v4.0)

### Error Handling
Custom exceptions with structured responses:
- `FileProcessingError`: File upload and processing issues
- `AIAnalysisError`: OpenAI API and analysis failures  
- `PaymentError`: Stripe integration problems
- Global exception handlers provide consistent JSON error responses

### API Design Principles
- RESTful endpoints under `/api/v1/`
- File uploads via multipart form data
- Consistent JSON response format
- Environment-specific features (admin endpoints only in dev)

## AI Integration

### OpenAI Configuration
- Model: `gpt-4o-mini` for cost efficiency
- Temperature: `0.7` for balanced creativity/consistency
- Max tokens: `1500` per analysis
- Timeout: `60 seconds` per request

### Prompt Management
AI prompts are externalized in `app/data/prompts.json`:
- **Free Analysis**: Basic resume feedback with upgrade prompts
- **Premium Analysis**: Comprehensive analysis with text rewrites
- **Job Fit Analysis**: Resume-to-job-posting matching
- **Cover Letter**: Tailored cover letter generation

### Response Processing
- JSON response parsing with markdown cleanup
- Fallback handling for malformed AI responses
- Structured error responses when AI calls fail

## Payment Integration

### Stripe Architecture
- Environment-aware key selection (test vs live)
- Regional pricing with 6 supported currencies (USD, PKR, INR, HKD, AED, BDT)
- Session-based payment flow with unique client reference IDs
- Webhook handling for payment verification

### Payment Flow
1. User uploads resume → gets free analysis
2. Premium upgrade creates Stripe payment session
3. Successful payment triggers premium analysis generation
4. Results delivered via success URL with analysis display

## Regional Pricing System

### Supported Regions
- 🇺🇸 United States (USD)
- 🇵🇰 Pakistan (PKR) 
- 🇮🇳 India (INR)
- 🇭🇰 Hong Kong (HKD)
- 🇦🇪 UAE (AED)
- 🇧🇩 Bangladesh (BDT)

### Currency Detection
- Automatic geolocation via IP detection
- Manual region override for testing
- Fallback pricing configuration in JSON

## Testing and Deployment

### Local Testing Requirements
- Real resume files for testing (ResumeLAW.docx reference)
- Valid OpenAI API key for AI analysis
- Stripe test keys for payment flow testing
- All tests must pass before deployment

### Railway Deployment
- Auto-deployment from main branch
- Environment variables set via Railway dashboard
- Health check endpoint at `/health`
- Logging optimized per environment

### Production Checklist
- ✅ All local tests passing (6/6)
- ✅ Stripe sandbox testing complete
- ✅ Railway staging validated
- ✅ Environment variables configured
- ✅ Webhook endpoints configured in Stripe dashboard

## Security Considerations

### API Security
- No hardcoded secrets (all via environment variables)
- Request validation and sanitization
- File upload size and type restrictions (10MB max, PDF/DOCX/TXT only)
- Stripe webhook signature verification

### Data Handling
- In-memory file processing (no persistent file storage)
- Session-based payment tracking
- SQLite database for analysis results
- No user account system (stateless by design)

## Key Implementation Notes

### File Processing
- PyMuPDF for PDF text extraction
- python-docx for Word document processing
- Automatic file type detection via content type and extension
- Text validation before AI analysis

### AI Analysis Validation
- Minimum text length requirements
- Resume content structure validation
- Expected section detection (experience, education, skills)
- Response format validation with fallback handling

### Payment Session Management
- UUID-based session tracking
- Client reference ID mapping to analysis records
- Session verification before premium service delivery
- Graceful handling of payment cancellation/failure

This codebase prioritizes maintainability, testing, and production reliability over feature complexity, making it suitable for real-world deployment with paying customers.