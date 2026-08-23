"""
RecoverAI — Request ID & Logging Middleware
============================================
Injects and propagates X-Request-ID headers across all requests and logs processing duration.
"""

from __future__ import annotations

import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("recoverai.api")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Ensures every request has a unique Request ID for traceability.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check if client supplied X-Request-ID header
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:12]}"

        request.state.request_id = request_id

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({process_time:.2f}ms)"
        )
        return response
