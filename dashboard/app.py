import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# Import dashboard components
from components.ranking_component import show_ranking_lists
from components.histogram_component import show_score_histogram
from utils.data_fetcher import DataFetcher

# Page configuration
st.set_page_config(
    page_title="QuickDraw Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .difficulty-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-weight: bold;
        color: white;
        display: inline-block;
        margin: 0.25rem;
    }
    
    .easy { background-color: #4CAF50; }
    .medium { background-color: #FF9800; }
    .hard { background-color: #F44336; }
    </style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🎨 QuickDraw Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.title("Dashboard Settings")
    
    # Backend URL configuration
    backend_url = st.sidebar.text_input(
        "Backend URL", 
        value="http://localhost:8000",
        help="URL of your QuickDraw backend API"
    )
    
    # Initialize data fetcher
    data_fetcher = DataFetcher(backend_url)
    
    # Check backend connection
    if not data_fetcher.check_connection():
        st.error("❌ Cannot connect to backend. Please check the backend URL and ensure the server is running.")
        st.stop()
    
    st.sidebar.success("✅ Connected to backend")
    
    # Time range filter
    time_range = st.sidebar.selectbox(
        "Time Range",
        options=["Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
        index=3
    )
    
    # Difficulty filter
    difficulty_filter = st.sidebar.multiselect(
        "Difficulty Levels",
        options=["easy", "medium", "hard"],
        default=["easy", "medium", "hard"]
    )
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.info("Dashboard will refresh every 30 seconds")
    
    # Main dashboard tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🏆 Rankings", "📈 Score Analysis"])
    
    # Fetch data
    with st.spinner("Loading dashboard data..."):
        sessions_data = data_fetcher.get_all_sessions()
        
        if not sessions_data:
            st.warning("No game data found. Play some games first!")
            st.stop()
    
    # Filter data based on selections
    filtered_data = data_fetcher.filter_sessions(sessions_data, time_range, difficulty_filter)
    
    with tab1:
        show_overview(filtered_data)
    
    with tab2:
        show_ranking_lists(filtered_data)
    
    with tab3:
        show_score_histogram(filtered_data)
    
    # Auto-refresh
    if auto_refresh:
        import time
        time.sleep(30)
        st.rerun()

def show_overview(data):
    """Show overview statistics"""
    if not data:
        st.info("No data available for the selected filters.")
        return
    
    # Calculate metrics
    total_players = len(data)
    total_games = sum(len(session.get('drawings', [])) for session in data)
    avg_score = sum(session.get('total_score', 0) for session in data) / len(data) if data else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Players", total_players)
    
    with col2:
        st.metric("Total Games", total_games)
    
    with col3:
        st.metric("Average Score", f"{avg_score:.1f}")
    
    with col4:
        difficulty_counts = {}
        for session in data:
            diff = session.get('difficulty', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        most_popular = max(difficulty_counts, key=difficulty_counts.get) if difficulty_counts else "N/A"
        st.metric("Popular Difficulty", most_popular)
    
    # Difficulty distribution chart
    st.subheader("Player Distribution by Difficulty")
    
    if difficulty_counts:
        df_diff = pd.DataFrame(list(difficulty_counts.items()), columns=['Difficulty', 'Count'])
        
        fig = px.pie(
            df_diff, 
            values='Count', 
            names='Difficulty',
            title="Players by Difficulty Level",
            color_discrete_map={
                'easy': '#4CAF50',
                'medium': '#FF9800', 
                'hard': '#F44336'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Create a timeline of recent games
    recent_sessions = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    for session in recent_sessions:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write(f"**{session.get('player_name', 'Unknown')}**")
        
        with col2:
            difficulty = session.get('difficulty', 'unknown')
            color_class = {'easy': 'easy', 'medium': 'medium', 'hard': 'hard'}.get(difficulty, 'easy')
            st.markdown(f'<span class="difficulty-badge {color_class}">{difficulty.upper()}</span>', unsafe_allow_html=True)
        
        with col3:
            st.write(f"Score: {session.get('total_score', 0)}")
        
        with col4:
            timestamp = session.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.write(dt.strftime("%m/%d %H:%M"))
                except:
                    st.write("Recent")

if __name__ == "__main__":
    main()