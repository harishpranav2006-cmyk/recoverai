# RecoverAI — Autonomous AI Revenue Recovery Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29%2B-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-235%20Passing-brightgreen.svg)]()
[![Coverage](https://img.shields.io/badge/Coverage-84%25-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Status-Buildathon%20Submission%20Ready-brightgreen.svg)]()

> **Razorpay AI Buildathon Prototype Submission**  
> **Track:** *Autonomous AI Revenue Recovery for Recurring & High-Velocity Payment Failures*  
> **Environment:** *Synthetic Data • Deterministic Simulations • Zero Real Money Transactions*

### 🌐 Public Cloud Deployment Endpoints

```
LIVE DEMO:
[STREAMLIT URL AFTER DEPLOYMENT]

BACKEND API:
[RENDER URL AFTER DEPLOYMENT]

SWAGGER:
[RENDER URL]/docs
```

Please see the main codebase and comprehensive documentation in [`recoverai/`](file:///e:/education/razor%20pay%20buildthon/recoverai):

- **Full Project README**: [`recoverai/README.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/README.md)
- **Chronological Phase Walkthroughs**: [`recoverai/docs/PHASE_WALKTHROUGHS.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/PHASE_WALKTHROUGHS.md)
- **Pitch Package & Presentation Scripts**: [`recoverai/docs/pitch.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/pitch.md)
- **Comprehensive Technical Deep-Dive**: [`recoverai/docs/technical_deep_dive.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/technical_deep_dive.md)
- **Panel Interview & Q&A Preparation**: [`recoverai/docs/interview.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/interview.md)
- **Buildathon Submission Checklist**: [`recoverai/docs/submission_checklist.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/submission_checklist.md)
- **Deployment & Operations Guide**: [`recoverai/docs/deployment.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/deployment.md)
- **Production Readiness & Roadmap**: [`recoverai/docs/production_readiness.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/production_readiness.md)
- **Testing & QA Strategy**: [`recoverai/docs/testing.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/testing.md)
- **Reliability & Fault Tolerance**: [`recoverai/docs/reliability.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/reliability.md)
- **Dashboard User Guide**: [`recoverai/docs/dashboard.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/dashboard.md)
- **5-Minute Buildathon Pitch Guide**: [`recoverai/docs/demo.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/demo.md)
- **Production REST API Documentation**: [`recoverai/docs/api.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/api.md)
- **System Architecture Specification**: [`recoverai/docs/architecture.md`](file:///e:/education/razor%20pay%20buildthon/recoverai/docs/architecture.md)

### Cloud Deployment (Render + Streamlit Community Cloud)

1. **FastAPI Backend on Render (Docker Runtime)**:
   - **Repository**: `harishpranav2006-cmyk/recoverai`
   - **Runtime**: `Docker`
   - **Dockerfile Path**: `./Dockerfile` (or Root Directory: `recoverai`, Dockerfile: `Dockerfile`)
   - **Health Check Path**: `/api/v1/health/live`
   - **Auto-Provision**: Or click **New +** → **Blueprint** pointing to `render.yaml`.

2. **Frontend Dashboard on Streamlit Community Cloud**:
   - **Repository**: `harishpranav2006-cmyk/recoverai`
   - **Main file path**: `recoverai/dashboard/app.py`
   - **App Settings → Secrets**:
     ```toml
     RECOVERAI_API_URL = "https://<your-render-service>.onrender.com/api/v1"
     API_TIMEOUT_SECONDS = 25
     ```

---

### Quickstart with Docker Compose
```bash
cd recoverai
docker compose up --build
```
- Dashboard: [http://localhost:8501](http://localhost:8501)
- Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Local Python Quickstart
```bash
cd recoverai
pip install -r requirements.txt
python scripts/setup_demo.py

# Terminal 1: Backend REST API
uvicorn backend.main:app --reload

# Terminal 2: Streamlit Fintech Dashboard
streamlit run dashboard/app.py
```
