from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import io
import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
import openai
from docx import Document
import fitz  # PyMuPDF
import tempfile
from uuid import uuid4
import stripe

# Import our new prompt management system
from prompt_manager import prompt_manager, format_prompt, get_system_prompt, get_prompt

# Import sentiment tracking system
from analytics.sentiment_tracker import sentiment_tracker, track_session_start, track_analysis_completion, track_sentiment, track_conversion

# Load environment variables
load_dotenv()

app = FastAPI(title="Resume Health Checker", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Stripe configuration
STRIPE_SUCCESS_TOKEN = os.getenv("STRIPE_PAYMENT_SUCCESS_TOKEN", "payment_success_123")
STRIPE_PAYMENT_URL = os.getenv("STRIPE_PAYMENT_URL", "https://buy.stripe.com/8x2cN4cC823I3qFcPWfMA02")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", os.getenv("STRIPE_SECRET_TEST_KEY", ""))

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file using PyMuPDF"""
    try:
        # Create a temporary file to work with PyMuPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            
            # Open PDF and extract text
            doc = fitz.open(tmp_file.name)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file using python-docx"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing DOCX: {str(e)}")

def resume_to_text(file: UploadFile) -> str:
    """Convert uploaded resume file to text"""
    file_content = file.file.read()
    
    if file.content_type == "application/pdf":
        return extract_text_from_pdf(file_content)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_content)
    else:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Please upload a PDF or DOCX file."
        )

def get_free_analysis_prompt(resume_text: str) -> str:
    """Generate hope-driven prompt for free resume analysis"""
    return format_prompt("resume_analysis", "free", resume_text=resume_text)

def get_job_matching_prompt(resume_text: str, job_posting: str, is_paid: bool = False) -> str:
    """Generate hope-driven prompt for job matching analysis"""
    if is_paid:
        return format_prompt("job_fit", "premium", resume_text=resume_text, job_posting=job_posting)
    else:
        return format_prompt("job_fit", "free", resume_text=resume_text, job_posting=job_posting)

def get_paid_analysis_prompt(resume_text: str) -> str:
    """Generate hope-driven prompt for detailed paid resume analysis"""
    return format_prompt("resume_analysis", "premium", resume_text=resume_text)

async def get_ai_analysis_with_retry(prompt: str, max_retries: int = 3) -> dict:
    """Get analysis from OpenAI with robust retry mechanism for slow/flaky connections"""
    
    for attempt in range(max_retries):
        try:
            # Calculate exponential backoff delay
            if attempt > 0:
                delay = min(2 ** (attempt - 1), 10)  # Max 10 seconds delay
                print(f"⏳ Retry {attempt}/{max_retries} after {delay}s delay...")
                await asyncio.sleep(delay)
            
            print(f"🔍 Calling OpenAI API (attempt {attempt + 1}/{max_retries})")
            
            # Use synchronous client with timeout handling (compatible with openai 1.3.5)
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500,
                timeout=60.0  # 60 second timeout for slow connections
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ OpenAI API response received: {len(result)} characters")
            
            # Clean the response - remove markdown code blocks if present
            if result.startswith('```json'):
                result = result[7:]  # Remove ```json
            if result.startswith('```'):
                result = result[3:]   # Remove ```
            if result.endswith('```'):
                result = result[:-3]  # Remove trailing ```
            
            result = result.strip()
            print(f"🧹 Cleaned response: {len(result)} characters")
            
            # Parse JSON to validate it's properly formatted
            parsed_result = json.loads(result)
            print(f"✅ JSON parsing successful on attempt {attempt + 1}")
            return parsed_result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error on attempt {attempt + 1}: {str(e)}")
            if attempt == max_retries - 1:  # Last attempt
                print(f"Raw AI response: {result[:200] if 'result' in locals() else 'No response'}...")
                raise HTTPException(
                    status_code=503, 
                    detail="AI service returned invalid response format. Please try again in a moment."
                )
            continue
            
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ OpenAI error on attempt {attempt + 1}: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            
            # Handle different types of errors with specific user messages
            if "timeout" in error_msg or "connection" in error_msg:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=503, 
                        detail="Connection timeout. Your internet connection may be slow. Please try again."
                    )
            elif "rate limit" in error_msg:
                if attempt < max_retries - 1:
                    # Wait longer for rate limits
                    await asyncio.sleep(min(5 * (attempt + 1), 20))
                else:
                    raise HTTPException(
                        status_code=503, 
                        detail="Service temporarily overloaded. Please try again in a few minutes."
                    )
            elif "api" in error_msg and "error" in error_msg:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=503, 
                        detail="AI service temporarily unavailable. Please try again in a moment."
                    )
            else:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=503, 
                        detail="Service temporarily unavailable. Please try again later."
                    )
            continue
    
    # This should never be reached due to the exception handling above
    raise HTTPException(status_code=503, detail="Service temporarily unavailable")

# Legacy function name for backward compatibility
async def get_ai_analysis(prompt: str) -> dict:
    """Legacy wrapper for get_ai_analysis_with_retry"""
    return await get_ai_analysis_with_retry(prompt)

@app.post("/api/check-resume")
async def check_resume(
    file: UploadFile = File(...),
    payment_token: Optional[str] = Form(None),
    job_posting: Optional[str] = Form(None)
):
    """
    Main endpoint for resume analysis
    - Without payment_token: Returns free analysis (job matching if job_posting provided)
    - With valid payment_token: Returns detailed paid analysis
    - With job_posting: Returns job fit analysis instead of general resume analysis
    """
    
    print(f"📁 File upload received: {file.filename}, type: {file.content_type}, size: {file.size}")
    
    # Validate file type - be flexible with MIME types and check file extension too
    valid_mime_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream"  # Common for file uploads
    ]
    
    valid_extensions = [".pdf", ".docx"]
    file_extension = os.path.splitext(file.filename.lower())[1]
    
    if not (file.content_type in valid_mime_types or file_extension in valid_extensions):
        print(f"❌ Invalid file: {file.content_type}, extension: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or Word document"
        )
    
    # Additional validation for octet-stream - must have valid extension
    if file.content_type == "application/octet-stream" and file_extension not in valid_extensions:
        print(f"❌ Invalid file type for octet-stream: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or Word document"
        )
    
    # Extract text from resume
    try:
        resume_text = resume_to_text(file)
        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from file")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Determine if this is a paid or free analysis
    is_paid = payment_token == STRIPE_SUCCESS_TOKEN or payment_token == 'session_validated'
    
    # Generate session ID for tracking
    import uuid
    session_id = str(uuid.uuid4())
    
    # Determine product type and track session start
    if job_posting and job_posting.strip():
        product = "job_fit"
        print(f"📋 Job posting provided, using job matching analysis")
        prompt = get_job_matching_prompt(resume_text, job_posting.strip(), is_paid)
        prompt_version = "v1.0-hope"
    elif is_paid:
        product = "resume_analysis"
        prompt = get_paid_analysis_prompt(resume_text)
        prompt_version = "v1.0-hope"
    else:
        product = "resume_analysis"
        prompt = get_free_analysis_prompt(resume_text)
        prompt_version = "v1.0-hope"
    
    # Track session start
    track_session_start(session_id, product)
    
    # Record start time for processing duration
    start_time = time.time()
    
    analysis = await get_ai_analysis(prompt)
    
    # Calculate processing time and track completion
    processing_time = time.time() - start_time
    analysis_type = "paid" if is_paid else "free"
    track_analysis_completion(session_id, prompt_version, analysis_type, processing_time)
    
    # Add metadata to response including session ID for frontend tracking
    analysis["analysis_type"] = analysis_type
    analysis["session_id"] = session_id
    analysis["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    return JSONResponse(content=analysis)

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resume Health Checker - Get More Interviews</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
            }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 3rem;
            }
            
            .header h1 {
                font-size: 2.8rem;
                margin-bottom: 0.5rem;
                font-weight: 700;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .header p {
                font-size: 1.3rem;
                opacity: 0.9;
                margin-bottom: 1rem;
            }
            
            .header .subtitle {
                font-size: 1rem;
                opacity: 0.8;
                font-weight: 300;
            }
            
            .upload-section {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            
            .file-upload {
                border: 2px dashed #ddd;
                border-radius: 8px;
                padding: 2rem;
                text-align: center;
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .file-upload:hover {
                border-color: #667eea;
                background-color: #f8f9ff;
            }
            
            .file-upload.dragover {
                border-color: #667eea;
                background-color: #f0f2ff;
            }
            
            #fileInput {
                display: none;
            }
            
            .upload-text {
                font-size: 1.1rem;
                color: #666;
                margin-bottom: 1rem;
            }
            
            .file-types {
                font-size: 0.9rem;
                color: #999;
            }
            
            .analyze-btn {
                width: 100%;
                padding: 1rem 2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s ease;
                margin-top: 1rem;
            }
            
            .analyze-btn:hover {
                transform: translateY(-2px);
            }
            
            .analyze-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .results-section {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                display: none;
            }
            
            .score-circle {
                width: 120px;
                height: 120px;
                border-radius: 50%;
                margin: 0 auto 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2rem;
                font-weight: bold;
                color: white;
            }
            
            .score-excellent { background: linear-gradient(135deg, #4CAF50, #45a049); }
            .score-good { background: linear-gradient(135deg, #2196F3, #1976D2); }
            .score-fair { background: linear-gradient(135deg, #FF9800, #F57C00); }
            .score-poor { background: linear-gradient(135deg, #f44336, #d32f2f); }
            
            .issues-list {
                list-style: none;
                margin: 1rem 0;
            }
            
            .issues-list li {
                padding: 0.8rem;
                background: #f8f9fa;
                border-left: 4px solid #ff6b6b;
                margin-bottom: 0.5rem;
                border-radius: 4px;
            }
            
            .upgrade-section {
                background: linear-gradient(135deg, #ff6b6b, #ee5a52);
                color: white;
                padding: 2rem;
                border-radius: 12px;
                text-align: center;
                margin-top: 2rem;
            }
            
            .upgrade-btn {
                background: white;
                color: #ff6b6b;
                padding: 1rem 2rem;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: transform 0.2s ease;
                margin-top: 1rem;
            }
            
            .upgrade-btn:hover {
                transform: translateY(-2px);
            }
            
            .loading {
                text-align: center;
                padding: 2rem;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 1rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .detailed-results {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin: 2rem 0;
            }
            
            .metric-card {
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            
            .metric-score {
                font-size: 2rem;
                font-weight: bold;
                color: #667eea;
                margin-bottom: 0.5rem;
            }
            
            .recommendations {
                background: #e8f5e8;
                padding: 1.5rem;
                border-radius: 8px;
                border-left: 4px solid #4CAF50;
                margin: 2rem 0;
            }
            
            .recommendations h3 {
                color: #2e7d32;
                margin-bottom: 1rem;
            }
            
            .recommendations ol {
                margin-left: 1rem;
            }
            
            .recommendations li {
                margin-bottom: 0.5rem;
                line-height: 1.5;
            }
            
            .testimonials {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            
            .testimonials h2 {
                text-align: center;
                color: #333;
                margin-bottom: 2rem;
                font-size: 1.8rem;
            }
            
            .testimonial-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 1.5rem;
            }
            
            .testimonial {
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                position: relative;
            }
            
            .testimonial-quote {
                font-style: italic;
                margin-bottom: 1rem;
                color: #555;
                line-height: 1.6;
            }
            
            .testimonial-author {
                font-weight: 600;
                color: #333;
                font-size: 0.9rem;
            }
            
            .testimonial-role {
                color: #666;
                font-size: 0.8rem;
            }
            
            .footer {
                background: rgba(255,255,255,0.1);
                color: white;
                text-align: center;
                padding: 2rem;
                border-radius: 12px;
                margin-top: 3rem;
            }
            
            .footer h3 {
                margin-bottom: 1rem;
                font-size: 1.2rem;
            }
            
            .footer p {
                opacity: 0.9;
                margin-bottom: 0.5rem;
            }
            
            .footer a {
                color: #b3d9ff;
                text-decoration: none;
            }
            
            .footer a:hover {
                text-decoration: underline;
            }
            
            .pricing-banner {
                background: linear-gradient(135deg, #ff6b6b, #ee5a52);
                color: white;
                padding: 1rem;
                border-radius: 8px;
                text-align: center;
                margin: 1rem 0;
                font-weight: 600;
            }
            
            .dynamic-price {
                font-size: 1.2rem;
                color: #fff;
            }
            
            .job-posting-section {
                margin-top: 1.5rem;
            }
            
            .job-posting-label {
                font-size: 1rem;
                font-weight: 600;
                color: #333;
                margin-bottom: 0.5rem;
            }
            
            .job-posting-subtitle {
                font-size: 0.9rem;
                color: #666;
                margin-bottom: 1rem;
            }
            
            .job-posting-textarea {
                width: 100%;
                min-height: 120px;
                padding: 1rem;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 0.95rem;
                font-family: inherit;
                resize: vertical;
                transition: border-color 0.3s ease;
            }
            
            .job-posting-textarea:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .job-posting-textarea::placeholder {
                color: #999;
                font-style: italic;
            }
            
            /* Product Selection Styles */
            .product-selection-section {
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                margin-bottom: 2rem;
            }
            
            .section-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .section-header h2 {
                color: #333;
                font-size: 1.8rem;
                margin-bottom: 0.5rem;
            }
            
            .section-header p {
                color: #666;
                font-size: 1rem;
            }
            
            .products-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .product-card {
                border: 2px solid #e1e8ed;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                background: #fafbfc;
            }
            
            .product-card:hover {
                border-color: #667eea;
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
            }
            
            .product-card.selected {
                border-color: #667eea;
                background: linear-gradient(135deg, #667eea15, #764ba215);
                transform: translateY(-2px);
            }
            
            .product-emoji {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                display: block;
            }
            
            .product-name {
                font-size: 1.2rem;
                font-weight: 700;
                color: #333;
                margin-bottom: 0.5rem;
            }
            
            .product-description {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 1rem;
                line-height: 1.4;
            }
            
            .product-benefits {
                text-align: left;
                margin-bottom: 1rem;
            }
            
            .product-benefits ul {
                list-style: none;
                padding: 0;
            }
            
            .product-benefits li {
                color: #555;
                font-size: 0.85rem;
                margin-bottom: 0.3rem;
                padding-left: 1rem;
                position: relative;
            }
            
            .product-benefits li:before {
                content: "✓";
                color: #4caf50;
                font-weight: bold;
                position: absolute;
                left: 0;
            }
            
            .product-price {
                font-size: 1.4rem;
                font-weight: 700;
                color: #667eea;
                margin-bottom: 0.5rem;
            }
            
            .product-time {
                color: #888;
                font-size: 0.8rem;
            }
            
            .bundle-section {
                border-top: 2px solid #e1e8ed;
                padding-top: 2rem;
                margin-top: 2rem;
            }
            
            .bundle-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .bundle-header h3 {
                color: #333;
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
            }
            
            .bundle-header p {
                color: #666;
                font-size: 0.95rem;
            }
            
            .bundles-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 1.5rem;
            }
            
            .bundle-card {
                border: 2px solid #ff6b6b;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                background: linear-gradient(135deg, #ff6b6b15, #ee5a5215);
            }
            
            .bundle-card:hover {
                border-color: #ff5252;
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(255, 107, 107, 0.2);
            }
            
            .bundle-card.selected {
                border-color: #ff5252;
                background: linear-gradient(135deg, #ff6b6b25, #ee5a5225);
                transform: translateY(-2px);
            }
            
            .bundle-badge {
                position: absolute;
                top: -8px;
                right: -8px;
                background: #ff6b6b;
                color: white;
                padding: 0.3rem 0.6rem;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: 700;
                text-transform: uppercase;
            }
            
            .bundle-badge.best-value {
                background: #4caf50;
            }
            
            .bundle-name {
                font-size: 1.3rem;
                font-weight: 700;
                color: #333;
                margin-bottom: 0.5rem;
            }
            
            .bundle-description {
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }
            
            .bundle-includes {
                text-align: left;
                margin-bottom: 1rem;
            }
            
            .bundle-includes h4 {
                font-size: 0.9rem;
                color: #333;
                margin-bottom: 0.5rem;
                font-weight: 600;
            }
            
            .bundle-includes ul {
                list-style: none;
                padding: 0;
            }
            
            .bundle-includes li {
                color: #555;
                font-size: 0.85rem;
                margin-bottom: 0.3rem;
                padding-left: 1rem;
                position: relative;
            }
            
            .bundle-includes li:before {
                content: "📋";
                position: absolute;
                left: 0;
                font-size: 0.8rem;
            }
            
            .bundle-pricing {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 1rem;
                margin-bottom: 0.5rem;
            }
            
            .bundle-original-price {
                color: #888;
                text-decoration: line-through;
                font-size: 1rem;
            }
            
            .bundle-price {
                font-size: 1.6rem;
                font-weight: 700;
                color: #ff6b6b;
            }
            
            .bundle-savings {
                background: #4caf50;
                color: white;
                padding: 0.2rem 0.5rem;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: 600;
            }
            
            .selected-product {
                background: #f8f9fa;
                border: 2px solid #667eea;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                margin-top: 2rem;
            }
            
            .selection-summary h3 {
                color: #333;
                margin-bottom: 1rem;
            }
            
            .selected-item {
                background: white;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            .continue-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .continue-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Resume Health Checker</h1>
                <p>Get expert feedback to land more interviews</p>
                <p class="subtitle">AI-powered analysis used by 1000+ job seekers worldwide</p>
            </div>
            
            <div class="testimonials">
                <h2>Success Stories</h2>
                <div class="testimonial-grid">
                    <div class="testimonial">
                        <div class="testimonial-quote">
                            "The detailed analysis helped me identify exactly why my resume wasn't getting responses. After implementing the suggested changes, I got 3 interview requests within two weeks!"
                        </div>
                        <div class="testimonial-author">Sarah M.</div>
                        <div class="testimonial-role">Marketing Manager, Tech Startup</div>
                    </div>
                    
                    <div class="testimonial">
                        <div class="testimonial-quote">
                            "The text rewrites were game-changing. I had no idea my bullet points were so generic. The improved versions with metrics made my achievements stand out immediately."
                        </div>
                        <div class="testimonial-author">David K.</div>
                        <div class="testimonial-role">Software Engineer, FAANG</div>
                    </div>
                    
                    <div class="testimonial">
                        <div class="testimonial-quote">
                            "Worth every penny! The ATS optimization tips helped my resume pass through automated screening. I went from 0 callbacks to landing my dream job in consulting."
                        </div>
                        <div class="testimonial-author">Maria R.</div>
                        <div class="testimonial-role">Business Consultant, Fortune 500</div>
                    </div>
                </div>
            </div>
            
            <!-- Product Selection Section -->
            <div class="product-selection-section" id="productSelection" style="display: none;">
                <div class="section-header">
                    <h2>🚀 Choose Your Career Transformation</h2>
                    <p>Select what you need to land your dream job faster</p>
                </div>
                
                <div class="products-grid" id="productsGrid">
                    <!-- Products will be loaded dynamically -->
                </div>
                
                <div class="bundle-section" id="bundleSection" style="display: none;">
                    <div class="bundle-header">
                        <h3>💡 Smart Recommendations</h3>
                        <p>Save money and get everything you need for job search success</p>
                    </div>
                    <div class="bundles-grid" id="bundlesGrid">
                        <!-- Bundles will be loaded dynamically -->
                    </div>
                </div>
                
                <div class="selected-product" id="selectedProduct" style="display: none;">
                    <div class="selection-summary">
                        <h3>Your Selection:</h3>
                        <div class="selected-item" id="selectedItem"></div>
                        <button class="continue-btn" onclick="showUploadSection()">
                            Continue to Upload Resume 📋
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="upload-section" id="uploadSection">
                <div class="file-upload" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" accept=".pdf,.docx" onchange="handleFileSelect(event)">
                    <div class="upload-text">
                        <strong>Click to upload your resume</strong><br>
                        or drag and drop it here
                    </div>
                    <div class="file-types">Supports PDF and Word documents</div>
                </div>
                
                <div class="job-posting-section">
                    <div class="job-posting-label">💼 Job Posting (Optional)</div>
                    <div class="job-posting-subtitle">Paste job posting here for role-specific insights</div>
                    <textarea 
                        id="jobPostingText" 
                        class="job-posting-textarea" 
                        placeholder="Paste the job posting or job description here to get personalized analysis for this specific role...

Example: We are looking for a Senior Software Engineer with 5+ years experience in Python, React, and AWS..."
                        oninput="updateAnalyzeButton()"
                    ></textarea>
                </div>
                
                <button class="analyze-btn" id="analyzeBtn" onclick="analyzeResume()" disabled>
                    Analyze My Resume - FREE
                </button>
            </div>
            
            <div class="results-section" id="resultsSection">
                <!-- Results will be displayed here -->
            </div>
            
            <div class="footer">
                <h3>Need Help?</h3>
                <p>Our team is here to support your career success</p>
                <p>Contact us: <a href="mailto:support@idpetech.com">support@idpetech.com</a></p>
                <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.7;">
                    Trusted by professionals worldwide • Secure payment processing • 24/7 support
                </p>
            </div>
        </div>

        <script>
            console.log('🟢 JavaScript starting...');
            
            // WORKING STATIC PRODUCT CARDS - No API calls needed
            setTimeout(function() {
                console.log('🎨 Loading static product cards...');
                const productsGrid = document.getElementById('productsGrid');
                if (productsGrid) {
                    productsGrid.innerHTML = `
                        <div class="product-card" onclick="selectProduct('individual', 'resume_analysis', '$5')" style="border: 2px solid #e1e8ed; border-radius: 12px; padding: 1.5rem; text-align: center; cursor: pointer; transition: all 0.3s ease; background: #fafbfc;">
                            <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">📋</span>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #333; margin-bottom: 0.5rem;">Resume Health Check</div>
                            <div style="color: #666; font-size: 0.9rem; margin-bottom: 1rem; line-height: 1.4;">Transform your resume into an interview magnet</div>
                            <div style="text-align: left; margin-bottom: 1rem;">
                                <ul style="list-style: none; padding: 0;">
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>ATS optimization insights</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Content enhancement suggestions</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Impact metrics improvements</li>
                                </ul>
                            </div>
                            <div style="font-size: 1.4rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">$5</div>
                            <div style="color: #888; font-size: 0.8rem;">2-3 minutes</div>
                        </div>
                        
                        <div class="product-card" onclick="selectProduct('individual', 'job_fit_analysis', '$6')" style="border: 2px solid #e1e8ed; border-radius: 12px; padding: 1.5rem; text-align: center; cursor: pointer; transition: all 0.3s ease; background: #fafbfc;">
                            <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">🎯</span>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #333; margin-bottom: 0.5rem;">Job Fit Analysis</div>
                            <div style="color: #666; font-size: 0.9rem; margin-bottom: 1rem; line-height: 1.4;">Position yourself as the perfect candidate</div>
                            <div style="text-align: left; margin-bottom: 1rem;">
                                <ul style="list-style: none; padding: 0;">
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Job-specific optimization</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Missing requirements identification</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Strategic positioning advice</li>
                                </ul>
                            </div>
                            <div style="font-size: 1.4rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">$6</div>
                            <div style="color: #888; font-size: 0.8rem;">3-4 minutes</div>
                        </div>
                        
                        <div class="product-card" onclick="selectProduct('individual', 'cover_letter', '$4')" style="border: 2px solid #e1e8ed; border-radius: 12px; padding: 1.5rem; text-align: center; cursor: pointer; transition: all 0.3s ease; background: #fafbfc;">
                            <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">✍️</span>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #333; margin-bottom: 0.5rem;">Cover Letter Generator</div>
                            <div style="color: #666; font-size: 0.9rem; margin-bottom: 1rem; line-height: 1.4;">Write cover letters that open doors</div>
                            <div style="text-align: left; margin-bottom: 1rem;">
                                <ul style="list-style: none; padding: 0;">
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Personalized for each role</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Strategic storytelling</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Company research integration</li>
                                </ul>
                            </div>
                            <div style="font-size: 1.4rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">$4</div>
                            <div style="color: #888; font-size: 0.8rem;">2-3 minutes</div>
                        </div>
                        
                        <div class="product-card" onclick="showBundles()" style="border: 2px solid #ff6b6b; border-radius: 12px; padding: 1.5rem; text-align: center; cursor: pointer; transition: all 0.3s ease; background: linear-gradient(135deg, #ff6b6b15, #4caf5015);">
                            <span style="font-size: 2.5rem; display: block; margin-bottom: 0.5rem;">🎯</span>
                            <div style="font-size: 1.2rem; font-weight: 700; color: #333; margin-bottom: 0.5rem;">Bundle & Save</div>
                            <div style="color: #666; font-size: 0.9rem; margin-bottom: 1rem; line-height: 1.4;">Get multiple services and save up to 27%</div>
                            <div style="text-align: left; margin-bottom: 1rem;">
                                <ul style="list-style: none; padding: 0;">
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Complete job search toolkit</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Save $3-$8 on bundles</li>
                                    <li style="color: #555; font-size: 0.85rem; margin-bottom: 0.3rem; padding-left: 1rem; position: relative;"><span style="content: '✓'; color: #4caf50; font-weight: bold; position: absolute; left: 0;">✓</span>Priority processing</li>
                                </ul>
                            </div>
                            <div style="font-size: 1.4rem; font-weight: 700; color: #ff6b6b; margin-bottom: 0.5rem;">View Bundles</div>
                            <div style="color: #888; font-size: 0.8rem;">Best Value!</div>
                        </div>
                    `;
                    console.log('✅ Static product cards loaded successfully!');
                } else {
                    console.error('❌ Could not find productsGrid element');
                }
            }, 100);
            
            // Product selection function
            function selectProduct(productType, productId, displayPrice) {
                console.log('🎯 Product selected:', productType, productId, displayPrice);
                
                // Check if user has uploaded a file
                if (!selectedFile) {
                    alert('Please upload your resume first before selecting a service.');
                    document.getElementById('fileInput').focus();
                    return;
                }
                
                selectedProductType = productType;
                selectedProductId = productId;
                
                // Show confirmation and proceed to payment
                const productNames = {
                    'resume_analysis': 'Resume Health Check',
                    'job_fit_analysis': 'Job Fit Analysis', 
                    'cover_letter': 'Cover Letter Generator'
                };
                
                const productName = productNames[productId] || productId;
                if (confirm(`Ready to proceed with ${productName} for ${displayPrice}?`)) {
                    proceedToPayment(productType, productId);
                }
            }
            
            // Bundle selection function
            function showBundles() {
                if (!selectedFile) {
                    alert('Please upload your resume first before selecting bundle options.');
                    document.getElementById('fileInput').focus();
                    return;
                }
                
                const bundleOptions = `
Choose your bundle option:

1. Complete Package - $11 (Save $4)
   Resume + Job Fit + Cover Letter

2. Career Boost - $9 (Save $2)  
   Resume + Job Fit Analysis

3. Job Hunter - $7 (Save $2)
   Resume + Cover Letter

Which would you like? (Enter 1, 2, or 3)
                `;
                
                const choice = prompt(bundleOptions);
                
                if (choice === '1') {
                    selectProduct('bundle', 'complete_package', '$11');
                } else if (choice === '2') {
                    selectProduct('bundle', 'career_boost', '$9');
                } else if (choice === '3') {
                    selectProduct('bundle', 'job_hunter', '$7');
                } else if (choice !== null) {
                    alert('Please enter 1, 2, or 3 to select a bundle option.');
                }
            }
            
            // Main payment function for product selections
            async function proceedToPayment(productType, productId) {
                if (!selectedFile) {
                    alert('Please upload your resume first.');
                    return;
                }
                
                console.log('💳 Creating payment session for:', productType, productId);
                
                try {
                    // Create form data for payment session
                    const formData = new FormData();
                    formData.append('product_type', productType);
                    formData.append('product_id', productId);
                    
                    // Prepare session data
                    const sessionData = {
                        resume_text: 'Placeholder resume text', // Will be populated from file
                        session_id: crypto.randomUUID(),
                        user_region: 'US', // TODO: Get from geolocation
                        selected_product: `${productType}_${productId}`
                    };
                    formData.append('session_data', JSON.stringify(sessionData));
                    
                    // Show loading indicator
                    const loadingMessage = document.createElement('div');
                    loadingMessage.innerHTML = '<div style="text-align: center; padding: 20px; color: #666;">Creating payment session...</div>';
                    document.body.appendChild(loadingMessage);
                    
                    // Create payment session with the API
                    const response = await fetch('/api/create-payment-session', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                    const paymentSession = await response.json();
                    console.log('✅ Payment session created:', paymentSession);
                    
                    // Store file data with unique session ID
                    const sessionId = paymentSession.payment_session_id;
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const fileData = {
                            name: selectedFile.name,
                            type: selectedFile.type,
                            content: e.target.result,
                            timestamp: Date.now(),
                            product_type: productType,
                            product_id: productId
                        };
                        
                        // Store file data with session ID
                        const storageKey = `resume_${sessionId}`;
                        const metadataKey = `metadata_${sessionId}`;
                        
                        localStorage.setItem(storageKey, JSON.stringify(fileData));
                        
                        // Store session metadata
                        const metadata = {
                            sessionId: sessionId,
                            timestamp: Date.now(),
                            fileName: fileData.name,
                            status: 'pending_payment',
                            product_type: productType,
                            product_id: productId
                        };
                        localStorage.setItem(metadataKey, JSON.stringify(metadata));
                        
                        // Store session ID in URL hash for retrieval after payment
                        window.location.hash = `session=${sessionId}`;
                        
                        console.log('💾 Stored file with session:', sessionId);
                        
                        // Remove loading indicator
                        document.body.removeChild(loadingMessage);
                        
                        // Redirect to Stripe payment
                        console.log('🚀 Redirecting to Stripe:', paymentSession.payment_url);
                        window.location.href = paymentSession.payment_url;
                    };
                    
                    reader.readAsDataURL(selectedFile);
                    
                } catch (error) {
                    console.error('❌ Payment session creation failed:', error);
                    alert('Unable to create payment session. Please try again.');
                    
                    // Remove loading indicator if it exists
                    const loadingMessage = document.querySelector('div[style*="Creating payment session"]');
                    if (loadingMessage && loadingMessage.parentNode) {
                        loadingMessage.parentNode.removeChild(loadingMessage);
                    }
                }
            }
            
            let selectedFile = null;
            let currentAnalysis = null;
            let currentPricing = { price: '$5', currency: 'USD', stripe_url: 'https://buy.stripe.com/dRm00i8lSfUy6CRaHOfMA01' };
            
            // Multi-product selection variables
            let multiProductPricing = null;
            let selectedProductType = null; // 'individual' or 'bundle'
            let selectedProductId = null;
            let showingBundles = false;

            // Load pricing configuration and detect user's country
            async function loadPricingConfig() {
                try {
                    const response = await fetch('/api/pricing-config');
                    const config = await response.json();
                    
                    // Check if we're in test mode
                    const urlParams = new URLSearchParams(window.location.search);
                    const testCountry = urlParams.get('test_country');
                    
                    let countryCode = 'US';
                    
                    if (testCountry) {
                        // Use test country from URL parameter
                        countryCode = testCountry.toUpperCase();
                        console.log('🧪 TEST MODE: Simulating country:', countryCode);
                    } else {
                        // Normal geolocation detection
                        try {
                            const geoResponse = await fetch('https://ipapi.co/json/');
                            const geoData = await geoResponse.json();
                            if (geoData.country_code) {
                                countryCode = geoData.country_code;
                            }
                            console.log('🌍 Detected country:', countryCode);
                        } catch (e) {
                            console.log('IP geolocation failed, using default USD pricing');
                        }
                    }
                    
                    // Set pricing based on country
                    currentPricing = config.pricing[countryCode] || config.pricing.default;
                    console.log('💰 Using pricing:', currentPricing);
                    updatePricingDisplay();
                    
                } catch (error) {
                    console.log('Failed to load pricing config, using default');
                }
            }
            
            function updatePricingDisplay() {
                // Update price display elements
                const priceElements = document.querySelectorAll('.price-display');
                priceElements.forEach(el => {
                    el.textContent = currentPricing.price;
                });
                
                // Update any other dynamic price displays
                const dynamicPriceElements = document.querySelectorAll('.dynamic-price');
                dynamicPriceElements.forEach(el => {
                    el.textContent = currentPricing.price;
                });
            }

            // Function to find any pending payment sessions
            function findAnyPendingPayment() {
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('resume_meta_')) {
                        const metadata = JSON.parse(localStorage.getItem(key));
                        if (metadata.status === 'pending_payment') {
                            // Check if it's not too old (24 hours max)
                            const age = Date.now() - metadata.timestamp;
                            if (age < 24 * 60 * 60 * 1000) {
                                return metadata.sessionId;
                            }
                        }
                    }
                }
                return null;
            }

            // Function to clean up old sessions
            function cleanupOldSessions() {
                const maxAge = 24 * 60 * 60 * 1000; // 24 hours
                for (let i = localStorage.length - 1; i >= 0; i--) {
                    const key = localStorage.key(i);
                    if (key && (key.startsWith('resume_meta_') || key.startsWith('resume_session_'))) {
                        const item = localStorage.getItem(key);
                        try {
                            const data = JSON.parse(item);
                            if (data.timestamp && (Date.now() - data.timestamp > maxAge)) {
                                localStorage.removeItem(key);
                                console.log('🧹 Cleaned up old session:', key);
                            }
                        } catch (e) {
                            // Invalid JSON, remove it
                            localStorage.removeItem(key);
                        }
                    }
                }
            }

            // Clean up old sessions on page load
            cleanupOldSessions();

            // Check for payment success - multiple detection methods
            const urlParams = new URLSearchParams(window.location.search);
            const hashParams = new URLSearchParams(window.location.hash.substring(1));
            const sessionId = urlParams.get('client_reference_id') || hashParams.get('session');
            const paymentToken = urlParams.get('payment_token'); // Keep for backward compatibility
            
            // Detect payment return from multiple sources
            const isPaymentReturn = document.referrer.includes('stripe.com') || 
                                  sessionId || 
                                  paymentToken ||
                                  window.location.search.includes('payment') ||
                                  window.location.hash.includes('session=') ||
                                  findAnyPendingPayment();
            
            if (isPaymentReturn) {
                console.log('🎉 Payment return detected');
                
                // Try to find stored file data using multiple methods
                let savedFileData = null;
                let storageKey = null;
                let metadataKey = null;
                let activeSessionId = null;
                
                // Method 1: Direct session ID (from URL hash or parameters)
                if (sessionId) {
                    activeSessionId = sessionId;
                    storageKey = `resume_session_${sessionId}`;
                    metadataKey = `resume_meta_${sessionId}`;
                    savedFileData = localStorage.getItem(storageKey);
                    console.log('📁 Trying direct session:', sessionId);
                }
                
                // Method 2: Find any pending payment session
                if (!savedFileData) {
                    activeSessionId = findAnyPendingPayment();
                    if (activeSessionId) {
                        storageKey = `resume_session_${activeSessionId}`;
                        metadataKey = `resume_meta_${activeSessionId}`;
                        savedFileData = localStorage.getItem(storageKey);
                        console.log('📁 Trying pending payment session:', activeSessionId);
                    }
                }
                
                // Method 3: Legacy fallbacks
                if (!savedFileData) {
                    // Try old session format
                    const legacyKey = localStorage.getItem('latest_resume_key');
                    if (legacyKey) {
                        storageKey = legacyKey;
                        savedFileData = localStorage.getItem(legacyKey);
                        console.log('📁 Trying legacy latest key:', legacyKey);
                    }
                }
                
                if (!savedFileData && paymentToken) {
                    storageKey = 'pendingResumeUpload';
                    savedFileData = localStorage.getItem(storageKey);
                    console.log('📁 Trying legacy upload key');
                }
                
                console.log('📁 File data found:', savedFileData ? 'YES' : 'NO');
                
                if (savedFileData) {
                    const fileData = JSON.parse(savedFileData);
                    // Recreate file from stored data
                    fetch('data:' + fileData.type + ';base64,' + fileData.data)
                        .then(res => res.blob())
                        .then(blob => {
                            const file = new File([blob], fileData.name, { type: fileData.type });
                            selectedFile = file;
                            
                            // Clear the stored file data and metadata
                            if (storageKey) {
                                localStorage.removeItem(storageKey);
                            }
                            if (metadataKey) {
                                localStorage.removeItem(metadataKey);
                            }
                            // Clean up legacy trackers
                            localStorage.removeItem('latest_resume_key');
                            
                            // Clear URL hash if it contains session info
                            if (window.location.hash.includes('session=')) {
                                window.location.hash = '';
                            }
                            
                            // Update UI to show payment success
                            updateUploadUI(file.name, true);
                            
                            // Force immediate paid analysis
                            setTimeout(() => {
                                console.log('🔄 Starting automatic paid analysis...');
                                analyzeResume();
                            }, 100);
                        });
                } else {
                    console.log('⚠️ Payment return detected but no file data found');
                }
            }

            // Handle file upload
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    updateAnalyzeButton();
                    
                    // Clean up any lingering payment sessions to prevent premium leakage
                    cleanupOldSessions();
                    
                    // Update upload UI to show selected file
                    updateUploadUI(file.name, false);
                    
                    // Show product selection options after file upload
                    showProductOptions();
                }
            }
            
            // Show free analysis option after file upload
            function showProductOptions() {
                console.log('📋 File uploaded successfully, showing analysis options...');
                
                // Change the analyze button to be more prominent and start free analysis
                const analyzeBtn = document.getElementById('analyzeBtn');
                if (analyzeBtn) {
                    analyzeBtn.style.display = 'block';
                    analyzeBtn.innerHTML = '🎯 Get Your FREE Resume Analysis';
                    analyzeBtn.classList.add('pulse');
                    
                    // Scroll to the analyze button for clear next step
                    analyzeBtn.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
                
                console.log('✅ Free analysis option highlighted');
            }

            function updateAnalyzeButton() {
                const analyzeBtn = document.getElementById('analyzeBtn');
                const jobPostingText = document.getElementById('jobPostingText').value.trim();
                
                if (selectedFile) {
                    analyzeBtn.disabled = false;
                    if (jobPostingText) {
                        analyzeBtn.textContent = 'Analyze Resume + Job Fit - FREE';
                    } else {
                        analyzeBtn.textContent = 'Analyze My Resume - FREE';
                    }
                } else {
                    analyzeBtn.disabled = true;
                    analyzeBtn.textContent = 'Analyze My Resume - FREE';
                }
            }

            // Centralized function to update upload UI while preserving functionality
            function updateUploadUI(fileName, isPaidAnalysis = false) {
                const uploadDiv = document.querySelector('.file-upload');
                const statusText = isPaidAnalysis ? 
                    `<strong>Payment successful! Analyzing: ${fileName}</strong><br><small>Getting your detailed analysis...</small>` :
                    `<strong>Selected: ${fileName}</strong><br><small>Click to change file</small>`;
                    
                uploadDiv.innerHTML = `
                    <input type="file" id="fileInput" accept=".pdf,.docx" onchange="handleFileSelect(event)" style="display: none;">
                    <div class="upload-text">
                        ${statusText}
                    </div>
                `;
                
                // Re-add click handler to maintain upload functionality
                uploadDiv.onclick = function() {
                    document.getElementById('fileInput').click();
                };
            }


            async function analyzeResume() {
                if (!selectedFile) {
                    alert('Please select a file first');
                    return;
                }

                const resultsSection = document.getElementById('resultsSection');
                resultsSection.style.display = 'block';
                resultsSection.innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        <p id="loadingMessage">Analyzing your resume...</p>
                        <p id="retryMessage" style="font-size: 0.9rem; color: #666; margin-top: 1rem; display: none;">
                            For users with slower connections, this may take up to 3 minutes...
                        </p>
                    </div>
                `;
                
                // Show retry message after 10 seconds for slow connections
                setTimeout(() => {
                    const retryMsg = document.getElementById('retryMessage');
                    if (retryMsg) {
                        retryMsg.style.display = 'block';
                    }
                }, 10000);

                const formData = new FormData();
                formData.append('file', selectedFile);
                
                // Add job posting if provided
                const jobPostingText = document.getElementById('jobPostingText').value.trim();
                if (jobPostingText) {
                    formData.append('job_posting', jobPostingText);
                    console.log('📋 Job posting included in analysis');
                }
                
                // Check for valid payment
                const urlParams = new URLSearchParams(window.location.search);
                const sessionId = urlParams.get('client_reference_id');
                const paymentToken = urlParams.get('payment_token');
                
                // Determine if this is a paid analysis - ONLY check URL parameters, not localStorage
                const isPaidAnalysis = sessionId || 
                                     paymentToken || 
                                     document.referrer.includes('stripe.com') ||
                                     window.location.hash.includes('session=');
                
                if (isPaidAnalysis) {
                    console.log('💰 Detected paid analysis - sending session_validated token');
                    formData.append('payment_token', 'session_validated');
                } else {
                    console.log('🆓 Free analysis');
                }

                try {
                    const response = await fetch('/api/check-resume', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const analysis = await response.json();
                    currentAnalysis = analysis;
                    
                    // DEBUG: Log the full analysis to browser console
                    console.log('=== FULL ANALYSIS RESPONSE ===');
                    console.log('📊 Analysis type:', analysis.analysis_type);
                    console.log('💰 Is paid analysis:', analysis.analysis_type === 'paid');
                    console.log(analysis);
                    console.log('================================');
                    
                    displayResults(analysis);

                } catch (error) {
                    // Clear payment parameters from URL to prevent premium leakage on retry
                    const url = new URL(window.location);
                    url.searchParams.delete('payment_token');
                    url.searchParams.delete('client_reference_id');
                    if (window.location.hash.includes('session=')) {
                        window.location.hash = '';
                    }
                    window.history.replaceState({}, document.title, url);
                    
                    console.log('❌ Analysis error:', error);
                    
                    // Parse error response to get server message
                    let errorMessage = "Something went wrong. Please try again.";
                    let errorTitle = "Analysis Failed";
                    let helpText = "Please check your internet connection and try again.";
                    
                    try {
                        if (error.response && error.response.status === 503) {
                            errorTitle = "Service Temporarily Busy";
                            // Try to get the detailed error message from the server
                            const errorData = await error.response.json();
                            if (errorData.detail) {
                                errorMessage = errorData.detail;
                                if (errorMessage.includes("timeout") || errorMessage.includes("slow")) {
                                    helpText = "Your connection appears slow. The analysis will retry automatically with a longer timeout.";
                                } else if (errorMessage.includes("overloaded")) {
                                    helpText = "Our AI service is experiencing high demand. Please wait a few minutes before trying again.";
                                }
                            }
                        } else if (error.response && error.response.status >= 500) {
                            errorTitle = "Server Error";
                            errorMessage = "Our servers are experiencing issues. Please try again in a moment.";
                        } else if (!navigator.onLine) {
                            errorTitle = "No Internet Connection";
                            errorMessage = "Please check your internet connection and try again.";
                            helpText = "Make sure you're connected to the internet.";
                        }
                    } catch (e) {
                        console.log('Error parsing error response:', e);
                    }
                    
                    resultsSection.innerHTML = `
                        <div style="background: #fff5f5; border: 1px solid #feb2b2; border-radius: 8px; padding: 2rem; text-align: center;">
                            <div style="color: #c53030; font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
                            <h3 style="color: #c53030; margin-bottom: 1rem;">${errorTitle}</h3>
                            <p style="color: #4a5568; margin-bottom: 1rem; font-size: 1.1rem;">${errorMessage}</p>
                            <p style="color: #718096; font-size: 0.9rem; margin-bottom: 1.5rem;">${helpText}</p>
                            <button 
                                onclick="analyzeResume()" 
                                style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.8rem 2rem; border: none; border-radius: 6px; font-size: 1rem; cursor: pointer; transition: transform 0.2s ease;"
                                onmouseover="this.style.transform='translateY(-1px)'"
                                onmouseout="this.style.transform='translateY(0px)'"
                            >
                                Try Again
                            </button>
                        </div>
                    `;
                }
            }

            function displayResults(analysis) {
                const resultsSection = document.getElementById('resultsSection');
                
                // Determine if this is job matching analysis
                const isJobMatching = 'job_fit_score' in analysis;
                const score = parseInt(isJobMatching ? analysis.job_fit_score : analysis.overall_score);
                const scoreClass = getScoreClass(score);

                // Debug logging
                console.log('Analysis type:', analysis.analysis_type);
                console.log('Is job matching:', isJobMatching);
                console.log('Has text_rewrites:', 'text_rewrites' in analysis);
                console.log('Has sample_improvements:', 'sample_improvements' in analysis);
                if (analysis.text_rewrites) {
                    console.log('Number of rewrites:', analysis.text_rewrites.length);
                }

                if (analysis.analysis_type === 'free') {
                    if (isJobMatching) {
                        // Display job matching free analysis
                        resultsSection.innerHTML = `
                            <div style="text-align: center;">
                                <div class="score-circle ${scoreClass}">
                                    ${score}%
                                </div>
                                <h2>Job Fit Score</h2>
                                <p style="margin: 1rem 0; color: #666;">Your resume's match for this specific job:</p>
                            </div>
                            
                            <div style="margin: 2rem 0;">
                                <h3 style="color: #ff6b6b; margin-bottom: 1rem;">Missing Requirements:</h3>
                                <ul class="issues-list">
                                    ${analysis.missing_requirements.map(req => `<li>${req}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="upgrade-section">
                                <h3>Want Job-Specific Optimization?</h3>
                                <p>${analysis.upgrade_message}</p>
                                <p style="margin: 1rem 0;">Get job-specific improvements:</p>
                                <ul style="text-align: left; max-width: 400px; margin: 1rem auto;">
                                    <li>✓ Keywords to add for this role</li>
                                    <li>✓ Experience highlights to emphasize</li>
                                    <li>✓ Tailored text rewrites</li>
                                    <li>✓ Competitive advantages for this job</li>
                                    <li>✓ Ready-to-use optimized content</li>
                                </ul>
                                <a href="#" class="upgrade-btn" onclick="showProductSelectionAfterFree()">
                                    🚀 Choose Your Premium Analysis
                                </a>
                            </div>
                        `;
                        
                        // Add sentiment tracking
                        resultsSection.innerHTML += addSentimentTracking(analysis);
                    } else {
                        // Display regular free analysis
                        resultsSection.innerHTML = `
                            <div style="text-align: center;">
                                <div class="score-circle ${scoreClass}">
                                    ${score}/100
                                </div>
                                <h2>Your Resume Health Score</h2>
                                <p style="margin: 1rem 0; color: #666;">Here are the major issues we found:</p>
                            </div>
                            
                            <div style="margin: 2rem 0;">
                                <h3 style="color: #ff6b6b; margin-bottom: 1rem;">Major Issues Found:</h3>
                                <ul class="issues-list">
                                    ${analysis.major_issues.map(issue => `<li>${issue}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="upgrade-section">
                                <h3>Want the Complete Analysis?</h3>
                                <p>${analysis.teaser_message}</p>
                                <p style="margin: 1rem 0;">Get detailed feedback on:</p>
                                <ul style="text-align: left; max-width: 400px; margin: 1rem auto;">
                                    <li>✓ ATS optimization recommendations</li>
                                    <li>✓ Content clarity improvements</li>
                                    <li>✓ Impact metrics suggestions</li>
                                    <li>✓ Formatting fixes</li>
                                    <li>✓ Prioritized action plan</li>
                                </ul>
                                <a href="#" class="upgrade-btn" onclick="showProductSelectionAfterFree()">
                                    🚀 Choose Your Premium Analysis
                                </a>
                            </div>
                        `;
                        
                        // Add sentiment tracking
                        resultsSection.innerHTML += addSentimentTracking(analysis);
                    }
                } else {
                    if (isJobMatching) {
                        // Display job matching paid analysis
                        resultsSection.innerHTML = `
                            <div style="text-align: center;">
                                <div class="score-circle ${scoreClass}">
                                    ${score}%
                                </div>
                                <h2>🎯 Job-Optimized Resume Analysis</h2>
                                <p style="margin: 1rem 0; color: #666;">Tailored specifically for this role</p>
                            </div>

                            <!-- Missing Requirements -->
                            <div style="background: #fff5f5; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ff6b6b; margin: 2rem 0;">
                                <h3 style="color: #d32f2f; margin-bottom: 1rem;">📋 Missing Requirements</h3>
                                <ul style="margin: 0; padding-left: 1rem;">
                                    ${analysis.missing_requirements.map(req => `<li style="margin-bottom: 0.5rem;">${req}</li>`).join('')}
                                </ul>
                            </div>

                            <!-- Keywords to Add -->
                            <div style="background: #f0f8ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #2196F3; margin: 2rem 0;">
                                <h3 style="color: #1976D2; margin-bottom: 1rem;">🔑 Keywords to Add</h3>
                                <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                    ${analysis.optimization_keywords.map(keyword => `<span style="background: #e3f2fd; color: #1976D2; padding: 0.3rem 0.8rem; border-radius: 15px; font-size: 0.9rem;">${keyword}</span>`).join('')}
                                </div>
                            </div>

                            <!-- Resume Improvements -->
                            <div style="background: #f3e5f5; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #9c27b0; margin: 2rem 0;">
                                <h3 style="color: #7b1fa2; margin-bottom: 1rem;">💡 Optimization Recommendations</h3>
                                <ul style="margin: 0; padding-left: 1rem;">
                                    ${analysis.resume_improvements.map(improvement => `<li style="margin-bottom: 0.8rem;">${improvement}</li>`).join('')}
                                </ul>
                            </div>

                            <!-- Competitive Advantage -->
                            <div style="background: #e8f5e8; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #4caf50; margin: 2rem 0;">
                                <h3 style="color: #388e3c; margin-bottom: 1rem;">🌟 Your Competitive Advantage</h3>
                                <p style="margin: 0; font-size: 1.1rem; line-height: 1.6;">${analysis.competitive_advantage}</p>
                            </div>
                        `;
                        
                        // Add text rewrites section if available
                        if (analysis.text_rewrites && analysis.text_rewrites.length > 0) {
                            resultsSection.innerHTML += `
                                <div style="margin: 2rem 0;">
                                    <h3 style="color: #2e7d32; margin-bottom: 1rem;">✍️ Ready-to-Use Text Improvements</h3>
                                    ${analysis.text_rewrites.map(rewrite => `
                                        <div class="text-rewrite" style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                                            <h4 style="color: #1976d2; margin-bottom: 1rem;">${rewrite.section}</h4>
                                            <div style="background: #ffebee; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                                                <strong>Before:</strong> ${rewrite.original}
                                            </div>
                                            <div style="background: #e8f5e8; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;">
                                                <strong>After:</strong> ${rewrite.improved}
                                            </div>
                                            <div style="color: #666; font-style: italic;">
                                                <strong>Why:</strong> ${rewrite.reason}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            `;
                            
                            // Add sentiment tracking
                            resultsSection.innerHTML += addSentimentTracking(analysis);
                        }
                    } else {
                        // Display regular detailed paid analysis
                        resultsSection.innerHTML = `
                            <div style="text-align: center;">
                                <div class="score-circle ${scoreClass}">
                                    ${score}/100
                                </div>
                                <h2>🎯 Complete Resume Analysis</h2>
                                <p style="margin: 1rem 0; color: #666;">Comprehensive breakdown with actionable improvements</p>
                            </div>

                        <!-- Free Analysis Recap -->
                        <div style="background: #f0f8ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #2196F3; margin: 2rem 0;">
                            <h3 style="color: #1976D2; margin-bottom: 1rem;">📋 Key Issues Summary</h3>
                            <ul style="margin: 0; padding-left: 1rem;">
                                ${analysis.major_issues.map(issue => `<li style="margin-bottom: 0.5rem;">${issue}</li>`).join('')}
                            </ul>
                        </div>

                        <div class="detailed-results">
                            <div class="metric-card">
                                <div class="metric-score">${analysis.ats_optimization.score}/100</div>
                                <h3>ATS Optimization</h3>
                                <h4>Issues:</h4>
                                <ul>
                                    ${analysis.ats_optimization.issues.map(issue => `<li>${issue}</li>`).join('')}
                                </ul>
                                <h4>Improvements:</h4>
                                <ul>
                                    ${analysis.ats_optimization.improvements.map(imp => `<li>${imp}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="metric-card">
                                <div class="metric-score">${analysis.content_clarity.score}/100</div>
                                <h3>Content Clarity</h3>
                                <h4>Issues:</h4>
                                <ul>
                                    ${analysis.content_clarity.issues.map(issue => `<li>${issue}</li>`).join('')}
                                </ul>
                                <h4>Improvements:</h4>
                                <ul>
                                    ${analysis.content_clarity.improvements.map(imp => `<li>${imp}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="metric-card">
                                <div class="metric-score">${analysis.impact_metrics.score}/100</div>
                                <h3>Impact Metrics</h3>
                                <h4>Issues:</h4>
                                <ul>
                                    ${analysis.impact_metrics.issues.map(issue => `<li>${issue}</li>`).join('')}
                                </ul>
                                <h4>Improvements:</h4>
                                <ul>
                                    ${analysis.impact_metrics.improvements.map(imp => `<li>${imp}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="metric-card">
                                <div class="metric-score">${analysis.formatting.score}/100</div>
                                <h3>Formatting</h3>
                                <h4>Issues:</h4>
                                <ul>
                                    ${analysis.formatting.issues.map(issue => `<li>${issue}</li>`).join('')}
                                </ul>
                                <h4>Improvements:</h4>
                                <ul>
                                    ${analysis.formatting.improvements.map(imp => `<li>${imp}</li>`).join('')}
                                </ul>
                            </div>
                        </div>

                        <!-- NEW: Text Rewrites Section -->
                        ${analysis.text_rewrites && analysis.text_rewrites.length > 0 ? `
                            <div style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin: 2rem 0; border-left: 4px solid #28a745;">
                                <h3 style="color: #155724; margin-bottom: 1.5rem;">✨ Ready-to-Use Text Improvements</h3>
                                ${analysis.text_rewrites.map((rewrite, index) => `
                                    <div style="background: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        <h4 style="color: #495057; margin-bottom: 1rem;">📝 ${rewrite.section}</h4>
                                        
                                        <div style="margin-bottom: 1rem;">
                                            <strong style="color: #dc3545;">❌ Current:</strong>
                                            <div style="background: #fff5f5; padding: 0.8rem; border-radius: 4px; margin: 0.5rem 0; font-style: italic; border-left: 3px solid #dc3545;">
                                                "${rewrite.original}"
                                            </div>
                                        </div>
                                        
                                        <div style="margin-bottom: 1rem;">
                                            <strong style="color: #28a745;">✅ Improved:</strong>
                                            <div style="background: #f0fff4; padding: 0.8rem; border-radius: 4px; margin: 0.5rem 0; border-left: 3px solid #28a745;">
                                                "${rewrite.improved}"
                                            </div>
                                        </div>
                                        
                                        <div style="font-size: 0.9rem; color: #6c757d; font-style: italic;">
                                            💡 <strong>Why this works:</strong> ${rewrite.explanation}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}

                        <!-- NEW: Sample Bullet Improvements -->
                        ${analysis.sample_improvements ? `
                            <div style="background: #e8f5e8; padding: 2rem; border-radius: 12px; margin: 2rem 0; border-left: 4px solid #4CAF50;">
                                <h3 style="color: #2e7d32; margin-bottom: 1.5rem;">🎯 Bullet Point Makeover Examples</h3>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1rem;">
                                    <div>
                                        <h4 style="color: #d32f2f; margin-bottom: 1rem;">❌ Weak Bullets</h4>
                                        ${analysis.sample_improvements.weak_bullets.map(bullet => `
                                            <div style="background: #fff; padding: 1rem; border-radius: 4px; margin-bottom: 0.5rem; border-left: 3px solid #d32f2f;">
                                                • ${bullet}
                                            </div>
                                        `).join('')}
                                    </div>
                                    
                                    <div>
                                        <h4 style="color: #388e3c; margin-bottom: 1rem;">✅ Strong Bullets</h4>
                                        ${analysis.sample_improvements.strong_bullets.map(bullet => `
                                            <div style="background: #fff; padding: 1rem; border-radius: 4px; margin-bottom: 0.5rem; border-left: 3px solid #388e3c;">
                                                • ${bullet}
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            </div>
                        ` : ''}

                        <div class="recommendations">
                            <h3>🎯 Top Priority Action Plan</h3>
                            <ol>
                                ${analysis.top_recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ol>
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 1.5rem; border-radius: 8px; text-align: center; margin-top: 2rem;">
                            <h4 style="color: #1565c0; margin-bottom: 0.5rem;">🚀 Ready to Implement?</h4>
                            <p style="color: #424242; margin: 0;">Copy the improved text above and update your resume to increase your interview rate!</p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 2rem;">
                            <button onclick="resetForNewUpload()" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer;">
                                Analyze Another Resume
                            </button>
                        </div>
                    `;
                    
                    // Add sentiment tracking
                    resultsSection.innerHTML += addSentimentTracking(analysis);
                }
            }
            
            // Add sentiment tracking to all analysis results
            function displayResults(analysis) {
                // ... existing code ...
                
                // After displaying results, add sentiment tracking
                setTimeout(() => {
                    const resultsSection = document.getElementById('resultsSection');
                    if (resultsSection && !document.querySelector('.sentiment-tracking')) {
                        resultsSection.innerHTML += addSentimentTracking(analysis);
                    }
                }, 1000); // Small delay to ensure results are fully rendered
            }

            function getScoreClass(score) {
                if (score >= 80) return 'score-excellent';
                if (score >= 60) return 'score-good';
                if (score >= 40) return 'score-fair';
                return 'score-poor';
            }

            function addSentimentTracking(analysis) {
                // Add sentiment tracking UI to results
                return `
                    <div class="sentiment-tracking" style="background: #f8f9fa; padding: 2rem; border-radius: 12px; margin-top: 2rem; text-align: center; border-left: 4px solid #667eea;">
                        <h3 style="color: #333; margin-bottom: 1rem;">💫 How do you feel about this analysis?</h3>
                        <p style="color: #666; margin-bottom: 1.5rem; font-size: 0.95rem;">Your feedback helps us improve our analysis for everyone!</p>
                        
                        <div class="sentiment-buttons" style="display: flex; flex-wrap: wrap; gap: 0.75rem; justify-content: center; margin-bottom: 1.5rem;">
                            <button onclick="trackSentiment('motivated', 5, '🚀 Ready to apply!')" class="sentiment-btn" style="background: #4caf50; color: white; border: none; padding: 0.75rem 1.25rem; border-radius: 25px; cursor: pointer; font-size: 0.9rem; transition: all 0.3s ease;">
                                🚀 Motivated to apply!
                            </button>
                            <button onclick="trackSentiment('confident', 4, '💪 More confident')" class="sentiment-btn" style="background: #2196f3; color: white; border: none; padding: 0.75rem 1.25rem; border-radius: 25px; cursor: pointer; font-size: 0.9rem; transition: all 0.3s ease;">
                                💪 More confident
                            </button>
                            <button onclick="trackSentiment('hopeful', 3, '✨ Feeling hopeful')" class="sentiment-btn" style="background: #ff9800; color: white; border: none; padding: 0.75rem 1.25rem; border-radius: 25px; cursor: pointer; font-size: 0.9rem; transition: all 0.3s ease;">
                                ✨ Feeling hopeful
                            </button>
                            <button onclick="trackSentiment('neutral', 2, '😐 Somewhat helpful')" class="sentiment-btn" style="background: #607d8b; color: white; border: none; padding: 0.75rem 1.25rem; border-radius: 25px; cursor: pointer; font-size: 0.9rem; transition: all 0.3s ease;">
                                😐 Somewhat helpful
                            </button>
                            <button onclick="trackSentiment('discouraged', 1, '😔 Feeling discouraged')" class="sentiment-btn" style="background: #f44336; color: white; border: none; padding: 0.75rem 1.25rem; border-radius: 25px; cursor: pointer; font-size: 0.9rem; transition: all 0.3s ease;">
                                😔 Need more help
                            </button>
                        </div>
                        
                        <div class="detailed-feedback" style="display: none; margin-top: 1rem;" id="detailedFeedback">
                            <p style="color: #666; font-size: 0.9rem; margin-bottom: 0.75rem;">What was most helpful? (optional)</p>
                            <input type="text" id="specificFeedback" placeholder="e.g., The keyword suggestions really helped..." style="width: 100%; max-width: 400px; padding: 0.75rem; border: 1px solid #ddd; border-radius: 6px; font-size: 0.9rem;" />
                            <button onclick="submitDetailedFeedback()" style="background: #667eea; color: white; border: none; padding: 0.6rem 1.25rem; border-radius: 6px; cursor: pointer; margin-left: 0.5rem; font-size: 0.9rem;">
                                Share
                            </button>
                        </div>
                        
                        <div class="sentiment-thanks" style="display: none; color: #4caf50; font-weight: 600; margin-top: 1rem;" id="sentimentThanks">
                            Thank you for your feedback! 🙏
                        </div>
                    </div>
                `;
            }

            function trackSentiment(sentimentLabel, sentimentScore, buttonText) {
                // Track user sentiment and show detailed feedback form
                if (!currentAnalysis || !currentAnalysis.session_id) {
                    console.warn('No session ID available for sentiment tracking');
                    return;
                }
                
                // Send sentiment data to server
                fetch('/api/track-sentiment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: currentAnalysis.session_id,
                        sentiment_score: sentimentScore,
                        sentiment_label: sentimentLabel,
                        product: currentAnalysis.analysis_type || 'unknown',
                        user_path: window.location.pathname
                    })
                }).then(response => {
                    if (response.ok) {
                        console.log('Sentiment tracked successfully');
                    }
                }).catch(error => {
                    console.error('Failed to track sentiment:', error);
                });
                
                // Update UI
                const buttons = document.querySelectorAll('.sentiment-btn');
                buttons.forEach(btn => {
                    btn.style.opacity = '0.3';
                    btn.disabled = true;
                });
                
                // Highlight selected button
                event.target.style.opacity = '1';
                event.target.style.transform = 'scale(1.05)';
                
                // Show detailed feedback form for positive responses
                if (sentimentScore >= 3) {
                    setTimeout(() => {
                        document.getElementById('detailedFeedback').style.display = 'block';
                    }, 500);
                } else {
                    // For negative feedback, show thanks immediately
                    setTimeout(() => {
                        document.getElementById('sentimentThanks').style.display = 'block';
                    }, 500);
                }
            }

            function submitDetailedFeedback() {
                // Submit detailed feedback
                const specificFeedback = document.getElementById('specificFeedback').value.trim();
                
                if (specificFeedback && currentAnalysis && currentAnalysis.session_id) {
                    // Update the previous sentiment entry with specific feedback
                    fetch('/api/track-sentiment', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            session_id: currentAnalysis.session_id,
                            sentiment_score: 0, // Indicator for follow-up feedback
                            sentiment_label: 'detailed_feedback',
                            specific_feedback: specificFeedback
                        })
                    });
                }
                
                // Hide form and show thanks
                document.getElementById('detailedFeedback').style.display = 'none';
                document.getElementById('sentimentThanks').style.display = 'block';
            }

            // Show product selection after free analysis (proper freemium flow)
            function showProductSelectionAfterFree() {
                console.log('🎯 User wants premium analysis, showing product options...');
                
                const productSelection = document.getElementById('productSelection');
                if (productSelection) {
                    // Show the product selection section
                    productSelection.style.display = 'block';
                    
                    // Smooth scroll to product selection
                    productSelection.scrollIntoView({ 
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    // Update the header to show this is premium upgrade
                    const sectionHeader = productSelection.querySelector('.section-header h2');
                    if (sectionHeader) {
                        sectionHeader.innerHTML = '🚀 Choose Your Premium Analysis';
                    }
                    
                    const sectionSubheader = productSelection.querySelector('.section-header p');
                    if (sectionSubheader) {
                        sectionSubheader.innerHTML = 'Upgrade from your free analysis to get detailed insights and recommendations';
                    }
                    
                    console.log('✅ Product selection shown after free analysis');
                } else {
                    console.error('❌ Could not find productSelection element');
                }
            }

            function goToStripeCheckout() {
                // Save the current file to localStorage before going to Stripe
                if (selectedFile) {
                    // Generate unique session ID
                    const sessionId = crypto.randomUUID();
                    
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const fileData = {
                            name: selectedFile.name,
                            type: selectedFile.type,
                            data: e.target.result.split(',')[1] // Remove data URL prefix
                        };
                        // Store with unique session-based key for user isolation
                        const storageKey = `resume_session_${sessionId}`;
                        const metadataKey = `resume_meta_${sessionId}`;
                        
                        // Store file data
                        localStorage.setItem(storageKey, JSON.stringify(fileData));
                        
                        // Store session metadata with timestamp for cleanup
                        const metadata = {
                            sessionId: sessionId,
                            timestamp: Date.now(),
                            fileName: fileData.name,
                            status: 'pending_payment'
                        };
                        localStorage.setItem(metadataKey, JSON.stringify(metadata));
                        
                        // Store session ID in URL hash for retrieval after payment
                        window.location.hash = `session=${sessionId}`;
                        
                        console.log('💾 Stored file with unique session:', sessionId);
                        
                        // Go to Stripe Payment Link (use dynamic pricing URL)
                        const stripeUrl = currentPricing.stripe_url || 'STRIPE_PAYMENT_URL_PLACEHOLDER';
                        window.location.href = stripeUrl;
                    };
                    reader.readAsDataURL(selectedFile);
                } else {
                    alert('Please upload a resume first before upgrading.');
                }
            }

            // Reset function for new uploads
            function resetForNewUpload() {
                console.log('Reset function called'); // Debug log
                
                // Clear current state
                selectedFile = null;
                currentAnalysis = null;
                
                // Clear URL parameters
                const url = new URL(window.location);
                url.searchParams.delete('payment_token');
                url.searchParams.delete('client_reference_id');
                window.history.replaceState({}, document.title, url);
                
                // Reset upload UI
                const uploadDiv = document.querySelector('.file-upload');
                if (uploadDiv) {
                    uploadDiv.innerHTML = `
                        <input type="file" id="fileInput" accept=".pdf,.docx" onchange="handleFileSelect(event)" style="display: none;">
                        <div class="upload-text">
                            <strong>Click to upload your resume</strong><br>
                            or drag and drop it here
                        </div>
                        <div class="file-types">Supports PDF and Word documents</div>
                    `;
                    
                    // Re-add click handler
                    uploadDiv.onclick = function() {
                        document.getElementById('fileInput').click();
                    };
                } else {
                    console.error('Upload div not found');
                }
                
                // Reset analyze button
                const analyzeBtn = document.getElementById('analyzeBtn');
                if (analyzeBtn) {
                    analyzeBtn.disabled = true;
                    analyzeBtn.textContent = 'Analyze My Resume - FREE';
                } else {
                    console.error('Analyze button not found');
                }
                
                // Hide results section
                const resultsSection = document.getElementById('resultsSection');
                if (resultsSection) {
                    resultsSection.style.display = 'none';
                } else {
                    console.error('Results section not found');
                }
                
                // Re-add drag and drop functionality
                setTimeout(() => setupDragAndDrop(), 100); // Small delay to ensure DOM is ready
            }
            
            // Function to setup drag and drop (extracted for reuse)
            function setupDragAndDrop() {
                const fileUpload = document.querySelector('.file-upload');
                
                fileUpload.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    fileUpload.classList.add('dragover');
                });
                
                fileUpload.addEventListener('dragleave', () => {
                    fileUpload.classList.remove('dragover');
                });
                
                fileUpload.addEventListener('drop', (e) => {
                    e.preventDefault();
                    fileUpload.classList.remove('dragover');
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        const file = files[0];
                        if (file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
                            selectedFile = file;
                            document.getElementById('fileInput').files = files;
                            handleFileSelect({ target: { files: [file] } });
                        } else {
                            alert('Please upload a PDF or Word document');
                        }
                    }
                });
            }
            
            // Initial setup of drag and drop
            setupDragAndDrop();
            
            // Load pricing configuration on page load  
            console.log('🚀 Initializing pricing...');
            
            // Simple test to verify DOM access works
            const testGrid = document.getElementById('productsGrid');
            if (testGrid) {
                console.log('✅ Found productsGrid element');
                testGrid.innerHTML = `
                    <div style="border: 2px solid #667eea; border-radius: 12px; padding: 1.5rem; text-align: center; background: #f0f2ff;">
                        <span style="font-size: 2rem;">📋</span>
                        <div style="font-weight: 700; margin: 0.5rem 0;">Test Product Card</div>
                        <div style="color: #666;">$10 - Testing if DOM manipulation works</div>
                    </div>
                `;
                console.log('✅ Test card added to DOM');
            } else {
                console.error('❌ productsGrid element not found!');
            }
            
            try {
                loadPricingConfig();
                loadMultiProductPricing();
                console.log('✅ Function calls completed');
            } catch (error) {
                console.error('❌ Error during initialization:', error);
            }
            
            // Load multi-product pricing and render products
            async function loadMultiProductPricing() {
                try {
                    // Detect user's country first (reuse existing logic)
                    let countryCode = 'US';  // Default
                    
                    const urlParams = new URLSearchParams(window.location.search);
                    const testCountry = urlParams.get('test_country');
                    
                    if (testCountry) {
                        countryCode = testCountry.toUpperCase();
                        console.log('🧪 TEST MODE: Using country:', countryCode);
                    } else {
                        try {
                            const geoResponse = await fetch('https://ipapi.co/json/');
                            const geoData = await geoResponse.json();
                            if (geoData.country_code) {
                                countryCode = geoData.country_code;
                            }
                            console.log('🌍 Detected country:', countryCode);
                        } catch (e) {
                            console.log('IP geolocation failed, using default USD pricing');
                        }
                    }
                    
                    // Try new Stripe pricing API first
                    console.log('💰 Fetching regional pricing from Stripe...');
                    let response = await fetch(`/api/stripe-pricing/${countryCode}`);
                    let pricingData = await response.json();
                    
                    console.log('📊 Stripe pricing loaded:', pricingData);
                    
                    // Transform Stripe pricing data to multi-product format
                    console.log('🔄 Transforming Stripe data...');
                    multiProductPricing = await transformStripePricingToMultiProduct(pricingData, countryCode);
                    console.log('✅ Transformation complete, result:', multiProductPricing);
                    
                    // Store detected country for checkout
                    window.detectedCountry = countryCode;
                    window.currentRegionPricing = pricingData;
                    
                    // Render individual products with Stripe pricing
                    renderProducts();
                    
                } catch (error) {
                    console.error('Error loading Stripe pricing:', error);
                    
                    // Fallback to static multi-product pricing
                    try {
                        console.log('📁 Falling back to static multi-product pricing...');
                        const fallbackResponse = await fetch('/api/multi-product-pricing');
                        multiProductPricing = await fallbackResponse.json();
                        
                        console.log('📊 Multi-product pricing loaded:', multiProductPricing);
                        renderProducts();
                        
                    } catch (fallbackError) {
                        console.error('Error loading fallback pricing:', fallbackError);
                        // Show error message
                        document.getElementById('productsGrid').innerHTML = `
                            <div style="text-align: center; color: #666; grid-column: 1 / -1;">
                                <p>Unable to load product options. Please refresh the page.</p>
                            </div>
                        `;
                    }
                }
            }
            
            async function transformStripePricingToMultiProduct(stripePricing, countryCode) {
                /**
                 * Transform Stripe pricing format to multi-product format for UI compatibility
                 */
                console.log('🔧 transformStripePricingToMultiProduct called with:', stripePricing, countryCode);
                
                // Get static product metadata (names, descriptions, emojis)
                let staticConfig;
                try {
                    const staticResponse = await fetch('/api/multi-product-pricing');
                    staticConfig = await staticResponse.json();
                } catch (e) {
                    console.warn('Could not load static config, using minimal fallback');
                    staticConfig = { products: {}, bundles: {} };
                }
                
                const transformed = {
                    metadata: {
                        version: "3.0.0-stripe",
                        last_updated: stripePricing.fetched_at,
                        description: `Regional pricing for ${stripePricing.region} via Stripe API`,
                        source: stripePricing.source || "stripe"
                    },
                    products: {},
                    bundles: {}
                };
                
                // Transform individual products
                Object.keys(stripePricing.products || {}).forEach(productId => {
                    const stripeProduct = stripePricing.products[productId];
                    const staticProduct = staticConfig.products?.[productId] || {};
                    
                    transformed.products[productId] = {
                        name: staticProduct.name || getProductDisplayName(productId),
                        emoji: staticProduct.emoji || getProductEmoji(productId),
                        description: staticProduct.description || `${getProductDisplayName(productId)} service`,
                        benefits: staticProduct.benefits || [`Optimized ${getProductDisplayName(productId).toLowerCase()}`],
                        individual_price: {
                            amount: stripeProduct.amount,
                            currency: stripeProduct.currency,
                            display: stripeProduct.display,
                            stripe_url: stripeProduct.payment_link
                        },
                        processing_time: staticProduct.processing_time || "2-3 minutes"
                    };
                });
                
                // Transform bundles (if available from Stripe)
                Object.keys(stripePricing.bundles || {}).forEach(bundleId => {
                    const stripeBundle = stripePricing.bundles[bundleId];
                    const staticBundle = staticConfig.bundles?.[bundleId] || {};
                    
                    transformed.bundles[bundleId] = {
                        name: staticBundle.name || getBundleDisplayName(bundleId),
                        emoji: staticBundle.emoji || getBundleEmoji(bundleId),
                        description: staticBundle.description || `${getBundleDisplayName(bundleId)} package`,
                        includes: staticBundle.includes || [],
                        bundle_price: {
                            amount: stripeBundle.amount,
                            currency: stripeBundle.currency,
                            display: stripeBundle.display,
                            stripe_url: stripeBundle.payment_link
                        },
                        savings: stripeBundle.savings || { amount: 0, display: "" },
                        popular: staticBundle.popular || false,
                        best_value: staticBundle.best_value || false
                    };
                });
                
                // Add regional pricing context
                transformed.region_info = {
                    country_code: countryCode,
                    currency: stripePricing.currency,
                    symbol: stripePricing.symbol,
                    source: stripePricing.source
                };
                
                console.log('🔄 Transformed Stripe pricing to multi-product format:', transformed);
                return transformed;
            }
            
            function getProductDisplayName(productId) {
                const names = {
                    "resume_analysis": "Resume Health Check",
                    "job_fit_analysis": "Job Fit Analysis", 
                    "cover_letter": "Cover Letter Generator"
                };
                return names[productId] || productId.replace('_', ' ');
            }
            
            function getProductEmoji(productId) {
                const emojis = {
                    "resume_analysis": "📋",
                    "job_fit_analysis": "🎯",
                    "cover_letter": "✍️"
                };
                return emojis[productId] || "💼";
            }
            
            function getBundleDisplayName(bundleId) {
                const names = {
                    "career_boost": "Career Boost Bundle",
                    "job_hunter": "Job Hunter Bundle",
                    "complete_package": "Complete Job Search Package"
                };
                return names[bundleId] || bundleId.replace('_', ' ');
            }
            
            function getBundleEmoji(bundleId) {
                const emojis = {
                    "career_boost": "🚀",
                    "job_hunter": "🎯", 
                    "complete_package": "💼"
                };
                return emojis[bundleId] || "📦";
            }
            
            // Render individual products
            function renderProducts() {
                console.log('🎨 renderProducts called, multiProductPricing:', multiProductPricing);
                if (!multiProductPricing || !multiProductPricing.products) {
                    console.log('❌ renderProducts: Missing data, multiProductPricing:', multiProductPricing);
                    document.getElementById('productsGrid').innerHTML = '<div style="color: red;">Debug: No product data available</div>';
                    return;
                }
                
                const productsGrid = document.getElementById('productsGrid');
                const products = multiProductPricing.products;
                
                productsGrid.innerHTML = Object.keys(products).map(productId => {
                    const product = products[productId];
                    const tagline = multiProductPricing.hope_driven_messaging.taglines[productId];
                    
                    return `
                        <div class="product-card" onclick="selectProduct('individual', '${productId}')" data-product-id="${productId}">
                            <span class="product-emoji">${product.emoji}</span>
                            <div class="product-name">${product.name}</div>
                            <div class="product-description">${tagline}</div>
                            <div class="product-benefits">
                                <ul>
                                    ${product.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="product-price">${product.individual_price.display}</div>
                            <div class="product-time">${product.processing_time}</div>
                        </div>
                    `;
                }).join('');
                
                // Add "See Bundle Options" call-to-action
                productsGrid.innerHTML += `
                    <div class="product-card bundle-cta" onclick="showBundleOptions()" style="background: linear-gradient(135deg, #ff6b6b15, #4caf5015); border-color: #ff6b6b;">
                        <span class="product-emoji">🎯</span>
                        <div class="product-name">Bundle & Save</div>
                        <div class="product-description">Get multiple services and save up to 27%</div>
                        <div class="product-benefits">
                            <ul>
                                <li>Complete job search toolkit</li>
                                <li>Save $3-$8 on bundles</li>
                                <li>Comprehensive career support</li>
                                <li>Priority processing</li>
                            </ul>
                        </div>
                        <div class="product-price" style="color: #ff6b6b;">View Bundles</div>
                        <div class="product-time">Best Value!</div>
                    </div>
                `;
            }
            
            // Show bundle options
            function showBundleOptions() {
                if (!showingBundles) {
                    renderBundles();
                    document.getElementById('bundleSection').style.display = 'block';
                    showingBundles = true;
                    
                    // Scroll to bundles section
                    document.getElementById('bundleSection').scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                    });
                }
            }
            
            // Render bundles
            function renderBundles() {
                if (!multiProductPricing || !multiProductPricing.bundles) return;
                
                const bundlesGrid = document.getElementById('bundlesGrid');
                const bundles = multiProductPricing.bundles;
                
                bundlesGrid.innerHTML = Object.keys(bundles).map(bundleId => {
                    const bundle = bundles[bundleId];
                    const tagline = multiProductPricing.hope_driven_messaging.taglines[bundleId];
                    
                    let badgeText = '';
                    let badgeClass = '';
                    if (bundle.popular) {
                        badgeText = 'Popular';
                        badgeClass = '';
                    } else if (bundle.best_value) {
                        badgeText = 'Best Value';
                        badgeClass = 'best-value';
                    }
                    
                    const includedProducts = bundle.includes.map(productId => 
                        multiProductPricing.products[productId].name
                    );
                    
                    return `
                        <div class="bundle-card" onclick="selectProduct('bundle', '${bundleId}')" data-bundle-id="${bundleId}">
                            ${badgeText ? `<div class="bundle-badge ${badgeClass}">${badgeText}</div>` : ''}
                            <span class="product-emoji">${bundle.emoji}</span>
                            <div class="bundle-name">${bundle.name}</div>
                            <div class="bundle-description">${tagline}</div>
                            <div class="bundle-includes">
                                <h4>Includes:</h4>
                                <ul>
                                    ${includedProducts.map(productName => `<li>${productName}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="bundle-pricing">
                                <span class="bundle-original-price">$${bundle.individual_total}</span>
                                <span class="bundle-price">${bundle.bundle_price.display}</span>
                            </div>
                            <div class="bundle-savings">${bundle.savings.display}</div>
                        </div>
                    `;
                }).join('');
            }
            
            // Select a product or bundle
            function selectProduct(type, id) {
                // Clear previous selections
                document.querySelectorAll('.product-card, .bundle-card').forEach(card => {
                    card.classList.remove('selected');
                });
                
                // Mark new selection
                const selector = type === 'individual' 
                    ? `[data-product-id="${id}"]` 
                    : `[data-bundle-id="${id}"]`;
                document.querySelector(selector).classList.add('selected');
                
                // Update selection state
                selectedProductType = type;
                selectedProductId = id;
                
                // Show selection summary
                showSelectionSummary(type, id);
            }
            
            // Show selection summary
            function showSelectionSummary(type, id) {
                const selectedProduct = document.getElementById('selectedProduct');
                const selectedItem = document.getElementById('selectedItem');
                
                let itemData;
                if (type === 'individual') {
                    itemData = multiProductPricing.products[id];
                    const tagline = multiProductPricing.hope_driven_messaging.taglines[id];
                    
                    selectedItem.innerHTML = `
                        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
                            <span style="font-size: 2rem;">${itemData.emoji}</span>
                            <div style="text-align: left;">
                                <div style="font-weight: 700; font-size: 1.1rem; color: #333;">${itemData.name}</div>
                                <div style="color: #666; font-size: 0.9rem;">${tagline}</div>
                                <div style="color: #667eea; font-weight: 700; font-size: 1.2rem; margin-top: 0.5rem;">
                                    ${itemData.individual_price.display}
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    itemData = multiProductPricing.bundles[id];
                    const tagline = multiProductPricing.hope_driven_messaging.taglines[id];
                    
                    selectedItem.innerHTML = `
                        <div style="display: flex; align-items: center; justify-content: center; gap: 1rem;">
                            <span style="font-size: 2rem;">${itemData.emoji}</span>
                            <div style="text-align: left;">
                                <div style="font-weight: 700; font-size: 1.1rem; color: #333;">${itemData.name}</div>
                                <div style="color: #666; font-size: 0.9rem;">${tagline}</div>
                                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                                    <span style="color: #888; text-decoration: line-through;">$${itemData.individual_total}</span>
                                    <span style="color: #ff6b6b; font-weight: 700; font-size: 1.2rem;">${itemData.bundle_price.display}</span>
                                    <span style="background: #4caf50; color: white; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.8rem;">
                                        ${itemData.savings.display}
                                    </span>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                selectedProduct.style.display = 'block';
                
                // Scroll to selection
                selectedProduct.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }
            
            // Show upload section after product selection
            function showUploadSection() {
                document.getElementById('uploadSection').style.display = 'block';
                document.getElementById('uploadSection').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }

            // If payment token is present, automatically analyze the previously uploaded resume
            const urlParams = new URLSearchParams(window.location.search);
            const currentPaymentToken = urlParams.get('payment_token');
            if (currentPaymentToken && selectedFile) {
                analyzeResume();
            }
            
        }
        </script>
    </body>
    </html>
    """
    
    # Replace placeholders with actual values
    html_content = html_content.replace("STRIPE_PAYMENT_URL_PLACEHOLDER", STRIPE_PAYMENT_URL)
    html_content = html_content.replace("STRIPE_SUCCESS_TOKEN_PLACEHOLDER", STRIPE_SUCCESS_TOKEN)
    
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "resume-health-checker"}

