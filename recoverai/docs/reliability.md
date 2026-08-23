# RecoverAI — Reliability, Fault Tolerance & System Integrity

## 1. Architectural Reliability Overview

RecoverAI is built to operate reliably in high-volume, automated financial recovery scenarios. It enforces strict invariants at every layer to prevent common failure modes such as double charging, duplicate retries, invalid state transitions, data leakage, and unhandled network errors.

```
                                  RECOVERAI RELIABILITY MATRIX
                                  
+---------------------------------------------------------------------------------------------------+
| 1. IDEMPOTENCY & DEDUPLICATION                                                                    |
|    • Workflow checks existing terminal outcomes before triggering new actions                     |
|    • Repeated requests return cached results; duplicate RetryAttempt records are prevented       |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| 2. FINITE STATE MACHINE LIFECYCLE ENFORCEMENT                                                     |
|    • Enforces directed acyclic graph transitions for PaymentState and CaseState                   |
|    • Prevents illegal transitions (e.g. RECOVERED -> RETRYING or RECOVERED -> FAILED)             |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| 3. RETRY SAFETY & HARD RATE LIMITS                                                                |
|    • Maximum 3 retries per payment enforced at both Decision Engine and Service levels            |
|    • Strict minimum 4-hour spacing between attempts; premature retries trigger HTTP 409 Conflict  |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| 4. RESILIENT LLM FALLBACK & SAFETY OVERRIDES                                                      |
|    • Mock LLM generator enables 100% offline, deterministic execution                             |
|    • Decision Engine hard rules unconditionally override LLM suggestions for safety               |
+---------------------------------------------------------------------------------------------------+
                                                  |
+---------------------------------------------------------------------------------------------------+
| 5. DECOUPLED STREAMLIT CLIENT & DISTRIBUTED TRACING                                               |
|    • Streamlit consumes FastAPI REST API; handles network drops with friendly error banners       |
|    • Every API request carries an X-Request-ID and X-Process-Time-Ms header for end-to-end audit  |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Idempotency & Replay Safety

When a payment recovery action is triggered:
1. **Outcome Cache Inspection:** `run_recovery_workflow` queries `RecoveryOutcome` for the payment's active `RecoveryCase`. If the case is already `RECOVERED` or resolved and `force_fresh=False`, it immediately returns the cached outcome.
2. **Zero Duplicate Financial Accounting:** Revenue recovery metrics (`recovered_value`, `recovered_count`) are derived directly from distinct database states, ensuring that repeated API calls cannot inflate recovery figures.
3. **Deterministic Simulation:** The Payment Simulator and Outreach Simulator accept an explicit `seed` parameter (default: 42), guaranteeing reproducible simulation results across test and demo runs.

---

## 3. Finite State Machine (FSM)

RecoverAI enforces strict state transitions through [`services/state_machine.py`](file:///e:/education/razor%20pay%20buildthon/recoverai/services/state_machine.py):

### Payment Lifecycle
- `FAILED` $\rightarrow$ `RETRY_SCHEDULED` $\rightarrow$ `RETRYING` $\rightarrow$ `RECOVERED` (Terminal)
- `FAILED` $\rightarrow$ `SUPPRESSED` (Terminal)
- `FAILED` $\rightarrow$ `PERMANENTLY_FAILED` (Terminal unless payment method updated)

### Recovery Case Lifecycle
- `OPEN` $\rightarrow$ `STRATEGY_SELECTED` $\rightarrow$ `ACTION_SCHEDULED` $\rightarrow$ `ACTION_EXECUTED` $\rightarrow$ `RECOVERED` / `FAILED` / `SUPPRESSED`

**Illegal Transition Guards:** Attempting to transition from a terminal state like `RECOVERED` back to `RETRYING` raises an `InvalidStateTransitionError`, blocking data corruption.

---

## 4. Retry Safety & Rate Limiting

1. **Max Retry Limit (3 Attempts):**
   - If `retry_count >= 3`, the Decision Engine forcibly assigns `RecoveryStrategy.SUPPRESSION` and `ReasonCode.RETRY_LIMIT_REACHED`.
   - The Retry Service checks this limit independently before executing any gateway action.
2. **Exponential / Domain Spacing:**
   - Technical failures (`network_failure`, `temporary_gateway_failure`, `payment_timeout`): **4-hour delay**.
   - Balance/decline failures (`insufficient_funds`, `bank_declined`): **24-hour delay**.
   - Minimum delay threshold: **4.0 hours**. Attempting an immediate retry before the spacing elapses raises `RetrySpacingViolationError`.

---

## 5. Privacy, Security & Data Protection

- **Customer Outreach Privacy:** Customer SMS, Email, and WhatsApp templates are generated without internal model artifacts (no probability scores, SHAP values, tier strings, or reason codes).
- **Leakage Prevention:** Machine learning inputs undergo validation against forbidden post-outcome fields (`recovered_after_failure`, `recovery_time_hours`, `recovered_amount`), raising immediate exceptions if detected.
- **Request Tracing:** All API responses and error envelopes contain a unique `request_id` (e.g. `req_abc123`) and latency timing (`x-process-time-ms`).
- **Simulated Environment:** All operations are synthetic simulations; no real bank networks, payment gateways, or customer phones are contacted.
