"""
RecoverAI — State Machine Test Suite
====================================
Tests valid and invalid lifecycle transitions for payments and recovery cases.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.state_machine import (
    CaseState,
    InvalidStateTransitionError,
    PaymentState,
    PaymentStateMachine,
)


class TestPaymentStateMachine:
    """Verifies payment state transitions."""

    def test_valid_payment_transitions(self) -> None:
        # FAILED -> RETRY_SCHEDULED -> RETRYING -> RECOVERED
        s1 = PaymentStateMachine.transition_payment(PaymentState.FAILED, PaymentState.RETRY_SCHEDULED)
        assert s1 == PaymentState.RETRY_SCHEDULED

        s2 = PaymentStateMachine.transition_payment(s1, PaymentState.RETRYING)
        assert s2 == PaymentState.RETRYING

        s3 = PaymentStateMachine.transition_payment(s2, PaymentState.RECOVERED)
        assert s3 == PaymentState.RECOVERED

    def test_invalid_payment_transition_from_recovered(self) -> None:
        """RECOVERED is terminal; retrying recovered payment is strictly rejected."""
        with pytest.raises(InvalidStateTransitionError):
            PaymentStateMachine.transition_payment(PaymentState.RECOVERED, PaymentState.RETRYING)

    def test_invalid_payment_transition_from_recovered_to_failed(self) -> None:
        with pytest.raises(InvalidStateTransitionError):
            PaymentStateMachine.transition_payment(PaymentState.RECOVERED, PaymentState.FAILED)


class TestRecoveryCaseStateMachine:
    """Verifies recovery case state transitions."""

    def test_valid_case_lifecycle(self) -> None:
        # OPEN -> STRATEGY_SELECTED -> ACTION_SCHEDULED -> ACTION_EXECUTED -> RECOVERED
        c1 = PaymentStateMachine.transition_case(CaseState.OPEN, CaseState.STRATEGY_SELECTED)
        assert c1 == CaseState.STRATEGY_SELECTED

        c2 = PaymentStateMachine.transition_case(c1, CaseState.ACTION_SCHEDULED)
        assert c2 == CaseState.ACTION_SCHEDULED

        c3 = PaymentStateMachine.transition_case(c2, CaseState.ACTION_EXECUTED)
        assert c3 == CaseState.ACTION_EXECUTED

        c4 = PaymentStateMachine.transition_case(c3, CaseState.RECOVERED)
        assert c4 == CaseState.RECOVERED

    def test_invalid_case_transition_from_recovered(self) -> None:
        with pytest.raises(InvalidStateTransitionError):
            PaymentStateMachine.transition_case(CaseState.RECOVERED, CaseState.ACTION_SCHEDULED)
