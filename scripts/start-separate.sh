#!/bin/bash

# QuickDraw Multi-Terminal Startup Script
# Opens each service in a separate terminal tab/window

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting QuickDraw Services in Separate Terminals...${NC}"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a  # Turn off automatic export
fi

# Set default values for environment variables
FRONTEND_PORT=${FRONTEND_PORT:-3030}
BACKEND_PORT=${BACKEND_PORT:-8000}
DASHBOARD_PORT=${DASHBOARD_PORT:-8501}
FRONTEND_HOST=${FRONTEND_HOST:-localhost}
BACKEND_HOST=${BACKEND_HOST:-localhost}
DASHBOARD_HOST=${DASHBOARD_HOST:-localhost}

# Function to detect terminal emulator and open new tabs/windows
open_in_terminal() {
    local script_name=$1
    local service_name=$2
    local script_path="$SCRIPT_DIR/$script_name"
    
    # Make script executable if not already
    chmod +x "$script_path"
    
    echo -e "${YELLOW}📂 Opening $service_name in new terminal...${NC}"
    
    # Detect available terminal and open accordingly
    if command -v gnome-terminal >/dev/null 2>&1; then
        # GNOME Terminal (Ubuntu/most Linux)
        gnome-terminal --tab --title="QuickDraw $service_name" -- bash -c "cd '$SCRIPT_DIR' && ./$script_name; exec bash"
    elif command -v konsole >/dev/null 2>&1; then
        # KDE Konsole
        konsole --new-tab --title "QuickDraw $service_name" -e bash -c "cd '$SCRIPT_DIR' && ./$script_name; exec bash" &
    elif command -v xfce4-terminal >/dev/null 2>&1; then
        # XFCE Terminal
        xfce4-terminal --tab --title="QuickDraw $service_name" --command="bash -c 'cd \"$SCRIPT_DIR\" && ./$script_name; exec bash'" &
    elif command -v terminator >/dev/null 2>&1; then
        # Terminator
        terminator --new-tab --title="QuickDraw $service_name" --command="bash -c 'cd \"$SCRIPT_DIR\" && ./$script_name; exec bash'" &
    elif command -v alacritty >/dev/null 2>&1; then
        # Alacritty
        alacritty --title "QuickDraw $service_name" --command bash -c "cd '$SCRIPT_DIR' && ./$script_name; exec bash" &
    elif command -v tilix >/dev/null 2>&1; then
        # Tilix
        tilix --new-session --title="QuickDraw $service_name" --command="bash -c 'cd \"$SCRIPT_DIR\" && ./$script_name; exec bash'" &
    else
        # Fallback: try xterm
        if command -v xterm >/dev/null 2>&1; then
            xterm -title "QuickDraw $service_name" -e bash -c "cd '$SCRIPT_DIR' && ./$script_name; exec bash" &
        else
            echo -e "${RED}❌ No supported terminal emulator found${NC}"
            echo -e "${YELLOW}💡 Please manually run: ./$script_name${NC}"
            return 1
        fi
    fi
    
    sleep 0.5  # Brief delay between opening terminals
}

# Check if individual scripts exist
for script in "start-backend.sh" "start-frontend.sh" "start-dashboard.sh"; do
    if [ ! -f "$SCRIPT_DIR/$script" ]; then
        echo -e "${RED}❌ Script not found: $script${NC}"
        exit 1
    fi
done

echo -e "${BLUE}🔧 Opening services in separate terminals...${NC}"

# Open each service in a new terminal
open_in_terminal "start-backend.sh" "Backend"
open_in_terminal "start-frontend.sh" "Frontend" 
open_in_terminal "start-dashboard.sh" "Dashboard"

echo -e "\n${GREEN}🎉 All services are being started in separate terminals!${NC}"
echo -e "${BLUE}📋 Service URLs (will be available shortly):${NC}"
echo -e "  🎮 Game Frontend:  ${GREEN}http://${FRONTEND_HOST}:${FRONTEND_PORT}${NC}"
echo -e "  📡 Backend API:    ${GREEN}http://${BACKEND_HOST}:${BACKEND_PORT}${NC}"
echo -e "  📊 Dashboard:      ${GREEN}http://${DASHBOARD_HOST}:${DASHBOARD_PORT}${NC}"
echo -e "  📚 API Docs:       ${GREEN}http://${BACKEND_HOST}:${BACKEND_PORT}/docs${NC}"

echo -e "\n${YELLOW}💡 Each service is running in its own terminal tab/window${NC}"
echo -e "${YELLOW}   Close the respective terminal to stop each service${NC}"