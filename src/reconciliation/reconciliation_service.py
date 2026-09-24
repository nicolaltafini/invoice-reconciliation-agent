from sqlalchemy import select
from sqlalchemy.orm import Session

from reconciliation.matching import ReconciliationResult, reconcile
from reconciliation.models import Ddt, Invoice, PurchaseOrder


def reconcile_invoice(session: Session, invoice_id: int) -> tuple[Invoice, ReconciliationResult] | None:
    invoice = session.get(Invoice, invoice_id)
    if invoice is None:
        return None
    return invoice, _reconcile(session, invoice)


def reconcile_all(session: Session) -> list[tuple[Invoice, ReconciliationResult]]:
    invoices = session.scalars(select(Invoice).order_by(Invoice.id)).all()
    return [(invoice, _reconcile(session, invoice)) for invoice in invoices]


def _reconcile(session: Session, invoice: Invoice) -> ReconciliationResult:
    order = None
    if invoice.order_number:
        order = session.scalar(
            select(PurchaseOrder).where(PurchaseOrder.order_number == invoice.order_number)
        )

    ddt = None
    if invoice.ddt_number:
        ddt = session.scalar(
            select(Ddt).where(
                Ddt.supplier_id == invoice.supplier_id,
                Ddt.ddt_number == invoice.ddt_number,
            )
        )
    if ddt is None and invoice.order_number:
        ddt = session.scalar(
            select(Ddt).where(
                Ddt.supplier_id == invoice.supplier_id,
                Ddt.order_number == invoice.order_number,
            )
        )

    return reconcile(invoice, order, ddt)