#!/bin/bash

# Docker Frontend Startup Script
# Injects environment variables and starts the frontend server

set -e

echo "🔧 Injecting environment variables for Docker frontend..."

# Set working directory
cd /app

# Set default values for environment variables (Docker containers receive these from docker-compose)
BACKEND_PORT=${BACKEND_PORT:-8000}
BACKEND_HOST=${BACKEND_HOST:-backend}
FRONTEND_PORT=${FRONTEND_PORT:-3030}
FRONTEND_HOST=${FRONTEND_HOST:-frontend}
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}
DASHBOARD_HOST=${DASHBOARD_HOST:-dashboard}

DEFAULT_BACKEND_CLIENT="http://${BACKEND_HOST}:${BACKEND_PORT}"
DEFAULT_FRONTEND_CLIENT="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
DEFAULT_DASHBOARD_CLIENT="http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"

# If PUBLIC_FRONTEND_URL is set (ngrok), use it for both frontend and backend
if [ -n "$PUBLIC_FRONTEND_URL" ]; then
    BACKEND_CLIENT_VALUE=$PUBLIC_FRONTEND_URL
    FRONTEND_CLIENT_VALUE=$PUBLIC_FRONTEND_URL
else
    BACKEND_CLIENT_VALUE=${BACKEND_CLIENT:-$DEFAULT_BACKEND_CLIENT}
    FRONTEND_CLIENT_VALUE=${FRONTEND_CLIENT:-$DEFAULT_FRONTEND_CLIENT}
fi
DASHBOARD_CLIENT_VALUE=${DASHBOARD_CLIENT:-$DEFAULT_DASHBOARD_CLIENT}

# Create the environment injection file for frontend
cat > "/app/frontend/env-inject.js" << EOF
// Auto-generated environment variables for Docker
// This file is created by scripts/docker-frontend-start.sh
window.BACKEND_PORT = '${BACKEND_PORT}';
window.BACKEND_HOST = '${BACKEND_HOST}';
window.FRONTEND_PORT = '${FRONTEND_PORT}';
window.FRONTEND_HOST = '${FRONTEND_HOST}';
window.DASHBOARD_PORT = '${DASHBOARD_PORT}';
window.DASHBOARD_HOST = '${DASHBOARD_HOST}';
window.BACKEND_CLIENT = '${BACKEND_CLIENT_VALUE}';
window.FRONTEND_CLIENT = '${FRONTEND_CLIENT_VALUE}';
window.DASHBOARD_CLIENT = '${DASHBOARD_CLIENT_VALUE}';
window.PUBLIC_FRONTEND_URL = '${FRONTEND_CLIENT_VALUE}';
EOF

echo "✅ Environment variables injected for Docker frontend"
echo "   Backend: ${BACKEND_CLIENT_VALUE}"
echo "   Frontend: ${FRONTEND_CLIENT_VALUE}"
echo "   Dashboard: ${DASHBOARD_CLIENT_VALUE}"

# Change to frontend directory and start server
cd /app/frontend
echo "🚀 Starting frontend server on port ${FRONTEND_PORT:-3030}..."
exec python -m http.server ${FRONTEND_PORT:-3030}