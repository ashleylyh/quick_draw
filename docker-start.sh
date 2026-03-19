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

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo -e "${BLUE}📋 Loading environment variables from .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
else
    echo -e "${YELLOW}⚠️  No .env file found, using default values${NC}"
fi

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

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down Docker services...${NC}"
    compose down
    echo -e "${GREEN}✅ All Docker services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check prerequisites
check_docker
check_docker_compose

PROFILE_FLAG=""
if [ "${ENABLE_NGROK_FRONTEND:-false}" = "true" ]; then
    if [ -z "${NGROK_AUTHTOKEN:-}" ]; then
        echo -e "${RED}❌ ENABLE_NGROK_FRONTEND is true but NGROK_AUTHTOKEN is not set.${NC}"
        echo -e "${YELLOW}➡️  Please provide your ngrok auth token in the .env file before continuing.${NC}"
        exit 1
    fi
    PROFILE_FLAG="--profile sharing"
    echo -e "${BLUE}🌐 ngrok frontend tunnelling enabled (profile: sharing)${NC}"
fi

# Build the Docker images
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
compose build

# Start all services
echo -e "${YELLOW}🚀 Starting all services...${NC}"
if [ -n "$PROFILE_FLAG" ]; then
    compose $PROFILE_FLAG up -d
else
    compose up -d
fi

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start...${NC}"

# Wait for backend to be ready
echo -e "${BLUE}📡 Checking backend service...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:${BACKEND_PORT:-8000}/docs >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend API is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend API failed to start${NC}"
        compose logs backend
        exit 1
    fi
    sleep 2
done

# Wait for frontend to be ready
echo -e "${BLUE}🌐 Checking frontend service...${NC}"
for i in {1..15}; do
    if curl -s http://localhost:${FRONTEND_PORT:-3000} >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is ready!${NC}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "${RED}❌ Frontend failed to start${NC}"
        compose logs frontend
        exit 1
    fi
    sleep 2
done

# Wait for dashboard to be ready
echo -e "${BLUE}📊 Checking dashboard service...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:${DASHBOARD_PORT:-8501}/_stcore/health >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Dashboard is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Dashboard failed to start${NC}"
        compose logs dashboard
        exit 1
    fi
    sleep 2
done

echo -e "\n${GREEN}🎉 All services are running successfully!${NC}"
echo -e "\n${BLUE}📋 Service URLs:${NC}"
echo -e "🎮 Game Interface:     ${GREEN}http://localhost:${FRONTEND_PORT:-3000}${NC}"
echo -e "📡 Backend API:        ${GREEN}http://localhost:${BACKEND_PORT:-8000}${NC}"
echo -e "📚 API Documentation:  ${GREEN}http://localhost:${BACKEND_PORT:-8000}/docs${NC}"
echo -e "📊 Analytics Dashboard: ${GREEN}http://localhost:${DASHBOARD_PORT:-8501}${NC}"
echo -e "🔧 Redis Database:     ${GREEN}localhost:${REDIS_PORT:-6379}${NC}"

if [ "${ENABLE_NGROK_FRONTEND:-false}" = "true" ]; then
    echo -e "\n${BLUE}🌐 Discovering ngrok public URL...${NC}"
    if [ -x "$SCRIPT_DIR/scripts/show-ngrok-urls.sh" ]; then
        "$SCRIPT_DIR/scripts/show-ngrok-urls.sh" --update-env --reload-backend || \
            echo -e "${YELLOW}⚠️  Unable to fetch ngrok URL automatically. Run scripts/show-ngrok-urls.sh manually once the tunnel is ready.${NC}"
    else
        echo -e "${YELLOW}⚠️  scripts/show-ngrok-urls.sh is not executable or missing. Please run it manually after fixing permissions.${NC}"
    fi
fi

echo -e "\n${YELLOW}📝 To view logs:${NC}"
echo -e "All services: ${BLUE}${COMPOSE_CMD[*]} logs -f${NC}"
echo -e "Backend only: ${BLUE}${COMPOSE_CMD[*]} logs -f backend${NC}"
echo -e "Frontend only: ${BLUE}${COMPOSE_CMD[*]} logs -f frontend${NC}"
echo -e "Dashboard only: ${BLUE}${COMPOSE_CMD[*]} logs -f dashboard${NC}"

echo -e "\n${YELLOW}🛑 To stop all services: ${BLUE}Ctrl+C or run: ${COMPOSE_CMD[*]} down${NC}"

# Follow logs (optional - can be interrupted)
echo -e "\n${BLUE}📋 Following logs (Ctrl+C to stop log viewing):${NC}"
compose logs -f