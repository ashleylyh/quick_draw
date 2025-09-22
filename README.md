
# Quick Draw — AI Drawing Duel


A lightweight web app for a Quick, Draw! AI drawing duel. Frontend lets players draw sketches and the backend returns model predictions, embeddings, and visualizations (UMAP / radar). This README explains setup, how to run the project, and documents the main backend API and data layout.

## Prerequisites
- Python 3.12 (pyproject specifies 3.12.3)
- Redis server
- Recommended: Create a virtual environment using uv for Python

## Clone the Repository
```bash
git clone https://github.com/ashleylyh/quick_draw.git
cd quick_draw
```

## Install Python dependencies
The project uses `pyproject.toml` with optional dashboard dependencies. Using UV to install dependencies:

**Basic installation:**
```bash
uv sync
source .venv/bin/activate  # Activate virtual environment

deactivate # exit a virtual env
```

**With dashboard (analytics) features:**
```bash
uv sync --extra dashboard
```

Or use the setup script:
```bash
./setup-dashboard.sh
```

## Install Redis
For redis database installation, please refer to this document:

https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/

---

## Quick start (development)
Open terminals (remember to activate virtual environment with `source .venv/bin/activate`)

1) Start Redis (default port 6379)

```bash
redis-server
```

2) Start backend API (serves on localhost port 8000), for API docs: http://localhost:8000/docs#/
```bash
# from project root
uv run uvicorn backend.app:app --host 0.0.0.0 --port 8000
# or manually: cd backend && python app.py
```

3) Serve frontend (static files) — simple Python HTTP server

```bash
cd frontend
python -m http.server 3000
# then open http://localhost:3000 in a browser
```

4) **NEW**: Analytics Dashboard (optional)

```bash
cd dashboard
./run.sh
# then open http://localhost:8501 in a browser
```

> Tip: If you get CORS issues in production, restrict `allow_origins` in `backend/app.py` instead of `"*"`.
```bash
sudo kill -9 $(sudo lsof -t -i:8080)
```

---

## Features

### 🎨 Core Game
- **Drawing Interface**: HTML5 Canvas-based drawing with real-time AI predictions
- **Multiple Difficulties**: Easy, Medium, Hard modes with different class sets
- **ML Predictions**: TensorFlow-based doodle classification
- **Visual Analytics**: UMAP embeddings and radar charts for drawing analysis

### 📊 Analytics Dashboard (NEW)
- **Player Rankings**: Leaderboards by difficulty level with podium displays
- **Score Analysis**: Distribution histograms and statistical analysis
- **Real-time Metrics**: Live dashboard with player statistics and recent activity
- **Interactive Visualizations**: Plotly-powered charts with filtering and time ranges

### 🔧 Technical Features
- **FastAPI Backend**: RESTful API with automatic documentation
- **Redis Storage**: Session management and caching
- **Streamlit Dashboard**: Interactive analytics interface
- **QR Code Sharing**: Share game results easily

---

## Project layout (important files)
- `backend/` — FastAPI backend and ML helpers
    - `app.py` — FastAPI app entrypoint
    - `api.py` — REST endpoints (sessions, predict, umap, radar, qr, uploads)
    - `ml_utils.py` — model loading and preprocessing utilities
    - `plotting_api.py` — UMAP / radar plotting helpers and Redis caching
    - `redis_utils.py` — Redis connection helper
    - `game_logic.py` — building rounds and prompts
- `frontend/` — static site (HTML/CSS/JS)
    - `index.html` — landing / game pages
    - `score.html` — results page (UMAP, radar, drawings)
    - `sketch.js`, `score.js` — frontend logic
    - `score_style.css`, `sketch_style.css` — styles
- `dashboard/` — **NEW**: Streamlit analytics dashboard
    - `app.py` — main dashboard application
    - `components/` — ranking and histogram components
    - `utils/` — data fetching and processing utilities
    - `run.sh` / `run.bat` — startup scripts
- `model/` — pretrained model artifacts (may contain `doodleNet-model.keras`)
- `feature/`— background embeddings and cached datasets
---
## UMAP model file
please download the umap joblib file via:\
https://drive.google.com/file/d/15NLciurQcZmeL0ToH-XFJCODLTK8Z8aG/view?usp=sharing

---

## Credits & Acknowledgements
- Dataset: Google Quick, Draw! Dataset
- Model inspiration / original repo: https://github.com/yining1023/doodleNet


