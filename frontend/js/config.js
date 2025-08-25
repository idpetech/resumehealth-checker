// API Configuration for Resume Health Checker
const API_CONFIG = {
    // Development environment
    development: {
        baseUrl: 'http://localhost:8000',
        endpoints: {
            checkResume: '/api/check-resume',
            health: '/api/health'
        }
    },
    
    // Production environment
    production: {
        baseUrl: 'https://q752325o84.execute-api.us-east-1.amazonaws.com/Prod',
        endpoints: {
            checkResume: '/api/check-resume',
            health: '/api/health'
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
    paymentUrl: 'https://buy.stripe.com/eVqaEWfOk37Mf9ncPWfMA00',
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