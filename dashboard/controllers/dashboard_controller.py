"""
Dashboard Controller - Main controller for managing the QuickDraw dashboard
"""
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any
from utils.data_fetcher import DataFetcher
from components.overview_tab import OverviewTab
from components.rankings_tab import RankingsTab
from components.score_analysis_tab import ScoreAnalysisTab


class DashboardController:
    """Main controller for the QuickDraw Dashboard"""
    
    def __init__(self):
        # Use environment variable for backend URL (for Docker compatibility)
        import os
        self.backend_url = os.getenv("QUICKDRAW_BACKEND_URL", "http://http://140.109.74.39:8088/")
        self.data_fetcher = DataFetcher(backend_url=self.backend_url)
        
        # Initialize session state for language if not exists
        if 'language' not in st.session_state:
            st.session_state.language = 'zh'  # Default to Chinese
        self.view_names = ["📊 概覽 Overview", "🏆 玩家排行榜 Rankings", "📈 分數分析 Score Analysis"]
        self.tab_classes = [OverviewTab, RankingsTab, ScoreAnalysisTab]
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables"""
        if 'current_view' not in st.session_state:
            st.session_state.current_view = 0
        if 'last_switch_time' not in st.session_state:
            st.session_state.last_switch_time = datetime.now()
        if 'previous_view' not in st.session_state:
            st.session_state.previous_view = 0
        if 'main_placeholder' not in st.session_state:
            st.session_state.main_placeholder = None
    
    def render_sidebar(self) -> Dict[str, Any]:
        """Render sidebar controls and return configuration"""
        st.sidebar.title("Dashboard Settings 儀表板設定")
        
        # Language toggle button
        language_options = {
            'zh': '中文 (Chinese)',
            'en': '英文 (English)'
        }
        
        current_language = st.session_state.get('language', 'zh')
        
        # Language selection
        selected_language = st.sidebar.selectbox(
            "Language / 語言",
            options=['zh', 'en'],
            format_func=lambda x: language_options[x],
            index=0 if current_language == 'zh' else 1,
            key="language_selector"
        )
        
        # Update session state if language changed
        if selected_language != st.session_state.language:
            # Clear all cached content when language changes
            self._clear_all_tab_caches()
            st.session_state.language = selected_language
            st.rerun()
        
        st.sidebar.divider()
        
        # # Backend URL configuration
        # backend_url = st.sidebar.text_input(
        #     "Backend URL 後端網址", 
        #     value=self.backend_url,
        #     help="URL of your QuickDraw backend API 你畫我猜後端API網址"
        # )
        
        # # Update backend URL if changed
        # if backend_url != self.backend_url:
        #     self.backend_url = backend_url
        #     self.data_fetcher = DataFetcher(backend_url)
        
        # Check backend connection
        if not self.data_fetcher.check_connection():
            st.error("❌ Cannot connect to backend. Please check the backend URL and ensure the server is running. 無法連接到後端，請檢查後端網址並確保伺服器正在運行。")
            st.stop()
        
        st.sidebar.success("✅ Connected to backend 已連接到後端")
        
        # Time range filter
        time_range = st.sidebar.selectbox(
            "Time Range 時間範圍",
            options=["Last 1 hour", "Last 24 hours", "Last 7 days", "Last 30 days", "All time"],
            index=4
        )
        
        # Difficulty filter
        difficulty_filter = st.sidebar.multiselect(
            "Difficulty Levels 難度等級",
            options=["easy", "hard"],
            default=["easy", "hard"]
        )
        
        # Auto-refresh option
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s) 自動刷新 (30秒)", value=False)
        if auto_refresh:
            st.sidebar.info("Dashboard will refresh every 30 seconds 儀表板將每30秒刷新一次")
        
        # Auto tab switching option
        auto_switch_tabs = st.sidebar.checkbox("Auto-switch views (10s) 自動切換頁面 (10秒)", value=False)
        switch_interval = st.sidebar.slider("Switch interval (seconds) 切換間隔(秒)", 5, 30, 10)
        
        if auto_switch_tabs:
            st.sidebar.info(f"Views will switch every {switch_interval} seconds 頁面將每{switch_interval}秒自動切換")
            self._handle_auto_switching(switch_interval)
            self._render_switch_indicator(switch_interval)
        
        return {
            'time_range': time_range,
            'difficulty_filter': difficulty_filter,
            'auto_refresh': auto_refresh,
            'auto_switch_tabs': auto_switch_tabs,
            'switch_interval': switch_interval
        }
    
    def _handle_auto_switching(self, switch_interval: int):
        """Handle automatic view switching logic"""
        current_time = datetime.now()
        if (current_time - st.session_state.last_switch_time).seconds >= switch_interval:
            # Clear cache for the current view before switching
            current_view = st.session_state.get('current_view', 0)
            self._clear_view_specific_cache(current_view)
            
            # Clear any existing content before switching
            self._clear_tab_content()
            
            # Update view tracking
            st.session_state.previous_view = st.session_state.current_view
            st.session_state.current_view = (st.session_state.current_view + 1) % 3
            st.session_state.last_switch_time = current_time
            
            # Force rerun to refresh the display
            st.rerun()
    
    def _render_switch_indicator(self, switch_interval: int):
        """Render auto-switch progress indicator"""
        current_view_name = self.view_names[st.session_state.current_view]
        st.sidebar.write(f"**Current view:** {current_view_name}")
        
        time_since_switch = (datetime.now() - st.session_state.last_switch_time).seconds
        remaining_time = switch_interval - time_since_switch
        st.sidebar.write(f"**Next switch in:** {remaining_time}s")
        
        # Progress bar for visual feedback
        progress = time_since_switch / switch_interval
        st.sidebar.progress(progress)
    
    def _clear_tab_content(self):
        """Clear previous tab content to prevent content overlap"""
        # Clear any session state that might cache content between tabs
        keys_to_clear = [key for key in st.session_state.keys() if 
                        key.startswith('plotly_') or 
                        key.startswith('chart_') or 
                        key.startswith('tab_') or
                        key.startswith('data_cache_') or
                        key.startswith('render_')]
        
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Clear the main placeholder if it exists
        if 'main_placeholder' in st.session_state and st.session_state.main_placeholder is not None:
            st.session_state.main_placeholder.empty()
            st.session_state.main_placeholder = None
        
        # Force garbage collection to ensure clean memory state
        import gc
        gc.collect()
    
    def _get_cache_key_prefix(self) -> str:
        """Generate a unique cache key prefix for the current session and view"""
        current_view = st.session_state.get('current_view', 0)
        language = st.session_state.get('language', 'zh')
        session_id = id(st.session_state)  # Use session state object id as unique session identifier
        return f"tab_{current_view}_{language}_{session_id}"
    
    def _clear_view_specific_cache(self, view_index: int):
        """Clear cache specific to a particular view"""
        language = st.session_state.get('language', 'zh')
        session_id = id(st.session_state)
        view_prefix = f"tab_{view_index}_{language}_{session_id}"
        
        # Clear session state keys for this specific view
        keys_to_clear = [key for key in st.session_state.keys() if key.startswith(view_prefix)]
        for key in keys_to_clear:
            del st.session_state[key]
    
    def _clear_all_tab_caches(self):
        """Clear all tab-related caches (useful for language changes)"""
        session_id = id(st.session_state)
        
        # Clear all tab-related session state keys
        keys_to_clear = [key for key in st.session_state.keys() if 
                        any(prefix in key for prefix in [
                            'tab_', 'overview_', 'rankings_', 'score_analysis_',
                            'plotly_', 'chart_', 'data_cache_', 'render_'
                        ]) and str(session_id) in key]
        
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Clear main placeholder
        if 'main_placeholder' in st.session_state:
            if st.session_state.main_placeholder is not None:
                st.session_state.main_placeholder.empty()
            st.session_state.main_placeholder = None
    
    def load_data(self, time_range: str, difficulty_filter: List[str]) -> List[Dict[str, Any]]:
        """Load and filter dashboard data"""
        with st.spinner("Loading dashboard data... 載入儀表板數據中..."):
            sessions_data = self.data_fetcher.get_all_sessions(filter_complete=True)  # Only complete sessions for dashboard
            
            if not sessions_data:
                st.warning("No game data found. Play some games first! 找不到遊戲數據，請先玩幾局遊戲！")
                st.stop()
        
        # Filter data based on selections
        return self.data_fetcher.filter_sessions(sessions_data, time_range, difficulty_filter)
    
    def render_content(self, data: List[Dict[str, Any]], config: Dict[str, Any]):
        """Render main dashboard content"""
        auto_switch_tabs = config['auto_switch_tabs']
        current_language = st.session_state.get('language', 'zh')
        
        if auto_switch_tabs:
            # Auto-switching mode: show content based on session state
            current_view = st.session_state.current_view
            cache_key_prefix = self._get_cache_key_prefix()
            
            # Create a new placeholder for each switch to ensure clean rendering
            placeholder_key = f"main_placeholder_{current_view}_{datetime.now().timestamp()}"
            
            # Clear any existing placeholder
            if 'main_placeholder' in st.session_state and st.session_state.main_placeholder is not None:
                st.session_state.main_placeholder.empty()
            
            # Create fresh placeholder
            st.session_state.main_placeholder = st.empty()
            
            # Render new content in the placeholder
            with st.session_state.main_placeholder.container():
                st.header(self.view_names[current_view])
                
                # Create and render the appropriate tab with unique cache prefix
                tab_class = self.tab_classes[current_view]
                tab_instance = tab_class(data, current_language)
                
                # Store the cache prefix in session state for the tab to use
                st.session_state[f'{cache_key_prefix}_active'] = True
                
                tab_instance.render()
        else:
            # Manual mode: show traditional tabs with proper isolation
            tab1, tab2, tab3 = st.tabs(["📊 概覽 Overview", "🏆 玩家排行榜 Rankings", "📈 分數分析 Score Analysis"])
            
            with tab1:
                # Generate unique cache key for overview tab
                overview_cache_key = f"overview_{current_language}_{id(st.session_state)}"
                st.session_state[f'{overview_cache_key}_active'] = True
                
                overview_tab = OverviewTab(data, current_language)
                overview_tab.render()
            
            with tab2:
                # Generate unique cache key for rankings tab
                rankings_cache_key = f"rankings_{current_language}_{id(st.session_state)}"
                st.session_state[f'{rankings_cache_key}_active'] = True
                
                rankings_tab = RankingsTab(data, current_language)
                rankings_tab.render()
            
            with tab3:
                # Generate unique cache key for score analysis tab
                score_cache_key = f"score_analysis_{current_language}_{id(st.session_state)}"
                st.session_state[f'{score_cache_key}_active'] = True
                
                score_analysis_tab = ScoreAnalysisTab(data, current_language)
                score_analysis_tab.render()
    
    def handle_auto_refresh(self, config: Dict[str, Any]):
        """Handle auto-refresh logic"""
        auto_refresh = config['auto_refresh']
        auto_switch_tabs = config['auto_switch_tabs']
        
        if auto_refresh or auto_switch_tabs:
            import time
            
            # Only clear cache if we're switching tabs, not just refreshing
            if auto_switch_tabs:
                # The cache clearing is handled in _handle_auto_switching
                pass
            elif auto_refresh:
                # For regular refresh, only clear data caches, not UI state
                self._clear_data_caches_only()
            
            # Use a shorter sleep for more responsive switching
            time.sleep(1)
            st.rerun()
    
    def _clear_data_caches_only(self):
        """Clear only data-related caches, preserving UI state"""
        keys_to_clear = [key for key in st.session_state.keys() if 
                        key.startswith('data_cache_') or 
                        key.startswith('api_cache_')]
        
        for key in keys_to_clear:
            del st.session_state[key]
    
    def run(self):
        """Main method to run the dashboard"""
        # Render header
        st.markdown(
            '<h2 class="main-header">🎨 你畫我猜 - AI猜圖擂台賽 即時戰況</h1>', 
            unsafe_allow_html=True
        )
        
        # Render sidebar and get configuration
        config = self.render_sidebar()
        
        # Load data
        filtered_data = self.load_data(config['time_range'], config['difficulty_filter'])
        
        # Render main content
        self.render_content(filtered_data, config)
        
        # Handle auto-refresh
        self.handle_auto_refresh(config)