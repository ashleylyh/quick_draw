#!/bin/bash

# Docker Build Script for QuickDraw
# This script builds the Docker images without starting services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔨 Building QuickDraw Docker Images...${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

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
    echo -e "${GREEN}✅ Using $COMPOSE_CMD${NC}"
}

# Check prerequisites
check_docker
check_docker_compose

# Parse command line arguments
REBUILD=false
if [[ "$1" == "--rebuild" || "$1" == "-r" ]]; then
    REBUILD=true
    echo -e "${YELLOW}🔄 Rebuilding images from scratch...${NC}"
fi

# Build images
if [ "$REBUILD" = true ]; then
    echo -e "${YELLOW}🗑️  Removing existing images...${NC}"
    docker image rm quickdraw-backend quickdraw-frontend quickdraw-dashboard 2>/dev/null || true
    
    echo -e "${YELLOW}🔨 Building images without cache...${NC}"
    $COMPOSE_CMD build --no-cache
else
    echo -e "${YELLOW}🔨 Building images...${NC}"
    $COMPOSE_CMD build
fi

echo -e "${GREEN}✅ Docker images built successfully!${NC}"

# Show built images
echo -e "\n${BLUE}📋 Built images:${NC}"
docker images | grep -E "(quickdraw|redis)" | head -10

echo -e "\n${BLUE}💡 Next steps:${NC}"
echo -e "Start services: ${GREEN}./docker-start.sh${NC}"
echo -e "Stop services:  ${GREEN}./docker-stop.sh${NC}"