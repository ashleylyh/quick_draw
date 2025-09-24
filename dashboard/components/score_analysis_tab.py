"""
Score Analysis Tab - Score distribution analysis and statistics
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np
from typing import List, Dict, Any
from components.base_tab import BaseTab


class ScoreAnalysisTab(BaseTab):
    """Score Analysis tab showing score distributions and statistics"""
    
    def __init__(self, data: List[Dict[str, Any]], language: str = 'zh'):
        super().__init__(data, language)
        self.colors = {'easy': self.EASY_COLOR, 'hard': self.HARD_COLOR}
        
    def render(self):
        """Render the score analysis tab content"""
        if not self.has_data():
            self.show_no_data_message()
            return
            
        # Import data fetcher here to avoid circular imports
        from utils.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        score_data = data_fetcher.get_score_distribution(self.data)
        
        # Show all analysis in a single comprehensive view
        col1, col2 = st.columns([2,1])
        with col1:
            self._show_combined_analysis(score_data)
        with col2:
            self._show_statistical_summary(score_data)

    def _show_combined_analysis(self, score_data: Dict[str, List[float]]):
        """Show combined histogram for all difficulties"""
        
        # Prepare data for combined histogram
        all_scores = []
        all_difficulties = []
        
        for difficulty, scores in score_data.items():
            all_scores.extend(scores)
            all_difficulties.extend([difficulty.title()] * len(scores))
        
        if not all_scores:
            no_data_text = "No score data available." if self.language == 'en' else "沒有可用的分數數據。"
            st.info(no_data_text)
            return
        
        # Create DataFrame
        df = pd.DataFrame({
            'Score': all_scores,
            'Difficulty': all_difficulties
        })
        col1, col2 = st.columns(2)
        with col1:
            self._render_overlapping_histograms(df, score_data)
        with col2:
            self._render_box_plots(df)

    def _render_overlapping_histograms(self, df: pd.DataFrame, score_data: Dict[str, List[float]]):
        """Render overlapping histograms for different difficulties"""

        fig = go.Figure()
        
        # Map difficulty labels to appropriate language for display
        if self.language == 'en':
            df['Difficulty_Display'] = df['Difficulty'].str.lower().map({'easy': 'Easy', 'hard': 'Hard'})
        else:
            df['Difficulty_Display'] = df['Difficulty'].str.lower().map(self.label_map)
        
        for difficulty in ['Easy', 'Hard']:
            key = difficulty.lower()
            if key in score_data and score_data[key]:
                difficulty_scores = df[df['Difficulty'] == difficulty]['Score']
                difficulty_display = self.get_difficulty_label(key)
                fig.add_trace(go.Histogram(
                    x=difficulty_scores,
                    name=difficulty_display,
                    opacity=0.7,
                    marker_color=self.colors[key],
                    nbinsx=20
                ))
        hist_title = self.get_text('difficulty_score_distribution')
        st.write(f"**{hist_title}**")
        fig.update_layout(
            # title=self.get_text('difficulty_score_distribution'),
            xaxis_title=self.get_text('score'),
            yaxis_title=self.get_text('number_of_players'),
            barmode='overlay',
            height=500
        )
        
        st.plotly_chart(fig, width='stretch', key="combined_histogram_chart", title=self.get_text('difficulty_score_distribution'))
    
    def _render_box_plots(self, df: pd.DataFrame):
        """Render box plots for score distribution comparison"""
 
        if self.language == 'en':
            df['Difficulty_Display'] = df['Difficulty'].str.lower().map({'easy': 'Easy', 'hard': 'Hard'})
        else:
            df['Difficulty_Display'] = df['Difficulty'].str.lower().map(self.label_map)
        
        box_title =self.get_text('score_distribution_boxplot')
        st.write(f"**{box_title}**")
        fig_box = px.box(
            df, 
            x='Difficulty_Display', 
            y='Score',
            # title=self.get_text('score_distribution_boxplot'),
            color='Difficulty_Display',
            color_discrete_map=self.get_difficulty_color_map(),
            labels={'Difficulty_Display': self.get_text('difficulty'), 'Score': self.get_text('score')}
        )
        
        fig_box.update_layout(
            height=500,
            xaxis_title=self.get_text('difficulty'),
            yaxis_title=self.get_text('score'),
            legend_title_text=self.get_text('difficulty')
        )
        st.plotly_chart(fig_box, width='stretch', key="combined_boxplot_chart", title=self.get_text('score_distribution_boxplot'))
    
    def _show_statistical_summary(self, score_data: Dict[str, List[float]]):
        """Show detailed statistical summary"""
        
        # Overall statistics from all difficulties
        all_scores = []
        for scores in score_data.values():
            all_scores.extend(scores)
        
        if not all_scores:
            no_data_text = "No score data available." if self.language == 'en' else "沒有可用的分數數據。"
            st.info(no_data_text)
            return

        self._show_player_demographics_impact()


    
    def _show_player_demographics_impact(self):
        """Show player demographics impact on scores"""
        # Age group analysis
        age_scores = {}
        for session in self.data:
            age = int(session.get('age', 0))
            score = session.get('total_score', 0)
            if age >= 0:
                start = (age // 5) * 5
                end = start + 4
                if self.language == 'en':
                    age_group = f"{start}-{end}"
                else:
                    age_group = f"{start}-{end}歲"
                if age_group not in age_scores:
                    age_scores[age_group] = []
                age_scores[age_group].append(score)

        # Show bar plot for average score by age group
        if age_scores:
            age_groups = sorted(age_scores.keys(), key=lambda x: int(x.split('-')[0]))
            avg_scores = [np.mean(age_scores[ag]) for ag in age_groups]
            player_counts = [len(age_scores[ag]) for ag in age_groups]

            bar_title = self.get_text('age_range')
            st.write(f"**{bar_title}**")

            fig = go.Figure(data=[
                go.Bar(
                    x=age_groups,
                    y=avg_scores,
                    text=player_counts,
                    textposition='auto',
                    marker_color="#FBC02D"
                )
            ])
            fig.update_layout(
                xaxis_title="Age Group" if self.language == 'en' else "年齡層",
                yaxis_title="Average Score" if self.language == 'en' else "平均分數",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
  