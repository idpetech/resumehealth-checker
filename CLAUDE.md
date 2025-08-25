# CLAUDE.md - Resume Health Checker

This file provides guidance to Claude Code, Warp AI, and Cursor when working with the Resume Health Checker codebase.

## Project Overview

**Resume Health Checker** - AI-powered resume analysis platform with freemium business model.
- **Free Tier**: Basic analysis with 3 major issues identified
- **Premium Tier**: $10 comprehensive analysis with text rewrites and bullet improvements
- **Status**: Production-ready MVP deployed on Railway
- **URL**: https://web-production-f7f3.up.railway.app/

## Current Architecture

### Technology Stack
- **Backend**: FastAPI (Python 3.9.18) - Monolithic application
- **AI Processing**: OpenAI GPT-4o-mini for resume analysis
- **Deployment**: Railway Platform (auto-deploy from GitHub)
- **Payments**: Stripe Payment Links (configured in dashboard)
- **File Processing**: PyMuPDF (PDF) + python-docx (Word) - in-memory processing
- **Frontend**: Single-page application (embedded HTML/CSS/JavaScript)

### Key Files
- `main_vercel.py` - Main FastAPI application (monolithic)
- `requirements-deploy.txt` - Python dependencies for Railway
- `railway.json` - Railway deployment configuration  
- `SPRINT_ARTIFACTS.md` - Previous sprint documentation

### Environment Variables (Required)
```bash
OPENAI_API_KEY=sk-...                           # OpenAI API access
STRIPE_PAYMENT_URL=https://buy.stripe.com/...   # Stripe Payment Link
STRIPE_PAYMENT_SUCCESS_TOKEN=payment_success_123 # Static success token
```

### Deployment Commands
```bash
# Local Development
source .venv/bin/activate
uvicorn main_vercel:app --host 0.0.0.0 --port 8001 --reload

# Deploy to Production
git add . && git commit -m "Description" && git push
# Railway auto-deploys from main branch
```

## Current Implementation Status

### ✅ Working Features
- **File Upload**: PDF/DOCX drag-and-drop with validation
- **Free Analysis**: Score (1-100) + 3 major issues + teaser message
- **Premium Analysis**: 4 detailed categories + text rewrites + bullet improvements
- **Payment Flow**: Stripe integration with file persistence via localStorage
- **Reset Functionality**: "Analyze Another Resume" button for multiple analyses
- **Cross-Browser Support**: Chrome, Safari, Firefox, Mobile

