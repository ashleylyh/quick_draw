#!/bin/bash

# QuickDraw Stop Script
# Stops all running QuickDraw services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping QuickDraw Services...${NC}"

# Function to kill processes by pattern
kill_process() {
    local pattern=$1
    local service_name=$2
    
    local pids=$(pgrep -f "$pattern" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo -e "${YELLOW}🔄 Stopping $service_name...${NC}"
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$pattern" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "${YELLOW}🔨 Force stopping $service_name...${NC}"
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ $service_name stopped${NC}"
    else
        echo -e "${BLUE}ℹ️  $service_name was not running${NC}"
    fi
}

# Stop each service
kill_process "uvicorn.*app:app" "Backend API"
kill_process "python.*-m.*http.server.*8080" "Frontend Server"
kill_process "streamlit.*run" "Dashboard"

# Also try to kill by port (backup method)
echo -e "${BLUE}🔍 Checking for any remaining processes on ports 8000, 8080, 8501...${NC}"

for port in 8000 8080 8501; do
    local pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}🔄 Killing process on port $port (PID: $pid)...${NC}"
        kill -TERM $pid 2>/dev/null || true
        sleep 1
        # Force kill if needed
        if kill -0 $pid 2>/dev/null; then
            kill -KILL $pid 2>/dev/null || true
        fi
    fi
done

echo -e "\n${GREEN}🎉 All QuickDraw services have been stopped!${NC}"

# Clean up any log files if they exist
if [ -d "logs" ]; then
    echo -e "${BLUE}📁 Log files are preserved in the logs/ directory${NC}"
fi