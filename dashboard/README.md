# QuickDraw Analytics Dashboard

A comprehensive Streamlit-powered dashboard for analyzing QuickDraw game performance, rankings, and score distributions.

## 🎯 Features

### 📊 Overview Dashboard
- **Real-time Metrics**: Total players, games played, average scores
- **Player Distribution**: Visual breakdown by difficulty levels
- **Recent Activity**: Timeline of recent game sessions
- **Difficulty Popularity**: Most played difficulty levels

### 🏆 Rankings System
- **Difficulty-based Rankings**: Separate leaderboards for Easy, Medium, and Hard levels
- **Podium Display**: Visual top 3 players with medals
- **Complete Rankings Table**: Full player listings with scores and statistics
- **Cross-difficulty Comparison**: Performance metrics across all difficulty levels
- **Player Statistics**: Games played, average scores, and demographic data

### 📈 Score Analysis
- **Distribution Histograms**: Score distribution patterns for each difficulty
- **Statistical Analysis**: Mean, median, percentiles, and distribution properties
- **Comparative Analysis**: Cross-difficulty performance comparison
- **Performance Categories**: Player skill classification (Beginner/Intermediate/Advanced)
- **Advanced Metrics**: Skewness, kurtosis, normality tests, and Q-Q plots

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **uv package manager** installed (recommended) or pip
3. **Redis server** running (for data storage)
4. **QuickDraw Backend** running on `http://localhost:8000`

### Quick Setup Script

For the fastest setup, use the provided script:

```bash
# From the project root directory
./setup-dashboard.sh
```

This script will:
- Install all base dependencies
- Install dashboard-specific dependencies
- Provide instructions for running both backend and dashboard

### Installation

1. **Navigate to the project root directory:**
   ```bash
   cd /path/to/quickdraw
   ```

2. **Install dependencies using uv (recommended):**
   ```bash
   # Install base dependencies
   uv sync
   
   # Install dashboard dependencies
   uv sync --extra dashboard
   ```

   **Or using pip (alternative):**
   ```bash
   cd dashboard
   pip install -r requirements.txt
   ```

3. **Start Redis server** (if not already running):
   ```bash
   # On Linux/macOS
   redis-server
   
   # On Windows (if using WSL)
   sudo service redis-server start
   ```

4. **Start the QuickDraw backend** (if not already running):
   ```bash
   # Using uv (recommended)
   uv run uvicorn backend.app:app --host 0.0.0.0 --port 8000
   
   # Or using python directly
   cd backend
   python -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```

5. **Launch the dashboard:**
   ```bash
   cd dashboard
   ./run.sh                    # Uses uv if available, falls back to python
   
   # Or manually with uv
   uv run streamlit run app.py
   
   # Or manually with python
   streamlit run app.py
   ```

6. **Open your browser** and navigate to `http://localhost:8501`

## 🛠️ Configuration

### Environment Variables

You can configure the dashboard using environment variables:

```bash
# Backend API URL
export QUICKDRAW_BACKEND_URL="http://localhost:8000"

# Redis configuration
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export REDIS_DB="0"
```

### Dashboard Settings

The dashboard includes a sidebar with configuration options:

- **Backend URL**: Configure the QuickDraw backend API endpoint
- **Time Range**: Filter data by time periods (Last 24 hours, 7 days, 30 days, All time)
- **Difficulty Levels**: Select which difficulty levels to include in analysis
- **Auto-refresh**: Enable automatic dashboard refresh every 30 seconds

## 📁 Project Structure

```
dashboard/
├── app.py                          # Main Streamlit application
├── config.py                       # Dashboard configuration
├── requirements.txt                 # Python dependencies
├── README.md                       # This documentation
├── .streamlit/
│   └── config.toml                 # Streamlit configuration
├── components/
│   ├── __init__.py
│   ├── ranking_component.py        # Rankings display logic
│   └── histogram_component.py      # Score analysis and visualization
└── utils/
    ├── __init__.py
    └── data_fetcher.py             # Data retrieval and processing
```

## 📊 Data Sources

The dashboard connects to your QuickDraw game data through:

