# Lambda Function Magic Number Error Fixes

## Problem Identified

The Lambda function was experiencing "magic number error" issues when trying to read uploaded files. This typically occurs when:

1. **File corruption during upload/transmission**
2. **Incorrect file type detection** 
3. **Magic byte validation failures**
4. **Temporary file creation issues** in Lambda's read-only filesystem

## Root Causes

### 1. Temporary File Creation
- **Original code** used `tempfile.NamedTemporaryFile()` to create temporary files
- **Problem**: Lambda has a read-only filesystem (`/tmp` is writable but limited)
- **Impact**: File operations could fail or cause permission issues

### 2. Missing Magic Byte Validation
- **Original code** relied solely on `content_type` headers
- **Problem**: Headers can be spoofed or incorrect
- **Impact**: Invalid files could pass initial validation but fail during processing

### 3. Poor Error Handling
- **Original code** had generic error messages
- **Problem**: Difficult to debug file processing issues
- **Impact**: Users got unclear error messages, developers couldn't identify root causes

## Solutions Implemented

### 1. Magic Byte Validation Functions

```python
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
```

**Benefits**:
- Validates actual file content, not just headers
- Prevents processing of corrupted or invalid files
- Provides clear error messages for magic byte failures

### 2. Stream-Based File Processing

```python
def extract_text_from_pdf(file_content: bytes) -> str:
    # Validate magic bytes first
    if not validate_pdf_magic_bytes(file_content):
        raise HTTPException(status_code=400, detail="Invalid PDF file: Magic bytes do not match PDF format")
    
    try:
        # Use stream-based approach instead of temporary files (Lambda-friendly)
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        # Handle specific error types
        if "password" in str(e).lower():
            raise HTTPException(status_code=400, detail="PDF file is password-protected. Please remove password protection and try again.")
        else:
            raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
```

**Benefits**:
- No temporary file creation (Lambda-friendly)
- Direct memory processing
- Better error handling for specific failure types

### 3. Enhanced File Validation

```python
def resume_to_text(file: UploadFile) -> str:
    try:
        # Read file content as bytes
        file_content = file.file.read()
        
        # Validate file size (reasonable limit for resumes)
        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Please upload a file smaller than 10MB.")
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
        
        # Log file information for debugging
        print(f"Processing file: {file.filename}, type: {file.content_type}, size: {len(file_content)} bytes")
        print(f"First 8 bytes: {file_content[:8].hex()}")
        
        # Determine file type and extract text
        if file.content_type == "application/pdf" or (file.filename and file.filename.lower().endswith('.pdf')):
            return extract_text_from_pdf(file_content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or (file.filename and file.filename.lower().endswith(('.docx', '.doc'))):
            return extract_text_from_docx(file_content)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format. Content-Type: {file.content_type}, Filename: {file.filename}. Please upload a PDF or DOCX file."
            )
    except Exception as e:
        print(f"Error in resume_to_text: {str(e)}")
        raise e
```

**Benefits**:
- File size validation (prevents memory issues)
- Empty file detection
- Enhanced logging for debugging
- Fallback filename-based validation

### 4. Improved Lambda Handler

```python
def lambda_handler(event, context):
    """
    AWS Lambda entry point with enhanced error handling and debugging
    """
    try:
        print(f"🔍 Lambda event received: {json.dumps(event)}")
        print(f"🔍 Lambda context: {context}")
        
        # Process the request through Mangum
        response = handler(event, context)
        
        print(f"✅ Lambda response: {json.dumps(response)}")
        return response
        
    except Exception as e:
        print(f"❌ Lambda error: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        
        # Return a proper error response
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "detail": f"Internal server error: {str(e)}",
                "error_type": type(e).__name__,
                "message": "The Lambda function encountered an error while processing your request. Please check the logs for more details."
            })
        }
```

**Benefits**:
- Comprehensive error logging
- Proper error response formatting
- CORS headers included
- Better debugging information

## Files Modified

1. **`main.py`** - Main FastAPI application with fixes
2. **`main_working.py`** - Working version with fixes (used by Lambda)
3. **`main_minimal.py`** - Minimal version with fixes
4. **`lambda_handler.py`** - Enhanced Lambda handler with error handling

## Testing

Created `test_lambda_fixes.py` to verify:
- ✅ Magic byte validation works correctly
- ✅ File processing handles errors gracefully
- ✅ Error messages are clear and actionable
- ✅ Lambda handler provides proper error responses

## Deployment Notes

1. **Lambda Configuration**: The `template.yaml` is already configured to use `lambda_handler_working.lambda_handler`
2. **Dependencies**: All required packages are in `requirements-lambda.txt`
3. **Memory/Timeout**: Lambda is configured with 1024MB memory and 30-second timeout

## Expected Results

After deploying these fixes:

1. **Magic number errors** will be caught early with clear error messages
2. **File processing** will be more reliable in Lambda environment
3. **Error messages** will be more helpful for debugging
4. **Performance** should improve due to elimination of temporary file operations
5. **Debugging** will be easier with enhanced logging

## Monitoring

Monitor CloudWatch logs for:
- File processing success/failure rates
- Magic byte validation failures
- File size violations
- Processing time improvements

## Future Improvements

1. **File Type Detection**: Consider using `python-magic` library for more robust file type detection
2. **Compression**: Add support for compressed files (ZIP, RAR)
3. **Virus Scanning**: Integrate with AWS GuardDuty or similar for file security
4. **Caching**: Implement file content caching for repeated uploads
