"""
Application Configuration and Constants

This module centralizes all configuration settings and constants
for the Resume Health Checker application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Centralized application settings"""
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.stripe_test_key = os.getenv("STRIPE_SECRET_TEST_KEY", "")
        self.stripe_live_key = os.getenv("STRIPE_SECRET_LIVE_KEY", "")
        self.stripe_payment_url = os.getenv("STRIPE_PAYMENT_URL", "https://buy.stripe.com/8x2cN4cC823I3qFcPWfMA02")
        self.stripe_success_token = os.getenv("STRIPE_PAYMENT_SUCCESS_TOKEN", "payment_success_123")
        self.environment = os.getenv("RAILWAY_ENVIRONMENT", "development")
        
        # Validate required settings
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")

class Constants:
    """Application constants"""
    # OpenAI Configuration
    MODEL_NAME = "gpt-4o-mini"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1500
    
    # File Processing
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    }
    
    # Pricing
    US_BASE_PRICE = 10.00
    BUNDLE_DISCOUNT = 0.20  # 20% savings
    
    # Session Management
    SESSION_TIMEOUT = 3600  # 1 hour
    
    # Rate Limiting
    API_RATE_LIMIT = "10/minute"  # 10 requests per minute per IP
    ANALYSIS_RATE_LIMIT = "3/minute"  # 3 analysis requests per minute per IP

# Initialize global instances
settings = Settings()
constants = Constants()