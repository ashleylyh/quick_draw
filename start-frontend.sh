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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ Frontend directory not found: $FRONTEND_DIR${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8080 is already in use${NC}"
    echo -e "Please stop the existing service or use a different port"
    exit 1
fi

cd "$FRONTEND_DIR"

echo -e "${GREEN}✅ Starting Frontend Server on http://localhost:8080${NC}"
echo -e "${BLUE}🎮 Game Interface: http://localhost:8080${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo

# Start the HTTP server
python -m http.server 8080