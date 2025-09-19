@echo off
REM QuickDraw Dashboard Startup Script for Windows

echo 🎨 QuickDraw Analytics Dashboard
echo =================================

REM Check if we're in the dashboard directory
if not exist "app.py" (
    echo ❌ Error: Please run this script from the dashboard directory
    echo Usage: cd dashboard && run.bat
    pause
    exit /b 1
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo 🐍 Using Python:
python --version

REM Check if Streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    python -m pip install -r requirements.txt
    
    if errorlevel 1 (
        echo ❌ Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if Redis is running
echo 🔍 Checking Redis connection...
python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: Cannot connect to Redis server
    echo    Please ensure Redis is running on localhost:6379
    echo.
)

REM Check if backend is running
echo 🔍 Checking backend connection...
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Warning: Cannot connect to QuickDraw backend
    echo    Please ensure the backend is running on http://localhost:8000
    echo.
)

echo 🚀 Starting QuickDraw Dashboard...
echo    Dashboard will be available at: http://localhost:8501
echo    Press Ctrl+C to stop the dashboard
echo.

REM Start Streamlit
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501