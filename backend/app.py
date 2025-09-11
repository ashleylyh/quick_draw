# app.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import tensorflow as tf
import numpy as np
import uuid
import os
import json
from datetime import datetime
import redis
import uvicorn
from PIL import Image
import io
import random
import keras

from api import router
from ml_utils import load_model

model = None
embed_model = None

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup code
#     print("[Startup] System Start")
#     yield
#     # Shutdown code (if any)
#     print("[Shutdown] System End")

# app = FastAPI(title="QuickDraw API", lifespan=lifespan)

app = FastAPI(title="QuickDraw API")
app.include_router(router)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# async def startup_event():
#     """Load models on startup"""
#     print("[Startup] System Start")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
