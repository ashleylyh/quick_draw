# QuickDraw Docker Deployment Guide 🐳

This guide explains how to deploy the QuickDraw application using Docker, maintaining the same structure as your local development environment.

## 📋 Overview

The Docker setup creates 4 services that mirror your current development flow:
1. **Redis** - Database and caching (port 6379)
2. **Backend** - FastAPI application (port 8000)
3. **Frontend** - HTTP server for game interface (port 3000) 
4. **Dashboard** - Streamlit analytics dashboard (port 8501)

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for containers
- Ports 3000, 6379, 8000, 8501 available on your system
- (Optional) NVIDIA GPU drivers + NVIDIA Container Toolkit if you plan to run with GPU acceleration

### 1. One-Command Start
```bash
./docker-start.sh
```

This script will:
- Build all Docker images
- Start all services with proper dependencies
- Wait for services to be healthy
- Display service URLs and logging instructions

### 2. Alternative: Manual Docker Compose
```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### ⚡ Optional: Enable GPU Acceleration
By default the stack runs entirely on CPU, so it works on servers without NVIDIA hardware. If you have an NVIDIA GPU and want TensorFlow to access it, supply the GPU override file when starting the stack:
```bash
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```
This keeps the core configuration portable while enabling GPU reservations only when explicitly requested.

## 🔧 Docker Scripts

### `docker-start.sh` - Complete Startup
- Builds images if needed
- Starts all services with health checks
- Displays service URLs
- Follows logs (Ctrl+C to stop log viewing only)
- When `ENABLE_NGROK_FRONTEND=true` in `.env`, automatically launches the optional `ngrok-frontend` service and prints the public URL for sharing the game interface

### `scripts/show-ngrok-urls.sh` - Inspect ngrok tunnel
- Queries the ngrok admin API (default `http://127.0.0.1:4040/api/tunnels`)
- Prints any active HTTPS tunnels and the selected frontend URL
- With `--update-env`, persists the discovered URL into `.env` (`PUBLIC_FRONTEND_URL`)
- With `--reload-backend`, recreates the backend container so the updated origin is allowed by CORS

### `docker-stop.sh` - Clean Shutdown
- Stops all running containers
- Preserves data volumes
- Shows container status

### `docker-build.sh` - Build Only
```bash
# Regular build
./docker-build.sh

# Rebuild from scratch (clears cache)
./docker-build.sh --rebuild
```

## 🌐 Service URLs

Once running, access your application at (ports can be customized in `.env`):
- **🎮 Game Interface**: http://localhost:3030
- **📡 Backend API**: http://localhost:8000  
- **📚 API Documentation**: http://localhost:8000/docs
- **📊 Analytics Dashboard**: http://localhost:8501
- **🔧 Redis Database**: localhost:6379
- **🌍 Public Frontend (optional)**: Set `ENABLE_NGROK_FRONTEND=true` and run `docker-start.sh` to generate a single ngrok tunnel. The discovered HTTPS URL is stored in `.env` as `PUBLIC_FRONTEND_URL` and shown after startup.

## 📊 Container Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Dashboard     │
│   Port: 3000    │    │   Port: 8501    │
│   (HTTP Server) │    │   (Streamlit)   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────┐
         │   Backend       │
         │   Port: 8000    │
         │   (FastAPI)     │
         └─────────────────┘
                     │
         ┌─────────────────┐
         │   Redis         │
         │   Port: 6379    │
         │   (Database)    │
         └─────────────────┘
```

## 🔍 Monitoring & Debugging

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend  
docker-compose logs -f dashboard
docker-compose logs -f redis
```

### Check Service Health
```bash
# Container status
docker-compose ps

# Service health endpoints
curl http://localhost:8000/docs      # Backend API docs
curl http://localhost:3000           # Frontend
curl http://localhost:8501/_stcore/health  # Dashboard health
```

### Resource Usage
```bash
# Container resource usage
docker stats

# Individual container info
docker inspect quickdraw-backend
```

## 📁 Volume Mounts

