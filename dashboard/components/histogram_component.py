import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np
from typing import List, Dict, Any

label_map = {'easy': '簡單', 'hard': '困難'}

def show_score_histogram(sessions_data: List[Dict[str, Any]]):
    """Display score di        fig_mean =                'Hard': '#F44336',x.bar(
            stats_df,
            x='Difficulty',
            y='Mean',
            title="Average Score by Difficulty",
            color='Difficulty',
            color_discrete_map={
                'Easy': '#4CAF50',
                'Hard': '#F44336'
            }
        )istograms and statistics"""
    
    if not sessions_data:
        st.info("No data available for score analysis.")
        return
    
    # Import data fetcher here to avoid circular imports
    from utils.data_fetcher import DataFetcher
    
    # Create a dummy data fetcher to use its methods
    data_fetcher = DataFetcher()
    score_data = data_fetcher.get_score_distribution(sessions_data)
    
    # st.header("📈 分數分佈分析")
    
    # Analysis type selection
    analysis_type = st.selectbox(
        "選擇分析類型",
        ["組合分析", "比較分析", "統計摘要"]
    )
    
    if analysis_type == "組合分析":
        show_combined_analysis(score_data)
    elif analysis_type == "比較分析":
        show_comparative_analysis(score_data)
    else:
        show_statistical_summary(score_data, sessions_data)

def show_combined_analysis(score_data: Dict[str, List[float]]):
    """Show combined histogram for all difficulties"""
    
    # Prepare data for combined histogram
    all_scores = []
    all_difficulties = []
    
    colors = {'easy': '#4CAF50', 'hard': '#F44336'}
    
    for difficulty, scores in score_data.items():
        all_scores.extend(scores)
        all_difficulties.extend([difficulty.title()] * len(scores))
    
    if not all_scores:
        st.info("No score data available.")
        return
    
    # Create DataFrame
    df = pd.DataFrame({
        'Score': all_scores,
        'Difficulty': all_difficulties
    })
    
    # Overlapping histograms
    st.subheader("難度分數分佈")
    
    fig = go.Figure()
    
    # Map difficulty labels to Chinese for display
    df['Difficulty_CN'] = df['Difficulty'].str.lower().map(label_map)
    
    for difficulty in ['Easy', 'Hard']:
        key = difficulty.lower()
        if key in score_data and score_data[key]:
            difficulty_scores = df[df['Difficulty'] == difficulty]['Score']
            difficulty_cn = label_map.get(key, difficulty)
            fig.add_trace(go.Histogram(
                x=difficulty_scores,
                name=difficulty_cn,
                opacity=0.7,
                marker_color=colors[key],
                nbinsx=20
            ))
    
    fig.update_layout(
        title="所有難度的分數分佈",
        xaxis_title="分數",
        yaxis_title="玩家人數",
        barmode='overlay',
        height=500
    )
    
    st.plotly_chart(fig, width='stretch')
    
    # Box plot for comparison
    st.subheader("分數分佈箱型圖")
    
    fig_box = px.box(
        df, 
        x='Difficulty_CN', 
        y='Score',
        title="各難度分數分佈統計",
        color='Difficulty_CN',
        color_discrete_map={
            label_map['easy']: '#4CAF50',
            label_map['hard']: '#F44336'
        },
        labels={'Difficulty_CN': '難度', 'Score': '分數'}
    )
    
    fig_box.update_layout(
        height=400,
        xaxis_title="難度",
        yaxis_title="分數",
        legend_title_text="難度"
    )
    st.plotly_chart(fig_box, width='stretch')

# def show_individual_analysis(score_data: Dict[str, List[float]]):
#     """Show detailed analysis for individual difficulties"""
    
#     difficulty_choice = st.selectbox(
#         "Select Difficulty Level",
#         ["Easy", "Hard"]
#     )
    
#     difficulty_key = difficulty_choice.lower()
#     scores = score_data.get(difficulty_key, [])
    
#     if not scores:
#         st.info(f"No data available for {difficulty_choice} difficulty.")
#         return
    
#     colors = {'easy': '#4CAF50', 'hard': '#F44336'}
#     color = colors[difficulty_key]
    
#     # Basic statistics
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric("Total Players", len(scores))
    
#     with col2:
#         st.metric("Average Score", f"{np.mean(scores):.1f}")
    
#     with col3:
#         st.metric("Median Score", f"{np.median(scores):.1f}")
    
#     with col4:
#         st.metric("Max Score", f"{np.max(scores):.1f}")
    
#     # Detailed histogram
#     st.subheader(f"{difficulty_choice} Difficulty - Score Distribution")
    
