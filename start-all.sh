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
PROJECT_ROOT="$SCRIPT_DIR"

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
check_port 8000 || { echo -e "${RED}❌ Backend port 8000 is occupied${NC}"; exit 1; }
check_port 3000 || { echo -e "${RED}❌ Frontend port 3000 is occupied${NC}"; exit 1; }
check_port 8501 || { echo -e "${RED}❌ Dashboard port 8501 is occupied${NC}"; exit 1; }

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
echo -e "${YELLOW}📡 Starting Backend API (port 8000)...${NC}"
cd "$PROJECT_ROOT/backend"
python app.py > "../logs/backend.log" 2>&1 &
BACKEND_PID=$!

# 2. Start Frontend Server
echo -e "${YELLOW}🌐 Starting Frontend Server (port 3000)...${NC}"
cd "$PROJECT_ROOT/frontend"
python -m http.server 3000 > "../logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

# 3. Start Dashboard
echo -e "${YELLOW}📊 Starting Dashboard (port 8501)...${NC}"
cd "$PROJECT_ROOT/dashboard"
streamlit run app.py --server.port=8501 --server.headless=true > "../logs/dashboard.log" 2>&1 &
DASHBOARD_PID=$!

# Wait for services to be ready
sleep 2
wait_for_service "http://localhost:8000/docs" "Backend API"
wait_for_service "http://localhost:3000" "Frontend"
wait_for_service "http://localhost:8501" "Dashboard"

echo -e "\n${GREEN}🎉 All services are running!${NC}"
echo -e "${BLUE}📋 Service URLs:${NC}"
echo -e "  🎮 Game Frontend:  ${GREEN}http://localhost:3000${NC}"
echo -e "  📡 Backend API:    ${GREEN}http://localhost:8000${NC}"
echo -e "  📊 Dashboard:      ${GREEN}http://localhost:8501${NC}"
echo -e "  📚 API Docs:       ${GREEN}http://localhost:8000/docs${NC}"

echo -e "\n${YELLOW}💡 Logs are being written to:${NC}"
echo -e "  • Backend:   logs/backend.log"
echo -e "  • Frontend:  logs/frontend.log"
echo -e "  • Dashboard: logs/dashboard.log"

echo -e "\n${BLUE}Press Ctrl+C to stop all services${NC}"

# Keep the script running and wait for all background jobs
wait