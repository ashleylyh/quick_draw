"""
Drawings Tab - Display high score players' drawings
"""
import streamlit as st
from typing import List, Dict, Any
from components.base_tab import BaseTab


class DrawingsTab(BaseTab):
    """Drawings tab showing high score players' drawings"""
    
    def __init__(self, data: List[Dict[str, Any]], language: str = 'zh'):
        super().__init__(data, language)

    def render(self):
        """Render the drawings tab content"""
        if not self.has_data():
            self.show_no_data_message()
            return
            
        # Import data fetcher here to avoid circular imports
        from utils.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        
        # Get recent players' drawings data (all difficulties)
        with st.spinner(self.get_text('loading_drawings')):
            drawings_data = data_fetcher.get_high_score_drawings(
                self.data, 
                difficulty_filter=None,  # Always show all difficulties
                limit=6  # Show 6 most recent players
            )
        
        
        if not drawings_data:
            st.warning(self.get_text('no_drawings_found'))
            return
            
        self._render_drawings_gallery(drawings_data)
    
    def _render_drawings_gallery(self, drawings_data: List[Dict[str, Any]]):
        """Render the drawings gallery"""
        # st.subheader(f"🏆 {self.get_text('top_players')}")
        
        # Create single row with 6 columns (1 player per column)
        max_drawings = 6
        drawings_to_show = drawings_data[:max_drawings]
        
        if drawings_to_show:
            cols = st.columns(6)  # Fixed 6 columns in 1 row
            
            for col_idx, drawing in enumerate(drawings_to_show):
                with cols[col_idx]:
                    self._render_drawing_card(drawing, col_idx + 1)
    
    def _render_drawing_card(self, drawing: Dict[str, Any], rank: int):
        """Render a single drawing card"""
        player_name = drawing.get('player_name', 'Unknown')
        score = drawing.get('score', 0)
        prompt = drawing.get('prompt', '')
        time_spent = drawing.get('time_spent_sec', 0)
        difficulty = drawing.get('difficulty', 'unknown')
        image_data = drawing.get('image_data', '')
        predictions = drawing.get('predictions', {})
        
        # Get difficulty color
        difficulty_color = self.EASY_COLOR if difficulty == 'easy' else self.HARD_COLOR
        difficulty_label = self.get_difficulty_label(difficulty)
        
            # Create compact card container
        with st.container():
            # Compact rank and basic info
            st.markdown(f"""
            <div style="
                border: 1px solid {difficulty_color}; 
                border-radius: 8px; 
                padding: 8px; 
                margin: 5px 0;
                background: white;
                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            ">
                <div style="text-align: center; margin-bottom: 5px;">
                    <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 3px;">
                        <span style="font-weight: bold; font-size: 0.9em; color: {difficulty_color};">{player_name}</span>
                    </div>
                    <p style="margin: 2px 0; color: #666; font-size: 0.9em;">
                        {self.get_text('score')}: <span style="color: {difficulty_color}; font-weight: bold;">{score:.1f}</span>
                    </p>
                    <p style="margin: 2px 0; color: #666; font-size: 0.8em;">
                        {difficulty_label} | {self.get_class_translation(prompt)}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)            # Compact drawing image
            if image_data:
                try:
                    # Handle base64 image data like in frontend: data:image/png;base64,{image_data}
                    if image_data.startswith('data:image'):
                        # Already has data URL prefix, use as is
                        image_url = image_data
                    else:
                        # Add data URL prefix for base64 data (like frontend does)
                        image_url = f"data:image/png;base64,{image_data}"
                    
                    # Use st.markdown with HTML to display smaller image
                    st.markdown(f"""
                    <div style="text-align: center; margin: 5px 0;">
                        <img src="{image_url}" 
                             alt="Drawing for {prompt}" 
                             style="width: 200px; height: 200px; object-fit: cover; border-radius: 5px; border: 1px solid {difficulty_color};">
                    </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Error: {str(e)[:30]}...")
            else:
                st.markdown(f"""
                <div style="text-align: center; margin: 5px 0;">
                    <div style="width: 160px; height: 160px; background-color: #f0f0f0; border: 1px dashed #ccc; border-radius: 5px; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                        <span style="color: #999; font-size: 0.7em;">No Image</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Compact AI Prediction details with correct prediction indicator
            if predictions:
                # Show top prediction with translation
                top_pred = max(predictions.items(), key=lambda x: x[1])
                confidence = top_pred[1] * 100
                translated_pred = self.get_class_translation(top_pred[0])
                translated_prompt = self.get_class_translation(prompt)
                
                # Check if AI prediction is correct
                is_correct = top_pred[0] == prompt
                
                # Set colors based on correctness
                if is_correct:
                    bg_color = "#e8f5e8"  # Light green background
                    border_color = "#4caf50"  # Green border
                    pred_color = "#2e7d32"  # Dark green text
                    indicator = "✓ "  # Checkmark
                else:
                    bg_color = "#fff3e0"  # Light orange background
                    border_color = "#ff9800"  # Orange border
                    pred_color = "#e65100"  # Dark orange text
                    indicator = "✗ "  # X mark
                
                st.markdown(f"""
                <div style="text-align: center; margin-top: 5px; padding: 6px; background-color: {bg_color}; border-radius: 4px; border: 1px solid {border_color};">
                    <p style="margin: 2px 0; font-size: 1em; color: {pred_color}; font-weight: bold;">
                        <strong>{indicator}{self.get_text('ai_prediction')}:</strong> {translated_pred} ({confidence:.0f}%)
                    </p>
                    <p style="margin: 2px 0; font-size: 0.9em; color: #424242;">
                        <strong>{self.get_text('prompt')}:</strong> {translated_prompt}
                    </p>
                    <p style="margin: 2px 0; font-size: 0.9em; color: #424242;">
                        <strong>{self.get_text('time_spent')}:</strong> {time_spent:.1f}{self.get_text('seconds')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
