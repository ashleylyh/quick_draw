#!/bin/bash

# Docker-based QuickDraw Startup Script
# This script builds and starts all services using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Starting QuickDraw Application with Docker...${NC}"

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

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down Docker services...${NC}"
    $COMPOSE_CMD down
    echo -e "${GREEN}✅ All Docker services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check prerequisites
check_docker
check_docker_compose

# Build the Docker images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
$COMPOSE_CMD build

# Start all services
echo -e "${YELLOW}🚀 Starting all services...${NC}"
$COMPOSE_CMD up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"

# Wait for backend to be ready
echo -e "${BLUE}📡 Checking backend service...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/docs >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend API is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend API failed to start${NC}"
        $COMPOSE_CMD logs backend
        exit 1
    fi
    sleep 2
done

# Wait for frontend to be ready
echo -e "${BLUE}🌐 Checking frontend service...${NC}"
for i in {1..15}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is ready!${NC}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "${RED}❌ Frontend failed to start${NC}"
        $COMPOSE_CMD logs frontend
        exit 1
    fi
    sleep 2
done

# Wait for dashboard to be ready
echo -e "${BLUE}📊 Checking dashboard service...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8501/_stcore/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Dashboard is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Dashboard failed to start${NC}"
        $COMPOSE_CMD logs dashboard
        exit 1
    fi
    sleep 2
done

echo -e "\n${GREEN}🎉 All services are running successfully!${NC}"
echo -e "\n${BLUE}📋 Service URLs:${NC}"
echo -e "🎮 Game Interface:     ${GREEN}http://localhost:3000${NC}"
echo -e "📡 Backend API:        ${GREEN}http://localhost:8000${NC}"
echo -e "📚 API Documentation:  ${GREEN}http://localhost:8000/docs${NC}"
echo -e "📊 Analytics Dashboard: ${GREEN}http://localhost:8501${NC}"
echo -e "🔧 Redis Database:     ${GREEN}localhost:6379${NC}"

echo -e "\n${YELLOW}📝 To view logs:${NC}"
echo -e "All services: ${BLUE}$COMPOSE_CMD logs -f${NC}"
echo -e "Backend only: ${BLUE}$COMPOSE_CMD logs -f backend${NC}"
echo -e "Frontend only: ${BLUE}$COMPOSE_CMD logs -f frontend${NC}"
echo -e "Dashboard only: ${BLUE}$COMPOSE_CMD logs -f dashboard${NC}"

echo -e "\n${YELLOW}🛑 To stop all services: ${BLUE}Ctrl+C or run: $COMPOSE_CMD down${NC}"

# Follow logs (optional - can be interrupted)
echo -e "\n${BLUE}📋 Following logs (Ctrl+C to stop log viewing):${NC}"
$COMPOSE_CMD logs -f