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

## Next Sprint Planning

### Tonight's Work: Session Security Fix
- Replace static payment token with unique session IDs
- Maintain existing user experience
- Quick implementation for immediate security improvement

### Future Architecture: Multi-Service Platform
- User accounts and authentication
- Database persistence for sessions
- Subscription management
- Multiple AI services (resume, cover letter, job search)

---

**Last Updated**: August 25, 2025  
**Current Status**: Production MVP with security fix in progress  
**Team**: 1 Developer + 1 Product Owner  
**Repository**: https://github.com/idpetech/resumehealth-checker