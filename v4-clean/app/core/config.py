"""
Configuration management for multi-environment support.

Handles environment-specific settings for:
- Local development
- Railway staging  
- Railway production
"""
import os
from pathlib import Path
from typing import Literal

# Load environment variables from .env file in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in production, that's fine
    pass

Environment = Literal["local", "staging", "production"]

class Config:
    """Application configuration with environment-specific settings"""
    
    def __init__(self):
        # Core settings
        self.environment: Environment = os.getenv("ENVIRONMENT", "local")
        self.debug = self.environment != "production"
        
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if not self.openai_api_key:
            # In Railway, we might not have the key set yet - use placeholder for health checks
            self.openai_api_key = "sk-placeholder-for-health-check"
            print("⚠️ OPENAI_API_KEY not set - using placeholder for health checks")
        
        # Stripe configuration - use test keys for local/staging, live keys for production
        self.use_stripe_test_keys = self.environment in ["local", "staging"]
        
        if self.use_stripe_test_keys:
            self.stripe_secret_key = os.getenv("STRIPE_SECRET_TEST_KEY", "")
            self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_TEST_KEY", "")
            self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_TEST_SECRET", "")
        else:
            self.stripe_secret_key = os.getenv("STRIPE_SECRET_LIVE_KEY", "")
            self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_LIVE_KEY", "")
            self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_LIVE_SECRET", "")
        
        if not self.stripe_secret_key:
            # Use placeholder for health checks if Stripe keys not set
            self.stripe_secret_key = "sk_test_placeholder_for_health_check"
            self.stripe_publishable_key = "pk_test_placeholder_for_health_check"
            self.stripe_webhook_secret = "whsec_placeholder_for_health_check"
            print("⚠️ Stripe keys not set - using placeholders for health checks")
        
        # Base URL configuration
        self.base_url = self._get_base_url()
        
        # Database configuration
        self.database_path = self._get_database_path()
        
        # Application constants
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_file_types = {".pdf", ".docx", ".txt"}
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "3000"))
        
        # Context-specific token limits
        self.token_limits = {
            "resume_analysis": int(os.getenv("TOKENS_RESUME_ANALYSIS", "2000")),
            "job_fit": int(os.getenv("TOKENS_JOB_FIT", "2500")), 
            "cover_letter": int(os.getenv("TOKENS_COVER_LETTER", "2000")),
            "mock_interview": int(os.getenv("TOKENS_MOCK_INTERVIEW", "4000")),  # Higher for 10 questions
            "resume_rewrite": int(os.getenv("TOKENS_RESUME_REWRITE", "3500"))
        }
    
    def get_token_limit(self, analysis_type: str, context: str = "default") -> int:
        """Get appropriate token limit for specific analysis type"""
        if context == "mock_interview":
            return self.token_limits["mock_interview"]
        elif analysis_type in self.token_limits:
            return self.token_limits[analysis_type]
        else:
            return self.openai_max_tokens
        
    def _get_base_url(self) -> str:
        """Get the appropriate base URL for the current environment"""
        if self.environment == "local":
            port = os.getenv("PORT", "8000")
            return f"http://localhost:{port}"
        elif self.environment == "staging":
            # Try Railway's actual environment variables, then custom ones, then fallback
            railway_url = os.getenv("RAILWAY_STAGING_URL") or os.getenv("RAILWAY_STATIC_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN")
            if railway_url:
                return f"https://{railway_url}" if not railway_url.startswith("http") else railway_url
            return "http://localhost:8000"
        else:  # production
            # Try Railway's actual environment variables, then custom ones, then fallback
            railway_url = os.getenv("RAILWAY_STATIC_URL") or os.getenv("RAILWAY_PUBLIC_DOMAIN")
            if railway_url:
                return f"https://{railway_url}" if not railway_url.startswith("http") else railway_url
            return os.getenv("RAILWAY_PRODUCTION_URL", "http://localhost:8000")
    
    def _get_database_path(self) -> Path:
        """Get the appropriate database path for the current environment"""
        # Check for explicit DATABASE_PATH override first
        if os.getenv("DATABASE_PATH"):
            return Path(os.getenv("DATABASE_PATH"))
        
        # Railway provides persistent volume at /app/data if configured
        if os.getenv("RAILWAY_VOLUME_MOUNT_PATH"):
            railway_db_path = Path(os.getenv("RAILWAY_VOLUME_MOUNT_PATH")) / "database.db"
            # Ensure the directory exists
            railway_db_path.parent.mkdir(parents=True, exist_ok=True)
            return railway_db_path
        
        # Default behavior for local development
        return Path("database.db")
    
    def get_stripe_success_url(self, analysis_id: str, product_type: str) -> str:
        """Generate Stripe success URL with parameters"""
        return f"{self.base_url}/api/v1/payment/success?session_id={{CHECKOUT_SESSION_ID}}&analysis_id={analysis_id}&product_type={product_type}"
    
    def get_stripe_cancel_url(self, analysis_id: str, product_type: str) -> str:
        """Generate Stripe cancel URL with parameters"""
        return f"{self.base_url}/api/v1/payment/cancel?analysis_id={analysis_id}&product_type={product_type}"

# Global configuration instance
config = Config()


