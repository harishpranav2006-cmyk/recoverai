"""
RecoverAI — Analytics Endpoints (v1)
====================================
Exposes empirical revenue metrics, strategy breakdowns, failure statistics, and time-series trends.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.payment import Payment
from backend.schemas.analytics import (
    AnalyticsOverviewResponse,
    FailureAnalyticsItem,
    SegmentAnalyticsItem,
    StrategyAnalyticsItem,
    TrendPoint,
    TrendsAnalyticsResponse,
)
from services.analytics import (
    calculate_recovery_by_failure_reason,
    calculate_recovery_by_segment,
    calculate_recovery_by_strategy,
    calculate_recovery_metrics,
)

router = APIRouter(prefix="/analytics", tags=["Revenue Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Get Overview KPIs")
def get_analytics_overview(db: Session = Depends(get_db)) -> AnalyticsOverviewResponse:
    """
    Returns complete high-level revenue and recovery metrics calculated dynamically from database records.
    """
    metrics = calculate_recovery_metrics(db=db)
    return AnalyticsOverviewResponse(**metrics)


@router.get("/recovery", summary="Get Recovery KPIs")
def get_recovery_kpis(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns empirical revenue recovery metrics and failure population statistics.
    """
    return calculate_recovery_metrics(db=db)


@router.get("/by-strategy", response_model=List[StrategyAnalyticsItem], summary="Recovery Metrics by Strategy")
def get_recovery_by_strategy_endpoint(db: Session = Depends(get_db)) -> List[StrategyAnalyticsItem]:
    """
    Returns recovery attempt volume and conversion rate grouped by recovery strategy.
    """
    raw_list = calculate_recovery_by_strategy(db=db)
    return [StrategyAnalyticsItem(**item) for item in raw_list]


@router.get("/by-failure", response_model=List[FailureAnalyticsItem], summary="Recovery Metrics by Failure Reason")
def get_recovery_by_failure_endpoint(db: Session = Depends(get_db)) -> List[FailureAnalyticsItem]:
    """
    Returns recovery rates and recovered revenue broken down by initial transaction failure reason.
    """
    raw_list = calculate_recovery_by_failure_reason(db=db)
    return [FailureAnalyticsItem(**item) for item in raw_list]


@router.get("/by-segment", response_model=List[SegmentAnalyticsItem], summary="Recovery Metrics by Customer Segment")
def get_recovery_by_segment_endpoint(db: Session = Depends(get_db)) -> List[SegmentAnalyticsItem]:
    """
    Returns recovery volume and recovery rate segmented by customer tier (free_trial, basic, premium, enterprise).
    """
    raw_list = calculate_recovery_by_segment(db=db)
    return [SegmentAnalyticsItem(**item) for item in raw_list]


@router.get("/trends", response_model=TrendsAnalyticsResponse, summary="Time-Series Recovery Trends")
def get_recovery_trends(
    interval: str = Query("daily", description="Time interval: daily or monthly"),
    db: Session = Depends(get_db),
) -> TrendsAnalyticsResponse:
    """
    Returns structured time-series trend data of failed volume vs recovered volume for charts.
    """
    payments = (
        db.query(Payment)
        .filter(Payment.payment_success == False)
        .order_by(Payment.timestamp.asc())
        .all()
    )

    trend_buckets: Dict[str, Dict[str, Any]] = {}

    for p in payments:
        date_key = p.timestamp.strftime("%Y-%m-%d") if interval == "daily" else p.timestamp.strftime("%Y-%m")
        if date_key not in trend_buckets:
            trend_buckets[date_key] = {
                "date": date_key,
                "failed_count": 0,
                "failed_amount": 0.0,
                "recovered_count": 0,
                "recovered_amount": 0.0,
            }

        trend_buckets[date_key]["failed_count"] += 1
        trend_buckets[date_key]["failed_amount"] += float(p.amount)

        if p.recovered_after_failure:
            trend_buckets[date_key]["recovered_count"] += 1
            trend_buckets[date_key]["recovered_amount"] += float(p.recovered_amount or p.amount)

    points: List[TrendPoint] = []
    for date_key in sorted(trend_buckets.keys()):
        b = trend_buckets[date_key]
        rec_rate = (b["recovered_amount"] / b["failed_amount"]) if b["failed_amount"] > 0 else 0.0
        points.append(
            TrendPoint(
                date=b["date"],
                failed_count=b["failed_count"],
                failed_amount=round(b["failed_amount"], 2),
                recovered_count=b["recovered_count"],
                recovered_amount=round(b["recovered_amount"], 2),
                recovery_rate=round(rec_rate, 4),
            )
        )

    return TrendsAnalyticsResponse(interval=interval, points=points)
