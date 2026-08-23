"""
RecoverAI — Production FastAPI Backend Application
===================================================
Production-style REST API exposing ML intelligence, autonomous recovery agents,
payment simulation, revenue analytics, customer profiles, and health checks.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.analytics import router as legacy_analytics_router
from backend.api.recovery import router as legacy_recovery_router
from backend.api.v1 import api_v1_router
from backend.config import settings
from backend.errors import register_error_handlers
from backend.middleware import RequestIdMiddleware

tags_metadata = [
    {"name": "Health & Status", "description": "System health, liveness, and readiness probes."},
    {"name": "Customers", "description": "Customer profiles, segment classification, and transaction history."},
    {"name": "Payments", "description": "Payment records, failure diagnostics, and lifecycle timelines."},
    {"name": "Recovery & Decision Core", "description": "Decision Engine policy evaluation, recovery queues, and outcomes."},
    {"name": "AI Recovery Agent", "description": "Autonomous multi-tool recovery agent execution (single & batch)."},
    {"name": "Payment & Outreach Simulator", "description": "Deterministic simulation of payment gateways and customer outreach."},
    {"name": "Revenue Analytics", "description": "Empirical recovery KPIs, strategy benchmarks, and time-series trends."},
    {"name": "Decision History", "description": "Historical audit log of all AI recovery decisions."},
    {"name": "Machine Learning & Explainability", "description": "Calibrated ML probability inference and SHAP factor attribution."},
]

app = FastAPI(
    title="RecoverAI — Autonomous AI Revenue Recovery API",
    description="""
# RecoverAI REST API

Autonomous AI-powered revenue recovery platform designed for high-velocity subscription and recurring payment failures.

### Key Capabilities:
- **Calibrated ML Recovery Prediction**: Zero-leakage probability scoring with SHAP factor explainability.
- **14-Step Deterministic Decision Engine**: Enforces validated 3-tier recovery policies and strict safety rules.
- **Autonomous Multi-Tool Agent**: Orchestrates data queries, decisions, and privacy-safe customer communications.
- **Deterministic Payment & Outreach Simulator**: Models realistic gateway physics, retry fatigue, and customer responses.
- **Empirical Revenue Analytics**: Aggregates real financial recovery metrics, strategy conversion, and time-series trends.

> **SAFETY NOTICE**: All simulation endpoints execute in a simulated, non-financial sandbox environment. Zero real payment transactions or real messages are dispatched.
    """,
    version=settings.app_version,
    openapi_tags=tags_metadata,
)

# 1. Register Request ID & Performance Logging Middleware
app.add_middleware(RequestIdMiddleware)

# 2. Register CORS Middleware
allowed_origins = [orig.strip() for orig in settings.cors_allowed_origins.split(",") if orig.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register Centralized Error Envelopes
register_error_handlers(app)

# 4. Mount API v1 Routes
app.include_router(api_v1_router)

# 5. Mount Legacy / Backward-Compatible Routes
app.include_router(legacy_recovery_router)
app.include_router(legacy_analytics_router)


@app.get("/", tags=["Health & Status"], summary="RecoverAI API Root")
def root_index():
    """
    Root welcome endpoint returning platform metadata and links to interactive OpenAPI documentation.
    """
    return {
        "message": "Welcome to RecoverAI — Autonomous AI Revenue Recovery API",
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/api/v1/health",
        "analytics": "/api/v1/analytics/overview",
        "demo_mode": settings.demo_mode,
    }


@app.get("/health", tags=["Health & Status"], summary="Legacy Root Health Check")
def root_health_check():
    """
    Root health check endpoint for backward compatibility.
    """
    return {
        "status": "healthy",
        "app": "RecoverAI",
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
        "llm_provider": settings.llm_provider,
        "is_llm_available": settings.is_llm_available,
    }
