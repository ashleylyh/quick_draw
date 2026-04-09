// Frontend Configuration
// This file contains the configuration for the frontend application

// Get backend URL from environment or use default
// In development, this can be overridden by setting BACKEND_URL before serving
const getBackendUrl = () => {
    // Try to get from window if set by server
    if (window.BACKEND_URL) {
        return window.BACKEND_URL;
    }
    
    // Try to get from window environment variables (set by server)
    if (window.BACKEND_CLIENT) {
        return window.BACKEND_CLIENT;
    }
    
    // Try to get from current host (for production deployment)
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        // If accessing via ngrok or similar tunnel, use the same ngrok URL for backend
        // since both frontend and backend are served through the same ngrok tunnel via nginx proxy
        if (window.location.hostname.includes('ngrok') || window.location.hostname.includes('tunnel')) {
            return `${window.location.protocol}//${window.location.hostname}`;
        }
        // For true production deployment where backend is also public
        const backendPort = window.BACKEND_PORT || '8000';
        return `${window.location.protocol}//${window.location.hostname}:${backendPort}`;
    }
    
    // Default for local development - use environment variable for backend port
    const backendPort = window.BACKEND_PORT || '8000';
    const backendHost = window.BACKEND_HOST || 'localhost';
    return `http://${backendHost}:${backendPort}`;
};

// Configuration object
const CONFIG = {
    // Backend API configuration
    API_BASE: '/api/quickdraw',
    API_BASE_URL: '/api/quickdraw',
    BACKEND_URL: '/api/quickdraw',
    WS_BASE: (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws/quickdraw',
    DASHBOARD_URL: '/quickdraw-dashboard',
    
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