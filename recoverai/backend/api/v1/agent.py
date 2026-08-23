"""
RecoverAI — Agent Endpoints (v1)
================================
Provides single-payment and batch execution interfaces for the autonomous AI Recovery Agent.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from agent.agent import run_recovery_agent
from backend.config import settings
from backend.schemas.agent import (
    AgentBatchRequest,
    AgentBatchResponse,
    AgentBatchResponseItem,
    AgentRunRequest,
)

router = APIRouter(prefix="/agent", tags=["AI Recovery Agent"])


@router.post("/run", summary="Run Agent for Single Payment")
def run_agent(request: AgentRunRequest) -> Dict[str, Any]:
    """
    Executes the autonomous AI Recovery Agent for a single payment.
    """
    try:
        result = run_recovery_agent(payment_id=request.payment_id, channel_override=request.channel)
        return result
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Agent failed: {str(exc)}")


@router.post("/batch", response_model=AgentBatchResponse, summary="Run Agent in Batch")
def run_agent_batch(request: AgentBatchRequest) -> AgentBatchResponse:
    """
    Executes AI Recovery Agent over a batch of payment IDs (up to max configured batch limit of 50).
    """
    if len(request.payment_ids) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Batch size exceeds maximum limit of {settings.max_batch_size} payments.",
        )

    results: List[AgentBatchResponseItem] = []
    success_count = 0
    fail_count = 0

    for pid in request.payment_ids:
        try:
            agent_res = run_recovery_agent(payment_id=pid, channel_override=request.channel)
            results.append(
                AgentBatchResponseItem(
                    payment_id=pid,
                    success=True,
                    data=agent_res,
                )
            )
            success_count += 1
        except Exception as exc:
            results.append(
                AgentBatchResponseItem(
                    payment_id=pid,
                    success=False,
                    error=str(exc),
                )
            )
            fail_count += 1

    return AgentBatchResponse(
        total_requested=len(request.payment_ids),
        successful_count=success_count,
        failed_count=fail_count,
        results=results,
    )
