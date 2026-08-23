# RecoverAI — Dashboard Architecture & User Guide

## 1. High-Level Dashboard Architecture

The RecoverAI dashboard is a production-grade fintech web application built using **Streamlit** and **Plotly**. It communicates exclusively with the Phase 5 FastAPI REST backend (`/api/v1`) via a centralized, type-safe `APIClient`.

```
                    ┌────────────────────────┐
                    │  STREAMLIT DASHBOARD   │
                    │   (dashboard/app.py)   │
                    └───────────┬────────────┘
                                │
                    ┌───────────┴────────────┐
                    │       API CLIENT       │
                    │ (dashboard/api_client) │
                    └───────────┬────────────┘
                                │ HTTP / JSON
                                ▼
                    ┌────────────────────────┐
                    │  FASTAPI REST BACKEND  │
                    │       (/api/v1)        │
                    └────────────────────────┘
```

---

## 2. Dashboard Directory Layout

```
dashboard/
├── __init__.py
├── app.py                  # Main Streamlit entrypoint, theme styling & global navigation
├── api_client.py           # Centralized type-safe HTTP client
├── config.py               # Centralized high-contrast fintech dark palette & constants
├── components/             # Reusable UI component library
│   ├── __init__.py
│   ├── cards.py            # Detail cards, decision panels, outreach preview
│   ├── charts.py           # Interactive Plotly visualizations (Dark Mode calibrated)
│   ├── metrics.py          # Formatted KPI cards with ₹ INR currency notation
│   ├── tables.py           # Styled Dataframe tables with badge indicators
│   └── timeline.py         # Chronological event audit timeline
└── pages/                  # Dedicated multi-page modules
    ├── __init__.py
    ├── ai_decisions.py     # AI Decision Audit Ledger & Policy Re-Evaluation
    ├── analytics.py        # Financial & Recovery Analytics (with CSV export)
    ├── customers.py        # Customer Intelligence & Ledger Inspection
    ├── overview.py         # Executive Overview, Drill-Downs & 7-Scenario Runner
    ├── payments.py         # Payments Directory & Action Hub
    ├── recovery_queue.py   # Prioritized Recovery Workstation & Action Suite
    └── system.py           # System Diagnostics & Latency Benchmarks
```

---

## 3. High-Contrast Fintech Theme Palette

The frontend adheres to strict high-contrast fintech dark aesthetics:
- **Background**: `#0B0F17` (Deep obsidian dark)
- **Surfaces/Cards**: `#111827` (Elevation surface)
- **Primary Accent**: `#3B82F6` (Razorpay electric blue)
- **Text Primary**: `#FFFFFF` (High contrast crisp white)
- **Text Secondary**: `#E5E7EB` (Clean readable gray)
- **Borders**: `#1F2937` (Subtle boundary borders)
- **Success Accent**: `#22C55E` / `#4ADE80` (Financial recovery green)
- **Warning Accent**: `#F59E0B` / `#FBBF24` (Actionable outreach amber)
- **Danger Accent**: `#EF4444` / `#FB7185` (Suppression / churn red)

---

## 4. Detailed Page Breakdown & Operational Interactivity

### 🏠 1. Executive Overview (`overview.py`)
- **Top 8 Financial KPIs**: Total Payments (50K), Failed Volume (₹61.02M), Rescued Revenue (₹34.89M), Recovery Rate (57.18%), Unrecovered Loss (₹26.13M), Active Cases, Retries Logged, and Model Precision (71.02%).
- **Interactive KPI Drill-Down Bar**: Direct single-click navigation to:
  - `[ 🎯 Recovery Queue ]` $\rightarrow$ Opens prioritized queue.
  - `[ ⚠️ Failed Payments ]` $\rightarrow$ Opens Payments with `status="failed"` pre-filtered.
  - `[ 👤 Customer CLV ]` $\rightarrow$ Opens Customer Intelligence.
  - `[ 📊 Financial Analytics ]` $\rightarrow$ Opens Analytics.
  - `[ 🤖 AI Decision Audit ]` $\rightarrow$ Opens Decisions Ledger.
