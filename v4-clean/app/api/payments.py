"""
Payment Routes for Resume Health Checker v4.0

All payment-related endpoints including Stripe payment sessions, webhooks,
payment success/cancel handlers, and mock payment flows.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from ..core.database import AnalysisDB
from ..core.exceptions import PaymentError
from ..services.payments import get_payment_service
from ..services.geo import geo_service
from ..services.analysis import analysis_service
from ..services.premium_generation import premium_generation_service, AccessContext, AccessType

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

@router.post("/payment/create")
async def create_payment_session(
    request: Request,
    analysis_id: str = Form(...),
    product_type: str = Form(...),
    price: Optional[str] = Form(None),
    region_override: Optional[str] = Form(None),
    job_posting: Optional[str] = Form(None)
):
    """
    Create Stripe payment session
    
    - analysis_id: ID of analysis to upgrade
    - product_type: "resume_analysis", "job_fit_analysis", "cover_letter"
    - region_override: Optional region code for testing
    - job_posting: Optional job posting text for job-specific products
    """
    logger.info(f"Payment session creation: {analysis_id}, {product_type}, price={price}")
    logger.debug(f"Received price parameter: '{price}' (type: {type(price)})")
    
    try:
        # Verify analysis exists
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Store job posting if provided
        if job_posting and job_posting.strip():
            AnalysisDB.update_job_posting(analysis_id, job_posting.strip())
            logger.info(f"Stored job posting for analysis {analysis_id}")
        
        # Detect region and pricing
        if region_override:
            country = region_override.upper()
            logger.info(f"Using region override: {country}")
        else:
            region_info = geo_service.detect_region_from_request(request)
            country = region_info["country_code"]
        
        # Get pricing for region
        pricing = geo_service.get_pricing_for_region(country)
        product_info = pricing.get("products", {}).get(product_type)
        
        if not product_info:
            raise HTTPException(status_code=400, detail=f"Invalid product type: {product_type}")
        
        # Get Stripe-compatible amount and currency
        currency = geo_service.get_currency_for_stripe(country)
        
        # Use frontend price if provided, otherwise fall back to geo service pricing
        if price is not None and price.strip():
            try:
                price_float = float(price)
                amount = int(price_float * 100)  # Convert dollars to cents
                logger.info(f"Using frontend price: ${price_float} = {amount} cents")
            except ValueError:
                logger.warning(f"Invalid price format: {price}, falling back to geo service")
                amount = geo_service.convert_amount_for_stripe(country, product_type)
                logger.info(f"Using geo service price: {amount} cents")
        else:
            amount = geo_service.convert_amount_for_stripe(country, product_type)
            logger.info(f"Using geo service price: {amount} cents")
        
        product_name = product_info.get("name", product_type.replace('_', ' ').title())
        
        # Create payment session
        logger.info(f"About to create payment session with: analysis_id={analysis_id}, amount={amount}, currency={currency}")
        payment_service = get_payment_service()
        logger.info(f"Payment service obtained: {payment_service}")
        session_data = await payment_service.create_payment_session(
            analysis_id=analysis_id,
            product_type=product_type,
            amount=amount,
            currency=currency,
            product_name=product_name
        )
        logger.info(f"Payment session created: {session_data}")
        
        return {
            "payment_session": session_data,
            "pricing_info": {
                "country": country,
                "currency": currency.upper(),
                "amount_display": product_info.get("display"),
                "product_name": product_name
            }
        }
        
    except PaymentError as e:
        logger.error(f"Payment error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "payment_error", "message": str(e)}
        )
    
    except Exception as e:
        import traceback
        logger.error(f"Unexpected payment error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": f"Payment session creation failed: {str(e)}"}
        )

@router.get("/payment/success")
async def payment_success(
    request: Request,
    session_id: str,
    analysis_id: str,
    product_type: str
):
    """
    Handle successful payment return from Stripe
    """
    logger.info(f"Payment success: session {session_id}, analysis {analysis_id}")
    
    try:
        # Verify payment with Stripe
        verification = await get_payment_service().verify_payment_session(session_id)
        
        if verification['payment_status'] != 'paid':
            logger.warning(f"Payment not completed: {verification['payment_status']}")
            return HTMLResponse(
                content=f"<h1>Payment Not Completed</h1><p>Payment status: {verification['payment_status']}</p>",
                status_code=400
            )
        
        # Get analysis
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            return HTMLResponse(content="<h1>Analysis Not Found</h1>", status_code=404)
        
        # Mark as paid and trigger premium analysis if needed
        amount_paid = verification['amount_total']
        currency = verification['currency'].upper()
        AnalysisDB.mark_as_paid(analysis_id, amount_paid, currency)
        
        # If no premium result exists, trigger async generation (don't wait)
        if not analysis.get('premium_result'):
            try:
                logger.info(f"Triggering async premium {product_type} generation for {analysis_id}")
                
                # Create access context for payment
                access_context = AccessContext(
                    access_type=AccessType.PAYMENT,
                    payment_id=session_id,
                    metadata={
                        "amount_paid": amount_paid,
                        "currency": currency,
                        "payment_method": "stripe"
                    }
                )
                
                # Start async premium generation (don't await - let it run in background)
                import asyncio
                asyncio.create_task(
                    premium_generation_service.generate_premium_results(
                        analysis_id=analysis_id,
                        product_type=product_type,
                        access_context=access_context
                    )
                )
                
                logger.info(f"Async premium {product_type} generation started for {analysis_id}")
                
            except Exception as e:
                logger.error(f"Failed to start async premium generation for {analysis_id}: {e}")
                # Don't block the success page for this error
        
        # Return success page using template
        return templates.TemplateResponse("payment_success.html", {
            "request": request,
            "analysis_id": analysis_id,
            "product_type": product_type
        })
        
    except Exception as e:
        logger.error(f"Payment success handler error: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Payment verification failed: {str(e)}</p>",
            status_code=500
        )

@router.get("/payment/cancel")
async def payment_cancel(request: Request, analysis_id: str, product_type: str):
    """Handle payment cancellation"""
    logger.info(f"Payment cancelled: analysis {analysis_id}, product {product_type}")
    
    return templates.TemplateResponse("payment_cancel.html", {
        "request": request,
        "analysis_id": analysis_id,
        "product_type": product_type
    })

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks securely"""
    try:
        payload = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe signature")
        
        result = await get_payment_service().handle_webhook_event(payload, signature)
        return result
        
    except PaymentError as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/payment/mock")
