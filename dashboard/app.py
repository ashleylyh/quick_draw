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
    .hard { background-color: #F44336; }
    </style>
    
    <script>
    // Auto tab switching function (alternative approach)
    function autoSwitchTabs() {
        const tabs = document.querySelectorAll('[data-baseweb="tab"]');
        if (tabs.length > 0) {
            let currentIndex = 0;
            setInterval(() => {
                if (document.querySelector('.auto-switch-enabled')) {
                    tabs[currentIndex].click();
                    currentIndex = (currentIndex + 1) % tabs.length;
                }
            }, 15000); // Switch every 15 seconds
        }
    }
    
    // Run when page loads
    setTimeout(autoSwitchTabs, 1000);
    </script>
""", unsafe_allow_html=True)

label_map = {'easy': '簡單', 'hard': '困難'}

def main():
    # Header
    st.markdown('<h1 class="main-header">🎨 你畫我猜 - AI猜圖擂台賽 即時戰況</h1>', unsafe_allow_html=True)
    
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
        st.error("❌ Cannot connect to backend. Please check the backend URL and ensure the server is running. 無法連接到後端，請檢查後端網址並確保伺服器正在運行。")
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
        options=["easy", "hard"],
        default=["easy", "hard"]
    )
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.info("Dashboard will refresh every 30 seconds")
    
    # Auto tab switching option
    auto_switch_tabs = st.sidebar.checkbox("Auto-switch views (10s) 自動切換頁面 (10秒)", value=False)
    switch_interval = st.sidebar.slider("Switch interval (seconds) 切換間隔(秒)", 5, 30, 10)
    
    if auto_switch_tabs:
        st.sidebar.info(f"Views will switch every {switch_interval} seconds 頁面將每{switch_interval}秒自動切換")
    
    # Initialize session state for view switching
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 0
    if 'last_switch_time' not in st.session_state:
        st.session_state.last_switch_time = datetime.now()
    
    # Auto-switch views logic
    if auto_switch_tabs:
        current_time = datetime.now()
        if (current_time - st.session_state.last_switch_time).seconds >= switch_interval:
            st.session_state.current_view = (st.session_state.current_view + 1) % 3
            st.session_state.last_switch_time = current_time
    
    # View names and display current view indicator
    view_names = ["📊 概覽 Overview", "🏆 排名 Rankings", "📈 分數分析 Score Analysis"]
    
    if auto_switch_tabs:
        current_view_name = view_names[st.session_state.current_view]
        st.sidebar.write(f"**Current view:** {current_view_name}")
        time_since_switch = (datetime.now() - st.session_state.last_switch_time).seconds
        remaining_time = switch_interval - time_since_switch
        st.sidebar.write(f"**Next switch in:** {remaining_time}s")
        
        # Progress bar for visual feedback
        progress = time_since_switch / switch_interval
        st.sidebar.progress(progress)
    
    # Fetch data
    with st.spinner("Loading dashboard data... 載入儀表板數據中..."):
        sessions_data = data_fetcher.get_all_sessions()
        
        if not sessions_data:
            st.warning("No game data found. Play some games first! 找不到遊戲數據，請先玩幾局遊戲！")
            st.stop()
    
    # Filter data based on selections
    filtered_data = data_fetcher.filter_sessions(sessions_data, time_range, difficulty_filter)
    
    # Show content based on auto-switching or manual selection
    if auto_switch_tabs:
        # Auto-switching mode: show content based on session state
        if st.session_state.current_view == 0:
            st.header("📊 概覽 Overview")
            show_overview(filtered_data)
        elif st.session_state.current_view == 1:
            st.header("🏆 排名 Rankings")
            show_ranking_lists(filtered_data)
        elif st.session_state.current_view == 2:
            st.header("📈 分數分析 Score Analysis")
            show_score_histogram(filtered_data)
    else:
        # Manual mode: show traditional tabs
        tab1, tab2, tab3 = st.tabs(["📊 概覽", "🏆 玩家排行榜", "📈 分數分析"])
        
        with tab1:
            show_overview(filtered_data)
        
        with tab2:
            show_ranking_lists(filtered_data)
        
        with tab3:
            show_score_histogram(filtered_data)
    
    # Auto-refresh logic
    if auto_refresh or auto_switch_tabs:
        import time
        refresh_interval = 30 if auto_refresh else (switch_interval if auto_switch_tabs else 30)
        # Use a shorter sleep for more responsive switching
        time.sleep(1)
        st.rerun()

def show_overview(data):
    """Show overview statistics"""
    if not data:
        st.info("No data available for the selected filters. 所選篩選條件沒有可用數據。")
        return
    
    # Calculate metrics
    total_players = len(data)
    total_games = len({session.get('session_id') for session in data if session.get('session_id')})
    avg_score = sum(session.get('total_score', 0) for session in data) / len(data) if data else 0
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("總玩家數", total_players)
    
    with col2:
        st.metric("總遊戲數", total_games)
    
    with col3:
        st.metric("平均分數", f"{avg_score:.1f}")
    
    with col4:
        difficulty_counts = {}
        for session in data:
            diff = session.get('difficulty', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        most_popular_key = max(difficulty_counts, key=difficulty_counts.get) if difficulty_counts else "N/A"
        most_popular = label_map.get(most_popular_key, most_popular_key) if most_popular_key != "N/A" else "N/A"
        st.metric("熱門難度", most_popular)
    
    # Difficulty distribution chart
    st.subheader("各難度玩家分布")

    if difficulty_counts:
        # Map difficulty labels for display
        df_diff = pd.DataFrame(
            [(label_map.get(k, k), v) for k, v in difficulty_counts.items()],
            columns=['Difficulty', 'Count']
        )

        fig = px.pie(
            df_diff, 
            values='Count', 
            names='Difficulty',
            color='Difficulty',
            color_discrete_map={
                '簡單': '#4CAF50',
                '困難': '#F44336'
            }
        )
        fig.update_traces(
            textfont=dict(color='white', size=20, family='Arial', weight='bold'),
            textinfo='percent+label'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("最近戰況")
    
    # Create a timeline of recent games
    recent_sessions = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    for session in recent_sessions:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write(f"**{session.get('player_name', 'Unknown')}**")
        
        with col2:
            difficulty = session.get('difficulty', 'unknown')
            color_class = {'easy': 'easy', 'hard': 'hard'}.get(difficulty, 'easy')
            display_label = label_map.get(difficulty, difficulty)
            st.markdown(f'<span class="difficulty-badge {color_class}">{display_label}</span>', unsafe_allow_html=True)
        
        with col3:
            st.write(f"分數: {session.get('total_score', 0)}")
        
        with col4:
            timestamp = session.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.write(dt.strftime("%m/%d %H:%M"))
                except:
                    st.write("Recent 最近")

if __name__ == "__main__":
    main()