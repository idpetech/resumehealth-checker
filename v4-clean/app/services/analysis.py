"""
AI Analysis Service

Handles OpenAI integration for resume analysis, job fit analysis, and cover letter generation.
Uses the proven prompts from the original working system.
"""
import json
import logging
import openai
import httpx
import re
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
        """Load AI prompts from JSON file using strict parsing"""
        try:
            prompts_file = Path(__file__).parent.parent / "data" / "prompts.json"
            logger.info(f"🔍 STRICT PROMPTS: Loading from: {prompts_file}")
            logger.info(f"🔍 STRICT PROMPTS: File exists: {prompts_file.exists()}")
            logger.info(f"🔍 STRICT PROMPTS: File size: {prompts_file.stat().st_size if prompts_file.exists() else 'N/A'} bytes")
            
            if not prompts_file.exists():
                raise AIAnalysisError(f"Prompts file not found: {prompts_file}")
            
            # Read the raw file content first
            with open(prompts_file, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            
            logger.info(f"🔍 STRICT PROMPTS: Raw content length: {len(raw_content)}")
            logger.info(f"🔍 STRICT PROMPTS: First 200 chars: {repr(raw_content[:200])}")
            
            # Use strict JSON parsing
            try:
                prompts_data = json.loads(raw_content)
                logger.info("✅ STRICT PROMPTS: JSON parsing successful")
            except json.JSONDecodeError as e:
                logger.error(f"❌ STRICT PROMPTS: JSON decode error: {e}")
                logger.error(f"❌ STRICT PROMPTS: Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
                logger.error(f"❌ STRICT PROMPTS: Error line: {e.lineno if hasattr(e, 'lineno') else 'unknown'}")
                logger.error(f"❌ STRICT PROMPTS: Error column: {e.colno if hasattr(e, 'colno') else 'unknown'}")
                
                # Show context around the error
                if hasattr(e, 'pos') and e.pos:
                    start = max(0, e.pos - 100)
                    end = min(len(raw_content), e.pos + 100)
                    error_context = raw_content[start:end]
                    logger.error(f"❌ STRICT PROMPTS: Error context: {repr(error_context)}")
                
                raise AIAnalysisError(f"Invalid JSON in prompts file: {str(e)}")
            
            # Validate the structure
            required_keys = ["resume_analysis", "job_fit", "cover_letter"]
            for key in required_keys:
                if key not in prompts_data:
                    raise AIAnalysisError(f"Missing required section '{key}' in prompts.json")
                
                if "free" not in prompts_data[key]:
                    raise AIAnalysisError(f"Missing 'free' prompts in section '{key}'")
                
                if "premium" not in prompts_data[key]:
                    raise AIAnalysisError(f"Missing 'premium' prompts in section '{key}'")
            
            # Validate prompt structure
            for section_name, section in prompts_data.items():
                if isinstance(section, dict) and "free" in section:
                    for tier in ["free", "premium"]:
                        if tier in section:
                            tier_data = section[tier]
                            if "system_prompt" not in tier_data:
                                raise AIAnalysisError(f"Missing 'system_prompt' in {section_name}.{tier}")
                            if "user_prompt" not in tier_data:
                                raise AIAnalysisError(f"Missing 'user_prompt' in {section_name}.{tier}")
            
            logger.info("✅ STRICT PROMPTS: Structure validation successful")
            logger.info(f"✅ STRICT PROMPTS: Loaded {len(prompts_data)} sections")
            
            return prompts_data
            
        except AIAnalysisError:
            # Re-raise our custom errors
            raise
        except FileNotFoundError as e:
            logger.error(f"❌ STRICT PROMPTS: File not found: {e}")
            raise AIAnalysisError(f"Prompts file not found: {prompts_file}")
        except PermissionError as e:
            logger.error(f"❌ STRICT PROMPTS: Permission denied: {e}")
            raise AIAnalysisError(f"Cannot read prompts file (permission denied): {prompts_file}")
        except Exception as e:
            logger.error(f"❌ STRICT PROMPTS: Unexpected error: {e}")
            logger.error(f"❌ STRICT PROMPTS: Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ STRICT PROMPTS: Traceback: {traceback.format_exc()}")
            raise AIAnalysisError(f"Failed to load AI prompts: {str(e)}")
    
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
                timeout=30  # Reduced to 30 second timeout for better UX
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
                import datetime
                return {
                    "analysis_type": analysis_type,
                    "raw_response": ai_response[:500],  # Limit size
                    "cleaned_response": cleaned_response[:500],  # Limit size
                    "error": f"JSON parsing failed: {str(e)}",
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
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
    
    def _strict_json_parse(self, response: str) -> Dict[str, Any]:
        """
        STRICT JSON parsing with comprehensive validation and multiple extraction methods
        
        Args:
            response: Raw AI response that may contain JSON
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            AIAnalysisError: If JSON cannot be extracted or parsed
        """
        import re
        
        logger.info(f"🔍 STRICT PARSING: Input response length: {len(response)}")
        logger.info(f"🔍 STRICT PARSING: First 200 chars: {repr(response[:200])}")
        
        # Method 1: Try direct JSON parsing (cleanest responses)
        try:
            result = json.loads(response.strip())
            logger.info("✅ STRICT PARSING: Method 1 - Direct parsing successful")
            return result
        except json.JSONDecodeError:
            logger.info("❌ STRICT PARSING: Method 1 - Direct parsing failed")
        
        # Method 2: Remove markdown blocks and try again
        cleaned = response
        if "```json" in cleaned:
            # Simple approach: Find ```json and extract everything after it until ``` or end of string
            json_start = cleaned.find("```json")
            if json_start != -1:
                # Find the start of actual JSON (after ```json and any whitespace)
                json_content_start = json_start + 7  # len("```json")
                while json_content_start < len(cleaned) and cleaned[json_content_start] in ' \n\t':
                    json_content_start += 1
                
                # Find the end (look for closing ``` or use end of string)
                json_content_end = len(cleaned)
                closing_backticks = cleaned.find("```", json_content_start)
                if closing_backticks != -1:
                    json_content_end = closing_backticks
                
                cleaned = cleaned[json_content_start:json_content_end].strip()
                logger.info("🔍 STRICT PARSING: Extracted from ```json blocks (simple method)")
                logger.info(f"🔍 STRICT PARSING: Extracted length: {len(cleaned)}")
                logger.info(f"🔍 STRICT PARSING: Extracted first 200 chars: {repr(cleaned[:200])}")
        elif "```" in cleaned:
            # Extract content between generic ```
            pattern = r'```\s*(.*?)\s*```'
            match = re.search(pattern, cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
                logger.info("🔍 STRICT PARSING: Extracted from generic ``` blocks")
        
        try:
            result = json.loads(cleaned)
            logger.info("✅ STRICT PARSING: Method 2 - Markdown removal successful")
            return result
        except json.JSONDecodeError as e:
            logger.info(f"❌ STRICT PARSING: Method 2 - Markdown removal failed: {str(e)}")
            logger.info(f"🔍 STRICT PARSING: Error at position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
            logger.info(f"🔍 STRICT PARSING: JSON length: {len(cleaned)}")
            logger.info(f"🔍 STRICT PARSING: Failed to parse: {repr(cleaned[:200])}")
            
            # Show what's near the error position
            if hasattr(e, 'pos') and e.pos:
                error_pos = e.pos
                start = max(0, error_pos - 50)
                end = min(len(cleaned), error_pos + 50)
                logger.info(f"🔍 STRICT PARSING: Context around error: {repr(cleaned[start:end])}")
                logger.info(f"🔍 STRICT PARSING: Last 100 chars: {repr(cleaned[-100:])}")
            
            # Try to fix common JSON issues
            if "Unterminated string" in str(e):
                logger.info("🔍 STRICT PARSING: Attempting to fix unterminated strings")
                # Try to fix by adding closing quote and bracket/brace
                fixed_attempts = [
                    cleaned + '"}]}}',  # Most common case - unterminated string in nested structure
                    cleaned + '"}}',    # Simple unterminated string at end
                    cleaned + '}',      # Missing closing brace
                ]
                
                for i, attempt in enumerate(fixed_attempts):
                    try:
                        result = json.loads(attempt)
                        logger.info(f"✅ STRICT PARSING: Method 2 - JSON repair successful (fix {i+1})")
                        return result
                    except json.JSONDecodeError:
                        continue
                
                logger.info("❌ STRICT PARSING: All JSON repair attempts failed")
        
        # Method 3: Character-by-character brace matching (most robust for nested JSON)
        first_brace = response.find('{')
        if first_brace != -1:
            brace_count = 0
            in_string = False
            escape_next = False
            
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
                            candidate = response[first_brace:i + 1]
                            try:
                                result = json.loads(candidate)
                                logger.info("✅ STRICT PARSING: Method 3 - Brace matching successful")
                                logger.info(f"🔍 STRICT PARSING: Extracted: {candidate[:100]}...")
                                return result
                            except json.JSONDecodeError:
                                logger.info("❌ STRICT PARSING: Method 3 - Brace matching found invalid JSON")
                                break
        
        logger.info("❌ STRICT PARSING: Method 3 - Brace matching failed")
        
        # Method 4: Find JSON object using regex (fallback)
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested objects (as fallback)
        ]
        
        for i, pattern in enumerate(json_patterns, 4):
            matches = re.finditer(pattern, response, re.DOTALL)
            for match in matches:
                candidate = match.group(0)
                try:
                    result = json.loads(candidate)
                    logger.info(f"✅ STRICT PARSING: Method {i} - Regex pattern successful")
                    logger.info(f"🔍 STRICT PARSING: Extracted: {candidate[:100]}...")
                    return result
                except json.JSONDecodeError:
                    continue
            logger.info(f"❌ STRICT PARSING: Method {i} - Regex pattern failed")
        
        # All parsing methods failed
        
        logger.error("❌ STRICT PARSING: All methods failed")
        logger.error(f"🔍 STRICT PARSING: Full response: {repr(response)}")
        
        # Last resort: Try to fix common JSON issues
        fixed_attempts = [
            response.replace("'", '"'),  # Single quotes to double quotes
            response.replace('\n', '').replace('\t', ''),  # Remove whitespace
            re.sub(r',\s*}', '}', response),  # Remove trailing commas
            re.sub(r',\s*]', ']', response),  # Remove trailing commas in arrays
        ]
        
        for i, attempt in enumerate(fixed_attempts):
            try:
                # Find JSON in the fixed attempt
                first_brace = attempt.find('{')
                last_brace = attempt.rfind('}')
                if first_brace != -1 and last_brace > first_brace:
                    candidate = attempt[first_brace:last_brace + 1]
                    result = json.loads(candidate)
                    logger.info(f"✅ STRICT PARSING: Fix attempt {i+1} successful")
                    return result
            except json.JSONDecodeError:
                continue
        
        # Complete failure - return structured error
        raise AIAnalysisError(f"Failed to parse JSON from AI response after trying all methods. Response length: {len(response)}")
    
    def _clean_json_response(self, response: str) -> str:
        """
        Legacy method - now calls strict parser and returns JSON string
        Kept for backward compatibility
        """
        try:
            parsed = self._strict_json_parse(response)
            return json.dumps(parsed)
        except AIAnalysisError:
            # Return original response if parsing fails
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
    
    def _parse_mock_interview_json(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """
        Specialized JSON parser for mock interview responses
        Handles large responses with multiple questions and robust error recovery
        """
        import re
        
        logger.info(f"🎭 MOCK INTERVIEW PARSING: Starting specialized parser for {analysis_type}")
        logger.info(f"🎭 MOCK INTERVIEW PARSING: Response length: {len(response)}")
        
        # First, try the standard parsing
        try:
            result = self._strict_json_parse(response)
            logger.info("🎭 MOCK INTERVIEW PARSING: Standard parsing successful")
            return result
        except AIAnalysisError as e:
            logger.warning(f"🎭 MOCK INTERVIEW PARSING: Standard parsing failed: {e}")
        
        # If standard parsing fails, use mock interview-specific recovery
        logger.info("🎭 MOCK INTERVIEW PARSING: Attempting specialized recovery")
        
        # Remove markdown formatting
        cleaned = response
        if "```json" in cleaned:
            json_start = cleaned.find("```json")
            if json_start != -1:
                json_content_start = json_start + 7
                while json_content_start < len(cleaned) and cleaned[json_content_start] in ' \n\t':
                    json_content_start += 1
                
                json_content_end = len(cleaned)
                closing_backticks = cleaned.find("```", json_content_start)
                if closing_backticks != -1:
                    json_content_end = closing_backticks
                
                cleaned = cleaned[json_content_start:json_content_end].strip()
        
        # Fix common JSON issues in mock interviews
        fixes = [
            # Remove trailing commas
            lambda x: re.sub(r',\s*([}\]])', r'\1', x),
            # Fix unescaped quotes in strings
            lambda x: re.sub(r'"([^"]*?)"([^":,}\]\n]*?)"([^":,}\]\n]*?)"', r'"\1\\"\2\\"\3"', x),
            # Add missing closing braces/brackets based on opening ones
            lambda x: self._fix_incomplete_json(x),
        ]
        
        for i, fix_func in enumerate(fixes):
            try:
                fixed = fix_func(cleaned)
                result = json.loads(fixed)
                logger.info(f"🎭 MOCK INTERVIEW PARSING: Fix {i+1} successful")
                return result
            except (json.JSONDecodeError, Exception) as e:
                logger.info(f"🎭 MOCK INTERVIEW PARSING: Fix {i+1} failed: {e}")
                continue
        
        # If all parsing attempts fail, try to extract a partial structure
        logger.warning("🎭 MOCK INTERVIEW PARSING: All parsing failed, attempting partial extraction")
        
        # For premium mock interviews, try to extract interview_simulation array
        if analysis_type == "premium":
            simulation_match = re.search(r'"interview_simulation"\s*:\s*\[(.+?)\](?=\s*,\s*"[^"]+"\s*:|\s*\})', cleaned, re.DOTALL)
            if simulation_match:
                try:
                    # Try to parse just the interview_simulation array
                    simulation_content = simulation_match.group(1)
                    questions = self._extract_questions_from_array(simulation_content)
                    if questions:
                        logger.info(f"🎭 MOCK INTERVIEW PARSING: Extracted {len(questions)} questions from partial JSON")
                        return {
                            "interview_simulation": questions,
                            "interview_strategy": {},
                            "company_specific_prep": {},
                            "challenging_scenarios": [],
                            "confidence_boosters": {},
                            "final_preparation_checklist": [],
                            "interview_success_prediction": "Your preparation will significantly improve your interview performance.",
                            "parsing_note": "Partial extraction from incomplete JSON"
                        }
                except Exception as e:
                    logger.warning(f"🎭 MOCK INTERVIEW PARSING: Partial extraction failed: {e}")
        
        # For free mock interviews, try to extract sample_questions
        elif analysis_type == "free":
            questions_match = re.search(r'"sample_questions"\s*:\s*\[(.+?)\]', cleaned, re.DOTALL)
            if questions_match:
                try:
                    questions_content = questions_match.group(1)
                    questions = self._extract_questions_from_array(questions_content)
                    if questions:
                        logger.info(f"🎭 MOCK INTERVIEW PARSING: Extracted {len(questions)} free questions")
                        return {
                            "interview_readiness_score": "75",
                            "sample_questions": questions,
                            "preparation_gaps": ["Continue building interview preparation skills"],
                            "confidence_builder": "You have strong potential for interview success",
                            "full_prep_benefits": "Premium preparation provides comprehensive interview readiness",
                            "parsing_note": "Partial extraction from incomplete JSON"
                        }
                except Exception as e:
                    logger.warning(f"🎭 MOCK INTERVIEW PARSING: Free questions extraction failed: {e}")
        
        # Complete fallback - return minimal structure
        logger.error("🎭 MOCK INTERVIEW PARSING: All methods failed, returning fallback")
        if analysis_type == "premium":
            return {
                "interview_simulation": [{
                    "question": "Tell me about yourself and why you're interested in this position.",
                    "question_category": "General",
                    "strategic_approach": "Use a structured approach highlighting your relevant experience.",
                    "sample_answer_framework": "Brief professional summary + relevant experience + interest in role",
                    "key_points_to_include": ["Your core strengths", "Relevant achievements", "Career motivation"],
                    "follow_up_questions": ["What specifically interests you about our company?"],
                    "success_tips": "Keep your answer concise and focused on value you bring."
                }],
                "interview_strategy": {},
                "company_specific_prep": {},
                "challenging_scenarios": [],
                "confidence_boosters": {},
                "final_preparation_checklist": [],
                "interview_success_prediction": "With preparation, you can perform well in interviews.",
                "parsing_error": "Failed to parse full AI response, using fallback content",
                "raw_response_length": len(response)
            }
        else:
            return {
                "interview_readiness_score": "70",
                "sample_questions": [{
                    "question": "Tell me about your experience and why you're interested in this role.",
                    "question_type": "General",
                    "why_they_ask": "To understand your background and motivation",
                    "preparation_hint": "Prepare a concise summary of your relevant experience"
                }],
                "preparation_gaps": ["Continue developing interview skills"],
                "confidence_builder": "Your background shows strong potential",
                "full_prep_benefits": "Complete preparation significantly improves success rates",
                "parsing_error": "Failed to parse full AI response, using fallback content"
            }
    
    def _fix_incomplete_json(self, json_str: str) -> str:
        """
        Attempt to fix incomplete JSON by adding missing closing braces/brackets
        """
        # Count opening and closing braces/brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Add missing closing characters
        result = json_str
        
        # Add missing closing brackets
        missing_brackets = open_brackets - close_brackets
        if missing_brackets > 0:
            result += ']' * missing_brackets
        
        # Add missing closing braces
        missing_braces = open_braces - close_braces
        if missing_braces > 0:
            result += '}' * missing_braces
        
        return result
    
    def _extract_questions_from_array(self, array_content: str) -> list:
        """
        Extract question objects from JSON array content
        """
        questions = []
        
        # Use regex to find question objects
        question_pattern = r'\{[^{}]*?"question"[^{}]*?\}'
        question_matches = re.finditer(question_pattern, array_content, re.DOTALL)
        
        for match in question_matches:
            try:
                question_json = match.group(0)
                # Try to parse each question object
                question_obj = json.loads(question_json)
                questions.append(question_obj)
            except json.JSONDecodeError:
                # Skip malformed questions
                continue
        
        return questions
    
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
    
    async def rewrite_resume(
        self, 
        resume_text: str, 
        job_posting: str,
        analysis_type: str = "free"
    ) -> Dict[str, Any]:
        """
        Rewrite resume with job-targeted optimization
        
        Args:
            resume_text: Original resume text
            job_posting: Target job posting text
            analysis_type: "free" or "premium"
            
        Returns:
            Resume rewrite results as dictionary
            
        Raises:
            AIAnalysisError: If rewrite fails
        """
        logger.info(f"Starting {analysis_type} resume rewrite")
        
        try:
            # Validate inputs
            if not resume_text or len(resume_text.strip()) < 50:
                raise AIAnalysisError("Resume text is too short for meaningful rewrite")
            
            if not job_posting or len(job_posting.strip()) < 20:
                raise AIAnalysisError("Job posting is too short for effective resume targeting")
            
            # Get resume rewrite prompt
            prompt_data = self.prompts["resume_rewrite"][analysis_type]
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
            
            # Call OpenAI API with higher token limit for complete rewrites
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=messages,
                temperature=config.openai_temperature,
                max_tokens=config.openai_max_tokens * 2,  # Double tokens for complete rewrites
                timeout=90  # Longer timeout for complex rewrites
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            
            try:
                # Clean and parse JSON response
                cleaned_response = self._clean_json_response(ai_response)
                result = json.loads(cleaned_response)
                logger.info(f"Resume rewrite completed: {analysis_type}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Resume rewrite JSON parsing failed: {e}")
                logger.error(f"Raw AI response (first 1000 chars): {ai_response[:1000]}")
                
                # Return structured error response for resume rewrite
                return {
                    "analysis_type": analysis_type,
                    "service": "resume_rewrite",
                    "raw_response": ai_response[:1000],
                    "error": f"JSON parsing failed: {str(e)}",
                    "fallback_message": "Resume rewrite completed but response format needs adjustment",
                    "timestamp": "2025-09-10T00:00:00Z"
                }
                
        except Exception as e:
            logger.error(f"Resume rewrite failed: {e}")
            if isinstance(e, AIAnalysisError):
                raise
            else:
                raise AIAnalysisError(f"Resume rewrite failed: {str(e)}")
    
    async def preview_resume_rewrite(
        self, 
        resume_text: str, 
        job_posting: str
    ) -> Dict[str, Any]:
        """
        Generate a free preview of resume rewrite potential
        
        Args:
            resume_text: Original resume text
            job_posting: Target job posting text
            
        Returns:
            Resume rewrite preview results
        """
        return await self.rewrite_resume(resume_text, job_posting, "free")
    
    async def complete_resume_rewrite(
        self, 
        resume_text: str, 
        job_posting: str
    ) -> Dict[str, Any]:
        """
        Generate complete premium resume rewrite
        
        Args:
            resume_text: Original resume text
            job_posting: Target job posting text
            
        Returns:
            Complete resume rewrite results
        """
        return await self.rewrite_resume(resume_text, job_posting, "premium")
    
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
    
    async def generate_mock_interview(
        self,
        resume_text: str,
        job_posting: str,
        analysis_type: str = "free"
    ) -> Dict[str, Any]:
        """
        Generate mock interview questions and preparation guidance
        
        Args:
            resume_text: Extracted resume text
            job_posting: Target job posting text 
            analysis_type: "free" or "premium"
            
        Returns:
            Mock interview results as dictionary
            
        Raises:
            AIAnalysisError: If generation fails
        """
        logger.info(f"Generating {analysis_type} mock interview for job posting ({len(job_posting)} chars)")
        
        try:
            # Validate input
            if not resume_text or len(resume_text.strip()) < 50:
                raise AIAnalysisError("Resume text is too short for meaningful interview preparation")
            
            if not job_posting or len(job_posting.strip()) < 50:
                raise AIAnalysisError("Job posting is required for interview preparation")
            
            # Get appropriate prompt
            prompt_data = self.prompts["mock_interview"][analysis_type]
            user_prompt = prompt_data["user_prompt"].format(
                resume_text=resume_text,
                job_posting=job_posting
            )
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": prompt_data["system_prompt"]},
                {"role": "user", "content": user_prompt}
            ]
            
            # Get appropriate token limit for mock interview
            token_limit = config.get_token_limit("mock_interview", "mock_interview")
            logger.info(f"🎯 Using {token_limit} tokens for {analysis_type} mock interview")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=config.openai_model,
                messages=messages,
                temperature=config.openai_temperature,
                max_tokens=token_limit,
                timeout=60.0
            )
            
            # Extract and parse response
            ai_response = response.choices[0].message.content
            logger.info(f"AI mock interview response received ({len(ai_response)} chars)")
            
            # Parse JSON response with special handling for mock interview
            result = self._parse_mock_interview_json(ai_response, analysis_type)
            
            # DEBUG: Log the structure of the mock interview result
            logger.info(f"🔍 MOCK INTERVIEW DEBUG: Result keys: {list(result.keys())}")
            if 'interview_simulation' in result:
                logger.info(f"🔍 MOCK INTERVIEW DEBUG: Interview simulation count: {len(result['interview_simulation'])}")
                for i, question in enumerate(result.get('interview_simulation', [])):
                    logger.info(f"🔍 MOCK INTERVIEW DEBUG: Question {i+1} keys: {list(question.keys())}")
                    logger.info(f"🔍 MOCK INTERVIEW DEBUG: Question {i+1} text: {question.get('question', 'No question')[:100]}...")
            else:
                logger.warning(f"🔍 MOCK INTERVIEW DEBUG: No 'interview_simulation' key found in result")
            
            # Add metadata
            result["_metadata"] = {
                "analysis_type": analysis_type,
                "service_version": "v4.1-interview",
                "prompt_version": prompt_data.get("version", "unknown"),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
            logger.info(f"✅ Mock interview generation completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Mock interview generation failed: {str(e)}"
            logger.error(error_msg)
            raise AIAnalysisError(error_msg)
    
    async def generate_mock_interview_preview(
        self,
        resume_text: str,
        job_posting: str
    ) -> Dict[str, Any]:
        """Generate free mock interview preview"""
        return await self.generate_mock_interview(resume_text, job_posting, "free")
    
    async def generate_mock_interview_premium(
        self,
        resume_text: str,
        job_posting: str
    ) -> Dict[str, Any]:
        """Generate premium mock interview simulation"""
        return await self.generate_mock_interview(resume_text, job_posting, "premium")

# Singleton instance
analysis_service = AnalysisService()