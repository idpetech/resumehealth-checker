"""
Promotional Code Service - Minimal & Rugged Implementation

KISS Principle: Simple validation and discount calculation
DRY Principle: Reuses existing database patterns and error handling
Rugged Design: Graceful degradation, clear error messages, no hardcoding
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..core.database import get_db_connection
from ..core.exceptions import AIAnalysisError

logger = logging.getLogger(__name__)

class PromotionalService:
    """Minimal promotional code service - KISS principle"""
    
    def __init__(self):
        self._init_tables()
    
    def _init_tables(self):
        """Check if promotional tables exist - they should already be created"""
        try:
            with get_db_connection() as conn:
                # Just verify the tables exist - they should already be created with the correct schema
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promotional_codes'")
                if not cursor.fetchone():
                    logger.warning("promotional_codes table not found - may need manual creation")
                
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promo_usage'")
                if not cursor.fetchone():
                    logger.warning("promo_usage table not found - may need manual creation")
                    
        except Exception as e:
            logger.error(f"Failed to check promotional tables: {e}")
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """Validate promotional code - simple and clear"""
        if not code or len(code.strip()) < 3:
            raise AIAnalysisError("Invalid promotional code format")
        
        try:
            with get_db_connection() as conn:
                row = conn.execute("""
                    SELECT * FROM promotional_codes 
                    WHERE code = ? AND status = 'active'
                """, (code.upper().strip(),)).fetchone()
                
                if not row:
                    raise AIAnalysisError("Promotional code not found or inactive")
                
                # Check usage limits
                if row['usage_limit'] and row['usage_count'] >= row['usage_limit']:
                    raise AIAnalysisError("Promotional code usage limit reached")
                
                return {
                    "valid": True,
                    "code": row['code'],
                    "discount_type": row['discount_type'],
                    "discount_value": row['discount_value']
                }
                
        except AIAnalysisError:
            raise
        except Exception as e:
            logger.error(f"Code validation error: {e}")
            raise AIAnalysisError("Failed to validate promotional code")
    
    def calculate_discount(self, code: str, amount: float) -> Dict[str, Any]:
        """Calculate discount - simple math, clear logic"""
        validation = self.validate_code(code)
        
        if validation['discount_type'] == 'percentage':
            discount = (amount * validation['discount_value']) / 100
        else:  # fixed amount - this is the MAXIMUM discount, not a fixed deduction
            discount = min(validation['discount_value'], amount)  # Cap at the feature price
        
        final_amount = max(0, amount - discount)
        
        return {
            "original_amount": amount,
            "discount_amount": discount,
            "final_amount": final_amount,
            "is_free": final_amount == 0,
            "discount_percentage": (discount / amount * 100) if amount > 0 else 0
        }
    
    def track_usage(self, code: str, analysis_id: str, discount_amount: float) -> bool:
        """Track usage - simple insert, graceful failure"""
        try:
            with get_db_connection() as conn:
                # Insert usage record
                conn.execute("""
                    INSERT OR IGNORE INTO promo_usage (code, analysis_id, discount_amount)
                    VALUES (?, ?, ?)
                """, (code.upper().strip(), analysis_id, discount_amount))
                
                # Update usage count
                conn.execute("""
                    UPDATE promotional_codes 
                    SET usage_count = usage_count + 1
                    WHERE code = ?
                """, (code.upper().strip(),))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to track promo usage: {e}")
            return False  # Graceful degradation - don't fail the main flow
    
    def create_code(self, code: str, discount_type: str, discount_value: float, max_uses: Optional[int] = None) -> bool:
        """Create promotional code - admin function"""
        try:
            with get_db_connection() as conn:
                # Use existing table structure with proper column names
                conn.execute("""
                    INSERT INTO promotional_codes (id, code, discount_type, discount_value, usage_limit, rules, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (f"promo-{code.lower()}", code.upper().strip(), discount_type, discount_value, max_uses, '{}', 'active'))
                
                conn.commit()
                logger.info(f"Created promotional code: {code}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create promotional code {code}: {e}")
            return False

# Global instance - simple singleton pattern
promotional_service = PromotionalService()
