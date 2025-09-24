#!/bin/bash

# QuickDraw Backend Startup Script
# Starts the FastAPI backend server in a new terminal

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting QuickDraw Backend API...${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port 8000 is already in use${NC}"
    echo -e "Please stop the existing service or use a different port"
    exit 1
fi

cd "$BACKEND_DIR"

echo -e "${GREEN}✅ Starting Backend API on http://localhost:8000${NC}"
echo -e "${BLUE}📚 API Documentation: http://localhost:8000/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo

# Start the server
python app.py