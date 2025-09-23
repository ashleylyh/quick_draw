import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any

label_map = {'easy': '簡單', 'hard': '困難'}
label_gender_map = {'male': '男生', 'female': '女生', 'Other': '其他'}

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
    
    # st.header("🏆 玩家排行榜")
    
    # Show two tables side by side for each difficulty
    difficulty_levels = ['easy', 'hard']
    colors = ['#4CAF50', '#F44336']

    col_easy, col_hard = st.columns(2)

    for i, (col, difficulty) in enumerate(zip([col_easy, col_hard], difficulty_levels)):
        with col:
            players = rankings.get(difficulty, [])
            diff_label = label_map.get(difficulty, difficulty)
            st.subheader(f"{diff_label} 難度排行榜")

            if not players:
                st.info(f"No players found for {difficulty} difficulty. 找不到{difficulty}難度的玩家。")
                continue

            # Top 3 podium display
            if len(players) >= 3:
                c1, c2, c3 = st.columns(3)
                # 2nd place
                with c1:
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
                with c2:
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
                with c3:
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
            # st.subheader("Complete Rankings")
            label_map
            df_rankings = pd.DataFrame(players)
            df_rankings['rank'] = range(1, len(df_rankings) + 1)
            df_rankings['total_score'] = df_rankings['total_score'].round(1)
            df_rankings['gender'] = df_rankings['gender'].map(label_gender_map)
            display_df = df_rankings[['rank', 'player_name', 'total_score', 'age', 'gender']].copy()
            display_df.columns = ['排名', '玩家姓名', '總分數', '年齡', '性別']
            # Statistics
            if players:
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("總玩家數", len(players))
                with c2:
                    avg_score = sum(p['total_score'] for p in players) / len(players)
                    st.metric("平均分數", f"{avg_score:.1f}")
                with c3:
                    top_score = players[0]['total_score'] if players else 0
                    st.metric("最高分數", f"{top_score:.1f}")
                with c4:
                    # Calculate unique sessions for this difficulty
                    difficulty_sessions = [session for session in sessions_data if session.get('difficulty') == difficulty]
                    total_games = len({session.get('session_id') for session in difficulty_sessions if session.get('session_id')})
                    st.metric("總遊戲數", total_games)
            
            def style_rankings(row):
                if row['排名'] == 1:
                    return ['background-color: #FFD70030'] * len(row)
                elif row['排名'] == 2:
                    return ['background-color: #C0C0C030'] * len(row)
                elif row['排名'] == 3:
                    return ['background-color: #CD7F3230'] * len(row)
                else:
                    return [''] * len(row)

            styled_df = display_df.style.apply(style_rankings, axis=1)
            st.dataframe(styled_df, width='stretch', hide_index=True)

           

            # Score distribution chart for this difficulty
            if len(players) > 1:
                st.subheader(f"Score Distribution - {difficulty.title()} 分數分布 - {difficulty.title()}")
                scores = [p['total_score'] for p in players]
                names = [p['player_name'] for p in players]
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=names[:20],
                    y=scores[:20],
                    marker_color=colors[i],
                    name=f"{difficulty.title()} Scores"
                ))
                fig.update_layout(
                    title=f"Top 20 Player Scores - {difficulty.title()} Difficulty 前20名玩家分數 - {difficulty.title()}難度",
                    xaxis_title="Player Name 玩家姓名",
                    yaxis_title="Total Score 總分數",
                    showlegend=False,
                    height=400
                )
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, width='stretch')
    
    # Overall comparison across difficulties
    st.header("📊 跨難度比較")
    
    # Create comparison metrics
    comparison_data = []
    for difficulty in difficulty_levels:
        players = rankings.get(difficulty, [])
        if players:
            # Calculate unique sessions for this difficulty
            difficulty_sessions = [session for session in sessions_data if session.get('difficulty') == difficulty]
            total_games = len({session.get('session_id') for session in difficulty_sessions if session.get('session_id')})
            
            comparison_data.append({
                '難度': label_map.get(difficulty, difficulty),  # Use label_map for display
                '玩家數量': len(players),
                '平均分數': sum(p['total_score'] for p in players) / len(players),
                'Top Score': max(p['total_score'] for p in players),
                'Total Games': total_games
            })
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        
        # Create comparison charts
        col1, col2 = st.columns(2)
        
        with col1:
            fig_players = px.bar(
                df_comparison, 
                x='難度', 
                y='玩家數量',
                title="各難度玩家數量",
                color='難度',
                color_discrete_map={
                    label_map['easy']: '#4CAF50',
                    label_map['hard']: '#F44336'
                }
            )
            st.plotly_chart(fig_players, width='stretch')
        
        with col2:
            fig_scores = px.bar(
                df_comparison, 
                x='難度', 
                y='平均分數',
                title="各難度平均分數",
                color='難度',
                color_discrete_map={
                    label_map['easy']: '#4CAF50',
                    label_map['hard']: '#F44336'
                }
            )
            st.plotly_chart(fig_scores, width='stretch')
        
        # # Summary table
        # st.subheader("Summary Statistics 統計摘要")
        # st.dataframe(df_comparison, width='stretch', hide_index=True)