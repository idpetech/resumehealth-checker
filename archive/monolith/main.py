"""
Backward Compatibility Shim for main.py

This file provides backward compatibility for tests and deployment scripts
that expect to import from main.py. It simply re-exports the modular app.

This is the 2-minute critical fix mentioned in the architecture review.
"""

# Import the modular app and re-export it
from main_modular import app

# Re-export for backward compatibility
__all__ = ['app']

# Legacy imports that some tests might expect
try:
    from main_vercel import (
        # Export key functions for backward compatibility
        resume_to_text,
        get_ai_analysis_with_retry,
        STRIPE_SUCCESS_TOKEN,
        STRIPE_PAYMENT_URL,
    )
except ImportError:
    # If imports fail, provide minimal compatibility
    STRIPE_SUCCESS_TOKEN = "payment_success_123"
    STRIPE_PAYMENT_URL = "https://buy.stripe.com/test_payment"

print("✅ Backward compatibility shim loaded - tests can now import from main.py")