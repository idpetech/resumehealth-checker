"""
Background task processing for long-running AI analysis
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from ..core.database import AnalysisDB
from ..services.analysis import analysis_service

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """Simple background task manager for GPT-5 analysis"""
    
    def __init__(self):
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_premium_analysis(
        self, 
        analysis_id: str, 
        product_type: str,
        resume_text: str,
        job_posting: Optional[str] = None
    ) -> bool:
        """
        Start premium analysis in background
        
        Returns:
            True if task was started successfully
        """
        try:
            # Check if task already running for this analysis
            if analysis_id in self.running_tasks:
                existing_task = self.running_tasks[analysis_id]
                if not existing_task.done():
                    logger.info(f"Analysis {analysis_id} already in progress")
                    return True
                else:
                    # Clean up completed task
                    del self.running_tasks[analysis_id]
            
            # Start new background task
            task = asyncio.create_task(
                self._run_premium_analysis(analysis_id, product_type, resume_text, job_posting)
            )
            self.running_tasks[analysis_id] = task
            
            logger.info(f"Started background analysis for {analysis_id} ({product_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start background analysis for {analysis_id}: {e}")
            return False
    
    async def _run_premium_analysis(
        self,
        analysis_id: str,
        product_type: str, 
        resume_text: str,
        job_posting: Optional[str] = None
    ):
        """
        Execute the premium analysis in background
        """
        try:
            logger.info(f"🚀 Starting background {product_type} analysis for {analysis_id}")
            
            # Generate premium result based on product type
            if product_type == "resume_analysis":
                premium_result = await analysis_service.analyze_resume(
                    resume_text, 
                    'premium'
                )
            elif product_type == "job_fit_analysis":
                if not job_posting:
                    raise ValueError("Job posting required for job fit analysis")
                premium_result = await analysis_service.analyze_resume(
                    resume_text, 
                    'premium',
                    job_posting
                )
            elif product_type == "cover_letter":
                if not job_posting:
                    raise ValueError("Job posting required for cover letter generation")
                premium_result = await analysis_service.generate_cover_letter(
                    resume_text, 
                    job_posting
                )
            elif product_type == "resume_rewrite":
                if not job_posting:
                    raise ValueError("Job posting required for resume rewrite")
                premium_result = await analysis_service.complete_resume_rewrite(
                    resume_text, 
                    job_posting
                )
            elif product_type == "mock_interview":
                if not job_posting:
                    raise ValueError("Job posting required for mock interview")
                premium_result = await analysis_service.generate_mock_interview_premium(
                    resume_text, 
                    job_posting
                )
            else:
                raise ValueError(f"Unknown product type: {product_type}")
            
            # Save result to database
            if premium_result:
                AnalysisDB.update_premium_result(analysis_id, premium_result)
                logger.info(f"✅ Background {product_type} analysis completed for {analysis_id}")
            else:
                error_result = {
                    "error": f"Premium {product_type} generation failed",
                    "message": "Our AI analysis service returned an empty result. Please contact support.",
                    "analysis_id": analysis_id
                }
                AnalysisDB.update_premium_result(analysis_id, error_result)
                logger.error(f"❌ Background {product_type} analysis returned empty result for {analysis_id}")
            
        except Exception as e:
            logger.error(f"❌ Background {product_type} analysis failed for {analysis_id}: {e}")
            
            # Save error result to database
            error_result = {
                "error": f"Premium {product_type} generation failed",
                "message": "Our AI analysis service encountered an error. Please contact support.",
                "technical_details": str(e),
                "analysis_id": analysis_id
            }
            AnalysisDB.update_premium_result(analysis_id, error_result)
            
        finally:
            # Clean up task reference
            if analysis_id in self.running_tasks:
                del self.running_tasks[analysis_id]
    
    def get_task_status(self, analysis_id: str) -> str:
        """
        Get status of background task
        
        Returns:
            "running", "completed", or "not_found"
        """
        if analysis_id in self.running_tasks:
            task = self.running_tasks[analysis_id]
            if task.done():
                # Clean up completed task
                del self.running_tasks[analysis_id]
                return "completed"
            else:
                return "running"
        else:
            return "not_found"
    
    def cleanup_completed_tasks(self):
        """Remove completed tasks from tracking"""
        completed_tasks = [
            analysis_id for analysis_id, task in self.running_tasks.items() 
            if task.done()
        ]
        
        for analysis_id in completed_tasks:
            del self.running_tasks[analysis_id]
        
        if completed_tasks:
            logger.info(f"Cleaned up {len(completed_tasks)} completed background tasks")

# Global task manager instance
task_manager = BackgroundTaskManager()