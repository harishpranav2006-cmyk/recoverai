# ==============================================================================
# RecoverAI — Multi-Service Production Containerfile
# ==============================================================================
# Base Python image
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system utilities needed for healthcheck (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and artifacts
COPY backend/ ./backend/
COPY agent/ ./agent/
COPY ml/ ./ml/
COPY services/ ./services/
COPY simulator/ ./simulator/
COPY dashboard/ ./dashboard/
COPY data/ ./data/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY recoverai.db* ./

# Create unprivileged user for security hardening
RUN useradd -m -u 1001 appuser && \
    chown -R appuser:appuser /app

USER appuser

# ------------------------------------------------------------------------------
# Target: Backend REST API (FastAPI)
# ------------------------------------------------------------------------------
FROM base AS backend
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/live || exit 1

ENV PORT=8000
CMD ["sh", "-c", "exec python -m uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# ------------------------------------------------------------------------------
# Target: Frontend Dashboard (Streamlit)
# ------------------------------------------------------------------------------
FROM base AS frontend
EXPOSE 8501
ENV API_BASE_URL="http://backend:8000/api/v1"
HEALTHCHECK --interval=20s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
