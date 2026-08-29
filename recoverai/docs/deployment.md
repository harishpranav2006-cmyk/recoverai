# RecoverAI — Complete Deployment, Cloud Operations & Containerization Guide

This document provides complete, step-by-step instructions for deploying and running RecoverAI in both local development environments and cloud production platforms (Render + Streamlit Community Cloud).

---

## 1. Cloud Deployment Architecture

```
                USER (Judge / Evaluator)
                           │
                           ▼
        Streamlit Community Cloud (Frontend)
          (dashboard/app.py • 7 Interactive Pages)
                           │
                           │ HTTPS / REST (JSON)
                           ▼
              Render Web Service (Backend)
         (FastAPI / Uvicorn • Dynamic $PORT • 0.0.0.0)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
    ML Inference    Decision Engine    Payment Simulator
(Calibrated Logistic  (14-Step Safe     (Realistic Gateway
  Regression + SHAP)    Policy Matrix)      Physics Sandbox)
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
             SQLite Prototype Database
       (recoverai.db • Auto-Initialized & Seeded)
```

### Distinction Between Real vs. Simulated Systems:

| Subsystem | Execution Nature | Description |
| :--- | :--- | :--- |
| **REST API (`/api/v1`)** | **REAL** | True FastAPI HTTP service handling authentication, routing, validation, error envelopes, and latency logging. |
| **ML Inference** | **REAL** | True Scikit-Learn Calibrated Logistic Regression scoring 24 zero-leakage payment features. |
| **SHAP Explainability** | **REAL** | True mathematical Tree/Linear SHAP computing additive feature contributions per prediction. |
| **Decision Engine** | **REAL** | True 14-step deterministic policy matrix classifying payments into 3 risk tiers with hard safety blocks. |
| **Revenue Analytics** | **REAL** | Dynamic SQL aggregations calculating recovered volume, conversion rates, and time-series trends. |
| **Fintech Dashboard** | **REAL** | Multi-page Streamlit application with live API polling, interactive charts, and user controls. |
| **Gateway Execution** | *SIMULATED* | Realistic sandbox physics modeling issuer decline codes, network timeouts, and retry fatigue without processing real currency. |
| **Customer Outreach** | *SIMULATED* | Privacy-safe, templated WhatsApp/SMS/Email notifications generated and recorded in audit logs without dispatching real communications. |

---

## 2. Step-by-Step Cloud Deployment

### Step A: Push Code to GitHub
Ensure the latest codebase, including trained ML artifacts in `ml/artifacts/` and deployment configuration, is pushed to your GitHub repository:
```bash
git add .
git commit -m "feat: prepare RecoverAI for cloud deployment"
git push origin main
```
Repository: `https://github.com/harishpranav2006-cmyk/recoverai.git`

---

### Step B: Deploy FastAPI Backend on Render (Docker Runtime)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Web Service** (or click **New +** → **Blueprint** selecting `render.yaml`).
3. Connect your GitHub repository: `harishpranav2006-cmyk/recoverai`.
4. Configure service settings:
   - **Name**: `recoverai-api`
   - **Region**: Oregon (or nearest available)
   - **Branch**: `main`
   - **Root Directory**: `.` (leave blank / default root)
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`
   - **Plan Type**: `Free`
5. Configure Environment Variables:
   - `APP_ENV`: `production`
   - `DEMO_MODE`: `true`
   - `SIMULATION_MODE`: `true`
   - `LLM_PROVIDER`: `mock`
   - `DATABASE_URL`: `sqlite:///./recoverai.db`
   - `CORS_ALLOWED_ORIGINS`: `https://share.streamlit.io,https://*.streamlit.app,http://localhost:8501`
   - `PORT`: (injected automatically by Render)
6. Click **Create Web Service**.
7. Once deployed, copy your public service URL (e.g., `https://recoverai-api.onrender.com`).

---

### Step C: Deploy Streamlit Dashboard on Streamlit Community Cloud

