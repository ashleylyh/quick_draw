# app.py - Main application with WebSocket support
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import logging
import os

# Import routers and realtime modules
from api import router as game_router
from dashboard_api import router as dashboard_router
from realtime import (
    websocket_game_endpoint, 
    websocket_dashboard_endpoint, 
    sse_endpoint,
    start_event_listener
)
from env_config import (
    FRONTEND_CLIENT, 
    DASHBOARD_CLIENT,
    CORS_ENABLED,
    CORS_ALLOWED_ORIGINS,
    CORS_ALLOWED_ORIGIN_REGEX,
    CORS_ALLOWED_METHODS,
    CORS_ALLOWED_HEADERS,
    CORS_EXPOSED_HEADERS,
    CORS_ALLOW_CREDENTIALS,
    CORS_MAX_AGE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("Starting QuickDraw API server...")
    
    # Pre-load models during startup to avoid loading delays
    from api import get_models
    logger.info("Pre-loading ML models...")
    get_models()
    logger.info("ML models loaded successfully")
    
    # Start the event listener for real-time broadcasting
    event_listener_task = asyncio.create_task(start_event_listener())
    
    try:
        yield
    finally:
        logger.info("Shutting down QuickDraw API server...")
        event_listener_task.cancel()
        try:
            await event_listener_task
        except asyncio.CancelledError:
            pass

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="QuickDraw API",
    description="AI Drawing Duel Game API with Real-time Features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enhanced CORS configuration
if CORS_ENABLED:
    allow_origins = ['*'] if CORS_ALLOWED_ORIGINS == ['*'] else CORS_ALLOWED_ORIGINS
    origin_regex = CORS_ALLOWED_ORIGIN_REGEX if CORS_ALLOWED_ORIGIN_REGEX else None

    if allow_origins == ['*']:
        origin_regex = None

    logger.info(
        "CORS enabled with origins: %s%s",
        allow_origins,
        f" and regex: {origin_regex}" if origin_regex else ""
    )
    
    # Handle wildcard headers
    allowed_headers = CORS_ALLOWED_HEADERS.split(',') if CORS_ALLOWED_HEADERS != '*' else ['*']
    exposed_headers = CORS_EXPOSED_HEADERS.split(',') if CORS_EXPOSED_HEADERS != '*' else ['*']
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=origin_regex,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=allowed_headers,
        expose_headers=exposed_headers,
        max_age=CORS_MAX_AGE
    )
else:
    logger.info("CORS is disabled")

# Include API routers
app.include_router(game_router, prefix="", tags=["Game API"])
app.include_router(dashboard_router, prefix="", tags=["Dashboard API"])

# WebSocket endpoints for real-time communication
@app.websocket("/ws/game/{session_id}")
async def websocket_game(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for game clients"""
    await websocket_game_endpoint(websocket, session_id)

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """WebSocket endpoint for dashboard clients"""
    await websocket_dashboard_endpoint(websocket)

# Server-Sent Events endpoint
@app.get("/events")
async def events_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time updates"""
    return await sse_endpoint(request)

# Root endpoint with API information
@app.get("/")
async def root():
    """API information and status"""
    return {
        "name": "QuickDraw API",
        "version": "1.0.0",
        "description": "AI Drawing Duel Game API with Real-time Features",
        "endpoints": {
            "docs": "/docs",
            "websocket_game": "/ws/game/{session_id}",
            "websocket_dashboard": "/ws/dashboard", 
            "sse": "/events"
        },
        "features": [
            "Real-time WebSocket communication",
            "Server-Sent Events (SSE)",
            "Game session management"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    from fastapi.responses import JSONResponse
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error", 
            "message": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import os
    import signal
    
    # Check if we're in development mode
    is_dev = os.getenv("DEV_MODE", "false").lower() == "true"
    
    # Configure signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, stopping server...")
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"Starting server in {'development' if is_dev else 'production'} mode")
    
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8080,
        reload=is_dev,  # Only reload in development mode
        log_level="info",
        workers=1 if is_dev else None  # Single worker in dev mode for easier debugging
    )
