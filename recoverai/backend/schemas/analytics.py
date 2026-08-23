"""
RecoverAI — Analytics Pydantic Schemas
======================================
Contracts for revenue recovery KPIs, strategy benchmarks, failure breakdowns, and time-series trends.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsOverviewResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    total_customers: int
    total_payments: int
    total_failed_payments: int
    failed_payment_value: float
    recovered_payments: int
    recovered_value: float
    unrecovered_value: float
    recovery_rate: float
    recovery_rate_percentage: str
    retry_attempts: int
    active_recovery_cases: int
    currency: str = "INR"


class StrategyAnalyticsItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    strategy: str
    total_cases: int
    successful_recoveries: int
    recovered_value: float
    success_rate: float
    success_rate_percentage: str


class FailureAnalyticsItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    failure_reason: str
    total_failed: int
    recovered_count: int
    total_amount: float
    recovered_amount: float
    recovery_rate: float
    recovery_rate_percentage: str


class SegmentAnalyticsItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    segment: str
    total_failed_payments: int
    total_failed_value: float
    recovered_value: float
    recovery_rate: float
    recovery_rate_percentage: str


class TrendPoint(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    date: str
    failed_count: int
    failed_amount: float
    recovered_count: int
    recovered_amount: float
    recovery_rate: float


class TrendsAnalyticsResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    interval: str
    points: List[TrendPoint]
