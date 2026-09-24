from datetime import date
from decimal import Decimal
from xml.etree.ElementTree import Element, ParseError

from defusedxml import ElementTree as SafeElementTree
from defusedxml.common import DefusedXmlException
from pydantic import BaseModel


class InvoiceParsingError(Exception):
    """Il file non e' una fattura FatturaPA leggibile."""


class ParsedInvoiceLine(BaseModel):
    line_number: int
    item_code: str | None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class ParsedInvoice(BaseModel):
    supplier_vat_number: str
    supplier_name: str
    invoice_number: str
    invoice_date: date
    total_amount: Decimal | None
    order_number: str | None
    ddt_number: str | None
    lines: list[ParsedInvoiceLine]


SUPPLIER = "FatturaElettronicaHeader/CedentePrestatore/DatiAnagrafici"
DOCUMENT = "DatiGenerali/DatiGeneraliDocumento"


def parse_invoice(xml: bytes) -> ParsedInvoice:
    try:
        root = SafeElementTree.fromstring(xml)
    except (ParseError, DefusedXmlException) as error:
        raise InvoiceParsingError(f"XML non valido o non sicuro: {error}") from error

    body = root.find("FatturaElettronicaBody")
    if body is None:
        raise InvoiceParsingError("Manca FatturaElettronicaBody")

    try:
        lines = [_parse_line(node) for node in body.findall("DatiBeniServizi/DettaglioLinee")]
        if not lines:
            raise InvoiceParsingError("La fattura non contiene righe DettaglioLinee")

        total = _text(body, f"{DOCUMENT}/ImportoTotaleDocumento")

        return ParsedInvoice(
            supplier_vat_number=_required(root, f"{SUPPLIER}/IdFiscaleIVA/IdCodice"),
            supplier_name=_required(root, f"{SUPPLIER}/Anagrafica/Denominazione"),
            invoice_number=_required(body, f"{DOCUMENT}/Numero"),
            invoice_date=date.fromisoformat(_required(body, f"{DOCUMENT}/Data")),
            total_amount=Decimal(total) if total else None,
            order_number=_text(body, "DatiGenerali/DatiOrdineAcquisto/IdDocumento"),
            ddt_number=_text(body, "DatiGenerali/DatiDDT/NumeroDDT"),
            lines=lines,
        )
    except (ValueError, ArithmeticError) as error:
        raise InvoiceParsingError(f"Valore non valido nella fattura: {error}") from error


def _parse_line(node: Element) -> ParsedInvoiceLine:
    quantity = _text(node, "Quantita")
    return ParsedInvoiceLine(
        line_number=int(_required(node, "NumeroLinea")),
        item_code=_text(node, "CodiceArticolo/CodiceValore"),
        description=_required(node, "Descrizione"),
        quantity=Decimal(quantity) if quantity else Decimal("1"),
        unit_price=Decimal(_required(node, "PrezzoUnitario")),
        line_total=Decimal(_required(node, "PrezzoTotale")),
    )


def _text(element: Element, path: str) -> str | None:
    found = element.find(path)
    if found is None or found.text is None or not found.text.strip():
        return None
    return found.text.strip()


def _required(element: Element, path: str) -> str:
    value = _text(element, path)
    if value is None:
        raise InvoiceParsingError(f"Campo obbligatorio mancante: {path}")
    return value