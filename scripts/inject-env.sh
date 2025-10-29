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
PUBLIC_FRONTEND_URL=${PUBLIC_FRONTEND_URL:-}

DEFAULT_BACKEND_CLIENT="http://${BACKEND_HOST}:${BACKEND_PORT}"
DEFAULT_FRONTEND_CLIENT="http://${FRONTEND_HOST}:${FRONTEND_PORT}"
DEFAULT_DASHBOARD_CLIENT="http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"

BACKEND_CLIENT_VALUE=${BACKEND_CLIENT:-$DEFAULT_BACKEND_CLIENT}
FRONTEND_CLIENT_VALUE=${PUBLIC_FRONTEND_URL:-${FRONTEND_CLIENT:-$DEFAULT_FRONTEND_CLIENT}}
DASHBOARD_CLIENT_VALUE=${DASHBOARD_CLIENT:-$DEFAULT_DASHBOARD_CLIENT}

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
window.BACKEND_CLIENT = '${BACKEND_CLIENT_VALUE}';
window.FRONTEND_CLIENT = '${FRONTEND_CLIENT_VALUE}';
window.DASHBOARD_CLIENT = '${DASHBOARD_CLIENT_VALUE}';
window.PUBLIC_FRONTEND_URL = '${FRONTEND_CLIENT_VALUE}';
EOF

echo "✅ Environment variables injected into frontend"
echo "   Backend: ${BACKEND_CLIENT_VALUE}"
echo "   Frontend: ${FRONTEND_CLIENT_VALUE}"
echo "   Dashboard: ${DASHBOARD_CLIENT_VALUE}"