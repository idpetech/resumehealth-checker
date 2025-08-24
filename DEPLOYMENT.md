# Resume Health Checker - Deployment & Testing Guide

## 🧪 Testing Suite Overview

### Test Coverage
- **Unit Tests**: Core functionality, file processing, AI integration
- **Integration Tests**: End-to-end API workflows, error handling
- **Performance Tests**: Load testing, memory usage, response times
- **Security Tests**: Input validation, file safety, vulnerability scanning

### Running Tests

```bash
# Install dependencies
make install

# Run all tests
make test

# Run tests with coverage
make test-cov

# Run tests in watch mode (development)
make test-watch

# Run security scans
make security

# Run all quality checks
make check
```

### Test Categories

#### 1. Unit Tests (`test_main.py`)
- ✅ File processing (PDF/DOCX extraction)
- ✅ AI prompt generation
- ✅ Payment token validation
- ✅ Error handling for invalid inputs
- ✅ Health check endpoint

#### 2. Integration Tests (`test_integration.py`)
- ✅ Complete free analysis workflow
- ✅ Complete paid analysis workflow  
- ✅ File upload and processing pipeline
- ✅ OpenAI API integration
- ✅ Error scenarios and edge cases

#### 3. Performance Tests (`test_performance.py`)
- ✅ Response time under concurrent load
- ✅ Memory usage stability
- ✅ Large file handling
- ✅ Resource usage monitoring

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

The pipeline includes 5 main stages:

#### 1. **Test Stage** (`test`)
- Python 3.9 setup
- Dependency installation
- Code linting (flake8, black)
- Test execution with 80% coverage requirement
- Coverage reporting to Codecov

#### 2. **Security Scan** (`security-scan`)
- Safety check for vulnerable dependencies
- Bandit security linting
- Runs in parallel with tests

#### 3. **Deploy Staging** (`deploy-staging`)
- Triggered on `develop` branch pushes
- Deploys to Vercel staging environment
- Uses staging environment variables
- Available at: `resume-checker-staging.vercel.app`

#### 4. **Deploy Production** (`deploy-production`)
- Triggered on `main` branch pushes
- Deploys to production with full environment
- Only runs after tests and security scans pass

#### 5. **Smoke Tests** (`smoke-tests`)
- Validates production deployment
- Tests health endpoint and frontend loading
- Fails deployment if critical endpoints don't work

### Required GitHub Secrets

Set these in your repository's GitHub Actions secrets:

```bash
# Vercel Configuration
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_vercel_org_id  
VERCEL_PROJECT_ID=your_vercel_project_id

# Environment Variables - Staging
OPENAI_API_KEY_STAGING=your_staging_openai_key
STRIPE_TOKEN_STAGING=staging_payment_token

# Environment Variables - Production  
OPENAI_API_KEY_PROD=your_prod_openai_key
STRIPE_TOKEN_PROD=prod_payment_token
```

## 📋 Pre-Deployment Checklist

### Code Quality Gates

Before any deployment, ensure:

- [ ] All tests pass: `make test`
- [ ] Code coverage ≥ 80%
- [ ] Security scans pass: `make security`
- [ ] Code formatted: `make format`
- [ ] Linting passes: `make lint`
- [ ] Pre-commit hooks installed: `make install`

### Environment Setup

1. **Staging Environment**
   ```bash
   cp .env.example .env.staging
   # Configure staging values
   ```

2. **Production Environment**
   ```bash
   cp .env.example .env.production
   # Configure production values
   ```

### API Keys & Services

- [ ] OpenAI API key configured (separate keys for staging/prod)
- [ ] Stripe Payment Links created and tested
- [ ] Vercel project configured
- [ ] Domain name configured (if custom domain)

## 🔄 Deployment Workflow

### Staging Deployment (Automatic)

1. Create feature branch: `git checkout -b feature/new-feature`
2. Develop and test locally: `make dev`
3. Run quality checks: `make check`
4. Push to develop: `git push origin develop`
5. GitHub Actions automatically deploys to staging
6. Test on staging environment

### Production Deployment (Automatic)

1. Merge develop to main: `git checkout main && git merge develop`
2. Push to main: `git push origin main`
3. GitHub Actions runs full pipeline:
   - Tests and security scans
   - Production deployment
   - Smoke tests
   - Notification on success/failure

### Manual Deployment (Emergency)

```bash
# Deploy staging manually
make deploy-staging

# Deploy production manually  
make deploy-prod
```

## 🧪 Testing Strategies

### Regression Testing

Before each release:

1. **API Regression Tests**
   ```bash
   # Test all endpoints with various inputs
   pytest tests/test_integration.py -v
   ```

2. **Performance Regression Tests**
   ```bash
   # Ensure performance hasn't degraded
   pytest tests/test_performance.py -v
   ```

3. **Security Regression Tests**
   ```bash
   # Check for new vulnerabilities
   make security
   ```

### Load Testing (Production)

For production load testing:

```bash
# Install load testing tools
pip install locust

# Run load test (create locustfile.py)
locust -f locustfile.py --host=https://your-domain.com
```

Sample `locustfile.py`:
```python
from locust import HttpUser, task, between
import io

class ResumeCheckerUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def check_resume(self):
        # Sample PDF content for testing
        files = {'file': ('test.pdf', b'fake pdf content', 'application/pdf')}
        self.client.post('/api/check-resume', files=files)
    
    @task(2)  
    def load_homepage(self):
        self.client.get('/')
```

## 📊 Monitoring & Observability

### Key Metrics to Monitor

1. **Application Metrics**
   - Response time (95th percentile < 3s)
   - Error rate (< 1%)
   - Throughput (requests/minute)

2. **Business Metrics**
   - Free analysis requests
   - Paid conversion rate
   - Revenue per day

3. **Infrastructure Metrics**
   - Memory usage
   - CPU utilization
   - OpenAI API costs

### Logging Strategy

```python
# Add to main.py for production logging
import logging
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "request_processed",
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        process_time=process_time
    )
    return response
```

## 🚨 Incident Response

### Rollback Procedure

If deployment fails or issues arise:

1. **Immediate Rollback**
   ```bash
   # Revert to previous deployment
   vercel rollback your-project-name
   ```

2. **Fix and Redeploy**
   ```bash
   # Create hotfix branch
   git checkout -b hotfix/critical-fix
   # Make fix
   git commit -m "fix: critical issue"
   git push origin hotfix/critical-fix
   # Merge to main for immediate deployment
   ```

### Health Checks

Monitor these endpoints:

- `GET /health` - Application health
- `GET /` - Frontend availability
- `POST /api/check-resume` - Core functionality

### Alerting

Set up alerts for:
- Response time > 5 seconds
- Error rate > 5%
- Health check failures
- OpenAI API failures

## 🎯 Success Criteria

### Deployment Success

- ✅ All tests pass (100% success rate)
- ✅ Security scans clear
- ✅ Staging deployment successful
- ✅ Production deployment successful
- ✅ Smoke tests pass
- ✅ Response times within SLA (< 3s)

### Quality Gates

- ✅ Code coverage ≥ 80%
- ✅ Zero critical security vulnerabilities
- ✅ Performance tests pass
- ✅ Manual testing completed

This comprehensive testing and deployment strategy ensures reliability, security, and performance for your Resume Health Checker micro-SaaS application.