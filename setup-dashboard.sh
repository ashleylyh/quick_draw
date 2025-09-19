#!/bin/bash

# Script to set up QuickDraw with dashboard dependencies using uv

echo "🎨 Setting up QuickDraw with Dashboard Dependencies"
echo "=================================================="

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "📦 Installing base QuickDraw dependencies..."
uv sync

echo "📊 Installing dashboard dependencies..."
uv sync --extra dashboard

echo "✅ Installation complete!"
echo ""
echo "🚀 You can now run:"
echo "   Backend: uv run uvicorn backend.app:app --host 0.0.0.0 --port 8000"
echo "   Dashboard: cd dashboard && uv run streamlit run app.py"
echo ""
echo "📖 Or use the provided run scripts in the dashboard folder:"
echo "   cd dashboard && ./run.sh"