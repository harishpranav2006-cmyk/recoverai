"""
RecoverAI — Revenue Analytics API Routes
========================================
Endpoints exposing empirical revenue recovery KPIs, strategy performance,
failure breakdown, and customer segment recovery metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from services.analytics import (
    calculate_recovery_by_failure_type,
    calculate_recovery_by_segment,
    calculate_recovery_by_strategy,
    calculate_recovery_metrics,
)

router = APIRouter(prefix="/analytics", tags=["Revenue Analytics"])


@router.get("/recovery")
def get_overall_recovery_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns aggregate recovery KPIs: failed value, recovered value, unrecovered value, and recovery rate.
    """
    return calculate_recovery_metrics(db=db)


@router.get("/recovery/by-strategy")
def get_strategy_recovery_metrics(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns recovered volume, case count, and success rate broken down by recovery strategy.
    """
    return calculate_recovery_by_strategy(db=db)


@router.get("/recovery/by-failure")
def get_failure_recovery_metrics(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns recovery statistics grouped by initial payment failure reason.
    """
    return calculate_recovery_by_failure_type(db=db)


@router.get("/recovery/by-segment")
def get_segment_recovery_metrics(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns recovery performance segmented by customer tier.
    """
    return calculate_recovery_by_segment(db=db)
