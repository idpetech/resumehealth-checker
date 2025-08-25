from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import io
from typing import Optional
from dotenv import load_dotenv
import openai
from docx import Document
import fitz  # PyMuPDF
import tempfile

# Load environment variables
load_dotenv()

app = FastAPI(title="Resume Health Checker API", version="1.0.0")

# Add CORS middleware for cross-origin requests from S3 static site
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://resume.idpetech.com.s3-website-us-east-1.amazonaws.com",
        "https://resume.idpetech.com",
        "http://localhost:3000",  # For local development
        "http://127.0.0.1:3000",
        "*"  # Remove this in production and specify exact origins
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
STRIPE_SUCCESS_TOKEN = os.getenv("STRIPE_PAYMENT_SUCCESS_TOKEN", "payment_success_123")
STRIPE_PAYMENT_URL = os.getenv("STRIPE_PAYMENT_URL", "https://buy.stripe.com/test_placeholder")

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
    """Generate prompt for free resume analysis (teaser)"""
    return f"""
    You are a senior recruiter reviewing this resume. Provide a brief, high-level analysis focusing on 3 major weaknesses that would prevent this candidate from getting interviews.

    Resume content:
    {resume_text}

    Respond in JSON format with exactly this structure:
    {{
        "overall_score": "A number from 1-100",
        "major_issues": [
            "Issue 1: Brief description",
            "Issue 2: Brief description", 
            "Issue 3: Brief description"
        ],
        "teaser_message": "A compelling message encouraging the user to get the full analysis for $5"
    }}

    Keep it concise but actionable. Make the teaser compelling.
    """

def get_paid_analysis_prompt(resume_text: str) -> str:
    """Generate prompt for detailed paid resume analysis"""
    return f"""
    You are an expert recruiter and ATS specialist. Provide a comprehensive resume analysis with specific, actionable feedback AND actual text improvements.

    Resume content:
    {resume_text}

    Respond in JSON format with exactly this structure:
    {{
        "overall_score": "A number from 1-100",
        "major_issues": [
            "Brief issue 1 from free version",
            "Brief issue 2 from free version",
            "Brief issue 3 from free version"
        ],
        "ats_optimization": {{
            "score": "1-100",
            "issues": ["List specific ATS issues"],
            "improvements": ["List specific fixes"]
        }},
        "content_clarity": {{
            "score": "1-100", 
            "issues": ["List clarity issues"],
            "improvements": ["List specific improvements"]
        }},
        "impact_metrics": {{
            "score": "1-100",
            "issues": ["List missing or weak metrics"],
            "improvements": ["List specific metric improvements"]
        }},
        "formatting": {{
            "score": "1-100",
            "issues": ["List formatting issues"], 
            "improvements": ["List formatting fixes"]
        }},
        "text_rewrites": [
            {{
                "section": "Professional Summary/Experience/Skills/etc",
                "original": "Copy the original weak text from resume",
                "improved": "Provide the improved version with metrics and impact",
                "explanation": "Why this change improves the resume"
            }},
            {{
                "section": "Another section name",
                "original": "Another original weak text",
                "improved": "Another improved version",
                "explanation": "Why this change helps"
            }},
            {{
                "section": "Third section",
                "original": "Third original text",
                "improved": "Third improved text",
                "explanation": "Benefits of this change"
            }}
        ],
        "sample_improvements": {{
            "weak_bullets": [
                "Example of a weak bullet point from the resume",
                "Another weak bullet point"
            ],
            "strong_bullets": [
                "Improved version with metrics and impact",
                "Another improved bullet with quantified results"
            ]
        }},
        "top_recommendations": [
            "Priority 1: Most important fix with specific action",
            "Priority 2: Second most important fix with specific action", 
            "Priority 3: Third most important fix with specific action"
        ]
    }}

    IMPORTANT: 
    1. Include actual text from their resume in the "original" fields
    2. Provide specific improved versions they can copy-paste
    3. Focus on adding metrics, impact, and ATS-friendly keywords
    4. Make the improvements immediately actionable
    """

async def get_ai_analysis(prompt: str) -> dict:
    """Get analysis from OpenAI GPT-4o mini"""
    try:
        print(f"🔍 Calling OpenAI API with model: gpt-4o-mini")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert resume reviewer. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
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
        print(f"✅ JSON parsing successful")
        return parsed_result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {str(e)}")
        print(f"Raw AI response: {result[:200]}...")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@app.post("/api/check-resume")
async def check_resume(
    file: UploadFile = File(...),
    payment_token: Optional[str] = Form(None)
):
    """
    Main endpoint for resume analysis
    - Without payment_token: Returns free teaser analysis
    - With valid payment_token: Returns detailed paid analysis
    """
    
    print(f"📁 File upload received: {file.filename}, type: {file.content_type}, size: {file.size}")
    
    # Validate file type
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        print(f"❌ Invalid file type: {file.content_type}")
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
    is_paid = payment_token == STRIPE_SUCCESS_TOKEN
    
    # Generate appropriate prompt and get AI analysis
    if is_paid:
        prompt = get_paid_analysis_prompt(resume_text)
    else:
        prompt = get_free_analysis_prompt(resume_text)
    
    analysis = await get_ai_analysis(prompt)
    
    # Add metadata to response
    analysis["analysis_type"] = "paid" if is_paid else "free"
    analysis["timestamp"] = "2024-01-01T00:00:00Z"  # You could use datetime.now() here
    
    return JSONResponse(content=analysis)

@app.get("/api/health")
async def health_check():
    """API health check endpoint"""
    return {"status": "healthy", "service": "resume-health-checker-api", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)