"""
Analysis Routes Module

This module handles resume analysis and cover letter generation endpoints.
"""
import logging
from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Optional

from ..config.settings import constants
from ..utils.file_processing import resume_to_text

# Import existing analysis functions (temporary - these should be moved to services)
# We'll import these from the main module for now to avoid breaking changes
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger(__name__)

# Initialize router and limiter
router = APIRouter(prefix="/api")
limiter = Limiter(key_func=get_remote_address)

@router.post("/check-resume")
@limiter.limit(constants.ANALYSIS_RATE_LIMIT)
async def check_resume(
    request: Request,
    file: UploadFile = File(...),
    payment_token: Optional[str] = Form(None),
    job_posting: Optional[str] = Form(None)
):
    """
    Main endpoint for resume analysis
    - Without payment_token: Returns free analysis (job matching if job_posting provided)
    - With payment_token: Returns comprehensive premium analysis
    """
    
    logger.info(f"File upload received: {file.filename}, type: {file.content_type}, payment: {'Yes' if payment_token else 'No'}")
    
    try:
        # Extract text from file
        resume_text = resume_to_text(file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Resume appears to be empty or too short. Please upload a valid resume.")
        
        logger.info(f"Resume processed: {len(resume_text)} characters extracted")
        
        # Import analysis functions from main module (temporary solution)
        from main_vercel import (
            get_ai_analysis_with_retry, 
            get_free_analysis_prompt, 
            get_job_matching_prompt,
            get_paid_analysis_prompt,
            STRIPE_SUCCESS_TOKEN
        )
        
        # Determine analysis type and run appropriate analysis
        if payment_token and payment_token == STRIPE_SUCCESS_TOKEN:
            # Premium analysis
            if job_posting:
                prompt = get_job_matching_prompt(resume_text, job_posting, is_paid=True)
                analysis = await get_ai_analysis_with_retry(prompt)
            else:
                prompt = get_paid_analysis_prompt(resume_text)
                analysis = await get_ai_analysis_with_retry(prompt)
                
            logger.info("Premium analysis completed")
            return JSONResponse(content={
                "status": "success",
                "analysis": analysis,
                "type": "premium",
                "message": "Premium analysis completed successfully!"
            })
        else:
            # Free analysis
            if job_posting:
                prompt = get_job_matching_prompt(resume_text, job_posting, is_paid=False)
                analysis = await get_ai_analysis_with_retry(prompt)
                
                logger.info("Free job matching analysis completed")
                return JSONResponse(content={
                    "status": "success",
                    "analysis": analysis,
                    "type": "job_matching_free",
                    "message": "Free job fit analysis completed!"
                })
            else:
                prompt = get_free_analysis_prompt(resume_text)
                analysis = await get_ai_analysis_with_retry(prompt)
                
                logger.info("Free resume analysis completed")
                return JSONResponse(content={
                    "status": "success", 
                    "analysis": analysis,
                    "type": "free",
                    "message": "Free analysis completed! Upgrade for detailed improvements."
                })
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/generate-cover-letter")
@limiter.limit(constants.ANALYSIS_RATE_LIMIT)
async def generate_cover_letter(request: Request, file: UploadFile = File(...), job_posting: str = Form(...), payment_token: str = Form(None)):
    """Generate hope-driven cover letter based on resume and job posting"""
    
    logger.info(f"Cover letter request: {file.filename}, payment: {'Yes' if payment_token else 'No'}")
    
    try:
        # Extract text from resume
        resume_text = resume_to_text(file)
        
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Resume appears to be empty or too short.")
            
        if not job_posting or len(job_posting.strip()) < 20:
            raise HTTPException(status_code=400, detail="Job posting is too short. Please provide more details.")
        
        # Import functions from main module (temporary)
        from main_vercel import get_ai_analysis_with_retry, STRIPE_SUCCESS_TOKEN
        from prompt_manager import format_prompt
        
        # Determine tier based on payment
        tier = "premium" if (payment_token and payment_token == STRIPE_SUCCESS_TOKEN) else "free"
        
        # Generate cover letter prompt
        prompt = format_prompt("cover_letter", tier, resume_text=resume_text, job_posting=job_posting)
        
        # Get AI analysis
        cover_letter = await get_ai_analysis_with_retry(prompt)
        
        logger.info(f"Cover letter generated ({tier} tier)")
        
        return JSONResponse(content={
            "status": "success",
            "cover_letter": cover_letter,
            "tier": tier,
            "message": f"Cover letter generated successfully! ({tier.title()} tier)"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")

@router.post("/generate-cover-letter-text")
@limiter.limit(constants.ANALYSIS_RATE_LIMIT)
async def generate_cover_letter_text(request: Request, resume_text: str = Form(...), job_posting: str = Form(...), payment_token: str = Form(None)):
    """Generate cover letter from text input (for testing/API use)"""
    
    logger.info(f"Cover letter text request, payment: {'Yes' if payment_token else 'No'}")
    
    try:
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Resume text is too short.")
            
        if not job_posting or len(job_posting.strip()) < 20:
            raise HTTPException(status_code=400, detail="Job posting is too short.")
        
        # Import functions from main module (temporary)
        from main_vercel import get_ai_analysis_with_retry, STRIPE_SUCCESS_TOKEN
        from prompt_manager import format_prompt
        
        # Determine tier based on payment
        tier = "premium" if (payment_token and payment_token == STRIPE_SUCCESS_TOKEN) else "free"
        
        # Generate cover letter prompt
        prompt = format_prompt("cover_letter", tier, resume_text=resume_text, job_posting=job_posting)
        
        # Get AI analysis
        cover_letter = await get_ai_analysis_with_retry(prompt)
        
        logger.info(f"Cover letter generated from text ({tier} tier)")
        
        return JSONResponse(content={
            "status": "success",
            "cover_letter": cover_letter,
            "tier": tier,
            "message": f"Cover letter generated successfully! ({tier.title()} tier)"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter text generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Cover letter generation failed: {str(e)}")