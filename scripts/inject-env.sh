#!/bin/bash

# Environment Variable Injection Script
# Injects environment variables into frontend HTML files

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Turn off automatic export
fi

# Set default values for environment variables
BACKEND_PORT=${BACKEND_PORT:-8000}
BACKEND_HOST=${BACKEND_HOST:-localhost}
FRONTEND_PORT=${FRONTEND_PORT:-3030}
FRONTEND_HOST=${FRONTEND_HOST:-localhost}
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}
DASHBOARD_HOST=${DASHBOARD_HOST:-localhost}

echo "🔧 Injecting environment variables into frontend..."

# Create a temporary environment injection script
cat > "$FRONTEND_DIR/env-inject.js" << EOF
// Auto-generated environment variables
// This file is created by scripts/inject-env.sh
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

echo "✅ Environment variables injected into frontend"
echo "   Backend: http://${BACKEND_HOST}:${BACKEND_PORT}"
echo "   Frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"
echo "   Dashboard: http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"