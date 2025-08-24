# Development Rules & Lessons Learned

This document captures important lessons and rules to follow when developing this project and similar ones.

## Environment & Setup Rules

### ❌ NEVER assume system-level package managers
**Issue**: Used `pip` directly in Makefile without checking if it exists or is accessible
**Rule**: Always detect Python executable and use virtual environments
**Solution**: 
```makefile
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
```

### ✅ ALWAYS create virtual environments
**Issue**: Initially wrote setup scripts that installed directly to system Python
**Rule**: Every Python project MUST use virtual environments from day 1
**Implementation**:
- Create `.venv` directory automatically
- Provide scripts for both Unix and Windows activation
- Make activation instructions prominent in README

### ✅ ALWAYS provide multiple setup methods
**Rule**: Provide at least 3 ways to set up the project:
1. Automated script (`setup.sh` / `setup.py`)  
2. Makefile (if applicable)
3. Manual step-by-step instructions

## Testing Rules

### ❌ NEVER write async tests without proper decorators
**Issue**: Wrote `async def test_*` functions that were automatically skipped
**Rule**: Always use `@pytest.mark.asyncio` or ensure async functions are properly configured
**Fix**: Make functions `async def` AND add proper decorators

### ❌ NEVER mock with `spec=` for complex objects
**Issue**: `Mock(spec=UploadFile)` failed because spec prevented access to nested attributes
**Rule**: Use regular `Mock()` for complex objects with nested attributes
**Better**:
```python
mock_file = Mock()
mock_file.content_type = "application/pdf"  
mock_file.file = Mock()
mock_file.file.read.return_value = b"content"
```

### ✅ ALWAYS mock environment variables at module level
**Issue**: Patching `os.environ` after module import didn't work
**Rule**: Mock the actual variable in the module, not the environment
**Fix**: `@patch('main.STRIPE_SUCCESS_TOKEN', 'test_value')`

### ✅ ALWAYS include optional dependencies for comprehensive testing
**Issue**: `psutil` not included, causing performance tests to fail
**Rule**: Include ALL dependencies needed by ANY test in requirements.txt

## Code Architecture Rules

### ✅ ALWAYS design for testability from the start
**Rule**: Write code that can be easily mocked and tested
- Separate I/O operations from business logic
- Make external dependencies injectable
- Use clear interfaces

### ✅ ALWAYS validate inputs properly
**Rule**: Every API endpoint MUST validate ALL inputs
- File types, content types, sizes
- Required vs optional parameters  
- Sanitize all user inputs

## CI/CD Rules

### ✅ ALWAYS test the full pipeline locally first
**Rule**: Before pushing CI/CD workflows, test all commands locally
- Run all test commands manually
- Verify environment variable handling
- Test deployment steps in isolation

### ✅ ALWAYS provide fallbacks for CI failures
**Rule**: CI steps should degrade gracefully
- Use `|| true` for optional steps
- Provide clear error messages
- Have manual alternatives documented

## Error Handling Rules

### ✅ ALWAYS provide meaningful error messages
**Rule**: Every exception should help users understand what went wrong
- Include specific error details
- Suggest next steps when possible
- Log enough context for debugging

### ✅ ALWAYS handle edge cases explicitly
**Rule**: Test and handle edge cases:
- Empty files, corrupted files
- Network timeouts
- Invalid API responses
- Missing environment variables

## Documentation Rules

### ✅ ALWAYS provide working examples
**Rule**: Every setup instruction must be copy-pasteable and work
- Test all commands in clean environments
- Include expected outputs
- Document common error scenarios

### ✅ ALWAYS document the "why" not just the "what" 
**Rule**: Explain architectural decisions and trade-offs
- Why serverless vs traditional hosting
- Why specific libraries were chosen
- Why certain patterns are used

## Security Rules

### ✅ ALWAYS use environment variables for secrets
**Rule**: NEVER hardcode API keys, tokens, or passwords
- Use `.env.example` templates
- Validate required environment variables on startup
- Provide clear setup instructions

### ✅ ALWAYS validate file uploads thoroughly
**Rule**: Treat all uploaded files as potentially malicious
- Validate file types and sizes
- Process files in isolated environments
- Clean up temporary files immediately

## Performance Rules

### ✅ ALWAYS consider resource usage in tests
**Rule**: Performance tests should be realistic but not fragile
- Use reasonable thresholds
- Test on representative data sizes
- Mock expensive operations appropriately

## Git & Version Control Rules

### ✅ ALWAYS include proper .gitignore from start
**Rule**: Set up .gitignore before first commit
- Include virtual environments
- Include IDE files
- Include temporary files and logs
- Include environment files

## Deployment Rules

### ✅ ALWAYS test deployment configurations locally
**Rule**: Deployment should work in development mode first
- Test environment variable loading
- Test file paths and permissions
- Test external service connectivity

---

## Summary: Critical Checkpoints

Before any major milestone, verify:

1. **Setup works from scratch** in a clean environment
2. **All tests pass** including edge cases  
3. **Environment variables** are properly handled
4. **Dependencies** are correctly specified
5. **Documentation** includes working examples
6. **Error messages** are helpful to users
7. **Security** best practices are followed

## Next Developer Notes

When working on this project:
- Always activate virtual environment first: `source .venv/bin/activate`
- Run `./setup.sh test` before committing
- Update this rules file when encountering new issues
- Test setup instructions on different platforms when possible