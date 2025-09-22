from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import json
import numpy as np
import os
import sys
import base64
import qrcode
from io import BytesIO

module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(module_path)

from dashboard.utils.data_fetcher import DataFetcher
from utils.redis_utils import get_redis
from utils.ml_utils import ml_utils
from utils.game_logic import game_logic
from utils.plotting_api import plotting_api
import pandas as pd
from config import API_CLIENT, MAX_BG_SAMPLES_PER_CLASS

router = APIRouter()

# Global variables for models - loaded lazily
model = None
embed_model = None

def get_models():
    """Lazy loading of models to avoid loading on import"""
    global model, embed_model
    if model is None:
        print("[API] Loading models...")
        model, embed_model =  ml_utils.load_model()
        print(f"[API] Model loading completed. Model loaded: {model is not None}")
    return model, embed_model


class PlayerInfoRequest(BaseModel):
    player_name: str
    gender: str
    age: int
    difficulty: str

@router.post("/api/sessions")
async def create_session(player: PlayerInfoRequest):
    """Store Player's info and Create a new game session and store in Redis"""
    session_id = datetime.now().strftime("%Y%m%d%H%M%S") + os.urandom(4).hex()
    game_data = game_logic.build_rounds(player.difficulty)
    r = get_redis()
    session_data = {
        "session_id": session_id,
        "player_name": player.player_name,
        "timestamp": datetime.now().isoformat(),
        "age": player.age,
        "gender": player.gender,
        "difficulty": player.difficulty,
        "prompts": json.dumps(game_data["prompts"]),
        "rounds": json.dumps(game_data["rounds"]),
    }

    r.hset(f"session:{session_id}", mapping=session_data)
    return {
        "session_id": session_id,
        "rounds": game_data["rounds"],
        "prompts": game_data["prompts"]
    }

class PredictRealtimeRequest(BaseModel):
    image_data: str
    choices: List[str] = []
    
@router.post("/api/predict-realtime")
async def predict_realtime(data: PredictRealtimeRequest):
    """Predict class probabilities for a given image in real-time (not stored)"""
    model, embed_model = get_models()
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    try:
        image_data = data.image_data
        round_choices = data.choices
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        import base64
        image_bytes = base64.b64decode(image_data)
        processed_image = ml_utils.process_image_to_model_input(image_bytes)
        input_tensor = np.expand_dims(processed_image, axis=0)
        predictions = model.predict(input_tensor, verbose=0).squeeze()
        if round_choices:
            probs_map = {choice: float(predictions[ml_utils.classes.index(choice)]) for choice in round_choices if choice in ml_utils.classes}
            total_prob = sum(probs_map.values())
            if total_prob > 0:
                for choice in probs_map:
                    probs_map[choice] /= total_prob
        else:
            probs_map = {class_name: float(predictions[i]) for i, class_name in enumerate(ml_utils.classes)}
        return {"predictions": probs_map, "success": True}
    except Exception as e:
        return {"predictions": {}, "success": False, "error": str(e)}


class PredictRequest(BaseModel):
    session_id: str
    round: int
    prompt: str
    time_spent_sec: float
    timed_out: int
    drawing: str  # base64 encoded image data using 28*28
    original_image_data: str  # base64 encoded image data using original size

