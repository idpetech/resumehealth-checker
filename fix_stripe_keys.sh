#!/bin/bash
# Fix Stripe Keys - Add Missing Publishable Key

echo "🔧 Fixing Stripe Configuration..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi

# Add the missing publishable key
echo "Adding STRIPE_PUBLISHABLE_TEST_KEY to .env file..."

# Create a backup
cp .env .env.backup

# Add the publishable key (you'll need to get the real one from Stripe dashboard)
cat >> .env << 'EOF'

# Stripe Publishable Key (get from https://dashboard.stripe.com/test/apikeys)
STRIPE_PUBLISHABLE_TEST_KEY=pk_test_51Ru8yUEEk2SJOP4YKSKdJUQxO5N6qrFR6lkwqQ0ZbKvERDtcJLHWF9SBcQEuZISbqkMmQ9URUXr
m8u9BFophy0UC00tu60DjFn
EOF

echo "✅ Added STRIPE_PUBLISHABLE_TEST_KEY to .env"
echo ""
echo "🔍 To get your real publishable key:"
echo "1. Go to: https://dashboard.stripe.com/test/apikeys"
echo "2. Copy the 'Publishable key' (starts with pk_test_)"
echo "3. Replace the placeholder in .env with your real key"
echo ""
echo "🧪 Test the configuration:"
echo "   python check_stripe_config.py"


