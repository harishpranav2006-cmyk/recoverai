"""
RecoverAI — API Version 1 Router Aggregator
============================================
Consolidates all v1 endpoint routers into a unified prefix `/api/v1`.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.v1.agent import router as agent_router
from backend.api.v1.analytics import router as analytics_router
from backend.api.v1.customers import router as customers_router
from backend.api.v1.decisions import router as decisions_router
from backend.api.v1.health import router as health_router
from backend.api.v1.ml import router as ml_router
from backend.api.v1.payments import router as payments_router
from backend.api.v1.recovery import router as recovery_router
from backend.api.v1.simulation import router as simulation_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(customers_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(recovery_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(simulation_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(decisions_router)
api_v1_router.include_router(ml_router)