@router.post("/api/predict")
async def predict_drawing(data: PredictRequest):
    """Predict class probabilities for a given drawing for each round, store results and embedding in Redis"""
    model, embed_model = get_models()
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    try:
        r = get_redis()
        session_data = r.hgetall(f"session:{data.session_id}")
        round_choices = []
        if session_data and "rounds" in session_data:
            rounds = json.loads(session_data["rounds"])
            if data.round <= len(rounds):
                round_choices = rounds[data.round - 1]  # rounds are 1-indexed
        
        image_base64 = data.drawing
        original_image_base64 = data.original_image_data
        
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        if original_image_base64.startswith('data:image'):
            original_image_base64 = original_image_base64.split(',')[1]
        
        image_data = base64.b64decode(image_base64)
        original_image_data = base64.b64decode(original_image_base64)

        # Use the same image processing logic as predict-realtime
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Process image using the same method as predict-realtime
        processed_image = ml_utils.process_image_to_model_input(image_data)
        input_tensor = np.expand_dims(processed_image, axis=0)
        predictions = model.predict(input_tensor, verbose=0).squeeze()
        
        # Use identical prediction filtering logic as predict-realtime
        if round_choices:
            probs_map = {choice: float(predictions[ml_utils.classes.index(choice)]) for choice in round_choices if choice in ml_utils.classes}
            total_prob = sum(probs_map.values())
            if total_prob > 0:
                for choice in probs_map:
                    probs_map[choice] /= total_prob
        else:
            probs_map = {class_name: float(predictions[i]) for i, class_name in enumerate(ml_utils.classes)}
        
        # Generate embeddings (this is unique to predict endpoint)
        embedding = []
        if embed_model:
            try:
                embed_output = embed_model.predict(input_tensor, verbose=0)
                embedding = embed_output.flatten().tolist()
            except Exception as e:
                print(f"Error getting embedding: {e}")
        
        # calculate score for this round
        correct_prob = probs_map.get(data.prompt, 0.0)
        # Store data in Redis (unique to predict endpoint)
        drawing_id = f"drawing:{data.session_id}:{data.round}"
        drawing_data = {
            "session_id": data.session_id,
            "round": data.round,
            "prompt": data.prompt,
            "time_spent_sec": data.time_spent_sec,
            "timed_out": data.timed_out,
            "image_base64": image_base64,
            "predictions": json.dumps(probs_map),
            "round_choices": json.dumps(round_choices),
            "embedding": json.dumps(embedding),
            "timestamp": datetime.now().isoformat(),
            "original_image_data": original_image_base64,  # Store original image data for visualization
            "corr_prob": correct_prob  # Store score for this round
        }
        r.hset(drawing_id, mapping=drawing_data)
        r.lpush(f"session:{data.session_id}:drawings", drawing_id)
        
        # Return response in same format as predict-realtime (with additional embedding)
        return {
            "predictions": probs_map, "embedding": embedding, "success": True
        }
        
    except Exception as e:
        # Use same error handling pattern as predict-realtime
        return {
            "predictions": {}, "embedding": [], "success": False, "error": str(e)
        }

