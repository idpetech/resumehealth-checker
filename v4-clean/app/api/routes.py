"""o such errors occoured


API Routes for Resume Health Checker v4.0

All endpoints in one clean, organized file with proper error handling.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import uuid

from ..core.database import AnalysisDB, get_database_stats
from ..core.exceptions import FileProcessingError, AIAnalysisError, PaymentError, validate_file_upload
from ..services.files import file_service
from ..services.analysis import analysis_service
from ..services.payments import get_payment_service
from ..services.geo import geo_service
from ..services.promotional import promotional_service

logger = logging.getLogger(__name__)

# Create router and templates
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@router.post("/analyze")
async def analyze_resume(
    request: Request,
    file: UploadFile = File(...),
    analysis_type: str = Form("free"),
    job_posting: Optional[str] = Form(None)
):
    """
    Main endpoint for resume analysis
    
    - file: PDF, DOCX, or TXT resume file
    - analysis_type: "free" or "premium" 
    - job_posting: Optional job description for job fit analysis
    """
    logger.info(f"Resume analysis request: {file.filename}, type: {analysis_type}")
    
    try:
        # Read and validate file
        file_content = await file.read()
        validate_file_upload(file.filename, len(file_content), file.content_type)
        
        # Extract text from file
        resume_text = file_service.extract_text_from_file(
            file_content, file.filename, file.content_type
        )
        
        # Validate resume content
        validation = analysis_service.validate_resume_content(resume_text)
        if not validation["is_valid"]:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_resume_content",
                    "message": "Resume content validation failed",
                    "validation": validation
                }
            )
        
        # Create analysis record
        analysis_id = AnalysisDB.create(
            filename=file.filename,
            file_size=len(file_content),
            resume_text=resume_text,
            analysis_type=analysis_type
        )
        
        # Perform AI analysis
        if job_posting and job_posting.strip():
            # Job fit analysis
            result = await analysis_service.analyze_resume(
                resume_text, analysis_type, job_posting.strip()
            )
        else:
            # Regular resume analysis
            result = await analysis_service.analyze_resume(resume_text, analysis_type)
        
        # Store results
        if analysis_type == "free":
            AnalysisDB.update_free_result(analysis_id, result)
        else:
            AnalysisDB.update_premium_result(analysis_id, result)
        
        # Get region info for pricing context
        region_info = geo_service.detect_region_from_request(request)
        
        return {
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "result": result,
            "validation": validation,
            "region_info": region_info,
            "timestamp": "2025-09-02T13:00:00Z"
        }
        
    except FileProcessingError as e:
        logger.error(f"File processing failed: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "file_processing_error", "message": str(e)}
        )
    
    except AIAnalysisError as e:
        logger.error(f"AI analysis failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "ai_analysis_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in analysis: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Analysis failed unexpectedly"}
        )

@router.post("/payment/create")
async def create_payment_session(
    request: Request,
    analysis_id: str = Form(...),
    product_type: str = Form(...),
    region_override: Optional[str] = Form(None),
    promo_code: Optional[str] = Form(None)
):
    """
    Create Stripe payment session
    
    - analysis_id: ID of analysis to upgrade
    - product_type: "resume_analysis", "job_fit_analysis", "cover_letter"
    - region_override: Optional region code for testing
    """
    logger.info(f"Payment session creation: {analysis_id}, {product_type}")
    
    try:
        # Verify analysis exists
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
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
        amount = geo_service.convert_amount_for_stripe(country, product_type)
        product_name = product_info.get("name", product_type.replace('_', ' ').title())
        
        # Apply promotional code discount if provided
        original_amount = amount
        applied_discount = None
        if promo_code and promo_code.strip():
            try:
                # Convert cents to dollars for promo calculation, then back to cents
                amount_dollars = amount / 100
                discount = promotional_service.calculate_discount(promo_code.strip(), amount_dollars)
                amount = int(discount['final_amount'] * 100)  # Convert back to cents for Stripe
                applied_discount = discount
                logger.info(f"Applied promo code {promo_code}: original ${amount_dollars:.2f}, final ${discount['final_amount']:.2f}")
            except Exception as e:
                logger.warning(f"Failed to apply promo code {promo_code}: {e}")
                # Continue with original amount if promo code fails
        
        # Create payment session
        payment_service = get_payment_service()
        session_data = await payment_service.create_payment_session(
            analysis_id=analysis_id,
            product_type=product_type,
            amount=amount,
            currency=currency,
            product_name=product_name
        )
        
        # Calculate display amount (show discounted price if promo applied)
        if applied_discount:
            amount_display = f"${amount/100:.2f}"
            if applied_discount['is_free']:
                amount_display = "FREE"
        else:
            amount_display = product_info.get("display")
        
        return {
            "payment_session": session_data,
            "pricing_info": {
                "country": country,
                "currency": currency.upper(),
                "amount_display": amount_display,
                "product_name": product_name,
                "original_amount": f"${original_amount/100:.2f}",
                "discounted_amount": f"${amount/100:.2f}" if applied_discount else None,
                "promo_code": promo_code.strip() if promo_code and promo_code.strip() else None
            }
        }
        
    except PaymentError as e:
        logger.error(f"Payment error: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "payment_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Unexpected payment error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Payment session creation failed"}
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
        payment_service = get_payment_service()
        verification = await payment_service.verify_payment_session(session_id)
        
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
        
        # If no premium result exists, generate it now
        if not analysis.get('premium_result'):
            try:
                premium_result = await analysis_service.analyze_resume(
                    analysis['resume_text'], 
                    'premium'
                )
                AnalysisDB.update_premium_result(analysis_id, premium_result)
                analysis['premium_result'] = premium_result
            except Exception as e:
                logger.error(f"Failed to generate premium analysis: {e}")
        
        # Use the proper payment success template that was working before
        return templates.TemplateResponse("payment_success.html", {
            "request": request,
            "analysis_id": analysis_id,
            "product_type": product_type,
            "session_id": session_id,
            "amount_paid": amount_paid,
            "currency": currency
        })
        
    except Exception as e:
        logger.error(f"Payment success handler error: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Payment verification failed: {str(e)}</p>",
            status_code=500
        )

@router.get("/payment/cancel")
async def payment_cancel(analysis_id: str, product_type: str):
    """Handle payment cancellation"""
    logger.info(f"Payment cancelled: analysis {analysis_id}, product {product_type}")
    
    cancel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payment Cancelled - Resume Health Checker</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; text-align: center; }}
            .cancel {{ color: #dc3545; }}
            .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px; }}
        </style>
    </head>
    <body>
        <h1 class="cancel">Payment Cancelled</h1>
        <p>Your payment was cancelled. No charges were made.</p>
        <p>You can still access your free analysis results.</p>
        
        <a href="/" class="btn">Return to Resume Checker</a>
    </body>
    </html>
    """
    
    return HTMLResponse(content=cancel_html)

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks securely"""
    try:
        payload = await request.body()
        signature = request.headers.get('stripe-signature')
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe signature")
        
        payment_service = get_payment_service()
        result = await payment_service.handle_webhook_event(payload, signature)
        return result
        
    except PaymentError as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/pricing/{country_code}")
async def get_regional_pricing(country_code: str):
    """Get pricing for specific country/region"""
    try:
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
        region_info = geo_service.detect_region_from_request(request)
        return region_info
    except Exception as e:
        logger.error(f"Region detection error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "geo_error", "message": "Could not detect region"}
        )

@router.get("/premium/{analysis_id}")
async def get_premium_service(analysis_id: str, product_type: str = "resume_analysis", embedded: bool = False):
    """
    Get premium service results after successful payment
    
    - analysis_id: ID of the analysis
    - product_type: Type of premium service to deliver
    - embedded: If true, return HTML content for embedding in main app
    """
    logger.info(f"Premium service request: {analysis_id}, {product_type}, embedded={embedded}")
    
    try:
        # Get analysis data
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if premium result exists
        if analysis.get('premium_result'):
            logger.info(f"Returning existing premium result for {analysis_id}")
            
            if embedded:
                # Return HTML content for embedding in main app
                from .templates import (
                    generate_embedded_resume_analysis_html,
                    generate_embedded_job_fit_html,
                    generate_embedded_cover_letter_html,
                    generate_embedded_resume_rewrite_html,
                    generate_embedded_interview_prep_html
                )
                premium_result = analysis['premium_result']
                
                # Generate embedded HTML based on product type
                if product_type == "resume_analysis":
                    html_content = generate_embedded_resume_analysis_html(premium_result, analysis_id)
                elif product_type == "job_fit_analysis":
                    html_content = generate_embedded_job_fit_html(premium_result, analysis_id)
                elif product_type == "cover_letter":
                    html_content = generate_embedded_cover_letter_html(premium_result, analysis_id)
                elif product_type == "resume_rewrite":
                    html_content = generate_embedded_resume_rewrite_html(premium_result, analysis_id)
                elif product_type == "mock_interview":
                    html_content = generate_embedded_interview_prep_html(premium_result, analysis_id)
                else:
                    html_content = f"<h1>Premium {product_type} Results</h1><pre>{premium_result}</pre>"
                
                return HTMLResponse(content=html_content)
            else:
                # Return JSON for payment success page
                return {
                    "analysis_id": analysis_id,
                    "product_type": product_type,
                    "premium_result": analysis['premium_result'],
                    "status": "ready"
                }
        
        # If no premium result exists, return not ready status
        if embedded:
            return HTMLResponse(content="<h1>Results Not Ready</h1><p>Your premium analysis is still being generated. Please wait...</p>", status_code=202)
        else:
            return {
                "analysis_id": analysis_id,
                "product_type": product_type,
                "premium_result": None,
                "status": "generating"
            }
        
    except Exception as e:
        logger.error(f"Premium service retrieval error: {e}")
        if embedded:
            return HTMLResponse(content=f"<h1>Error</h1><p>Could not retrieve premium service: {str(e)}</p>", status_code=500)
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "premium_service_error", "message": "Could not retrieve premium service"}
            )

@router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Retrieve analysis by ID"""
    try:
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Remove sensitive data
        safe_analysis = {
            "id": analysis["id"],
            "filename": analysis["filename"],
            "analysis_type": analysis["analysis_type"],
            "free_result": analysis.get("free_result"),
            "premium_result": analysis.get("premium_result"),
            "payment_status": analysis["payment_status"],
            "created_at": analysis["created_at"]
        }
        
        return safe_analysis
        
    except Exception as e:
        logger.error(f"Analysis retrieval error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "retrieval_error", "message": "Could not retrieve analysis"}
        )

