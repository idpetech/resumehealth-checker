"""
Admin Routes for Resume Health Checker v4.0

Development and administration endpoints including debug information,
statistics, and test utilities.
"""
import logging
import datetime
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse

from ..core.database import AnalysisDB, get_database_stats
from ..services.payments import get_payment_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        from ..core.config import config
        
        return {
            "status": "healthy",
            "service": "Resume Health Checker v4.0",
            "environment": config.environment,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "version": "4.0.0"
        }
    except Exception as e:
        # Fallback health check if config fails
        return {
            "status": "healthy",
            "service": "Resume Health Checker v4.0",
            "environment": "unknown",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "version": "4.0.0",
            "note": "Basic health check - config may not be fully loaded"
        }

@router.get("/debug/payment")
async def debug_payment_service():
    """Debug endpoint to check PaymentService status"""
    from ..core.config import config
    payment_service = get_payment_service()
    
    return {
        "environment": config.environment,
        "stripe_secret_key_prefix": config.stripe_secret_key[:10] + "..." if config.stripe_secret_key else "None",
        "stripe_secret_key_length": len(config.stripe_secret_key) if config.stripe_secret_key else 0,
        "stripe_available": payment_service.stripe_available,
        "use_stripe_test_keys": config.use_stripe_test_keys
    }

@router.get("/admin/stats")
async def get_admin_stats():
    """Get database statistics (development/admin only)"""
    from ..core.config import config
    
    if config.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    try:
        stats = get_database_stats()
        recent_analyses = AnalysisDB.get_recent(10)
        
        return {
            "database_stats": stats,
            "recent_analyses": recent_analyses,
            "environment": config.environment
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "stats_error", "message": "Could not retrieve stats"}
        )

@router.post("/admin/test-payment")
async def test_payment_flow(
    analysis_id: str = Form(...),
    test_scenario: str = Form("success")
):
    """Test payment flow with various scenarios (development only)"""
    from ..core.config import config
    
    if config.environment == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    # Test payment scenarios for development
    test_responses = {
        "success": {"status": "success", "message": "Test payment completed"},
        "failure": {"status": "failure", "message": "Test payment failed"},
        "pending": {"status": "pending", "message": "Test payment pending"}
    }
    
    return test_responses.get(test_scenario, test_responses["success"])

@router.get("/pricing/{country_code}")
async def get_regional_pricing(country_code: str):
    """Get pricing for specific country/region"""
    try:
        from ..services.geo import geo_service
        pricing = geo_service.get_pricing_for_region(country_code.upper())
        return {
            "country_code": country_code.upper(),
            "pricing": pricing
        }
    except Exception as e:
        logger.error(f"Pricing lookup error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "pricing_error", "message": "Could not retrieve pricing"}
        )

@router.get("/detect-region")
async def detect_user_region(request: Request):
    """Detect user's region from IP"""
    try:
        from ..services.geo import geo_service
        region_info = geo_service.detect_region_from_request(request)
        return region_info
    except Exception as e:
        logger.error(f"Region detection error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "geo_error", "message": "Could not detect region"}
        )