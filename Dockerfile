# Multi‑stage Dockerfile for Daemon‑pmac

# ---------- Builder stage ----------
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements for caching
COPY requirements.txt .

# Install Python dependencies into the builder image
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Runtime stage ----------
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copy application source code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p backups logs data && \
    chmod 755 data backups logs

# Create non‑root user for production (commented out for CI)
# RUN useradd --create-home --shell /bin/bash appuser && \
#     chown -R appuser:appuser /app

# Health‑check (Docker)
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8004}/health || exit 1

# Expose application port (default 8004)
ENV PORT=8004
EXPOSE 8004

# Default command to run the FastAPI app
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8004}"]
