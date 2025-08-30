# Frontend-only Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy frontend files
COPY frontend/ ./frontend/
COPY frontend_server.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Set default port
ENV FRONTEND_PORT=8005

# Expose port
EXPOSE 8005

# Health check for frontend
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${FRONTEND_PORT:-8005}/ || exit 1

# Run frontend server
CMD ["sh", "-c", "python frontend_server.py --port ${FRONTEND_PORT:-8005}"]
