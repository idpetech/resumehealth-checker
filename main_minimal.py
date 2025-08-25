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

# Load environment variables
load_dotenv()

app = FastAPI(title="Resume Health Checker API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
STRIPE_SUCCESS_TOKEN = os.getenv("STRIPE_PAYMENT_SUCCESS_TOKEN", "payment_success_123")

def validate_pdf_magic_bytes(file_content: bytes) -> bool:
    """Validate PDF magic bytes to ensure file integrity"""
    # PDF files start with %PDF (hex: 25 50 44 46)
    pdf_magic = b'%PDF'
    return file_content.startswith(pdf_magic)

def validate_docx_magic_bytes(file_content: bytes) -> bool:
    """Validate DOCX magic bytes to ensure file integrity"""
    # DOCX files are ZIP files that start with PK (hex: 50 4B)
    docx_magic = b'PK'
    return file_content.startswith(docx_magic)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file - Lambda-optimized version"""
    # Validate magic bytes first
    if not validate_pdf_magic_bytes(file_bytes):
        raise HTTPException(status_code=400, detail="Invalid PDF file: Magic bytes do not match PDF format")
    
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        if "password" in str(e).lower():
            raise HTTPException(status_code=400, detail="PDF file is password-protected. Please remove password protection and try again.")
        else:
            raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file - Lambda-optimized version"""
    # Validate magic bytes first
    if not validate_docx_magic_bytes(file_bytes):
        raise HTTPException(status_code=400, detail="Invalid DOCX file: Magic bytes do not match DOCX format")
    
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing DOCX: {str(e)}")

@app.post("/api/check-resume")
async def check_resume(file: UploadFile = File(...), payment_token: Optional[str] = Form(None)):
    """Main endpoint for resume analysis - Lambda-optimized version"""
    
    # Read file content as bytes
    file_content = await file.read()
    
    # Validate file size (reasonable limit for resumes)
    if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Please upload a file smaller than 10MB.")
    
    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")
    
    # DEBUG: Log file information
    print(f"File info: name={file.filename}, type={file.content_type}, size={len(file_content)}")
    print(f"First 20 bytes: {file_content[:20].hex()}")
    print(f"Magic bytes: {file_content[:4]}")
    
    # Extract text based on file type (check both content_type and filename)
    filename = file.filename.lower() if file.filename else ""
    
    if file.content_type == "application/pdf" or filename.endswith(".pdf"):
        resume_text = extract_text_from_pdf(file_content)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or filename.endswith((".docx", ".doc")):
        resume_text = extract_text_from_docx(file_content)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Content-Type: {file.content_type}, Filename: {file.filename}. Please upload a PDF or DOCX file.")
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file. The file may be corrupted or contain no readable text.")
    
    # Simple analysis for testing
    is_paid = payment_token == STRIPE_SUCCESS_TOKEN
    
    if is_paid:
        analysis = {
            "overall_score": "85",
            "analysis_type": "paid",
            "major_issues": [
                "Missing quantified achievements",
                "Generic job descriptions",
                "Weak action verbs"
            ],
            "top_recommendations": [
                "Add specific metrics and numbers to achievements",
                "Use stronger action verbs like 'spearheaded', 'optimized', 'delivered'",
                "Customize resume for each job application"
            ]
        }
    else:
        analysis = {
            "overall_score": "72",
            "analysis_type": "free",
            "major_issues": [
                "Missing quantified results",
                "Generic descriptions",
                "Weak formatting"
            ],
            "teaser_message": "Get detailed analysis with specific improvements for $5"
        }
    
    return JSONResponse(content=analysis)

@app.options("/api/check-resume")
async def check_resume_options():
    """Handle CORS preflight"""
    return {"message": "OK"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "resume-health-checker-minimal"}

@app.options("/api/health")
async def health_options():
    """Handle CORS preflight"""
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)