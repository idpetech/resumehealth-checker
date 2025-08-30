# 🧪 Payment Flow Testing Guide

This guide shows you how to test the full payment functionality without spending real money.

## Method 1: URL Simulation (Instant Testing)

### Quick Test Commands
```bash
# Test the new session-based flow locally
open "http://localhost:8001/?client_reference_id=test-session-123"

# Test production with session
open "https://web-production-f7f3.up.railway.app/?client_reference_id=test-session-456"

# Test backward compatibility with old token
open "https://web-production-f7f3.up.railway.app/?payment_token=payment_success_123"
```

### Interactive Testing
1. Open `test_payment_flow.html` in your browser
2. Follow the step-by-step simulation
3. Test all payment return scenarios

## Method 2: Stripe Test Cards (Real Payment Flow)

### Stripe Test Card Numbers
```
✅ SUCCESSFUL PAYMENTS:
4242 4242 4242 4242  (Visa)
5555 5555 5555 4444  (Mastercard)
3782 822463 10005    (American Express)

❌ FAILED PAYMENTS:
4000 0000 0000 0002  (Card declined)
4000 0000 0000 9995  (Insufficient funds)

📝 ANY EXPIRY DATE: Use any future date (e.g., 12/25)
📝 ANY CVC: Use any 3-4 digit code (e.g., 123)
📝 ANY NAME: Use any name
```

### Test Payment Process
1. **Upload Resume**: Go to production site and upload a test resume
2. **Get Free Analysis**: See the teaser analysis
3. **Click "Upgrade"**: This saves your file and redirects to Stripe
4. **Use Test Card**: Enter `4242 4242 4242 4242` with any expiry/CVC
5. **Complete Payment**: You'll be redirected back with session ID
6. **Verify Premium**: Should automatically show full analysis

## Method 3: Local Development Testing

### Start Local Server
```bash
source .venv/bin/activate
uvicorn main_vercel:app --host 0.0.0.0 --port 8001 --reload
```

### Manual URL Testing
```bash
# Test session validation
curl "http://localhost:8001/?client_reference_id=test-123"

# Test old token (should still work)
curl "http://localhost:8001/?payment_token=payment_success_123"

# Test invalid session (should fail gracefully)
curl "http://localhost:8001/?client_reference_id=invalid"
```

## Method 4: Browser localStorage Testing

### Simulate Complete Flow
```javascript
// 1. Generate session ID
const sessionId = crypto.randomUUID();

// 2. Store fake file data
const fakeFile = {
    name: "test-resume.pdf",
    type: "application/pdf",
    data: btoa("fake pdf content")
};
localStorage.setItem(`resume_${sessionId}`, JSON.stringify(fakeFile));

// 3. Navigate to payment return URL
window.location.href = `/?client_reference_id=${sessionId}`;
```

## Testing Checklist

### ✅ Security Tests
- [ ] Old static token URL no longer gives free premium: `/?payment_token=payment_success_123`
- [ ] Invalid session IDs fail gracefully: `/?client_reference_id=fake-id`
- [ ] Valid session IDs work properly: `/?client_reference_id=real-uuid`

### ✅ Functionality Tests  
- [ ] File upload generates unique session ID
- [ ] File stored with session key in localStorage
- [ ] Stripe redirect includes session ID parameter
- [ ] Return from Stripe validates correct session
- [ ] Premium analysis delivered after valid session
- [ ] Reset button clears all parameters

### ✅ Backward Compatibility Tests
- [ ] Old payment tokens still work during transition
- [ ] Old localStorage keys still function
- [ ] Mixed scenarios handled gracefully

## Production Testing URLs

### Safe Test URLs (Won't charge you)
```
# New session-based (replace SESSION_ID with real UUID)
https://web-production-f7f3.up.railway.app/?client_reference_id=SESSION_ID

# Old token-based (deprecated but works)  
https://web-production-f7f3.up.railway.app/?payment_token=payment_success_123
```

### Stripe Test Mode Setup
1. **Login to Stripe Dashboard**: https://dashboard.stripe.com
2. **Toggle Test Mode**: Switch to "Test" in the top left
3. **Create Test Payment Link**: Use test mode for safe payments
4. **Use Test Cards**: No real charges will occur

## Common Issues & Solutions

### Issue: "Session not found" error
**Solution**: Make sure you generated and stored the session ID before testing the return URL

### Issue: Old token still works
**Solution**: This is intentional during transition period. Will be removed later.

### Issue: File not restored after payment
**Solution**: Check that the session ID in URL matches the localStorage key

### Issue: Stripe test payments not working
**Solution**: Ensure you're in Stripe test mode and using test card numbers

## Quick Start Testing

1. **Open**: `test_payment_flow.html`
2. **Click**: "1. Simulate File Upload"
3. **Click**: "2. Generate Session & Store"
4. **Click**: "Test Session-Based Return"
5. **Verify**: Premium analysis appears automatically

This simulates the complete payment flow without any real payments! 🎉