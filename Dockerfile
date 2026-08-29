# ==============================================================================
# RecoverAI — Production Dockerfile for Render Web Service
# ==============================================================================
# Builds and runs the RecoverAI FastAPI REST API service on Render.
# Compatible with both Root Context (.) and subfolder application structure.
# ==============================================================================

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies (curl for container healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application packages, services, and ML artifacts into /app
COPY recoverai/backend/ ./backend/
COPY recoverai/agent/ ./agent/
COPY recoverai/ml/ ./ml/
COPY recoverai/services/ ./services/
COPY recoverai/simulator/ ./simulator/
COPY recoverai/dashboard/ ./dashboard/
COPY recoverai/data/ ./data/
COPY recoverai/docs/ ./docs/
COPY recoverai/scripts/ ./scripts/

# Security: Create non-root user
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose default port
EXPOSE 8000

# Container liveness health check probe
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

# Render injects dynamic $PORT; default to 8000 for local testing
ENV PORT=8000
CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
