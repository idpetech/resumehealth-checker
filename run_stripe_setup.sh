#!/bin/bash
# Stripe Setup Script
# Run this after setting your API keys

echo "🚀 STRIPE AUTOMATED SETUP"
echo "=========================="
echo

# Check if API key is set
if [ -z "$STRIPE_SECRET_TEST_KEY" ]; then
    echo "❌ ERROR: STRIPE_SECRET_TEST_KEY not set"
    echo
    echo "Please run:"
    echo "export STRIPE_SECRET_TEST_KEY=\"sk_test_YOUR_KEY_HERE\""
    echo
    echo "Get your API key from: https://dashboard.stripe.com/apikeys"
    exit 1
fi

echo "✅ Stripe API key configured"
echo "🧪 Running in TEST mode first..."
echo

# Activate virtual environment and run setup
source .venv/bin/activate
python setup_stripe_products.py --mode test

echo
echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "1. Check your Stripe Dashboard: https://dashboard.stripe.com/test/products"
echo "2. Test some payments with test cards"  
echo "3. When ready, run with --mode live for production"
echo