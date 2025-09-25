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

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Turn off automatic export
fi

# Set default values for environment variables
BACKEND_PORT=${BACKEND_PORT:-8000}

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check if port is available
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${RED}❌ Port $BACKEND_PORT is already in use${NC}"
    echo -e "Please stop the existing service or use a different port"
    exit 1
fi

cd "$BACKEND_DIR"

echo -e "${GREEN}✅ Starting Backend API on http://localhost:$BACKEND_PORT${NC}"
echo -e "${BLUE}📚 API Documentation: http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo

# Start the server
python app.py