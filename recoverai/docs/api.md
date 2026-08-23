# RecoverAI — Production REST API Documentation

## 1. High-Level API Architecture

The RecoverAI backend exposes a modular, versioned REST API built with **FastAPI** and **Pydantic v2**. It connects the frontend presentation layer to the underlying ML inference engine, autonomous AI agent, payment simulator, and empirical revenue analytics.

```
                    ┌────────────────────────┐
                    │    FRONTEND DASHBOARD  │
                    └───────────┬────────────┘
                                │ HTTP / JSON
                                ▼
                    ┌────────────────────────┐
                    │  FASTAPI REST BACKEND  │
                    │       (/api/v1)        │
                    └───────────┬────────────┘
                                │
                    ┌───────────┴────────────┐
                    │     SERVICE LAYER      │
                    └───┬───────┬────────┬───┘
                        │       │        │
        ┌───────────────┘       │        └──────────────┐
        ▼                       ▼                       ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  ML ENGINE   │        │   AI AGENT   │        │  ANALYTICS   │
│  (Calibrated │        │  (14-Step DE │        │  (Empirical  │
│   Logistic)  │        │   + Tools)   │        │   Metrics)   │
└───────┬──────┘        └───────┬──────┘        └───────┬──────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ▼
                    ┌────────────────────────┐
                    │  SQLITE DATABASE & ORM │
                    │    (recoverai.db)      │
                    └────────────────────────┘
```

---

## 2. API Versioning & Global Base Path

All production endpoints are grouped under the `/api/v1` prefix:
- Base URL: `http://localhost:8000/api/v1`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`
- ReDoc Docs: `http://localhost:8000/redoc`

Root backward-compatible aliases exist for legacy health, recovery, and analytics routes.

---

## 3. Standardized Response Formats

### A. Paginated Collection Envelope
```json
{
  "items": [ ... ],
  "page": 1,
  "page_size": 25,
  "total": 5000,
  "total_pages": 200
}
```

### B. Standardized Error Envelope
Every error response returns a consistent JSON envelope with a unique request ID without leaking internal stack traces:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Payment with ID 'P999999' not found.",
    "request_id": "req_435dde993fb8"
  }
}
```

---

## 4. Request IDs & Observability Middleware

Every HTTP request passing through the backend receives an `X-Request-ID` and `X-Process-Time-Ms` response header. If an incoming client supplies an `X-Request-ID`, it is validated and propagated throughout logging and error structures.

---

## 5. Complete API Endpoint Inventory

### 🟢 1. Health & Status Probes
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Comprehensive system health validating database connectivity and ML model artifact presence. |
| `GET` | `/api/v1/health/live` | Process liveness probe for container orchestration. |
| `GET` | `/api/v1/health/ready` | Readiness probe confirming critical database and model dependencies. |

### 👥 2. Customer Management
| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/customers` | `page`, `page_size`, `search`, `segment`, `region`, `sort_by`, `sort_order` | Paginated customer directory with search and segment filtering. |
| `GET` | `/api/v1/customers/{customer_id}` | — | Detailed customer profile with aggregated transaction statistics. |
| `GET` | `/api/v1/customers/{customer_id}/history` | — | Chronological payment and recovery history for a specific customer. |

