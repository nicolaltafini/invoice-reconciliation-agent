from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconciliation.matching import ReconciliationStatus
from reconciliation.models import AuditLog, Invoice
from reconciliation.reconciliation_service import reconcile_invoice


class Role(StrEnum):
    VIEWER = "viewer"
    OPERATOR = "operator"


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"


class Decision(StrEnum):
    APPROVE = "approve"
    BLOCK = "block"


class DecisionError(Exception):
    """La decisione non e' consentita."""


STATUS_LABELS = {
    ApprovalStatus.PENDING: "da decidere",
    ApprovalStatus.APPROVED: "approvata",
    ApprovalStatus.BLOCKED: "bloccata",
}


def check_decision(
    role: str,
    approval_status: str,
    reconciliation_status: str,
    decision: Decision,
    note: str | None,
) -> None:
    """Regole pure: nessun accesso al DB, solleva DecisionError se la decisione non e' ammessa."""
    if role != Role.OPERATOR:
        raise DecisionError("Solo un operatore puo' approvare o bloccare le fatture")

    if approval_status != ApprovalStatus.PENDING:
        label = STATUS_LABELS.get(approval_status, approval_status)
        raise DecisionError(f"La fattura e' gia' {label}: la decisione non si puo' cambiare")

    has_note = bool(note and note.strip())

    if decision == Decision.BLOCK and not has_note:
        raise DecisionError("Per bloccare una fattura serve una motivazione")

    if decision == Decision.APPROVE:
        if reconciliation_status == ReconciliationStatus.WAITING_FOR_DDT:
            raise DecisionError("Non si puo' approvare: il DDT non e' ancora arrivato")
        if reconciliation_status == ReconciliationStatus.DISCREPANCIES and not has_note:
            raise DecisionError(
                "La fattura ha anomalie: per approvarla comunque serve una motivazione"
            )


def find_invoice(session: Session, invoice_number: str) -> Invoice:
    invoices = session.scalars(
        select(Invoice).where(Invoice.invoice_number == invoice_number)
    ).all()
    if not invoices:
        raise ValueError(f"Nessuna fattura con numero {invoice_number}")
    if len(invoices) > 1:
        raise ValueError(f"Piu' fatture con numero {invoice_number}: specifica il fornitore")
    return invoices[0]


def decide(
    session: Session,
    invoice_number: str,
    decision: Decision,
    actor: str,
    role: str,
    note: str | None = None,
) -> Invoice:
    invoice = find_invoice(session, invoice_number)
    _, result = reconcile_invoice(session, invoice.id)

    check_decision(role, invoice.approval_status, result.status, decision, note)

    invoice.approval_status = (
        ApprovalStatus.APPROVED if decision == Decision.APPROVE else ApprovalStatus.BLOCKED
    )
    invoice.decision_note = note.strip() if note else None
    invoice.decided_by = actor
    invoice.decided_at = datetime.now(UTC)

    session.add(AuditLog(
        actor=actor,
        role=role,
        action=f"invoice.{decision}",
        invoice_id=invoice.id,
        detail=(
            f"{invoice.invoice_number} | riconciliazione {result.status} | "
            f"a rischio {result.amount_at_risk} EUR | nota: {invoice.decision_note or '-'}"
        ),
    ))
    session.flush()
    return invoice