# =============================================================================
# ADMIN/DEBUG ENDPOINTS (development only)
# =============================================================================

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

# =============================================================================
# COVER LETTER ENDPOINT (bonus feature)
# =============================================================================

@router.post("/generate-cover-letter")
async def generate_cover_letter(
    request: Request,
    analysis_id: str = Form(...),
    job_posting: str = Form(...),
    analysis_type: str = Form("free")
):
    """Generate cover letter based on resume and job posting"""
    try:
        # Get analysis
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Generate cover letter
        cover_letter = await analysis_service.generate_cover_letter(
            analysis['resume_text'],
            job_posting,
            analysis_type
        )
        
        return {
            "analysis_id": analysis_id,
            "cover_letter": cover_letter,
            "analysis_type": analysis_type
        }
        
    except AIAnalysisError as e:
        logger.error(f"Cover letter generation failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "ai_analysis_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Cover letter error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Cover letter generation failed"}
        )

# =============================================================================
# PROMOTIONAL CODE ENDPOINTS
# =============================================================================

@router.post("/promo/validate")
async def validate_promo_code(request: Request):
    """Validate promotional code and calculate discount"""
    try:
        body = await request.json()
        code = body.get('code', '').strip()
        amount = float(body.get('amount', 0))
        
        if not code:
            raise HTTPException(status_code=400, detail="Code required")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
        
        # Get validation info first to include discount type and value
        validation = promotional_service.validate_code(code)
        result = promotional_service.calculate_discount(code, amount)
        
        # Add discount type and value to the result for UI calculations
        result['discount_type'] = validation['discount_type']
        result['discount_value'] = validation['discount_value']
        
        return JSONResponse(content={
            "valid": True,
            "discount": result,
            "message": f"Save ${result['discount_amount']:.2f}!"
        })
        
    except AIAnalysisError as e:
        return JSONResponse(status_code=400, content={"valid": False, "error": str(e)})
    except Exception as e:
        logger.error(f"Promo validation error: {e}")
        return JSONResponse(status_code=500, content={"valid": False, "error": "Validation failed"})

