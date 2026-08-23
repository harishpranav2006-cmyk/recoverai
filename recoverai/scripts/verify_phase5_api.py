"""
RecoverAI — Phase 5 API Verification Script
===========================================
Executes live queries against all representative v1 endpoints using FastAPI TestClient.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def verify_phase5() -> None:
    print("\n" + "=" * 80)
    print("  RECOVERAI — PHASE 5 REST API & ANALYTICS VERIFICATION")
    print("=" * 80 + "\n")

    endpoints = [
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/health/live"),
        ("GET", "/api/v1/health/ready"),
        ("GET", "/api/v1/customers?page=1&page_size=3"),
        ("GET", "/api/v1/customers/C00001"),
        ("GET", "/api/v1/customers/C00001/history"),
        ("GET", "/api/v1/payments?page=1&page_size=3&status=failed"),
        ("GET", "/api/v1/payments/P000004"),
        ("GET", "/api/v1/payments/P000004/timeline"),
        ("POST", "/api/v1/ml/predict/P000004"),
        ("GET", "/api/v1/ml/status"),
        ("POST", "/api/v1/recovery/P000004/analyze"),
        ("POST", "/api/v1/recovery/P000004/agent"),
        ("POST", "/api/v1/recovery/P000004/workflow?force_fresh=true&seed=42"),
        ("GET", "/api/v1/recovery/P000004/decision"),
        ("GET", "/api/v1/recovery/P000004/history"),
        ("GET", "/api/v1/recovery/queue?limit=3"),
        ("POST", "/api/v1/agent/run", {"payment_id": "P000004"}),
        ("POST", "/api/v1/agent/batch", {"payment_ids": ["P000004", "P000005"]}),
        ("POST", "/api/v1/simulation/payment/P000004?force_fresh=true&seed=42"),
        ("POST", "/api/v1/simulation/demo?seed=42"),
        ("GET", "/api/v1/analytics/overview"),
        ("GET", "/api/v1/analytics/by-strategy"),
        ("GET", "/api/v1/analytics/by-failure"),
        ("GET", "/api/v1/analytics/by-segment"),
        ("GET", "/api/v1/analytics/trends?interval=monthly"),
        ("GET", "/api/v1/decisions?page=1&page_size=3"),
    ]

    for item in endpoints:
        method = item[0]
        url = item[1]
        body = item[2] if len(item) > 2 else None

        if method == "GET":
            res = client.get(url)
        else:
            res = client.post(url, json=body) if body else client.post(url)

        req_id = res.headers.get("x-request-id", "N/A")
        proc_time = res.headers.get("x-process-time-ms", "N/A")

        status_flag = "PASS" if res.status_code == 200 else f"FAIL ({res.status_code})"
        print(f"[{status_flag:<9}] {method:<4} {url:<55} | ReqID: {req_id} | {proc_time}ms")
        assert res.status_code == 200, f"Failed on {url}: {res.text}"

    print("\n" + "=" * 80)
    print("  ALL 27 REPRESENTATIVE API WORKFLOWS VERIFIED SUCCESSFULLY!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    verify_phase5()
