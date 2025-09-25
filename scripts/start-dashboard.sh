#!/bin/bash

# QuickDraw Dashboard Startup Script
# Starts the Streamlit dashboard in a new terminal

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting QuickDraw Dashboard...${NC}"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Turn off automatic export
fi

# Set default values for environment variables
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}

# Check if dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo -e "${RED}❌ Dashboard directory not found: $DASHBOARD_DIR${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8501 is already in use${NC}"
    echo -e "Please stop the existing service or use a different port"
    exit 1
fi

cd "$DASHBOARD_DIR"

echo -e "${GREEN}✅ Starting Dashboard on http://localhost:$DASHBOARD_PORT${NC}"
echo -e "${BLUE}📊 Dashboard Interface: http://localhost:$DASHBOARD_PORT${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo

# Start Streamlit
streamlit run app.py --server.port=$DASHBOARD_PORT