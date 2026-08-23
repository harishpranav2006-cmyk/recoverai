"""
RecoverAI — Autonomous AI Recovery Agent
========================================
Tool-using orchestrator that executes the full end-to-end recovery lifecycle:
1. Ingests payment failure event
2. Gathers contextual payment and customer history
3. Runs calibrated ML recovery prediction
4. Executes deterministic Decision Engine policy
5. Generates safe customer communication if required
6. Persists audit record to database
7. Emits structured decision response
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.database import SessionLocal
from backend.models.agent import AgentDecision, ModelPrediction
from backend.models.recovery import RecoveryCase
from backend.schemas.decision import DecisionResponse
from agent.tools import (
    analyze_failure_reason,
    calculate_customer_value,
    generate_customer_message,
    get_customer_history,
    get_payment_details,
    predict_recovery_probability,
    recommend_recovery_strategy,
)

logger = logging.getLogger(__name__)


class RecoveryAgent:
    """
    Autonomous AI Recovery Agent orchestrating tools and recovery decisions.
    """

    def __init__(self) -> None:
        self.agent_name = "RecoverAI-Agent-v1"

    def run(self, payment_id: str, channel_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the end-to-end recovery agent workflow for a given payment ID.
        """
        execution_steps: List[str] = []

        # Step 1: Retrieve Payment Context
        execution_steps.append("get_payment_details")
        payment_details = get_payment_details(payment_id)
        customer_id = payment_details["customer_id"]

        # Step 2: Retrieve Customer Context
        execution_steps.append("get_customer_history")
        customer_history = get_customer_history(customer_id)

        # Step 3: Run ML Recovery Probability Prediction
        execution_steps.append("predict_recovery_probability")
        ml_result = predict_recovery_probability(payment_details)
        recovery_prob = float(ml_result["recovery_probability"])
        model_version = ml_result.get("model_version", "Calibrated Logistic Regression")
        factors = ml_result.get("factors", [])

        # Step 4: Failure Reason Analysis
        execution_steps.append("analyze_failure_reason")
        failure_analysis = analyze_failure_reason(payment_details["failure_reason"])

        # Step 5: Customer Value & VIP Evaluation
        execution_steps.append("calculate_customer_value")
        customer_value = calculate_customer_value(customer_id)

        # Step 6: Deterministic Policy Decision
        execution_steps.append("recommend_recovery_strategy")
        decision: DecisionResponse = recommend_recovery_strategy(
            payment=payment_details,
            customer=customer_history,
            recovery_probability=recovery_prob,
            context={"factors": factors, "failure_analysis": failure_analysis, "customer_value": customer_value},
        )

        # Step 7: Customer Communication Generation (if required by policy)
        customer_message_data: Optional[Dict[str, Any]] = None
        if decision.customer_message_required:
            execution_steps.append("generate_customer_message")
            customer_message_data = generate_customer_message(
                decision=decision,
                customer=customer_history,
                payment=payment_details,
                channel=channel_override or decision.channel_recommendation,
            )

        # Step 8: Database Persistence & Audit Record
        execution_steps.append("persist_decision_audit")
        self._persist_decision(
            payment_details=payment_details,
            customer_history=customer_history,
            decision=decision,
            model_version=model_version,
            factors=factors,
        )

        # Step 9: Assemble Final Structured Agent Output
        agent_output = {
            "payment_id": payment_id,
            "customer_id": customer_id,
            "recovery_probability": decision.recovery_probability,
            "tier": decision.tier,
            "strategy": decision.strategy,
            "recommended_action": decision.recommended_action,
            "delay_hours": decision.delay_hours,
            "reason_codes": decision.reason_codes,
            "explanation": decision.explanation,
            "customer_message": customer_message_data["content"] if customer_message_data else None,
            "customer_message_channel": customer_message_data["channel"] if customer_message_data else None,
            "customer_message_required": decision.customer_message_required,
            "human_review_required": decision.human_review_required,
            "model_version": model_version,
            "agent_name": self.agent_name,
            "execution_steps": execution_steps,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return agent_output

    def _persist_decision(
        self,
        payment_details: Dict[str, Any],
        customer_history: Dict[str, Any],
        decision: DecisionResponse,
        model_version: str,
        factors: List[Dict[str, Any]],
    ) -> None:
        """
        Persists structured decision and ML prediction audit trail to SQLite.
        """
        db = SessionLocal()
        try:
            payment_id = payment_details["payment_id"]
            customer_id = customer_history["customer_id"]
            now = datetime.now(timezone.utc)

            # 1. Upsert Recovery Case
            case = db.query(RecoveryCase).filter(RecoveryCase.payment_id == payment_id).first()
            if not case:
                case_id = f"CASE_{payment_id}"
                case = RecoveryCase(
                    id=case_id,
                    payment_id=payment_id,
                    customer_id=customer_id,
                    status="in_progress",
                    created_at=now,
                    updated_at=now,
                    recovery_probability=decision.recovery_probability,
                    recommended_action=decision.recommended_action,
                    amount=float(payment_details["amount"]),
                )
                db.add(case)
            else:
                case.updated_at = now
                case.recovery_probability = decision.recovery_probability
                case.recommended_action = decision.recommended_action
                case_id = case.id

            # 2. Persist Agent Decision
            agent_decision = AgentDecision(
                case_id=case_id,
                payment_id=payment_id,
                recovery_probability=decision.recovery_probability,
                recommended_action=decision.recommended_action,
                delay_hours=decision.delay_hours,
                reasoning=decision.explanation or "Deterministic recovery policy applied.",
                customer_message_required=decision.customer_message_required,
                alternative_payment_required=decision.strategy == "PAYMENT_METHOD_UPDATE",
                human_escalation_required=decision.human_review_required,
                timestamp=now,
            )
            db.add(agent_decision)

            # 3. Persist Model Prediction Audit
            import json
            model_pred = ModelPrediction(
                payment_id=payment_id,
                model_version=model_version,
                probability=decision.recovery_probability,
                top_features=json.dumps(factors),
                timestamp=now,
            )
            db.add(model_pred)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to persist agent decision for payment {payment_details.get('payment_id')}: {e}")
        finally:
            db.close()


# Global Singleton Agent Instance
_GLOBAL_AGENT: Optional[RecoveryAgent] = None


def get_recovery_agent() -> RecoveryAgent:
    """Returns the singleton RecoveryAgent instance."""
    global _GLOBAL_AGENT
    if _GLOBAL_AGENT is None:
        _GLOBAL_AGENT = RecoveryAgent()
    return _GLOBAL_AGENT


def run_recovery_agent(payment_id: str, channel_override: Optional[str] = None) -> Dict[str, Any]:
    """
    Public entry point to execute the Recovery Agent workflow on a payment ID.
    """
    agent = get_recovery_agent()
    return agent.run(payment_id=payment_id, channel_override=channel_override)
