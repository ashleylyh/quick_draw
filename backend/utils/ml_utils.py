import os
import json
import numpy as np
import keras
import tensorflow as tf
from PIL import Image
import io
from config import MODEL_PATH, CLASSES_PATH

class MLUtils:
    def __init__(self, model_path, classes_path):
        self.model_path = model_path
        self.classes_path = classes_path
        self.model = None
        self.embed_model = None
        self.classes = self._load_classes()
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}

    def _load_classes(self):
        with open(self.classes_path, "r") as f:
            classes_data = json.load(f)
            return classes_data["CLASSES"]

    def pick_embedding_layer(self, model, num_classes):
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

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                print(f"[Model] Successfully loaded model from {self.model_path}")
                print(f"[Model] Model input shape: {self.model.input_shape}")
                print(f"[Model] Model output shape: {self.model.output_shape}")

                emb_layer = self.pick_embedding_layer(self.model, len(self.classes))
                if emb_layer is None:
                    L = len(self.model.layers)
                    if L < 2:
                        raise RuntimeError("Model too shallow to pick an embedding layer.")
                    emb_layer = self.model.layers[L - 2]
                    print("[Model] Embedding fallback: second last layer")
                self.embed_model = tf.keras.Model(inputs=self.model.inputs, outputs=emb_layer.output)
                return self.model, self.embed_model
            else:
                print(f"[Model] Model file not found at {self.model_path}")
                return None, None
        except Exception as e:
            print(f"[Model] Error loading model: {e}")
            return None, None

    def process_image_to_model_input(self, image_data):
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


# Initialize the MLUtils class with constants
ml_utils = MLUtils(model_path=MODEL_PATH, classes_path=CLASSES_PATH)