1. **Redis Database**: Direct access to game sessions, player data, and drawings
2. **Backend API**: RESTful API endpoints for data retrieval and health checks
3. **Real-time Updates**: Live data refresh capabilities

### Data Models

The dashboard works with the following data structures:

- **Sessions**: Player information, difficulty settings, timestamps
- **Drawings**: Individual game drawings with predictions and scores
- **Scores**: Calculated performance metrics and rankings

## 🎨 Visualization Features

### Interactive Charts
- **Plotly Integration**: Interactive, zoomable, and exportable charts
- **Color-coded Difficulties**: Consistent color scheme across all visualizations
- **Responsive Design**: Charts adapt to screen size and container width

### Chart Types
- **Bar Charts**: Rankings and comparative analysis
- **Histograms**: Score distribution patterns
- **Box Plots**: Statistical distribution summaries
- **Pie Charts**: Categorical data breakdown
- **Violin Plots**: Distribution shape comparison
- **Q-Q Plots**: Normality assessment

## 🔧 Advanced Usage

### Custom Scoring Algorithm

The dashboard uses a sophisticated scoring system:

```python
def calculate_session_score(drawings):
    total_score = 0.0
    for drawing in drawings:
        predictions = drawing.get('predictions', {})
        target_class = drawing.get('target_class', '')
        
        if target_class in predictions:
            confidence = predictions[target_class]
            time_bonus = max(0, 1 - (time_spent / 30))  # 30s max
            score = confidence * (1 + time_bonus * 0.5)  # 50% time bonus
            total_score += score
    
    return total_score
```

### Statistical Analysis

The dashboard provides comprehensive statistical analysis:

- **Descriptive Statistics**: Mean, median, mode, standard deviation
- **Distribution Analysis**: Skewness, kurtosis, normality tests
- **Percentile Analysis**: Performance ranking and categorization
- **Comparative Statistics**: Cross-difficulty performance metrics

### Performance Categories

Players are automatically categorized based on their scores:

- **Beginner**: Bottom 25th percentile
- **Intermediate**: 25th to 75th percentile  
- **Advanced**: Top 25th percentile

## 🚨 Troubleshooting

### Common Issues

1. **Cannot connect to backend**
   ```
   ❌ Cannot connect to backend. Please check the backend URL and ensure the server is running.
   ```
   **Solution**: Verify that the QuickDraw backend is running on the correct port and URL.

2. **Redis connection failed**
   ```
   Redis connection failed: [Errno 111] Connection refused
   ```
   **Solution**: Start the Redis server and ensure it's accessible on the configured host/port.

3. **No data available**
   ```
   No game data found. Play some games first!
   ```
   **Solution**: Generate some game data by playing QuickDraw games through the main application.

4. **Module import errors**
   ```
   ImportError: No module named 'streamlit'
   ```
   **Solution**: Install the required dependencies using `pip install -r requirements.txt`.

### Performance Optimization

For large datasets:

1. **Enable Caching**: The dashboard uses Streamlit's caching for better performance
2. **Limit Data Range**: Use time range filters to reduce data processing
3. **Pagination**: Large result sets are automatically paginated
4. **Background Processing**: Heavy computations are optimized for performance

## 🔒 Security Considerations

- **No Authentication**: The dashboard currently has no built-in authentication
- **Local Network**: Recommended for use on trusted local networks only
- **Data Privacy**: Ensure Redis instance is properly secured
- **CORS Settings**: Configure CORS appropriately for your environment

## 🤝 Contributing

To contribute to the dashboard:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📈 Future Enhancements

Planned features:
- **User Authentication**: Login system for secure access
- **Data Export**: Export charts and data to various formats
- **Alert System**: Notifications for performance milestones
- **Advanced Filtering**: More granular data filtering options
- **Real-time Streaming**: Live updates as games are played
- **Machine Learning Insights**: Predictive analytics and player behavior analysis

## 📞 Support

For support and questions:
- Check the troubleshooting section above
- Review the QuickDraw backend documentation
- Verify Redis and Streamlit configurations

## 📄 License

This dashboard is part of the QuickDraw project. Please refer to the main project license for usage terms.