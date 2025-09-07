"""
Simplified AI Analysis Service v2

Uses individual prompt files instead of complex JSON parsing.
Increased timeout to 180 seconds for better Railway compliance.
"""

import json
import logging
import openai
import httpx
from typing import Dict, Any, Optional

from ..core.config import config
from ..core.exceptions import AIAnalysisError
from .prompt_loader import prompt_loader

logger = logging.getLogger(__name__)

class AnalysisServiceV2:
    """Simplified service for AI-powered resume analysis"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = openai.AsyncOpenAI(
            api_key=config.openai_api_key, 
            http_client=httpx.AsyncClient()
        )
        logger.info("Analysis service v2 initialized with OpenAI")
    
    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON"""
        if not response:
            return "{}"
        
        # Remove markdown code blocks
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        
        response = response.strip()
        
        # Find JSON object boundaries
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            response = response[start_idx:end_idx + 1]
        
        return response
    
    async def analyze_resume(
        self, 
        resume_text: str, 
        analysis_type: str = "free",
        job_posting: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze resume with AI using simplified prompts
        
        Args:
            resume_text: Extracted resume text
            analysis_type: "free" or "premium"
            job_posting: Optional job posting for job fit analysis
            
        Returns:
            Analysis results as dictionary
        """
        logger.info(f"Starting {analysis_type} resume analysis ({len(resume_text)} characters)")
        
        try:
            # Validate input
            if not resume_text or len(resume_text.strip()) < 50:
                raise AIAnalysisError("Resume text is too short for meaningful analysis")
            
            # Get prompt from individual files
            if job_posting:
                # Job fit analysis
                prompt_data = prompt_loader.get_job_fit_prompt(is_premium=(analysis_type == "premium"))
                user_prompt = prompt_data["user_prompt"].format(
                    resume_text=resume_text, 
                    job_posting=job_posting
                )
            else:
                # Regular resume analysis
                prompt_data = prompt_loader.get_resume_analysis_prompt(is_premium=(analysis_type == "premium"))
                user_prompt = prompt_data["user_prompt"].format(resume_text=resume_text)
            
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": prompt_data["system_prompt"]
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
            
            logger.info(f"🚀 Calling OpenAI with {analysis_type} prompt")
            
            # Call OpenAI API with increased timeout
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=messages,
                temperature=config.openai_temperature,
                max_tokens=config.openai_max_tokens,
                timeout=180  # Increased to 180 seconds for Railway compliance
            )
            
            # Extract and parse response
            ai_response = response.choices[0].message.content
            logger.info(f"✅ Received AI response ({len(ai_response)} characters)")
            
            # Clean and parse JSON response
            cleaned_response = self._clean_json_response(ai_response)
            
            try:
                result = json.loads(cleaned_response)
                logger.info(f"✅ Analysis completed successfully: {analysis_type}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed: {e}")
                logger.error(f"Raw response: {ai_response[:500]}")
                logger.error(f"Cleaned response: {cleaned_response[:500]}")
                
                # Return structured error response
                return {
                    "error": "json_parsing_error",
                    "message": f"Failed to parse AI response: {str(e)}",
                    "raw_response": ai_response[:500],
                    "analysis_type": analysis_type
                }
            
        except openai.RateLimitError:
            logger.error("OpenAI rate limit exceeded")
            raise AIAnalysisError("AI service is temporarily overloaded. Please try again in a few minutes.")
        
        except openai.AuthenticationError:
            logger.error("OpenAI authentication failed")
            raise AIAnalysisError("AI service authentication failed. Please contact support.")
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise AIAnalysisError("AI service is temporarily unavailable. Please try again later.")
        
        except Exception as e:
            logger.error(f"Unexpected error in analysis: {e}")
            raise AIAnalysisError(f"Analysis failed: {str(e)}")
    
    async def generate_cover_letter(
        self, 
        resume_text: str, 
        job_posting: str,
        analysis_type: str = "free"
    ) -> Dict[str, Any]:
        """
        Generate cover letter with AI using simplified prompts
        
        Args:
            resume_text: Extracted resume text
            job_posting: Job posting text
            analysis_type: "free" or "premium"
            
        Returns:
            Cover letter results as dictionary
        """
        logger.info(f"Starting {analysis_type} cover letter generation")
        
        try:
            # Validate inputs
            if not resume_text or len(resume_text.strip()) < 50:
                raise AIAnalysisError("Resume text is too short for cover letter generation")
            
            if not job_posting or len(job_posting.strip()) < 20:
                raise AIAnalysisError("Job posting is too short for meaningful cover letter")
            
            # Get cover letter prompt from individual files
            prompt_data = prompt_loader.get_cover_letter_prompt(is_premium=(analysis_type == "premium"))
            user_prompt = prompt_data["user_prompt"].format(
                resume_text=resume_text,
                job_posting=job_posting
            )
            
            # Prepare messages for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": prompt_data["system_prompt"]
                },
                {
                    "role": "user", 
                    "content": user_prompt
                }
            ]
            
            logger.info(f"🚀 Calling OpenAI for cover letter generation")
            
            # Call OpenAI API with increased timeout
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=messages,
                temperature=config.openai_temperature,
                max_tokens=config.openai_max_tokens,
                timeout=180  # Increased to 180 seconds
            )
            
            # Extract and parse response
            ai_response = response.choices[0].message.content
            logger.info(f"✅ Received cover letter response ({len(ai_response)} characters)")
            
            # Clean and parse JSON response
            cleaned_response = self._clean_json_response(ai_response)
            
            try:
                result = json.loads(cleaned_response)
                logger.info(f"✅ Cover letter generation completed successfully: {analysis_type}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed: {e}")
                logger.error(f"Raw response: {ai_response[:500]}")
                logger.error(f"Cleaned response: {cleaned_response[:500]}")
                
                # Return structured error response
                return {
                    "error": "json_parsing_error",
                    "message": f"Failed to parse AI response: {str(e)}",
                    "raw_response": ai_response[:500],
                    "analysis_type": analysis_type
                }
            
        except Exception as e:
            logger.error(f"Unexpected error in cover letter generation: {e}")
            raise AIAnalysisError(f"Cover letter generation failed: {str(e)}")
    
    async def analyze_resume_premium(self, resume_text: str) -> Dict[str, Any]:
        """Premium resume analysis - alias for analyze_resume with premium=True"""
        return await self.analyze_resume(resume_text, analysis_type="premium")
    
    async def analyze_job_fit(self, resume_text: str, job_posting: str, analysis_type: str = "free") -> Dict[str, Any]:
        """Job fit analysis - alias for analyze_resume with job_posting"""
        return await self.analyze_resume(resume_text, analysis_type=analysis_type, job_posting=job_posting)
    
    async def enhance_resume(self, resume_text: str) -> Dict[str, Any]:
        """Resume enhancement - alias for premium analysis"""
        return await self.analyze_resume(resume_text, analysis_type="premium")
    
    async def generate_interview_prep(self, resume_text: str) -> Dict[str, Any]:
        """Generate interview preparation - placeholder implementation"""
        logger.info("Generating interview preparation")
        return {
            "interview_prep": "Interview preparation feature coming soon",
            "analysis_type": "interview_prep",
            "timestamp": "2025-09-07T00:00:00Z"
        }
    
    async def generate_salary_insights(self, resume_text: str) -> Dict[str, Any]:
        """Generate salary insights - placeholder implementation"""
        logger.info("Generating salary insights")
        return {
            "salary_insights": "Salary insights feature coming soon",
            "analysis_type": "salary_insights", 
            "timestamp": "2025-09-07T00:00:00Z"
        }
    
    def validate_resume_content(self, resume_text: str) -> Dict[str, Any]:
        """Validate resume content - simple validation"""
        if not resume_text or len(resume_text.strip()) < 50:
            return {
                "valid": False,
                "error": "Resume text is too short (minimum 50 characters)"
            }
        
        return {
            "valid": True,
            "character_count": len(resume_text),
            "word_count": len(resume_text.split())
        }

# Global instance
analysis_service_v2 = AnalysisServiceV2()