async def mock_payment_page(
    request: Request,
    session_id: str,
    analysis_id: str,
    product_type: str
):
    """Mock payment page for testing when Stripe is not configured"""
    from ..core.config import config
    
    return templates.TemplateResponse("mock_payment.html", {
        "request": request,
        "session_id": session_id,
        "analysis_id": analysis_id,
        "product_type": product_type,
        "environment": config.environment
    })

@router.post("/payment/complete")
async def complete_payment(request: Request):
    """Mark payment as completed (for mock payments using Stripe sandbox)"""
    try:
        data = await request.json()
        analysis_id = data.get('analysis_id')
        product_type = data.get('product_type')
        session_id = data.get('session_id')
        
        if not analysis_id:
            raise HTTPException(status_code=400, detail="Analysis ID required")
        
        # Get analysis to check if premium result already exists
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Mark analysis as paid (mock payment with configurable amount)
        from ..core.config import config
        mock_amount = getattr(config, 'mock_payment_amount', 1000)  # Default 1000 cents if not configured
        mock_currency = getattr(config, 'mock_payment_currency', 'usd')
        AnalysisDB.mark_as_paid(analysis_id, mock_amount, mock_currency)
        
        # If no premium result exists, trigger async generation (don't wait)
        if not analysis.get('premium_result'):
            try:
                logger.info(f"Triggering async premium {product_type} generation for {analysis_id} (mock payment)")
                
                # Create access context for mock payment
                access_context = AccessContext(
                    access_type=AccessType.PAYMENT,
                    payment_id=session_id or f"mock_{analysis_id}",
                    metadata={
                        "amount_paid": mock_amount,
                        "currency": mock_currency,
                        "payment_method": "stripe_sandbox",
                        "is_mock": True
                    }
                )
                
                # Start async premium generation (don't await - let it run in background)
                import asyncio
                asyncio.create_task(
                    premium_generation_service.generate_premium_results(
                        analysis_id=analysis_id,
                        product_type=product_type,
                        access_context=access_context
                    )
                )
                
                logger.info(f"Async premium {product_type} generation started for {analysis_id} (mock payment)")
                
            except Exception as e:
                logger.error(f"Failed to start async premium generation for {analysis_id}: {e}")
                # Don't block the success response for this error
        
        logger.info(f"Mock payment completed for analysis {analysis_id}, product {product_type}")
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "product_type": product_type,
            "message": "Payment completed successfully",
            "premium_result": analysis.get('premium_result') is not None
        }
        
    except Exception as e:
        logger.error(f"Payment completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "payment_completion_error", "message": str(e)}
        )

# Alternate payment success handler for different URL patterns
@router.get("/payment/success")
async def payment_success_alternate(
    session_id: str,
    analysis_id: str,
    product_type: str
):
    """Payment success page (for real Stripe integration)"""
    # This would handle real Stripe success redirects
    return JSONResponse(content={
        "status": "success",
        "message": "Payment completed successfully",
        "session_id": session_id,
        "analysis_id": analysis_id,
        "product_type": product_type
    })

# Alternate payment cancel handler for different URL patterns  
@router.get("/payment/cancel")
async def payment_cancel_alternate(
    analysis_id: str,
    product_type: str
):
    """Payment cancel page (for real Stripe integration)"""
    # This would handle real Stripe cancel redirects
    return JSONResponse(content={
        "status": "cancelled",
        "message": "Payment was cancelled",
        "analysis_id": analysis_id,
        "product_type": product_type
    })