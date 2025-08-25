"""
AWS Lambda handler for FastAPI Resume Health Checker
Reuses the existing FastAPI app from main.py with improved error handling
"""
import json
import traceback
from mangum import Mangum
from main import app

# Create the Lambda handler using existing FastAPI app
handler = Mangum(app, lifespan="off")

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