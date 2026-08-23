"""
RecoverAI — Payment & Recovery Case State Machine
=================================================
Enforces strict, auditable lifecycle transitions for payment transactions and recovery cases.
Rejects invalid or unauthorized state transitions with informative exceptions.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, Set

logger = logging.getLogger(__name__)


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal lifecycle transition is attempted."""
    pass


class PaymentState(str, Enum):
    FAILED = "FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    RETRYING = "RETRYING"
    RECOVERED = "RECOVERED"
    PERMANENTLY_FAILED = "PERMANENTLY_FAILED"
    SUPPRESSED = "SUPPRESSED"


class CaseState(str, Enum):
    OPEN = "OPEN"
    STRATEGY_SELECTED = "STRATEGY_SELECTED"
    ACTION_SCHEDULED = "ACTION_SCHEDULED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    SUPPRESSED = "SUPPRESSED"


# Valid Transition Graphs
VALID_PAYMENT_TRANSITIONS: Dict[PaymentState, Set[PaymentState]] = {
    PaymentState.FAILED: {
        PaymentState.RETRY_SCHEDULED,
        PaymentState.RETRYING,
        PaymentState.SUPPRESSED,
        PaymentState.PERMANENTLY_FAILED,
        PaymentState.RECOVERED,  # E.g. manual payment / link payment direct
    },
    PaymentState.RETRY_SCHEDULED: {
        PaymentState.RETRYING,
        PaymentState.SUPPRESSED,
        PaymentState.PERMANENTLY_FAILED,
    },
    PaymentState.RETRYING: {
        PaymentState.RECOVERED,
        PaymentState.FAILED,
        PaymentState.RETRY_SCHEDULED,
        PaymentState.PERMANENTLY_FAILED,
        PaymentState.SUPPRESSED,
    },
    PaymentState.RECOVERED: set(),  # Terminal state: No transitions allowed
    PaymentState.PERMANENTLY_FAILED: {
        PaymentState.RECOVERED,  # Allowed only if customer supplies a brand new payment method
    },
    PaymentState.SUPPRESSED: {
        PaymentState.RECOVERED,  # Allowed if customer manually settles payment
    },
}

VALID_CASE_TRANSITIONS: Dict[CaseState, Set[CaseState]] = {
    CaseState.OPEN: {
        CaseState.STRATEGY_SELECTED,
        CaseState.ACTION_SCHEDULED,
        CaseState.ACTION_EXECUTED,
        CaseState.SUPPRESSED,
    },
    CaseState.STRATEGY_SELECTED: {
        CaseState.ACTION_SCHEDULED,
        CaseState.ACTION_EXECUTED,
        CaseState.SUPPRESSED,
    },
    CaseState.ACTION_SCHEDULED: {
        CaseState.ACTION_EXECUTED,
        CaseState.SUPPRESSED,
    },
    CaseState.ACTION_EXECUTED: {
        CaseState.RECOVERED,
        CaseState.FAILED,
        CaseState.ACTION_SCHEDULED,  # Multi-step next retry
        CaseState.SUPPRESSED,
    },
    CaseState.RECOVERED: set(),  # Terminal state
    CaseState.FAILED: {
        CaseState.ACTION_SCHEDULED,  # Subsequent retry attempt allowed if limit not reached
        CaseState.SUPPRESSED,
    },
    CaseState.SUPPRESSED: set(),  # Terminal state
}


class PaymentStateMachine:
    """
    Validates and executes lifecycle state transitions.
    """

    @staticmethod
    def transition_payment(
        current_state: PaymentState,
        target_state: PaymentState,
        payment_id: str = "P_UNKNOWN",
    ) -> PaymentState:
        """
        Validates whether transitioning from current_state to target_state is legal.
        """
        allowed = VALID_PAYMENT_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            error_msg = (
                f"Illegal payment state transition for '{payment_id}': "
                f"Cannot transition from '{current_state.value}' to '{target_state.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )
            logger.error(error_msg)
            raise InvalidStateTransitionError(error_msg)

        logger.info(f"Payment '{payment_id}' transitioned: {current_state.value} -> {target_state.value}")
        return target_state

    @staticmethod
    def transition_case(
        current_state: CaseState,
        target_state: CaseState,
        case_id: str = "CASE_UNKNOWN",
    ) -> CaseState:
        """
        Validates case state transitions.
        """
        allowed = VALID_CASE_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            error_msg = (
                f"Illegal recovery case transition for '{case_id}': "
                f"Cannot transition from '{current_state.value}' to '{target_state.value}'. "
                f"Allowed target states: {[s.value for s in allowed]}"
            )
            logger.error(error_msg)
            raise InvalidStateTransitionError(error_msg)

        logger.info(f"Recovery case '{case_id}' transitioned: {current_state.value} -> {target_state.value}")
        return target_state
