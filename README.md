
# QuickDraw — AI Drawing Duel 🎨

A comprehensive web application for a Quick, Draw! AI drawing duel featuring real-time ML predictions, interactive analytics dashboard, and engaging gameplay. Players draw sketches that are classified by a TensorFlow model, with detailed visualizations including UMAP embeddings and radar charts.

## ✨ Features

### 🎮 Core Game
- **Interactive Drawing Interface**: HTML5 Canvas-based drawing with real-time AI predictions
- **Multiple Difficulty Levels**: Easy, Medium, Hard modes with different class sets
- **Smart ML Predictions**: TensorFlow-powered doodle classification with confidence scoring
- **Visual Analytics**: UMAP embeddings and radar charts for drawing analysis
- **QR Code Sharing**: Instantly share game results

### 📊 Analytics Dashboard
- **Player Rankings**: Dynamic leaderboards by difficulty with podium displays
- **Score Analysis**: Statistical distributions and performance metrics
- **Real-time Monitoring**: Live dashboard with player activity and session data
- **Interactive Visualizations**: Plotly-powered charts with filtering capabilities

### 🔧 Technical Stack
- **Backend**: FastAPI with automatic API documentation
- **Frontend**: Vanilla JavaScript with HTML5 Canvas
- **Dashboard**: Streamlit-powered analytics interface
- **Database**: Redis for session management and caching
- **ML**: TensorFlow/Keras for doodle classification
- **Visualization**: UMAP, Plotly, and custom radar charts

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (project specifies 3.12.3)
- Redis server running
- UV package manager (recommended) or pip

### 1. Clone the Repository
```bash
git clone https://github.com/ashleylyh/quick_draw.git
cd quick_draw
```

### 2. Install Dependencies
The project uses `pyproject.toml` with optional dashboard dependencies:

**Using UV (recommended):**
```bash
# Basic installation
uv sync

# With dashboard analytics features
uv sync --extra dashboard

# Activate virtual environment
source .venv/bin/activate
# remember to activate virtual env for every terminal
```

**Using pip:**
```bash
pip install -e .
# For dashboard features: pip install -e .[dashboard]
```

### 3. Install and Start Redis
Redis is required for session management and caching:

```bash
# Ubuntu/Debian
sudo apt install redis-server
redis-server

# macOS
brew install redis
redis-server
```

