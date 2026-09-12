# ==============================================================================
# Dockerfile for RailBlock AI - Indian Railways Automatic Block Planning System
# Production-ready, lightweight, secure Python container
# ==============================================================================

FROM python:3.11-slim AS builder

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final minimal production image
FROM python:3.11-slim

WORKDIR /app

# Copy installed wheels from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Copy application files
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py .
COPY README.md .

# Expose production port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/network')" || exit 1

# Production command with Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