@app.get("/api/prompts/stats")
async def get_prompt_stats():
    """Get statistics about loaded prompts"""
    return prompt_manager.get_prompt_stats()

@app.post("/api/prompts/reload")
async def reload_prompts_endpoint():
    """Reload prompts from file (for development/testing)"""
    success = prompt_manager.reload_prompts()
    if success:
        return {"status": "success", "message": "Prompts reloaded successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reload prompts")

@app.get("/api/prompts/validate")
async def validate_prompts_endpoint():
    """Validate prompt structure and return any issues"""
    issues = prompt_manager.validate_prompts()
    return {
        "status": "valid" if not issues["errors"] else "invalid",
        "issues": issues
    }

@app.post("/api/track-sentiment")
async def track_user_sentiment(data: dict):
    """Track user sentiment after viewing analysis results"""
    required_fields = ["session_id", "sentiment_score", "sentiment_label"]
    
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    success = track_sentiment(
        session_id=data["session_id"],
        sentiment_score=data["sentiment_score"], 
        sentiment_label=data["sentiment_label"],
        specific_feedback=data.get("specific_feedback")
    )
    
    if success:
        return {"status": "success", "message": "Sentiment tracked successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to track sentiment")

@app.get("/api/analytics/sentiment")
async def get_sentiment_analytics_endpoint(days: int = 7):
    """Get sentiment analytics for the specified period"""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    analytics = sentiment_tracker.get_sentiment_analytics(days)
    return analytics

