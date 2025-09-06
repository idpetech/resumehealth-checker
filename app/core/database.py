"""
SQLite database management with minimal dependencies.

Pure SQL implementation - no ORM for maximum simplicity and control.
"""
import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

from .config import config

logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE CONNECTION MANAGEMENT
# =============================================================================

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(config.database_path, timeout=30.0)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize database schema"""
    # Ensure database directory exists
    config.database_path.parent.mkdir(exist_ok=True)
    
    with get_db_connection() as conn:
        # Create analyses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_size INTEGER,
                analysis_type TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                free_result JSON,
                premium_result JSON,
                job_posting TEXT,
                payment_status TEXT DEFAULT 'pending',
                payment_amount INTEGER,
                payment_currency TEXT DEFAULT 'usd',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add job_posting column if it doesn't exist (for existing databases)
        try:
            conn.execute("ALTER TABLE analyses ADD COLUMN job_posting TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Create payments table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                stripe_session_id TEXT UNIQUE,
                stripe_payment_intent_id TEXT,
                amount INTEGER NOT NULL,
                currency TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES analyses (id)
            )
        """)
        
        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_analyses_payment_status ON analyses(payment_status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_stripe_session_id ON payments(stripe_session_id)")
        
        conn.commit()
        logger.info("✅ Database schema initialized")

# =============================================================================
# ANALYSIS DATABASE OPERATIONS
# =============================================================================

class AnalysisDB:
    """Database operations for resume analyses"""
    
    @staticmethod
    def create(filename: str, file_size: int, resume_text: str, analysis_type: str = "free") -> str:
        """Create new analysis record"""
        analysis_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO analyses (
                    id, filename, file_size, analysis_type, resume_text, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (analysis_id, filename, file_size, analysis_type, resume_text))
            conn.commit()
        
        logger.info(f"Created analysis {analysis_id} for file {filename}")
        return analysis_id
    
    @staticmethod
    def get(analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID"""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM analyses WHERE id = ?", 
                (analysis_id,)
            ).fetchone()
            
            if row:
                result = dict(row)
                # Parse JSON fields
                if result.get('free_result'):
                    result['free_result'] = json.loads(result['free_result'])
                if result.get('premium_result'):
                    result['premium_result'] = json.loads(result['premium_result'])
                return result
        
        return None
    
    @staticmethod
    def update_free_result(analysis_id: str, result: Dict[str, Any]):
        """Update free analysis result"""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE analyses 
                SET free_result = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(result), analysis_id))
            conn.commit()
        
        logger.info(f"Updated free result for analysis {analysis_id}")
    
    @staticmethod
    def update_premium_result(analysis_id: str, result: Dict[str, Any]):
        """Update premium analysis result"""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE analyses 
                SET premium_result = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (json.dumps(result), analysis_id))
            conn.commit()
        
        logger.info(f"Updated premium result for analysis {analysis_id}")
    
    @staticmethod
    def update_job_posting(analysis_id: str, job_posting: str):
        """Update job posting for analysis"""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE analyses 
                SET job_posting = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (job_posting, analysis_id))
            conn.commit()
        
        logger.info(f"Updated job posting for analysis {analysis_id}")
    
    @staticmethod
    def mark_as_paid(analysis_id: str, amount: int, currency: str = "usd"):
        """Mark analysis as paid"""
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE analyses 
                SET payment_status = 'paid', payment_amount = ?, payment_currency = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (amount, currency, analysis_id))
            conn.commit()
        
        logger.info(f"Marked analysis {analysis_id} as paid: {amount} {currency}")
    
    @staticmethod
    def get_recent(limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analyses (for debugging/monitoring)"""
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, filename, analysis_type, payment_status, created_at
                FROM analyses 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]

# =============================================================================
# PAYMENT DATABASE OPERATIONS
# =============================================================================

class PaymentDB:
    """Database operations for payments"""
    
    @staticmethod
    def create_session(analysis_id: str, stripe_session_id: str, amount: int, currency: str, metadata: Dict[str, Any] = None) -> str:
        """Record new payment session"""
        payment_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO payments (
                    id, analysis_id, stripe_session_id, amount, currency, status, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
            """, (payment_id, analysis_id, stripe_session_id, amount, currency, json.dumps(metadata or {})))
            conn.commit()
        
        logger.info(f"Created payment session {payment_id} for analysis {analysis_id}")
        return payment_id
    
    @staticmethod
    def update_session_status(stripe_session_id: str, status: str, payment_intent_id: str = None):
        """Update payment session status"""
        with get_db_connection() as conn:
            if payment_intent_id:
                conn.execute("""
                    UPDATE payments 
                    SET status = ?, stripe_payment_intent_id = ?
                    WHERE stripe_session_id = ?
                """, (status, payment_intent_id, stripe_session_id))
            else:
                conn.execute("""
                    UPDATE payments 
                    SET status = ?
                    WHERE stripe_session_id = ?
                """, (status, stripe_session_id))
            conn.commit()
        
        logger.info(f"Updated payment session {stripe_session_id} status to {status}")
    
    @staticmethod
    def get_by_session_id(stripe_session_id: str) -> Optional[Dict[str, Any]]:
        """Get payment by Stripe session ID"""
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM payments WHERE stripe_session_id = ?",
                (stripe_session_id,)
            ).fetchone()
            
            if row:
                result = dict(row)
                if result.get('metadata'):
                    result['metadata'] = json.loads(result['metadata'])
                return result
        
        return None

# =============================================================================
# DATABASE UTILITIES
# =============================================================================

def get_database_stats() -> Dict[str, Any]:
    """Get database statistics for monitoring"""
    with get_db_connection() as conn:
        analyses_count = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        payments_count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        paid_analyses = conn.execute("SELECT COUNT(*) FROM analyses WHERE payment_status = 'paid'").fetchone()[0]
        
        return {
            "total_analyses": analyses_count,
            "total_payments": payments_count,
            "paid_analyses": paid_analyses,
            "conversion_rate": f"{(paid_analyses / max(analyses_count, 1) * 100):.1f}%" if analyses_count > 0 else "0%"
        }

