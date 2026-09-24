from sqlalchemy import select
from sqlalchemy.orm import Session

from reconciliation.fatturapa import ParsedInvoice
from reconciliation.models import Invoice, InvoiceLine, Supplier


class DuplicateInvoiceError(Exception):
    """Fattura gia' ricevuta per lo stesso fornitore."""


def save_invoice(session: Session, parsed: ParsedInvoice, source_filename: str) -> Invoice:
    supplier = session.scalar(
        select(Supplier).where(Supplier.vat_number == parsed.supplier_vat_number)
    )

    if supplier is None:
        supplier = Supplier(vat_number=parsed.supplier_vat_number, name=parsed.supplier_name)
        session.add(supplier)
    else:
        duplicate = session.scalar(
            select(Invoice).where(
                Invoice.supplier_id == supplier.id,
                Invoice.invoice_number == parsed.invoice_number,
            )
        )
        if duplicate is not None:
            raise DuplicateInvoiceError(
                f"Fattura {parsed.invoice_number} di {supplier.name} gia' presente (id {duplicate.id})"
            )

    invoice = Invoice(
        supplier=supplier,
        invoice_number=parsed.invoice_number,
        invoice_date=parsed.invoice_date,
        total_amount=parsed.total_amount,
        order_number=parsed.order_number,
        ddt_number=parsed.ddt_number,
        source_filename=source_filename,
        lines=[
            InvoiceLine(
                line_number=line.line_number,
                item_code=line.item_code,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                line_total=line.line_total,
            )
            for line in parsed.lines
        ],
    )
    session.add(invoice)
    session.flush()
    return invoice