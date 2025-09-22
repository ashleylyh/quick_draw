"""
Radar chart visualization functions for API integration
"""
import os
import base64
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional
from matplotlib import font_manager as fm
import matplotlib.patches as patches
from utils.plot_utils import get_class_label_map
from config import NOTOSANSTC_PATH

class RadarChart:
    def __init__(self, font_path: Optional[str] = None):
        self.font_path = font_path or NOTOSANSTC_PATH
        if not os.path.exists(self.font_path):
            print("Warning: Chinese font not found, using default font")
            self.font_path = None

    def create_radar_chart(
        self,
        prompts: List[str],
        probabilities: List[float],
        figsize=(10, 10),
        title: str = "AI預測繪圖準確度雷達圖",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Prepare labels (use Chinese mapping if available)
            label_map = get_class_label_map()
            labels = [label_map.get(prompt, prompt) for prompt in prompts]

            # Convert probabilities to percentages
            values = [prob * 100 for prob in probabilities]

            # Number of variables
            N = len(labels)

            # Compute angle for each axis
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            angles += angles[:1]  # Complete the circle

            # Add the first value at the end to close the radar chart
            values += values[:1]
            labels += labels[:1]

            # Initialize the plot
            fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection='polar'))
            fig.patch.set_facecolor('white')

            # Set up font properties
            prop = None
            if self.font_path and os.path.exists(self.font_path):
                try:
                    prop = fm.FontProperties(fname=self.font_path)
                except Exception:
                    prop = None

            # Draw the plot
            ax.plot(angles, values, 'o-', linewidth=2, label='準確度', color='#1f77b4')
            ax.fill(angles, values, alpha=0.25, color='#1f77b4')

            # Add labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels[:-1], fontproperties=prop, fontsize=25)

            # Set y-axis limits and labels
            ax.set_ylim(0, 100)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(['20%', '40%', '60%', '80%', '100%'], fontsize=18)
            ax.grid(True)

            # Add title
            plt.title(title, fontproperties=prop, fontsize=30, fontweight='extra bold', pad=25)

            # Add a border around the entire figure
            border = patches.Rectangle(
                (0.02, 0.02), 0.96, 0.96,
                transform=fig.transFigure,
                linewidth=2,
                edgecolor="black",
                facecolor="none",
                zorder=1000
            )
            fig.patches.append(border)

            # Save to file or memory
            if output_path is None:
                output_path = "/tmp/temp_radar_chart.png"

            plt.savefig(
                output_path,
                dpi=150,
                bbox_inches="tight",
                pad_inches=0.05,
                facecolor='white',
                edgecolor='none'
            )

            # Read and encode as base64
            with open(output_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            # Clean up temporary file
            if output_path.startswith("/tmp/"):
                os.remove(output_path)

            plt.close(fig)

            return {
                "status": "success",
                "image_base64": image_base64,
                "prompts": prompts,
                "probabilities": probabilities
            }

        except Exception as e:
            plt.close('all')  # Clean up any open figures
            if output_path and output_path.startswith("/tmp/") and os.path.exists(output_path):
                os.remove(output_path)

            return {
                "status": "error",
                "error": str(e),
                "image_base64": None,
                "prompts": prompts,
                "probabilities": probabilities
            }

    def create_radar_from_session_data(
        self,
        session_drawings: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        prompts = []
        probabilities = []

        for drawing in session_drawings:
            prompt = drawing.get("prompt")
            predictions = drawing.get("predictions", {})

            if prompt and isinstance(predictions, dict):
                # Get the probability for the specific prompt
                prob = predictions.get(prompt, 0.0)
                prompts.append(prompt)
                probabilities.append(prob)

        if not prompts:
            return {
                "status": "error",
                "error": "No valid drawing data found",
                "image_base64": None,
                "prompts": [],
                "probabilities": []
            }

        return self.create_radar_chart(
            prompts=prompts,
            probabilities=probabilities,
            title="AI預測繪圖準確度雷達圖",
            **kwargs
        )

radar_chart = RadarChart()