"""
Enhanced plotting API with Redis storage support for both UMAP and radar charts.
"""

import os
import json
from typing import Dict, Any, List, Optional
import pandas as pd
from redis_utils import get_redis
from umap_auto import plot_umap_with_user
from radar_chart_auto import create_radar_from_session_data


class PlottingAPI:
    """Enhanced plotting API with Redis storage support."""
    
    def __init__(self, redis_expire_sec: int = 3600):
        """
        Initialize plotting API.
        
        Args:
            redis_expire_sec: Default expiration time for Redis keys
        """
        # self.redis_expire_sec = redis_expire_sec
        self.redis_client = get_redis()
    
    def create_umap_plot(
        self,
        user_embedding_df: pd.DataFrame,
        session_id: str,
        max_background_samples_per_class: Optional[int] = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create UMAP plot and store in Redis.
        
        Args:
            user_embedding_df: User embeddings DataFrame
            session_id: Session ID for Redis key generation
            max_background_samples_per_class: Maximum background samples per class (None = use all)
            **kwargs: Additional arguments for plot_umap_with_user
        
        Returns:
            Dictionary with plot results and Redis key
        """
        try:
            # Generate Redis key
            redis_key = f"umap_plot:{session_id}"
            
            # Default paths - adjust these based on your setup
            default_params = {
                "raw_embedding_csv": "./feature/background_embedding_5per_class.csv",
                "umap_background_csv": "./feature/background_Umap.csv", 
                "umap_reducer_path": "./feature/background_Umap_top72.joblib",
                "feature_cols": [f"emb_{i}" for i in range(512)],
                "input_class_col": "prompt",
                "bg_class_col": "class",
                "cluster_col": "cluster",
                "sample_size": 1,
                "random_state": 42,
                "normalize_class_space": True,
                "max_background_samples_per_class": max_background_samples_per_class,
                "background_sample_strategy": "uniform",
                "figsize": (10, 7),
                "user_marker": "^",
                "user_color": "black", 
                "user_size": 120,
                "annotate": True,
                "redis_key": redis_key,
                "show": False,
                "font_path": "./feature/NotoSansTC.ttf"
            }
            
            # Update with any provided kwargs
            default_params.update(kwargs)
            
            # Create the plot
            result = plot_umap_with_user(
                user_embedding_df=user_embedding_df,
                **default_params
            )
            
            # Store additional metadata in Redis
            metadata_key = f"umap_metadata:{session_id}"
            metadata = {
                "session_id": session_id,
                "num_user_points": len(user_embedding_df),
                "num_background_samples_per_class": str(max_background_samples_per_class) if max_background_samples_per_class else "all",
                "skipped_classes": json.dumps(result.get("skipped_classes", [])),
                "used_scaled": str(result.get("used_scaled", False)),
                "x_col": result.get("x_col", ""),
                "y_col": result.get("y_col", "")
            }
            
            self.redis_client.hset(metadata_key, mapping=metadata)
            # self.redis_client.expire(metadata_key, self.redis_expire_sec)
            
            return {
                "status": "success",
                "redis_key": redis_key,
                "metadata_key": metadata_key,
                "image_base64": result.get("image_base64"),
                "user_points": len(user_embedding_df),
                "skipped_classes": result.get("skipped_classes", []),
                "background_samples_per_class": max_background_samples_per_class
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "redis_key": None,
                "image_base64": None
            }
    
    def create_radar_plot(
        self,
        session_drawings: List[Dict[str, Any]],
        session_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create radar chart and store in Redis.
        
        Args:
            session_drawings: List of drawing data with prompts and predictions
            session_id: Session ID for Redis key generation
            **kwargs: Additional arguments for radar chart creation
        
        Returns:
            Dictionary with plot results and Redis key
        """
        try:
            # Generate Redis key
            redis_key = f"radar_plot:{session_id}"
            
            # Create radar chart
            result = create_radar_from_session_data(
                session_drawings=session_drawings,
                **kwargs
            )
            
            if result["status"] == "success":
                # Store in Redis
                self.redis_client.set(redis_key, result["image_base64"])
                # self.redis_client.expire(redis_key, self.redis_expire_sec)

                # Store metadata
                metadata_key = f"radar_metadata:{session_id}"
                metadata = {
                    "session_id": session_id,
                    "num_drawings": len(session_drawings),
                    "prompts": json.dumps(result.get("prompts", [])),
                    "probabilities": json.dumps(result.get("probabilities", []))
                }
                
                self.redis_client.hset(metadata_key, mapping=metadata)
                # self.redis_client.expire(metadata_key, self.redis_expire_sec)
                
                return {
                    "status": "success",
                    "redis_key": redis_key,
                    "metadata_key": metadata_key,
                    "image_base64": result["image_base64"],
                    "prompts": result.get("prompts", []),
                    "probabilities": result.get("probabilities", [])
                }
            else:
                return result
                
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "redis_key": None,
                "image_base64": None
            }
    
    def get_plot_from_redis(self, redis_key: str) -> Optional[str]:
        """
        Retrieve plot image from Redis.
        
        Args:
            redis_key: Redis key for the plot
        
        Returns:
            Base64 encoded image string or None if not found
        """
        try:
            return self.redis_client.get(redis_key)
        except Exception as e:
            print(f"Error retrieving plot from Redis: {e}")
            return None
    
    def get_metadata_from_redis(self, metadata_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve plot metadata from Redis.
        
        Args:
            metadata_key: Redis key for the metadata
        
        Returns:
            Dictionary with metadata or None if not found
        """
        try:
            metadata = self.redis_client.hgetall(metadata_key)
            if metadata:
                # Parse JSON fields
                if "skipped_classes" in metadata:
                    metadata["skipped_classes"] = json.loads(metadata["skipped_classes"])
                if "prompts" in metadata:
                    metadata["prompts"] = json.loads(metadata["prompts"])
                if "probabilities" in metadata:
                    metadata["probabilities"] = json.loads(metadata["probabilities"])
                if "used_scaled" in metadata:
                    metadata["used_scaled"] = metadata["used_scaled"].lower() == "true"
                    
            return metadata
        except Exception as e:
            print(f"Error retrieving metadata from Redis: {e}")
            return None
    
    def create_both_plots(
        self,
        user_embedding_df: pd.DataFrame,
        session_drawings: List[Dict[str, Any]],
        session_id: str,
        max_background_samples_per_class: Optional[int] = 500,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create both UMAP and radar plots for a session.
        
        Args:
            user_embedding_df: User embeddings DataFrame
            session_drawings: List of drawing data
            session_id: Session ID
            max_background_samples_per_class: Maximum background samples per class (None = use all)
            **kwargs: Additional arguments
        
        Returns:
            Dictionary with results for both plots
        """
        # Split kwargs for different plot types
        umap_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('radar_')}
        radar_kwargs = {k[6:]: v for k, v in kwargs.items() if k.startswith('radar_')}
        
        # Create UMAP plot
        umap_result = self.create_umap_plot(
            user_embedding_df=user_embedding_df,
            session_id=session_id,
            max_background_samples_per_class=max_background_samples_per_class,
            **umap_kwargs
        )
        
        # Create radar plot
        radar_result = self.create_radar_plot(
            session_drawings=session_drawings,
            session_id=session_id,
            **radar_kwargs
        )
        
        return {
            "umap": umap_result,
            "radar": radar_result,
            "session_id": session_id
        }


# Create global instance
plotting_api = PlottingAPI()
