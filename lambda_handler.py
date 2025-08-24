"""
AWS Lambda handler for FastAPI Resume Health Checker
Reuses the existing FastAPI app from main.py
"""
from mangum import Mangum
from main import app

# Create the Lambda handler using existing FastAPI app
handler = Mangum(app, lifespan="off")

# AWS Lambda entry point
lambda_handler = handler