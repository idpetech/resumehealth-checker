import pytest
import json
import io
import os
from unittest.mock import patch, Mock
from fastapi import UploadFile
from fastapi.testclient import TestClient

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "resume-health-checker"}

class TestFrontend:
    """Test frontend serving"""
    
    def test_serve_frontend(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Resume Health Checker" in response.text
        assert "text/html" in response.headers["content-type"]

class TestFileProcessing:
    """Test file processing utilities"""
    
    @patch('main.fitz.open')
    def test_extract_text_from_pdf_success(self, mock_fitz_open, sample_pdf_file):
        from main import extract_text_from_pdf
        
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Sample resume text"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.close = Mock()
        mock_fitz_open.return_value = mock_doc
        
        result = extract_text_from_pdf(sample_pdf_file)
        assert result == "Sample resume text"
        mock_doc.close.assert_called_once()
    
    def test_extract_text_from_docx_success(self, sample_docx_file):
        from main import extract_text_from_docx
        
        result = extract_text_from_docx(sample_docx_file)
        assert "John Doe" in result
        assert "Software Developer" in result
        assert "Python, JavaScript, React" in result
    
    def test_extract_text_from_docx_invalid_file(self):
        from main import extract_text_from_docx
        
        with pytest.raises(Exception):
            extract_text_from_docx(b"invalid docx content")
    
    @patch('main.extract_text_from_pdf')
    @patch('main.extract_text_from_docx')
    def test_resume_to_text_pdf(self, mock_docx, mock_pdf):
        from main import resume_to_text
        
        mock_pdf.return_value = "PDF content"
        
        # Create mock UploadFile for PDF
        mock_file = Mock()
        mock_file.content_type = "application/pdf"
        mock_file.file = Mock()
        mock_file.file.read.return_value = b"pdf content"
        
        result = resume_to_text(mock_file)
        assert result == "PDF content"
        mock_pdf.assert_called_once()
        mock_docx.assert_not_called()
    
    @patch('main.extract_text_from_pdf')
    @patch('main.extract_text_from_docx')
    def test_resume_to_text_docx(self, mock_docx, mock_pdf):
        from main import resume_to_text
        
        mock_docx.return_value = "DOCX content"
        
        # Create mock UploadFile for DOCX
        mock_file = Mock()
        mock_file.content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        mock_file.file = Mock()
        mock_file.file.read.return_value = b"docx content"
        
        result = resume_to_text(mock_file)
        assert result == "DOCX content"
        mock_docx.assert_called_once()
        mock_pdf.assert_not_called()
    
    def test_resume_to_text_unsupported_format(self):
        from main import resume_to_text
        from fastapi import HTTPException
        
        # Create mock UploadFile for unsupported format
        mock_file = Mock()
        mock_file.content_type = "text/plain"
        
        with pytest.raises(HTTPException) as exc_info:
            resume_to_text(mock_file)
        
        assert exc_info.value.status_code == 400
        assert "Unsupported file format" in str(exc_info.value.detail)

class TestPromptGeneration:
    """Test AI prompt generation"""
    
    def test_get_free_analysis_prompt(self):
        from main import get_free_analysis_prompt
        
        prompt = get_free_analysis_prompt("Sample resume text")
        assert "Sample resume text" in prompt
        assert "senior recruiter" in prompt.lower()
        assert "major_issues" in prompt
        assert "teaser_message" in prompt
    
    def test_get_paid_analysis_prompt(self):
        from main import get_paid_analysis_prompt
        
        prompt = get_paid_analysis_prompt("Sample resume text")
        assert "Sample resume text" in prompt
        assert "expert recruiter" in prompt.lower()
        assert "ats_optimization" in prompt
        assert "content_clarity" in prompt
        assert "impact_metrics" in prompt
        assert "formatting" in prompt

class TestAIAnalysis:
    """Test AI analysis functionality"""
    
    @patch('main.openai.chat.completions.create')
    async def test_get_ai_analysis_success(self, mock_openai, mock_openai_response):
        from main import get_ai_analysis
        
        mock_openai.return_value = Mock(
            choices=[Mock(message=Mock(content=json.dumps({"test": "data"})))]
        )
        
        result = await get_ai_analysis("test prompt")
        assert result == {"test": "data"}
        mock_openai.assert_called_once()
    
    @patch('main.openai.chat.completions.create')
    async def test_get_ai_analysis_json_parse_error(self, mock_openai):
        from main import get_ai_analysis
        from fastapi import HTTPException
        
        mock_openai.return_value = Mock(
            choices=[Mock(message=Mock(content="invalid json"))]
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_ai_analysis("test prompt")
        
        assert exc_info.value.status_code == 500
        assert "Failed to parse AI response" in str(exc_info.value.detail)
    
    @patch('main.openai.chat.completions.create')
    async def test_get_ai_analysis_openai_error(self, mock_openai):
        from main import get_ai_analysis
        from fastapi import HTTPException
        
        mock_openai.side_effect = Exception("OpenAI API Error")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_ai_analysis("test prompt")
        
        assert exc_info.value.status_code == 500
        assert "AI analysis failed" in str(exc_info.value.detail)

class TestResumeAnalysisEndpoint:
    """Test the main resume analysis endpoint"""
    
    @patch('main.get_ai_analysis')
    @patch('main.resume_to_text')
    def test_check_resume_free_analysis(self, mock_resume_to_text, mock_ai_analysis, client, sample_pdf_file):
        mock_resume_to_text.return_value = "Sample resume content"
        mock_ai_analysis.return_value = {
            "overall_score": 75,
            "major_issues": ["Issue 1", "Issue 2", "Issue 3"],
            "teaser_message": "Upgrade for detailed analysis"
        }
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "free"
        assert data["overall_score"] == 75
        assert len(data["major_issues"]) == 3
        assert "teaser_message" in data
    
    @patch('main.STRIPE_SUCCESS_TOKEN', 'payment_success_123')
    @patch('main.get_ai_analysis') 
    @patch('main.resume_to_text')
    def test_check_resume_paid_analysis(self, mock_resume_to_text, mock_ai_analysis, client, sample_pdf_file):
        mock_resume_to_text.return_value = "Sample resume content"
        mock_ai_analysis.return_value = {
            "overall_score": 85,
            "ats_optimization": {"score": 80, "issues": [], "improvements": []},
            "content_clarity": {"score": 90, "issues": [], "improvements": []},
            "impact_metrics": {"score": 75, "issues": [], "improvements": []},
            "formatting": {"score": 85, "issues": [], "improvements": []},
            "top_recommendations": ["Rec 1", "Rec 2", "Rec 3"]
        }
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")},
            data={"payment_token": "payment_success_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_type"] == "paid"
        assert data["overall_score"] == 85
        assert "ats_optimization" in data
        assert "top_recommendations" in data
    
    def test_check_resume_unsupported_file_type(self, client):
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.txt", b"text content", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Please upload a PDF or Word document" in response.json()["detail"]
    
    @patch('main.resume_to_text')
    def test_check_resume_empty_file_content(self, mock_resume_to_text, client, sample_pdf_file):
        mock_resume_to_text.return_value = ""  # Empty string should trigger the strip() check
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 400
        # Test passes if we get a 400 status code (empty file rejected)
    
    @patch('main.resume_to_text')
    def test_check_resume_file_processing_error(self, mock_resume_to_text, client, sample_pdf_file):
        mock_resume_to_text.side_effect = Exception("File processing error")
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 400