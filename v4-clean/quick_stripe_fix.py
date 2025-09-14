#!/usr/bin/env python3
"""
Quick fix for Stripe library import issues in payments.py
Replace the problematic exception handling with a simpler approach.
"""

import re

def fix_payments_file():
    """Fix the payments.py file by cleaning up exception handling"""
    
    file_path = "app/services/payments.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the malformed exception handling by replacing the entire problematic section
    # Find the section starting with "except Exception as e:" and ending with the last Stripe error
    pattern = r'(\s+)except Exception as e:\s*# Handle specific Stripe errors.*?except stripe_lib\.error\.StripeError as e:.*?raise PaymentError\([^)]*\)'
    
    replacement = '''        except Exception as e:
            logger.error(f"Unexpected error creating payment session: {e}")
            raise PaymentError(f"Payment session creation failed: {str(e)}")'''
    
    # Replace the problematic section
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also fix the verification method
    pattern2 = r'(\s+)except stripe_lib\.error\.InvalidRequestError:[^}]*?except stripe_lib\.error\.StripeError as e:[^}]*?}'
    
    replacement2 = '''        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return {
                'session_id': session_id,
                'payment_status': 'error',
                'error': str(e)
            }'''
    
    new_content = re.sub(pattern2, replacement2, new_content, flags=re.DOTALL)
    
    # Fix webhook handling
    pattern3 = r'(\s+)except stripe_lib\.error\.SignatureVerificationError:[^}]*?}'
    
    replacement3 = '''        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            raise PaymentError(f"Invalid webhook signature: {str(e)}")'''
    
    new_content = re.sub(pattern3, replacement3, new_content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Fixed payments.py file")

if __name__ == "__main__":
    fix_payments_file()