- **Guided 7-Step Stepper**: Visual step-by-step pipeline overview.
- **Interactive Demo Scenario Runner**:
  - Run all 7 benchmark failure archetypes in batch, or run individual archetypes (`HIGH_RECOVERY_CASE`, `MEDIUM_RECOVERY_CASE`, `LOW_RECOVERY_CASE`, `HIGH_VALUE_CUSTOMER`, `MULTIPLE_RETRY_CASE`, `TEMPORARY_FAILURE_CASE`, `PERMANENT_FAILURE_CASE`).
  - View real outcome badges with direct `[ 🔍 Inspect in Recovery Queue Workstation ]` link.
- **Analytics Charts**: Time-series recovery trend with Monthly vs. Daily toggle, revenue donut, strategy performance, and failure reason breakdowns.

### 🎯 2. Recovery Queue & Workstation (`recovery_queue.py`)
- **Prioritization Matrix**: Ranked queue based on calibrated recovery probability ($p$), customer CLV, and retry eligibility rules.
- **Multi-Dimensional Filters**: Policy Tier, Strategy, Failure Reason, Customer Segment, Human Review, and Retry Eligibility.
- **Deep Inspection Workstation**:
  - Payment Summary Card & Customer Context Card.
  - Calibrated ML Score ($p \in [0, 1]$) with top positive/negative SHAP feature attributions.
  - Deterministic AI Decision Panel with reason codes and delay hours.
  - Customer Outreach Panel (WhatsApp / SMS / Email).
- **Operational Action Suite**:
  - `[ 🧠 Analyze Payment ]` $\rightarrow$ Calls `/recovery/{id}/analyze` and shows live policy evaluation.
  - `[ 🤖 Run AI Agent ]` $\rightarrow$ Calls `/recovery/{id}/agent` and executes multi-tool agent.
  - `[ ⚡ Simulate Gateway ]` $\rightarrow$ Simulates immediate gateway retry response code.
  - `[ 👤 View Customer ]` $\rightarrow$ Jumps to Customer Profile.
- **High-Impact Workflow Execution (with Confirmation)**:
  - Safely confirm and execute `/recovery/{id}/workflow` with custom seed and fresh force flags.
  - Displays real-time recovered revenue badge, state machine transition, and chronological timeline.

### 💳 3. Payments Directory (`payments.py`)
- Browse 50,000 transactions with server-side pagination (Previous / Next / Page jump).
- Multi-dimensional filters: Search ID, Status (`failed`, `succeeded`, `recovered`), Method (`card`, `upi`, `netbanking`), Failure Reason, and Min/Max Amount.
- **Deep Payment Inspector & Action Toolbar**:
  - `[ 🧠 Analyze Payment ]` $\rightarrow$ Live decision rule evaluation.
  - `[ 🤖 Run AI Recovery Agent ]` $\rightarrow$ Multi-tool agent execution.
  - `[ 🎯 Open in Queue Workstation ]` $\rightarrow$ Seamless triage jump.
  - `[ 👤 View Customer Profile ]` $\rightarrow$ Customer ledger jump.
  - Event timeline visualization.

### 👤 4. Customer Intelligence (`customers.py`)
- Search 5,000 customer profiles with sorting by CLV, successful count, failed count, or recovery rate.
- Inspect detailed customer profile, segment tier, and full transaction ledger.
- Interactive transaction selector to immediately analyze or triage any payment from customer ledger.

### 🤖 5. AI Decision Audit Ledger (`ai_decisions.py`)
- Complete audit trail of automated policy decisions.
- Filter by Tier, Strategy, Human Review flag, Payment ID, or Customer ID.
- Inspect decision rationale, reason codes, and retry delays.
- `[ 🔄 Re-Evaluate Decision Engine ]` button performs live policy comparison against current database state.

### 📊 6. Financial Analytics (`analytics.py`)
- Time-series interval toggle (Monthly vs. Daily).
- Strategy conversion benchmarking (`SMART_RETRY` vs. `CUSTOMER_OUTREACH` vs. `PAYMENT_METHOD_UPDATE`).
- Failure diagnostics and customer segment yield breakdown.
- `[ 📥 Download Strategy Performance CSV ]` for external financial audits.

### ⚙️ 7. System Diagnostics (`system.py`)
- Live infrastructure health probes (`/api/v1/health`, `/live`, `/ready`).
- `[ 🔄 Re-Check Health ]` button with live round-trip latency measurement in milliseconds.
- SQLite database status and 50,000 record verification.
- ML model specs (Calibrated Logistic Regression, 75 features, zero data leakage).
- Direct portal links to interactive Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI schema.
