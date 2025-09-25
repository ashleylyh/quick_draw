import streamlit as st
from controllers.dashboard_controller import DashboardController
import os
from config import DEFAULT_CONFIG
# Page configuration
st.set_page_config(
    page_title="QuickDraw Dashboard",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 0.75rem;
        margin: 0.25rem 0;
    }
    
    .difficulty-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-weight: bold;
        color: white;
        display: inline-block;
        margin: 0.15rem;
        font-size: 0.85em;
    }
    
    /* Difficulty colors - should match BaseTab.EASY_COLOR and BaseTab.HARD_COLOR */
    .easy { background-color: #4CAF50; }
    .hard { background-color: #F44336; }
    
    /* Reduce spacing between elements */
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    /* Compact dataframe styling */
    .stDataFrame {
        font-size: 0.9em;
    }
    
    /* Reduce padding around main content */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 1rem;
    }
    
    /* Compact subheader styling */
    .stSubheader {
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point"""
    # Initialize and run the dashboard controller
    dashboard = DashboardController()
    dashboard.run()


if __name__ == "__main__":
    main()