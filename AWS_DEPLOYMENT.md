# AWS Lambda Deployment Guide

This guide covers deploying the Resume Health Checker to AWS Lambda with API Gateway.

## Architecture

```
User → API Gateway → Lambda Function (FastAPI) → OpenAI API
                                   ↓
                               CloudWatch Logs
```

## Prerequisites

### 1. AWS CLI Setup
```bash
# Install AWS CLI
brew install awscli  # macOS
# or pip install awscli

# Configure AWS credentials
aws configure
# Enter your AWS Access Key ID, Secret Key, Region (e.g., us-east-1)
```

### 2. SAM CLI Installation
```bash
# Install SAM CLI
pip install aws-sam-cli

# Verify installation
sam --version
```

### 3. Environment Variables
Create a `.env.production` file or export these variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export STRIPE_PAYMENT_URL="your-stripe-payment-url"  
export STRIPE_PAYMENT_SUCCESS_TOKEN="your-stripe-success-token"
export AWS_REGION="us-east-1"  # or your preferred region
export S3_DEPLOYMENT_BUCKET="your-deployment-bucket-name"
```

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

```bash
# Load environment variables
source .env.production  # or set them manually

# Deploy to production
./deploy.sh prod

# Deploy to staging
./deploy.sh staging
```

### Method 2: Manual SAM Deployment

```bash
# Build the application
sam build

# Deploy (guided first time)
sam deploy --guided

# Subsequent deployments
sam deploy
```

### Method 3: Step-by-Step Deployment

1. **Build the Lambda package:**
```bash
sam build -t template.yaml
```

2. **Deploy with parameters:**
```bash
sam deploy \
  --stack-name resume-health-checker-prod \
  --s3-bucket your-deployment-bucket \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=prod \
    OpenAIApiKey=$OPENAI_API_KEY \
    StripePaymentUrl=$STRIPE_PAYMENT_URL \
    StripeSuccessToken=$STRIPE_PAYMENT_SUCCESS_TOKEN
```

## Configuration Details

### Lambda Function Settings
- **Runtime**: Python 3.11
- **Memory**: 1024 MB (for PDF processing)
- **Timeout**: 30 seconds
- **Handler**: `lambda_handler.lambda_handler`

### API Gateway Settings
- **CORS**: Enabled for all origins
- **Binary Media Types**: Supports PDF and DOCX uploads
- **Timeout**: 30 seconds

### Environment Variables (Automatically Set)
- `OPENAI_API_KEY`: Your OpenAI API key
- `STRIPE_PAYMENT_URL`: Stripe payment link
- `STRIPE_PAYMENT_SUCCESS_TOKEN`: Token for premium features
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

## Post-Deployment Steps

### 1. Test the Deployment
```bash
# Get your API URL from deployment output, then:
curl https://your-api-url/health

# Test file upload
curl -X POST https://your-api-url/api/check-resume \
  -F "file=@sample-resume.pdf"
```

### 2. Configure Custom Domain (Optional)
```bash
# Create a custom domain in API Gateway
aws apigateway create-domain-name \
  --domain-name resume-checker.yourdomain.com \
  --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/abc123
```

### 3. Set up Monitoring
- CloudWatch Logs: Automatically configured
- CloudWatch Alarms: Set up for error rates and latency
- AWS X-Ray: Enable for detailed tracing (optional)

## File Structure for Lambda

```
.
├── lambda_handler.py          # AWS Lambda entry point
├── main.py                   # FastAPI application
├── requirements-lambda.txt   # Lambda-specific dependencies
├── template.yaml            # SAM template
├── deploy.sh               # Deployment script
└── AWS_DEPLOYMENT.md       # This file
```

## Important Notes

### File Size Limits
- **Lambda payload limit**: 6 MB (API Gateway)
- **Resume files**: Should be under 5 MB
- **Response size**: Limited to 10 MB

### Performance Considerations
- **Cold starts**: First request may take 5-10 seconds
- **Memory allocation**: 1024 MB for PDF processing
- **Concurrent executions**: Default limit is 1000

### Cost Optimization
- **Free tier**: 1M requests/month and 400,000 GB-seconds
- **Pricing**: ~$0.20 per 1M requests + compute time
- **Estimate**: For 10,000 resume analyses/month ≈ $5-10

## Troubleshooting

### Common Issues

1. **Import errors in Lambda:**
   ```bash
   # Use Lambda-specific requirements
   pip install -r requirements-lambda.txt -t .
   ```

2. **File upload issues:**
   ```yaml
   # Ensure binary media types are configured in template.yaml
   BinaryMediaTypes:
     - "multipart/form-data"
     - "application/pdf"
   ```

3. **OpenAI API timeouts:**
   ```python
   # Increase timeout in main.py if needed
   openai.timeout = 25  # seconds
   ```

4. **Memory errors with large PDFs:**
   ```yaml
   # Increase memory in template.yaml
   MemorySize: 1536  # MB
   ```

### Debugging

1. **Check CloudWatch Logs:**
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/resume-health-checker"
```

2. **Stream logs in real-time:**
```bash
sam logs -n ResumeHealthCheckerFunction --stack-name resume-health-checker-prod --tail
```

3. **Local testing:**
```bash
sam local start-api --env-vars env.json
```

## Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **IAM Roles**: Use least-privilege principle
3. **API Gateway**: Consider adding API keys or authentication
4. **CORS**: Restrict origins in production
5. **Input Validation**: Always validate file uploads

## Scaling Considerations

- **Concurrent executions**: Monitor and adjust limits
- **API Gateway throttling**: Configure per-client limits
- **OpenAI rate limits**: Implement exponential backoff
- **Monitoring**: Set up CloudWatch alarms for errors and latency

## Rollback Strategy

```bash
# Rollback to previous version
aws cloudformation cancel-update-stack --stack-name resume-health-checker-prod

# Or delete and redeploy
sam delete --stack-name resume-health-checker-prod
./deploy.sh prod
```