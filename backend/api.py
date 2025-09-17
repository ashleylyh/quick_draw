from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime
import json
import numpy as np
import os
import base64


# Import utility functions and global objects
from redis_utils import get_redis
from ml_utils import process_image_to_model_input, CLASSES, load_model
from game_logic import build_rounds
from plotting_api import plotting_api
import pandas as pd

router = APIRouter()

print("[API] Loading models...")
model, embed_model = load_model()
print(f"[API] Model loading completed. Model loaded: {model is not None}")


class PlayerInfo(BaseModel):
    player_name: str
    gender: str
    age: int
    difficulty: str

@router.post("/api/sessions")
async def create_session(player: PlayerInfo):
    session_id = datetime.now().strftime("%Y%m%d%H%M%S") + os.urandom(4).hex()
    game_data = build_rounds(player.difficulty)
    r = get_redis()
    session_data = {
        "player_name": player.player_name,
        "gender": player.gender,
        "age": player.age,
        "difficulty": player.difficulty,
        "rounds": json.dumps(game_data["rounds"]),
        "prompts": json.dumps(game_data["prompts"]),
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id
    }
    r.hset(f"session:{session_id}", mapping=session_data)
    # r.expire(f"session:{session_id}", 86400) # 1 day
    # 
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
        processed_image = process_image_to_model_input(image_bytes)
        input_tensor = np.expand_dims(processed_image, axis=0)
        predictions = model.predict(input_tensor, verbose=0).squeeze()
        if round_choices:
            probs_map = {choice: float(predictions[CLASSES.index(choice)]) for choice in round_choices if choice in CLASSES}
            total_prob = sum(probs_map.values())
            if total_prob > 0:
                for choice in probs_map:
                    probs_map[choice] /= total_prob
        else:
            probs_map = {class_name: float(predictions[i]) for i, class_name in enumerate(CLASSES)}
        return {"predictions": probs_map, "success": True}
    except Exception as e:
        return {"predictions": {}, "success": False, "error": str(e)}

@router.post("/api/predict")
async def predict_drawing(
    session_id: str = Form(...),
    round: int = Form(...),
    prompt: str = Form(...),
    time_spent_sec: float = Form(...),
    timed_out: int = Form(...),
    drawing: UploadFile = File(...),
    original_image_data: UploadFile = File(...),
):
    if not model:
        raise HTTPException(status_code=500, detail="Model not loaded")
    try:
        # Get session data to retrieve round choices
        r = get_redis()
        session_data = r.hgetall(f"session:{session_id}")
        round_choices = []
        if session_data and "rounds" in session_data:
            rounds = json.loads(session_data["rounds"])
            if round <= len(rounds):
                round_choices = rounds[round - 1]  # rounds are 1-indexed
        
        # Read and process image data (same as predict-realtime)
        image_data = await drawing.read()
        original_image_data = await original_image_data.read()
        
        # Convert to base64 for consistent processing with predict-realtime
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        original_image_base64 = base64.b64encode(original_image_data).decode('utf-8')


        # Use the same image processing logic as predict-realtime
        if not image_data:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Process image using the same method as predict-realtime
        processed_image = process_image_to_model_input(image_data)
        input_tensor = np.expand_dims(processed_image, axis=0)
        predictions = model.predict(input_tensor, verbose=0).squeeze()
        
        # Use identical prediction filtering logic as predict-realtime
        if round_choices:
            probs_map = {choice: float(predictions[CLASSES.index(choice)]) for choice in round_choices if choice in CLASSES}
            total_prob = sum(probs_map.values())
            if total_prob > 0:
                for choice in probs_map:
                    probs_map[choice] /= total_prob
        else:
            probs_map = {class_name: float(predictions[i]) for i, class_name in enumerate(CLASSES)}
        
        # Generate embeddings (this is unique to predict endpoint)
        embedding = []
        if embed_model:
            try:
                embed_output = embed_model.predict(input_tensor, verbose=0)
                embedding = embed_output.flatten().tolist()
            except Exception as e:
                print(f"Error getting embedding: {e}")
        
        # Store data in Redis (unique to predict endpoint)
        drawing_id = f"drawing:{session_id}:{round}"
        drawing_data = {
            "session_id": session_id,
            "round": round,
            "prompt": prompt,
            "time_spent_sec": time_spent_sec,
            "timed_out": timed_out,
            "image_base64": image_base64,
            "predictions": json.dumps(probs_map),
            "round_choices": json.dumps(round_choices),
            "embedding": json.dumps(embedding),
            "timestamp": datetime.now().isoformat(),
            "original_image_data": original_image_base64  # Store original image data for visualization
        }
        r.hset(drawing_id, mapping=drawing_data)
        r.lpush(f"session:{session_id}:drawings", drawing_id)
        
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
    r = get_redis()
    session_data = r.hgetall(f"session:{session_id}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data["rounds"] = json.loads(session_data.get("rounds", "[]"))
    session_data["prompts"] = json.loads(session_data.get("prompts", "[]"))
    return {"session": session_data}

@router.get("/api/drawing/{session_id}")
async def get_drawing(session_id: str):
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
            max_background_samples_per_class=500,  # 500 samples per class
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
    """Generate both UMAP and radar charts by calling existing endpoints"""
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
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "embed_model_loaded": embed_model is not None,
        "classes_count": len(CLASSES)
    }

