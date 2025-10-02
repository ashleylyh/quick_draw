#!/bin/bash

# Streamlit Configuration Generator
# Generates streamlit config.toml based on environment variables

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"
STREAMLIT_CONFIG_DIR="$DASHBOARD_DIR/.streamlit"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Turn off automatic export
fi

# Set default values for environment variables
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}
DASHBOARD_HOST=${DASHBOARD_HOST:-localhost}
CORS_ENABLED=${CORS_ENABLED:-true}

# Create .streamlit directory if it doesn't exist
mkdir -p "$STREAMLIT_CONFIG_DIR"

echo "🔧 Generating Streamlit configuration..."

# Create the config.toml file
cat > "$STREAMLIT_CONFIG_DIR/config.toml" << EOF
[global]
developmentMode = false

[server]
headless = true
port = ${DASHBOARD_PORT}
address = "0.0.0.0"
enableCORS = ${CORS_ENABLED,,}
enableXsrfProtection = false

[browser]
gatherUsageStats = false
serverAddress = "${DASHBOARD_HOST}"

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
EOF

echo "✅ Streamlit configuration generated"
echo "   Port: ${DASHBOARD_PORT}"
echo "   Host: ${DASHBOARD_HOST}"
echo "   CORS: ${CORS_ENABLED}"