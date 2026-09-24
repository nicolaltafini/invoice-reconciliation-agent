from pathlib import Path
from typing import Annotated

import anthropic
from fastapi import Depends, FastAPI, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from reconciliation.db import engine, get_session
from reconciliation.ddt_extraction import DdtExtractionError, extract_ddt
from reconciliation.ddts import DuplicateDdtError, MissingSupplierVatError, save_ddt
from reconciliation.fatturapa import InvoiceParsingError, parse_invoice
from reconciliation.invoices import DuplicateInvoiceError, save_invoice
from reconciliation.reconciliation_api import router as reconciliation_router
from reconciliation.chat_api import router as chat_router

MAX_INVOICE_BYTES = 5 * 1024 * 1024
MAX_DDT_BYTES = 10 * 1024 * 1024

app = FastAPI(title="Invoice Reconciliation Agent")
app.include_router(reconciliation_router)
app.include_router(chat_router)

SessionDep = Annotated[Session, Depends(get_session)]


class InvoiceCreated(BaseModel):
    id: int
    invoice_number: str
    supplier_name: str
    order_number: str | None
    ddt_number: str | None
    line_count: int


class DdtCreated(BaseModel):
    id: int
    ddt_number: str
    supplier_name: str
    order_number: str | None
    line_count: int
    extraction_model: str
    input_tokens: int
    output_tokens: int


def _read_upload(file: UploadFile, max_bytes: int) -> bytes:
    content = file.file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File troppo grande")
    return content


def _safe_filename(file: UploadFile, default: str) -> str:
    return Path(file.filename or default).name[:255]


@app.get("/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}


@app.post("/invoices", status_code=status.HTTP_201_CREATED)
def upload_invoice(file: UploadFile, session: SessionDep) -> InvoiceCreated:
    content = _read_upload(file, MAX_INVOICE_BYTES)

    try:
        parsed = parse_invoice(content)
    except InvoiceParsingError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error

    try:
        invoice = save_invoice(session, parsed, _safe_filename(file, "unknown.xml"))
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


@app.post("/ddts", status_code=status.HTTP_201_CREATED)
def upload_ddt(file: UploadFile, session: SessionDep) -> DdtCreated:
    content = _read_upload(file, MAX_DDT_BYTES)
    if not content.startswith(b"%PDF"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Il file non e' un PDF")

    try:
        extraction = extract_ddt(content)
    except DdtExtractionError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    except anthropic.APIError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Servizio LLM non disponibile") from error

    try:
        ddt = save_ddt(session, extraction, _safe_filename(file, "unknown.pdf"))
        session.commit()
    except MissingSupplierVatError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    except DuplicateDdtError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error

    return DdtCreated(
        id=ddt.id,
        ddt_number=ddt.ddt_number,
        supplier_name=ddt.supplier.name,
        order_number=ddt.order_number,
        line_count=len(ddt.lines),
        extraction_model=ddt.extraction_model,
        input_tokens=ddt.input_tokens,
        output_tokens=ddt.output_tokens,
    )