# HackFlow Production Dockerfile for Google Cloud Run

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance folder and logs folder for Flask
RUN mkdir -p /app/instance /app/logs

# Set default environment variables
ENV PORT=8080
ENV FLASK_ENV=production
ENV FLASK_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Expose the port Cloud Run expects
EXPOSE 8080

# Health check for Cloud Run
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health/liveness || exit 1

# Run with gunicorn for production
# Using multiple workers based on CPU cores, timeout for slow requests
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "run:app"]