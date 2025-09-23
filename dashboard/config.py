# Dashboard Configuration
import os
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    # Backend API settings
    "backend_url": os.getenv("QUICKDRAW_BACKEND_URL", "http://localhost:8000"),
    
    # Redis settings
    "redis_host": os.getenv("REDIS_HOST", "localhost"),
    "redis_port": int(os.getenv("REDIS_PORT", "6379")),
    "redis_db": int(os.getenv("REDIS_DB", "0")),
    
    # Dashboard settings
    "auto_refresh_interval": 30,  # seconds
    "max_players_in_charts": 20,
    "default_time_range": "All time",
    "default_difficulties": ["easy", "hard"],
    
    # Chart settings
    "chart_height": 400,
    "color_scheme": {
        "easy": "#4CAF50",
        "hard": "#F44336"
    },
    
    # Pagination settings
    "max_sessions_per_page": 100,
    "max_rankings_display": 100,
    
    # Cache settings
    "cache_ttl": 300,  # 5 minutes
}

def get_config() -> Dict[str, Any]:
    """Get dashboard configuration"""
    return DEFAULT_CONFIG.copy()

def update_config(new_config: Dict[str, Any]) -> None:
    """Update configuration with new values"""
    DEFAULT_CONFIG.update(new_config)