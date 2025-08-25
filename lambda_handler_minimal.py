import json
from mangum import Mangum
from main_minimal import app

# Create the Lambda handler
lambda_handler = Mangum(app, lifespan="off")

# Test handler for debugging
def debug_handler(event, context):
    """Debug version of Lambda handler with detailed logging"""
    print(f"Event: {json.dumps(event)}")
    print(f"Context: {context}")
    
    try:
        response = lambda_handler(event, context)
        print(f"Response: {response}")
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Content-Type": "application/json"
            },
            "body": json.dumps({"detail": f"Internal server error: {str(e)}"})
        }