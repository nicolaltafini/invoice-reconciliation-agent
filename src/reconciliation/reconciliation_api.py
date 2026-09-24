from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from reconciliation.db import get_session
from reconciliation.matching import ReconciliationResult
from reconciliation.models import Invoice
from reconciliation.reconciliation_service import reconcile_all, reconcile_invoice

router = APIRouter(tags=["reconciliation"])

SessionDep = Annotated[Session, Depends(get_session)]


class DiscrepancyOut(BaseModel):
    type: str
    message: str
    item_code: str | None
    expected: Decimal | None
    actual: Decimal | None
    amount_at_risk: Decimal


class ReconciliationOut(BaseModel):
    invoice_id: int
    invoice_number: str
    supplier_name: str
    order_number: str | None
    ddt_number: str | None
    status: str
    amount_at_risk: Decimal
    discrepancies: list[DiscrepancyOut]


@router.get("/reconciliations")
def list_reconciliations(session: SessionDep) -> list[ReconciliationOut]:
    return [_to_out(invoice, result) for invoice, result in reconcile_all(session)]


@router.get("/invoices/{invoice_id}/reconciliation")
def get_reconciliation(invoice_id: int, session: SessionDep) -> ReconciliationOut:
    found = reconcile_invoice(session, invoice_id)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Fattura {invoice_id} non trovata")
    return _to_out(*found)


def _to_out(invoice: Invoice, result: ReconciliationResult) -> ReconciliationOut:
    return ReconciliationOut(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        supplier_name=invoice.supplier.name,
        order_number=invoice.order_number,
        ddt_number=invoice.ddt_number,
        status=result.status,
        amount_at_risk=result.amount_at_risk,
        discrepancies=[
            DiscrepancyOut(
                type=d.type,
                message=d.message,
                item_code=d.item_code,
                expected=d.expected,
                actual=d.actual,
                amount_at_risk=d.amount_at_risk,
            )
            for d in result.discrepancies
        ],
    )