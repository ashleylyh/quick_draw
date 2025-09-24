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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DASHBOARD_DIR="$SCRIPT_DIR/dashboard"

# Check if dashboard directory exists
if [ ! -d "$DASHBOARD_DIR" ]; then
    echo -e "${RED}❌ Dashboard directory not found: $DASHBOARD_DIR${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8501 is already in use${NC}"
    echo -e "Please stop the existing service or use a different port"
    exit 1
fi

cd "$DASHBOARD_DIR"

echo -e "${GREEN}✅ Starting Dashboard on http://localhost:8501${NC}"
echo -e "${BLUE}📊 Dashboard Interface: http://localhost:8501${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo

# Start Streamlit
streamlit run app.py --server.port=8501