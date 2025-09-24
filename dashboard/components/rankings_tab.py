"""
Rankings Tab - Player rankings and leaderboards
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
from components.base_tab import BaseTab


class RankingsTab(BaseTab):
    """Rankings tab showing leaderboards and player statistics"""
    
    def __init__(self, data: List[Dict[str, Any]], language: str = 'zh'):
        super().__init__(data, language)
        self.difficulty_levels = ['easy', 'hard']
        self.colors = [self.EASY_COLOR, self.HARD_COLOR]

        
    def render(self):
        """Render the rankings tab content"""
        if not self.has_data():
            self.show_no_data_message()
            return
            
        # Import data fetcher here to avoid circular imports
        from utils.data_fetcher import DataFetcher
        data_fetcher = DataFetcher()
        rankings = data_fetcher.get_ranking_data(self.data)
        
        self._render_difficulty_rankings(rankings)
    
    def _render_difficulty_rankings(self, rankings: Dict[str, List[Dict]]):
        """Render rankings for each difficulty level"""
        col_easy, col_hard = st.columns(2)
        
        for i, (col, difficulty) in enumerate(zip([col_easy, col_hard], self.difficulty_levels)):
            with col:
                players = rankings.get(difficulty, [])
                diff_label = self.get_difficulty_label(difficulty)
                st.subheader(f"{diff_label} {self.get_text('leaderboard')}")

                if not players:
                    st.info(f"{self.get_text('no_players_found')} {diff_label} {self.get_text('difficulty')}")
                    continue

                self._render_podium(players)
                self._render_statistics(players, difficulty)
                self._render_rankings_table(players)

    
    def _render_podium(self, players: List[Dict]):
        """Render top 3 podium display"""
        if len(players) >= 3:
            c1, c2, c3 = st.columns([1, 1, 1], gap="small", vertical_alignment="center")
            
            # 2nd place
            # Determine language and set titles accordingly
            if self.language == 'en':
                second_title = "🥈 2nd Place<br><span style='font-size:0.9rem;color:#888'>(第二名)</span>"
                first_title = "👑 1st Place<br><span style='font-size:0.9rem;color:#888'>(第一名)</span>"
                third_title = "🥉 3rd Place<br><span style='font-size:0.9rem;color:#888'>(第三名)</span>"
            else:
                second_title = "🥈 第二名"
                first_title = "👑 第一名"
                third_title = "🥉 第三名"

            with c1:
                st.markdown(self._get_podium_html(
                    players[1], 
                    second_title, 
                    "#000000",  # pale silver
                    "linear-gradient(135deg, #C0C0C0, #F5F5F5)", 
                    position="2nd"), 
                    unsafe_allow_html=True)
            
            # 1st place (larger)
            with c2:
                st.markdown(self._get_podium_html(
                    players[0], 
                    first_title, 
                    "#000000",  # pale gold
                    "linear-gradient(135deg, #FFD700, #FFF8DC)", 
                    scale="1.02", font_size="2rem", position="1st"), 
                    unsafe_allow_html=True)
            
            # 3rd place
            with c3:
                st.markdown(self._get_podium_html(
                    players[2], 
                    third_title, 
                    "#000000",  # pale bronze
                    "linear-gradient(135deg, #CD7F32, #EED8B0)", 
                    position="3rd"), 
                    unsafe_allow_html=True)
    
    def _get_podium_html(self, player: Dict, title: str, color: str, background: str, 
                        scale: str = "1.0", font_size: str = "1.5rem", position: str = "3rd") -> str:
        """Generate HTML for podium display"""
        # Make all podiums thinner
        padding = "0.6rem 0.3rem" if scale != "1.0" else "0.5rem 0.25rem"
        
        # Set different heights for realistic podium effect
        if position == "1st":
            height = "140px"
            margin_top = "0px"
        elif position == "2nd":
            height = "120px"
            margin_top = "20px"
        else:  # 3rd place
            height = "100px"
            margin_top = "40px"
        
        # Place ranking place and name together in the same line
        return f"""
        <div style="text-align: center; padding: {padding}; background: {background}; 
                    border-radius: 10px; margin-top: {margin_top}; transform: scale({scale}); 
                    display: flex; flex-direction: column; justify-content: flex-end; height: {height}; width: 85%;">
            <div style="margin-left: -1.2rem; margin-bottom: 0.1rem; font-size: 1rem; font-weight: bold;">
                <span>{title.split('<br>')[0] if '<br>' in title else title}</span>
                <span style="margin-left: 0.2rem; font-size: 1.5rem; font-weight: bold;">{player['player_name']}</span>
            </div>
            <div style="color: {color}; font-size: {font_size}; font-weight: bold; margin-bottom: 0.1rem;">{player['total_score']:.1f}</div>
        </div>
        """
    def _render_rankings_table(self, players: List[Dict]):
        """Render the complete rankings table (top 10 only)"""
        # Limit to top 10 players
        top_players = players[:10]
        df_rankings = pd.DataFrame(top_players)
        df_rankings['rank'] = range(1, len(df_rankings) + 1)
        df_rankings['total_score'] = df_rankings['total_score'].round(1).astype(str)
        df_rankings['gender'] = df_rankings['gender'].map(lambda x: self.get_gender_label(x))
        display_df = df_rankings[['rank', 'player_name', 'total_score', 'age', 'gender']].copy()
        
        # Set column names based on language
        if self.language == 'en':
            display_df.columns = [
                self.get_text('rank'), 
                self.get_text('player_name'), 
                self.get_text('total_score'), 
                self.get_text('age'), 
                self.get_text('gender')
            ]
        else:
            display_df.columns = ['排名', '玩家姓名', '總分數', '年齡', '性別']
        
        def style_rankings(row):
            rank_col = self.get_text('rank') if self.language == 'en' else '排名'
            if row[rank_col] == 1:
                return ['background-color: #FFD70030'] * len(row)
            elif row[rank_col] == 2:
                return ['background-color: #C0C0C030'] * len(row)
            elif row[rank_col] == 3:
                return ['background-color: #CD7F3230'] * len(row)
            else:
                return [''] * len(row)

        styled_df = display_df.style.apply(style_rankings, axis=1)
        st.dataframe(styled_df, width='stretch', hide_index=True)
    def _render_statistics(self, players: List[Dict], difficulty: str):
        """Render statistics for the difficulty level"""
        if players:
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric(self.get_text('total_players'), len(players))
            
            with c2:
                avg_score = sum(p['total_score'] for p in players) / len(players)
                st.metric(self.get_text('average_score'), f"{avg_score:.1f}")
            
            with c3:
                top_score = players[0]['total_score'] if players else 0
                st.metric(self.get_text('top_score'), f"{top_score:.1f}")
            
            with c4:
                # Calculate unique sessions for this difficulty
                difficulty_sessions = [session for session in self.data if session.get('difficulty') == difficulty]
                total_games = len({session.get('session_id') for session in difficulty_sessions if session.get('session_id')})
                st.metric(self.get_text('total_games'), total_games)