#     # Calculate optimal number of bins
#     n_bins = min(max(10, len(scores) // 5), 30)
    
#     fig = go.Figure()
#     fig.add_trace(go.Histogram(
#         x=scores,
#         nbinsx=n_bins,
#         marker_color=color,
#         opacity=0.8,
#         name=f"{difficulty_choice} Scores"
#     ))
    
#     # Add statistical lines
#     mean_score = np.mean(scores)
#     median_score = np.median(scores)
    
#     fig.add_vline(x=mean_score, line_dash="dash", line_color="red", 
#                   annotation_text=f"Mean: {mean_score:.1f}")
#     fig.add_vline(x=median_score, line_dash="dot", line_color="blue", 
#                   annotation_text=f"Median: {median_score:.1f}")
    
#     fig.update_layout(
#         title=f"Score Distribution - {difficulty_choice} Difficulty",
#         xaxis_title="Score",
#         yaxis_title="Number of Players",
#         height=500
#     )
    
#     st.plotly_chart(fig, width='stretch')
    
#     # Percentile analysis
#     st.subheader("Percentile Analysis")
    
#     percentiles = [10, 25, 50, 75, 90, 95, 99]
#     percentile_values = [np.percentile(scores, p) for p in percentiles]
    
#     df_percentiles = pd.DataFrame({
#         'Percentile': [f"{p}th" for p in percentiles],
#         'Score': percentile_values
#     })
    
#     fig_percentiles = px.bar(
#         df_percentiles,
#         x='Percentile',
#         y='Score',
#         title=f"Score Percentiles - {difficulty_choice} Difficulty",
#         color='Score',
#         color_continuous_scale='Viridis'
#     )
    
#     st.plotly_chart(fig_percentiles, width='stretch')
    
#     # Performance categories
#     st.subheader("Performance Categories")
    
#     # Define score ranges
#     q25, q75 = np.percentile(scores, [25, 75])
    
#     categories = {
#         'Beginner': len([s for s in scores if s < q25]),
#         'Intermediate': len([s for s in scores if q25 <= s < q75]),
#         'Advanced': len([s for s in scores if s >= q75])
#     }
    
#     df_categories = pd.DataFrame(list(categories.items()), columns=['Category', 'Players'])
    
#     fig_pie = px.pie(
#         df_categories,
#         values='Players',
#         names='Category',
#         title=f"Player Skill Distribution - {difficulty_choice}",
#         color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
#     )
    
#     st.plotly_chart(fig_pie, width='stretch')

def show_comparative_analysis(score_data: Dict[str, List[float]]):
    """Show comparative analysis across difficulties"""
    
    st.subheader("跨難度比較")
    
    # Prepare comparative statistics
    stats_data = []
    
    for difficulty, scores in score_data.items():
        if scores:
            stats_data.append({
                '難度': label_map.get(difficulty, difficulty),
                '玩家數量': len(scores),
                '平均分數': np.mean(scores),
                '中位數': np.median(scores),
                '標準差': np.std(scores),
                '最小值': np.min(scores),
                '最大值': np.max(scores),
                '分數範圍': np.max(scores) - np.min(scores)
            })
    
    if not stats_data:
        st.info("No data available for comparison.")
        return
    
    df_stats = pd.DataFrame(stats_data)
    
    # Display statistics table
    st.subheader("統計比較")
    st.dataframe(df_stats, width='stretch', hide_index=True)
    
    # Violin plot for distribution comparison
    st.subheader("分佈形狀比較")
    
    # Prepare data for violin plot
    plot_data = []
    for difficulty, scores in score_data.items():
        for score in scores:
            difficulty = label_map.get(difficulty, difficulty)
            plot_data.append({'難度': difficulty, '分數': score})
    
    if plot_data:
        df_plot = pd.DataFrame(plot_data)
        
        fig_violin = px.violin(
            df_plot,
            x='難度',
            y='分數',
            title="按難度劃分的分數分佈形狀",
            color='難度',
            color_discrete_map={
                label_map['easy']: '#4CAF50',
                label_map['hard']: '#F44336'
            },
            box=True
        )
        
        fig_violin.update_layout(height=500)
        st.plotly_chart(fig_violin, width='stretch')
    
    # Mean comparison chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig_mean = px.bar(
            df_stats,
            x='難度',
            y='平均分數',
            title="按難度劃分的平均分數",
            color='難度',
            color_discrete_map={
                label_map['easy']: '#4CAF50',
                label_map['hard']: '#F44336'
            },
        )
        st.plotly_chart(fig_mean, width='stretch')
    
    with col2:
        fig_range = px.bar(
            df_stats,
            x='難度',
            y='分數範圍',
            title="按難度劃分的分數範圍",
            color='難度',
            color_discrete_map={
                label_map['easy']: '#4CAF50',
                label_map['hard']: '#F44336'
            }
        )
        st.plotly_chart(fig_range, width='stretch')