### 4. Download Required Models
Download the UMAP model file:
- [UMAP Background Model](https://drive.google.com/file/d/15NLciurQcZmeL0ToH-XFJCODLTK8Z8aG/view?usp=sharing)
- Place in `backend/feature/` directory

## 🎯 Running the Application

### 🐳 Docker Deployment (Recommended)
For the easiest setup, use Docker to run all services:

```bash
# One-command start (builds and runs everything)
./docker-start.sh

# Stop all services
./docker-stop.sh
```

**Docker Requirements:**
- Docker and Docker Compose installed
- Ports 3000, 6379, 8000, 8501 available

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for detailed Docker instructions.

### 💻 Local Development

### Option 1: All Services at Once (Recommended)
```bash
# Start all services (backend, frontend, dashboard) in one terminal
scripts/start-all.sh
```

### Option 2: Separate Terminals for Each Service
```bash
# Opens each service in its own terminal tab/window
scripts/start-separate.sh
```

### Option 3: Individual Services
```bash
# Start services individually
scripts/start-backend.sh    # Backend API (port 8000)
scripts/start-frontend.sh   # Frontend (port 3000)
scripts/start-dashboard.sh  # Dashboard (port 8501)
```
### Option 4: Individual Services Manually
```bash
# Start services individually
redis-server
cd frontend && python -m http.server 3000
cd backend && python app.py
cd dashboard && streamlit run app.py
```

### Stop All Services
```bash
scripts/stop-all.sh
```

## ⚙️ Environment Configuration

The application uses environment variables for configuration. Copy `.env.example` to `.env` and customize as needed:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration
nano .env
```

Key environment variables:
- `FRONTEND_PORT` - Frontend server port (default: 3000)
- `BACKEND_PORT` - Backend API port (default: 8000)
- `DASHBOARD_PORT` - Dashboard port (default: 8501)
- `REDIS_HOST` - Redis host (default: localhost)
- `REDIS_PORT` - Redis port (default: 6379)

## 🌐 Access URLs
Once running, access the application at:
- **🎮 Game Interface**: http://localhost:3000
- **📡 Backend API**: http://localhost:8000
- **📚 API Documentation**: http://localhost:8000/docs
- **📊 Analytics Dashboard**: http://localhost:8501

## 💡 Development Tips

### Port Conflicts
If ports are occupied:
```bash
# Check what's using a port
lsof -i :8000

# Kill processes by port
sudo kill -9 $(sudo lsof -t -i:8000)

# Or use the stop script
scripts/stop-all.sh
```

### Logs and Debugging
When using `scripts/start-all.sh`, logs are saved to:
- `logs/backend.log` - Backend API logs
- `logs/frontend.log` - Frontend server logs
- `logs/dashboard.log` - Dashboard logs


## 📁 Project Structure

```
quickdraw/
├── 🚀 Docker Scripts
│   ├── docker-start.sh       # Start all services with Docker
│   ├── docker-stop.sh        # Stop Docker services
│   ├── docker-build.sh       # Build Docker images
│   └── docker-compose.yml    # Docker Compose configuration
│
├── 📂 scripts/              # Development Scripts
│   ├── start-all.sh          # Start all services together
│   ├── start-separate.sh     # Start each service in separate terminals
│   ├── start-backend.sh      # Backend only
│   ├── start-frontend.sh     # Frontend only
│   ├── start-dashboard.sh    # Dashboard only
│   └── stop-all.sh          # Stop all services
│
├── 📡 backend/              # FastAPI Backend
│   ├── app.py               # Main FastAPI application
│   ├── api.py               # Game API endpoints
│   ├── dashboard_api.py     # Dashboard API endpoints
│   ├── realtime.py          # WebSocket and SSE handlers
│   ├── model/               # ML model files
│   │   ├── doodleNet-model.keras
│   │   └── class_names.txt
│   ├── feature/             # UMAP and background embeddings
│   │   ├── background_Umap_top72.joblib
│   │   └── background_embedding_5per_class.csv
│   └── utils/               # Utility modules
│       ├── game_logic.py
│       ├── ml_utils.py
│       ├── plot_utils.py
│       └── redis_utils.py
│
├── 🌐 frontend/             # Game Interface
│   ├── index.html           # Main game page
│   ├── score.html           # Results visualization
│   ├── sketch.js            # Drawing logic
│   ├── score.js             # Results display
│   └── assets/              # Images and fonts
│
├── 📊 dashboard/            # Analytics Dashboard
│   ├── app.py               # Streamlit application
│   ├── components/          # Dashboard components
│   │   ├── overview_tab.py
│   │   ├── rankings_tab.py
│   │   └── score_analysis_tab.py
│   ├── controllers/         # Business logic
│   └── utils/               # Data processing
│
├── 📋 Configuration & Environment
│   ├── pyproject.toml       # Project dependencies
│   ├── config.py            # Shared configuration
│   ├── uv.lock              # Dependency lock file
│   ├── .env.example         # Environment variables template
│   ├── .env                 # Environment configuration (local)
│   └── .dockerignore        # Docker ignore patterns
│
└── 📝 Documentation
    ├── README.md            # This file
    └── STARTUP_SCRIPTS.md   # Detailed script documentation
```



## 🎮 Game Modes & Difficulty Levels

### Difficulty Levels
- **Easy**: 10 common drawing categories (e.g., cat, car, house)
- **Medium**: 25 categories with moderate complexity
- **Hard**: 72+ categories including abstract concepts

### Scoring System
- Base score calculated from prediction confidence
- Time bonus for quick correct guesses
- Difficulty multiplier applied
- Leaderboard rankings by difficulty level

## 🔧 API Endpoints

### Core Game API (`/api/`)
- `POST /sessions` - Create new game session
- `POST /predict` - Submit drawing for AI prediction
- `GET /umap` - Generate UMAP visualization
- `GET /radar` - Generate radar chart analysis
- `POST /qr` - Generate QR code for sharing

### Dashboard API (`/dashboard/`)
- `GET /stats` - Overall game statistics
- `GET /rankings` - Player leaderboards
- `GET /scores` - Score distributions
- `GET /sessions` - Recent game sessions

### Real-time Features
- WebSocket endpoints for live updates
- Server-Sent Events (SSE) for dashboard streaming

## 🧠 Machine Learning Pipeline

### Model Architecture
- **Base Model**: Custom CNN trained on Google Quick, Draw! dataset
- **Classes**: 345 drawing categories with hierarchical difficulty
- **Input**: 28x28 grayscale images from canvas drawings
- **Output**: Confidence scores for all categories

### Visualization Features
- **UMAP Embeddings**: 2D projection of drawing features
- **Radar Charts**: Multi-dimensional analysis of drawing characteristics
- **Background Dataset**: 5 samples per class for comparison context



## 🚀 Production Deployment

### Environment Variables
```bash
# Backend Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
FRONTEND_CLIENT=http://localhost:3000
DASHBOARD_CLIENT=http://localhost:8501

# Dashboard Configuration  
BACKEND_API_URL=http://localhost:8000
```

## 📄 License



## 🙏 Credits & Acknowledgements

- **Dataset**: [Google Quick, Draw! Dataset](https://quickdraw.withgoogle.com/data)
- **Model Inspiration**: [doodleNet by yining1023](https://github.com/yining1023/doodleNet)
- **Usage**: This project is developed for Academia Sinica 2025 Open House Activity.

---

**🎨 Ready to start drawing? Run `./start-all.sh` and visit http://localhost:3000!**