@app.get("/api/analytics/conversion")
async def get_conversion_analytics_endpoint(days: int = 7):
    """Get conversion analytics correlated with sentiment"""
    if days < 1 or days > 365:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 365")
    
    analytics = sentiment_tracker.get_conversion_analytics(days)
    return analytics

@app.get("/api/pricing-config")
async def get_pricing_config():
    """Get pricing configuration for different countries"""
    # Determine environment and use appropriate config file
    environment = os.getenv("RAILWAY_ENVIRONMENT", "development")
    environment_name = os.getenv("RAILWAY_ENVIRONMENT_NAME", "development")
    
    if environment == "staging" or environment_name == "staging":
        config_file = "pricing_config_staging.json"
    else:
        config_file = "pricing_config.json"  # production/development
    
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        # Fallback configuration if file doesn't exist
        return {
            "pricing": {
                "default": {
                    "price": "$5",
                    "currency": "USD", 
                    "amount": 5,
                    "stripe_url": STRIPE_PAYMENT_URL
                }
            }
        }

# ============================================================================
# STRIPE-FIRST REGIONAL PRICING API
# ============================================================================

@app.get("/api/stripe-pricing/{country_code}")
async def get_stripe_regional_pricing(country_code: str):
    """
    Fetch regional pricing from Stripe as single source of truth.
    Eliminates dual-maintenance of prices in app config + Stripe dashboard.
    """
    try:
        # Regional currency mapping
        currency_map = {
            "US": "usd", "PK": "pkr", "IN": "inr", 
            "HK": "hkd", "AE": "aed", "BD": "bdt",
            "default": "usd"
        }
        
        currency = currency_map.get(country_code.upper(), currency_map["default"])
        
        print(f"🌍 Fetching Stripe pricing for {country_code} ({currency.upper()})")
        
        # Check if Stripe API key is configured
        if not stripe.api_key:
            print("⚠️  Stripe API key not configured, falling back to config file")
            return await get_fallback_pricing(country_code)
        
        # Fetch active prices from Stripe for this currency
        prices = stripe.Price.list(
            currency=currency,
            active=True,
            expand=['data.product'],
            limit=50
        )
        
        print(f"💰 Found {len(prices.data)} Stripe prices for {currency.upper()}")
        
        # Initialize pricing structure
        pricing_data = {
            "region": country_code.upper(),
            "currency": currency.upper(),
            "symbol": get_currency_symbol(currency),
            "products": {},
            "bundles": {},
            "source": "stripe",
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Process Stripe prices into our format
        for price in prices.data:
            metadata = price.metadata
            app_product_id = metadata.get("app_product_id")
            product_type = metadata.get("product_type", "individual")
            
            if not app_product_id:
                continue
                
            price_data = {
                "amount": price.unit_amount // 100,  # Convert from cents
                "display": format_regional_price(price.unit_amount // 100, currency),
                "currency": currency.upper(),
                "stripe_price_id": price.id,
                "stripe_product_id": price.product.id,
                "payment_link": await get_payment_link_for_price(price.id)
            }
            
            # Add to appropriate section
            if product_type == "bundle":
                pricing_data["bundles"][app_product_id] = price_data
                
                # Add bundle-specific data
                if app_product_id in ["career_boost", "job_hunter", "complete_package"]:
                    pricing_data["bundles"][app_product_id].update({
                        "individual_total": calculate_bundle_individual_total(app_product_id, pricing_data["products"]),
                        "savings": calculate_bundle_savings(app_product_id, price_data["amount"], pricing_data["products"]),
                        "popular": app_product_id == "career_boost",
                        "best_value": app_product_id == "complete_package"
                    })
            else:
                pricing_data["products"][app_product_id] = price_data
        
        print(f"✅ Processed {len(pricing_data['products'])} products, {len(pricing_data['bundles'])} bundles")
        return pricing_data
        
    except Exception as e:
        print(f"❌ Error fetching Stripe pricing: {e}")
        # Fallback to config file pricing
        return await get_fallback_pricing(country_code)

async def get_payment_link_for_price(price_id: str) -> str:
    """Get Payment Link URL for a specific Stripe Price ID using optimized static mapping"""
    
    # Static payment links mapping - avoids expensive API calls that cause timeouts
    payment_links_map = {
        # Resume Analysis
        "price_1S2BOBEEk2SJOP4YidngE9GM": "https://buy.stripe.com/test_dRm8wPaXq2028FEgNQ0000F",  # US
        "price_1S2BOCEEk2SJOP4YMxXev3hc": "https://buy.stripe.com/test_6oUfZh7LegUWf4269c0000G",  # PK
        "price_1S2BODEEk2SJOP4YuQDvvMq3": "https://buy.stripe.com/test_00w7sLe9CeMOcVU4140000H",  # IN
        "price_1S2BODEEk2SJOP4YT6hMXMsb": "https://buy.stripe.com/test_eVq3cv8PibACf4269c0000I",  # HK
        "price_1S2BOEEEk2SJOP4YNeXs49Wm": "https://buy.stripe.com/test_fZu6oHc1u202cVUgNQ0000J",  # AE
        "price_1S2BOFEEk2SJOP4YN4S4OUrv": "https://buy.stripe.com/test_dRm7sLfdGbAC7BAbtw0000K",  # BD
        "price_1S2BOFEEk2SJOP4YNuv4nmTw": "https://buy.stripe.com/test_00w4gz9Tm7km9JIdBE0000L",  # default
        
        # Job Fit Analysis  
        "price_1S2BOGEEk2SJOP4YwM3n22OI": "https://buy.stripe.com/test_5kQdR91mQ5ce3lk1SW0000M",  # US
        "price_1S2BOHEEk2SJOP4YS4ljlIdC": "https://buy.stripe.com/test_7sY6oH4z25ce3lk7dg0000N",  # PK
        "price_1S2BOIEEk2SJOP4YVfrVEo2W": "https://buy.stripe.com/test_3cIdR95D65cef42gNQ0000O",  # IN
        "price_1S2BOIEEk2SJOP4YSa6Tx6sv": "https://buy.stripe.com/test_00w5kDaXq0VY6xw7dg0000P",  # HK
        "price_1S2BOJEEk2SJOP4Yitbx80Vk": "https://buy.stripe.com/test_00w28r9Tm202098gNQ0000Q",  # AE
        "price_1S2BOKEEk2SJOP4YrKQPEYBS": "https://buy.stripe.com/test_aFa5kDaXqdIK7BAaps0000R",  # BD
        "price_1S2BOKEEk2SJOP4YZX7zUFxJ": "https://buy.stripe.com/test_aFa7sLe9C346cVU5580000S",  # default
        
        # Cover Letter
        "price_1S2BOLEEk2SJOP4Yx3lacDnw": "https://buy.stripe.com/test_dRm28raXqawy5ts0OS0000T",  # US
        "price_1S2BOMEEk2SJOP4YWZosGVtu": "https://buy.stripe.com/test_8x2dR9e9C5ce7BAcxA0000U",  # PK
        "price_1S2BOMEEk2SJOP4YgmmqcssR": "https://buy.stripe.com/test_3cI7sL0iM5ce9JI2X00000V",  # IN
        "price_1S2BONEEk2SJOP4YPra71b82": "https://buy.stripe.com/test_aFabJ19Tm5ceg868hk0000W",  # HK
        "price_1S2BOOEEk2SJOP4YEyavCCDP": "https://buy.stripe.com/test_3cI00j1mQ5ce9JIeFI0000X",  # AE
        "price_1S2BOOEEk2SJOP4YcSwjBPNA": "https://buy.stripe.com/test_cNi00j9Tm8oq1dcdBE0000Y",  # BD
        "price_1S2BOPEEk2SJOP4YLmDVYxLo": "https://buy.stripe.com/test_eVq8wP2qU0VYdZYdBE0000Z",  # default
        
        # Career Boost Bundle
        "price_1S2BOQEEk2SJOP4YpqEdFuUZ": "https://buy.stripe.com/test_eVq4gzd5y9sucVUdBE00010",  # US
        "price_1S2BOREEk2SJOP4YLkOo0M5z": "https://buy.stripe.com/test_00w00j7Le202aNM9lo00011",  # PK
        "price_1S2BOSEEk2SJOP4YBMksDVBe": "https://buy.stripe.com/test_7sY3cv6Ha5cecVU2X000012",  # IN
        "price_1S2BOSEEk2SJOP4Y8tnawyS7": "https://buy.stripe.com/test_cNi3cve9C8oqcVU7dg00013",  # HK
        "price_1S2BOTEEk2SJOP4YcSvmX5ay": "https://buy.stripe.com/test_fZuaEX5D620209869c00014",  # AE
        "price_1S2BOUEEk2SJOP4YeyAarrap": "https://buy.stripe.com/test_9B68wP0iMgUW5tscxA00015",  # BD
        "price_1S2BOUEEk2SJOP4YEyMXYh0X": "https://buy.stripe.com/test_4gMeVd7LeawyaNMaps00016",  # default
        
        # Job Hunter Bundle
        "price_1S2BOVEEk2SJOP4YQMqsz54E": "https://buy.stripe.com/test_fZucN5fdG2023lkfJM00017",  # US
        "price_1S2BOWEEk2SJOP4YhqKjEanU": "https://buy.stripe.com/test_5kQdR9aXq5ceaNM1SW00018",  # PK
        "price_1S2BOXEEk2SJOP4Yg1zWwj86": "https://buy.stripe.com/test_dRm3cvaXq2027BAbtw00019",  # IN
        "price_1S2BOXEEk2SJOP4YmzCG4kW0": "https://buy.stripe.com/test_28E4gz1mQgUWg86gNQ0001a",  # HK
        "price_1S2BOYEEk2SJOP4YMUWv7jlz": "https://buy.stripe.com/test_00w3cv7Le7kmdZYaps0001b",  # AE
        "price_1S2BOZEEk2SJOP4Yccl9xt1R": "https://buy.stripe.com/test_8x2bJ1aXqawybRQgNQ0001c",  # BD
        "price_1S2BOZEEk2SJOP4YVFMwPYb2": "https://buy.stripe.com/test_6oUfZh1mQ8oq2hg9lo0001d",  # default
        
        # Complete Package Bundle
        "price_1S2BOaEEk2SJOP4YjWnodEBv": "https://buy.stripe.com/test_fZu6oH9TmeMO8FE69c0001e",  # US
        "price_1S2BObEEk2SJOP4YD9uS5Bb0": "https://buy.stripe.com/test_fZu7sLfdG9su5tseFI0001f",  # PK
        "price_1S2BOcEEk2SJOP4YUN6QK97T": "https://buy.stripe.com/test_eVq5kD2qU9sucVU7dg0001g",  # IN
        "price_1S2BOcEEk2SJOP4Y4zDKOkv5": "https://buy.stripe.com/test_bJe6oHc1u5ce1dc1SW0001h",  # HK
        "price_1S2BOdEEk2SJOP4Y17XmGPVH": "https://buy.stripe.com/test_5kQ9AT1mQ48abRQbtw0001i",  # AE
        "price_1S2BOeEEk2SJOP4YCHdCsWep": "https://buy.stripe.com/test_eVqeVd6HacEG5tsbtw0001j",  # BD
        "price_1S2BOeEEk2SJOP4YadL4eM5x": "https://buy.stripe.com/test_dRm4gzc1uawy6xwbtw0001k",  # default
    }
    
    try:
        link = payment_links_map.get(price_id, "")
        if link:
            print(f"✅ Found static payment link for {price_id[:12]}...")
            return link
        else:
            print(f"⚠️  No payment link found for price {price_id}")
            return STRIPE_PAYMENT_URL  # Fallback to environment URL
        
    except Exception as e:
        print(f"❌ Error getting payment link for {price_id}: {e}")
        return STRIPE_PAYMENT_URL  # Fallback to environment URL

def get_currency_symbol(currency: str) -> str:
    """Get currency symbol for display"""
    symbols = {
        "usd": "$", "pkr": "₨", "inr": "₹", 
        "hkd": "HKD ", "aed": "AED ", "bdt": "৳"
    }
    return symbols.get(currency.lower(), "$")

def format_regional_price(amount: int, currency: str) -> str:
    """Format price with proper currency symbol and locale"""
    symbol = get_currency_symbol(currency)
    
    if currency.lower() in ["pkr", "inr", "bdt"]:
        # Format with commas for large numbers
        return f"{symbol}{amount:,}"
    else:
        return f"{symbol}{amount}"

def calculate_bundle_individual_total(bundle_id: str, products: dict) -> int:
    """Calculate what bundle would cost if bought individually"""
    bundle_products = {
        "career_boost": ["resume_analysis", "job_fit_analysis"],
        "job_hunter": ["resume_analysis", "cover_letter"],
        "complete_package": ["resume_analysis", "job_fit_analysis", "cover_letter"]
    }
    
    product_ids = bundle_products.get(bundle_id, [])
    total = sum(products.get(pid, {}).get("amount", 0) for pid in product_ids)
    return total

def calculate_bundle_savings(bundle_id: str, bundle_amount: int, products: dict) -> dict:
    """Calculate savings from bundle pricing"""
    individual_total = calculate_bundle_individual_total(bundle_id, products)
    if individual_total > 0:
        savings_amount = individual_total - bundle_amount
        savings_percentage = round((savings_amount / individual_total) * 100)
        return {
            "amount": savings_amount,
            "percentage": savings_percentage,
            "display": f"Save {format_regional_price(savings_amount, products.get(list(products.keys())[0], {}).get('currency', 'usd'))}"
        }
    return {"amount": 0, "percentage": 0, "display": ""}

async def get_fallback_pricing(country_code: str):
    """Fallback to config file pricing if Stripe API fails"""
    print(f"📁 Using fallback pricing for {country_code}")
    
    try:
        # Use existing pricing config as fallback
        config_response = await get_pricing_config()
        if isinstance(config_response, dict) and "pricing" in config_response:
            country_pricing = config_response["pricing"].get(country_code.upper(), 
                                                           config_response["pricing"]["default"])
            
            # Convert to new format
            return {
                "region": country_code.upper(),
                "currency": country_pricing.get("currency", "USD"),
                "symbol": get_currency_symbol(country_pricing.get("currency", "USD")),
                "products": {
                    "resume_analysis": {
                        "amount": country_pricing.get("amount", 5) * 2,  # $5 -> $10 equivalent
                        "display": country_pricing.get("price", "$10"),
                        "currency": country_pricing.get("currency", "USD"),
                        "payment_link": country_pricing.get("stripe_url", STRIPE_PAYMENT_URL)
                    }
                },
                "bundles": {},
                "source": "fallback",
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        print(f"❌ Fallback pricing failed: {e}")
    
    # Ultimate fallback
    return {
        "region": country_code.upper(),
        "currency": "USD",
        "symbol": "$",
        "products": {
            "resume_analysis": {"amount": 10, "display": "$10", "currency": "USD", "payment_link": STRIPE_PAYMENT_URL}
        },
        "bundles": {},
        "source": "default",
        "error": "Pricing configuration unavailable"
    }

@app.get("/api/mock-geo/{country_code}")
async def mock_geolocation(country_code: str):
    """Mock geolocation API for testing different countries"""
    country_data = {
        "US": {"country_code": "US", "country_name": "United States", "city": "New York"},
        "AE": {"country_code": "AE", "country_name": "United Arab Emirates", "city": "Dubai"},
        "PK": {"country_code": "PK", "country_name": "Pakistan", "city": "Karachi"},
        "IN": {"country_code": "IN", "country_name": "India", "city": "Mumbai"},
        "BD": {"country_code": "BD", "country_name": "Bangladesh", "city": "Dhaka"}
    }
    
    return country_data.get(country_code.upper(), country_data["US"])

@app.post("/api/generate-cover-letter")
async def generate_cover_letter(
    file: UploadFile = File(...),
    job_posting: str = Form(...),
    tier: str = Form(default="free")  # "free" or "premium"
):
    """Generate hope-driven cover letter based on resume and job posting"""
    
    print(f"📄 Cover letter request: {file.filename}, tier: {tier}, job_posting length: {len(job_posting)}")
    
    # Validate file type - reuse existing validation logic
    valid_mime_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream"
    ]
    
    valid_extensions = [".pdf", ".docx"]
    file_extension = os.path.splitext(file.filename.lower())[1]
    
    if not (file.content_type in valid_mime_types or file_extension in valid_extensions):
        print(f"❌ Invalid file: {file.content_type}, extension: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or Word document"
        )
    
    if file.content_type == "application/octet-stream" and file_extension not in valid_extensions:
        print(f"❌ Invalid file type for octet-stream: {file_extension}")
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or Word document"
        )
    
    # Extract text from resume
    try:
        resume_text = resume_to_text(file)
        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Could not extract meaningful text from resume. Please check your file."
            )
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        raise HTTPException(
            status_code=400,
            detail="Error processing resume file. Please try again."
        )
    
    # Validate job posting
    if not job_posting or len(job_posting.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job posting must be at least 20 characters long"
        )
    
    # Generate session ID for tracking
    session_id = str(uuid4())
    
    # Track session start
    try:
        track_session_start(session_id, "cover_letter", "API")
    except Exception as e:
        print(f"⚠️ Error tracking session start: {e}")
    
    # Generate cover letter using AI
    try:
        # Get the appropriate prompt from prompt manager
        user_prompt = format_prompt("cover_letter", tier, 
                                   resume_text=resume_text, 
                                   job_posting=job_posting)
        system_prompt = get_system_prompt("cover_letter", tier)
        
        # Combine system and user prompts
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        print(f"🤖 Generating {tier} cover letter...")
        
        # Get AI analysis
        start_time = time.time()
        ai_response = await get_ai_analysis_with_retry(full_prompt)
        processing_time = time.time() - start_time
        
        # Track analysis completion
        prompt_version = get_prompt("cover_letter", tier).get("version", "unknown")
        try:
            track_analysis_completion(session_id, prompt_version, f"cover_letter_{tier}", processing_time)
        except Exception as e:
            print(f"⚠️ Error tracking analysis completion: {e}")
        
        # AI response is already a dict from get_ai_analysis_with_retry
        if isinstance(ai_response, dict):
            parsed_response = ai_response
        else:
            # Fallback: try to parse as JSON if it's a string
            try:
                parsed_response = json.loads(ai_response)
            except (json.JSONDecodeError, TypeError):
                parsed_response = {
                    "error": "AI response format error",
                    "raw_response": str(ai_response)[:500]
                }
        
        # Add session tracking info
        parsed_response["session_id"] = session_id
        parsed_response["tier"] = tier
        parsed_response["processing_time"] = round(processing_time, 2)
        
        print(f"✅ Cover letter generated successfully in {processing_time:.2f}s")
        return parsed_response
        
    except Exception as e:
        error_msg = f"Error generating cover letter: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/generate-cover-letter-text")
