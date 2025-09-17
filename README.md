
# Quick Draw — AI Drawing Duel

A lightweight web app for a Quick, Draw!-style AI drawing duel. Frontend lets players draw sketches and the backend returns model predictions, embeddings, and visualizations (UMAP / radar). This README explains setup, how to run the project, and documents the main backend API and data layout.

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
The project uses `pyproject.toml`. Using UV to install dependencies into your environment:

```bash
uv sync
source .venv/bin/activate

deactivate # exit a virtual env
```

## Install Redis
For redis database installation, please refer to this document:

https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/

---

## Quick start (development)
Open three terminals (remember to activate vitrual env)

1) Start Redis (default port 6379)

```bash
redis-server
```

2) Start backend API (it serves on localhost port 8000), for API docs, access through http://localhost:8000/docs#/
```bash
# from project root
cd backend
python app.py
```

3) Serve frontend (static files) — simple Python HTTP server

```bash
cd frontend
python -m http.server 3000
# then open http://localhost:3000 in a browser
```

> Tip: If you get CORS issues in production, restrict `allow_origins` in `backend/app.py` instead of `"*"`.

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