### 💳 3. Payment Intelligence & Lifecycle
| Method | Endpoint | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/payments` | `page`, `page_size`, `status`, `failure_reason`, `payment_method`, `customer_id`, `min_amount`, `max_amount`, `date_from`, `date_to`, `sort_by`, `sort_order` | Paginated payment records with multi-dimensional filtering. |
| `GET` | `/api/v1/payments/{payment_id}` | — | Deep inspection of payment, customer details, and latest AI decisions. |
| `GET` | `/api/v1/payments/{payment_id}/timeline` | — | Chronological event timeline (failure, ML prediction, decision, outreach, retry, outcome). |

### 🧠 4. Recovery & Decision Core
| Method | Endpoint | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/recovery/{payment_id}/analyze` | — | Direct evaluation of payment via calibrated ML and 14-step Decision Engine. |
| `POST` | `/api/v1/recovery/{payment_id}/agent` | `channel` (optional) | Executes full multi-tool AI Recovery Agent with customer messaging. |
| `POST` | `/api/v1/recovery/{payment_id}/execute` | `delay_hours`, `seed` | Executes approved recovery retry governed by safety constraints. |
| `POST` | `/api/v1/recovery/{payment_id}/workflow` | `channel`, `force_fresh`, `seed` | Complete autonomous pipeline: Agent $\rightarrow$ Decision $\rightarrow$ Simulation $\rightarrow$ Outcome $\rightarrow$ Persistence. |
| `GET` | `/api/v1/recovery/{payment_id}/decision` | — | Retrieves latest stored AI decision record. |
| `GET` | `/api/v1/recovery/{payment_id}/history` | — | Retrieves full audit log of predictions and decision iterations. |
| `GET` | `/api/v1/recovery/{payment_id}/outcome` | — | Retrieves simulated recovery outcome and revenue status. |
| `GET` | `/api/v1/recovery/queue` | `tier`, `strategy`, `human_review_required`, `retry_eligible`, `failure_reason`, `customer_segment`, `limit` | Prioritized queue of failed payments requiring action. |

### 🤖 5. AI Agent Execution
| Method | Endpoint | Body | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/agent/run` | `{ "payment_id": "P000004", "channel": "whatsapp" }` | Runs autonomous recovery agent for a single payment. |
| `POST` | `/api/v1/agent/batch` | `{ "payment_ids": ["P000004", "P000005"] }` | Batch execution over up to 50 payment IDs with per-item status. |

### 🧪 6. Payment & Outreach Simulator
| Method | Endpoint | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/simulation/payment/{payment_id}` | `delay_hours`, `is_method_updated`, `force_fresh`, `seed` | Simulates a single payment retry attempt through the gateway. |
| `POST` | `/api/v1/simulation/workflow/{payment_id}` | `channel`, `force_fresh`, `seed` | Simulates the end-to-end recovery lifecycle. |
| `POST` | `/api/v1/simulation/demo` | `seed` | Batch execution across all 7 benchmark failure demo scenarios. |

### 📊 7. Revenue Analytics
| Method | Endpoint | Parameters | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/analytics/overview` | — | High-level financial KPIs (failed volume, recovered volume, recovery rate, active cases). |
| `GET` | `/api/v1/analytics/recovery` | — | Core recovery metrics dictionary. |
| `GET` | `/api/v1/analytics/by-strategy` | — | Conversion volume and success rate grouped by recovery strategy. |
| `GET` | `/api/v1/analytics/by-failure` | — | Recovery rates and recovered amounts broken down by initial failure reason. |
| `GET` | `/api/v1/analytics/by-segment` | — | Recovery breakdown by customer segment (enterprise, premium, basic, free_trial). |
| `GET` | `/api/v1/analytics/trends` | `interval` (daily/monthly) | Structured time-series data of failed vs recovered volume for charts. |

### 📋 8. Decision History & ML Inference
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/decisions` | Paginated decision audit records with multi-criteria filtering. |
| `GET` | `/api/v1/decisions/{decision_id}` | Inspection of a specific decision record. |
| `POST` | `/api/v1/ml/predict/{payment_id}` | Calibrated probability prediction with SHAP top-factor attributions. |
| `GET` | `/api/v1/ml/status` | ML model version, feature count (75 features), calibration status, artifact paths. |

---

## 6. Safety & Simulation Sandbox Guarantees

> **CRITICAL COMPLIANCE NOTICE**:
> 1. Every simulation response explicitly contains `"simulated": true`.
> 2. Zero actual financial transactions are processed.
> 3. Zero actual SMS, Email, or WhatsApp messages are dispatched to real recipients.
> 4. Future simulation outcomes are strictly isolated and NEVER leaked into ML inference features.
