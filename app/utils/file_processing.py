"""
File Processing Utilities

This module handles file upload, processing, and text extraction
for PDF, DOCX, and TXT files.
"""
import io
import os
import tempfile
import logging
from fastapi import UploadFile, HTTPException
from docx import Document
import fitz  # PyMuPDF

from ..config.settings import constants

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file using PyMuPDF"""
    try:
        logger.info(f"Processing PDF file, size: {len(file_content)} bytes")
        
        # Create a temporary file to work with PyMuPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_content)
            tmp_file.flush()
            
            # Open PDF and extract text
            doc = fitz.open(tmp_file.name)
            text = ""
            for page_num, page in enumerate(doc):
                text += page.get_text()
                
            doc.close()
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text.strip()
            
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file using python-docx"""
    try:
        logger.info(f"Processing DOCX file, size: {len(file_content)} bytes")
        
        doc = Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
        logger.info(f"Successfully extracted {len(text)} characters from DOCX")
        return text.strip()
        
    except Exception as e:
        logger.error(f"DOCX processing error: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing DOCX: {str(e)}")

def resume_to_text(file: UploadFile) -> str:
    """Convert uploaded resume file to text"""
    logger.info(f"Processing file: {file.filename}, content_type: {file.content_type}")
    
    # Validate file size (check content length if available)
    file_content = file.file.read()
    if len(file_content) > constants.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {constants.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Validate content type
    if file.content_type not in constants.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Please upload a PDF, DOCX, or TXT file."
        )
    
    if file.content_type == "application/pdf":
        return extract_text_from_pdf(file_content)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_content)
    elif file.content_type == "text/plain":
        return file_content.decode('utf-8')
    else:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file format. Please upload a PDF, DOCX, or TXT file."
        )