"""
AI Analysis Service

Handles OpenAI integration for resume analysis, job fit analysis, and cover letter generation.
Uses the proven prompts from the original working system.
"""
import json
import logging
import openai
import httpx
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.config import config
from ..core.exceptions import AIAnalysisError

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service for AI-powered resume analysis"""
    
    def __init__(self):
        """Initialize OpenAI client and load prompts"""
        self.client = openai.AsyncOpenAI(api_key=config.openai_api_key, http_client=httpx.AsyncClient())
        self.prompts = self._load_prompts()
        logger.info("Analysis service initialized with OpenAI")
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Load AI prompts from JSON file"""
        try:
            prompts_file = Path(__file__).parent.parent / "data" / "prompts.json"
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            logger.info("AI prompts loaded successfully")
            return prompts_data
            
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            raise AIAnalysisError(f"Could not load AI prompts: {str(e)}")
    
    async def analyze_resume(
        self, 
        resume_text: str, 
        analysis_type: str = "free",
        job_posting: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze resume with AI
        
        Args:
            resume_text: Extracted resume text
            analysis_type: "free" or "premium"
            job_posting: Optional job posting for job fit analysis
            
        Returns:
            Analysis results as dictionary
            
        Raises:
            AIAnalysisError: If analysis fails
        """
        logger.info(f"Starting {analysis_type} resume analysis ({len(resume_text)} characters)")
        
        try:
            # Validate input
            if not resume_text or len(resume_text.strip()) < 50:
                raise AIAnalysisError("Resume text is too short for meaningful analysis")
            
            # Determine analysis type and get appropriate prompt
            if job_posting:
                # Job fit analysis
                prompt_data = self.prompts["job_fit"][analysis_type]
                user_prompt = prompt_data["user_prompt"].format(
                    resume_text=resume_text, 
                    job_posting=job_posting
                )
            else:
                # Regular resume analysis
                prompt_data = self.prompts["resume_analysis"][analysis_type]
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
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=messages,
                temperature=config.openai_temperature,
                max_tokens=config.openai_max_tokens,
                timeout=60  # 60 second timeout
            )
            
            # Extract and parse response
            ai_response = response.choices[0].message.content
            
            try:
                # Clean the response by removing markdown formatting
                cleaned_response = self._clean_json_response(ai_response)
                
                # Parse JSON response
                result = json.loads(cleaned_response)
                logger.info(f"Analysis completed: {analysis_type}")
                return result
                
            except json.JSONDecodeError as e:
                # If JSON parsing fails, return raw response with structure
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"JSON error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                logger.error(f"Raw AI response (first 1000 chars): {ai_response[:1000]}")
                logger.error(f"Cleaned response (first 1000 chars): {cleaned_response[:1000]}")
                logger.error(f"Cleaned response length: {len(cleaned_response)}")
                
                # Try to extract any meaningful content
                return {
                    "analysis_type": analysis_type,
                    "raw_response": ai_response[:500],  # Limit size
                    "cleaned_response": cleaned_response[:500],  # Limit size
                    "error": f"JSON parsing failed: {str(e)}",
                    "timestamp": "2025-09-07T00:00:00Z"
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
        Generate cover letter with AI
        
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
            
            # Get cover letter prompt
            prompt_data = self.prompts["cover_letter"][analysis_type]
            user_prompt = prompt_data["user_prompt"].format(
                resume_text=resume_text,
                job_posting=job_posting
            )
            
            # Prepare messages
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
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=messages,
                temperature=config.openai_temperature,
                max_tokens=config.openai_max_tokens,
                timeout=60
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            
            try:
                # Clean the response by removing markdown formatting
                cleaned_response = self._clean_json_response(ai_response)
                
                result = json.loads(cleaned_response)
                logger.info(f"Cover letter generated: {analysis_type}")
                return result
            except json.JSONDecodeError:
                logger.warning("Cover letter response was not valid JSON")
                return {
                    "analysis_type": analysis_type,
                    "raw_response": ai_response,
                    "error": "Response was not in expected JSON format"
                }
                
        except Exception as e:
            logger.error(f"Cover letter generation failed: {e}")
            if isinstance(e, AIAnalysisError):
                raise
            else:
                raise AIAnalysisError(f"Cover letter generation failed: {str(e)}")
    
    def _clean_json_response(self, response: str) -> str:
        """
        Clean AI response by removing markdown formatting and extracting JSON
        
        Args:
            response: Raw AI response that may contain markdown formatting
            
        Returns:
            Cleaned JSON string
        """
        original_response = response
        logger.debug(f"Cleaning JSON response (length: {len(response)})")
        
        # Remove markdown code blocks
        if response.startswith("```json"):
            # Remove ```json at the beginning and ``` at the end
            response = response[7:]  # Remove ```json
            if response.endswith("```"):
                response = response[:-3]  # Remove ```
        elif response.startswith("```"):
            # Remove generic code blocks
            response = response[3:]  # Remove ```
            if response.endswith("```"):
                response = response[:-3]  # Remove ```
        
        # Remove any leading/trailing whitespace and newlines
        response = response.strip()
        
        # Find the first { and matching } using proper brace counting
        first_brace = response.find('{')
        if first_brace == -1:
            logger.warning("No opening brace found in response")
            return response
        
        # Count braces to find the matching closing brace
        brace_count = 0
        in_string = False
        escape_next = False
        last_brace = -1
        
        for i in range(first_brace, len(response)):
            char = response[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        last_brace = i
                        break
        
        if last_brace != -1:
            json_content = response[first_brace:last_brace + 1]
            logger.debug(f"Extracted JSON content: {json_content[:100]}...")
            return json_content
        else:
            logger.warning("No matching closing brace found")
            # Fallback to original method
            last_brace = response.rfind('}')
            if last_brace > first_brace:
                return response[first_brace:last_brace + 1]
            return response

    def validate_resume_content(self, resume_text: str) -> Dict[str, Any]:
        """
        Validate resume content for analysis
        
        Returns validation result with suggestions
        """
        issues = []
        suggestions = []
        
        text = resume_text.strip()
        
        # Check length
        if len(text) < 50:
            issues.append("Resume text is too short")
            suggestions.append("Upload a complete resume with at least a few sentences")
        elif len(text) < 200:
            issues.append("Resume appears incomplete")
            suggestions.append("Ensure the entire resume content was captured")
        
        # Check for common resume sections
        text_lower = text.lower()
        expected_sections = ["experience", "education", "skills", "work", "employment"]
        found_sections = [section for section in expected_sections if section in text_lower]
        
        if len(found_sections) < 2:
            issues.append("Resume may be missing key sections")
            suggestions.append("Ensure resume includes experience, education, and skills sections")
        
        # Check for contact information
        if not any(indicator in text_lower for indicator in ["email", "@", "phone", "contact"]):
            suggestions.append("Consider adding contact information for completeness")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestions": suggestions,
            "character_count": len(text),
            "estimated_pages": max(1, len(text) // 2000)  # Rough estimate
        }
    
    async def _call_openai(self, prompt: str) -> str:
        """Helper method to call OpenAI with a simple prompt"""
        try:
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=[
                    {"role": "system", "content": "You are a professional resume and career advisor. Provide detailed, actionable advice in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.openai_temperature,
                max_tokens=config.openai_max_tokens,
                timeout=60
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise AIAnalysisError(f"AI service error: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse and clean JSON response from OpenAI"""
        try:
            cleaned_response = self._clean_json_response(response)
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.warning(f"AI response was not valid JSON: {e}")
            logger.warning(f"Raw response: {response[:500]}...")
            # Return a structured fallback response
            return {
                "raw_response": response,
                "error": "Response was not in expected JSON format",
                "fallback_analysis": "AI analysis completed but response format needs adjustment"
            }
    
    async def analyze_job_fit(self, resume_text: str, job_posting: str) -> Dict[str, Any]:
        """Generate job fit analysis comparing resume to job posting"""
        prompt = f"""
        Analyze how well this resume matches the job posting requirements.
        
        RESUME:
        {resume_text}
        
        JOB POSTING:
        {job_posting}
        
        Provide a comprehensive job fit analysis including:
        1. Match percentage (0-100%)
        2. Key requirements met
        3. Missing qualifications
        4. Strengths that align with the role
        5. Areas for improvement
        6. Specific recommendations to improve fit
        
        Return as JSON with keys: match_percentage, requirements_met, missing_qualifications, strengths, improvements, recommendations
        """
        
        response = await self._call_openai(prompt)
        return self._parse_json_response(response)
    
    async def generate_cover_letter(self, resume_text: str, job_posting: str) -> Dict[str, Any]:
        """Generate a tailored cover letter based on resume and job posting"""
        prompt = f"""
        Generate a professional cover letter tailored to this job posting using the resume information.
        
        RESUME:
        {resume_text}
        
        JOB POSTING:
        {job_posting}
        
        Create a compelling cover letter that:
        1. Addresses the hiring manager professionally
        2. Highlights relevant experience from the resume
        3. Shows understanding of the role requirements
        4. Demonstrates enthusiasm for the position
        5. Includes a strong closing
        
        Return as JSON with keys: cover_letter, key_points_highlighted, tone, word_count
        """
        
        response = await self._call_openai(prompt)
        return self._parse_json_response(response)
    
    async def enhance_resume(self, resume_text: str, job_posting: str) -> Dict[str, Any]:
        """Provide resume enhancement suggestions based on job posting"""
        prompt = f"""
        Analyze this resume against the job posting and provide specific enhancement suggestions.
        
        RESUME:
        {resume_text}
        
        JOB POSTING:
        {job_posting}
        
        Provide detailed enhancement recommendations including:
        1. Skills to add or emphasize
        2. Experience descriptions to improve
        3. Keywords to include
        4. Formatting improvements
        5. Content additions
        6. Specific examples of improved sections
        
        Return as JSON with keys: enhancement_score, skills_to_add, improved_sections, keywords_to_include, formatting_suggestions, sample_improvements
        """
        
        response = await self._call_openai(prompt)
        return self._parse_json_response(response)
    
    async def generate_interview_prep(self, resume_text: str, job_posting: str = None) -> Dict[str, Any]:
        """Generate interview preparation materials"""
        job_context = f" for this position: {job_posting}" if job_posting else ""
        
        prompt = f"""
        Generate comprehensive interview preparation materials based on this resume{job_context}.
        
        RESUME:
        {resume_text}
        
        Create interview preparation including:
        1. Common questions for this role/background
        2. Behavioral questions with STAR method examples
        3. Technical questions (if applicable)
        4. Questions to ask the interviewer
        5. Key talking points from the resume
        6. Potential weaknesses to address
        
        Return as JSON with keys: common_questions, behavioral_questions, technical_questions, questions_to_ask, talking_points, weakness_strategies
        """
        
        response = await self._call_openai(prompt)
        return self._parse_json_response(response)
    
    async def generate_salary_insights(self, resume_text: str) -> Dict[str, Any]:
        """Generate salary insights and market analysis"""
        prompt = f"""
        Analyze this resume and provide salary insights and market analysis.
        
        RESUME:
        {resume_text}
        
        Provide comprehensive salary insights including:
        1. Estimated salary range based on experience
        2. Market comparison data
        3. Factors affecting salary potential
        4. Negotiation tips
        5. Career progression salary outlook
        6. Industry-specific insights
        
        Return as JSON with keys: salary_range, market_comparison, salary_factors, negotiation_tips, career_outlook, industry_insights
        """
        
        response = await self._call_openai(prompt)
        return self._parse_json_response(response)
    
    async def analyze_resume_premium(self, resume_text: str, job_posting: str = None) -> Dict[str, Any]:
        """Generate premium resume analysis with enhanced insights"""
        job_context = f"\n\nJOB POSTING (for context):\n{job_posting}" if job_posting else ""
        
        prompt = f"""
        Provide a comprehensive premium resume analysis that helps this candidate stand out.
        
        RESUME:
        {resume_text}{job_context}
        
        Analyze and provide:
        1. Overall score (70-95 range)
        2. Key strengths with specific impact
        3. Detailed improvement opportunities
        4. ATS optimization suggestions
        5. Content enhancement recommendations
        6. Specific text improvements with examples - CRITICAL: For text_rewrites, you MUST find and copy the exact current text from the resume sections (like Professional Summary, Experience descriptions, etc.) for the "original" field. Do not use placeholder text.
        
        Return as JSON with this exact structure:
        {{
            "overall_score": 85,
            "strength_highlights": [
                "Specific strength 1 with impact",
                "Specific strength 2 with value",
                "Specific strength 3 with advantage"
            ],
            "improvement_opportunities": [
                "Opportunity 1: Specific actionable improvement",
                "Opportunity 2: Quick win that makes big difference",
                "Opportunity 3: Strategic enhancement for maximum impact"
            ],
            "ats_optimization": {{
                "current_strength": "What's already working well",
                "enhancement_opportunities": ["Specific ATS improvements"],
                "impact_prediction": "How changes will improve success rate"
            }},
            "content_enhancement": {{
                "strong_sections": ["What's already compelling"],
                "growth_areas": ["How to make good sections great"],
                "strategic_additions": ["What to add for maximum impact"]
            }},
            "text_rewrites": [
                {{
                    "section": "Professional Summary",
                    "original": "Copy the exact text from the PROFESSIONAL SUMMARY section in the resume above",
                    "improved": "Powerful rewrite showcasing value",
                    "why_better": "Explanation of improvement's impact"
                }},
                {{
                    "section": "Experience Description",
                    "original": "Copy the exact text from a relevant experience bullet point in the resume above",
                    "improved": "Enhanced version with quantified impact",
                    "why_better": "Explanation of improvement's impact"
                }}
            ],
            "competitive_advantages": "What makes them uniquely valuable",
            "success_prediction": "Encouraging forecast of job search success"
        }}
        """
        
        response = await self._call_openai(prompt)
        return self._parse_json_response(response)

# Singleton instance
analysis_service = AnalysisService()