#!/bin/bash

# AWS Lambda Deployment Script for Resume Health Checker
set -e

# Configuration
STACK_NAME="resume-health-checker"
ENVIRONMENT=${1:-prod}
REGION=${AWS_REGION:-us-east-1}
S3_BUCKET=${S3_DEPLOYMENT_BUCKET:-"resume-health-checker-deployments"}

echo "🚀 Starting deployment to AWS Lambda..."
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack: $STACK_NAME-$ENVIRONMENT"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI not found. Please install it first:"
    echo "pip install aws-sam-cli"
    exit 1
fi

# Check required environment variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable is required"
    exit 1
fi

if [ -z "$STRIPE_PAYMENT_URL" ]; then
    echo "❌ STRIPE_PAYMENT_URL environment variable is required"
    exit 1
fi

if [ -z "$STRIPE_PAYMENT_SUCCESS_TOKEN" ]; then
    echo "❌ STRIPE_PAYMENT_SUCCESS_TOKEN environment variable is required"
    exit 1
fi

# Create S3 bucket if it doesn't exist
if ! aws s3 ls "s3://$S3_BUCKET" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "📦 Creating S3 deployment bucket: $S3_BUCKET"
    aws s3 mb "s3://$S3_BUCKET" --region "$REGION" || true
fi

echo "🔨 Building SAM application..."
sam build

echo "📤 Deploying to AWS..."
sam deploy \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --s3-bucket "$S3_BUCKET" \
    --s3-prefix "deployments/$ENVIRONMENT" \
    --region "$REGION" \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
        Environment="$ENVIRONMENT" \
        OpenAIApiKey="$OPENAI_API_KEY" \
        StripePaymentUrl="$STRIPE_PAYMENT_URL" \
        StripeSuccessToken="$STRIPE_PAYMENT_SUCCESS_TOKEN" \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

# Get the API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME-$ENVIRONMENT" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Deployment Details:"
echo "  Stack Name: $STACK_NAME-$ENVIRONMENT"
echo "  Region: $REGION"
echo "  Environment: $ENVIRONMENT"
echo ""
echo "🌐 Your application is available at:"
echo "  $API_URL"
echo ""
echo "🔧 Management URLs:"
echo "  CloudFormation: https://$REGION.console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks/stackinfo?stackId=$STACK_NAME-$ENVIRONMENT"
echo "  Lambda Function: https://$REGION.console.aws.amazon.com/lambda/home?region=$REGION#/functions/resume-health-checker-$ENVIRONMENT"
echo "  API Gateway: https://$REGION.console.aws.amazon.com/apigateway/main/apis?region=$REGION"
echo ""
echo "💡 To test your deployment:"
echo "  curl $API_URL/health"
echo ""