import pytest

from reconciliation.approvals import Decision, DecisionError, check_decision

MATCHED = "MATCHED"
DISCREPANCIES = "DISCREPANCIES"
WAITING = "WAITING_FOR_DDT"


def test_viewer_cannot_decide():
    with pytest.raises(DecisionError, match="operatore"):
        check_decision("viewer", "PENDING", MATCHED, Decision.APPROVE, None)


def test_operator_approves_matched_invoice_without_note():
    check_decision("operator", "PENDING", MATCHED, Decision.APPROVE, None)


def test_approving_invoice_with_discrepancies_requires_note():
    with pytest.raises(DecisionError, match="motivazione"):
        check_decision("operator", "PENDING", DISCREPANCIES, Decision.APPROVE, "  ")

    check_decision("operator", "PENDING", DISCREPANCIES, Decision.APPROVE, "Nota di credito concordata")


def test_blocking_requires_reason():
    with pytest.raises(DecisionError, match="motivazione"):
        check_decision("operator", "PENDING", DISCREPANCIES, Decision.BLOCK, None)


def test_cannot_approve_without_ddt():
    with pytest.raises(DecisionError, match="DDT"):
        check_decision("operator", "PENDING", WAITING, Decision.APPROVE, "urgente")


def test_decision_cannot_be_changed():
    with pytest.raises(DecisionError, match="approvata"):
        check_decision("operator", "APPROVED", MATCHED, Decision.BLOCK, "ripensamento")