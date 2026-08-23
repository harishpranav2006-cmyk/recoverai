"""
RecoverAI — ML Prediction Schemas
==================================
Contracts for inference queries, status health, and feature attributions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MLFactor(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    feature: str
    impact: str  # positive or negative
    importance: float
    description: str


class MLPredictResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    recovery_probability: float = Field(..., ge=0.0, le=1.0)
    prediction: int  # 1 or 0
    model_version: str
    calibrated: bool
    factors: List[MLFactor] = Field(default_factory=list)


class MLStatusResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    model_loaded: bool
    model_version: str
    calibrated: bool
    feature_count: int
    features: List[str]
    artifact_paths: Dict[str, str]
