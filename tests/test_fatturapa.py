from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from reconciliation.fatturapa import InvoiceParsingError, parse_invoice

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "invoices"


def load(name: str) -> bytes:
    return (SAMPLES / name).read_bytes()


def test_parses_header_fields():
    invoice = parse_invoice(load("IT01111111111_00145.xml"))

    assert invoice.supplier_vat_number == "01111111111"
    assert invoice.supplier_name == "Ferramenta Adige Srl"
    assert invoice.invoice_number == "FA-2026/0145"
    assert invoice.invoice_date == date(2026, 9, 8)
    assert invoice.total_amount == Decimal("161.04")
    assert invoice.order_number == "PO-2026-001"
    assert invoice.ddt_number == "DDT-0877"


def test_parses_lines():
    invoice = parse_invoice(load("IT01111111111_00145.xml"))

    assert len(invoice.lines) == 3
    first = invoice.lines[0]
    assert first.line_number == 1
    assert first.item_code == "VIT-M8-50"
    assert first.quantity == Decimal("1000")
    assert first.unit_price == Decimal("0.085")
    assert first.line_total == Decimal("85.00")


def test_parses_line_not_in_order():
    invoice = parse_invoice(load("IT01111111111_00162.xml"))

    assert [line.item_code for line in invoice.lines] == ["VIT-M6-30", "TAS-8", "TRASP"]


@pytest.mark.parametrize("path", sorted(SAMPLES.glob("*.xml")), ids=lambda p: p.name)
def test_all_samples_are_consistent(path: Path):
    invoice = parse_invoice(path.read_bytes())

    assert invoice.lines
    for line in invoice.lines:
        assert line.quantity * line.unit_price == line.line_total


def test_rejects_xml_with_external_entity():
    malicious = b"""<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]>
<foo>&xxe;</foo>"""

    with pytest.raises(InvoiceParsingError):
        parse_invoice(malicious)


def test_rejects_invoice_without_number():
    xml = load("IT01111111111_00145.xml").replace(b"<Numero>FA-2026/0145</Numero>", b"")

    with pytest.raises(InvoiceParsingError, match="Numero"):
        parse_invoice(xml)