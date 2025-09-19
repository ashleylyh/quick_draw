import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any

def show_ranking_lists(sessions_data: List[Dict[str, Any]]):
    """Display ranking lists for different difficulty levels"""
    
    if not sessions_data:
        st.info("No data available for rankings.")
        return
    
    # Import data fetcher here to avoid circular imports
    from utils.data_fetcher import DataFetcher
    
    # Create a dummy data fetcher to use its methods
    data_fetcher = DataFetcher()
    rankings = data_fetcher.get_ranking_data(sessions_data)
    
    st.header("🏆 Player Rankings")
    
    # Create tabs for each difficulty
    difficulty_tabs = st.tabs(["🟢 Easy", "🟡 Medium", "🔴 Hard"])
    
    difficulty_levels = ['easy', 'medium', 'hard']
    colors = ['#4CAF50', '#FF9800', '#F44336']
    
    for i, (tab, difficulty) in enumerate(zip(difficulty_tabs, difficulty_levels)):
        with tab:
            players = rankings.get(difficulty, [])
            
            if not players:
                st.info(f"No players found for {difficulty} difficulty.")
                continue
            
            st.subheader(f"{difficulty.title()} Difficulty Rankings")
            
            # Top 3 podium display
            if len(players) >= 3:
                col1, col2, col3 = st.columns(3)
                
                # 2nd place
                with col1:
                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #C0C0C0, #E8E8E8); border-radius: 10px; margin: 1rem 0;">
                            <h3>🥈 2nd Place</h3>
                            <h2>{players[1]['player_name']}</h2>
                            <h1 style="color: {colors[i]};">{players[1]['total_score']:.1f}</h1>
                            <p>Games: {players[1]['games_played']}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                # 1st place (larger)
                with col2:
                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #FFD700, #FFA500); border-radius: 10px; margin: 0.5rem 0; transform: scale(1.05);">
                            <h3>👑 1st Place</h3>
                            <h2>{players[0]['player_name']}</h2>
                            <h1 style="color: #B8860B; font-size: 2.5rem;">{players[0]['total_score']:.1f}</h1>
                            <p>Games: {players[0]['games_played']}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                
                # 3rd place
                with col3:
                    st.markdown(
                        f"""
                        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #CD7F32, #D2B48C); border-radius: 10px; margin: 1rem 0;">
                            <h3>🥉 3rd Place</h3>
                            <h2>{players[2]['player_name']}</h2>
                            <h1 style="color: {colors[i]};">{players[2]['total_score']:.1f}</h1>
                            <p>Games: {players[2]['games_played']}</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            # Full rankings table
            st.subheader("Complete Rankings")
            
            # Create DataFrame for the table
            df_rankings = pd.DataFrame(players)
            df_rankings['rank'] = range(1, len(df_rankings) + 1)
            
            # Format the table
            display_df = df_rankings[['rank', 'player_name', 'total_score', 'games_played', 'age', 'gender']].copy()
            display_df.columns = ['Rank', 'Player Name', 'Total Score', 'Games Played', 'Age', 'Gender']
            
            # Style the dataframe
            def style_rankings(row):
                if row['Rank'] == 1:
                    return ['background-color: #FFD70030'] * len(row)
                elif row['Rank'] == 2:
                    return ['background-color: #C0C0C030'] * len(row)
                elif row['Rank'] == 3:
                    return ['background-color: #CD7F3230'] * len(row)
                else:
                    return [''] * len(row)
            
            styled_df = display_df.style.apply(style_rankings, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Statistics
            if players:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Players", len(players))
                
                with col2:
                    avg_score = sum(p['total_score'] for p in players) / len(players)
                    st.metric("Average Score", f"{avg_score:.1f}")
                
                with col3:
                    top_score = players[0]['total_score'] if players else 0
                    st.metric("Top Score", f"{top_score:.1f}")
                
                with col4:
                    total_games = sum(p['games_played'] for p in players)
                    st.metric("Total Games", total_games)
            
            # Score distribution chart for this difficulty
            if len(players) > 1:
                st.subheader(f"Score Distribution - {difficulty.title()}")
                
                scores = [p['total_score'] for p in players]
                names = [p['player_name'] for p in players]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=names[:20],  # Show top 20 players
                    y=scores[:20],
                    marker_color=colors[i],
                    name=f"{difficulty.title()} Scores"
                ))
                
                fig.update_layout(
                    title=f"Top 20 Player Scores - {difficulty.title()} Difficulty",
                    xaxis_title="Player Name",
                    yaxis_title="Total Score",
                    showlegend=False,
                    height=400
                )
                
                # Rotate x-axis labels for better readability
                fig.update_xaxes(tickangle=45)
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Overall comparison across difficulties
    st.header("📊 Cross-Difficulty Comparison")
    
    # Create comparison metrics
    comparison_data = []
    for difficulty in difficulty_levels:
        players = rankings.get(difficulty, [])
        if players:
            comparison_data.append({
                'Difficulty': difficulty.title(),
                'Players': len(players),
                'Avg Score': sum(p['total_score'] for p in players) / len(players),
                'Top Score': max(p['total_score'] for p in players),
                'Total Games': sum(p['games_played'] for p in players)
            })
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        
        # Create comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_players = px.bar(
                df_comparison, 
                x='Difficulty', 
                y='Players',
                title="Number of Players by Difficulty",
                color='Difficulty',
                color_discrete_map={
                    'Easy': '#4CAF50',
                    'Medium': '#FF9800',
                    'Hard': '#F44336'
                }
            )
            st.plotly_chart(fig_players, use_container_width=True)
        
        with col2:
            fig_scores = px.bar(
                df_comparison, 
                x='Difficulty', 
                y='Avg Score',
                title="Average Score by Difficulty",
                color='Difficulty',
                color_discrete_map={
                    'Easy': '#4CAF50',
                    'Medium': '#FF9800',
                    'Hard': '#F44336'
                }
            )
            st.plotly_chart(fig_scores, use_container_width=True)
        
        # Summary table
        st.subheader("Summary Statistics")
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)