1. Log in to [Streamlit Community Cloud](https://share.streamlit.io).
2. Click **New app**.
3. Select your repository: `harishpranav2006-cmyk/recoverai`.
4. Set **Branch** to `main`.
5. Set **Main file path** to:
   ```
   recoverai/dashboard/app.py
   ```
   *(Note: Since the application lives in the `recoverai/` directory within the repository, specify `recoverai/dashboard/app.py`)*
6. Click **Advanced settings...** → **Secrets**.
7. Paste your Render backend URL into the secrets configuration:
   ```toml
   RECOVERAI_API_URL = "https://<your-service>.onrender.com/api/v1"
   API_TIMEOUT_SECONDS = 25
   ```
8. Click **Save**, then click **Deploy!**.

---

## 3. Verification & Live Health Probes

### Verifying the Render Backend
Execute following health checks against your public Render URL:

```bash
# 1. Root Welcome & Metadata
curl -s https://<your-render-url>.onrender.com/

# 2. Comprehensive Health Probe (DB + ML Status)
curl -s https://<your-render-url>.onrender.com/api/v1/health

# 3. Liveness Probe (Kubernetes/Container)
curl -s https://<your-render-url>.onrender.com/api/v1/health/live

# 4. Readiness Probe (Critical Dependencies)
curl -s https://<your-render-url>.onrender.com/api/v1/health/ready

# 5. Interactive OpenAPI Documentation
# Open in browser: https://<your-render-url>.onrender.com/docs
```

Expected output for `/api/v1/health`:
```json
{
  "status": "healthy",
  "database": "connected",
  "ml_model": "available",
  "llm_mode": "mock",
  "simulator": "available",
  "version": "1.0.0"
}
```

### Verifying the Streamlit Dashboard
1. Open your Streamlit Cloud URL (e.g., `https://recoverai.streamlit.app`).
2. Verify the **Sidebar System Status** card displays:
   - `🟢 REST API: OK`
   - `🟢 ML Model: Loaded`
   - `🟢 Database: 50K Records`
3. Navigate to **⚙️ System Diagnostics**:
   - Verify all 5 subsystems (Frontend, Backend API, Database, ML Model, Simulator) display `🟢 READY` / `🟢 HEALTHY`.
   - Click the **Open Swagger UI** button to confirm it opens the live documentation on Render.

---

## 4. Local Execution Options

### Option A: Multi-Service Docker Compose
```bash
# Build and start all services (FastAPI on 8000, Streamlit on 8501)
docker compose up --build

# Run in background (detached)
docker compose up -d

# Stop containers
docker compose down
```

### Option B: Local Python Startup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run one-time environment verification and schema setup
python scripts/setup_demo.py

# 3. Start Backend REST API (Terminal 1)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 4. Start Streamlit Dashboard (Terminal 2)
streamlit run dashboard/app.py
```

---

## 5. Environment Variables & Secrets Reference

| Variable | Scope | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Backend | `production` | Deployment environment identifier. |
| `PORT` | Backend | `8000` | Bind port injected by Render / container host. |
| `HOST` | Backend | `0.0.0.0` | Bind host IP for server listening. |
| `DATABASE_URL` | Backend | `sqlite:///./recoverai.db` | SQLAlchemy connection string. |
| `CORS_ALLOWED_ORIGINS` | Backend | `http://localhost:8501,...` | Permitted origins. Regex automatically allows `https://*.streamlit.app`. |
| `SIMULATION_MODE` | Backend | `true` | Enforces simulation sandbox safety constraints. |
| `LLM_PROVIDER` | Backend | `mock` | `mock` (deterministic offline) or `openai`. |
| `RECOVERAI_API_URL` | Frontend | `http://localhost:8000/api/v1` | URL consumed by Streamlit (configured in Streamlit Secrets). |
| `API_TIMEOUT_SECONDS` | Frontend | `15` | Network request timeout in seconds. |

---

## 6. Troubleshooting & Common Issues

### 1. "RecoverAI API is currently unavailable" on Streamlit Cloud
- **Cause**: Render free tier services spin down after 15 minutes of inactivity.
- **Solution**: The first request wakes the service, taking 30–50 seconds. Click **🔄 Refresh System Status** or **🔄 Retry Connection** in the dashboard once the backend has finished booting.
- **Check**: Open your Render backend URL directly in your browser at `/api/v1/health`.

### 2. Streamlit Cloud Cannot Reach Backend (CORS / Network Error)
- Ensure `RECOVERAI_API_URL` in Streamlit Secrets is set to the HTTPS URL of your Render service ending in `/api/v1`:
  ```toml
  RECOVERAI_API_URL = "https://<your-service>.onrender.com/api/v1"
  ```
- Ensure there is no trailing slash after `/api/v1`.

### 3. Database is Empty on Fresh Deploy
- RecoverAI includes safe auto-initialization. On startup, FastAPI detects missing/empty database tables and automatically seeds 5,000 customers and 50,000 payments deterministically (`seed=42`). No manual database migration or seed commands are required.

---

## 7. Buildathon Limitations & Production Roadmap

- **Single-Node SQLite**: For the Razorpay AI Buildathon, SQLite provides a self-contained, deterministic database with zero infrastructure dependencies. In enterprise production, this should be replaced with managed AWS Aurora PostgreSQL or Google Cloud SQL with read replicas and PgBouncer connection pooling.
- **Stateless Cloud Worker Storage**: On free-tier platforms without persistent disks, ephemeral storage will re-seed data automatically if the container is destroyed. Seed records are completely deterministic and idempotent.
- **Synthetic Data**: All transaction records, customer details, and card profiles are generated synthetically. Zero real card numbers (PANs) or customer PII are stored or processed.
