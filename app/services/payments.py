"""
Payment Processing Service

Handles Stripe integration with bulletproof session management and multi-environment support.
This is the critical component that fixes all the payment flow issues from previous versions.
"""
import stripe
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..core.config import config
from ..core.exceptions import PaymentError, StripeError
from ..core.database import PaymentDB

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for handling Stripe payments with bulletproof session management"""
    
    def __init__(self):
        """Initialize Stripe with environment-appropriate keys"""
        try:
            stripe.api_key = config.stripe_secret_key
            self.environment = config.environment
            self.stripe_available = False
            
            logger.info(f"Payment service initialized for {self.environment} environment")
            
            # Check if we have valid Stripe keys
            if not config.stripe_secret_key or "placeholder" in config.stripe_secret_key or "your-" in config.stripe_secret_key:
                logger.warning("⚠️ No valid Stripe keys configured - mock payments enabled")
                self.stripe_available = False
            else:
                # Test real Stripe keys
                try:
                    # Test the connection by retrieving account balance
                    stripe.Balance.retrieve()
                    logger.info("✅ Stripe connection verified with real keys")
                    self.stripe_available = True
                except stripe.error.AuthenticationError as e:
                    logger.warning(f"⚠️ Stripe authentication failed - using mock payments: {e}")
                    self.stripe_available = False
                except Exception as e:
                    logger.warning(f"⚠️ Stripe connection failed - using mock payments: {e}")
                    self.stripe_available = False
                    
        except Exception as e:
            logger.error(f"Payment service initialization failed: {e}")
            self.stripe_available = False
    
    async def create_payment_session(
        self,
        analysis_id: str,
        product_type: str,
        amount: int,
        currency: str = "usd",
        product_name: str = "Resume Analysis"
    ) -> Dict[str, Any]:
        """
        Create Stripe Checkout session with bulletproof URL handling
        
        Args:
            analysis_id: ID of the analysis this payment is for
            product_type: Type of product (resume_analysis, job_fit_analysis, etc.)
            amount: Amount in cents (e.g., 1000 for $10.00)
            currency: Currency code (usd, pkr, inr, etc.)
            product_name: Display name for the product
            
        Returns:
            Dictionary with session details
            
        Raises:
            PaymentError: If session creation fails
        """
        logger.info(f"Creating payment session: {product_type} for analysis {analysis_id}")
        
        # Check if Stripe is available
        if not self.stripe_available:
            logger.warning("Stripe not available - returning mock payment session for testing")
            return self._create_mock_payment_session(analysis_id, product_type, amount, currency, product_name)
        
        try:
            # Generate unique session reference
            session_ref = f"analysis_{analysis_id}_{uuid.uuid4().hex[:8]}"
            
            # Calculate session expiry (30 minutes from now)
            expires_at = int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
            
            # Get URLs for logging
            success_url = config.get_stripe_success_url(analysis_id, product_type)
            cancel_url = config.get_stripe_cancel_url(analysis_id, product_type)
            logger.info(f"Success URL: {success_url}")
            logger.info(f"Cancel URL: {cancel_url}")
            
            # Create Stripe session with bulletproof URLs
            session = stripe.checkout.Session.create(
                mode='payment',
                payment_method_types=['card'],
                
                line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': product_name,
                            'description': f"AI-powered {product_type.replace('_', ' ').title()}"
                        },
                        'unit_amount': amount,  # Amount should already be in cents
                    },
                    'quantity': 1,
                }],
                
                # CRITICAL: Bulletproof success/cancel URLs with all context
                success_url=success_url,
                cancel_url=cancel_url,
                
                # Session configuration
                expires_at=expires_at,
                client_reference_id=session_ref,
                
                # Metadata for tracking and webhooks
                metadata={
                    'analysis_id': analysis_id,
                    'product_type': product_type,
                    'session_reference': session_ref,
                    'environment': self.environment,
                    'amount_dollars': f"{amount/100:.2f}",
                    'currency': currency.upper()
                },
                
                # Additional settings
                billing_address_collection='auto',
                shipping_address_collection=None,  # Digital product
                allow_promotion_codes=self.environment != "production",  # Only in test/staging
                
                # Customer can save payment methods for future use
                customer_creation='if_required',
                
                # Automatic tax calculation if configured
                automatic_tax={'enabled': False},  # Keep simple for now
            )
            
            # Store payment session in database for tracking
            await self._store_payment_session(
                analysis_id=analysis_id,
                stripe_session_id=session.id,
                session_ref=session_ref,
                amount=amount,
                currency=currency,
                product_type=product_type
            )
            
            logger.info(f"✅ Payment session created: {session.id}")
            
            return {
                'session_id': session.id,
                'payment_url': session.url,
                'session_url': session.url,  # Keep both for compatibility
                'session_reference': session_ref,
                'expires_at': expires_at,
                'amount': amount,
                'currency': currency.upper(),
                'product_type': product_type,
                'environment': self.environment
            }
            
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid Stripe request: {e}")
            raise PaymentError(f"Payment setup failed: {str(e)}")
        
        except stripe.error.AuthenticationError as e:
            logger.error(f"Stripe authentication error: {e}")
            raise PaymentError("Payment service authentication failed")
        
        except stripe.error.RateLimitError as e:
            logger.error(f"Stripe rate limit exceeded: {e}")
            raise PaymentError("Payment service is temporarily overloaded. Please try again.")
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise PaymentError(f"Payment processing error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error creating payment session: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise PaymentError(f"Payment session creation failed: {str(e)}")
    
    async def verify_payment_session(self, session_id: str) -> Dict[str, Any]:
        """
        Verify and retrieve payment session details
        
        Args:
            session_id: Stripe session ID
            
        Returns:
            Session verification details
            
        Raises:
            PaymentError: If verification fails
        """
        logger.info(f"Verifying payment session: {session_id}")
        
        try:
            # Retrieve session from Stripe with expanded data
            session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['line_items', 'payment_intent', 'customer']
            )
            
            # Extract key information
            verification_result = {
                'session_id': session.id,
                'payment_status': session.payment_status,
                'session_status': session.status,
                'amount_total': session.amount_total,
                'currency': session.currency,
                'customer_email': session.customer_details.email if session.customer_details else None,
                'customer_name': session.customer_details.name if session.customer_details else None,
                'payment_intent_id': session.payment_intent.id if session.payment_intent else None,
                'client_reference_id': session.client_reference_id,
                'metadata': session.metadata,
                'created': session.created,
                'expires_at': session.expires_at
            }
            
            # Update local database
            if session.payment_status == 'paid':
                await self._mark_payment_completed(session_id, verification_result)
            
            logger.info(f"✅ Payment session verified: {session.payment_status}")
            return verification_result
            
        except stripe.error.InvalidRequestError:
            logger.error(f"Invalid session ID: {session_id}")
            raise PaymentError("Invalid payment session")
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying session: {e}")
            raise PaymentError(f"Payment verification failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error verifying session: {e}")
            raise PaymentError(f"Payment verification error: {str(e)}")
    
    async def handle_webhook_event(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events securely
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            
        Returns:
            Event processing result
        """
        logger.info("Processing Stripe webhook")
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, config.stripe_webhook_secret
            )
            
            event_type = event['type']
            logger.info(f"Processing webhook event: {event_type}")
            
            # Handle different event types
            if event_type == 'checkout.session.completed':
                await self._handle_session_completed(event['data']['object'])
            elif event_type == 'payment_intent.succeeded':
                await self._handle_payment_succeeded(event['data']['object'])
            elif event_type == 'payment_intent.payment_failed':
                await self._handle_payment_failed(event['data']['object'])
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            return {
                'status': 'success',
                'event_type': event_type,
                'processed_at': datetime.utcnow().isoformat()
            }
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise PaymentError("Invalid webhook signature")
        
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise PaymentError(f"Webhook processing failed: {str(e)}")
    
    async def _store_payment_session(
        self, 
        analysis_id: str, 
        stripe_session_id: str, 
        session_ref: str,
        amount: int, 
        currency: str, 
        product_type: str
    ):
        """Store payment session in database"""
        try:
            metadata = {
                'session_reference': session_ref,
                'product_type': product_type,
                'environment': self.environment
            }
            
            PaymentDB.create_session(
                analysis_id=analysis_id,
                stripe_session_id=stripe_session_id,
                amount=amount,
                currency=currency,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to store payment session: {e}")
            # Don't raise error - payment session was created successfully in Stripe
    
    async def _mark_payment_completed(self, session_id: str, verification_result: Dict[str, Any]):
        """Mark payment as completed in database"""
        try:
            payment_intent_id = verification_result.get('payment_intent_id')
            PaymentDB.update_session_status(session_id, 'completed', payment_intent_id)
            
        except Exception as e:
            logger.error(f"Failed to mark payment as completed: {e}")
    
    async def _handle_session_completed(self, session):
        """Handle checkout session completed webhook"""
        session_id = session['id']
        analysis_id = session['metadata'].get('analysis_id')
        
        logger.info(f"Session completed: {session_id} for analysis {analysis_id}")
        
        # Update database
        await self._mark_payment_completed(session_id, {'payment_intent_id': session.get('payment_intent')})
    
    async def _handle_payment_succeeded(self, payment_intent):
        """Handle payment intent succeeded webhook"""
        logger.info(f"Payment succeeded: {payment_intent['id']}")
    
    async def _handle_payment_failed(self, payment_intent):
        """Handle payment intent failed webhook"""
        logger.warning(f"Payment failed: {payment_intent['id']}")
    
    def _create_mock_payment_session(
        self,
        analysis_id: str,
        product_type: str,
        amount: int,
        currency: str,
        product_name: str
    ) -> Dict[str, Any]:
        """Create a mock payment session for testing when Stripe is not available"""
        session_ref = f"mock_analysis_{analysis_id}_{uuid.uuid4().hex[:8]}"
        expires_at = int((datetime.utcnow() + timedelta(minutes=30)).timestamp())
        
        # Create a mock session URL that shows a test message
        mock_url = f"{config.base_url}/api/v1/payment/mock?session_id=mock_{session_ref}&analysis_id={analysis_id}&product_type={product_type}"
        
        logger.info(f"✅ Mock payment session created: {session_ref}")
        
        return {
            'session_id': f"mock_{session_ref}",
            'payment_url': mock_url,
            'session_url': mock_url,  # Keep both for compatibility
            'session_reference': session_ref,
            'expires_at': expires_at,
            'amount': amount,
            'currency': currency.upper(),
            'product_type': product_type,
            'environment': self.environment,
            'mock': True,
            'message': 'This is a mock payment session for testing. Stripe keys are not configured.'
        }

# Singleton instance - lazy initialization
payment_service = None

def get_payment_service():
    """Get the payment service instance with lazy initialization"""
    global payment_service
    if payment_service is None:
        payment_service = PaymentService()
    return payment_service