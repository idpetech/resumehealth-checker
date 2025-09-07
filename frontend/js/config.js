// API Configuration for Resume Health Checker
const API_CONFIG = {
    // Development environment
    development: {
        baseUrl: 'http://localhost:8000',
        endpoints: {
            checkResume: '/api/v1/analyze',
            health: '/api/v1/health',
            createPaymentSession: '/api/v1/payment/create'
        }
    },
    
    // Production environment
    production: {
        baseUrl: '',  // Use relative URLs for Railway deployment
        endpoints: {
            checkResume: '/api/v1/analyze',
            health: '/api/v1/health',
            createPaymentSession: '/api/v1/payment/create'
        }
    }
};

// Automatically detect environment
const ENVIRONMENT = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'development' 
    : 'production';

// Current API configuration
const API = API_CONFIG[ENVIRONMENT];

// Stripe Configuration
const STRIPE_CONFIG = {
    paymentUrl: 'https://buy.stripe.com/test_dRm8wPaXq2028FEgNQ0000F',
    successToken: 'payment_success_123'
};

// Helper function to build full API URLs
function getApiUrl(endpoint) {
    return API.baseUrl + API.endpoints[endpoint];
}

// Export for use in other scripts
window.API_CONFIG = API_CONFIG;
window.API = API;
window.STRIPE_CONFIG = STRIPE_CONFIG;
window.getApiUrl = getApiUrl;