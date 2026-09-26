"""Carica nel database le fatture XML e i DDT PDF di esempio (salta quelli gia' presenti)."""

from pathlib import Path

from sqlalchemy.orm import Session

from reconciliation.db import engine
from reconciliation.ddt_extraction import extract_ddt
from reconciliation.ddts import DuplicateDdtError, save_ddt
from reconciliation.fatturapa import parse_invoice
from reconciliation.invoices import DuplicateInvoiceError, save_invoice

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def main() -> None:
    for path in sorted((SAMPLES / "invoices").glob("*.xml")):
        with Session(engine) as session:
            try:
                save_invoice(session, parse_invoice(path.read_bytes()), path.name)
                session.commit()
                print(f"Fattura caricata: {path.name}")
            except DuplicateInvoiceError:
                print(f"Fattura gia' presente: {path.name}")

    for path in sorted((SAMPLES / "ddt").glob("*.pdf")):
        with Session(engine) as session:
            try:
                save_ddt(session, extract_ddt(path.read_bytes()), path.name)
                session.commit()
                print(f"DDT caricato: {path.name}")
            except DuplicateDdtError:
                print(f"DDT gia' presente: {path.name}")


if __name__ == "__main__":
    main()