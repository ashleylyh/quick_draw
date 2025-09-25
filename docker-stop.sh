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

# Function to check if docker-compose is available
check_docker_compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        echo -e "${RED}❌ Neither docker-compose nor 'docker compose' is available${NC}"
        exit 1
    fi
}

check_docker_compose

# Stop all services
echo -e "${YELLOW}🛑 Stopping all services...${NC}"
$COMPOSE_CMD down

# Optional: Remove volumes (uncomment if you want to clear Redis data)
# echo -e "${YELLOW}🗑️  Removing volumes...${NC}"
# $COMPOSE_CMD down -v

echo -e "${GREEN}✅ All QuickDraw Docker services stopped${NC}"

# Show status
echo -e "\n${BLUE}📋 Current Docker containers:${NC}"
docker ps -a --filter "name=quickdraw"