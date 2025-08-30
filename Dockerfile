FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories and ensure proper permissions
RUN mkdir -p backups logs data && \
    chmod 755 data backups logs

# Create non-root user (use appuser to avoid conflict with existing daemon user)
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Create a script to fix volume permissions at runtime
RUN echo '#!/bin/bash' > /app/fix-permissions.sh && \
    echo 'if [ -d /app/data ]; then' >> /app/fix-permissions.sh && \
    echo '  chown -R appuser:appuser /app/data /app/logs /app/backups 2>/dev/null || true' >> /app/fix-permissions.sh && \
    echo '  chmod -R 755 /app/data /app/logs /app/backups 2>/dev/null || true' >> /app/fix-permissions.sh && \
    echo 'fi' >> /app/fix-permissions.sh && \
    echo 'exec "$@"' >> /app/fix-permissions.sh && \
    chmod +x /app/fix-permissions.sh && \
    chown appuser:appuser /app/fix-permissions.sh

USER appuser

# Set default port as environment variable
ENV PORT=8004

# Expose port (can be overridden via environment)
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8004}/health || exit 1

# Command to run the application
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8004}"]
