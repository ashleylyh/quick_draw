"""
Overview Tab - Dashboard overview with metrics and recent activity
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Any
from components.base_tab import BaseTab


class OverviewTab(BaseTab):
    """Overview tab showing general statistics and recent activity"""
    
    def __init__(self, data: List[Dict[str, Any]], language: str = 'zh'):
        super().__init__(data, language)
    
    def render(self):
        """Render the overview tab content"""
        if not self.has_data():
            self.show_no_data_message()
            return
            
        metrics = self.calculate_basic_metrics()
        
        # Add minimal spacing
        st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)
        mcol1, mcol2 = st.columns([2.6, 1], vertical_alignment="top")
        with mcol1:
            css = """
            .st-key-my_yellow_container1 {
                background-color: #F5F5F5;
                border-radius: 10px;
                padding: 1rem;
                margin: 0.25rem 0;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                border: 2px solid #E0E0E0;
            }
            """
            st.html(f"<style>{css}</style>")
            with st.container(key="my_yellow_container1"):
                self._render_metrics(metrics)
            col1, col2 = st.columns([2,1])
            with col1:
                self._render_cross_difficulty_comparison()
            with col2:
                self._render_difficulty_distribution(metrics['difficulty_counts'])
        with mcol2:
            css = """
            .st-key-my_yellow_container2 {
                background-color: #FFF7D9;
                border-radius: 10px;
                padding: 1rem;
                margin: 0.25rem 0;
                box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                border: 2px solid #fff0c5;
            }
            """
            st.html(f"<style>{css}</style>")
            with st.container(key="my_yellow_container2"):
                self._render_recent_activity()
    
    def _render_metrics(self, metrics: Dict[str, Any]):
        """Render the main metrics row"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"<span style='font-size:1em; font-weight:bold'>{self.get_text('total_players')}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:2.2em; font-weight:semibold'>{metrics['total_players']}</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<span style='font-size:1em; font-weight:bold'>{self.get_text('average_score')}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:2.2em; font-weight:semibold'>{metrics['avg_score']:.1f}</span>", unsafe_allow_html=True)

        with col3:
            difficulty_counts = metrics['difficulty_counts']
            most_popular_key = max(difficulty_counts, key=difficulty_counts.get) if difficulty_counts else "N/A"
            most_popular = self.get_difficulty_label(most_popular_key) if most_popular_key != "N/A" else "N/A"
            st.markdown(f"<span style='font-size:1em; font-weight:bold'>{self.get_text('popular_difficulty')}</span>", unsafe_allow_html=True)
            st.markdown(f"<span style='font-size:2.2em; font-weight:semibold'>{most_popular}</span>", unsafe_allow_html=True)
    
    def _render_difficulty_distribution(self, difficulty_counts: Dict[str, int]):
        """Render the difficulty distribution pie chart"""
        if difficulty_counts:
            # Map difficulty labels for display
            difficulty_col = self.get_text('difficulty') if self.language == 'en' else '難度'
            count_col = self.get_text('player_count') if self.language == 'en' else '玩家數量'
            df_diff = pd.DataFrame(
                [(self.get_difficulty_label(k), v) for k, v in difficulty_counts.items()],
                columns=[difficulty_col, count_col]
            )

            # Use centralized color mapping
            color_map = self.get_difficulty_color_map()

            fig = px.pie(
                df_diff, 
                values=count_col, 
                names=difficulty_col,
                color=difficulty_col,
                color_discrete_map=color_map,
                title=self.get_text('difficulty_distribution')
            )
            fig.update_traces(
                textfont=dict(color='white', size=16, family='Arial', weight='bold'),
                textinfo='label+percent'  # Show both label and percent
            )
            fig.update_layout(
                height=300, 
                margin=dict(t=50, b=20, l=20, r=20),
                showlegend=False  # Remove legend beside the graph
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_cross_difficulty_comparison(self):
        """Render cross-difficulty comparison section"""
        # Import data fetcher here to avoid circular imports
        from utils.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        rankings = data_fetcher.get_ranking_data(self.data)
        
        # Create comparison metrics
        comparison_data = []
        difficulty_levels = ['easy', 'hard']
        
        for difficulty in difficulty_levels:
            players = rankings.get(difficulty, [])
            if players:         
                difficulty_col = self.get_text('difficulty') if self.language == 'en' else '難度'
                player_count_col = self.get_text('player_count') if self.language == 'en' else '玩家數量'
                avg_score_col = self.get_text('average_score') if self.language == 'en' else '平均分數'
                
                comparison_data.append({
                    difficulty_col: self.get_difficulty_label(difficulty),
                    player_count_col: len(players),
                    avg_score_col: sum(p['total_score'] for p in players) / len(players),
                })
        
        if comparison_data:
            self._render_comparison_charts(comparison_data)
    
    def _render_comparison_charts(self, comparison_data: List[Dict]):
        """Render comparison charts"""
        import plotly.express as px
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Get column names based on language
        difficulty_col = self.get_text('difficulty') if self.language == 'en' else '難度'
        player_count_col = self.get_text('player_count') if self.language == 'en' else '玩家數量'
        avg_score_col = self.get_text('average_score') if self.language == 'en' else '平均分數'
        
        # Create comparison charts
        col1, col2 = st.columns(2)
        
        # Use centralized color mapping
        color_map = self.get_difficulty_color_map()
        
        with col1:
            fig_players = px.bar(
                df_comparison, 
                x=difficulty_col, 
                y=player_count_col,
                title=self.get_text('difficulty_player_count'),
                color=difficulty_col,
                color_discrete_map=color_map
            )
            fig_players.update_layout(
                height=280, 
                margin=dict(t=50, b=40, l=40, r=40),
                showlegend=False  # Remove legend beside the graph
            )
            st.plotly_chart(fig_players, use_container_width=True, key="overview_player_count_chart")
        
        with col2:
            fig_scores = px.bar(
                df_comparison, 
                x=difficulty_col, 
                y=avg_score_col,
                title=self.get_text('difficulty_average_score'),
                color=difficulty_col,
                color_discrete_map=color_map
            )
            fig_scores.update_layout(
                height=280, 
                margin=dict(t=50, b=40, l=40, r=40),
                showlegend=False  # Remove legend beside the graph
            )
            st.plotly_chart(fig_scores, use_container_width=True, key="overview_avg_score_chart")
      
    def _render_recent_activity(self):
        """Render the recent activity section"""
        st.markdown(
            f"<div style='font-size:1.1em; font-weight:bold; text-align:center; padding: -3rem 0.5rem;'>{self.get_text('recent_activity')}</div>",
            unsafe_allow_html=True
        )
        # Create a timeline of recent games - show 8 for balance between compactness and info
        recent_sessions = sorted(self.data, key=lambda x: x.get('timestamp', ''), reverse=True)[:8]
        
        for session in recent_sessions:
            # Make col1 (player name) smaller, e.g. [1, 1.5, 1, 1]
            col1, col2, col3, col4 = st.columns([1, 0.8, 1, 1])
            
            with col1:
                st.markdown(f"<div style='font-size:0.9em; font-weight:bold; margin:0.1rem 0;'>{session.get('player_name', 'Unknown')}</div>", unsafe_allow_html=True)
            
            with col2:
                difficulty = session.get('difficulty', 'unknown')
                color_class = {'easy': 'easy', 'hard': 'hard'}.get(difficulty, 'easy')
                display_label = self.get_difficulty_label(difficulty)
                st.markdown(f'<span class="difficulty-badge {color_class}">{display_label}</span>', unsafe_allow_html=True)
            
            with col3:
                score_label = self.get_text('score') if self.language == 'en' else '分數'
                st.markdown(f"<div style='font-size:0.9em; margin:0.1rem 0;'>{score_label}: {session.get('total_score', 0)}</div>", unsafe_allow_html=True)
            
            with col4:
                timestamp = session.get('timestamp', '')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime("%m/%d %H:%M")
                    except:
                        recent_text = self.get_text('recent') if self.language == 'en' else '最近'
                        time_str = recent_text
                else:
                    recent_text = self.get_text('recent') if self.language == 'en' else '最近'
                    time_str = recent_text
                st.markdown(f"<div style='font-size:0.85em; margin:0.1rem 0;'>{time_str}</div>", unsafe_allow_html=True)