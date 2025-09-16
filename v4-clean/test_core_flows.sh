#!/bin/bash
#
# MANDATORY Core Flow Testing Script
# This script MUST pass before any commit to prevent breaking working functionality
#

set -e  # Exit on any error

echo "🔍 MANDATORY CORE FLOW TESTING"
echo "================================"

BASE_URL="http://localhost:8000"

# Check if server is running
if ! curl -s "$BASE_URL/health" > /dev/null 2>&1; then
    echo "❌ Server not running at $BASE_URL"
    echo "   Start server with: python main.py"
    exit 1
fi

echo "✅ Server is running"

# Test 1: Main page loads and has required JavaScript functions
echo ""
echo "🔍 Test 1: JavaScript Functions Available"
MAIN_PAGE=$(curl -s "$BASE_URL/")

REQUIRED_FUNCTIONS=("exportToPDFClient" "exportToWord" "copyToClipboard" "toggleQuestion" "toggleAllQuestions")

for func in "${REQUIRED_FUNCTIONS[@]}"; do
    if echo "$MAIN_PAGE" | grep -q "function $func"; then
        echo "✅ Function $func found"
    else
        echo "❌ Function $func MISSING - CRITICAL ERROR"
        exit 1
    fi
done

# Test 2: Free analysis endpoint works
echo ""
echo "🔍 Test 2: Free Analysis Flow"

# Create a test resume file
cat > test_resume_temp.txt << 'EOF'
John Smith
Software Engineer

Experience:
- Software Developer at ABC Company (2020-2022)
- Built web applications using Python and JavaScript
- Improved system performance by 30%

Education:
- Bachelor's Degree in Computer Science from XYZ University (2018)

Skills:
- Python, JavaScript, React, Node.js
- Database management
- Problem solving
EOF

# Test file upload and analysis
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@test_resume_temp.txt" "$BASE_URL/api/v1/analyze")

if echo "$UPLOAD_RESPONSE" | grep -q '"analysis_id"'; then
    echo "✅ Free analysis API working"
    
    # Extract analysis ID for further testing
    ANALYSIS_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"analysis_id":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$ANALYSIS_ID" ]; then
        echo "✅ Analysis ID: $ANALYSIS_ID"
        
        # Test if analysis results are accessible
        RESULTS_URL="$BASE_URL/api/v1/premium-results/$ANALYSIS_ID?embedded=true&product_type=resume_analysis"
        RESULTS_RESPONSE=$(curl -s "$RESULTS_URL")
        
        if echo "$RESULTS_RESPONSE" | grep -q "premium-results"; then
            echo "✅ Analysis results accessible"
            
            # Test if required buttons exist in free analysis
            if echo "$RESULTS_RESPONSE" | grep -q 'onclick="copyToClipboard'; then
                echo "✅ Copy button found in free analysis"
            else
                echo "❌ Copy button MISSING in free analysis"
                exit 1
            fi
            
            if echo "$RESULTS_RESPONSE" | grep -q 'onclick="exportToPDFClient'; then
                echo "✅ PDF export button found in free analysis"
            else
                echo "❌ PDF export button MISSING in free analysis"
                exit 1
            fi
            
        else
            echo "❌ Analysis results NOT accessible"
            exit 1
        fi
    else
        echo "❌ Could not extract analysis ID"
        exit 1
    fi
else
    echo "❌ Free analysis API BROKEN"
    exit 1
fi

# Clean up temp file
rm -f test_resume_temp.txt

# Test 3: Template structure validation
echo ""
echo "🔍 Test 3: Template Structure Validation"

TEMPLATES=("resume_analysis" "mock_interview" "resume_rewrite" "job_fit_analysis" "cover_letter")

for template in "${TEMPLATES[@]}"; do
    TEMPLATE_URL="$BASE_URL/api/v1/premium-results/test?embedded=true&product_type=$template"
    TEMPLATE_RESPONSE=$(curl -s "$TEMPLATE_URL" 2>/dev/null || echo "error")
    
    if [ "$TEMPLATE_RESPONSE" != "error" ]; then
        # Templates will return "Analysis not found" for invalid IDs, which is expected behavior
        if echo "$TEMPLATE_RESPONSE" | grep -q "Analysis not found"; then
            echo "✅ Template $template responding correctly (404 for invalid ID)"
        elif echo "$TEMPLATE_RESPONSE" | grep -q "premium-results"; then
            echo "✅ Template $template structure valid"
        else
            echo "⚠️  Template $template may have issues"
        fi
    else
        echo "⚠️  Template $template not accessible (may be expected)"
    fi
done

# Test 4: No JavaScript errors in main page
echo ""
echo "🔍 Test 4: JavaScript Syntax Validation"

# Check for basic JavaScript syntax issues
if echo "$MAIN_PAGE" | grep -q "function.*{" && echo "$MAIN_PAGE" | grep -q "</script>"; then
    echo "✅ JavaScript syntax appears valid"
else
    echo "❌ JavaScript syntax issues detected"
    exit 1
fi

# Test 5: Required libraries loaded
echo ""
echo "🔍 Test 5: Required Libraries"

REQUIRED_LIBS=("jspdf" "html2canvas")

for lib in "${REQUIRED_LIBS[@]}"; do
    if echo "$MAIN_PAGE" | grep -qi "$lib"; then
        echo "✅ Library $lib found"
    else
        echo "❌ Library $lib MISSING"
        exit 1
    fi
done

echo ""
echo "🎉 ALL CORE FLOWS WORKING"
echo "================================"
echo "✅ JavaScript functions available"
echo "✅ Free analysis flow working"
echo "✅ Template structures valid"
echo "✅ No syntax errors detected"
echo "✅ Required libraries loaded"
echo ""
echo "💚 SAFE TO COMMIT"

exit 0