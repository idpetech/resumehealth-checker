"""
API Routes for Resume Health Checker v4.0

Modular router that combines all specialized route modules:
- Analysis routes: Resume analysis, job fit, cover letters, rewrites
- Payment routes: Stripe integration, payment flows, webhooks  
- Export routes: PDF and DOCX generation
- Admin routes: Health checks, debug endpoints, statistics
- Template routes: Premium results HTML generation
"""
import logging
from fastapi import APIRouter

# Import modular route modules
from .analysis import router as analysis_router
from .payments import router as payments_router  
from .exports import router as exports_router
from .admin import router as admin_router
from .templates import router as templates_router

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Register all modular routers with appropriate prefixes
router.include_router(
    analysis_router, 
    tags=["Analysis"],
    responses={404: {"description": "Not found"}}
)

router.include_router(
    payments_router, 
    tags=["Payments"],
    responses={404: {"description": "Not found"}}
)

router.include_router(
    exports_router, 
    tags=["Exports"],
    responses={404: {"description": "Not found"}}
)

router.include_router(
    admin_router, 
    tags=["Admin"],
    responses={404: {"description": "Not found"}}
)

router.include_router(
    templates_router, 
    tags=["Templates"],
    responses={404: {"description": "Not found"}}
)

logger.info("🏗️ Modular routes loaded successfully")
logger.info("✅ Analysis routes: /analyze, /premium/{id}, /rewrite-preview, /generate-*")
logger.info("✅ Payment routes: /payment/*, /webhooks/stripe")
logger.info("✅ Export routes: /export/{id}/pdf, /export/{id}/docx")
logger.info("✅ Admin routes: /health, /debug/*, /admin/*")  
logger.info("✅ Template routes: /premium-results/{id}")