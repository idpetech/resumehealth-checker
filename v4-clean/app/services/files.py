"""
File Processing Service

Handles PDF, DOCX, and TXT file processing with built-in tools only.
No external dependencies beyond what's in requirements.txt.
"""
import tempfile
import subprocess
import zipfile
import xml.etree.ElementTree as ET
import os
import logging
from pathlib import Path
from io import BytesIO
from typing import Union

from ..core.exceptions import FileProcessingError
from ..core.config import config

logger = logging.getLogger(__name__)

class FileProcessingService:
    """Service for processing uploaded resume files"""
    
    @staticmethod
    def extract_text_from_file(file_content: bytes, filename: str, content_type: str) -> str:
        """
        Extract text from uploaded file based on type
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            content_type: MIME content type
            
        Returns:
            Extracted text content
            
        Raises:
            FileProcessingError: If file processing fails
        """
        logger.info(f"Processing file: {filename} ({len(file_content)} bytes, {content_type})")
        
        # Determine file type
        file_ext = Path(filename).suffix.lower() if filename else ""
        
        # Handle generic content type by using extension
        if content_type == "application/octet-stream":
            if file_ext == ".pdf":
                content_type = "application/pdf"
            elif file_ext == ".docx":
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_ext == ".txt":
                content_type = "text/plain"
        
        try:
            if content_type == "application/pdf" or file_ext == ".pdf":
                return FileProcessingService._extract_pdf_text(file_content)
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_ext == ".docx":
                return FileProcessingService._extract_docx_text(file_content)
            elif content_type == "text/plain" or file_ext == ".txt":
                return FileProcessingService._extract_txt_text(file_content)
            else:
                raise FileProcessingError(f"Unsupported file type: {content_type}")
                
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {e}")
            if isinstance(e, FileProcessingError):
                raise
            else:
                raise FileProcessingError(f"Failed to process {filename}: {str(e)}")
    
    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        """Extract text from PDF using system tools or basic parsing"""
        logger.info("Attempting PDF text extraction")
        
        # Method 1: Try system pdftotext command (if available)
        try:
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                
                # Try pdftotext system command
                result = subprocess.run(
                    ['pdftotext', tmp_file.name, '-'], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                # Clean up temp file
                Path(tmp_file.name).unlink(missing_ok=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    logger.info("PDF extracted using pdftotext")
                    return result.stdout.strip()
                    
        except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
            logger.warning("pdftotext not available or failed, trying fallback method")
            pass
        
        # Method 2: Try PyMuPDF if available (should be in requirements)
        try:
            import fitz  # PyMuPDF
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_file.flush()
                
                doc = fitz.open(tmp_file.name)
                text_parts = []
                
                for page_num in range(doc.page_count):
                    page = doc[page_num]
                    text_parts.append(page.get_text())
                
                doc.close()
                Path(tmp_file.name).unlink(missing_ok=True)
                
                extracted_text = '\n'.join(text_parts).strip()
                if extracted_text:
                    logger.info(f"PDF extracted using PyMuPDF: {len(extracted_text)} characters")
                    return extracted_text
                    
        except ImportError:
            logger.warning("PyMuPDF not available")
            pass
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
            pass
        
        # Method 3: Basic text extraction fallback
        logger.warning("Using basic PDF text extraction fallback")
        try:
            text = content.decode('latin-1', errors='ignore')
            # Very basic extraction - look for text between stream markers
            import re
            text_objects = re.findall(r'BT\s*(.*?)\s*ET', text, re.DOTALL)
            if text_objects:
                # Extract readable text from text objects
                extracted = []
                for obj in text_objects:
                    # Look for text in parentheses or brackets
                    text_matches = re.findall(r'[(\[]([^)\]]*)[)\]]', obj)
                    extracted.extend(text_matches)
                
                result = ' '.join(extracted).strip()
                if result and len(result) > 50:  # Only return if we got substantial text
                    logger.info(f"PDF extracted using fallback method: {len(result)} characters")
                    return result
        except Exception as e:
            logger.error(f"Fallback PDF extraction failed: {e}")
        
        raise FileProcessingError("Could not extract text from PDF. The file may be image-based or corrupted.")
    
    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        """Extract text from DOCX using zipfile and XML parsing"""
        logger.info("Extracting DOCX text")
        
        try:
            with zipfile.ZipFile(BytesIO(content)) as docx_zip:
                # Read the main document XML
                with docx_zip.open('word/document.xml') as doc_xml:
                    tree = ET.parse(doc_xml)
                
                # Find all text elements
                # Namespace for Word documents
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                
                # Extract all text elements
                text_elements = tree.findall('.//w:t', ns)
                text_parts = [elem.text or '' for elem in text_elements]
                
                # Also check for text in paragraphs without namespace (fallback)
                if not text_parts:
                    text_elements = tree.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                    text_parts = [elem.text or '' for elem in text_elements]
                
                # Final fallback - get all text content
                if not text_parts:
                    root_text = tree.getroot()
                    text_parts = [elem.text or '' for elem in root_text.iter() if elem.text and elem.text.strip()]
                
                extracted_text = '\n'.join(text_parts).strip()
                
                if extracted_text:
                    logger.info(f"DOCX extracted: {len(extracted_text)} characters")
                    return extracted_text
                else:
                    raise FileProcessingError("No text content found in DOCX file")
                    
        except zipfile.BadZipFile:
            raise FileProcessingError("Invalid DOCX file format")
        except ET.ParseError:
            raise FileProcessingError("Could not parse DOCX document structure")
        except Exception as e:
            raise FileProcessingError(f"DOCX processing failed: {str(e)}")
    
    @staticmethod
    def _extract_txt_text(content: bytes) -> str:
        """Extract text from plain text file"""
        logger.info("Processing text file")
        
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                text = content.decode(encoding).strip()
                if text:
                    logger.info(f"Text file decoded with {encoding}: {len(text)} characters")
                    return text
            except UnicodeDecodeError:
                continue
        
        raise FileProcessingError("Could not decode text file with any supported encoding")
    
    @staticmethod
    def validate_file(filename: str, file_size: int, content_type: str) -> None:
        """
        Validate uploaded file meets requirements
        
        Raises:
            FileProcessingError: If validation fails
        """
        # Check file size
        if file_size > config.max_file_size:
            raise FileProcessingError(
                f"File too large. Maximum size is {config.max_file_size // (1024*1024)}MB"
            )
        
        # Check filename
        if not filename or not filename.strip():
            raise FileProcessingError("Filename is required")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in config.allowed_file_types:
            allowed_types = ", ".join(config.allowed_file_types)
            raise FileProcessingError(
                f"Unsupported file type '{file_ext}'. Allowed types: {allowed_types}"
            )
        
        # Check content type (allow generic uploads)
        allowed_content_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "application/octet-stream"  # Generic binary upload
        }
        
        if content_type not in allowed_content_types:
            logger.warning(f"Unusual content type: {content_type}")
            # Don't raise error for content type - rely on file extension
        
        logger.info(f"File validation passed: {filename} ({file_size} bytes, {content_type})")

# Singleton instance for easy import
file_service = FileProcessingService()