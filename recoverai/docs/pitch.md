# RecoverAI — Pitch Package & Presentation Guide

> **Razorpay AI Buildathon Submission**  
> *Track: Autonomous AI Revenue Recovery for Recurring & High-Velocity Payment Failures*

---

## 1. 30-Second Elevator Pitch

> "Every day, subscription businesses and digital merchants lose up to 10% of their revenue to involuntary payment failures. Traditional recovery relies on static cron-based retries that blindly hit cards, waste fees, and churn customers.  
> 
> **RecoverAI** transforms payment recovery into an intelligent decision engine. Using calibrated machine learning, SHAP explainability, and an autonomous multi-tool AI agent governed by deterministic safety rules, RecoverAI predicts recovery likelihood, selects the optimal retry delay or outreach channel, and recovers lost revenue—safely and automatically."

---

## 2. 1-Minute Problem Pitch

> "When a recurring subscription payment fails, what happens today?
> 
> Most payment stacks do one of two things: they immediately and blindly retry the payment 3 times over 3 days, or they do nothing until the subscription expires.
> 
> This causes three severe problems:
> 1. **Blind Retries on Hard Declines**: Retrying an expired card or closed account 3 times has a 0% chance of success, but racks up merchant gateway fees and frustrates banks.
> 2. **Lack of Timing Intelligence**: A transient network timeout needs a 4-hour retry; an end-of-month insufficient funds failure needs a 24-to-48-hour retry to align with payroll cycles.
> 3. **Impersonal Customer Outreach**: High-value VIP customers get the same generic email as free-trial churners.
> 
> **RecoverAI solves this by turning recovery from a blind retry problem into an intelligent, policy-governed decision problem.**"

---

## 3. 5-Minute Complete Buildathon Pitch (Judge Script)

### [0:00 – 0:45] The Problem & The Market Opportunity
"Good morning, judges. In digital commerce and SaaS subscriptions, **involuntary churn accounts for 20% to 40% of all customer churn**. Millions of dollars are lost every month not because customers wanted to cancel, but because a payment failed.

Today's recovery mechanisms are dumb. They don't know the difference between an expired card, a transient bank timeout, and a customer waiting on their monthly salary.

We built **RecoverAI**—an autonomous AI revenue recovery platform designed to sit alongside payment gateways like Razorpay."

### [0:45 – 1:30] How RecoverAI Works (Architecture Overview)
"When a payment fails, RecoverAI processes the failure through an intelligent 5-stage pipeline:
1. **Zero-Leakage ML Model**: A Calibrated Logistic Regression model analyzes 24 transaction, customer, and failure features to output an exact recovery probability $p \in [0, 1]$.
2. **SHAP Factor Attribution**: The model doesn't just give a score; it computes exact mathematical feature attributions explaining *why* the payment is likely or unlikely to recover.
3. **Autonomous AI Recovery Agent**: An 8-tool AI agent investigates customer lifetime value, historical recovery rates, and failure categories.
4. **14-Step Deterministic Decision Engine**: Safety rules override the AI whenever necessary—enforcing strict 3-attempt caps, 4h vs 24h delay spacing, and blocking blind retries on expired cards.
5. **Simulated Action & State Machine**: The system schedules a Smart Retry, dispatches a privacy-safe WhatsApp/SMS payment update link, or escalates high-value VIPs to human support."

### [1:30 – 3:30] Live Dashboard Demonstration
*(Show Streamlit Dashboard at `http://localhost:8501`)*

1. **Executive Overview Page**:
   - "Here on our Executive Overview, leadership sees top-level financial impact: Total Payments, Gross Revenue, Recovered Revenue, and the Net Recovery Rate.
   - Let's run a live demo scenario: **Scenario 1: High-Confidence Network Failure**."
2. **Live Triage & Recovery Queue**:
   - *(Click Scenario 1 / View Recovery Queue)*
   - "Payment `P000004` failed due to a `network_failure`. 
   - Look at the ML prediction: **$p = 0.6719$ (High Confidence)**.
   - The SHAP breakdown clearly shows why: *+ Solid customer payment track record* and *+ Temporary failure category*.
   - The Decision Engine assigns **Tier 1: SMART_RETRY** with a recommended **4-hour delay**.
   - With one click, we trigger the autonomous workflow: the payment state machine transitions to `RETRY_SCHEDULED`, the gateway simulator executes, and the payment is marked **✅ RECOVERED**."
3. **Actionable Outreach Demo**:
   - "Now let's look at **Scenario 7: Expired Card Failure**.
   - A naive system would retry and fail 3 times. RecoverAI recognizes an expired card cannot succeed without an updated payment method ($p = 0.58$).
   - The Decision Engine suppresses blind retries and generates a personalized, privacy-safe **PAYMENT_METHOD_UPDATE** link dispatched via WhatsApp without exposing internal ML scores."

### [3:30 – 4:15] Technical Rigor & Empirical Validation
"We didn't just build a UI mockup. RecoverAI is backed by real engineering rigor:
- **Calibrated ML Pipeline**: Evaluated across Logistic Regression, Random Forest, and XGBoost on a chronological test split. Calibrated Logistic Regression achieved **71.02% Precision on Tier 1 ($p \ge 0.65$)**.
- **Complete Test Coverage**: **199 automated unit, integration, and E2E tests passing with 84% code coverage**.
- **Production REST API**: 27 endpoints under FastAPI `/api/v1` with request tracing (`X-Request-ID`), standardized error envelopes, and sub-20ms ML inference latency.
- **Safety by Design**: Zero data leakage, strict finite state machines, and complete Docker Compose deployment readiness."

### [4:15 – 5:00] Business Impact & Value Proposition
"What does this mean for merchants using Razorpay?
- **Recovers up to 70%+ of high-confidence failed revenue** without annoying customers.
- **Reduces wasted gateway retry fees** by suppressing unrecoverable hard declines.
- **Prevents involuntary churn** by providing frictionless self-serve payment update links.

RecoverAI turns payment failure recovery from a static retry problem into an intelligent, autonomous decision engine. Thank you, and we look forward to your questions."

---

## 4. Closing Statement

> "In summary: RecoverAI gives modern subscription businesses the brain their billing system was missing. It is explainable, safe, scalable, and built for the future of autonomous fintech."
