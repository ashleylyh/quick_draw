// Frontend Configuration
// This file contains the configuration for the frontend application

// Get backend URL from environment or use default
// In development, this can be overridden by setting BACKEND_URL before serving
const getBackendUrl = () => {
    // Try to get from window if set by server
    if (window.BACKEND_URL) {
        return window.BACKEND_URL;
    }
    
    // Try to get from current host (for production deployment)
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    
    // Default for local development
    return 'http://localhost:8000';
};

// Configuration object
const CONFIG = {
    // Backend API configuration
    BACKEND_URL: getBackendUrl(),
    API_BASE: `${getBackendUrl()}/api`,
    
    // WebSocket configuration
    WS_BASE: getBackendUrl().replace('http', 'ws'),
    
    // Frontend configuration
    FRONTEND_URL: window.location.origin,
    
    // UI Configuration
    CANVAS_WIDTH: 400,
    CANVAS_HEIGHT: 400,
    
    // Game Configuration (should match backend)
    PER_ROUND: 4,
    NUM_ROUNDS: 6,
    
    // API Endpoints
    ENDPOINTS: {
        SESSIONS: '/sessions',
        PREDICT: '/predict',
        PREDICT_REALTIME: '/predict-realtime', 
        UMAP: '/umap',
        RADAR: '/radar',
        PLOTS: '/plots',
        QR_CODE: '/qr-code',
        GENERATE_QR: '/generate-qr-code',
        UPLOAD_SCREENSHOT: '/upload-screenshot',
        SESSION: '/session',
        DRAWING: '/drawing'
    },
    
    // WebSocket endpoints
    WS_ENDPOINTS: {
        GAME: '/ws/game',
        DASHBOARD: '/ws/dashboard'
    },
    
    // SSE endpoints
    SSE_ENDPOINTS: {
        EVENTS: '/events'
    }
};

// Export for use in other scripts
window.CONFIG = CONFIG;