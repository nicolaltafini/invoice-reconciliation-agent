from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from reconciliation.db import engine, get_session
from reconciliation.fatturapa import InvoiceParsingError, parse_invoice
from reconciliation.invoices import DuplicateInvoiceError, save_invoice

MAX_INVOICE_BYTES = 5 * 1024 * 1024

app = FastAPI(title="Invoice Reconciliation Agent")

SessionDep = Annotated[Session, Depends(get_session)]


class InvoiceCreated(BaseModel):
    id: int
    invoice_number: str
    supplier_name: str
    order_number: str | None
    ddt_number: str | None
    line_count: int


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@app.post("/invoices", status_code=status.HTTP_201_CREATED)
def upload_invoice(file: UploadFile, session: SessionDep) -> InvoiceCreated:
    content = file.file.read(MAX_INVOICE_BYTES + 1)
    if len(content) > MAX_INVOICE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File oltre 5 MB")

    try:
        parsed = parse_invoice(content)
    except InvoiceParsingError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error

    filename = Path(file.filename or "unknown.xml").name[:255]

    try:
        invoice = save_invoice(session, parsed, filename)
        session.commit()
    except DuplicateInvoiceError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    return InvoiceCreated(
        id=invoice.id,
        invoice_number=invoice.invoice_number,
        supplier_name=invoice.supplier.name,
        order_number=invoice.order_number,
        ddt_number=invoice.ddt_number,
        line_count=len(invoice.lines),
    )