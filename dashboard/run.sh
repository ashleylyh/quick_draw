#!/bin/bash

# QuickDraw Dashboard Startup Script

echo "🎨 QuickDraw Analytics Dashboard"
echo "================================="

# Check if we're in the dashboard directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the dashboard directory"
    echo "Usage: cd dashboard && ./run.sh"
    exit 1
fi

# Check if Python is available
PYTHON_CMD=""
if command -v uv &> /dev/null; then
    echo "🎯 Using uv for Python execution"
    PYTHON_CMD="uv run"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Neither uv nor Python is installed or not in PATH"
    exit 1
fi

echo "🐍 Using Python execution method: $PYTHON_CMD"

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
if [ "$PYTHON_CMD" = "uv run" ]; then
    # For uv, check if the project is set up
    if [ ! -f "../pyproject.toml" ]; then
        echo "❌ Error: pyproject.toml not found. Please run from the dashboard directory inside the project."
        exit 1
    fi
    
    # Check if dashboard extra is installed
    if ! $PYTHON_CMD python -c "import streamlit" 2>/dev/null; then
        echo "📦 Installing dashboard dependencies with uv..."
        cd .. && uv sync --extra dashboard && cd dashboard
        
        if [ $? -ne 0 ]; then
            echo "❌ Error: Failed to install dependencies with uv"
            exit 1
        fi
    fi
else
    # For regular Python, check if Streamlit is installed
    if ! $PYTHON_CMD -c "import streamlit" 2>/dev/null; then
        echo "📦 Installing dependencies..."
        $PYTHON_CMD -m pip install -r requirements.txt
        
        if [ $? -ne 0 ]; then
            echo "❌ Error: Failed to install dependencies"
            exit 1
        fi
    fi
fi

# Check if Redis is running
echo "🔍 Checking Redis connection..."
if ! $PYTHON_CMD -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" 2>/dev/null; then
    echo "⚠️  Warning: Cannot connect to Redis server"
    echo "   Please ensure Redis is running on localhost:6379"
    echo "   Start Redis with: redis-server"
    echo ""
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Cannot connect to QuickDraw backend"
    echo "   Please ensure the backend is running on http://localhost:8000"
    echo "   Start backend with: cd ../backend && python -m uvicorn app:app --host 0.0.0.0 --port 8000"
    echo ""
fi

echo "🚀 Starting QuickDraw Dashboard..."
echo "   Dashboard will be available at: http://localhost:8501"
echo "   Press Ctrl+C to stop the dashboard"
echo ""

# Start Streamlit
if [ "$PYTHON_CMD" = "uv run" ]; then
    $PYTHON_CMD streamlit run app.py --server.address 0.0.0.0 --server.port 8501
else
    $PYTHON_CMD -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
fi