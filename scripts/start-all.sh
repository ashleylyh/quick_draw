#!/bin/bash

# QuickDraw All-in-One Startup Script
# This script starts all services (backend, frontend, dashboard) in one command

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting QuickDraw Application Suite...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Turn off automatic export
fi

# Set default values for environment variables
FRONTEND_PORT=${FRONTEND_PORT:-3000}
BACKEND_PORT=${BACKEND_PORT:-8000}  
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}⏳ Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${RED}❌ $service_name failed to start within 30 seconds${NC}"
    return 1
}

# Check if required ports are available
echo -e "${BLUE}🔍 Checking port availability...${NC}"
check_port $BACKEND_PORT || { echo -e "${RED}❌ Backend port $BACKEND_PORT is occupied${NC}"; exit 1; }
check_port $FRONTEND_PORT || { echo -e "${RED}❌ Frontend port $FRONTEND_PORT is occupied${NC}"; exit 1; }
check_port $DASHBOARD_PORT || { echo -e "${RED}❌ Dashboard port $DASHBOARD_PORT is occupied${NC}"; exit 1; }

echo -e "${GREEN}✅ All ports available${NC}"

# Create log directory
mkdir -p "$PROJECT_ROOT/logs"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill all background jobs
    jobs -p | xargs -I {} kill {} 2>/dev/null || true
    
    # Kill processes by port if they're still running
    pkill -f "uvicorn.*app:app" 2>/dev/null || true
    pkill -f "python.*-m.*http.server.*3000" 2>/dev/null || true
    pkill -f "streamlit.*run" 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}🔧 Starting services...${NC}"

# 1. Start Backend API
echo -e "${YELLOW}📡 Starting Backend API (port $BACKEND_PORT)...${NC}"
cd "$PROJECT_ROOT/backend"
export BACKEND_PORT FRONTEND_PORT DASHBOARD_PORT
python app.py > "../logs/backend.log" 2>&1 &
BACKEND_PID=$!

# 2. Start Frontend Server
echo -e "${YELLOW}🌐 Starting Frontend Server (port $FRONTEND_PORT)...${NC}"
cd "$PROJECT_ROOT/frontend"
python -m http.server $FRONTEND_PORT > "../logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

# 3. Start Dashboard
echo -e "${YELLOW}📊 Starting Dashboard (port $DASHBOARD_PORT)...${NC}"
cd "$PROJECT_ROOT/dashboard"
streamlit run app.py --server.port=$DASHBOARD_PORT --server.headless=true > "../logs/dashboard.log" 2>&1 &
DASHBOARD_PID=$!

# Wait for services to be ready
sleep 2
wait_for_service "http://localhost:$BACKEND_PORT/docs" "Backend API"
wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"
wait_for_service "http://localhost:$DASHBOARD_PORT" "Dashboard"

echo -e "\n${GREEN}🎉 All services are running!${NC}"
echo -e "${BLUE}📋 Service URLs:${NC}"
echo -e "  🎮 Game Frontend:  ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  📡 Backend API:    ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  📊 Dashboard:      ${GREEN}http://localhost:$DASHBOARD_PORT${NC}"
echo -e "  📚 API Docs:       ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"

echo -e "\n${YELLOW}💡 Logs are being written to:${NC}"
echo -e "  • Backend:   logs/backend.log"
echo -e "  • Frontend:  logs/frontend.log"
echo -e "  • Dashboard: logs/dashboard.log"

echo -e "\n${BLUE}Press Ctrl+C to stop all services${NC}"

# Keep the script running and wait for all background jobs
wait