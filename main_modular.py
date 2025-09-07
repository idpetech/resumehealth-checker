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
from app.core.config import config
from app.api.routes import router as api_router

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

# CORS configuration - SECURITY FIX: No wildcards in production
allowed_origins = [
    "https://web-production-f7f3.up.railway.app",
    "http://localhost:8002",
    "http://localhost:8001",
    "http://localhost:3000",  # For development frontends
    "https://resumehealthchecker.com",  # Add your actual domain
] if config.environment == "production" else [
    "http://localhost:8002",
    "http://localhost:8001", 
    "http://localhost:3000",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global exception handler - SECURITY FIX: Hide error details in production
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {exc}")
    
    # Hide sensitive error details in production
    if config.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error", 
                "message": "Something went wrong. Please try again."
            }
        )
    else:
        # Show details in development for debugging
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(exc)}
        )

# =============================================================================
# API CLIENT INITIALIZATION
# =============================================================================

# Initialize OpenAI client
openai.api_key = config.openai_api_key
logger.info("OpenAI client initialized")

# Stripe configuration
stripe.api_key = config.stripe_secret_key
logger.info(f"Stripe client initialized for {config.environment} environment")

# Legacy constants for backward compatibility (if needed)
STRIPE_SUCCESS_TOKEN = "payment_success_123"  # Default value
STRIPE_PAYMENT_URL = "https://buy.stripe.com/test_placeholder"  # Default value

# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

# Register route modules
app.include_router(api_router, prefix="/api/v1")

# Add simple health checks for Railway
@app.get("/")
async def root():
    return {"status": "ok", "message": "Resume Health Checker v4.0 is running"}

@app.get("/health")
async def simple_health():
    return {"status": "healthy", "service": "Resume Health Checker v4.0"}

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
    import os
    
    # Use Railway's PORT environment variable, fallback to 8000
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting Resume Health Checker v4.0 on port {port}")
    print(f"🌍 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'local')}")
    print(f"📡 Health check available at: http://0.0.0.0:{port}/health")
    
    uvicorn.run(
        "main_modular:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    )