def show_statistical_summary(score_data: Dict[str, List[float]], sessions_data: List[Dict[str, Any]]):
    """Show detailed statistical summary"""
    
    st.subheader("全面的統計分析s")
    
    # Overall statistics
    all_scores = []
    for scores in score_data.values():
        all_scores.extend(scores)
    
    if not all_scores:
        st.info("No score data available.")
        return
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("總遊戲數", len(all_scores))
    
    with col2:
        st.metric("整體平均", f"{np.mean(all_scores):.1f}")
    
    with col3:
        st.metric("整體中位數", f"{np.median(all_scores):.1f}")
    
    with col4:
        st.metric("標準差", f"{np.std(all_scores):.1f}")
    
    with col5:
        st.metric("分數範圍", f"{np.max(all_scores) - np.min(all_scores):.1f}")
    
    # 進階統計
    st.subheader("進階指標")
    
    # Calculate additional metrics
    try:
        from scipy import stats
        scipy_available = True
    except ImportError:
        scipy_available = False
        st.warning("SciPy not available. Some advanced statistics will be skipped.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("分佈特性")
        
        if scipy_available:
            skewness = stats.skew(all_scores)
            kurtosis = stats.kurtosis(all_scores)
            
            st.write(f"**偏態 (Skewness)：** {skewness:.3f}")
            if skewness > 0:
                st.write("↗️ 右偏（分數分佈尾巴延伸至較高分）")
            elif skewness < 0:
                st.write("↖️ 左偏（分數分佈尾巴延伸至較低分）")
            else:
                st.write("➡️ 近似對稱")
            
            st.write(f"**峰態 (Kurtosis)：** {kurtosis:.3f}")
            if kurtosis > 0:
                st.write("📈 高峰厚尾（極端分數較多）")
            else:
                st.write("📉 低峰薄尾（極端分數較少）")
        else:
            st.write("SciPy not available. Some advanced statistics will be skipped.")
    
    with col2:
        st.subheader("玩家人口統計影響")
        
        # 依年齡分組分析分數
        age_scores = {}
        for session in sessions_data:
            age = int(session.get('age', 0))
            score = session.get('total_score', 0)
            if age > 0:
                age_group = f"{(age//10)*10}歲"
                if age_group not in age_scores:
                    age_scores[age_group] = []
                age_scores[age_group].append(score)
        
        if age_scores:
            st.write("**各年齡層平均分數：**")
            for age_group, scores in sorted(age_scores.items()):
                avg_score = np.mean(scores)
                st.write(f"- {age_group}: {avg_score:.1f} 分（{len(scores)} 位玩家）")
    
    # 常態分佈檢驗
    st.subheader("分佈分析")
    
    if scipy_available:
        # Shapiro-Wilk test for normality (if sample size is appropriate)
        if 3 <= len(all_scores) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(all_scores)
            st.write(f"**常態性檢驗（Shapiro-Wilk）:**")
            st.write(f"- 統計量: {shapiro_stat:.4f}")
            st.write(f"- P 值: {shapiro_p:.4f}")
            if shapiro_p < 0.05:
                st.write("❌ 分數分佈不符合常態分佈")
            else:
                st.write("✅ 分數分佈近似常態分佈")
        
        # Q-Q plot
        fig_qq = go.Figure()
        
        # Calculate theoretical quantiles for normal distribution
        sorted_scores = np.sort(all_scores)
        n = len(sorted_scores)
        theoretical_quantiles = stats.norm.ppf(np.arange(1, n+1) / (n+1), loc=np.mean(all_scores), scale=np.std(all_scores))
        
        fig_qq.add_trace(go.Scatter(
            x=theoretical_quantiles,
            y=sorted_scores,
            mode='markers',
            name='實際 vs 理論',
            marker=dict(color='blue', size=6)
        ))
        
        # Add reference line
        min_val = min(min(theoretical_quantiles), min(sorted_scores))
        max_val = max(max(theoretical_quantiles), max(sorted_scores))
        fig_qq.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='完美常態',
            line=dict(color='red', dash='dash')
        ))
        
        fig_qq.update_layout(
            title="Q-Q Plot: 實際分數 vs 理論分佈",
            xaxis_title="理論分位數",
            yaxis_title="實際分數",
            height=400
        )
        
        st.plotly_chart(fig_qq, width='stretch')
    else:
        st.write("Advanced distribution analysis requires SciPy installation")