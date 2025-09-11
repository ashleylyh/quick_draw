from fastapi import APIRouter, File, UploadFile, Form, HTTPException
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
from umap_api_helper import create_umap_from_embeddings, get_class_label_map
from radar_chart_auto import create_radar_from_session_data

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
        "timestamp": datetime.now().isoformat()
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
    drawing: UploadFile = File(...)
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
        
        image_data = await drawing.read()
        processed_image = process_image_to_model_input(image_data)
        input_tensor = np.expand_dims(processed_image, axis=0)
        predictions = model.predict(input_tensor, verbose=0).squeeze()
        
        # Filter predictions based on round choices (same logic as predict-realtime)
        if round_choices:
            probs_map = {choice: float(predictions[CLASSES.index(choice)]) for choice in round_choices if choice in CLASSES}
            total_prob = sum(probs_map.values())
            if total_prob > 0:
                for choice in probs_map:
                    probs_map[choice] /= total_prob
        else:
            probs_map = {class_name: float(predictions[i]) for i, class_name in enumerate(CLASSES)}
        
        embedding = []
        if embed_model:
            try:
                embed_output = embed_model.predict(input_tensor, verbose=0)
                embedding = embed_output.flatten().tolist()
            except Exception as e:
                print(f"Error getting embedding: {e}")
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        drawing_id = f"drawing:{session_id}:{round}"
        drawing_data = {
            "session_id": session_id,
            "round": round,
            "prompt": prompt,
            "time_spent_sec": time_spent_sec,
            "timed_out": timed_out,
            "image_base64": image_base64,
            "predictions": json.dumps(probs_map),
            "round_choices": json.dumps(round_choices),  # Store round choices for score page
            "embedding": json.dumps(embedding),
            "timestamp": datetime.now().isoformat()
        }
        r.hset(drawing_id, mapping=drawing_data)
        r.lpush(f"session:{session_id}:drawings", drawing_id)
        # r.expire(drawing_id, 86400)
        # r.expire(f"session:{session_id}:drawings", 86400)
        return {"predictions": probs_map, "embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    """Generate UMAP visualization for a session's embeddings"""
    try:
        r = get_redis()
        # Get all drawing IDs for this session
        drawing_ids = r.lrange(f"session:{session_id}:drawings", 0, -1)
        if not drawing_ids:
            raise HTTPException(status_code=404, detail="No drawings found for this session")

        embeddings = []
        prompts = []
        
        for drawing_id in drawing_ids:
            drawing_data = r.hgetall(drawing_id)
            if drawing_data and "embedding" in drawing_data and "prompt" in drawing_data:
                emb = json.loads(drawing_data.get("embedding", "[]"))
                if emb:  # Only add non-empty embeddings
                    embeddings.append(emb)
                    prompts.append(drawing_data.get("prompt", "unknown"))

        if not embeddings:
            raise HTTPException(status_code=404, detail="No embeddings found for this session")

        # Get Chinese label mapping
        label_map = get_class_label_map()
        
        # Generate UMAP visualization
        result = create_umap_from_embeddings(
            user_embeddings=embeddings,
            user_prompts=prompts,
            label_map=label_map,
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
                "embeddings_count": len(embeddings),
                "user_coordinates": result["user_umap"],
                "skipped_classes": result["skipped_classes"]
            }
        else:
            raise HTTPException(status_code=500, detail=f"UMAP generation failed: {result['error']}")

    except Exception as e:
        print(f"Error generating UMAP visualization: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating UMAP visualization: {str(e)}")

@router.get("/api/radar/{session_id}")
async def generate_radar_chart(session_id: str):
    try:
        r = get_redis()
        
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
        
        # Generate radar chart (mapping and font path handled internally)
        result = create_radar_from_session_data(
            session_drawings=session_drawings
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "image_base64": result["image_base64"],
                "prompts": result["prompts"],
                "probabilities": result["probabilities"],
                "drawings_count": len(session_drawings)
            }
        else:
            raise HTTPException(status_code=500, detail=f"Radar chart generation failed: {result['error']}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating radar chart: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating radar chart: {str(e)}")

@router.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "embed_model_loaded": embed_model is not None,
        "classes_count": len(CLASSES)
    }