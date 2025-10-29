// realtime.js - Real-time communication utilities for frontend
class RealTimeManager {
    constructor() {
        this.websocket = null;
        this.eventSource = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.isConnected = false;
        
        // Event callbacks
        this.onConnectionChange = null;
        this.onGameEvent = null;
        this.onError = null;
        
        // Ping interval for keeping connection alive
        this.pingInterval = null;
    }
    
    // Initialize WebSocket connection for game sessions
    connectWebSocket(sessionId) {
        this.sessionId = sessionId;
        this.disconnectWebSocket(); // Close any existing connection
        
        try {
            const wsUrl = `${window.CONFIG.WS_BASE}/ws/game/${sessionId}`;
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = (event) => {
                console.log('WebSocket connected for session:', sessionId);
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 1000;
                
                if (this.onConnectionChange) {
                    this.onConnectionChange(true);
                }
                
                // Start ping interval to keep connection alive
                this.startPingInterval();
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = (event) => {
                console.log('WebSocket connection closed:', event.code, event.reason);
                this.isConnected = false;
                this.stopPingInterval();
                
                if (this.onConnectionChange) {
                    this.onConnectionChange(false);
                }
                
                // Attempt to reconnect if not a manual close
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect();
                }
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                
                if (this.onError) {
                    this.onError('WebSocket connection error');
                }
            };
            
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            if (this.onError) {
                this.onError('Failed to establish real-time connection');
            }
        }
    }
    
    // Handle incoming WebSocket messages
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection_confirmed':
                // console.log('WebSocket connection confirmed');
                break;
                
            case 'pong':
                // Connection is alive
                break;
                
            case 'game_event':
                if (this.onGameEvent) {
                    this.onGameEvent(data.event);
                }
                break;
                
            case 'game_status':
                // Handle game status updates
                this.handleGameStatus(data.session);
                break;
                
            case 'connection_stats':
                // Handle connection statistics updates
                this.handleConnectionStats(data.stats);
                break;
                
            default:
                // console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    // Handle game status updates
    handleGameStatus(sessionData) {
        // Update UI with current game status
        if (sessionData && sessionData.status) {
            const statusElement = document.getElementById('game-status');
            if (statusElement) {
                statusElement.textContent = `Status: ${sessionData.status}`;
            }
            
            // Update progress indicator
            const progressElement = document.getElementById('game-progress');
            if (progressElement && sessionData.completed_rounds && sessionData.total_rounds) {
                const progress = (sessionData.completed_rounds / sessionData.total_rounds) * 100;
                progressElement.style.width = `${progress}%`;
            }
        }
    }
    
    // Handle connection statistics updates
    handleConnectionStats(stats) {
        // console.log('Connection stats received:', stats);
        
        // Update connection indicator if available
        if (window.connectionIndicator && stats) {
            // You can extend this to show more detailed connection info
            const totalConnections = stats.total_connections || 0;
            const gameConnections = stats.game_connections || 0;
            const dashboardConnections = stats.dashboard_connections || 0;
            
            // Update the connection indicator with stats (optional)
            if (window.connectionIndicator.indicator) {
                const currentText = window.connectionIndicator.indicator.textContent;
                if (currentText.includes('Connected')) {
                    window.connectionIndicator.indicator.title = 
                        `Total: ${totalConnections}, Games: ${gameConnections}, Dashboards: ${dashboardConnections}`;
                }
            }
        }
        
        // Dispatch custom event for other components to listen
        window.dispatchEvent(new CustomEvent('connectionStats', { 
            detail: { stats } 
        }));
    }
    