@router.post("/promo/apply")
async def apply_promo_code(request: Request):
    """Apply promotional code - integrates with unified premium service"""
    try:
        from ..services.premium_generation import premium_generation_service, AccessContext, AccessType
        
        body = await request.json()
        code = body.get('code', '').strip()
        analysis_id = body.get('analysis_id')
        product_type = body.get('product_type', 'resume_analysis')
        amount = float(body.get('amount', 0))
        
        if not all([code, analysis_id]):
            raise HTTPException(status_code=400, detail="Code and analysis_id required")
        
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        discount = promotional_service.calculate_discount(code, amount)
        promotional_service.track_usage(code, analysis_id, discount['discount_amount'])
        
        if discount['is_free']:
            logger.info(f"Free promo access for {analysis_id}")
            
            access_context = AccessContext(
                access_type=AccessType.PROMO_CODE,
                promo_code=code,
                metadata={"discount_amount": discount['discount_amount']}
            )
            
            premium_result = await premium_generation_service.generate_premium_results(
                analysis_id=analysis_id,
                product_type=product_type,
                access_context=access_context
            )
            
            analysis['premium_result'] = premium_result
            analysis['payment_status'] = 'paid'
            AnalysisDB.update(analysis_id, analysis)
            
            return JSONResponse(content={
                "success": True,
                "free_access": True,
                "premium_result": premium_result,
                "message": "Free access granted!"
            })
        
        return JSONResponse(content={
            "success": True,
            "free_access": False,
            "discount": discount,
            "message": f"Pay ${discount['final_amount']:.2f} (save ${discount['discount_amount']:.2f})"
        })
        
    except HTTPException:
        raise
    except AIAnalysisError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    except Exception as e:
        logger.error(f"Promo application error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": "Application failed"})

@router.post("/promo/create")
async def create_promo_code(request: Request):
    """Create promotional code - admin endpoint"""
    try:
        body = await request.json()
        
        code = body.get('code', '').strip()
        discount_type = body.get('type', 'percentage')
        discount_value = float(body.get('value', 0))
        max_uses = body.get('max_uses')
        
        if not code or discount_value <= 0:
            raise HTTPException(status_code=400, detail="Invalid code or value")
        
        if discount_type not in ['percentage', 'fixed']:
            raise HTTPException(status_code=400, detail="Type must be 'percentage' or 'fixed'")
        
        success = promotional_service.create_code(code, discount_type, discount_value, max_uses)
        
        if not success:
            raise HTTPException(status_code=400, detail="Code already exists")
        
        return JSONResponse(content={"success": True, "message": f"Code '{code}' created"})
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Promo creation error: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": "Creation failed"})