### 🚨 Known Security Issue
**Critical**: Static payment token allows premium access without payment
- Anyone can access: `/?payment_token=payment_success_123` for free premium
- **Fix Planned**: Enhanced localStorage with unique session IDs (Tonight's work)

## Business Context

### Current State
- **Phase**: Pre-launch MVP (not advertised yet)
- **Pricing**: $10 one-time premium analysis
- **Priority**: Speed to market + user feedback validation

### Planned Features (Next Sprints)
1. **Cover Letter Generation** based on resume + job requirements
2. **Job Profile Suggestions** based on resume analysis  
3. **Job Search Integration** with resume matching
4. **Subscription Model** alongside pay-per-use

### Success Metrics
- Conversion rate: Free → Paid analysis
- User behavior: Resume issue priorities
- Technical performance: OpenAI costs, processing speed
- Market validation: Geographic distribution, user segments

## Development Guidelines

### Code Standards
- **Security First**: Never expose API keys, validate all inputs
- **Error Handling**: Comprehensive try-catch with user-friendly messages
- **Performance**: Optimize OpenAI calls (temp 0.7, max_tokens 1500)
- **User Experience**: Single-page app with immediate feedback

### Testing Approach
- **Local Testing**: http://localhost:8001 with test files
- **Production Testing**: Railway deployment with real Stripe integration
- **Browser Testing**: Chrome, Safari, Firefox, Mobile Safari

### Payment Integration Rules
- **Free Analysis**: No payment token required
- **Premium Analysis**: Requires valid payment token
- **File Persistence**: localStorage across payment redirect
- **Stripe Configuration**: Success URL configured in Stripe dashboard (not code)

## Current Session Management Issue

### Problem Description
```javascript
// Current implementation - SECURITY FLAW
const paymentToken = 'payment_success_123'; // Static for all users!
```

### Immediate Fix Plan (Tonight)
Replace with unique session-based approach:
```javascript
// Proposed fix
const sessionId = crypto.randomUUID();
const paymentUrl = `${stripeUrl}?client_reference_id=${sessionId}`;
localStorage.setItem(`resume_${sessionId}`, fileData);
```

## AI Analysis Prompts

### Free Analysis Prompt Structure
- Focus on 3 major weaknesses preventing interviews
- Include overall score (1-100)
- Add compelling teaser for premium upgrade
- Response format: JSON with specific structure

### Premium Analysis Prompt Structure  
- Comprehensive breakdown: ATS optimization, content clarity, impact metrics, formatting
- Include actual text rewrites with before/after examples
- Provide prioritized action plan
- Enhanced JSON structure with detailed improvements

## Common Commands

### Development Workflow
```bash
# Start local development
source .venv/bin/activate
uvicorn main_vercel:app --host 0.0.0.0 --port 8001 --reload

# Test file processing
curl -X POST http://localhost:8001/api/check-resume \
  -F "file=@test-resume.pdf"

# Deploy to production
git add . && git commit -m "Description" && git push
```

### Debugging
- **Frontend**: Browser console (F12) for JavaScript errors
- **Backend**: Server logs show OpenAI API calls and file processing
- **Payment Flow**: Check localStorage for file persistence

## Important Notes for AI Assistants

### Context Preservation
- This is a PRODUCTION application with REAL customers and payments
- Any changes must maintain backward compatibility
- Test thoroughly before deploying (users are paying $10)

### Priority Order
1. **User Experience** - Payment flow must work flawlessly
2. **Security** - Prevent unauthorized premium access
3. **Performance** - Fast analysis delivery
4. **Feature Development** - New capabilities

### Do NOT Break
- Existing payment flow (customers mid-purchase)
- File upload functionality (core feature)
- OpenAI API integration (business logic)
- Railway deployment process (production system)

### Common Pitfalls
- Don't change Stripe Payment Link URL (configured in dashboard)
- Don't modify environment variable names (Railway deployment)
- Don't break localStorage file persistence (payment flow)
- Don't change API endpoint paths (frontend dependencies)

## Tonight's Session Security Fix - CRITICAL

### The Exact Problem
```javascript
// Current code in main_vercel.py line ~547
const paymentToken = urlParams.get('payment_token'); // Gets 'payment_success_123'

// SECURITY FLAW: Static token means anyone can access premium for free by visiting:
// https://web-production-f7f3.up.railway.app/?payment_token=payment_success_123
```

### Solution Architecture Agreed Upon
**Enhanced localStorage with Unique Session IDs** - balances speed-to-market with security

### Implementation Steps
1. **Generate unique session ID on file upload**
   ```javascript
   const sessionId = crypto.randomUUID(); // Browser native API
   ```

2. **Include session ID in Stripe Payment URL**
   ```javascript
   const paymentUrl = `${stripeUrl}?client_reference_id=${sessionId}`;
   ```

3. **Store file with session validation**
   ```javascript
   localStorage.setItem(`resume_${sessionId}`, fileData);
   ```

4. **Validate session on return from Stripe**
   ```javascript
   const sessionId = urlParams.get('client_reference_id');
   const storedFile = localStorage.getItem(`resume_${sessionId}`);
   ```

### Key Files to Modify
- **`main_vercel.py`** lines 879-901 (goToStripeCheckout function)
- **`main_vercel.py`** lines 545-571 (payment return detection)
- **Environment**: Update Stripe Payment Link to use `client_reference_id` parameter

### Testing Checklist
- [ ] Upload file → generates unique session ID
- [ ] Payment flow → includes session ID in URL  
- [ ] Return from Stripe → validates correct session
- [ ] Multiple users → each gets unique sessions
- [ ] Static token URL → no longer works for premium access

### Deployment Process
```bash
# Test locally first
uvicorn main_vercel:app --host 0.0.0.0 --port 8001 --reload

# Deploy to production
git add main_vercel.py && git commit -m "Fix: Implement unique session-based payment validation" && git push
```

### Current Stripe Configuration
- **Payment Link**: `https://buy.stripe.com/eVqaEWfOk37Mf9ncPWfMA00`
- **Success URL**: `https://web-production-f7f3.up.railway.app/?payment_token=payment_success_123`
- **Needs Update**: Change to use `client_reference_id` parameter

### Risk Mitigation
- **User Experience**: Keep existing flow, just add session validation
- **Backward Compatibility**: Old payment token still works during transition
- **Error Handling**: Graceful degradation if session validation fails
- **Testing**: Test with real Stripe payments before full deployment

## Previous Context - Essential for New Session

### What Just Happened (Last Session Summary)
1. **Completed**: Full payment flow integration with Stripe Payment Links
2. **Fixed**: Upload functionality breaking after payment completion  
3. **Added**: "Analyze Another Resume" reset functionality
4. **Identified**: Critical security flaw - static payment token allows free premium access
5. **Decided**: Enhanced localStorage approach for immediate fix (vs full database solution)
6. **Status**: Production system working but vulnerable - needs tonight's security fix

### User Requirements Confirmed
- **Speed to Market**: Critical priority over perfect security
- **Future Features**: Cover letter generation, job search, subscription model
- **Business Model**: $10 premium analysis + planned subscription tiers
- **Launch Timeline**: Delayed slightly for security fix, then immediate launch

### Technical Decisions Made
- **Architecture**: Keep stateless FastAPI monolith for now
- **Payment**: Continue with Stripe Payment Links (easier than Checkout Sessions)
- **Storage**: Enhanced localStorage (not database) for immediate fix
- **Migration Path**: Proper session management in Sprint 2 with user accounts

## Next Sprint Planning

### Sprint 2: Proper Session Management + User Accounts
- Database persistence for user sessions
- Stripe Checkout Sessions for proper payment verification
- User registration/login system
- Analysis history and saved resumes

### Sprint 3+: Feature Expansion
- Cover Letter Generation based on resume + job requirements  
- Job Profile Suggestions based on resume analysis
- Job Search Integration with resume matching
- Subscription Model alongside pay-per-use

### Future Architecture: Multi-Service Platform
- User accounts and authentication
- Database persistence for sessions  
- Subscription management
- Multiple AI services (resume, cover letter, job search)

---

**Last Updated**: August 25, 2025 - End of Sprint 1  
**Current Status**: Production MVP - SECURITY FIX IN PROGRESS TONIGHT  
**Critical**: Static payment token `payment_success_123` allows free premium access  
**Tonight's Goal**: Implement unique session IDs for payment validation  
**Team**: 1 Developer + 1 Product Owner  
**Repository**: https://github.com/idpetech/resumehealth-checker