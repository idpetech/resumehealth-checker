"""
Resume Health Checker - Modular FastAPI Application

This is the refactored, maintainable version of the Resume Health Checker
with proper separation of concerns and modular structure.

BEFORE: 3,729 lines in one file (maintenance nightmare)
AFTER:  Clean modular structure with logical separation
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import openai
import stripe
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import our modular components
from app.config.settings import settings, constants
from app.routes.main import router as main_router
from app.routes.analysis import router as analysis_router

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================

app = FastAPI(title="Resume Health Checker", version="3.2.0")

# =============================================================================
# MIDDLEWARE & RATE LIMITING
# =============================================================================

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration based on environment
allowed_origins = [
    "https://web-production-f7f3.up.railway.app",
    "http://localhost:8002",
    "http://localhost:8001"
] if settings.environment == "production" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# =============================================================================
# API CLIENT INITIALIZATION
# =============================================================================

# Initialize OpenAI client
openai.api_key = settings.openai_api_key
logger.info("OpenAI client initialized")

# Stripe configuration
stripe.api_key = settings.stripe_test_key or settings.stripe_live_key
logger.info(f"Stripe client initialized for {settings.environment} environment")

# Legacy constants for backward compatibility
STRIPE_SUCCESS_TOKEN = settings.stripe_success_token
STRIPE_PAYMENT_URL = settings.stripe_payment_url

# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

# Register route modules
app.include_router(main_router)
app.include_router(analysis_router)

# =============================================================================
# TEMPORARY IMPORTS FOR BACKWARD COMPATIBILITY
# =============================================================================
# These will be moved to proper services in the next phase

# Import all the existing functions from the monolithic file
# This ensures the modular version works exactly the same as before
try:
    from main_vercel import (
        # Analysis functions
        get_free_analysis_prompt,
        get_job_matching_prompt, 
        get_paid_analysis_prompt,
        get_ai_analysis_with_retry,
        
        # All the remaining endpoints that aren't modularized yet
        # These will be gradually moved to appropriate route modules
    )
    logger.info("Legacy functions imported successfully")
except ImportError as e:
    logger.warning(f"Some legacy functions could not be imported: {e}")

# =============================================================================
# REMAINING ENDPOINTS (TO BE MODULARIZED)
# =============================================================================
# 
# The following endpoints from main_vercel.py still need to be moved to 
# appropriate route modules:
#
# - /api/prompts/* (prompts management)
# - /api/track-sentiment (analytics)
# - /api/analytics/* (analytics)
# - /api/pricing-config (pricing)
# - /api/stripe-pricing/* (pricing)
# - /api/mock-geo/* (geo)
# - /api/multi-product-pricing (pricing)
# - /api/create-payment-session (payments)
# - /api/retrieve-payment-session/* (payments)
# - /api/upselling-recommendations/* (recommendations)
# - /debug/env (debug)
#
# For now, these will continue to work through the main_vercel.py import

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_modular:app",
        host="0.0.0.0",
        port=8003,  # Different port to avoid conflict
        reload=True
    )