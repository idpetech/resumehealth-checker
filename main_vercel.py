from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
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
    is_paid = payment_token == STRIPE_SUCCESS_TOKEN or payment_token == 'session_validated'
    
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
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
                font-weight: 700;
            }
            
            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Resume Health Checker</h1>
                <p>Get expert feedback to land more interviews</p>
            </div>
            
            <div class="upload-section">
                <div class="file-upload" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" accept=".pdf,.docx" onchange="handleFileSelect(event)">
                    <div class="upload-text">
                        <strong>Click to upload your resume</strong><br>
                        or drag and drop it here
                    </div>
                    <div class="file-types">Supports PDF and Word documents</div>
                </div>
                <button class="analyze-btn" id="analyzeBtn" onclick="analyzeResume()" disabled>
                    Analyze My Resume - FREE
                </button>
            </div>
            
            <div class="results-section" id="resultsSection">
                <!-- Results will be displayed here -->
            </div>
        </div>

        <script>
            let selectedFile = null;
            let currentAnalysis = null;

            // Check for payment success with session validation
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('client_reference_id');
            const paymentToken = urlParams.get('payment_token'); // Keep for backward compatibility
            
            // If returning from payment with session ID, restore the previously uploaded file
            if (sessionId) {
                console.log('🎉 Payment return detected with session ID:', sessionId);
                const savedFileData = localStorage.getItem(`resume_${sessionId}`);
                console.log('📁 Stored file data found:', savedFileData ? 'YES' : 'NO');
                if (savedFileData) {
                    const fileData = JSON.parse(savedFileData);
                    // Recreate file from stored data
                    fetch('data:' + fileData.type + ';base64,' + fileData.data)
                        .then(res => res.blob())
                        .then(blob => {
                            const file = new File([blob], fileData.name, { type: fileData.type });
                            selectedFile = file;
                            
                            // Clear the stored file data first
                            localStorage.removeItem(`resume_${sessionId}`);
                            
                            // Update UI to show payment success
                            updateUploadUI(file.name, true);
                            
                            // Force immediate paid analysis (add small delay to ensure UI updates)
                            setTimeout(() => {
                                console.log('🔄 Starting automatic paid analysis...');
                                analyzeResume();
                            }, 100);
                        });
                }
            }
            // Fallback: Check for old payment token (backward compatibility during transition)
            else if (paymentToken) {
                const savedFileData = localStorage.getItem('pendingResumeUpload');
                if (savedFileData) {
                    const fileData = JSON.parse(savedFileData);
                    // Recreate file from stored data
                    fetch('data:' + fileData.type + ';base64,' + fileData.data)
                        .then(res => res.blob())
                        .then(blob => {
                            const file = new File([blob], fileData.name, { type: fileData.type });
                            selectedFile = file;
                            
                            // Clear the stored file data first
                            localStorage.removeItem('pendingResumeUpload');
                            
                            // Update UI to show payment success
                            updateUploadUI(file.name, true);
                            
                            // Force immediate paid analysis (add small delay to ensure UI updates)
                            setTimeout(() => {
                                console.log('🔄 Starting automatic paid analysis...');
                                analyzeResume();
                            }, 100);
                        });
                }
            }

            // Handle file upload
            function handleFileSelect(event) {
                const file = event.target.files[0];
                if (file) {
                    selectedFile = file;
                    document.getElementById('analyzeBtn').disabled = false;
                    
                    // Update upload UI to show selected file
                    updateUploadUI(file.name, false);
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
                        <p>Analyzing your resume...</p>
                    </div>
                `;

                const formData = new FormData();
                formData.append('file', selectedFile);
                
                // Check for valid payment (session-based or backward compatibility)
                const urlParams = new URLSearchParams(window.location.search);
                const sessionId = urlParams.get('client_reference_id');
                const paymentToken = urlParams.get('payment_token');
                
                if (sessionId) {
                    // New session-based validation - no longer send token
                    console.log('💰 Sending session_validated token for session:', sessionId);
                    formData.append('payment_token', 'session_validated');
                } else if (paymentToken) {
                    // Backward compatibility for old payment tokens
                    console.log('💰 Sending legacy payment token:', paymentToken);
                    formData.append('payment_token', paymentToken);
                } else {
                    console.log('🆓 No payment token - free analysis');
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
                    resultsSection.innerHTML = `
                        <div style="color: #f44336; text-align: center; padding: 2rem;">
                            <h3>Analysis Failed</h3>
                            <p>Something went wrong. Please try again.</p>
                            <small>Error: ${error.message}</small>
                        </div>
                    `;
                }
            }

            function displayResults(analysis) {
                const resultsSection = document.getElementById('resultsSection');
                const score = parseInt(analysis.overall_score);
                const scoreClass = getScoreClass(score);

                // Debug logging
                console.log('Analysis type:', analysis.analysis_type);
                console.log('Has text_rewrites:', 'text_rewrites' in analysis);
                console.log('Has sample_improvements:', 'sample_improvements' in analysis);
                if (analysis.text_rewrites) {
                    console.log('Number of rewrites:', analysis.text_rewrites.length);
                }

                if (analysis.analysis_type === 'free') {
                    // Display free analysis with upgrade prompt
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
                            <a href="#" class="upgrade-btn" onclick="goToStripeCheckout()">
                                Unlock Full Report - $5
                            </a>
                        </div>
                    `;
                } else {
                    // Display detailed paid analysis
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
                }
            }

            function getScoreClass(score) {
                if (score >= 80) return 'score-excellent';
                if (score >= 60) return 'score-good';
                if (score >= 40) return 'score-fair';
                return 'score-poor';
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
                        localStorage.setItem(`resume_${sessionId}`, JSON.stringify(fileData));
                        
                        // Now go to Stripe with session ID
                        const stripeUrl = 'STRIPE_PAYMENT_URL_PLACEHOLDER';
                        const successUrl = encodeURIComponent(window.location.origin + '/?client_reference_id=' + sessionId);
                        const fullUrl = stripeUrl + '?success_url=' + successUrl;
                        window.location.href = fullUrl;
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

            // If payment token is present, automatically analyze the previously uploaded resume
            if (paymentToken && selectedFile) {
                analyzeResume();
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

@app.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment variables"""
    return {
        "stripe_payment_url": STRIPE_PAYMENT_URL,
        "stripe_success_token": STRIPE_SUCCESS_TOKEN,
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
        "is_production": "production" in STRIPE_PAYMENT_URL.lower(),
        "is_test_mode": "test_" in STRIPE_PAYMENT_URL.lower()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)