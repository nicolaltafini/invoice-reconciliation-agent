from sqlalchemy import select
from sqlalchemy.orm import Session

from reconciliation.ddt_extraction import DdtExtraction
from reconciliation.models import Ddt, DdtLine, Supplier


class DuplicateDdtError(Exception):
    """DDT gia' ricevuto per lo stesso fornitore."""


class MissingSupplierVatError(Exception):
    """Nel DDT non e' stata trovata la partita IVA del fornitore."""


def save_ddt(session: Session, extraction: DdtExtraction, source_filename: str) -> Ddt:
    extracted = extraction.ddt
    if not extracted.supplier_vat_number:
        raise MissingSupplierVatError(
            f"Partita IVA non trovata nel DDT {extracted.ddt_number}: serve revisione manuale"
        )

    supplier = session.scalar(
        select(Supplier).where(Supplier.vat_number == extracted.supplier_vat_number)
    )
    if supplier is None:
        supplier = Supplier(vat_number=extracted.supplier_vat_number, name=extracted.supplier_name)
        session.add(supplier)
    else:
        duplicate = session.scalar(
            select(Ddt).where(Ddt.supplier_id == supplier.id, Ddt.ddt_number == extracted.ddt_number)
        )
        if duplicate is not None:
            raise DuplicateDdtError(
                f"DDT {extracted.ddt_number} di {supplier.name} gia' presente (id {duplicate.id})"
            )

    ddt = Ddt(
        supplier=supplier,
        ddt_number=extracted.ddt_number,
        ddt_date=extracted.ddt_date,
        order_number=extracted.order_number,
        source_filename=source_filename,
        extraction_model=extraction.model,
        input_tokens=extraction.input_tokens,
        output_tokens=extraction.output_tokens,
        lines=[
            DdtLine(
                line_number=number,
                item_code=line.item_code,
                description=line.description,
                quantity=line.quantity,
                unit=line.unit,
            )
            for number, line in enumerate(extracted.lines, start=1)
        ],
    )
    session.add(ddt)
    session.flush()
    return ddt