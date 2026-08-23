"""
RecoverAI — Recovery & Queue Schemas
====================================
Contracts for recovery cases, queue items, and workflow execution.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.decision import DecisionResponse, ReasonCode, RecommendedAction, RecoveryStrategy, RecoveryTier


class RecoveryQueueItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    customer_id: str
    customer_name: str
    customer_segment: str
    customer_lifetime_value: float
    is_vip: bool
    amount: float
    currency: str
    failure_reason: str
    failure_category: Optional[str] = None
    retry_count: int
    retry_eligible: bool
    timestamp: datetime
    recovery_probability: float
    tier: RecoveryTier
    strategy: RecoveryStrategy
    recommended_action: RecommendedAction
    human_review_required: bool
    priority_score: float


class RecoveryQueueResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    total_pending: int
    items: List[RecoveryQueueItem]


class RecoveryOutcomeResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    case_id: str
    case_status: str
    amount: float
    recovered_amount: float
    is_recovered: bool
    strategy_used: Optional[str] = None
    timestamp: str
    simulated: bool = True
