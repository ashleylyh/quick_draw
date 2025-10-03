# realtime.py - WebSocket and SSE endpoints for real-time communication
from fastapi import WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from typing import Dict, Set
import asyncio
import json
from datetime import datetime
import logging
import re

from env_config import (
    CORS_ALLOWED_ORIGINS,
    CORS_ALLOWED_ORIGIN_REGEX,
    CORS_ALLOW_CREDENTIALS,
    PUBLIC_FRONTEND_URL,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    _compiled_cors_origin_regex = (
        re.compile(CORS_ALLOWED_ORIGIN_REGEX)
        if CORS_ALLOWED_ORIGIN_REGEX
        else None
    )
except re.error:
    logger.warning(
        "Invalid CORS_ALLOWED_ORIGIN_REGEX pattern: %s",
        CORS_ALLOWED_ORIGIN_REGEX,
    )
    _compiled_cors_origin_regex = None


def _is_origin_allowed(origin: str) -> bool:
    if not origin:
        return False

    if not CORS_ALLOWED_ORIGINS:
        return False

    if '*' in CORS_ALLOWED_ORIGINS:
        return True

    if origin in CORS_ALLOWED_ORIGINS:
        return True

    if PUBLIC_FRONTEND_URL and origin == PUBLIC_FRONTEND_URL:
        return True

    if _compiled_cors_origin_regex and _compiled_cors_origin_regex.match(origin):
        return True

    return False

class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # WebSocket connections by type
        self.game_connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        self.dashboard_connections: Set[WebSocket] = set()
        
        # SSE connections
        self.sse_connections: Set[asyncio.Queue] = set()
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, str]] = {}
        
    async def connect_game(self, websocket: WebSocket, session_id: str):
        """Connect a game client WebSocket"""
        await websocket.accept()
        self.game_connections[session_id] = websocket
        self.connection_metadata[websocket] = {
            "type": "game",
            "session_id": session_id,
            "connected_at": datetime.now().isoformat()
        }
        logger.info(f"Game client connected for session: {session_id}")
        
        # Send connection confirmation
        await self.send_to_session(session_id, {
            "type": "connection_confirmed",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    async def connect_dashboard(self, websocket: WebSocket):
        """Connect a dashboard WebSocket"""
        await websocket.accept()
        self.dashboard_connections.add(websocket)
        self.connection_metadata[websocket] = {
            "type": "dashboard",
            "connected_at": datetime.now().isoformat()
        }
        logger.info("Dashboard client connected")
        
        # Send connection confirmation
        await self.send_to_dashboard({
            "type": "connection_confirmed",
            "timestamp": datetime.now().isoformat()
        })
    
    async def disconnect_game(self, session_id: str):
        """Disconnect a game client"""
        if session_id in self.game_connections:
            websocket = self.game_connections[session_id]
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
            del self.game_connections[session_id]
            logger.info(f"Game client disconnected for session: {session_id}")
    
    async def disconnect_dashboard(self, websocket: WebSocket):
        """Disconnect a dashboard client"""
        self.dashboard_connections.discard(websocket)
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        logger.info("Dashboard client disconnected")
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send message to a specific game session"""
        if session_id in self.game_connections:
            websocket = self.game_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                await self.disconnect_game(session_id)
    
    async def send_to_dashboard(self, message: dict):
        """Send message to all dashboard clients"""
        disconnected = []
        for websocket in self.dashboard_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to dashboard: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            await self.disconnect_dashboard(websocket)
    
    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        # Send to all game sessions
        for session_id in list(self.game_connections.keys()):
            await self.send_to_session(session_id, message)
        
        # Send to all dashboard clients
        await self.send_to_dashboard(message)
        
        # Send to SSE clients
        for queue in list(self.sse_connections):
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Error sending SSE message: {e}")
                self.sse_connections.discard(queue)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "game_connections": len(self.game_connections),
            "dashboard_connections": len(self.dashboard_connections),
            "sse_connections": len(self.sse_connections),
            "total_connections": len(self.game_connections) + len(self.dashboard_connections) + len(self.sse_connections)
        }

# Global connection manager instance
connection_manager = ConnectionManager()

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    return connection_manager

# WebSocket endpoint handlers
async def websocket_game_endpoint(websocket: WebSocket, session_id: str):
    """Handle WebSocket connections for game clients"""
    await connection_manager.connect_game(websocket, session_id)
    
    try:
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await connection_manager.send_to_session(session_id, {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "game_status_request":
                    # Get session status and send back
                    await connection_manager.send_to_session(session_id, {
                        "type": "game_status",
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    logger.info(f"Received message from session {session_id}: {message}")
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from session {session_id}")
            except Exception as e:
                logger.error(f"Error handling message from session {session_id}: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect_game(session_id)

async def websocket_dashboard_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for dashboard clients"""
    await connection_manager.connect_dashboard(websocket)
    
    try:
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await connection_manager.send_to_dashboard({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "stats_request":
                    stats = connection_manager.get_connection_stats()
                    await connection_manager.send_to_dashboard({
                        "type": "connection_stats",
                        "stats": stats,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    logger.info(f"Received message from dashboard: {message}")
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from dashboard")
            except Exception as e:
                logger.error(f"Error handling message from dashboard: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect_dashboard(websocket)

async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for real-time updates"""
    origin = request.headers.get("origin")
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }

    if _is_origin_allowed(origin):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
        if CORS_ALLOW_CREDENTIALS:
            headers["Access-Control-Allow-Credentials"] = "true"

    async def event_stream():
        # Create a queue for this SSE connection
        queue = asyncio.Queue()
        connection_manager.sse_connections.add(queue)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            while True:
                try:
                    # Wait for events with timeout
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()})}\n\n"
                
        except asyncio.CancelledError:
            pass
        finally:
            connection_manager.sse_connections.discard(queue)
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=headers
    )

# Background task for event listening (simplified)
async def start_event_listener():
    """Background task for broadcasting events"""
    logger.info("Event listener started for real-time broadcasting")
    
    try:
        while True:
            # Simple periodic broadcast for testing
            await asyncio.sleep(30)
            
            # Broadcast connection stats periodically
            stats = connection_manager.get_connection_stats()
            await connection_manager.broadcast_message({
                "type": "connection_stats",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            })
            
    except asyncio.CancelledError:
        logger.info("Event listener stopped")
    except Exception as e:
        logger.error(f"Event listener error: {e}")