from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconciliation.db import engine
from reconciliation.matching import ReconciliationResult
from reconciliation.models import Invoice, PurchaseOrder
from reconciliation.reconciliation_service import reconcile_all, reconcile_invoice


def list_reconciliations(status: str | None = None) -> list[dict]:
    with Session(engine) as session:
        return [
            _summary(invoice, result)
            for invoice, result in reconcile_all(session)
            if status is None or result.status == status
        ]


def get_reconciliation(invoice_number: str) -> dict:
    with Session(engine) as session:
        invoices = session.scalars(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        ).all()
        if not invoices:
            raise ValueError(f"Nessuna fattura con numero {invoice_number}")
        if len(invoices) > 1:
            suppliers = ", ".join(invoice.supplier.name for invoice in invoices)
            raise ValueError(f"Piu' fatture con numero {invoice_number} (fornitori: {suppliers})")

        invoice, result = reconcile_invoice(session, invoices[0].id)
        return {
            **_summary(invoice, result),
            "discrepancies": [
                {
                    "type": d.type,
                    "message": d.message,
                    "item_code": d.item_code,
                    "expected": _dec(d.expected),
                    "actual": _dec(d.actual),
                    "amount_at_risk": _dec(d.amount_at_risk),
                }
                for d in result.discrepancies
            ],
        }


def get_purchase_order(order_number: str) -> dict:
    with Session(engine) as session:
        order = session.scalar(
            select(PurchaseOrder).where(PurchaseOrder.order_number == order_number)
        )
        if order is None:
            raise ValueError(f"Ordine {order_number} non trovato")
        return {
            "order_number": order.order_number,
            "supplier": order.supplier.name,
            "order_date": order.order_date.isoformat(),
            "lines": [
                {
                    "item_code": line.item_code,
                    "description": line.description,
                    "quantity": _dec(line.quantity),
                    "unit_price": _dec(line.unit_price),
                }
                for line in order.lines
            ],
        }


def _summary(invoice: Invoice, result: ReconciliationResult) -> dict:
    return {
        "invoice_number": invoice.invoice_number,
        "supplier": invoice.supplier.name,
        "invoice_date": invoice.invoice_date.isoformat(),
        "total_amount": _dec(invoice.total_amount),
        "order_number": invoice.order_number,
        "ddt_number": invoice.ddt_number,
        "status": result.status,
        "amount_at_risk": _dec(result.amount_at_risk),
    }


def _dec(value: Decimal | None) -> str | None:
    return None if value is None else f"{value.normalize():f}"