#!/bin/bash

# Docker-based QuickDraw Stop Script
# This script stops all Docker services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Stopping QuickDraw Docker Services...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Function to check if docker-compose is available
check_docker_compose() {
    COMPOSE_IS_LEGACY=false
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD=(docker compose)
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD=(docker-compose)
        COMPOSE_IS_LEGACY=true
    else
        echo -e "${RED}❌ Neither docker-compose nor 'docker compose' is available${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Using ${COMPOSE_CMD[*]}${NC}"

    if [ "$COMPOSE_IS_LEGACY" = true ]; then
        echo -e "${YELLOW}⚠️  Legacy docker-compose detected; enabling compatibility mode (PYTHONNOUSERSITE=1).${NC}"
    fi
}

compose() {
    if [ "$COMPOSE_IS_LEGACY" = true ]; then
        PYTHONNOUSERSITE=1 "${COMPOSE_CMD[@]}" "$@"
    else
        "${COMPOSE_CMD[@]}" "$@"
    fi
}

check_docker_compose

# Stop all services
echo -e "${YELLOW}🛑 Stopping all services...${NC}"
compose down

# Optional: Remove volumes (uncomment if you want to clear Redis data)
# echo -e "${YELLOW}🗑️  Removing volumes...${NC}"
# compose down -v

echo -e "${GREEN}✅ All QuickDraw Docker services stopped${NC}"

# Show status
echo -e "\n${BLUE}📋 Current Docker containers:${NC}"
docker ps -a --filter "name=quickdraw"