@router.get("/api/qr-code/{session_id}")
async def get_qr_code(session_id: str):
    """
    Check if QR code already exists for a session and return the QR code image
    """
    try:
        r = get_redis()
        qr_data = r.hgetall(f"qr_code:{session_id}")
        
        if not qr_data:
            return {
                "status": "not_found",
                "message": "QR code not found for this session"
            }
        
        # Convert bytes to strings
        # qr_info = {key.decode(): value.decode() for key, value in qr_data.items()}
        
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

@router.delete("/api/qr-code/{session_id}")
async def delete_qr_code(session_id: str):
    """
    Delete QR code from Redis database
    """
    try:
        r = get_redis()
        qr_data = r.hgetall(f"qr_code:{session_id}")
        
        if not qr_data:
            raise HTTPException(status_code=404, detail="QR code not found")
        
        # Delete QR code metadata and image from Redis
        r.delete(f"qr_code:{session_id}")
        
        return {
            "status": "success",
            "message": "QR code deleted successfully from database"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting QR code: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/api/generate-qr-code")
async def generate_qr_code(
    sessionId: str = Form(...),
    playerName: str = Form(...),
    shareableUrl: str = Form(...)
):
    """
    Generate QR code image and store in Redis database
    """
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        r = get_redis()
        
        # Check if QR code already exists for this session
        existing_qr = r.hgetall(f"qr_code:{sessionId}")
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
        qr.add_data(shareableUrl)
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
            "session_id": sessionId,
            "player_name": playerName,
            "shareable_url": shareableUrl,
            "qr_image_base64": qr_image_base64,
            "created_at": current_time
        }
        r.hset(f"qr_code:{sessionId}", mapping=qr_code_data)
        r.expire(f"qr_code:{sessionId}", 7 * 24 * 3600)  # Expire after 7 days
        
        return {
            "status": "success",
            "qr_image_base64": qr_image_base64,
            "shareable_url": shareableUrl,
            "message": "QR code generated and stored in database",
            "from_cache": False,
            "created_at": current_time
        }
        
    except Exception as e:
        print(f"Error generating QR code: {e}")
        raise HTTPException(status_code=500, detail=f"QR code generation failed: {str(e)}")

@router.post("/api/upload-screenshot")
async def upload_screenshot(
    screenshot: UploadFile = File(...),
    sessionId: str = Form(...),
    playerName: str = Form(...)
):
    """
    Upload a screenshot and return a shareable URL for QR code generation
    Screenshot is still saved as file for download functionality
    """
    try:
        # Validate file type
        if not screenshot.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads/screenshots"
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = screenshot.filename.split('.')[-1] if '.' in screenshot.filename else 'png'
        safe_player_name = "".join(c for c in playerName if c.isalnum() or c in ('-', '_'))
        filename = f"quickdraw_{safe_player_name}_{sessionId}_{timestamp}.{file_extension}"
        
        # Save file
        file_path = os.path.join(uploads_dir, filename)
        content = await screenshot.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Generate shareable URL
        shareable_url = f"http://localhost:8000/api/download-screenshot/{filename}"
        
        current_time = datetime.now().isoformat()
        
        # Store screenshot metadata in Redis
        r = get_redis()
        screenshot_data = {
            "filename": filename,
            "session_id": sessionId,
            "player_name": playerName,
            "upload_time": current_time,
            "file_size": len(content),
            "shareable_url": shareable_url
        }
        r.hset(f"screenshot:{filename}", mapping=screenshot_data)
        r.expire(f"screenshot:{filename}", 7 * 24 * 3600)  # Expire after 7 days
        
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