    // Send message through WebSocket
    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
            return true;
        }
        return false;
    }
    
    // Request current game status
    requestGameStatus() {
        return this.sendWebSocketMessage({
            type: 'game_status_request'
        });
    }
    
    // Start ping interval to keep connection alive
    startPingInterval() {
        this.stopPingInterval();
        this.pingInterval = setInterval(() => {
            this.sendWebSocketMessage({ type: 'ping' });
        }, 30000); // Ping every 30 seconds
    }
    
    // Stop ping interval
    stopPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }
    
    // Schedule reconnection attempt
    scheduleReconnect() {
        this.reconnectAttempts++;
        // console.log(`Scheduling WebSocket reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${this.reconnectDelay}ms`);
        
        setTimeout(() => {
            if (this.sessionId) {
                this.connectWebSocket(this.sessionId);
            }
        }, this.reconnectDelay);
        
        // Exponential backoff
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    }
    
    // Disconnect WebSocket
    disconnectWebSocket() {
        this.stopPingInterval();
        
        if (this.websocket) {
            this.websocket.close(1000, 'Manual disconnect');
            this.websocket = null;
        }
        
        this.isConnected = false;
        this.sessionId = null;
        this.reconnectAttempts = 0;
    }
    
    // Initialize Server-Sent Events for general updates
    connectSSE() {
        this.disconnectSSE(); // Close any existing connection
        
        try {
            this.eventSource = new EventSource(`${window.CONFIG.BACKEND_URL}/events`);
            
            this.eventSource.onopen = () => {
                // console.log('SSE connection established');
            };
            
            this.eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleSSEMessage(data);
                } catch (error) {
                    console.error('Error parsing SSE message:', error);
                }
            };
            
            this.eventSource.onerror = (error) => {
                console.error('SSE error:', error);
                
                // Reconnect after a delay
                setTimeout(() => {
                    if (!this.eventSource || this.eventSource.readyState === EventSource.CLOSED) {
                        this.connectSSE();
                    }
                }, 5000);
            };
            
        } catch (error) {
            console.error('Failed to create SSE connection:', error);
        }
    }
    
    // Handle SSE messages
    handleSSEMessage(data) {
        switch (data.type) {
            case 'connected':
                console.log('SSE connected');
                break;
                
            case 'keepalive':
                // Connection is alive
                break;
                
            case 'connection_stats':
                // Handle connection statistics from SSE
                this.handleConnectionStats(data.stats);
                break;
                
            case 'event':
                // Handle game events
                if (this.onGameEvent) {
                    this.onGameEvent(data.event);
                }
                break;
                
            default:
                console.log('Unknown SSE message type:', data.type);
        }
    }
    
    // Disconnect SSE
    disconnectSSE() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
    
    // Disconnect all connections
    disconnect() {
        this.disconnectWebSocket();
        this.disconnectSSE();
    }
    
    // Get connection status
    getConnectionStatus() {
        return {
            websocket: this.isConnected,
            sse: this.eventSource && this.eventSource.readyState === EventSource.OPEN,
            sessionId: this.sessionId
        };
    }
}

// Connection status indicator
class ConnectionIndicator {
    constructor() {
        this.indicator = null;
        this.createIndicator();
    }
    
    createIndicator() {
        this.indicator = document.createElement('div');
        this.indicator.id = 'connection-indicator';
        this.indicator.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            padding: 8px 12px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            z-index: 1000;
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(this.indicator);
        this.updateStatus(false);
    }
    
    updateStatus(connected) {
        if (!this.indicator) return;
        
        if (connected) {
            this.indicator.textContent = '🟢 Connected';
            this.indicator.style.backgroundColor = '#4CAF50';
        } else {
            this.indicator.textContent = '🔴 Disconnected';
            this.indicator.style.backgroundColor = '#f44336';
        }
    }
    
    remove() {
        if (this.indicator && this.indicator.parentNode) {
            this.indicator.parentNode.removeChild(this.indicator);
        }
    }
}

// Global instances
window.realTimeManager = new RealTimeManager();

// Setup connection status monitoring
window.realTimeManager.onConnectionChange = (connected) => {
    window.connectionIndicator.updateStatus(connected);
    
    // Show user notification
    const message = connected ? 'Real-time connection established' : 'Real-time connection lost';
    if (window.showNotification) {
        window.showNotification(message, connected ? 'success' : 'warning');
    }
};

// Setup error handling
window.realTimeManager.onError = (error) => {
    console.error('Real-time error:', error);
    if (window.showNotification) {
        window.showNotification(`Connection error: ${error}`, 'error');
    }
};

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    window.realTimeManager.disconnect();
    window.connectionIndicator.remove();
});

// Export for use in other scripts
window.RealTimeManager = RealTimeManager;

console.log('Real-time communication manager loaded');