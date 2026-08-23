"""
RecoverAI — High-Performance API Client (Session Pooling & Caching)
===================================================================
Type-safe HTTP client with persistent connection pooling and intelligent
Streamlit caching for instantaneous, sub-millisecond page transitions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import requests
import streamlit as st

from dashboard.config import API_BASE_URL, API_TIMEOUT_SECONDS

logger = logging.getLogger("recoverai.dashboard.api_client")


class APIClient:
    """Client for interacting with RecoverAI FastAPI REST endpoints with connection pooling."""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=1)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Executes an HTTP request against the API backend using pooled connections.
        Returns (data, error_message).
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            resp = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )

            if resp.status_code >= 400:
                try:
                    err_json = resp.json()
                    err_msg = (
                        err_json.get("error", {}).get("message")
                        or err_json.get("detail")
                        or f"HTTP {resp.status_code}: {resp.text}"
                    )
                except Exception:
                    err_msg = f"HTTP {resp.status_code}: {resp.text}"
                return None, err_msg

            return resp.json(), None

        except requests.exceptions.ConnectionError:
            return None, "Backend API unavailable. Please ensure the backend server is running."
        except requests.exceptions.Timeout:
            return None, f"Request timed out after {self.timeout}s."
        except Exception as e:
            return None, f"Unexpected network error: {str(e)}"

    # -------------------------------------------------------------------------
    # Health & System Status
    # -------------------------------------------------------------------------
    def get_health(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves comprehensive backend health status."""
        return self._request("GET", "/health")

    def get_health_live(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves backend liveness status."""
        return self._request("GET", "/health/live")

    def get_health_ready(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves backend readiness status."""
        return self._request("GET", "/health/ready")

    # -------------------------------------------------------------------------
    # Overview & Revenue Analytics (Cached for instantaneous navigation)
    # -------------------------------------------------------------------------
    def get_overview(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves high-level overview metrics."""
        return self._cached_get_overview()

    @st.cache_data(ttl=15, show_spinner=False)
    def _cached_get_overview(_self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        return _self._request("GET", "/analytics/overview")

    def get_recovery_analytics(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves core recovery metrics."""
        return self._cached_get_recovery_analytics()

    @st.cache_data(ttl=15, show_spinner=False)
    def _cached_get_recovery_analytics(_self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        return _self._request("GET", "/analytics/recovery")

    def get_strategy_analytics(self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Retrieves recovery analytics grouped by strategy."""
        return self._cached_get_strategy_analytics()

    @st.cache_data(ttl=15, show_spinner=False)
    def _cached_get_strategy_analytics(_self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        return _self._request("GET", "/analytics/by-strategy")

    def get_failure_analytics(self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Retrieves recovery analytics grouped by failure reason."""
        return self._cached_get_failure_analytics()

    @st.cache_data(ttl=15, show_spinner=False)
    def _cached_get_failure_analytics(_self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        return _self._request("GET", "/analytics/by-failure")

    def get_segment_analytics(self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Retrieves recovery analytics grouped by customer segment."""
        return self._cached_get_segment_analytics()

    @st.cache_data(ttl=15, show_spinner=False)
    def _cached_get_segment_analytics(_self) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        return _self._request("GET", "/analytics/by-segment")

    def get_trends(self, interval: str = "monthly") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves time-series recovery trends."""
        return self._cached_get_trends(interval)

    @st.cache_data(ttl=15, show_spinner=False)
    def _cached_get_trends(_self, interval: str = "monthly") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        return _self._request("GET", "/analytics/trends", params={"interval": interval})

    # -------------------------------------------------------------------------
    # Customers
    # -------------------------------------------------------------------------
    def get_customers(
        self,
        page: int = 1,
        page_size: int = 25,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        region: Optional[str] = None,
        sort_by: str = "lifetime_value",
        sort_order: str = "desc",
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves a paginated list of customers."""
        params = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if search:
            params["search"] = search
        if segment:
            params["segment"] = segment
        if region:
            params["region"] = region
        return self._request("GET", "/customers", params=params)

    def get_customer(self, customer_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves detailed profile for a specific customer."""
        return self._request("GET", f"/customers/{customer_id}")

    def get_customer_history(self, customer_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves payment and recovery history for a customer."""
        return self._request("GET", f"/customers/{customer_id}/history")

    # -------------------------------------------------------------------------
    # Payments
    # -------------------------------------------------------------------------
    def get_payments(
        self,
        page: int = 1,
        page_size: int = 25,
        status: Optional[str] = None,
        failure_reason: Optional[str] = None,
        payment_method: Optional[str] = None,
        customer_id: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves a paginated list of payments with multi-filtering."""
        params: Dict[str, Any] = {
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        if status:
            params["status"] = status
        if failure_reason:
            params["failure_reason"] = failure_reason
        if payment_method:
            params["payment_method"] = payment_method
        if customer_id:
            params["customer_id"] = customer_id
        if min_amount is not None:
            params["min_amount"] = min_amount
        if max_amount is not None:
            params["max_amount"] = max_amount
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        if search:
            params["search"] = search
        return self._request("GET", "/payments", params=params)

    def get_payment(self, payment_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves deep details for a specific payment."""
        return self._request("GET", f"/payments/{payment_id}")

    def get_payment_timeline(self, payment_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves chronological event timeline for a payment."""
        return self._request("GET", f"/payments/{payment_id}/timeline")

    # -------------------------------------------------------------------------
    # Recovery & Decision Core
    # -------------------------------------------------------------------------
    def get_recovery_queue(
        self,
        tier: Optional[str] = None,
        strategy: Optional[str] = None,
        human_review_required: Optional[bool] = None,
        retry_eligible: Optional[bool] = None,
        failure_reason: Optional[str] = None,
        customer_segment: Optional[str] = None,
        limit: int = 50,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
        """Retrieves prioritized recovery queue."""
        params: Dict[str, Any] = {"limit": limit}
        if tier:
            params["tier"] = tier
        if strategy:
            params["strategy"] = strategy
        if human_review_required is not None:
            params["human_review_required"] = human_review_required
        if retry_eligible is not None:
            params["retry_eligible"] = retry_eligible
        if failure_reason:
            params["failure_reason"] = failure_reason
        if customer_segment:
            params["customer_segment"] = customer_segment
        return self._request("GET", "/recovery/queue", params=params)

    def analyze_recovery(self, payment_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Evaluates a payment through ML and deterministic Decision Engine."""
        return self._request("POST", f"/recovery/{payment_id}/analyze")

    def run_agent(
        self, payment_id: str, channel: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Executes autonomous multi-tool AI Recovery Agent for a payment."""
        params = {"channel": channel} if channel else None
        return self._request("POST", f"/recovery/{payment_id}/agent", params=params)

    def execute_recovery(
        self, payment_id: str, delay_hours: Optional[float] = None, seed: int = 42
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Executes approved recovery retry attempt."""
        params: Dict[str, Any] = {"seed": seed}
        if delay_hours is not None:
            params["delay_hours"] = delay_hours
        res, err = self._request("POST", f"/recovery/{payment_id}/execute", params=params)
        if not err:
            st.cache_data.clear()
        return res, err

    def run_workflow(
        self, payment_id: str, channel: Optional[str] = None, force_fresh: bool = False, seed: int = 42
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Executes full autonomous recovery workflow."""
        params: Dict[str, Any] = {"force_fresh": force_fresh, "seed": seed}
        if channel:
            params["channel"] = channel
        res, err = self._request("POST", f"/recovery/{payment_id}/workflow", params=params)
        if not err:
            st.cache_data.clear()
        return res, err

    # -------------------------------------------------------------------------
    # ML Explainability & Predictions
    # -------------------------------------------------------------------------
    def predict_payment(self, payment_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Generates calibrated recovery probability with SHAP feature attributions."""
        return self._request("POST", f"/ml/predict/{payment_id}")

    # -------------------------------------------------------------------------
    # Simulations
    # -------------------------------------------------------------------------
    def simulate_payment(
        self, payment_id: str, force_fresh: bool = False, seed: int = 42
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Simulates gateway recovery execution."""
        params = {"force_fresh": force_fresh, "seed": seed}
        res, err = self._request("POST", f"/simulation/payment/{payment_id}", params=params)
        if not err:
            st.cache_data.clear()
        return res, err

    def simulate_demo(self, seed: int = 42) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Executes all benchmark demo recovery scenarios."""
        res, err = self._request("POST", "/simulation/demo", params={"seed": seed})
        if not err:
            st.cache_data.clear()
        return res, err

    # -------------------------------------------------------------------------
    # Decisions Audit Ledger
    # -------------------------------------------------------------------------
    def get_decisions(
        self,
        page: int = 1,
        page_size: int = 25,
        tier: Optional[str] = None,
        strategy: Optional[str] = None,
        human_review_required: Optional[bool] = None,
        payment_id: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Retrieves paginated decision log."""
        params: Dict[str, Any] = {"page": page, "page_size": page_size}
        if tier:
            params["tier"] = tier
        if strategy:
            params["strategy"] = strategy
        if human_review_required is not None:
            params["human_review_required"] = human_review_required
        if payment_id:
            params["payment_id"] = payment_id
        if customer_id:
            params["customer_id"] = customer_id
        return self._request("GET", "/decisions", params=params)


# Shared global APIClient instance
api_client = APIClient()
