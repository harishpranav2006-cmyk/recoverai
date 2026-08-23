"""
RecoverAI — Health & Readiness Schemas
======================================
Contracts for system health checks, liveness probes, and readiness verification.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: str
    database: str
    ml_model: str
    llm_mode: str
    simulator: str
    version: str


class LivenessResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: str
    alive: bool


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: str
    ready: bool
    database_connected: bool
    ml_model_loaded: bool
