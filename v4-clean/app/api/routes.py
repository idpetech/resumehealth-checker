"""
API Routes for Resume Health Checker v4.0

All endpoints in one clean, organized file with proper error handling.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
import uuid

from ..core.database import AnalysisDB, get_database_stats
from ..core.exceptions import FileProcessingError, AIAnalysisError, PaymentError, validate_file_upload
from ..services.files import file_service
from ..services.analysis import analysis_service
from ..services.payments import get_payment_service
from ..services.geo import geo_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# =============================================================================
# MAIN ENDPOINTS
# =============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring and load balancers"""
    from ..core.config import config
    import datetime
    
    return {
        "status": "healthy",
        "service": "Resume Health Checker v4.0",
        "environment": config.environment,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
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

@router.get("/premium/{analysis_id}")
async def get_premium_service(analysis_id: str, product_type: str = "resume_analysis"):
    """
    Get premium service results after successful payment
    
    - analysis_id: ID of the analysis
    - product_type: Type of premium service to deliver
    """
    logger.info(f"Premium service request: {analysis_id}, {product_type}")
    
    try:
        # Get analysis data
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if payment was successful
        if analysis.get('payment_status') != 'paid':
            raise HTTPException(status_code=402, detail="Payment required")
        
        # Get job posting if available
        job_posting = analysis.get('job_posting')
        
        # Generate premium service based on product type
        if product_type == "resume_analysis":
            result = await analysis_service.analyze_resume(
                analysis['resume_text'], 
                'premium',
                job_posting
            )
        elif product_type == "job_fit_analysis":
            if not job_posting:
                raise HTTPException(status_code=400, detail="Job posting required for job fit analysis")
            result = await analysis_service.analyze_resume(
                analysis['resume_text'], 
                'premium',
                job_posting
            )
        elif product_type == "cover_letter":
            if not job_posting:
                raise HTTPException(status_code=400, detail="Job posting required for cover letter generation")
            result = await analysis_service.generate_cover_letter(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "resume_enhancer":
            if not job_posting:
                raise HTTPException(status_code=400, detail="Job posting required for resume enhancement")
            result = await analysis_service.enhance_resume(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "interview_prep":
            result = await analysis_service.generate_interview_prep(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "salary_insights":
            result = await analysis_service.generate_salary_insights(
                analysis['resume_text']
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid product type: {product_type}")
        
        # Store the premium result
        AnalysisDB.update_premium_result(analysis_id, result)
        
        return {
            "analysis_id": analysis_id,
            "product_type": product_type,
            "result": result,
            "timestamp": "2025-09-02T13:00:00Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Premium service error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "premium_service_error", "message": str(e)}
        )

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
    job_posting: Optional[str] = Form(None)
):
    """
    Create Stripe payment session
    
    - analysis_id: ID of analysis to upgrade
    - product_type: "resume_analysis", "job_fit_analysis", "cover_letter"
    - region_override: Optional region code for testing
    - job_posting: Optional job posting text for job-specific products
    """
    logger.info(f"Payment session creation: {analysis_id}, {product_type}")
    
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
        amount = geo_service.convert_amount_for_stripe(country, product_type)
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
        logger.error(f"Unexpected payment error: {e}")
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
        
        # If no premium result exists, generate it now
        if not analysis.get('premium_result'):
            try:
                logger.info(f"Generating premium analysis for {analysis_id}")
                premium_result = await analysis_service.analyze_resume(
                    analysis['resume_text'], 
                    'premium'
                )
                if premium_result:
                    AnalysisDB.update_premium_result(analysis_id, premium_result)
                    analysis['premium_result'] = premium_result
                    logger.info(f"Premium analysis generated successfully for {analysis_id}")
                else:
                    logger.error(f"Premium analysis returned empty result for {analysis_id}")
                    analysis['premium_result'] = {
                        "error": "Premium analysis generation failed",
                        "message": "Our AI analysis service is temporarily unavailable. Please contact support.",
                        "analysis_id": analysis_id
                    }
            except Exception as e:
                logger.error(f"Failed to generate premium analysis for {analysis_id}: {e}")
                logger.error(f"Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                analysis['premium_result'] = {
                    "error": "Premium analysis generation failed",
                    "message": "Our AI analysis service encountered an error. Please contact support.",
                    "technical_details": str(e),
                    "analysis_id": analysis_id
                }
        
        # Return success page with results
        success_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Payment Successful - Resume Health Checker</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .success {{ color: #28a745; }}
                .analysis-box {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .btn {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1 class="success">✅ Payment Successful!</h1>
            <p>Thank you for your payment. Your premium analysis is ready!</p>
            
            <div class="analysis-box">
                <h3>Payment Details</h3>
                <p><strong>Amount:</strong> {amount_paid/100:.2f} {currency}</p>
                <p><strong>Product:</strong> {product_type.replace('_', ' ').title()}</p>
                <p><strong>Session ID:</strong> {session_id}</p>
            </div>
            
            <div class="analysis-box">
                <h3>Your Premium Analysis</h3>"""
        
        # Handle different types of premium results
        premium_result = analysis.get('premium_result')
        if premium_result is None:
            success_html += """
                <p style="color: #ffc107;">⏳ Your premium analysis is being generated. Please refresh this page in a moment.</p>"""
        elif isinstance(premium_result, dict) and premium_result.get('error'):
            success_html += f"""
                <div style="color: #dc3545; background: #f8d7da; padding: 15px; border-radius: 5px;">
                    <h4>⚠️ Analysis Service Issue</h4>
                    <p>{premium_result.get('message', 'Unknown error occurred')}</p>
                    <p><strong>Analysis ID:</strong> {analysis_id}</p>
                    <p><em>Please screenshot this page and contact support for assistance.</em></p>
                </div>"""
        else:
            # Simple premium analysis display similar to free version
            success_html += f"""
                <div style="background: #f8f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e0e0e0;">
                    <h3 style="color: #667eea; margin-top: 0;">🎯 Premium Analysis Results</h3>
                    
                    <div style="margin: 15px 0;">
                        <h4 style="color: #333; margin-bottom: 10px;">Overall Score: {premium_result.get('overall_score', 'N/A')}</h4>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <h4 style="color: #28a745;">💪 Key Strengths</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">"""
            
            # Add strengths
            for strength in premium_result.get('strength_highlights', []):
                success_html += f'<li style="margin: 8px 0; line-height: 1.4;">{strength}</li>'
            
            success_html += """</ul>
                    </div>
                    
                    <div style="margin: 15px 0;">
                        <h4 style="color: #ffc107;">🚀 Improvement Opportunities</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">"""
            
            # Add improvements
            for improvement in premium_result.get('improvement_opportunities', []):
                success_html += f'<li style="margin: 8px 0; line-height: 1.4;">{improvement}</li>'
            
            success_html += """</ul>
                    </div>"""
            
            # Add competitive advantages if available
            competitive_advantages = premium_result.get('competitive_advantages')
            if competitive_advantages:
                success_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #28a745;">
                        <h4 style="color: #28a745; margin-top: 0;">🏆 Your Competitive Advantages</h4>
                        <p style="margin: 0; line-height: 1.5;">{competitive_advantages}</p>
                    </div>"""
            
            # Add success prediction if available
            success_prediction = premium_result.get('success_prediction')
            if success_prediction:
                success_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #e8f4fd; border-radius: 8px; border-left: 4px solid #667eea;">
                        <h4 style="color: #667eea; margin-top: 0;">🎯 Success Prediction</h4>
                        <p style="margin: 0; line-height: 1.5;">{success_prediction}</p>
                    </div>"""
            
            success_html += """
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                        <button onclick="window.print()" style="background: #28a745; color: white; border: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; margin: 5px; cursor: pointer;">🖨️ Print Analysis</button>
                        <a href="/" style="background: #667eea; color: white; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-size: 16px; margin: 5px; display: inline-block;">🏠 Analyze Another Resume</a>
                    </div>
                </div>"""
        
        success_html += """
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=success_html)
        
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
        
        result = await get_payment_service().handle_webhook_event(payload, signature)
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
# MOCK PAYMENT ENDPOINTS (for testing)
# =============================================================================

@router.get("/payment/mock")
async def mock_payment_page(
    session_id: str,
    analysis_id: str,
    product_type: str
):
    """Mock payment page for testing when Stripe is not configured"""
    from ..core.config import config
    
    # Return a simple HTML page for mock payment
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mock Payment - Resume Health Checker</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                color: #333;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 500px;
                width: 90%;
            }}
            .success-icon {{
                font-size: 4rem;
                color: #28a745;
                margin-bottom: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: left;
            }}
            .info p {{
                margin: 5px 0;
                font-size: 14px;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>
            <h1>Mock Payment Successful!</h1>
            <p>This is a test payment page for development purposes.</p>
            
            <div class="info">
                <p><strong>Session ID:</strong> {session_id}</p>
                <p><strong>Analysis ID:</strong> {analysis_id}</p>
                <p><strong>Product Type:</strong> {product_type}</p>
                <p><strong>Environment:</strong> {config.environment}</p>
            </div>
            
            <p>In a real implementation, this would redirect to Stripe Checkout.</p>
            
            <div class="actions">
                <a href="/" class="btn" onclick="returnToApp()">Return to App</a>
                <a href="/api/v1/admin/stats" class="btn">View Stats</a>
            </div>
            
            <script>
                // Mark analysis as paid and redirect to app
                async function returnToApp() {{
                    try {{
                        // Mark payment as completed
                        await fetch('/api/v1/payment/complete', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                analysis_id: '{analysis_id}',
                                product_type: '{product_type}',
                                session_id: '{session_id}'
                            }})
                        }});
                        
                        // Redirect to main app with premium results
                        window.location.href = '/?premium=true&product={product_type}&analysis_id={analysis_id}';
                    }} catch (error) {{
                        console.error('Error completing payment:', error);
                        window.location.href = '/';
                    }}
                }}
                
                // Auto-redirect after 3 seconds
                setTimeout(returnToApp, 3000);
            </script>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@router.get("/premium-results/{analysis_id}")
async def premium_results_page(
    analysis_id: str,
    product_type: str = "resume_analysis",
    embedded: bool = False
):
    """Display premium service results in a beautiful HTML page"""
    try:
        # Get the premium service data
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            return HTMLResponse(content="<h1>Analysis not found</h1>", status_code=404)
        
        # Check if payment was successful
        if analysis.get('payment_status') != 'paid':
            return HTMLResponse(content="<h1>Payment required</h1>", status_code=402)
        
        # Get job posting if available
        job_posting = analysis.get('job_posting')
        
        # Generate premium service based on product type
        if product_type == "resume_analysis":
            result = await analysis_service.analyze_resume(
                analysis['resume_text'], 
                'premium',
                job_posting
            )
        elif product_type == "job_fit_analysis":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for job fit analysis</h1>", status_code=400)
            result = await analysis_service.analyze_resume(
                analysis['resume_text'], 
                'premium',
                job_posting
            )
        elif product_type == "cover_letter":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for cover letter generation</h1>", status_code=400)
            result = await analysis_service.generate_cover_letter(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "resume_enhancer":
            if not job_posting:
                return HTMLResponse(content="<h1>Job posting required for resume enhancement</h1>", status_code=400)
            result = await analysis_service.enhance_resume(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "interview_prep":
            result = await analysis_service.generate_interview_prep(
                analysis['resume_text'], 
                job_posting
            )
        elif product_type == "salary_insights":
            result = await analysis_service.generate_salary_insights(
                analysis['resume_text']
            )
        else:
            return HTMLResponse(content=f"<h1>Invalid product type: {product_type}</h1>", status_code=400)
        
        # Store the premium result
        AnalysisDB.update_premium_result(analysis_id, result)
        
        # Generate HTML content based on product type
        if embedded:
            html_content = generate_embedded_premium_results_html(product_type, result, analysis_id)
        else:
            html_content = generate_premium_results_html(product_type, result, analysis_id)
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Premium results page error: {e}")
        return HTMLResponse(content=f"<h1>Error generating premium results: {str(e)}</h1>", status_code=500)

def generate_premium_results_html(product_type: str, result: dict, analysis_id: str) -> str:
    """Generate beautiful HTML for premium results"""
    
    if product_type == "resume_analysis":
        return generate_resume_analysis_html(result, analysis_id)
    elif product_type == "job_fit_analysis":
        return generate_job_fit_html(result, analysis_id)
    elif product_type == "cover_letter":
        return generate_cover_letter_html(result, analysis_id)
    elif product_type == "interview_prep":
        return generate_interview_prep_html(result, analysis_id)
    elif product_type == "salary_insights":
        return generate_salary_insights_html(result, analysis_id)
    else:
        return f"<h1>Premium results for {product_type}</h1><pre>{result}</pre>"

def generate_resume_analysis_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for premium resume analysis results"""
    
    # Extract data safely
    overall_score = result.get('overall_score', 'N/A')
    strengths = result.get('strength_highlights', [])
    opportunities = result.get('improvement_opportunities', [])
    ats_opt = result.get('ats_optimization', {})
    content_enhancement = result.get('content_enhancement', {})
    text_rewrites = result.get('text_rewrites', [])
    competitive_advantages = result.get('competitive_advantages', '')
    success_prediction = result.get('success_prediction', '')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Premium Resume Analysis - Resume Health Checker</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5rem;
                font-weight: 700;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.1rem;
                opacity: 0.9;
            }}
            .content {{
                padding: 40px;
            }}
            .score-section {{
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
                border-radius: 12px;
                border: 2px solid #667eea;
            }}
            .score {{
                font-size: 4rem;
                font-weight: 700;
                color: #667eea;
                margin: 0;
            }}
            .score-label {{
                font-size: 1.2rem;
                color: #666;
                margin-top: 10px;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section h2 {{
                color: #667eea;
                font-size: 1.8rem;
                margin-bottom: 20px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}
            .section h3 {{
                color: #333;
                font-size: 1.3rem;
                margin-bottom: 15px;
            }}
            .strengths-list, .opportunities-list {{
                list-style: none;
                padding: 0;
            }}
            .strengths-list li, .opportunities-list li {{
                background: #f8f9ff;
                margin: 10px 0;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .strengths-list li {{
                border-left-color: #28a745;
            }}
            .opportunities-list li {{
                border-left-color: #ffc107;
            }}
            .text-rewrite {{
                background: #f8f9ff;
                padding: 20px;
                border-radius: 8px;
                margin: 15px 0;
                border: 1px solid #e0e0e0;
            }}
            .original {{
                background: #fff3cd;
                padding: 15px;
                border-radius: 6px;
                margin: 10px 0;
                border-left: 4px solid #ffc107;
            }}
            .improved {{
                background: #d4edda;
                padding: 15px;
                border-radius: 6px;
                margin: 10px 0;
                border-left: 4px solid #28a745;
            }}
            .why-better {{
                font-style: italic;
                color: #666;
                margin-top: 10px;
            }}
            .competitive-advantages, .success-prediction {{
                background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
                padding: 25px;
                border-radius: 12px;
                border: 2px solid #28a745;
                margin: 20px 0;
            }}
            .actions {{
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 1px solid #e0e0e0;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }}
            .print-btn {{
                background: #28a745;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Premium Resume Analysis</h1>
                <p>Your comprehensive resume optimization report</p>
            </div>
            
            <div class="content">
                <div class="score-section">
                    <div class="score">{overall_score}</div>
                    <div class="score-label">Overall Resume Score</div>
                </div>
                
                <div class="section">
                    <h2>💪 Key Strengths</h2>
                    <ul class="strengths-list">
    """
    
    for strength in strengths:
        html_content += f'<li>{strength}</li>'
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🚀 Improvement Opportunities</h2>
                    <ul class="opportunities-list">
    """
    
    for opportunity in opportunities:
        html_content += f'<li>{opportunity}</li>'
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="section">
                    <h2>📊 ATS Optimization</h2>
                    <h3>Current Strength</h3>
                    <p>{ats_opt.get('current_strength', 'N/A')}</p>
                    
                    <h3>Enhancement Opportunities</h3>
                    <ul>
    """
    
    for enhancement in ats_opt.get('enhancement_opportunities', []):
        html_content += f'<li>{enhancement}</li>'
    
    html_content += f"""
                    </ul>
                    
                    <h3>Impact Prediction</h3>
                    <p>{ats_opt.get('impact_prediction', 'N/A')}</p>
                </div>
                
                <div class="section">
                    <h2>📝 Content Enhancement</h2>
                    <h3>Strong Sections</h3>
                    <ul>
    """
    
    for section in content_enhancement.get('strong_sections', []):
        html_content += f'<li>{section}</li>'
    
    html_content += f"""
                    </ul>
                    
                    <h3>Growth Areas</h3>
                    <ul>
    """
    
    for area in content_enhancement.get('growth_areas', []):
        html_content += f'<li>{area}</li>'
    
    html_content += f"""
                    </ul>
                    
                    <h3>Strategic Additions</h3>
                    <ul>
    """
    
    for addition in content_enhancement.get('strategic_additions', []):
        html_content += f'<li>{addition}</li>'
    
    html_content += f"""
                    </ul>
                </div>
    """
    
    if text_rewrites:
        html_content += """
                <div class="section">
                    <h2>✏️ Text Rewrites</h2>
        """
        
        for rewrite in text_rewrites:
            html_content += f"""
                    <div class="text-rewrite">
                        <h3>{rewrite.get('section', 'Section')}</h3>
                        <div class="original">
                            <strong>Original:</strong><br>
                            {rewrite.get('original', 'N/A')}
                        </div>
                        <div class="improved">
                            <strong>Improved:</strong><br>
                            {rewrite.get('improved', 'N/A')}
                        </div>
                        <div class="why-better">
                            <strong>Why this is better:</strong> {rewrite.get('why_better', 'N/A')}
                        </div>
                    </div>
            """
        
        html_content += """
                </div>
        """
    
    html_content += f"""
                <div class="competitive-advantages">
                    <h2>🏆 Competitive Advantages</h2>
                    <p>{competitive_advantages}</p>
                </div>
                
                <div class="success-prediction">
                    <h2>🎯 Success Prediction</h2>
                    <p>{success_prediction}</p>
                </div>
                
                <div class="actions">
                    <button class="btn print-btn" onclick="window.print()">🖨️ Print Report</button>
                    <a href="/" class="btn">🏠 Return to App</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_job_fit_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for job fit analysis results"""
    
    match_percentage = result.get('match_percentage', 'N/A')
    requirements_met = result.get('requirements_met', [])
    missing_qualifications = result.get('missing_qualifications', [])
    strengths = result.get('strengths', [])
    improvements = result.get('improvements', [])
    recommendations = result.get('recommendations', [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Job Fit Analysis - Resume Health Checker</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5rem;
                font-weight: 700;
            }}
            .content {{
                padding: 40px;
            }}
            .score-section {{
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
                border-radius: 12px;
                border: 2px solid #667eea;
            }}
            .score {{
                font-size: 4rem;
                font-weight: 700;
                color: #667eea;
                margin: 0;
            }}
            .section {{
                margin-bottom: 40px;
            }}
            .section h2 {{
                color: #667eea;
                font-size: 1.8rem;
                margin-bottom: 20px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }}
            .list {{
                list-style: none;
                padding: 0;
            }}
            .list li {{
                background: #f8f9ff;
                margin: 10px 0;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .actions {{
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 1px solid #e0e0e0;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Job Fit Analysis</h1>
                <p>How well your resume matches the job requirements</p>
            </div>
            
            <div class="content">
                <div class="score-section">
                    <div class="score">{match_percentage}%</div>
                    <div class="score-label">Job Match Score</div>
                </div>
                
                <div class="section">
                    <h2>✅ Requirements Met</h2>
                    <ul class="list">
    """
    
    for req in requirements_met:
        html_content += f'<li>{req}</li>'
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="section">
                    <h2>❌ Missing Qualifications</h2>
                    <ul class="list">
    """
    
    for missing in missing_qualifications:
        html_content += f'<li>{missing}</li>'
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="section">
                    <h2>💪 Strengths</h2>
                    <ul class="list">
    """
    
    for strength in strengths:
        html_content += f'<li>{strength}</li>'
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🚀 Improvements</h2>
                    <ul class="list">
    """
    
    for improvement in improvements:
        html_content += f'<li>{improvement}</li>'
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="actions">
                    <button class="btn" onclick="window.print()">🖨️ Print Report</button>
                    <a href="/" class="btn">🏠 Return to App</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_cover_letter_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for cover letter results"""
    
    cover_letter = result.get('cover_letter', '')
    key_points = result.get('key_points_highlighted', [])
    tone = result.get('tone', '')
    word_count = result.get('word_count', '')
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Cover Letter - Resume Health Checker</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            .content {{
                padding: 40px;
            }}
            .cover-letter {{
                background: #f8f9ff;
                padding: 30px;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                white-space: pre-line;
                line-height: 1.6;
                font-size: 1.1rem;
            }}
            .actions {{
                text-align: center;
                margin-top: 40px;
                padding-top: 30px;
                border-top: 1px solid #e0e0e0;
            }}
            .btn {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                margin: 10px;
                text-decoration: none;
                display: inline-block;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 AI Cover Letter</h1>
                <p>Your personalized cover letter</p>
            </div>
            
            <div class="content">
                <div class="cover-letter">{cover_letter}</div>
                
                <div class="actions">
                    <button class="btn" onclick="window.print()">🖨️ Print Letter</button>
                    <a href="/" class="btn">🏠 Return to App</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def generate_interview_prep_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for interview prep results"""
    return f"<h1>Interview Prep Results</h1><pre>{result}</pre>"

def generate_salary_insights_html(result: dict, analysis_id: str) -> str:
    """Generate HTML for salary insights results"""
    return f"<h1>Salary Insights Results</h1><pre>{result}</pre>"

@router.post("/payment/complete")
async def complete_payment(request: Request):
    """Mark payment as completed (for mock payments)"""
    try:
        data = await request.json()
        analysis_id = data.get('analysis_id')
        product_type = data.get('product_type')
        session_id = data.get('session_id')
        
        if not analysis_id:
            raise HTTPException(status_code=400, detail="Analysis ID required")
        
        # Mark analysis as paid
        AnalysisDB.mark_as_paid(analysis_id, 1000, "usd")  # Mock amount
        
        logger.info(f"Payment completed for analysis {analysis_id}, product {product_type}")
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "product_type": product_type,
            "message": "Payment completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Payment completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "payment_completion_error", "message": str(e)}
        )

@router.get("/payment/success")
async def payment_success(
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

@router.get("/payment/cancel")
async def payment_cancel(
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

def generate_embedded_premium_results_html(product_type: str, result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for premium results that fits in the right panel"""
    
    if product_type == "resume_analysis":
        return generate_embedded_resume_analysis_html(result, analysis_id)
    elif product_type == "job_fit_analysis":
        return generate_embedded_job_fit_html(result, analysis_id)
    elif product_type == "cover_letter":
        return generate_embedded_cover_letter_html(result, analysis_id)
    elif product_type == "interview_prep":
        return generate_embedded_interview_prep_html(result, analysis_id)
    elif product_type == "salary_insights":
        return generate_embedded_salary_insights_html(result, analysis_id)
    else:
        return f"<h1>Premium results for {product_type}</h1><pre>{result}</pre>"

def generate_embedded_resume_analysis_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for premium resume analysis results"""
    
    # Extract data safely
    overall_score = result.get('overall_score', 'N/A')
    strengths = result.get('strength_highlights', [])
    opportunities = result.get('improvement_opportunities', [])
    ats_opt = result.get('ats_optimization', {})
    content_enhancement = result.get('content_enhancement', {})
    text_rewrites = result.get('text_rewrites', [])
    competitive_advantages = result.get('competitive_advantages', '')
    success_prediction = result.get('success_prediction', '')
    
    html_content = f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>🎯 Premium Resume Analysis</h2>
            <p>Your comprehensive resume optimization report</p>
        </div>
        
        <div class="score-section">
            <div class="score">{overall_score}</div>
            <div class="score-label">Overall Resume Score</div>
        </div>
        
        <div class="section">
            <h3>💪 Key Strengths</h3>
            <ul class="strengths-list">
    """
    
    for strength in strengths:
        html_content += f'<li>{strength}</li>'
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="section">
            <h3>🚀 Improvement Opportunities</h3>
            <ul class="opportunities-list">
    """
    
    for opportunity in opportunities:
        html_content += f'<li>{opportunity}</li>'
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="section">
            <h3>📊 ATS Optimization</h3>
            <h4>Current Strength</h4>
            <p>{ats_opt.get('current_strength', 'N/A')}</p>
            
            <h4>Enhancement Opportunities</h4>
            <ul>
    """
    
    for enhancement in ats_opt.get('enhancement_opportunities', []):
        html_content += f'<li>{enhancement}</li>'
    
    html_content += f"""
            </ul>
            
            <h4>Impact Prediction</h4>
            <p>{ats_opt.get('impact_prediction', 'N/A')}</p>
        </div>
        
        <div class="section">
            <h3>📝 Content Enhancement</h3>
            <h4>Strong Sections</h4>
            <ul>
    """
    
    for strong in content_enhancement.get('strong_sections', []):
        html_content += f'<li>{strong}</li>'
    
    html_content += f"""
            </ul>
            
            <h4>Growth Areas</h4>
            <ul>
    """
    
    for growth in content_enhancement.get('growth_areas', []):
        html_content += f'<li>{growth}</li>'
    
    html_content += f"""
            </ul>
            
            <h4>Strategic Additions</h4>
            <ul>
    """
    
    for addition in content_enhancement.get('strategic_additions', []):
        html_content += f'<li>{addition}</li>'
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="section">
            <h3>✏️ Text Rewrites</h3>
    """
    
    for rewrite in text_rewrites:
        html_content += f"""
            <div class="text-rewrite">
                <h4>{rewrite.get('section', 'Section')}</h4>
                <div class="original">
                    <strong>Original:</strong><br>
                    {rewrite.get('original', 'N/A')}
                </div>
                <div class="improved">
                    <strong>Improved:</strong><br>
                    {rewrite.get('improved', 'N/A')}
                </div>
                <div class="why-better">
                    <strong>Why this is better:</strong> {rewrite.get('why_better', 'N/A')}
                </div>
            </div>
        """
    
    html_content += f"""
        </div>
        
        <div class="competitive-advantages">
            <h3>🏆 Competitive Advantages</h3>
            <p>{competitive_advantages}</p>
        </div>
        
        <div class="success-prediction">
            <h3>🎯 Success Prediction</h3>
            <p>{success_prediction}</p>
        </div>
        
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">🖨️ Print Report</button>
            <a href="/" class="btn">🏠 Return to App</a>
        </div>
    </div>
    
    <style>
        .premium-results {{
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .premium-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }}
        
        .premium-header h2 {{
            color: #667eea;
            margin: 0;
            font-size: 1.8rem;
        }}
        
        .premium-header p {{
            color: #666;
            margin: 10px 0 0 0;
        }}
        
        .score-section {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
            border-radius: 12px;
            border: 2px solid #667eea;
        }}
        
        .score {{
            font-size: 3rem;
            font-weight: 700;
            color: #667eea;
            margin: 0;
        }}
        
        .score-label {{
            font-size: 1.1rem;
            color: #666;
            margin-top: 10px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h3 {{
            color: #667eea;
            font-size: 1.4rem;
            margin-bottom: 15px;
            border-bottom: 1px solid #667eea;
            padding-bottom: 8px;
        }}
        
        .section h4 {{
            color: #333;
            font-size: 1.1rem;
            margin-bottom: 10px;
        }}
        
        .strengths-list, .opportunities-list {{
            list-style: none;
            padding: 0;
        }}
        
        .strengths-list li, .opportunities-list li {{
            background: #f8f9ff;
            margin: 8px 0;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .strengths-list li {{
            border-left-color: #28a745;
        }}
        
        .opportunities-list li {{
            border-left-color: #ffc107;
        }}
        
        .text-rewrite {{
            background: #f8f9ff;
            padding: 15px;
            border-radius: 6px;
            margin: 12px 0;
            border: 1px solid #e0e0e0;
        }}
        
        .original {{
            background: #fff3cd;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
            border-left: 3px solid #ffc107;
        }}
        
        .improved {{
            background: #d4edda;
            padding: 12px;
            border-radius: 4px;
            margin: 8px 0;
            border-left: 3px solid #28a745;
        }}
        
        .why-better {{
            font-style: italic;
            color: #666;
            margin-top: 8px;
        }}
        
        .competitive-advantages, .success-prediction {{
            background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #28a745;
            margin: 15px 0;
        }}
        
        .actions {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin: 8px;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        
        .print-btn {{
            background: #28a745;
        }}
    </style>
    """
    
    return html_content

def generate_embedded_job_fit_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for job fit analysis results"""
    # Simplified version for embedded display
    match_percentage = result.get('match_percentage', 'N/A')
    requirements_met = result.get('requirements_met', [])
    missing_qualifications = result.get('missing_qualifications', [])
    recommendations = result.get('recommendations', [])
    
    html_content = f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>🎯 Job Fit Analysis</h2>
            <p>How well your resume matches the job requirements</p>
        </div>
        
        <div class="score-section">
            <div class="score">{match_percentage}%</div>
            <div class="score-label">Job Match Score</div>
        </div>
        
        <div class="section">
            <h3>✅ Requirements Met</h3>
            <ul class="strengths-list">
    """
    
    for req in requirements_met:
        html_content += f'<li>{req}</li>'
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="section">
            <h3>❌ Missing Qualifications</h3>
            <ul class="opportunities-list">
    """
    
    for missing in missing_qualifications:
        html_content += f'<li>{missing}</li>'
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="section">
            <h3>💡 Recommendations</h3>
            <ul class="strengths-list">
    """
    
    for rec in recommendations:
        html_content += f'<li>{rec}</li>'
    
    html_content += f"""
            </ul>
        </div>
        
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">🖨️ Print Report</button>
            <a href="/" class="btn">🏠 Return to App</a>
        </div>
    </div>
    
    <style>
        .premium-results {{
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .premium-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }}
        
        .premium-header h2 {{
            color: #667eea;
            margin: 0;
            font-size: 1.8rem;
        }}
        
        .premium-header p {{
            color: #666;
            margin: 10px 0 0 0;
        }}
        
        .score-section {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
            border-radius: 12px;
            border: 2px solid #667eea;
        }}
        
        .score {{
            font-size: 3rem;
            font-weight: 700;
            color: #667eea;
            margin: 0;
        }}
        
        .score-label {{
            font-size: 1.1rem;
            color: #666;
            margin-top: 10px;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h3 {{
            color: #667eea;
            font-size: 1.4rem;
            margin-bottom: 15px;
            border-bottom: 1px solid #667eea;
            padding-bottom: 8px;
        }}
        
        .strengths-list, .opportunities-list {{
            list-style: none;
            padding: 0;
        }}
        
        .strengths-list li, .opportunities-list li {{
            background: #f8f9ff;
            margin: 8px 0;
            padding: 12px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }}
        
        .strengths-list li {{
            border-left-color: #28a745;
        }}
        
        .opportunities-list li {{
            border-left-color: #ffc107;
        }}
        
        .actions {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin: 8px;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        
        .print-btn {{
            background: #28a745;
        }}
    </style>
    """
    
    return html_content

def generate_embedded_cover_letter_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for cover letter results"""
    cover_letter = result.get('cover_letter', '')
    
    html_content = f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>📝 AI-Generated Cover Letter</h2>
            <p>Tailored specifically for your target position</p>
        </div>
        
        <div class="section">
            <h3>Your Cover Letter</h3>
            <div class="cover-letter-content">
                {cover_letter.replace(chr(10), '<br>')}
            </div>
        </div>
        
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">🖨️ Print Cover Letter</button>
            <button class="btn" onclick="copyToClipboard()">📋 Copy to Clipboard</button>
            <a href="/" class="btn">🏠 Return to App</a>
        </div>
    </div>
    
    <style>
        .premium-results {{
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .premium-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }}
        
        .premium-header h2 {{
            color: #667eea;
            margin: 0;
            font-size: 1.8rem;
        }}
        
        .premium-header p {{
            color: #666;
            margin: 10px 0 0 0;
        }}
        
        .section {{
            margin-bottom: 30px;
        }}
        
        .section h3 {{
            color: #667eea;
            font-size: 1.4rem;
            margin-bottom: 15px;
            border-bottom: 1px solid #667eea;
            padding-bottom: 8px;
        }}
        
        .cover-letter-content {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            line-height: 1.6;
            white-space: pre-wrap;
        }}
        
        .actions {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
        }}
        
        .btn {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin: 8px;
            text-decoration: none;
            display: inline-block;
        }}
        
        .btn:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        
        .print-btn {{
            background: #28a745;
        }}
    </style>
    
    <script>
        function copyToClipboard() {{
            const content = document.querySelector('.cover-letter-content').textContent;
            navigator.clipboard.writeText(content).then(() => {{
                alert('Cover letter copied to clipboard!');
            }});
        }}
    </script>
    """
    
    return html_content

def generate_embedded_interview_prep_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for interview prep results"""
    return f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>🎤 Interview Preparation</h2>
            <p>Personalized interview questions and answers</p>
        </div>
        <div class="section">
            <h3>Interview Prep Results</h3>
            <pre>{result}</pre>
        </div>
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">🖨️ Print Report</button>
            <a href="/" class="btn">🏠 Return to App</a>
        </div>
    </div>
    """

def generate_embedded_salary_insights_html(result: dict, analysis_id: str) -> str:
    """Generate embedded HTML for salary insights results"""
    return f"""
    <div class="premium-results">
        <div class="premium-header">
            <h2>💰 Salary Insights</h2>
            <p>Market rate analysis for your role</p>
        </div>
        <div class="section">
            <h3>Salary Insights</h3>
            <pre>{result}</pre>
        </div>
        <div class="actions">
            <button class="btn print-btn" onclick="window.print()">🖨️ Print Report</button>
            <a href="/" class="btn">🏠 Return to App</a>
        </div>
    </div>
    """