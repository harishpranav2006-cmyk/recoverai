"""
RecoverAI — Health & Readiness Endpoints (v1)
=============================================
Provides real-time health checks, liveness probes, and readiness verification.
"""

from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.config import settings
from backend.database import get_db
from backend.schemas.health import HealthResponse, LivenessResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["Health & Status"])


@router.get("", response_model=HealthResponse, summary="System Health Check")
def get_system_health(db: Session = Depends(get_db)) -> HealthResponse:
    """
    Returns complete system health, validating actual database connectivity and ML artifact presence.
    """
    # 1. Verify Database
    db_status = "connected"
    try:
        db.execute(text("SELECT 1")).scalar()
    except Exception:
        db_status = "disconnected"

    # 2. Verify ML Model Artifact
    ml_status = "available"
    model_file = settings.project_root / settings.model_path
    if not model_file.exists():
        ml_status = "unavailable"

    overall_status = "healthy" if db_status == "connected" and ml_status == "available" else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        ml_model=ml_status,
        llm_mode=settings.llm_provider,
        simulator="available",
        version=settings.app_version,
    )


@router.get("/live", response_model=LivenessResponse, summary="Liveness Probe")
def get_liveness() -> LivenessResponse:
    """
    Kubernetes/container liveness probe confirming process is responsive.
    """
    return LivenessResponse(status="alive", alive=True)


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Probe")
def get_readiness(db: Session = Depends(get_db)) -> ReadinessResponse:
    """
    Readiness probe validating whether critical dependencies (DB & ML model) are ready.
    """
    db_ok = False
    try:
        val = db.execute(text("SELECT 1")).scalar()
        db_ok = (val == 1)
    except Exception:
        db_ok = False

    ml_ok = (settings.project_root / settings.model_path).exists()

    is_ready = db_ok and ml_ok
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is not ready. Critical dependencies unavailable.",
        )

    return ReadinessResponse(
        status="ready",
        ready=True,
        database_connected=db_ok,
        ml_model_loaded=ml_ok,
    )
