"""
Payment Routes Module

This module handles payment session creation and Stripe integration.
For now, these are temporary imports from the monolithic file.
"""
import logging
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config.settings import constants

logger = logging.getLogger(__name__)

# Initialize router and limiter
router = APIRouter(prefix="/api")
limiter = Limiter(key_func=get_remote_address)

# Import functions from main_vercel.py temporarily
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from main_vercel import (
        stripe,
        get_stripe_pricing_from_api,
        get_multi_product_pricing,
        get_pricing_config,
        session_data_store,
    )
except ImportError as e:
    logger.error(f"Could not import payment functions: {e}")

@router.post("/create-payment-session")
@limiter.limit(constants.ANALYSIS_RATE_LIMIT)
async def create_payment_session(
    request: Request,
    product_type: str = Form(...),  # "individual" or "bundle"
    product_id: str = Form(...),    # product name or bundle name
    session_data: str = Form(...)   # JSON string with user's analysis data
):
    """Create a payment session with product selection and user data"""
    
    try:
        # Import the actual function from main_vercel
        from main_vercel import create_payment_session as original_create_payment_session
        
        # Call the original function with the same parameters
        # Note: We need to handle the request parameter difference
        result = await original_create_payment_session(product_type, product_id, session_data)
        return result
        
    except Exception as e:
        logger.error(f"Payment session creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Payment session creation failed: {str(e)}")

@router.get("/retrieve-payment-session/{session_id}")
async def retrieve_payment_session(session_id: str):
    """Retrieve stored session data after successful payment"""
    
    try:
        from main_vercel import retrieve_payment_session as original_retrieve_payment_session
        result = await original_retrieve_payment_session(session_id)
        return result
        
    except Exception as e:
        logger.error(f"Payment session retrieval error: {e}")
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@router.get("/stripe-pricing/{country_code}")
async def get_stripe_pricing(country_code: str):
    """Fetch regional pricing from Stripe as single source of truth"""
    
    try:
        from main_vercel import get_stripe_pricing as original_get_stripe_pricing
        result = await original_get_stripe_pricing(country_code)
        return result
        
    except Exception as e:
        logger.error(f"Stripe pricing error: {e}")
        raise HTTPException(status_code=500, detail=f"Pricing fetch failed: {str(e)}")

@router.get("/multi-product-pricing")
async def multi_product_pricing():
    """Get comprehensive pricing for all products and bundles"""
    
    try:
        from main_vercel import multi_product_pricing as original_multi_product_pricing
        result = await original_multi_product_pricing()
        return result
        
    except Exception as e:
        logger.error(f"Multi-product pricing error: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-product pricing failed: {str(e)}")

@router.get("/pricing-config")
async def pricing_config():
    """Get pricing configuration for different countries"""
    
    try:
        from main_vercel import pricing_config as original_pricing_config
        result = await original_pricing_config()
        return result
        
    except Exception as e:
        logger.error(f"Pricing config error: {e}")
        raise HTTPException(status_code=500, detail=f"Pricing config failed: {str(e)}")