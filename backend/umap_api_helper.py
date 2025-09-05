"""
UMAP visualization functions for API integration
"""
import os
import base64
from typing import List, Dict, Any, Optional
import pandas as pd
from umap_auto import plot_umap_with_user

def create_umap_from_embeddings(
    user_embeddings: List[List[float]],
    user_prompts: List[str],
    output_path: Optional[str] = None,
    figsize=(10, 7),
    user_marker="^",
    user_color="black",
    user_size=120,
    annotate=True,
    label_map: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create UMAP visualization from user embeddings and return as base64 image.
    
    Args:
        user_embeddings: List of embedding vectors for each user drawing
        user_prompts: List of prompts corresponding to each drawing
        output_path: Optional path to save the image file
        figsize: Figure size tuple
        user_marker: Marker style for user points
        user_color: Color for user points
        user_size: Size of user points
        annotate: Whether to add text labels
        label_map: Optional mapping from English to Chinese labels
        
    Returns:
        Dict containing:
        - image_base64: Base64 encoded PNG image
        - user_umap: DataFrame with UMAP coordinates
        - skipped_classes: List of skipped classes
    """
    # Convert embeddings to DataFrame
    feature_cols = [f"emb_{i}" for i in range(len(user_embeddings[0]))]
    user_df = pd.DataFrame(user_embeddings, columns=feature_cols)
    user_df.insert(0, "prompt", user_prompts)
    
    # Create temporary CSV file
    temp_csv = "/tmp/temp_user_embeddings.csv"
    user_df.to_csv(temp_csv, index=False)
    
    # Use temporary output path if none provided
    if output_path is None:
        output_path = "/tmp/temp_umap_output.png"
    
    try:
        # Generate UMAP visualization
        result = plot_umap_with_user(
            raw_embedding_csv="./feature/background_embedding.csv",
            umap_background_csv="./feature/background_Umap.csv",
            user_embedding_csv=temp_csv,
            umap_reducer_path="./feature/background_Umap_top72.joblib",
            
            feature_cols=feature_cols,
            input_class_col="prompt",
            bg_class_col="class",
            cluster_col="cluster",
            sample_size=1,
            random_state=42,
            normalize_class_space=True,
            
            figsize=figsize,
            user_marker=user_marker,
            user_color=user_color,
            user_size=user_size,
            annotate=annotate,
            label_map=label_map,
            output_path=output_path,
            show=False,
            font_path="./feature/NotoSansTC.ttf"
        )
        
        # Read the generated image and convert to base64
        if os.path.exists(output_path):
            with open(output_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
        else:
            raise FileNotFoundError(f"Output image not found at {output_path}")
            
        # Clean up temporary files
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        if output_path.startswith("/tmp/") and os.path.exists(output_path):
            os.remove(output_path)
            
        return {
            "image_base64": image_base64,
            "user_umap": result["user_umap"].to_dict('records'),
            "skipped_classes": result["skipped_classes"],
            "status": "success"
        }
        
    except Exception as e:
        # Clean up temporary files on error
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        if output_path.startswith("/tmp/") and os.path.exists(output_path):
            os.remove(output_path)
            
        return {
            "status": "error",
            "error": str(e),
            "image_base64": None,
            "user_umap": [],
            "skipped_classes": []
        }

def get_class_label_map() -> Dict[str, str]:
    """
    Get mapping from English class names to Chinese labels.
    Add your mappings here.
    """
    return {
        "eyeglasses": "眼鏡",
        "mushroom": "蘑菇", 
        "campfire": "營火",
        "ambulance": "救護車",
        "envelope": "信封",
        "strawberry": "草莓",
        "soccer_ball": "足球",
        "bicycle": "腳踏車",
        "clock": "時鐘",
        "map": "地圖",
        "spider": "蜘蛛",
        "hot_air_balloon": "熱氣球",
        "bus": "公車",
        # Add more mappings as needed
    }
