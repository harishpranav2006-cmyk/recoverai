"""
RecoverAI — Backend API Package
================================
Aggregates legacy and v1 route modules for unified import.
"""

from backend.api.recovery import router as legacy_recovery_router
from backend.api.analytics import router as legacy_analytics_router

__all__ = [
    "legacy_recovery_router",
    "legacy_analytics_router",
]
