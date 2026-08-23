"""
RecoverAI — Customer Pydantic Schemas
======================================
Contracts for customer listings, customer profiles, and customer payment histories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    name: str
    email: str
    region: str
    segment: str
    lifetime_value: float
    age_days: int
    created_at: datetime


class CustomerDetailResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    name: str
    email: str
    region: str
    segment: str
    lifetime_value: float
    age_days: int
    created_at: datetime
    is_vip: bool
    total_transactions: int
    successful_payments: int
    failed_payments: int
    recovered_payments: int
    historical_recovery_rate: float
    total_spend: float
    unrecovered_debt: float


class CustomerHistoryItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    timestamp: datetime
    amount: float
    currency: str
    payment_method: str
    payment_success: bool
    failure_reason: Optional[str] = None
    recovered_after_failure: Optional[bool] = None
    recovered_amount: Optional[float] = None
    retry_count: int


class CustomerHistoryResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    customer_id: str
    customer_name: str
    total_payments: int
    successful_payments: int
    failed_payments: int
    payments: List[CustomerHistoryItem]
