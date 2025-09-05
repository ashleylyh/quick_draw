import os
import json
import numpy as np
import keras
import tensorflow as tf
from PIL import Image
import io
from config import MODEL_PATH, CLASSES_PATH
import threading

model = None
embed_model = None

# Load classes
with open(CLASSES_PATH, "r") as f:
    classes_data = json.load(f)
    CLASSES = classes_data["CLASSES"]

def pick_embedding_layer(model, num_classes):
    """
    Find the best embedding layer before the softmax output layer.
    Returns the layer object or None.
    """
    for i in range(len(model.layers) - 1, -1, -1):
        layer = model.layers[i]
        config = layer.get_config() if hasattr(layer, 'get_config') else {}
        units = config.get('units', None)
        activation = config.get('activation', None)
        # Skip softmax layers
        if activation == 'softmax':
            continue
        # Skip output layer with units == num_classes
        if units == num_classes:
            continue
        if i >= 1:
            return layer
    return None

def load_model():
    global model, embed_model
    try:
        if os.path.exists(MODEL_PATH):
            model = keras.models.load_model(MODEL_PATH)
            print(f"[Model] Successfully loaded model from {MODEL_PATH}")
            print(f"[Model] Model input shape: {model.input_shape}")
            print(f"[Model] Model output shape: {model.output_shape}")

            emb_layer = pick_embedding_layer(model, len(CLASSES))
            if emb_layer is None:
                L = len(model.layers)
                if L < 2:
                    raise RuntimeError("Model too shallow to pick an embedding layer.")
                emb_layer = model.layers[L - 2]
                print("[Model] Embedding fallback: second last layer")
            embed_model = tf.keras.Model(inputs=model.inputs, outputs=emb_layer.output)
            return model, embed_model
        else:
            print(f"[Model] Model file not found at {MODEL_PATH}")
            return None, None
    except Exception as e:
        print(f"[Model] Error loading model: {e}")
        return None, None

def process_image_to_model_input(image_data):
    """Convert image to 28x28x1 format for model - exactly like original getInputImage()"""
    try:
        img = Image.open(io.BytesIO(image_data))
        img = img.convert('L')  # Convert to grayscale
        img = img.resize((28, 28), Image.Resampling.BILINEAR)
        img_array = np.array(img, dtype=np.float32)
        # Invert colors (white background -> black, black drawing -> white) like original
        img_array = (255 - img_array) / 255.0
        img_array = img_array.reshape(28, 28, 1).astype(np.float32)
        return img_array
    except Exception as e:
        print(f"Error processing image: {e}")
        raise

CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}

def _ensure_probabilities(vec: np.ndarray) -> np.ndarray:
    vec = np.asarray(vec, dtype=np.float32).squeeze()
    # valid probs: non-negative and sum ~ 1
    if np.any(vec < 0) or not np.isfinite(vec).all() or not np.isclose(vec.sum(), 1.0, atol=1e-3):
        # treat as logits
        vec = tf.nn.softmax(vec).numpy()
    return vec


def predict_with_round_choices(processed_image, round_choices):
    """
    Predict with probability normalization exactly like the original code.
    This mimics the original tf.tidy + tf.gather + normalize approach.
    """
    if not model:
        raise ValueError("Model not loaded")
    
    # Get full predictions for all classes [345]
    input_tensor = np.expand_dims(processed_image, axis=0)  # [1, 28, 28, 1]
    full_predictions = model.predict(input_tensor, verbose=0).squeeze()  # [345]
    full_predictions = _ensure_probabilities(full_predictions)  # Ensure valid probabilities
    
    if not round_choices:
        # Return all predictions if no round choices specified
        return {class_name: float(full_predictions[i]) for i, class_name in enumerate(CLASSES)}
    
    # Create idxMap - indices of round_choices in CLASSES (like original)
    idx_map = []
    valid_choices = []
    
    for choice in round_choices:
        if choice in CLASSES:
            idx = CLASS_TO_IDX.get(choice)
            if idx is not None:
                idx_map.append(idx)
                valid_choices.append(choice)

    if not idx_map:
        # No valid choices, return empty
        return {}
    
    # Extract predictions for round choices only (like tf.gather)
    picked_predictions = full_predictions[idx_map]  # Shape: [len(round_choices)]
    
    # Normalize exactly like original: picked.div(picked.sum())
    total_prob = np.sum(picked_predictions)
    if total_prob > 0:
        normalized_probs = picked_predictions / total_prob
    else:
        # Handle edge case where all probabilities are 0
        normalized_probs = np.full_like(picked_predictions, 1.0 / len(picked_predictions))
    
    # Create probability map for round choices only
    probs_map = {}
    for i, choice in enumerate(valid_choices):
        probs_map[choice] = float(normalized_probs[i])
    
    return probs_map

def get_embedding(processed_image):
    """Get embedding vector exactly like original"""
    if not embed_model:
        return []
    
    try:
        input_tensor = np.expand_dims(processed_image, axis=0).astype(np.float32)  # [1, 28, 28, 1]
        embedding_output = embed_model.predict(input_tensor, verbose=0)
        embedding_vec = embedding_output.reshape(-1).astype(np.float32).tolist()
        return embedding_vec
    except Exception as e:
        print(f"Warning: Embedding extraction failed: {e}")
        return []

def predict_all_classes(processed_image):
    """Get predictions for all classes (for final submission)"""
    if not model:
        raise ValueError("Model not loaded")
    
    input_tensor = np.expand_dims(processed_image, axis=0)
    predictions = model.predict(input_tensor, verbose=0).squeeze()
    predictions = _ensure_probabilities(predictions)
    
    # Return all class predictions without normalization (original behavior)
    probs_map = {}
    for i, class_name in enumerate(CLASSES):
        probs_map[class_name] = float(predictions[i])
    
    return probs_map