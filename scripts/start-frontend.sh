#!/bin/bash

# QuickDraw Frontend Startup Script
# Starts the frontend HTTP server in a new terminal

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting QuickDraw Frontend Server...${NC}"

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
FRONTEND_PORT=${FRONTEND_PORT:-3000}

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 3000 is already in use${NC}"
    echo -e "Please stop the existing service or use a different port"
    exit 1
fi

cd "$FRONTEND_DIR"

echo -e "${GREEN}✅ Starting Frontend Server on http://localhost:$FRONTEND_PORT${NC}"
echo -e "${BLUE}🎮 Game Interface: http://localhost:$FRONTEND_PORT${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo

# Start the HTTP server
python -m http.server   3000