#!/usr/bin/env python3
"""
Resume Health Checker v4.0 - Clean Architecture
Single entry point for the application

BEFORE: 3,800-line monolithic nightmare
AFTER:  Clean, maintainable FastAPI service

Key Features:
- Single entry point for all environments
- Built-in static file serving
- Multi-environment configuration
- Railway-optimized deployment
"""
import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Import our clean modular components
from app.core.config import config
from app.core.database import init_db
from app.core.exceptions import add_exception_handlers
from app.api.routes import router

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO if config.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
logger.info(f"🚀 Starting Resume Health Checker v4.0 in {config.environment} mode")

# =============================================================================
# FASTAPI APPLICATION SETUP  
# =============================================================================

app = FastAPI(
    title="Resume Health Checker",
    description="AI-powered resume analysis with premium upgrades",
    version="4.0.0",
    docs_url="/docs" if config.debug else None,  # Hide docs in production
    redoc_url="/redoc" if config.debug else None
)

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

# CORS - Environment specific origins
allowed_origins = {
    "local": ["http://localhost:8000", "http://127.0.0.1:8000"],
    "staging": [config.base_url, "https://staging-resume-checker.up.railway.app"],
    "production": [config.base_url, "https://resumehealthchecker.com"]
}.get(config.environment, ["http://localhost:8000"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

add_exception_handlers(app)

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database and perform startup tasks"""
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
        logger.info(f"✅ Serving on {config.base_url}")
        logger.info(f"✅ Environment: {config.environment}")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

# =============================================================================
# HEALTH CHECK - Must be defined BEFORE static files
# =============================================================================

@app.get("/health")
async def health_check():
    """Simple health check endpoint for Railway and monitoring"""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "environment": config.environment,
        "timestamp": "2025-09-02T12:00:00Z"
    }

# API routes
app.include_router(router, prefix="/api/v1")

# Static files - serve frontend from /static directory
static_dir = Path(__file__).parent / "app" / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    logger.info(f"✅ Static files mounted from {static_dir}")
else:
    logger.warning(f"⚠️ Static directory not found: {static_dir}")

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Railway provides PORT environment variable
    port = int(os.getenv("PORT", 8000))
    
    # Development vs Production configuration
    if config.environment == "local":
        # Local development with hot reload
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    else:
        # Production mode for Railway
        uvicorn.run(
            app,
            host="0.0.0.0", 
            port=port,
            log_level="warning",
            access_log=False  # Disable access logs in production
        )