@router.get("/api/session/{session_id}")
async def get_results(session_id: str):
    """Get session info and all drawings for a given session ID"""
    r = get_redis()
    session_data = r.hgetall(f"session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data["rounds"] = json.loads(session_data.get("rounds", "[]"))
    session_data["prompts"] = json.loads(session_data.get("prompts", "[]"))
    return {"session": session_data}

@router.get("/api/drawing/{session_id}")
async def get_drawing(session_id: str):
    """Get all drawings for a given session ID"""
    r = get_redis()
    drawing_ids = r.lrange(f"session:{session_id}:drawings", 0, -1)
    drawings = []
    for drawing_id in drawing_ids:
        drawing_data = r.hgetall(drawing_id)
        if drawing_data:
            drawing_data["predictions"] = json.loads(drawing_data.get("predictions", "{}"))
            drawing_data["embedding"] = json.loads(drawing_data.get("embedding", "[]"))
            drawing_data["round"] = int(drawing_data.get("round", 0))
            drawing_data["time_spent_sec"] = float(drawing_data.get("time_spent_sec", 0))
            drawing_data["timed_out"] = int(drawing_data.get("timed_out", 0))
            drawings.append(drawing_data)
    drawings.sort(key=lambda x: x["round"])
    return {"drawing": drawings}

@router.get("/api/umap/{session_id}")
async def generate_umap_visualization(session_id: str):
    """Generate UMAP visualization for a session's embeddings and store in Redis"""
    try:
        r = get_redis()
        
        # Check if already exists in Redis
        redis_key = f"umap_plot:{session_id}"
        existing_plot = plotting_api.get_plot_from_redis(redis_key)
        if existing_plot:
            metadata = plotting_api.get_metadata_from_redis(f"umap_metadata:{session_id}")
            return {
                "status": "success",
                "image_base64": existing_plot,
                "from_cache": True,
                "metadata": metadata
            }
        
        # Get all drawing IDs for this session
        drawing_ids = r.lrange(f"session:{session_id}:drawings", 0, -1)
        if not drawing_ids:
            raise HTTPException(status_code=404, detail="No drawings found for this session")

        # Collect embeddings and prompts
        embeddings_data = []
        for drawing_id in drawing_ids:
            drawing_data = r.hgetall(drawing_id)
            if drawing_data and "embedding" in drawing_data and "prompt" in drawing_data:
                emb = json.loads(drawing_data.get("embedding", "[]"))
                if emb:  # Only add non-empty embeddings
                    prompt = drawing_data.get("prompt", "unknown")
                    row_data = {"prompt": prompt}
                    # Add embedding features
                    for i, val in enumerate(emb):
                        row_data[f"emb_{i}"] = val
                    embeddings_data.append(row_data)

        if not embeddings_data:
            raise HTTPException(status_code=404, detail="No embeddings found for this session")
        
        # Create DataFrame for the new API
        user_embedding_df = pd.DataFrame(embeddings_data)
        
        # Generate UMAP visualization using new plotting API
        result = plotting_api.create_umap_plot(
            user_embedding_df=user_embedding_df,
            session_id=session_id,
            max_background_samples_per_class=MAX_BG_SAMPLES_PER_CLASS,  # 500 samples per class
            figsize=(10, 7),
            user_marker="^",
            user_color="black",
            user_size=120,
            annotate=True
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "image_base64": result["image_base64"],
                "redis_key": result["redis_key"],
                "embeddings_count": len(embeddings_data),
                "skipped_classes": result["skipped_classes"],
                "background_samples_per_class": result["background_samples_per_class"],
                "from_cache": False
            }
        else:
            raise HTTPException(status_code=500, detail=f"UMAP generation failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Error generating UMAP visualization: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating UMAP visualization: {str(e)}")

@router.get("/api/radar/{session_id}")
async def generate_radar_chart(session_id: str):
    """Generate radar chart for a session and store in Redis"""
    try:
        r = get_redis()
        
        # Check if already exists in Redis
        redis_key = f"radar_plot:{session_id}"
        existing_plot = plotting_api.get_plot_from_redis(redis_key)
        if existing_plot:
            metadata = plotting_api.get_metadata_from_redis(f"radar_metadata:{session_id}")
            return {
                "status": "success", 
                "image_base64": existing_plot,
                "from_cache": True,
                "metadata": metadata
            }
        
        # Get session data
        session_data = r.hgetall(f"session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Get all drawings for this session
        drawing_ids = r.lrange(f"session:{session_id}:drawings", 0, -1)
        if not drawing_ids:
            raise HTTPException(status_code=404, detail="No drawings found for this session")
        
        # Collect drawing data
        session_drawings = []
        for drawing_id in drawing_ids:
            drawing_data = r.hgetall(drawing_id)
            if drawing_data:
                prompt = drawing_data.get("prompt", "")
                predictions_str = drawing_data.get("predictions", "{}")
                
                try:
                    predictions = json.loads(predictions_str) if predictions_str else {}
                except json.JSONDecodeError:
                    print(f"Error parsing predictions for {drawing_id}: {predictions_str}")
                    continue
                
                session_drawings.append({
                    "prompt": prompt,
                    "predictions": predictions
                })
        
        if not session_drawings:
            raise HTTPException(status_code=404, detail="No valid drawing data found")
        
        # Generate radar chart using new plotting API
        result = plotting_api.create_radar_plot(
            session_drawings=session_drawings,
            session_id=session_id
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "image_base64": result["image_base64"],
                "redis_key": result["redis_key"],
                "prompts": result["prompts"],
                "probabilities": result["probabilities"],
                "drawings_count": len(session_drawings),
                "from_cache": False
            }
        else:
            raise HTTPException(status_code=500, detail=f"Radar chart generation failed: {result.get('error', 'Unknown error')}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating radar chart: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating radar chart: {str(e)}")

@router.get("/api/plots/{session_id}")
async def generate_both_plots(session_id: str):
    """Generate both UMAP and radar charts a the same time by calling existing endpoints"""
    try:
        # Call existing UMAP and radar endpoints
        umap_result = await generate_umap_visualization(session_id)
        radar_result = await generate_radar_chart(session_id)
        
        return {
            "status": "success",
            "umap": umap_result,
            "radar": radar_result,
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating plots: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating plots: {str(e)}")

@router.get("/api/health")
async def health_check():
    """Health check endpoint to verify API and model status"""
    model, embed_model = get_models()
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "embed_model_loaded": embed_model is not None,
        "classes_count": len(ml_utils.classes)
    }

@router.get("/api/qr-code/{session_id}")
async def get_qr_code(session_id: str):
    """Check if QR code already exists for a session and return the QR code image"""
    try:
        r = get_redis()
        qr_data = r.hgetall(f"qr_code:{session_id}")
        
        if not qr_data:
            return {
                "status": "not_found",
                "message": "QR code not found for this session"
            }
        
        return {
            "status": "exists",
            "qr_image_base64": qr_data["qr_image_base64"],
            "shareable_url": qr_data["shareable_url"],
            "created_at": qr_data["created_at"],
            "session_id": session_id,
            "player_name": qr_data["player_name"]
        }
        
    except Exception as e:
        print(f"Error checking QR code: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking QR code: {str(e)}")


class QRCodeRequest(BaseModel):
    session_id: str
    player_name: str
    shareable_url: str

@router.post("/api/generate-qr-code")
async def generate_qr_code(data: QRCodeRequest):
    """ Generate QR code image and store in Redis database"""
    try:
        r = get_redis()
        
        # Check if QR code already exists for this session
        existing_qr = r.hgetall(f"qr_code:{data.session_id}")
        if existing_qr:
            qr_info = {key.decode(): value.decode() for key, value in existing_qr.items()}
            return {
                "status": "success",
                "qr_image_base64": qr_info["qr_image_base64"],
                "shareable_url": qr_info["shareable_url"],
                "message": "QR code already exists in database",
                "from_cache": True,
                "created_at": qr_info["created_at"]
            }
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(data.shareable_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        current_time = datetime.now().isoformat()
            
        # Store QR code in Redis
        qr_code_data = {
            "session_id": data.session_id,
            "player_name": data.player_name,
            "shareable_url": data.shareable_url,
            "qr_image_base64": qr_image_base64,
            "created_at": current_time
        }
        r.hset(f"qr_code:{data.session_id}", mapping=qr_code_data)
        
        return {
            "status": "success",
            "qr_image_base64": qr_image_base64,
            "shareable_url": data.shareable_url,
            "message": "QR code generated and stored in database",
            "from_cache": False,
            "created_at": current_time
        }
        
    except Exception as e:
        print(f"Error generating QR code: {e}")
        raise HTTPException(status_code=500, detail=f"QR code generation failed: {str(e)}")


class QRCodeRequest(BaseModel):
    screenshot: str
    session_id: str
    player_name: str

@router.post("/api/upload-screenshot")
async def upload_screenshot(data: QRCodeRequest):
    """
    Upload a screenshot (passed as base64 string) and return a shareable URL for QR code generation.
    Screenshot is saved as a file for download functionality.
    """
    try:

        # Validate base64 string
        if not data.screenshot or not isinstance(data.screenshot, str):
            raise HTTPException(status_code=400, detail="Screenshot must be a base64-encoded string")

        # Remove data URL prefix if present
        if data.screenshot.startswith('data:image'):
            base64_data = data.screenshot.split(',')[1]
        else:
            base64_data = data.screenshot

        try:
            image_bytes = base64.b64decode(base64_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")

        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads/screenshots"
        os.makedirs(uploads_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = "png"  # Default to png
        safe_player_name = "".join(c for c in data.player_name if c.isalnum() or c in ('-', '_'))
        filename = f"quickdraw_{safe_player_name}_{data.session_id}_{timestamp}.{file_extension}"

        # Save file
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # Generate shareable URL
        shareable_url = f"http://{API_CLIENT}/api/download-screenshot/{filename}"

        current_time = datetime.now().isoformat()

        # Store screenshot metadata in Redis
        r = get_redis()
        screenshot_data = {
            "filename": filename,
            "session_id": data.session_id,
            "player_name": data.player_name,
            "upload_time": current_time,
            "file_size": len(image_bytes),
            "shareable_url": shareable_url
        }
        r.hset(f"screenshot:{filename}", mapping=screenshot_data)

        return {
            "status": "success",
            "filename": filename,
            "shareableUrl": shareable_url,
            "message": "Screenshot uploaded successfully",
            "created_at": current_time
        }

    except Exception as e:
        print(f"Error uploading screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/api/download-screenshot/{filename}")
async def download_screenshot(filename: str):
    """
    Download a screenshot by filename
    """
    try:
        file_path = os.path.join("uploads/screenshots", filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Screenshot not found")
        
        # Return file for download
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='image/png'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/api/screenshot-info/{filename}")
async def get_screenshot_info(filename: str):
    """
    Get metadata about a screenshot
    """
    try:
        r = get_redis()
        screenshot_data = r.hgetall(f"screenshot:{filename}")
        
        if not screenshot_data:
            raise HTTPException(status_code=404, detail="Screenshot metadata not found")
        
        # Convert bytes to strings for JSON serialization
        return {key.decode(): value.decode() for key, value in screenshot_data.items()}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting screenshot info: {e}")
        raise HTTPException(status_code=500, detail=f"Info retrieval failed: {str(e)}")




@router.get("/api/leaderboard") #TODO
async def get_leaderboard(difficulty: str = None):
    """Get leaderboard data"""
    try:
        r = get_redis()
        
        # Get all session keys
        session_keys = r.keys("session:*")
        
        # Collect all sessions with scores
        sessions = []
        for key in session_keys:
            session_data = r.hgetall(key)
            if session_data:
                # Decode byte strings
                session = {k.decode(): v.decode() for k, v in session_data.items()}
                
                # Filter by difficulty if specified
                if difficulty and session.get('difficulty') != difficulty:
                    continue
                
                # Calculate a simple score (this could be more sophisticated)
                # For now, just use timestamp as a placeholder
                session['score'] = session.get('timestamp', '0')
                sessions.append(session)
        
        # Sort by timestamp (most recent first) - replace with actual scoring logic
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit results
        # sessions = sessions[:limit]
        
        return {
            "leaderboard": sessions,
            "total_players": len(sessions),
            "difficulty_filter": difficulty
        }
        
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Leaderboard retrieval failed: {str(e)}")


@router.get("/api/dashboard/stats")
async def get_dashboard_stats(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    hours: Optional[int] = Query(None, description="Filter by last N hours"),
    # limit: Optional[int] = Query(100, description="Limit number of results")
):
    """
    Get overall dashboard statistics
    """
    try:
        r = get_redis()
        # Get all session keys
        session_keys = r.keys("session:*")
        sessions = []
        
        # Filter sessions based on criteria
        cutoff_time = None
        if hours:
            cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for key in session_keys:
            if ":drawings" not in key and ":qr_code" not in key:
                session_data = r.hgetall(key)
                if session_data:
                    # Filter by difficulty
                    if difficulty and session_data.get('difficulty') != difficulty:
                        continue
                    
                    # Filter by time
                    if cutoff_time:
                        timestamp_str = session_data.get('timestamp', '')
                        if timestamp_str:
                            try:
                                session_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                if session_time.replace(tzinfo=None) < cutoff_time:
                                    continue
                            except:
                                continue
                    
                    sessions.append(session_data)
        
        # Calculate statistics
        total_players = len(sessions)
        difficulty_counts = {}
        total_games = 0
        
        for session in sessions:
            diff = session.get('difficulty', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
            # Count games for this session
            session_id = session.get('session_id')
            if session_id:
                drawing_count = r.llen(f"session:{session_id}:drawings")
                total_games += drawing_count
        
        return {
            "total_players": total_players,
            "total_games": total_games,
            "difficulty_distribution": difficulty_counts,
            "period_description": f"Last {hours} hours" if hours else "All time"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")

@router.get("/api/dashboard/rankings")
async def get_rankings(
    difficulty: str = Query(..., description="Difficulty level (easy/hard)"),
    # limit: Optional[int] = Query(50, description="Number of top players to return")
):
    """
    Get player rankings for a specific difficulty
    """
    try:
        r = get_redis()
        data_fetcher = DataFetcher()
        
        # Get all sessions for this difficulty
        sessions = data_fetcher.get_all_sessions()
        filtered_sessions = [s for s in sessions if s.get('difficulty') == difficulty]
        
        # Calculate rankings
        rankings = []
        for session in filtered_sessions:
            drawings = session.get('drawings', [])
            total_score = data_fetcher.calculate_session_score(drawings)
            
            rankings.append({
                'player_name': session.get('player_name', 'Unknown'),
                'total_score': total_score,
                'games_played': len(drawings),
                'timestamp': session.get('timestamp', ''),
                'session_id': session.get('session_id', ''),
                'age': session.get('age', 0),
                'gender': session.get('gender', 'Unknown')
            })
        
        # Sort by score and limit
        rankings.sort(key=lambda x: x['total_score'], reverse=True)
        # top_rankings = rankings[:limit] if limit else rankings
        
        return {
            "difficulty": difficulty,
            "total_players": len(rankings),
            "rankings": rankings
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rankings retrieval failed: {str(e)}")

@router.get("/api/dashboard/score-distribution")
async def get_score_distribution(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    bins: Optional[int] = Query(20, description="Number of histogram bins")
):
    """
    Get score distribution data for histogram visualization
    """
    try:

        data_fetcher = DataFetcher()
        sessions = data_fetcher.get_all_sessions()
        
        if difficulty:
            sessions = [s for s in sessions if s.get('difficulty') == difficulty]
        
        # Calculate scores
        scores_by_difficulty = {'easy': [], 'hard': []}
        
        for session in sessions:
            session_difficulty = session.get('difficulty', 'easy')
            score = session.get('total_score', 0)
            if session_difficulty in scores_by_difficulty:
                scores_by_difficulty[session_difficulty].append(score)
        
        # Create histogram data
        histogram_data = {}
        
        for diff, scores in scores_by_difficulty.items():
            if scores:
                import numpy as np

                hist, bin_edges = np.histogram(scores, bins=bins)
                histogram_data[diff] = {
                    'counts': hist.tolist(),
                    'bin_edges': bin_edges.tolist(),
                    'statistics': {
                        'mean': float(np.mean(scores)),
                        'median': float(np.median(scores)),
                        'std': float(np.std(scores)),
                        'min': float(np.min(scores)),
                        'max': float(np.max(scores)),
                        'total_players': len(scores)
                    }
                }
        
        return {
            "histogram_data": histogram_data,
            "filter_applied": difficulty if difficulty else "all_difficulties"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Score distribution retrieval failed: {str(e)}")

@router.get("/api/dashboard/recent-activity")
async def get_recent_activity(
    limit: Optional[int] = Query(20, description="Number of recent sessions to return")
):
    """
    Get recent game activity
    """
    try:

        data_fetcher = DataFetcher()
        sessions = data_fetcher.get_all_sessions()
        
        # Sort by timestamp (most recent first)
        sessions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent_sessions = sessions[:limit] if limit else sessions
        
        # Format for dashboard consumption
        activity_data = []
        for session in recent_sessions:
            activity_data.append({
                'player_name': session.get('player_name', 'Unknown'),
                'difficulty': session.get('difficulty', 'unknown'),
                'total_score': session.get('total_score', 0),
                'games_played': len(session.get('drawings', [])),
                'timestamp': session.get('timestamp', ''),
                'age': session.get('age', 0),
                'gender': session.get('gender', 'Unknown')
            })
        
        return {
            "recent_activity": activity_data,
            "total_sessions": len(sessions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recent activity retrieval failed: {str(e)}")
