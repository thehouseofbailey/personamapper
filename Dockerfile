# Multi-stage build for PersonaMap

# Base image
FROM python:3.9-slim as base

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py \
    FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Copy production requirements first for caching
COPY requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Production stage
FROM base as production

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create necessary directories and set permissions BEFORE copying code
RUN mkdir -p /app/instance /app/logs && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser run.py config.py start.sh ./
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser migrations/ ./migrations/

# Ensure instance directory is writable by appuser
RUN chown -R appuser:appuser /app/instance && chmod -R 755 /app/instance

# Set executable permissions
RUN chmod +x start.sh

# Switch to non-root
USER appuser

# Cloud Run expects this port
EXPOSE 8080

# Default command - use startup script
CMD ["./start.sh"]
