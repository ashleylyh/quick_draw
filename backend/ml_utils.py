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