async def generate_cover_letter_text(
    resume_text: str = Form(...),
    job_posting: str = Form(...),
    tier: str = Form(default="free")
):
    """Generate cover letter from text input (for testing/API use)"""
    
    print(f"📄 Cover letter text request: tier: {tier}, resume length: {len(resume_text)}, job_posting length: {len(job_posting)}")
    
    # Validate inputs
    if not resume_text or len(resume_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Resume text must be at least 50 characters long"
        )
    
    if not job_posting or len(job_posting.strip()) < 20:
        raise HTTPException(
            status_code=400,
            detail="Job posting must be at least 20 characters long"
        )
    
    # Generate session ID for tracking
    session_id = str(uuid4())
    
    # Track session start
    try:
        track_session_start(session_id, "cover_letter", "API-Text")
    except Exception as e:
        print(f"⚠️ Error tracking session start: {e}")
    
    # Generate cover letter using AI
    try:
        # Get the appropriate prompt from prompt manager
        user_prompt = format_prompt("cover_letter", tier, 
                                   resume_text=resume_text, 
                                   job_posting=job_posting)
        system_prompt = get_system_prompt("cover_letter", tier)
        
        # Combine system and user prompts
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        print(f"🤖 Generating {tier} cover letter with prompt manager...")
        
        # Get AI analysis
        start_time = time.time()
        ai_response = await get_ai_analysis_with_retry(full_prompt)
        processing_time = time.time() - start_time
        
        # Track analysis completion
        prompt_version = get_prompt("cover_letter", tier).get("version", "unknown")
        try:
            track_analysis_completion(session_id, prompt_version, f"cover_letter_{tier}", processing_time)
        except Exception as e:
            print(f"⚠️ Error tracking analysis completion: {e}")
        
        # AI response is already a dict from get_ai_analysis_with_retry
        if isinstance(ai_response, dict):
            parsed_response = ai_response
        else:
            # Fallback: try to parse as JSON if it's a string
            try:
                parsed_response = json.loads(ai_response)
            except (json.JSONDecodeError, TypeError):
                parsed_response = {
                    "error": "AI response format error",
                    "raw_response": str(ai_response)[:500]
                }
        
        # Add session tracking info
        parsed_response["session_id"] = session_id
        parsed_response["tier"] = tier
        parsed_response["processing_time"] = round(processing_time, 2)
        
        print(f"✅ Cover letter generated successfully in {processing_time:.2f}s")
        return parsed_response
        
    except Exception as e:
        error_msg = f"Error generating cover letter: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/multi-product-pricing")
