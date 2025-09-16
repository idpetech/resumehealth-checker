"""
Analysis Routes for Resume Health Checker v4.0

All analysis-related endpoints including resume analysis, job fit analysis, 
cover letter generation, resume rewrites, and mock interviews.
"""
import logging
import datetime
from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from ..core.database import AnalysisDB
from ..core.exceptions import FileProcessingError, AIAnalysisError, validate_file_upload
from ..services.files import file_service
from ..services.analysis import analysis_service
from ..services.geo import geo_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

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
            # Set payment status to 'free' to allow access to free results
            AnalysisDB.update_payment_status(analysis_id, 'free')
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
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
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
        elif product_type == "resume_rewrite":
            if not job_posting:
                raise HTTPException(status_code=400, detail="Job posting required for resume rewrite")
            result = await analysis_service.complete_resume_rewrite(
                analysis['resume_text'], 
                job_posting
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid product type: {product_type}")
        
        # Store the premium result
        AnalysisDB.update_premium_result(analysis_id, result)
        
        return {
            "analysis_id": analysis_id,
            "product_type": product_type,
            "result": result,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Premium service error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "premium_service_error", "message": str(e)}
        )

@router.post("/rewrite-preview")
async def preview_resume_rewrite(
    request: Request,
    file: UploadFile = File(...),
    job_posting: str = Form(...)
):
    """
    Generate free preview of resume rewrite potential
    
    - file: PDF, DOCX, or TXT resume file  
    - job_posting: Target job posting text for optimization
    """
    logger.info(f"Resume rewrite preview request: {file.filename}")
    
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
        
        # Validate job posting
        if not job_posting or len(job_posting.strip()) < 20:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_job_posting",
                    "message": "Job posting must be at least 20 characters long"
                }
            )
        
        # Generate rewrite preview
        result = await analysis_service.preview_resume_rewrite(
            resume_text, job_posting.strip()
        )
        
        # Create analysis record
        analysis_id = AnalysisDB.create(
            filename=file.filename,
            file_size=len(file_content),
            resume_text=resume_text,
            analysis_type="rewrite_preview"
        )
        
        # Store job posting for potential premium upgrade
        AnalysisDB.update_job_posting(analysis_id, job_posting.strip())
        
        # Store free result
        AnalysisDB.update_free_result(analysis_id, result)
        
        # Get region info for pricing context
        region_info = geo_service.detect_region_from_request(request)
        
        return {
            "analysis_id": analysis_id,
            "analysis_type": "rewrite_preview",
            "result": result,
            "validation": validation,
            "region_info": region_info,
            "upgrade_options": {
                "complete_rewrite": {
                    "description": "Get the complete rewritten resume optimized for this job",
                    "includes": ["Full resume rewrite", "ATS optimization", "Keyword integration", "Multi-format output"]
                }
            },
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
    except FileProcessingError as e:
        logger.error(f"File processing failed: {e}")
        return JSONResponse(
            status_code=400,
            content={"error": "file_processing_error", "message": str(e)}
        )
    
    except AIAnalysisError as e:
        logger.error(f"Resume rewrite preview failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "ai_analysis_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in rewrite preview: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Resume rewrite preview failed unexpectedly"}
        )

@router.get("/premium/resume-rewrite/{analysis_id}")
async def get_premium_resume_rewrite(analysis_id: str):
    """
    Get premium complete resume rewrite after successful payment
    
    - analysis_id: ID of the analysis with paid status
    """
    logger.info(f"Premium resume rewrite request: {analysis_id}")
    
    try:
        # Get analysis data
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if payment was successful
        if analysis.get('payment_status') != 'paid':
            raise HTTPException(status_code=402, detail="Payment required for complete resume rewrite")
        
        # Get job posting (required for rewrite)
        job_posting = analysis.get('job_posting')
        if not job_posting:
            raise HTTPException(status_code=400, detail="Job posting required for resume rewrite")
        
        # Generate complete premium resume rewrite
        result = await analysis_service.complete_resume_rewrite(
            analysis['resume_text'], 
            job_posting
        )
        
        # Store the premium result
        AnalysisDB.update_premium_result(analysis_id, result)
        
        return {
            "analysis_id": analysis_id,
            "product_type": "resume_rewrite",
            "result": result,
            "download_options": {
                "formats": ["PDF", "DOCX", "TXT"],
                "note": "Multi-format downloads available in future update"
            },
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Premium resume rewrite error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "premium_rewrite_error", "message": str(e)}
        )

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

@router.post("/generate-mock-interview-preview")
async def generate_mock_interview_preview(
    request: Request,
    analysis_id: str = Form(...),
    job_posting: str = Form(...)
):
    """Generate free mock interview preview"""
    try:
        # Get analysis
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Generate mock interview preview
        interview_preview = await analysis_service.generate_mock_interview_preview(
            analysis['resume_text'],
            job_posting
        )
        
        return {
            "analysis_id": analysis_id,
            "interview_preview": interview_preview,
            "analysis_type": "free",
            "product_type": "mock_interview"
        }
        
    except AIAnalysisError as e:
        logger.error(f"Mock interview preview generation failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "ai_analysis_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Mock interview preview error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Mock interview preview generation failed"}
        )

@router.post("/generate-mock-interview-premium")  
async def generate_mock_interview_premium(
    request: Request,
    analysis_id: str = Form(...),
    job_posting: str = Form(...)
):
    """Generate premium mock interview simulation"""
    try:
        # Get analysis
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Check if payment was successful for premium features
        if analysis.get('payment_status') != 'paid':
            raise HTTPException(status_code=402, detail="Payment required for premium mock interview")
        
        # Generate premium mock interview
        interview_simulation = await analysis_service.generate_mock_interview_premium(
            analysis['resume_text'],
            job_posting
        )
        
        # Store the premium result
        AnalysisDB.update_premium_result(analysis_id, interview_simulation)
        
        return {
            "analysis_id": analysis_id,
            "interview_simulation": interview_simulation,
            "analysis_type": "premium",
            "product_type": "mock_interview",
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except AIAnalysisError as e:
        logger.error(f"Premium mock interview generation failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"error": "ai_analysis_error", "message": str(e)}
        )
    
    except Exception as e:
        logger.error(f"Premium mock interview error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Premium mock interview generation failed"}
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