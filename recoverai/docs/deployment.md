# RecoverAI — Deployment, Containerization & Operation Guide

## 1. Overview

RecoverAI is packaged for multi-modal execution:
1. **Local Python Execution**: High-velocity development mode using `uvicorn` and `streamlit`.
2. **Multi-Service Docker Compose**: Containerized multi-service deployment orchestrating FastAPI (`recoverai_backend`) and Streamlit (`recoverai_frontend`) with health checks, persistent volumes, and isolated networking.

```
                            DOCKER COMPOSE DEPLOYMENT ARCHITECTURE
                            
                 ┌─────────────────────────────────────────────────────────┐
                 │                   Host Machine / VM                     │
                 │                                                         │
                 │   Port 8501                     Port 8000               │
                 │       │                             │                   │
                 │       ▼                             ▼                   │
                 │ ┌──────────────┐              ┌──────────────┐          │
                 │ │  Streamlit   │              │   FastAPI    │          │
                 │ │  (Frontend)  │───HTTP/v1───►│  (Backend)   │          │
                 │ └──────────────┘              └──────┬───────┘          │
                 │   recoverai_net                      │                  │
                 │                                      │ Mounts           │
                 │                                      ▼                  │
                 │                             ┌─────────────────┐         │
                 │                             │  recoverai.db   │ (Vol)   │
                 │                             │  ml/artifacts/  │ (ro)    │
                 │                             └─────────────────┘         │
                 └─────────────────────────────────────────────────────────┘
```

---

## 2. Quickstart with Docker Compose

### Prerequisites
- Docker Engine 20.10+ and Docker Compose v2+
- Port `8000` (FastAPI REST API) and Port `8501` (Streamlit Dashboard) available.

### Step 1: Clone & Navigate
```bash
git clone <repository_url>
cd recoverai
```

### Step 2: Environment Configuration
Copy the provided `.env.example` template:
```bash
cp .env.example .env
```

### Step 3: Build & Start Multi-Service Containers
```bash
docker compose up --build
```
*To run in detached background mode:*
```bash
docker compose up -d
```

### Step 4: Access Services
- **Streamlit Fintech Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI Alternative Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Liveness Health Probe**: [http://localhost:8000/api/v1/health/live](http://localhost:8000/api/v1/health/live)

---

## 3. Local Development Startup (Without Docker)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database & Verify Environment
```bash
python scripts/setup_demo.py
```

### Step 3: Start Backend API (Terminal 1)
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Start Streamlit Dashboard (Terminal 2)
```bash
streamlit run dashboard/app.py
```

---

## 4. Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Execution environment (`development`, `production`). |
| `DATABASE_URL` | `sqlite:///./recoverai.db` | Database connection string (SQLite or PostgreSQL). |
| `HOST` | `0.0.0.0` | Server bind host. |
| `PORT` | `8000` | FastAPI server port. |
| `API_BASE_URL` | `http://localhost:8000/api/v1` | Backend URL consumed by Streamlit (use `http://backend:8000/api/v1` in Docker). |
| `SIMULATION_MODE` | `true` | Enforces simulation sandbox rules (no real payments or messages). |
| `LLM_PROVIDER` | `mock` | AI reasoning provider (`mock` for 100% deterministic offline execution, or `openai`). |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8501,...` | Comma-separated list of allowed browser origins. |
| `LOG_LEVEL` | `INFO` | Application log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `MODEL_PATH` | `ml/artifacts/model.joblib` | Path to production Calibrated Logistic Regression model. |
| `PREPROCESSOR_PATH` | `ml/artifacts/preprocessor.joblib` | Path to Scikit-Learn feature preprocessor. |
| `SHAP_PATH` | `ml/artifacts/shap_explainer.joblib` | Path to SHAP explainer artifact. |

---

## 5. Persistent Storage & ML Artifacts

1. **Database Volume (`recoverai.db`)**:
   - In `docker-compose.yml`, `./recoverai.db` is mounted directly into `/app/recoverai.db`.
   - Data persists across container restarts, stops, and rebuilds.
2. **ML Artifacts Mount (`ml/artifacts`)**:
   - Mounted as read-only (`:ro`) into `/app/ml/artifacts`.
   - The calibrated ML model, feature preprocessor, and SHAP explainer are loaded into memory on startup without requiring retraining.

---

## 6. Health Checks & Startup Ordering

RecoverAI defines container health probes:
- **Backend Liveness**: `curl -f http://localhost:8000/api/v1/health/live` (checked every 15s).
- **Backend Readiness**: `curl -f http://localhost:8000/api/v1/health/ready` (validates database query & ML model loading).
- **Startup Order Enforcement**: In `docker-compose.yml`, `frontend` declares:
  ```yaml
  depends_on:
    backend:
      condition: service_healthy
  ```
  This guarantees that Streamlit will never attempt to connect before FastAPI is ready to receive requests.

---

## 7. Container Lifecycle & Graceful Shutdown

- **Stop Containers**:
  ```bash
  docker compose stop
  ```
- **Stop and Remove Containers & Networks**:
  ```bash
  docker compose down
  ```
- **View Live Container Logs**:
  ```bash
  docker compose logs -f
  ```
- **Inspect Specific Service Logs**:
  ```bash
  docker compose logs -f backend
  docker compose logs -f frontend
  ```
