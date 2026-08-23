"""
RecoverAI — Customer Message Generation & LLM Integration
==========================================================
Generates safe, personalized, professional customer payment recovery messages
across Email, SMS, and WhatsApp.

Safety Guarantees:
- NEVER exposes recovery probabilities, ML scores, SHAP values, or internal risk tiers.
- Operates in deterministic Mock LLM mode without any external API key.
- Gracefully falls back to mock templates if external LLM call fails.
- LLM cannot modify or override the deterministic Decision Engine's action/strategy.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from backend.config import settings
from backend.schemas.decision import DecisionResponse, RecommendedAction, RecoveryStrategy

logger = logging.getLogger(__name__)


# Deterministic Mock Message Templates for Zero-API-Key Execution
MOCK_TEMPLATES = {
    "WHATSAPP": {
        "PAYMENT_LINK": (
            "Hi {name}, we noticed your recent subscription payment of ₹{amount:,.2f} could not be processed "
            "due to a temporary banking issue ({reason}). You can securely complete your payment in one click here: {link}"
        ),
        "RETENTION": (
            "Hi {name}, we saw you recently paused or cancelled your plan. If this was unintentional or if you'd "
            "like to renew with uninterrupted benefits, here is a quick renewal link: {link}"
        ),
        "DEFAULT": (
            "Hi {name}, your payment of ₹{amount:,.2f} for your subscription needs attention. "
            "Please click here to update your details and complete payment: {link}"
        ),
    },
    "SMS": {
        "PAYMENT_LINK": (
            "RecoverAI Alert: Payment of Rs.{amount:,.2f} was unsuccessful ({reason}). "
            "Tap link to complete securely: {link}"
        ),
        "CARD_UPDATE": (
            "RecoverAI Alert: Your card on file has expired. Update your payment method here to keep service active: {link}"
        ),
        "DEFAULT": (
            "RecoverAI Alert: Action needed on your payment of Rs.{amount:,.2f}. Visit: {link}"
        ),
    },
    "EMAIL": {
        "CARD_UPDATE": (
            "Dear {name},\n\n"
            "We were unable to process your recurring subscription payment of ₹{amount:,.2f} because your "
            "card on file appears to have expired or has invalid credentials.\n\n"
            "To ensure your service continues without interruption, please take a moment to update your payment details:\n"
            "{link}\n\n"
            "Thank you,\n"
            "Billing Support Team"
        ),
        "GRACE_PERIOD": (
            "Dear {name},\n\n"
            "We have attempted to process your payment of ₹{amount:,.2f} for your subscription. As we were unable "
            "to complete this transaction, we have placed your account on a complimentary 7-day grace period.\n\n"
            "You can update your payment method anytime via this secure portal:\n"
            "{link}\n\n"
            "Best regards,\n"
            "Customer Care"
        ),
        "DEFAULT": (
            "Dear {name},\n\n"
            "Your recent payment of ₹{amount:,.2f} was unsuccessful. Please use the secure link below to retry "
            "with an alternate payment method (UPI, NetBanking, or Card):\n"
            "{link}\n\n"
            "Thank you for your business,\n"
            "Accounts Team"
        ),
    },
}


def _format_friendly_reason(failure_reason: str) -> str:
    """Converts technical failure codes to polite customer-facing phrasing."""
    mapping = {
        "insufficient_funds": "temporary account balance limit",
        "expired_card": "card expiration",
        "invalid_payment_details": "card detail mismatch",
        "bank_declined": "bank-side authorization check",
        "network_failure": "transient network connection interruption",
        "temporary_gateway_failure": "temporary gateway maintenance",
        "payment_timeout": "session timeout",
        "customer_cancelled": "transaction cancelled",
        "limit_exceeded": "daily card transaction limit",
        "authentication_failure": "OTP / 3D-Secure verification timeout",
    }
    return mapping.get(failure_reason.lower(), "temporary processing error")


class MessageGenerator:
    """
    Generates tailored customer communications based on Decision Engine output.
    """

    def __init__(self, openai_api_key: Optional[str] = None) -> None:
        self.api_key = openai_api_key or settings.openai_api_key

    def generate_message(
        self,
        decision: DecisionResponse,
        customer_name: str = "Customer",
        amount: float = 0.0,
        failure_reason: str = "",
        payment_id: str = "",
        channel: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generates message content for the designated channel (Email, SMS, or WhatsApp).
        """
        chosen_channel = (channel or decision.channel_recommendation or "WHATSAPP").upper()
        if chosen_channel not in ["EMAIL", "SMS", "WHATSAPP"]:
            chosen_channel = "WHATSAPP"

        friendly_reason = _format_friendly_reason(failure_reason)
        payment_link = f"https://pay.recoverai.io/checkout/{payment_id or decision.payment_id}"

        # If real OpenAI LLM is enabled and configured, try LLM generation with fallback
        if settings.is_llm_available and self.api_key:
            try:
                llm_content = self._generate_with_llm(
                    decision=decision,
                    customer_name=customer_name,
                    amount=amount,
                    friendly_reason=friendly_reason,
                    payment_link=payment_link,
                    channel=chosen_channel,
                )
                if llm_content:
                    return {
                        "channel": chosen_channel,
                        "content": llm_content,
                        "generated_by": "llm",
                        "simulated": True,
                    }
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to deterministic template: {e}")

        # Deterministic Mock Template Generation
        content = self._generate_mock_template(
            decision=decision,
            customer_name=customer_name,
            amount=amount,
            friendly_reason=friendly_reason,
            payment_link=payment_link,
            channel=chosen_channel,
        )

        return {
            "channel": chosen_channel,
            "content": content,
            "generated_by": "mock_template",
            "simulated": True,
        }

    def _generate_mock_template(
        self,
        decision: DecisionResponse,
        customer_name: str,
        amount: float,
        friendly_reason: str,
        payment_link: str,
        channel: str,
    ) -> str:
        templates = MOCK_TEMPLATES.get(channel, MOCK_TEMPLATES["WHATSAPP"])

        if decision.strategy == RecoveryStrategy.PAYMENT_METHOD_UPDATE:
            template = templates.get("CARD_UPDATE", templates["DEFAULT"])
        elif decision.strategy == RecoveryStrategy.RETENTION_INCENTIVE:
            template = templates.get("RETENTION", templates["DEFAULT"])
        elif decision.strategy == RecoveryStrategy.SUPPRESSION:
            template = templates.get("GRACE_PERIOD", templates["DEFAULT"])
        else:
            template = templates.get("PAYMENT_LINK", templates["DEFAULT"])

        return template.format(
            name=customer_name,
            amount=amount,
            reason=friendly_reason,
            link=payment_link,
        )

    def _generate_with_llm(
        self,
        decision: DecisionResponse,
        customer_name: str,
        amount: float,
        friendly_reason: str,
        payment_link: str,
        channel: str,
    ) -> Optional[str]:
        """Calls OpenAI API with strict privacy instructions."""
        import openai

        client = openai.OpenAI(api_key=self.api_key)
        system_prompt = (
            "You are RecoverAI's polite and helpful customer billing assistant. "
            "Write a concise, professional message notifying the customer of a payment issue. "
            "CRITICAL RULES: "
            "1. NEVER mention probabilities, ML scores, SHAP values, risk scores, or internal terminology. "
            "2. Be empathetic and non-threatening. "
            "3. Include the payment link provided. "
            f"4. Format specifically for {channel}."
        )
        user_prompt = (
            f"Customer Name: {customer_name}\n"
            f"Amount: ₹{amount:,.2f}\n"
            f"Issue: {friendly_reason}\n"
            f"Recommended Strategy: {decision.strategy}\n"
            f"Payment Link: {payment_link}\n"
            f"Channel: {channel}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()


# Global Singleton
_GLOBAL_MESSAGING: Optional[MessageGenerator] = None


def get_message_generator() -> MessageGenerator:
    global _GLOBAL_MESSAGING
    if _GLOBAL_MESSAGING is None:
        _GLOBAL_MESSAGING = MessageGenerator()
    return _GLOBAL_MESSAGING


def generate_customer_recovery_message(
    decision: DecisionResponse,
    customer_name: str = "Customer",
    amount: float = 0.0,
    failure_reason: str = "",
    payment_id: str = "",
    channel: Optional[str] = None,
) -> Dict[str, Any]:
    generator = get_message_generator()
    return generator.generate_message(
        decision=decision,
        customer_name=customer_name,
        amount=amount,
        failure_reason=failure_reason,
        payment_id=payment_id,
        channel=channel,
    )
