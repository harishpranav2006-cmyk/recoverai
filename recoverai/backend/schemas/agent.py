"""
RecoverAI — Agent & Batch Schemas
==================================
Contracts for single and batch AI Recovery Agent execution.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AgentRunRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    channel: Optional[str] = None


class AgentBatchRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_ids: List[str] = Field(..., min_length=1, max_length=50)
    channel: Optional[str] = None


class AgentBatchResponseItem(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    payment_id: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentBatchResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    total_requested: int
    successful_count: int
    failed_count: int
    results: List[AgentBatchResponseItem]
