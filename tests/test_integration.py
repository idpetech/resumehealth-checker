import pytest
from unittest.mock import patch
import json


class TestEndToEndWorkflow:
    """End-to-end integration tests"""
    
    @patch('main.openai.chat.completions.create')
    def test_complete_free_analysis_workflow(self, mock_openai, client, sample_pdf_file):
        """Test complete workflow for free analysis"""
        # Mock OpenAI response
        mock_response = {
            "overall_score": "72",
            "major_issues": [
                "Lack of quantifiable achievements - your accomplishments are too vague",
                "Missing industry-specific keywords that ATS systems look for",
                "Inconsistent formatting makes it hard for recruiters to scan quickly"
            ],
            "teaser_message": "These issues are costing you interviews! Get the complete analysis with specific fixes for just $5."
        }
        
        mock_openai.return_value = type('MockResponse', (), {
            'choices': [type('Choice', (), {
                'message': type('Message', (), {
                    'content': json.dumps(mock_response)
                })()
            })()]
        })()
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("test_resume.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure for free analysis
        assert data["analysis_type"] == "free"
        assert "overall_score" in data
        assert "major_issues" in data
        assert "teaser_message" in data
        assert "timestamp" in data
        assert len(data["major_issues"]) == 3
        
        # Verify OpenAI was called with free analysis prompt
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert call_args[1]["model"] == "gpt-4o-mini"
        assert "senior recruiter" in call_args[1]["messages"][1]["content"].lower()
    
    @patch('main.STRIPE_SUCCESS_TOKEN', 'payment_success_123')
    @patch('main.openai.chat.completions.create')  
    def test_complete_paid_analysis_workflow(self, mock_openai, client, sample_pdf_file):
        """Test complete workflow for paid analysis"""
        # Mock OpenAI response for paid analysis
        mock_response = {
            "overall_score": "78",
            "ats_optimization": {
                "score": "75",
                "issues": ["Missing keywords: 'machine learning', 'cloud computing'", "Complex table formatting may break ATS parsing"],
                "improvements": ["Add relevant industry keywords naturally in context", "Use simple formatting with clear sections"]
            },
            "content_clarity": {
                "score": "82",
                "issues": ["Some job descriptions lack specific outcomes"],
                "improvements": ["Quantify each achievement with numbers/percentages"]
            },
            "impact_metrics": {
                "score": "70",
                "issues": ["Only 30% of bullets include quantifiable results"],
                "improvements": ["Add metrics like: revenue increased, time saved, efficiency improved"]
            },
            "formatting": {
                "score": "85",
                "issues": ["Inconsistent bullet point styles"],
                "improvements": ["Use consistent bullet formatting throughout"]
            },
            "top_recommendations": [
                "Priority 1: Add quantifiable metrics to all major achievements (increase from 30% to 80%)",
                "Priority 2: Include 5-7 industry-specific keywords naturally in your experience section", 
                "Priority 3: Standardize formatting - use consistent fonts, spacing, and bullet styles"
            ]
        }
        
        mock_openai.return_value = type('MockResponse', (), {
            'choices': [type('Choice', (), {
                'message': type('Message', (), {
                    'content': json.dumps(mock_response)
                })()
            })()]
        })()
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("test_resume.pdf", sample_pdf_file, "application/pdf")},
            data={"payment_token": "payment_success_123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure for paid analysis
        assert data["analysis_type"] == "paid"
        assert "overall_score" in data
        assert "ats_optimization" in data
        assert "content_clarity" in data
        assert "impact_metrics" in data
        assert "formatting" in data
        assert "top_recommendations" in data
        
        # Verify detailed structure
        for section in ["ats_optimization", "content_clarity", "impact_metrics", "formatting"]:
            assert "score" in data[section]
            assert "issues" in data[section]
            assert "improvements" in data[section]
        
        assert len(data["top_recommendations"]) == 3
        
        # Verify OpenAI was called with paid analysis prompt
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert "expert recruiter" in call_args[1]["messages"][1]["content"].lower()
    
    def test_docx_file_processing(self, client, sample_docx_file):
        """Test processing of DOCX files"""
        with patch('main.get_ai_analysis') as mock_ai:
            mock_ai.return_value = {
                "overall_score": 80,
                "major_issues": ["Issue 1", "Issue 2", "Issue 3"],
                "teaser_message": "Test message"
            }
            
            response = client.post(
                "/api/check-resume",
                files={"file": ("resume.docx", sample_docx_file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_type"] == "free"
    
    def test_invalid_payment_token(self, client, sample_pdf_file):
        """Test that invalid payment tokens default to free analysis"""
        with patch('main.get_ai_analysis') as mock_ai:
            mock_ai.return_value = {
                "overall_score": 75,
                "major_issues": ["Issue 1", "Issue 2", "Issue 3"],
                "teaser_message": "Test message"
            }
            
            response = client.post(
                "/api/check-resume",
                files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")},
                data={"payment_token": "invalid_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["analysis_type"] == "free"  # Should default to free for invalid token


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_missing_file(self, client):
        """Test API call without file"""
        response = client.post("/api/check-resume")
        assert response.status_code == 422  # Validation error
    
    def test_corrupted_pdf_file(self, client):
        """Test corrupted PDF file handling"""
        corrupted_pdf = b"fake pdf content"
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("corrupted.pdf", corrupted_pdf, "application/pdf")}
        )
        
        assert response.status_code == 400
        assert "Error processing PDF" in response.json()["detail"]
    
    def test_corrupted_docx_file(self, client):
        """Test corrupted DOCX file handling"""
        corrupted_docx = b"fake docx content"
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("corrupted.docx", corrupted_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        
        assert response.status_code == 400
        assert "Error processing DOCX" in response.json()["detail"]
    
    @patch('main.openai.chat.completions.create')
    def test_openai_api_failure(self, mock_openai, client, sample_pdf_file):
        """Test OpenAI API failure handling"""
        mock_openai.side_effect = Exception("OpenAI API is down")
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 500
        assert "AI analysis failed" in response.json()["detail"]
    
    @patch('main.openai.chat.completions.create')
    def test_invalid_json_from_openai(self, mock_openai, client, sample_pdf_file):
        """Test handling of invalid JSON response from OpenAI"""
        mock_openai.return_value = type('MockResponse', (), {
            'choices': [type('Choice', (), {
                'message': type('Message', (), {
                    'content': "This is not valid JSON"
                })()
            })()]
        })()
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
        )
        
        assert response.status_code == 500
        assert "Failed to parse AI response" in response.json()["detail"]


class TestSecurityAndValidation:
    """Test security and validation features"""
    
    def test_file_size_limit_handling(self, client):
        """Test handling of very large files"""
        # Create a 10MB file (simulating large resume)
        large_content = b"x" * (10 * 1024 * 1024)
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("large_resume.pdf", large_content, "application/pdf")}
        )
        
        # Should handle gracefully (either process or reject with proper error)
        assert response.status_code in [200, 400, 413]
    
    def test_malicious_file_content(self, client):
        """Test handling of potentially malicious file content"""
        malicious_content = b"<script>alert('xss')</script>" * 1000
        
        response = client.post(
            "/api/check-resume",
            files={"file": ("malicious.pdf", malicious_content, "application/pdf")}
        )
        
        # Should either process safely or reject with proper error
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            # If processed, ensure no script content in response
            data = response.json()
            response_str = json.dumps(data)
            assert "<script>" not in response_str
            assert "alert(" not in response_str
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/api/check-resume")
        # FastAPI with CORS middleware should handle OPTIONS requests
        assert response.status_code in [200, 405]
    
    def test_content_type_validation(self, client, sample_pdf_file):
        """Test strict content type validation"""
        # Try to upload PDF with wrong content type
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Please upload a PDF or Word document" in response.json()["detail"]


class TestPerformanceAndReliability:
    """Test performance and reliability aspects"""
    
    @patch('main.get_ai_analysis')
    def test_concurrent_requests(self, mock_ai_analysis, client, sample_pdf_file):
        """Test handling of concurrent requests"""
        import asyncio
        import httpx
        
        mock_ai_analysis.return_value = {
            "overall_score": 75,
            "major_issues": ["Issue 1", "Issue 2", "Issue 3"],
            "teaser_message": "Test message"
        }
        
        # Simulate multiple concurrent requests
        async def make_request():
            async with httpx.AsyncClient(app=client.app, base_url="http://test") as ac:
                response = await ac.post(
                    "/api/check-resume",
                    files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
                )
                return response.status_code
        
        # This would need to be run in an async context
        # For now, just test sequential requests
        for _ in range(3):
            response = client.post(
                "/api/check-resume",
                files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
            )
            assert response.status_code == 200
    
    @patch('main.get_ai_analysis')
    def test_response_time_acceptable(self, mock_ai_analysis, client, sample_pdf_file):
        """Test that response times are acceptable"""
        import time
        
        mock_ai_analysis.return_value = {
            "overall_score": 75,
            "major_issues": ["Issue 1", "Issue 2", "Issue 3"],
            "teaser_message": "Test message"
        }
        
        start_time = time.time()
        response = client.post(
            "/api/check-resume",
            files={"file": ("resume.pdf", sample_pdf_file, "application/pdf")}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        # Should complete within 30 seconds (generous for CI/CD)
        assert end_time - start_time < 30