The Docker setup mounts these directories for persistence:
- `./logs:/app/logs` - Application logs
- `./backend/uploads:/app/backend/uploads` - Game screenshots
- `redis_data` - Redis database (Docker managed volume)

## ⚙️ Environment Configuration

Key environment variables in docker-compose.yml:

### Backend Service
- `REDIS_HOST=redis` - Redis container hostname
- `REDIS_PORT=6379` - Redis port
- `FRONTEND_CLIENT=http://localhost:3000` - Frontend URL
- `DASHBOARD_CLIENT=http://localhost:8501` - Dashboard URL
- `PUBLIC_FRONTEND_URL=` - Optional HTTPS URL (ngrok) automatically whitelisted for CORS when set
<<<<<<< HEAD
=======
- `PUBLIC_BACKEND_URL=` - Optional HTTPS URL if the backend is exposed through a separate tunnel
>>>>>>> deploy

### Dashboard Service  
- `QUICKDRAW_BACKEND_URL=http://backend:8000` - Backend API URL (internal)
- `REDIS_HOST=redis` - Redis container hostname

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using a port
lsof -i :8000

# Stop conflicting services
./stop-all.sh  # Stop local development services
```

#### 2. Docker Build Fails
```bash
# Clear Docker cache and rebuild
./docker-build.sh --rebuild

# Or manually:
docker system prune -f
docker-compose build --no-cache
```

#### 3. Service Won't Start
```bash
# Check container logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart backend

# Recreate containers
docker-compose down
docker-compose up -d
```

#### 4. Redis Connection Issues
```bash
# Check Redis container
docker-compose logs redis

# Test Redis connection
docker-compose exec redis redis-cli ping
```

#### 5. Out of Disk Space
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove unused images
docker image prune -a
```

### Health Check Failures

If health checks fail:

1. **Backend**: Check if ML models are loading properly
2. **Frontend**: Ensure static files are accessible  
3. **Dashboard**: Verify Streamlit configuration
4. **Redis**: Check if Redis process started correctly

## 🔄 Development Workflow

### Making Code Changes
1. Stop containers: `./docker-stop.sh`
2. Make your changes
3. Rebuild and restart: `./docker-start.sh`

### For faster development iterations:
```bash
# Only rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Or restart without rebuilding (for config changes)
docker-compose restart backend
```

## 📈 Performance Optimization

### Resource Limits
Add resource limits to docker-compose.yml:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Image Size Optimization
- The Dockerfile uses multi-stage builds where possible
- `.dockerignore` excludes unnecessary files
- Uses slim Python base image

## 🔒 Security Considerations

- Redis runs without authentication (suitable for development)
- Services communicate via internal Docker network
- Only necessary ports are exposed to host
- No secrets are hardcoded in images
- When exposing the frontend via ngrok:
  - Restrict backend CORS to trusted origins by keeping `CORS_ALLOWED_ORIGINS` scoped
  - `PUBLIC_FRONTEND_URL` is automatically appended to the allowed origins set
  - The backend/Dashboard remain on the private Docker network and are not tunneled

For production deployment, consider:
- Adding Redis authentication
- Using environment files for secrets
- Implementing proper logging and monitoring
- Adding reverse proxy (nginx) for HTTPS

## 🧹 Cleanup

### Remove Everything
```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker rmi quickdraw-backend quickdraw-frontend quickdraw-dashboard

# Full Docker cleanup (careful!)
docker system prune -a --volumes
```

### Partial Cleanup
```bash
# Stop containers but keep volumes
./docker-stop.sh

# Remove only stopped containers
docker container prune

# Remove unused images only
docker image prune
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. View service logs: `docker-compose logs [service]`
3. Ensure Docker and Docker Compose are up to date
4. Try rebuilding images: `./docker-build.sh --rebuild`

## 🔄 Migration from Local Development

To migrate from your current local setup:

1. **Stop local services**: `./stop-all.sh`
2. **Start Docker services**: `./docker-start.sh` 
3. **Verify functionality**: Test all endpoints
4. **Update development workflow**: Use Docker scripts instead of local ones

Your data and logs will be preserved through volume mounts!