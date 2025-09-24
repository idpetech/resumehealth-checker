"""
Unified Premium Generation Service

This service provides a single source of truth for generating premium analysis results
across all access methods (payment, promotional codes, bundles, admin override).

Follows the "rugged code, design, and architecture mantra":
- Clean, simple, and efficient bug-free code
- Elegant design with single responsibility
- Secure and stable implementation
"""
import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone

from ..core.exceptions import AIAnalysisError, PaymentError
from ..services.analysis import analysis_service
from ..core.database import AnalysisDB

logger = logging.getLogger(__name__)


class AccessType(Enum):
    """Enumeration of access types for premium generation"""
    PAYMENT = "payment"
    PROMO_CODE = "promo_code"
    ADMIN_OVERRIDE = "admin_override"
    BUNDLE = "bundle"
    GIFT_CODE = "gift_code"


@dataclass
class AccessContext:
    """Context information for premium generation access"""
    access_type: AccessType
    payment_id: Optional[str] = None
    promo_code: Optional[str] = None
    admin_user: Optional[str] = None
    bundle_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate access context after initialization"""
        if self.metadata is None:
            self.metadata = {}
        
        # Validate required fields based on access type
        if self.access_type == AccessType.PAYMENT and not self.payment_id:
            raise ValueError("Payment ID required for payment access type")
        elif self.access_type == AccessType.PROMO_CODE and not self.promo_code:
            raise ValueError("Promo code required for promo code access type")
        elif self.access_type == AccessType.ADMIN_OVERRIDE and not self.admin_user:
            raise ValueError("Admin user required for admin override access type")
        elif self.access_type == AccessType.BUNDLE and not self.bundle_id:
            raise ValueError("Bundle ID required for bundle access type")


class PremiumGenerationService:
    """
    Unified service for generating premium analysis results.
    
    This service eliminates code duplication by providing a single method
    for premium generation regardless of access method (payment, promo codes, etc.).
    """
    
    def __init__(self):
        """Initialize the premium generation service"""
        self.analysis_service = analysis_service
        logger.info("PremiumGenerationService initialized")
    
    async def generate_premium_results(
        self, 
        analysis_id: str, 
        product_type: str,
        access_context: AccessContext
    ) -> Dict[str, Any]:
        """
        Unified method for generating premium results.
        
        This is the single source of truth for premium generation across all access methods.
        
        Args:
            analysis_id: ID of the analysis to generate premium results for
            product_type: Type of product (resume_analysis, job_fit_analysis, etc.)
            access_context: Context information about how access was granted
            
        Returns:
            Dict containing the premium analysis result
            
        Raises:
            AIAnalysisError: If premium generation fails
            ValueError: If analysis_id or product_type is invalid
        """
        logger.info(f"Generating premium {product_type} for analysis {analysis_id} via {access_context.access_type.value}")
        
        # Validate inputs
        if not analysis_id or not analysis_id.strip():
            raise ValueError("Analysis ID is required")
        
        if not product_type or not product_type.strip():
            raise ValueError("Product type is required")
        
        # Get analysis from database
        analysis = AnalysisDB.get(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis not found: {analysis_id}")
        
        # Check if premium result already exists
        if analysis.get('premium_result'):
            logger.info(f"Premium result already exists for analysis {analysis_id}")
            return analysis['premium_result']
        
        # Generate premium analysis based on product type
        try:
            premium_result = await self._generate_analysis_by_type(
                analysis=analysis,
                product_type=product_type,
                access_context=access_context
            )
            
            if not premium_result:
                raise AIAnalysisError(f"Premium {product_type} returned empty result")
            
            # Store the premium result in database
            AnalysisDB.update_premium_result(analysis_id, premium_result)
            
            # Log successful generation
            logger.info(f"Premium {product_type} generated successfully for analysis {analysis_id}")
            
            return premium_result
            
        except Exception as e:
            logger.error(f"Failed to generate premium {product_type} for analysis {analysis_id}: {e}")
            
            # Create error result for user
            error_result = {
                "error": f"Premium {product_type} generation failed",
                "message": "Our AI analysis service encountered an error. Please contact support.",
                "technical_details": str(e),
                "analysis_id": analysis_id,
                "access_type": access_context.access_type.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Store error result in database
            AnalysisDB.update_premium_result(analysis_id, error_result)
            
            raise AIAnalysisError(f"Premium generation failed: {str(e)}") from e
    
    async def _generate_analysis_by_type(
        self, 
        analysis: Dict[str, Any], 
        product_type: str,
        access_context: AccessContext
    ) -> Dict[str, Any]:
        """
        Generate premium analysis based on product type.
        
        This method encapsulates the product-specific generation logic
        that was previously duplicated across different flows.
        
        Args:
            analysis: Analysis data from database
            product_type: Type of product to generate
            access_context: Access context information
            
        Returns:
            Dict containing the generated premium result
        """
        resume_text = analysis['resume_text']
        
        # Get job posting if required
        job_posting = analysis.get('job_posting') or analysis.get('metadata', {}).get('job_posting', '')
        
        # Generate based on product type
        if product_type == "resume_analysis":
            return await self.analysis_service.analyze_resume(resume_text, 'premium')
            
        elif product_type == "job_fit_analysis":
            if not job_posting:
                raise ValueError("Job posting required for job fit analysis")
            return await self.analysis_service.analyze_resume(resume_text, 'premium', job_posting)
            
        elif product_type == "cover_letter":
            if not job_posting:
                raise ValueError("Job posting required for cover letter generation")
            return await self.analysis_service.generate_cover_letter(resume_text, job_posting)
            
        elif product_type == "resume_rewrite":
            if not job_posting:
                raise ValueError("Job posting required for resume rewrite")
            return await self.analysis_service.complete_resume_rewrite(resume_text, job_posting)
            
        elif product_type == "mock_interview":
            if not job_posting:
                raise ValueError("Job posting required for mock interview")
            return await self.analysis_service.generate_mock_interview_premium(resume_text, job_posting)
            
        else:
            raise ValueError(f"Unknown product type: {product_type}")
    
    def validate_access_context(self, access_context: AccessContext) -> bool:
        """
        Validate that the access context is properly formed.
        
        Args:
            access_context: Access context to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if access context is properly initialized
            if not isinstance(access_context, AccessContext):
                return False
            
            # Validate required fields based on access type
            if access_context.access_type == AccessType.PAYMENT:
                return bool(access_context.payment_id)
            elif access_context.access_type == AccessType.PROMO_CODE:
                return bool(access_context.promo_code)
            elif access_context.access_type == AccessType.ADMIN_OVERRIDE:
                return bool(access_context.admin_user)
            elif access_context.access_type == AccessType.BUNDLE:
                return bool(access_context.bundle_id)
            elif access_context.access_type == AccessType.GIFT_CODE:
                return True  # Gift codes may have different validation rules
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error validating access context: {e}")
            return False
    
    async def get_premium_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve existing premium result for an analysis.
        
        Args:
            analysis_id: ID of the analysis
            
        Returns:
            Premium result if exists, None otherwise
        """
        analysis = AnalysisDB.get(analysis_id)
        if analysis and analysis.get('premium_result'):
            return analysis['premium_result']
        return None
    
    def get_supported_product_types(self) -> List[str]:
        """
        Get list of supported product types for premium generation.
        
        Returns:
            List of supported product types
        """
        return [
            "resume_analysis",
            "job_fit_analysis", 
            "cover_letter",
            "resume_rewrite",
            "mock_interview"
        ]


# Global instance for dependency injection
premium_generation_service = PremiumGenerationService()
