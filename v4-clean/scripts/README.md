# 🚀 CI/CD Pipeline Scripts

## Current Branch Structure

- **v4.0-deployment**: Active development and deployment branch
  - Staging: `https://web-staging-f53d.up.railway.app` 
  - Production: `https://web-production-f7f3.up.railway.app`
- **main**: Legacy branch (not currently used for deployment)

## Pipeline Flow

```
1. 🧪 Local Testing     → ./scripts/test-local.sh
2. 🚀 Deploy Staging    → ./scripts/deploy-staging.sh  
3. 🌐 Deploy Production → ./scripts/deploy-production.sh
4. 🔄 Full Pipeline     → ./scripts/full-pipeline.sh
```

## Individual Scripts

### 1. Local Testing
```bash
./scripts/test-local.sh
```
- Activates venv
- Starts local server
- Tests health, file upload, pricing endpoints
- Must pass before any deployment

### 2. Staging Deployment  
```bash
./scripts/deploy-staging.sh
```
- Commits changes
- Pushes to v4.0-deployment 
- Tests staging environment
- Creates `.staging-tests-passed` flag

### 3. Production Deployment
```bash
./scripts/deploy-production.sh  
```
- Requires staging tests to pass
- Double confirmation prompt
- Pushes to v4.0-deployment (triggers production)
- Tests production environment

### 4. Full Pipeline
```bash
./scripts/full-pipeline.sh
```
- Runs all steps with confirmations
- Local → Staging → Production

## Safety Features

- ✅ **Step Dependencies**: Each step requires previous to pass
- ✅ **Confirmation Prompts**: Production requires explicit confirmation  
- ✅ **Automated Testing**: Health checks at each stage
- ✅ **Rollback Ready**: Easy to revert if issues found

## Railway Configuration

Both environments deploy from **v4.0-deployment** branch:

### Staging Environment Variables
```bash
ENVIRONMENT=staging
DEBUG=true
STRIPE_SECRET_TEST_KEY=sk_test_...
```

### Production Environment Variables  
```bash
ENVIRONMENT=production
DEBUG=false
STRIPE_SECRET_LIVE_KEY=sk_live_...
```

## Usage Examples

Quick staging test:
```bash
./scripts/test-local.sh && ./scripts/deploy-staging.sh
```

Full production deployment:
```bash
./scripts/full-pipeline.sh
```

Emergency production fix:
```bash
# Fix issue locally
./scripts/test-local.sh
# Deploy directly to production (skip staging if critical)
./scripts/deploy-production.sh
```