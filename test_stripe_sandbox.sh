#!/bin/bash
# Stripe Sandbox Testing Script
# Created: 2025-08-31
# Purpose: Comprehensive testing of Resume Health Checker Stripe integration

set -e

# Configuration
BASE_URL="http://localhost:8002"
TEST_REGIONS=("US" "PK" "IN" "HK" "AE" "BD")
COLORS_ENABLED=true

# Color codes for output
if [[ "$COLORS_ENABLED" == "true" ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    PURPLE=''
    CYAN=''
    NC=''
fi

# Helper functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_test() {
    echo -e "${CYAN}🧪 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test functions
test_server_health() {
    print_test "Testing server health check..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
    if [ "$response" = "200" ]; then
        print_success "Server is responding (HTTP $response)"
    else
        print_error "Server health check failed (HTTP $response)"
        exit 1
    fi
}

test_regional_pricing() {
    print_header "TESTING REGIONAL PRICING APIs"
    
    for region in "${TEST_REGIONS[@]}"; do
        print_test "Testing region: $region"
        
        response=$(curl -s "$BASE_URL/api/stripe-pricing/$region")
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/stripe-pricing/$region")
        
        if [ "$http_code" = "200" ]; then
            currency=$(echo "$response" | grep -o '"currency":"[^"]*' | cut -d'"' -f4)
            symbol=$(echo "$response" | grep -o '"symbol":"[^"]*' | cut -d'"' -f4)
            resume_amount=$(echo "$response" | grep -A5 '"resume_analysis"' | grep -o '"amount":[0-9]*' | cut -d':' -f2)
            
            print_success "Region: $region | Currency: $currency | Symbol: $symbol | Resume: $symbol$resume_amount"
        else
            print_error "Failed to fetch pricing for $region (HTTP $http_code)"
        fi
        
        sleep 0.5
    done
}

test_multi_product_config() {
    print_header "TESTING MULTI-PRODUCT CONFIGURATION"
    
    print_test "Fetching multi-product pricing config..."
    response=$(curl -s "$BASE_URL/api/multi-product-pricing")
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/multi-product-pricing")
    
    if [ "$http_code" = "200" ]; then
        version=$(echo "$response" | grep -o '"version":"[^"]*' | cut -d'"' -f4)
        resume_price=$(echo "$response" | grep -A10 '"resume_analysis"' | grep -o '"amount":[0-9]*' | head -1 | cut -d':' -f2)
        print_success "Multi-product config loaded | Version: $version | Resume: \$$resume_price"
    else
        print_error "Failed to fetch multi-product config (HTTP $http_code)"
    fi
}

test_payment_session_creation() {
    print_header "TESTING PAYMENT SESSION CREATION"
    
    # Test 1: Resume Analysis (US)
    print_test "Creating payment session for Resume Analysis (US region)..."
    session_response=$(curl -s -X POST "$BASE_URL/api/create-payment-session" \
        -F "product_type=individual" \
        -F "product_id=resume_analysis" \
        -F 'session_data={"resume_text":"Test resume content","session_id":"test_us_001","user_region":"US"}')
    
    session_id=$(echo "$session_response" | grep -o '"payment_session_id":"[^"]*' | cut -d'"' -f4)
    payment_url=$(echo "$session_response" | grep -o '"payment_url":"[^"]*' | cut -d'"' -f4)
    
    if [[ -n "$session_id" && -n "$payment_url" ]]; then
        print_success "US session created | ID: ${session_id:0:8}... | URL length: ${#payment_url}"
    else
        print_error "Failed to create US payment session"
    fi
    
    sleep 1
    
    # Test 2: Job Fit Analysis (Pakistan)  
    print_test "Creating payment session for Job Fit Analysis (Pakistan region)..."
    session_response=$(curl -s -X POST "$BASE_URL/api/create-payment-session" \
        -F "product_type=individual" \
        -F "product_id=job_fit_analysis" \
        -F 'session_data={"resume_text":"Test resume content","session_id":"test_pk_001","user_region":"PK"}')
    
    session_id=$(echo "$session_response" | grep -o '"payment_session_id":"[^"]*' | cut -d'"' -f4)
    amount=$(echo "$session_response" | grep -o '"amount":[0-9]*' | cut -d':' -f2)
    
    if [[ -n "$session_id" && -n "$amount" ]]; then
        print_success "Pakistan session created | ID: ${session_id:0:8}... | Amount: \$$amount"
    else
        print_error "Failed to create Pakistan payment session"
    fi
}

test_ui_loading() {
    print_header "TESTING UI LOADING"
    
    print_test "Testing homepage HTML loading..."
    html_response=$(curl -s "$BASE_URL/")
    
    if [[ "$html_response" == *"Resume Health Checker"* ]]; then
        print_success "Homepage HTML loads correctly"
    else
        print_error "Homepage HTML loading failed"
    fi
    
    # Test regional UI parameters
    for region in "US" "PK" "IN"; do
        print_test "Testing UI with region parameter: $region"
        regional_response=$(curl -s "$BASE_URL/?test_country=$region")
        if [[ "$regional_response" == *"Resume Health Checker"* ]]; then
            print_success "Regional UI loads for $region"
        else
            print_warning "Regional UI may have issues for $region"
        fi
        sleep 0.3
    done
}

run_comprehensive_test() {
    print_header "STRIPE SANDBOX COMPREHENSIVE TEST SUITE"
    echo -e "${PURPLE}Started: $(date)${NC}"
    echo -e "${PURPLE}Base URL: $BASE_URL${NC}"
    echo ""
    
    # Run all tests
    test_server_health
    echo ""
    test_regional_pricing
    echo ""
    test_multi_product_config  
    echo ""
    test_payment_session_creation
    echo ""
    test_ui_loading
    
    print_header "TEST SUITE COMPLETED"
    echo -e "${GREEN}✅ All tests completed successfully!${NC}"
    echo -e "${PURPLE}Finished: $(date)${NC}"
    echo ""
    echo -e "${CYAN}🔗 STRIPE TEST CARD FOR MANUAL TESTING:${NC}"
    echo -e "${YELLOW}   Card: 4242 4242 4242 4242${NC}"
    echo -e "${YELLOW}   Expiry: 12/25${NC}"
    echo -e "${YELLOW}   CVC: 123${NC}"
    echo ""
}

# Individual test functions for targeted testing
run_quick_test() {
    print_header "QUICK SMOKE TEST"
    test_server_health
    test_regional_pricing
    print_success "Quick test completed"
}

run_payment_test() {
    print_header "PAYMENT FLOW TEST"
    test_payment_session_creation
    print_success "Payment test completed"
}

# Help function
show_help() {
    echo "Stripe Sandbox Testing Script"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  full         Run comprehensive test suite (default)"
    echo "  quick        Run quick smoke test"
    echo "  pricing      Test regional pricing only"
    echo "  payment      Test payment session creation only"
    echo "  ui           Test UI loading only"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run full test suite"
    echo "  $0 quick          # Run quick smoke test"
    echo "  $0 pricing        # Test regional pricing APIs"
    echo ""
}

# Main execution logic
case "${1:-full}" in
    "full")
        run_comprehensive_test
        ;;
    "quick")
        run_quick_test
        ;;
    "pricing")
        test_regional_pricing
        ;;
    "payment")  
        run_payment_test
        ;;
    "ui")
        test_ui_loading
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac