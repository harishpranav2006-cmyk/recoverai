"""
RecoverAI — Payment Pydantic Schemas
====================================
Contracts for payment records, payment inspection details, and chronological lifecycle timelines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PaymentResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    customer_id: str
    timestamp: datetime
    amount: float
    currency: str
    payment_method: str
    payment_method_type: str
    device_type: str
    is_subscription: bool
    subscription_type: Optional[str] = None
    payment_success: bool
    failure_reason: Optional[str] = None
    failure_category: Optional[str] = None
    retry_count: int
    recovered_after_failure: Optional[bool] = None
    recovered_amount: Optional[float] = None
    recovery_time_hours: Optional[float] = None
    demo_scenario: Optional[str] = None


class PaymentDetailResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_lifetime_value: float
    timestamp: datetime
    amount: float
    currency: str
    payment_method: str
    payment_method_type: str
    device_type: str
    is_subscription: bool
    subscription_type: Optional[str] = None
    subscription_age_days: int
    payment_success: bool
    failure_reason: Optional[str] = None
    failure_category: Optional[str] = None
    failure_temporary: Optional[bool] = None
    retry_count: int
    recovered_after_failure: Optional[bool] = None
    recovered_amount: Optional[float] = None
    recovery_time_hours: Optional[float] = None
    demo_scenario: Optional[str] = None
    latest_prediction: Optional[Dict[str, Any]] = None
    latest_decision: Optional[Dict[str, Any]] = None
    latest_outcome: Optional[Dict[str, Any]] = None
    recovery_case_status: Optional[str] = None


class TimelineEvent(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    event_type: str  # PAYMENT_FAILURE, ML_PREDICTION, AGENT_DECISION, RETRY_ATTEMPT, OUTREACH_DISPATCH, RECOVERY_OUTCOME
    timestamp: datetime
    title: str
    description: str
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentTimelineResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    customer_id: str
    amount: float
    current_status: str
    total_events: int
    events: List[TimelineEvent]
