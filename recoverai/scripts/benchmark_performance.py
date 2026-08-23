"""
RecoverAI — API Performance & Response Time Benchmark
======================================================
Measures prototype local latency and throughput across core REST API endpoints.
"""

from __future__ import annotations

import time
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from backend.main import app

def run_performance_benchmark() -> None:
    client = TestClient(app)
    endpoints = [
        ("GET", "/api/v1/health", None),
        ("GET", "/api/v1/customers?page=1&page_size=20", None),
        ("GET", "/api/v1/payments?page=1&page_size=20", None),
        ("GET", "/api/v1/recovery/queue?limit=25", None),
        ("GET", "/api/v1/analytics/overview", None),
        ("POST", "/api/v1/ml/predict/P000004", None),
        ("POST", "/api/v1/recovery/P000004/workflow?force_fresh=true&seed=42", None),
    ]

    print("\n" + "=" * 80)
    print("  RECOVERAI — ENDPOINT PERFORMANCE & LATENCY BENCHMARK")
    print("=" * 80 + "\n")
    print(f"{'METHOD':<6} | {'ENDPOINT':<50} | {'RUN 1 (ms)':<10} | {'RUN 2 (ms)':<10} | {'AVG (ms)':<10}")
    print("-" * 96)

    # Warmup
    client.get("/api/v1/health")

    for method, path, body in endpoints:
        durations = []
        for _ in range(3):
            t0 = time.perf_counter()
            if method == "GET":
                res = client.get(path)
            elif method == "POST":
                res = client.post(path, json=body if body else {})
            t1 = time.perf_counter()
            durations.append((t1 - t0) * 1000.0)

        avg_ms = sum(durations) / len(durations)
        print(f"{method:<6} | {path:<50} | {durations[0]:>8.2f}ms | {durations[1]:>8.2f}ms | {avg_ms:>8.2f}ms")

    print("-" * 96 + "\n")

if __name__ == "__main__":
    run_performance_benchmark()
