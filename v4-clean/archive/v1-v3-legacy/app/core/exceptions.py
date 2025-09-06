"""
Exception handling for the application.

Provides structured error responses and logging.
"""
import logging
from typing import Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# =============================================================================
# CUSTOM EXCEPTION CLASSES
# =============================================================================

class ResumeAnalysisError(Exception):
    """Base exception for resume analysis errors"""
    pass

class FileProcessingError(ResumeAnalysisError):
    """Raised when file processing fails"""
    pass

class AIAnalysisError(ResumeAnalysisError):
    """Raised when AI analysis fails"""
    pass

class PaymentError(Exception):
    """Base exception for payment errors"""
    pass

class StripeError(PaymentError):
    """Raised when Stripe operations fail"""
    pass

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    
    # Hide sensitive details in production
    from .config import config
    if config.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "Something went wrong. Please try again.",
                "timestamp": "2025-09-02T12:00:00Z"
            }
        )
    else:
        # Show details in development
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": str(exc),
                "type": type(exc).__name__,
                "timestamp": "2025-09-02T12:00:00Z"
            }
        )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions"""
    logger.warning(f"HTTP exception on {request.url}: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": "2025-09-02T12:00:00Z"
        }
    )

async def file_processing_exception_handler(request: Request, exc: FileProcessingError) -> JSONResponse:
    """Handler for file processing errors"""
    logger.error(f"File processing error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "file_processing_error",
            "message": str(exc),
            "timestamp": "2025-09-02T12:00:00Z"
        }
    )

async def ai_analysis_exception_handler(request: Request, exc: AIAnalysisError) -> JSONResponse:
    """Handler for AI analysis errors"""
    logger.error(f"AI analysis error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=503,  # Service Unavailable
        content={
            "error": "ai_analysis_error",
            "message": "AI analysis is temporarily unavailable. Please try again later.",
            "timestamp": "2025-09-02T12:00:00Z"
        }
    )

async def payment_exception_handler(request: Request, exc: PaymentError) -> JSONResponse:
    """Handler for payment errors"""
    logger.error(f"Payment error on {request.url}: {exc}")
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "payment_error",
            "message": str(exc),
            "timestamp": "2025-09-02T12:00:00Z"
        }
    )

# =============================================================================
# EXCEPTION HANDLER REGISTRATION
# =============================================================================

def add_exception_handlers(app):
    """Add all exception handlers to the FastAPI app"""
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(FileProcessingError, file_processing_exception_handler)
    app.add_exception_handler(AIAnalysisError, ai_analysis_exception_handler)
    app.add_exception_handler(PaymentError, payment_exception_handler)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_error_response(error_type: str, message: str, status_code: int = 400) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "error": error_type,
        "message": message,
        "status_code": status_code,
        "timestamp": "2025-09-02T12:00:00Z"
    }

def validate_file_upload(filename: str, file_size: int, content_type: str) -> None:
    """Validate uploaded file and raise appropriate exceptions"""
    from .config import config
    
    # Check file size
    if file_size > config.max_file_size:
        raise FileProcessingError(
            f"File too large. Maximum size is {config.max_file_size // (1024*1024)}MB"
        )
    
    # Check file extension
    if not filename:
        raise FileProcessingError("Filename is required")
    
    file_ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
    if file_ext not in config.allowed_file_types:
        raise FileProcessingError(
            f"Unsupported file type. Allowed types: {', '.join(config.allowed_file_types)}"
        )
    
    # Check content type (with fallback for generic uploads)
    allowed_content_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/octet-stream"  # Generic uploads
    }
    
    if content_type not in allowed_content_types:
        raise FileProcessingError(
            f"Unsupported content type: {content_type}"
        )