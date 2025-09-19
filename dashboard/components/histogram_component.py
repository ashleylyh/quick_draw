import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import numpy as np
from typing import List, Dict, Any

def show_score_histogram(sessions_data: List[Dict[str, Any]]):
    """Display score distribution histograms and statistics"""
    
    if not sessions_data:
        st.info("No data available for score analysis.")
        return
    
    # Import data fetcher here to avoid circular imports
    from utils.data_fetcher import DataFetcher
    
    # Create a dummy data fetcher to use its methods
    data_fetcher = DataFetcher()
    score_data = data_fetcher.get_score_distribution(sessions_data)
    
    st.header("📈 Score Distribution Analysis")
    
    # Analysis type selection
    analysis_type = st.selectbox(
        "Choose Analysis Type",
        ["Combined Analysis", "Individual Difficulty", "Comparative Analysis", "Statistical Summary"]
    )
    
    if analysis_type == "Combined Analysis":
        show_combined_analysis(score_data)
    elif analysis_type == "Individual Difficulty":
        show_individual_analysis(score_data)
    elif analysis_type == "Comparative Analysis":
        show_comparative_analysis(score_data)
    else:
        show_statistical_summary(score_data, sessions_data)

def show_combined_analysis(score_data: Dict[str, List[float]]):
    """Show combined histogram for all difficulties"""
    
    # Prepare data for combined histogram
    all_scores = []
    all_difficulties = []
    
    colors = {'easy': '#4CAF50', 'medium': '#FF9800', 'hard': '#F44336'}
    
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
    st.subheader("Score Distribution by Difficulty")
    
    fig = go.Figure()
    
    for difficulty in ['Easy', 'Medium', 'Hard']:
        if difficulty in df['Difficulty'].values:
            difficulty_scores = df[df['Difficulty'] == difficulty]['Score']
            fig.add_trace(go.Histogram(
                x=difficulty_scores,
                name=difficulty,
                opacity=0.7,
                marker_color=colors[difficulty.lower()],
                nbinsx=20
            ))
    
    fig.update_layout(
        title="Score Distribution Across All Difficulties",
        xaxis_title="Score",
        yaxis_title="Number of Players",
        barmode='overlay',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Box plot for comparison
    st.subheader("Score Distribution Box Plot")
    
    fig_box = px.box(
        df, 
        x='Difficulty', 
        y='Score',
        title="Score Distribution Statistics by Difficulty",
        color='Difficulty',
        color_discrete_map={
            'Easy': '#4CAF50',
            'Medium': '#FF9800',
            'Hard': '#F44336'
        }
    )
    
    fig_box.update_layout(height=400)
    st.plotly_chart(fig_box, use_container_width=True)

def show_individual_analysis(score_data: Dict[str, List[float]]):
    """Show detailed analysis for individual difficulties"""
    
    difficulty_choice = st.selectbox(
        "Select Difficulty Level",
        ["Easy", "Medium", "Hard"]
    )
    
    difficulty_key = difficulty_choice.lower()
    scores = score_data.get(difficulty_key, [])
    
    if not scores:
        st.info(f"No data available for {difficulty_choice} difficulty.")
        return
    
    colors = {'easy': '#4CAF50', 'medium': '#FF9800', 'hard': '#F44336'}
    color = colors[difficulty_key]
    
    # Basic statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Players", len(scores))
    
    with col2:
        st.metric("Average Score", f"{np.mean(scores):.1f}")
    
    with col3:
        st.metric("Median Score", f"{np.median(scores):.1f}")
    
    with col4:
        st.metric("Max Score", f"{np.max(scores):.1f}")
    
    # Detailed histogram
    st.subheader(f"{difficulty_choice} Difficulty - Score Distribution")
    
    # Calculate optimal number of bins
    n_bins = min(max(10, len(scores) // 5), 30)
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=n_bins,
        marker_color=color,
        opacity=0.8,
        name=f"{difficulty_choice} Scores"
    ))
    
    # Add statistical lines
    mean_score = np.mean(scores)
    median_score = np.median(scores)
    
    fig.add_vline(x=mean_score, line_dash="dash", line_color="red", 
                  annotation_text=f"Mean: {mean_score:.1f}")
    fig.add_vline(x=median_score, line_dash="dot", line_color="blue", 
                  annotation_text=f"Median: {median_score:.1f}")
    
    fig.update_layout(
        title=f"Score Distribution - {difficulty_choice} Difficulty",
        xaxis_title="Score",
        yaxis_title="Number of Players",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Percentile analysis
    st.subheader("Percentile Analysis")
    
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    percentile_values = [np.percentile(scores, p) for p in percentiles]
    
    df_percentiles = pd.DataFrame({
        'Percentile': [f"{p}th" for p in percentiles],
        'Score': percentile_values
    })
    
    fig_percentiles = px.bar(
        df_percentiles,
        x='Percentile',
        y='Score',
        title=f"Score Percentiles - {difficulty_choice} Difficulty",
        color='Score',
        color_continuous_scale='Viridis'
    )
    
    st.plotly_chart(fig_percentiles, use_container_width=True)
    
    # Performance categories
    st.subheader("Performance Categories")
    
    # Define score ranges
    q25, q75 = np.percentile(scores, [25, 75])
    
    categories = {
        'Beginner': len([s for s in scores if s < q25]),
        'Intermediate': len([s for s in scores if q25 <= s < q75]),
        'Advanced': len([s for s in scores if s >= q75])
    }
    
    df_categories = pd.DataFrame(list(categories.items()), columns=['Category', 'Players'])
    
    fig_pie = px.pie(
        df_categories,
        values='Players',
        names='Category',
        title=f"Player Skill Distribution - {difficulty_choice}",
        color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

def show_comparative_analysis(score_data: Dict[str, List[float]]):
    """Show comparative analysis across difficulties"""
    
    st.subheader("Cross-Difficulty Comparison")
    
    # Prepare comparative statistics
    stats_data = []
    
    for difficulty, scores in score_data.items():
        if scores:
            stats_data.append({
                'Difficulty': difficulty.title(),
                'Players': len(scores),
                'Mean': np.mean(scores),
                'Median': np.median(scores),
                'Std Dev': np.std(scores),
                'Min': np.min(scores),
                'Max': np.max(scores),
                'Range': np.max(scores) - np.min(scores)
            })
    
    if not stats_data:
        st.info("No data available for comparison.")
        return
    
    df_stats = pd.DataFrame(stats_data)
    
    # Display statistics table
    st.subheader("Statistical Comparison")
    st.dataframe(df_stats, use_container_width=True, hide_index=True)
    
    # Violin plot for distribution comparison
    st.subheader("Distribution Shape Comparison")
    
    # Prepare data for violin plot
    plot_data = []
    for difficulty, scores in score_data.items():
        for score in scores:
            plot_data.append({'Difficulty': difficulty.title(), 'Score': score})
    
    if plot_data:
        df_plot = pd.DataFrame(plot_data)
        
        fig_violin = px.violin(
            df_plot,
            x='Difficulty',
            y='Score',
            title="Score Distribution Shapes by Difficulty",
            color='Difficulty',
            color_discrete_map={
                'Easy': '#4CAF50',
                'Medium': '#FF9800',
                'Hard': '#F44336'
            },
            box=True
        )
        
        fig_violin.update_layout(height=500)
        st.plotly_chart(fig_violin, use_container_width=True)
    
    # Mean comparison chart
    col1, col2 = st.columns(2)
    
    with col1:
        fig_mean = px.bar(
            df_stats,
            x='Difficulty',
            y='Mean',
            title="Average Score by Difficulty",
            color='Difficulty',
            color_discrete_map={
                'Easy': '#4CAF50',
                'Medium': '#FF9800',
                'Hard': '#F44336'
            }
        )
        st.plotly_chart(fig_mean, use_container_width=True)
    
    with col2:
        fig_range = px.bar(
            df_stats,
            x='Difficulty',
            y='Range',
            title="Score Range by Difficulty",
            color='Difficulty',
            color_discrete_map={
                'Easy': '#4CAF50',
                'Medium': '#FF9800',
                'Hard': '#F44336'
            }
        )
        st.plotly_chart(fig_range, use_container_width=True)

def show_statistical_summary(score_data: Dict[str, List[float]], sessions_data: List[Dict[str, Any]]):
    """Show detailed statistical summary"""
    
    st.subheader("Comprehensive Statistical Analysis")
    
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
        st.metric("Total Games", len(all_scores))
    
    with col2:
        st.metric("Overall Mean", f"{np.mean(all_scores):.1f}")
    
    with col3:
        st.metric("Overall Median", f"{np.median(all_scores):.1f}")
    
    with col4:
        st.metric("Standard Deviation", f"{np.std(all_scores):.1f}")
    
    with col5:
        st.metric("Score Range", f"{np.max(all_scores) - np.min(all_scores):.1f}")
    
    # Advanced statistics
    st.subheader("Advanced Metrics")
    
    # Calculate additional metrics
    try:
        from scipy import stats
        scipy_available = True
    except ImportError:
        scipy_available = False
        st.warning("SciPy not available. Some advanced statistics will be skipped.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distribution Properties")
        
        if scipy_available:
            skewness = stats.skew(all_scores)
            kurtosis = stats.kurtosis(all_scores)
            
            st.write(f"**Skewness:** {skewness:.3f}")
            if skewness > 0:
                st.write("↗️ Right-skewed (tail extends to higher scores)")
            elif skewness < 0:
                st.write("↖️ Left-skewed (tail extends to lower scores)")
            else:
                st.write("➡️ Approximately symmetric")
            
            st.write(f"**Kurtosis:** {kurtosis:.3f}")
            if kurtosis > 0:
                st.write("📈 Heavy-tailed (more extreme scores)")
            else:
                st.write("📉 Light-tailed (fewer extreme scores)")
        else:
            st.write("Advanced distribution metrics require SciPy installation")
    
    with col2:
        st.subheader("Player Demographics Impact")
        
        # Analyze score by age groups
        age_scores = {}
        for session in sessions_data:
            age = session.get('age', 0)
            score = session.get('total_score', 0)
            if age > 0:
                age_group = f"{(age//10)*10}s"
                if age_group not in age_scores:
                    age_scores[age_group] = []
                age_scores[age_group].append(score)
        
        if age_scores:
            st.write("**Average Score by Age Group:**")
            for age_group, scores in sorted(age_scores.items()):
                avg_score = np.mean(scores)
                st.write(f"- {age_group}: {avg_score:.1f} ({len(scores)} players)")
    
    # Normal distribution test
    st.subheader("Distribution Analysis")
    
    if scipy_available:
        # Shapiro-Wilk test for normality (if sample size is appropriate)
        if 3 <= len(all_scores) <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(all_scores)
            st.write(f"**Normality Test (Shapiro-Wilk):**")
            st.write(f"- Statistic: {shapiro_stat:.4f}")
            st.write(f"- P-value: {shapiro_p:.4f}")
            if shapiro_p < 0.05:
                st.write("❌ Scores are NOT normally distributed")
            else:
                st.write("✅ Scores appear to be normally distributed")
        
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
            name='Actual vs Theoretical',
            marker=dict(color='blue', size=6)
        ))
        
        # Add reference line
        min_val = min(min(theoretical_quantiles), min(sorted_scores))
        max_val = max(max(theoretical_quantiles), max(sorted_scores))
        fig_qq.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Perfect Normal',
            line=dict(color='red', dash='dash')
        ))
        
        fig_qq.update_layout(
            title="Q-Q Plot: Actual Scores vs Normal Distribution",
            xaxis_title="Theoretical Quantiles",
            yaxis_title="Actual Scores",
            height=400
        )
        
        st.plotly_chart(fig_qq, use_container_width=True)
    else:
        st.write("Advanced distribution analysis requires SciPy installation")