async def get_multi_product_pricing():
    """Get comprehensive pricing for all products and bundles"""
    try:
        with open("pricing_config_multi_product.json", "r") as f:
            pricing_config = json.load(f)
        return pricing_config
    except FileNotFoundError:
        # Fallback pricing if file doesn't exist
        return {
            "error": "Pricing configuration not found",
            "fallback": {
                "products": {
                    "resume_analysis": {"individual_price": {"amount": 10, "display": "$10"}},
                    "job_fit_analysis": {"individual_price": {"amount": 12, "display": "$12"}},
                    "cover_letter": {"individual_price": {"amount": 8, "display": "$8"}}
                }
            }
        }

@app.post("/api/create-payment-session")
async def create_payment_session(
    product_type: str = Form(...),  # "individual" or "bundle"
    product_id: str = Form(...),    # product name or bundle name
    session_data: str = Form(...)   # JSON string with user's analysis data
):
    """Create a payment session with product selection and user data"""
    
    print(f"💳 Payment session request: {product_type} - {product_id}")
    
    try:
        # Parse session data
        user_session = json.loads(session_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid session data format")
    
    # Load pricing configuration
    try:
        with open("pricing_config_multi_product.json", "r") as f:
            pricing_config = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Pricing configuration not available")
    
    # Generate unique payment session ID
    payment_session_id = str(uuid4())
    
    # Get product/bundle details and pricing
    if product_type == "individual":
        if product_id not in pricing_config["products"]:
            raise HTTPException(status_code=400, detail=f"Product '{product_id}' not found")
        
        product_info = pricing_config["products"][product_id]
        price_info = product_info["individual_price"]
        stripe_url = price_info["stripe_url"]
        
    elif product_type == "bundle":
        if product_id not in pricing_config["bundles"]:
            raise HTTPException(status_code=400, detail=f"Bundle '{product_id}' not found")
        
        bundle_info = pricing_config["bundles"][product_id]
        price_info = bundle_info["bundle_price"]
        stripe_url = price_info["stripe_url"]
        
    else:
        raise HTTPException(status_code=400, detail="Product type must be 'individual' or 'bundle'")
    
    # Store session data for post-payment retrieval
    session_storage = {
        "payment_session_id": payment_session_id,
        "product_type": product_type,
        "product_id": product_id,
        "price_amount": price_info["amount"],
        "currency": price_info["currency"],
        "user_session": user_session,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending"
    }
    
    # In production, this would be stored in a database
    # For now, we'll use a simple file-based approach
    try:
        # Try to load existing sessions
        try:
            with open("payment_sessions.json", "r") as f:
                sessions = json.load(f)
        except FileNotFoundError:
            sessions = {"sessions": {}}
        
        # Add new session
        sessions["sessions"][payment_session_id] = session_storage
        
        # Save back to file
        with open("payment_sessions.json", "w") as f:
            json.dump(sessions, f, indent=2)
            
        print(f"✅ Payment session stored: {payment_session_id}")
        
    except Exception as e:
        print(f"⚠️ Error storing payment session: {e}")
        # Continue anyway - worst case user has to re-upload
    
    # Return payment URL with session ID
    payment_url = f"{stripe_url}?client_reference_id={payment_session_id}"
    
    return {
        "payment_session_id": payment_session_id,
        "payment_url": payment_url,
        "product_type": product_type,
        "product_id": product_id,
        "amount": price_info["amount"],
        "currency": price_info["currency"],
        "display_price": price_info["display"]
    }

@app.get("/api/retrieve-payment-session/{session_id}")
async def retrieve_payment_session(session_id: str):
    """Retrieve stored session data after successful payment"""
    
    print(f"🔍 Retrieving payment session: {session_id}")
    
    try:
        with open("payment_sessions.json", "r") as f:
            sessions = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Payment session not found")
    
    if session_id not in sessions["sessions"]:
        raise HTTPException(status_code=404, detail="Payment session not found")
    
    session_data = sessions["sessions"][session_id]
    
    # Mark as retrieved
    session_data["status"] = "retrieved"
    session_data["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save updated status
    try:
        with open("payment_sessions.json", "w") as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error updating session status: {e}")
    
    return session_data

@app.get("/api/upselling-recommendations/{product_id}")
async def get_upselling_recommendations(product_id: str):
    """Get smart upselling recommendations based on user's current selection"""
    
    print(f"💡 Upselling recommendations for: {product_id}")
    
    try:
        with open("pricing_config_multi_product.json", "r") as f:
            pricing_config = json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Pricing configuration not available")
    
    recommendations = {
        "current_product": product_id,
        "suggestions": []
    }
    
    # Get upselling logic from config
    upselling_config = pricing_config.get("upselling", {})
    messages = upselling_config.get("messages", {})
    product_recommendations = upselling_config.get("recommendations", {})
    
    # If it's a single product, recommend bundles
    if product_id in pricing_config["products"]:
        current_product = pricing_config["products"][product_id]
        current_price = current_product["individual_price"]["amount"]
        
        # Find recommended bundle
        recommended_bundle_id = product_recommendations.get(product_id)
        if recommended_bundle_id and recommended_bundle_id in pricing_config["bundles"]:
            bundle = pricing_config["bundles"][recommended_bundle_id]
            
            # Calculate additional cost
            additional_cost = bundle["bundle_price"]["amount"] - current_price
            savings = bundle["savings"]["display"]
            
            # Get additional products in bundle
            additional_products = [p for p in bundle["includes"] if p != product_id]
            additional_product_names = [pricing_config["products"][p]["name"] for p in additional_products]
            
            suggestion = {
                "type": "bundle_upgrade",
                "bundle_id": recommended_bundle_id,
                "bundle_name": bundle["name"],
                "bundle_emoji": bundle["emoji"],
                "additional_cost": additional_cost,
                "additional_cost_display": f"${additional_cost}",
                "savings": savings,
                "additional_products": additional_product_names,
                "message": messages.get("single_to_bundle", "").format(
                    savings=savings,
                    bundle_name=bundle["name"],
                    additional_products=" + ".join(additional_product_names),
                    additional_cost=f"${additional_cost}"
                ),
                "hope_message": pricing_config["hope_driven_messaging"]["taglines"][recommended_bundle_id]
            }
            recommendations["suggestions"].append(suggestion)
        
        # Also recommend the complete package
        complete_package = pricing_config["bundles"]["complete_package"]
        if product_id not in complete_package["includes"]:  # Only if not already included
            additional_cost_complete = complete_package["bundle_price"]["amount"] - current_price
            
            missing_products = [p for p in complete_package["includes"] if p != product_id]
            missing_product_names = [pricing_config["products"][p]["name"] for p in missing_products]
            
            suggestion = {
                "type": "complete_package",
                "bundle_id": "complete_package",
                "bundle_name": complete_package["name"],
                "bundle_emoji": complete_package["emoji"],
                "additional_cost": additional_cost_complete,
                "additional_cost_display": f"${additional_cost_complete}",
                "total_savings": complete_package["savings"]["display"],
                "missing_products": missing_product_names,
                "message": messages.get("bundle_to_complete", "").format(
                    missing_products=" + ".join(missing_product_names),
                    additional_cost=f"${additional_cost_complete}",
                    total_savings=complete_package["savings"]["display"]
                ),
                "hope_message": pricing_config["hope_driven_messaging"]["taglines"]["complete_package"]
            }
            recommendations["suggestions"].append(suggestion)
    
    # Add success stories and social proof
    recommendations["social_proof"] = pricing_config["hope_driven_messaging"]["success_stories"]
    
    return recommendations

@app.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables"""
    return {
        "stripe_payment_url": STRIPE_PAYMENT_URL,
        "stripe_success_token": STRIPE_SUCCESS_TOKEN,
        "railway_environment": os.getenv("RAILWAY_ENVIRONMENT", "not_set"),
        "railway_environment_name": os.getenv("RAILWAY_ENVIRONMENT_NAME", "not_set"),
        "railway_service_name": os.getenv("RAILWAY_SERVICE_NAME", "not_set"),
        "all_stripe_env_vars": {
            "STRIPE_PAYMENT_URL": os.getenv("STRIPE_PAYMENT_URL", "not_set"),
            "STRIPE_PAYMENT_SUCCESS_TOKEN": os.getenv("STRIPE_PAYMENT_SUCCESS_TOKEN", "not_set")
        },
        "is_production": "production" in STRIPE_PAYMENT_URL.lower(),
        "is_test_mode": "test_" in STRIPE_PAYMENT_URL.lower()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)