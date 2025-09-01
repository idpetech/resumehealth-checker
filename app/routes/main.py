"""
Main Routes Module

This module contains the main frontend route and health check.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config.settings import constants
from ..services.template_service import template_service

# Initialize router and limiter
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.get("/", response_class=HTMLResponse)
@limiter.limit(constants.API_RATE_LIMIT)
async def serve_frontend(request: Request):
    """Serve the main HTML page"""
    try:
        html_content = template_service.get_index_html()
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error loading page</h1><p>{str(e)}</p></body></html>", status_code=500)

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "resume-health-checker"}