# QuickDraw Multi-Service Dockerfile
# This Dockerfile creates a single image that can run all QuickDraw services
FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_CACHE_DIR=/tmp/uv-cache \
    PATH="/app/.venv/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Set working directory
WORKDIR /app

# Control optional dependency installation (e.g., dashboard extras)
ARG INSTALL_DASHBOARD_EXTRAS=false

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN if [ "$INSTALL_DASHBOARD_EXTRAS" = "true" ]; then \
            uv sync --extra dashboard; \
        else \
            uv sync; \
        fi

# Copy the entire application
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads/screenshots

# Make scripts executable
RUN chmod +x scripts/*.sh

# Expose all required ports
EXPOSE 3000 8000 8501

# Default command - can be overridden in docker-compose
CMD ["bash", "-c", "echo 'Use docker-compose to start services'"]