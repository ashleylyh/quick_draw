"""
Environment Configuration for QuickDraw Backend
Loads configuration from environment variables with fallback defaults
"""
import os

# Game Configuration
IMAGE_SIZE = int(os.getenv('IMAGE_SIZE', '784'))  # 28*28
PER_ROUND = int(os.getenv('PER_ROUND', '4'))
NUM_ROUNDS = int(os.getenv('NUM_ROUNDS', '6'))

# Model Configuration
MODEL_PATH = os.getenv('MODEL_PATH', './model/doodleNet-model.keras')
CLASSES_PATH = os.getenv('CLASSES_PATH', './classes.json')

# Network Configuration
API_CLIENT = os.getenv('API_CLIENT', 'localhost:8000')
FRONTEND_CLIENT = os.getenv('FRONTEND_CLIENT', 'http://localhost:3030')
DASHBOARD_CLIENT = os.getenv('DASHBOARD_CLIENT', 'http://localhost:8501')

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# File Paths
FILE_EMB_5 = os.getenv('FILE_EMB_5', './feature/background_embedding_5per_class.csv')
FILE_UMAP = os.getenv('FILE_UMAP', './feature/background_Umap.csv')  
FILE_UMAP_REDUCER = os.getenv('FILE_UMAP_REDUCER', './feature/background_Umap_top72.joblib')

# ML Configuration
MAX_BG_SAMPLES_PER_CLASS = int(os.getenv('MAX_BG_SAMPLES_PER_CLASS', '500'))

# CORS Configuration
CORS_ENABLED = os.getenv('CORS_ENABLED', 'true').lower() == 'true'
# Handle CORS origins - support both comma-separated list and wildcard
cors_origins_env = os.getenv('CORS_ALLOWED_ORIGINS', f'{FRONTEND_CLIENT},{DASHBOARD_CLIENT}')
if cors_origins_env == '*':
    CORS_ALLOWED_ORIGINS = ["*"]
else:
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
CORS_ALLOWED_METHODS = [method.strip() for method in os.getenv('CORS_ALLOWED_METHODS', 'GET,POST,PUT,DELETE,OPTIONS').split(',') if method.strip()]
CORS_ALLOWED_HEADERS = os.getenv('CORS_ALLOWED_HEADERS', '*')
CORS_EXPOSED_HEADERS = os.getenv('CORS_EXPOSED_HEADERS', '*')
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'
CORS_MAX_AGE = int(os.getenv('CORS_MAX_AGE', '3600'))

# Font Configuration
NOTOSANSTC_PATH_FRONT = os.getenv('NOTOSANSTC_PATH_FRONT', './fonts/NotoSansTC.ttf')
NOTOSANSTC_PATH = os.getenv('NOTOSANSTC_PATH', '../frontend/fonts/NotoSansTC.ttf')