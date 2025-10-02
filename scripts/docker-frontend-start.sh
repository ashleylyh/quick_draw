#!/bin/bash

# Docker Frontend Startup Script
# Injects environment variables and starts the frontend server

set -e

echo "🔧 Injecting environment variables for Docker frontend..."

# Set working directory
cd /app

# Set default values for environment variables (Docker containers receive these from docker-compose)
BACKEND_PORT=${BACKEND_PORT:-8000}
BACKEND_HOST=${BACKEND_HOST:-backend}  # In Docker, use service name for internal communication
FRONTEND_PORT=${FRONTEND_PORT:-3000}
FRONTEND_HOST=${FRONTEND_HOST:-localhost}
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}
DASHBOARD_HOST=${DASHBOARD_HOST:-localhost}

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
window.BACKEND_CLIENT = 'http://${BACKEND_HOST}:${BACKEND_PORT}';
window.FRONTEND_CLIENT = 'http://${FRONTEND_HOST}:${FRONTEND_PORT}';
window.DASHBOARD_CLIENT = 'http://${DASHBOARD_HOST}:${DASHBOARD_PORT}';
EOF

echo "✅ Environment variables injected for Docker frontend"
echo "   Backend: http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "   Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "   Dashboard: http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"

# Change to frontend directory and start server
cd /app/frontend
echo "🚀 Starting frontend server on port ${FRONTEND_PORT}..."
exec python -m http.server ${FRONTEND_PORT}