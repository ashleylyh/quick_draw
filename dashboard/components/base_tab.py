"""
Base classes for dashboard tabs
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseTab(ABC):
    """Abstract base class for all dashboard tabs"""
    
    def __init__(self, data: List[Dict[str, Any]], language: str = 'zh'):
        self.data = data
        self.language = language
        
        # Color constants for consistent theming
        self.EASY_COLOR = '#43A047'  # Green for easy difficulty
        self.HARD_COLOR = '#E53935'  # Red for hard difficulty
        
        # Language mappings
        self.label_map = {'easy': '簡單', 'hard': '困難'}
        self.label_gender_map = {'male': '男生', 'female': '女生', 'Other': '其他'}
        
        # Multilingual text
        self.texts = {
            'zh': {
                'no_data': "所選篩選條件沒有可用數據。",
                'easy': '簡單',
                'hard': '困難',
                'male': '男生',
                'female': '女生',
                'other': '其他',
                'total_players': '總玩家數',
                'total_games': '總遊戲數',
                'average_score': '平均分數',
                'popular_difficulty': '熱門難度',
                'difficulty_distribution': '各難度玩家分布',
                'recent_activity': '最新遊戲結果',
                'score': '分數',
                'recent': '最近',
                'select_analysis_type': '選擇分析類型',
                'combined_analysis': '組合分析',
                'comparative_analysis': '比較分析',
                # 'statistical_summary': '統計摘要',
                'difficulty_score_distribution': '難度分數分佈',
                'score_distribution_all_difficulties': '所有難度的分數分佈',
                'number_of_players': '玩家人數',
                'score_distribution_boxplot': '分數分佈箱型圖',
                'score_distribution_statistics': '各難度分數分佈統計',
                'difficulty': '難度',
                'comparative_score_analysis': '分數分佈對比分析',
                'statistics_summary': '統計摘要',
                'highest_score': '最高分數',
                'standard_deviation': '標準差',
                'median': '中位數',
                'minimum': '最小值',
                'maximum': '最大值',
                'percentile_25': '第25百分位',
                'percentile_75': '第75百分位',
                'average_score_comparison': '各難度平均分數比較',
                'score_variance_comparison': '各難度分數變異程度',
                'score_distribution_comparison': '分數分佈比較',
                'leaderboard': '排行榜',
                'no_players_found': '找不到玩家',
                'rank': '排名',
                'player_name': '玩家姓名',
                'total_score': '總分數',
                'age': '年齡',
                'gender': '性別',
                'games': '遊戲',
                'score_distribution': '分數分布',
                'top_20_players': '前20名玩家分數',
                'cross_difficulty_comparison': '跨難度比較',
                'player_count': '玩家數量',
                'difficulty_player_count': '各難度玩家數量',
                'difficulty_average_score': '各難度平均分數',
                'top_score': '最高分數',
                'score_range': '分數範圍',
                'age_range':'各年齡層平均分數（每5歲）',
                'qq_plot': 'Q-Q 圖: 實際分數 vs 理論分佈'
            },
            'en': {
                'no_data': "No data available for the selected filters.",
                'easy': 'Easy',
                'hard': 'Hard',
                'male': 'Male',
                'female': 'Female',
                'other': 'Other',
                'total_players': 'Total Players',
                'total_games': 'Total Games',
                'average_score': 'Average Score',
                'popular_difficulty': 'Popular Difficulty',
                'difficulty_distribution': 'Player Distribution by Difficulty',
                'recent_activity': 'Recent Activity',
                'score': 'Score',
                'recent': 'Recent',
                'select_analysis_type': 'Select Analysis Type',
                'combined_analysis': 'Combined Analysis',
                'comparative_analysis': 'Comparative Analysis',
                'statistical_summary': 'Statistical Summary',
                'difficulty_score_distribution': 'Difficulty Score Distribution',
                'score_distribution_all_difficulties': 'Score Distribution for All Difficulties',
                'number_of_players': 'Number of Players',
                'score_distribution_boxplot': 'Score Distribution Box Plot',
                'score_distribution_statistics': 'Score Distribution Statistics by Difficulty',
                'difficulty': 'Difficulty',
                'comparative_score_analysis': 'Comparative Score Analysis',
                'statistics_summary': 'Statistics Summary',
                'highest_score': 'Highest Score',
                'standard_deviation': 'Standard Deviation',
                'median': 'Median',
                'minimum': 'Minimum',
                'maximum': 'Maximum',
                'percentile_25': '25th Percentile',
                'percentile_75': '75th Percentile',
                'average_score_comparison': 'Average Score Comparison by Difficulty',
                'score_variance_comparison': 'Score Variance by Difficulty',
                'score_distribution_comparison': 'Score Distribution Comparison',
                'leaderboard': 'Leaderboard',
                'no_players_found': 'No players found',
                'rank': 'Rank',
                'player_name': 'Player Name',
                'total_score': 'Total Score',
                'age': 'Age',
                'gender': 'Gender',
                'games': 'Games',
                'score_distribution': 'Score Distribution',
                'top_20_players': 'Top 20 Players Scores',
                'cross_difficulty_comparison': 'Cross-Difficulty Comparison',
                'player_count': 'Player Count',
                'difficulty_player_count': 'Player Count by Difficulty',
                'difficulty_average_score': 'Average Score by Difficulty',
                'top_score': 'Top Score',
                'score_range': 'Score Range',
                'age_range': 'Average Score by Age Group (5-year gap)',
                'qq_plot': 'Q-Q Plot: Actual Scores vs Theoretical Distribution'
            }
        }
        
    def get_text(self, key: str) -> str:
        """Get text in current language"""
        return self.texts.get(self.language, self.texts['zh']).get(key, key)
        
    def get_difficulty_label(self, difficulty: str) -> str:
        """Get difficulty label in current language"""
        if self.language == 'en':
            return {'easy': 'Easy', 'hard': 'Hard'}.get(difficulty, difficulty)
        return self.label_map.get(difficulty, difficulty)
        
    def get_gender_label(self, gender: str) -> str:
        """Get gender label in current language"""
        if self.language == 'en':
            return {'male': 'Male', 'female': 'Female', 'Other': 'Other'}.get(gender, gender)
        return self.label_gender_map.get(gender, gender)
    
    def get_difficulty_color_map(self) -> Dict[str, str]:
        """Get color mapping for difficulties based on current language"""
        if self.language == 'en':
            return {
                'Easy': self.EASY_COLOR,
                'Hard': self.HARD_COLOR
            }
        else:
            return {
                '簡單': self.EASY_COLOR,
                '困難': self.HARD_COLOR
            }
    
    def get_difficulty_color(self, difficulty: str) -> str:
        """Get color for a specific difficulty"""
        difficulty_colors = {
            'easy': self.EASY_COLOR,
            'hard': self.HARD_COLOR
        }
        return difficulty_colors.get(difficulty, self.EASY_COLOR)
        
    @abstractmethod
    def render(self):
        """Render the tab content - must be implemented by subclasses"""
        pass
    
    def has_data(self) -> bool:
        """Check if there's data available"""
        return bool(self.data)
    
    def show_no_data_message(self):
        """Show no data available message"""
        st.info(self.get_text('no_data'))
    
    def calculate_basic_metrics(self) -> Dict[str, Any]:
        """Calculate basic metrics used across multiple tabs"""
        if not self.data:
            return {}
            
        total_players = len(self.data)
        total_games = len({session.get('session_id') for session in self.data if session.get('session_id')})
        avg_score = sum(session.get('total_score', 0) for session in self.data) / len(self.data) if self.data else 0
        
        difficulty_counts = {}
        for session in self.data:
            diff = session.get('difficulty', 'unknown')
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
        return {
            'total_players': total_players,
            'total_games': total_games,
            'avg_score': avg_score,
            'difficulty_counts': difficulty_counts
        }