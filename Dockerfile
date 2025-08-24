# Multi-stage Dockerfile for Voice Log
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=voice_log.py \
    FLASK_CONFIG=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos '' voicelog

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data uploads backups logs cache && \
    chown -R voicelog:voicelog /app

# Switch to non-root user
USER voicelog

# Expose port
EXPOSE 5010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5010/api/stats || exit 1

# Run the application
CMD ["python", "voice_log.py"]