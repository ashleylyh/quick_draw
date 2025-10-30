"""
Environment Configuration for QuickDraw Dashboard
Loads configuration from environment variables with fallback defaults
"""
import os
from typing import Dict, Any

# Backend API settings
BACKEND_URL = os.getenv("QUICKDRAW_BACKEND_URL", "http://localhost:8000")

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Dashboard settings
AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "30"))
MAX_PLAYERS_IN_CHARTS = int(os.getenv("MAX_PLAYERS_IN_CHARTS", "20"))
DEFAULT_TIME_RANGE = os.getenv("DEFAULT_TIME_RANGE", "All time")

# Parse comma-separated difficulties
DEFAULT_DIFFICULTIES = os.getenv("DEFAULT_DIFFICULTIES", "easy,hard").split(",")

# Chart settings
CHART_HEIGHT = int(os.getenv("CHART_HEIGHT", "400"))
EASY_COLOR = os.getenv("EASY_COLOR", "#4CAF50") 
HARD_COLOR = os.getenv("HARD_COLOR", "#F44336")

# Pagination settings
MAX_SESSIONS_PER_PAGE = int(os.getenv("MAX_SESSIONS_PER_PAGE", "100"))
MAX_RANKINGS_DISPLAY = int(os.getenv("MAX_RANKINGS_DISPLAY", "100"))

# Cache settings
CACHE_TTL = int(os.getenv("CACHE_TTL", "0"))  # 0 = no expiration

# Configuration dictionary (for backward compatibility)
CONFIG = {
    "backend_url": BACKEND_URL,
    "redis_host": REDIS_HOST,
    "redis_port": REDIS_PORT,
    "redis_db": REDIS_DB,
    "auto_refresh_interval": AUTO_REFRESH_INTERVAL,
    "max_players_in_charts": MAX_PLAYERS_IN_CHARTS,
    "default_time_range": DEFAULT_TIME_RANGE,
    "default_difficulties": DEFAULT_DIFFICULTIES,
    "chart_height": CHART_HEIGHT,
    "color_scheme": {
        "easy": EASY_COLOR,
        "hard": HARD_COLOR
    },
    "max_sessions_per_page": MAX_SESSIONS_PER_PAGE,
    "max_rankings_display": MAX_RANKINGS_DISPLAY,
    "cache_ttl": CACHE_TTL,
}

def get_config() -> Dict[str, Any]:
    """Get dashboard configuration"""
    return CONFIG.copy()

def update_config(new_config: Dict[str, Any]) -> None:
    """Update configuration with new values"""
    CONFIG.update(new_config)