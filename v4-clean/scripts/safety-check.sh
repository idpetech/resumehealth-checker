#!/bin/bash

# Safety Check Script - Run before and after any changes
# Usage: ./scripts/safety-check.sh [before|after]

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOG_FILE="safety-check-$TIMESTAMP.log"

echo "🔍 Safety Check - $(date)" | tee $LOG_FILE
echo "=================================" | tee -a $LOG_FILE

# Check 1: API Endpoints
echo "📋 Current API Endpoints:" | tee -a $LOG_FILE
grep -n "@router\." app/api/routes.py | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Check 2: Critical Files Exist
echo "📁 Critical Files Check:" | tee -a $LOG_FILE
CRITICAL_FILES=(
    "app/api/routes.py"
    "app/templates/payment_success.html"
    "app/static/index.html"
    "app/services/payments.py"
    "app/services/analysis.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists" | tee -a $LOG_FILE
    else
        echo "❌ $file MISSING!" | tee -a $LOG_FILE
    fi
done
echo "" | tee -a $LOG_FILE

# Check 3: Syntax Check
echo "🔧 Syntax Check:" | tee -a $LOG_FILE
python3 -m py_compile app/api/routes.py 2>&1 | tee -a $LOG_FILE
if [ $? -eq 0 ]; then
    echo "✅ Syntax OK" | tee -a $LOG_FILE
else
    echo "❌ Syntax Errors Found!" | tee -a $LOG_FILE
fi
echo "" | tee -a $LOG_FILE

# Check 4: Git Status
echo "📊 Git Status:" | tee -a $LOG_FILE
git status --porcelain | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Check 5: Endpoint Count
ENDPOINT_COUNT=$(grep -c "@router\." app/api/routes.py)
echo "📊 Total API Endpoints: $ENDPOINT_COUNT" | tee -a $LOG_FILE

# Check 6: Key Endpoints Exist
KEY_ENDPOINTS=(
    "/analyze"
    "/payment/create"
    "/payment/success"
    "/premium/"
    "/promo/validate"
    "/analysis/"
)

echo "🎯 Key Endpoints Check:" | tee -a $LOG_FILE
for endpoint in "${KEY_ENDPOINTS[@]}"; do
    if grep -q "@router.*\"$endpoint" app/api/routes.py; then
        echo "✅ $endpoint exists" | tee -a $LOG_FILE
    else
        echo "❌ $endpoint MISSING!" | tee -a $LOG_FILE
    fi
done

echo "" | tee -a $LOG_FILE
echo "🔍 Safety Check Complete - Log saved to $LOG_FILE" | tee -a $LOG_FILE

# Create backup if requested
if [ "$1" = "before" ]; then
    echo "💾 Creating backup branch..." | tee -a $LOG_FILE
    git checkout -b "backup-before-$(date +%Y%m%d-%H%M%S)" 2>&1 | tee -a $LOG_FILE
    git checkout develop 2>&1 | tee -a $LOG_FILE
    echo "✅ Backup created" | tee -a $LOG_FILE
fi
